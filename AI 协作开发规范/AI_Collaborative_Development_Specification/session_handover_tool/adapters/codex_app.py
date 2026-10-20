"""Existing Codex App chats via the authenticated local App Tools MCP."""
import json
import os
from pathlib import Path
import queue
import subprocess
import threading
import time
import uuid

from ..errors import ToolError
from .base import native_id
from .codex_cli import metadata


class AppTools:
    def __init__(self, target):
        connection = target["connection"]
        pipe = os.environ.get(connection.get("pipe_path_env", "CODEX_APP_TOOLS_PIPE_PATH")) or connection.get("pipe_path")
        if not pipe or not connection.get("server_script"):
            raise ToolError("backend_unavailable", "Configure the App Tools server and current pipe locator")
        self.process = None
        self.inbox, self.next_id = queue.Queue(), 0
        self.caller_id = os.environ.get(connection.get("caller_thread_id_env", "CODEX_THREAD_ID")) or connection.get("caller_thread_id")
        try:
            self.process = subprocess.Popen([connection.get("node", "node"), connection["server_script"]],
                cwd=target["cwd"], env=dict(os.environ, CODEX_APP_TOOLS_PIPE_PATH=pipe),
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                text=True, encoding="utf-8", bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            threading.Thread(target=self._read, daemon=True).start()
            self.request("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                "clientInfo": {"name": "session-handover-tool", "version": "1.0.0"}})
            self._write({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
            self.catalog = {item["name"] for item in self.request("tools/list", {}).get("tools", [])}
        except Exception:
            self.close()
            raise

    def _read(self):
        for line in self.process.stdout:
            try:
                self.inbox.put(json.loads(line))
            except ValueError:
                self.inbox.put({"bridge_error": True})
        self.inbox.put({"bridge_error": True})

    def _write(self, data):
        try:
            self.process.stdin.write(json.dumps(data, ensure_ascii=False) + "\n")
            self.process.stdin.flush()
        except (OSError, ValueError):
            raise ToolError("bridge_unknown", "App Tools connection ended") from None

    def request(self, method, params, timeout=20):
        self.next_id += 1
        request_id = self.next_id
        self._write({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ToolError("bridge_unknown", "App Tools acknowledgement timed out")
            try:
                response = self.inbox.get(timeout=remaining)
            except queue.Empty:
                raise ToolError("bridge_unknown", "App Tools acknowledgement timed out") from None
            if response.get("bridge_error"):
                raise ToolError("bridge_unknown", "App Tools returned no valid acknowledgement")
            if response.get("id") != request_id:
                continue
            if "error" in response:
                error = response["error"]
                raise ToolError("native_rejected", "App Tools rejected the RPC: " + str(error.get("message", "unknown host error"))[:500])
            return response.get("result", {})

    def call(self, name, arguments):
        if name not in self.catalog:
            raise ToolError("unsupported", "Installed App Tools does not expose " + name)
        params = {"name": name, "arguments": arguments}
        if self.caller_id:
            params["_meta"] = {"threadId": native_id(self.caller_id), "callId": "session-tool-" + uuid.uuid4().hex}
        result = self.request("tools/call", params)
        if result.get("isError"):
            raise ToolError("native_rejected", "App Tools rejected " + name)
        if isinstance(result.get("structuredContent"), dict):
            value = result["structuredContent"]
            if value.get("ok") is False:raise ToolError("native_rejected", "App Tools rejected " + name)
            return value
        for item in result.get("content", []):
            if item.get("type") == "text":
                try:
                    value = json.loads(item["text"])
                    if isinstance(value, dict):
                        if value.get("ok") is False:raise ToolError("native_rejected", "App Tools rejected " + name)
                        return value
                except ValueError:
                    pass
        return result

    def close(self):
        if self.process is None:return
        if self.process.stdin:
            try:self.process.stdin.close()
            except OSError:pass
        try:self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.process.terminate(); self.process.wait(timeout=2)
        if self.process.stdout:self.process.stdout.close()

    def __enter__(self):return self
    def __exit__(self, *_):self.close()


class CodexApp:
    def create(self, *args, **kwargs):
        raise ToolError("unsupported", "Create App chats in the host UI, then explicitly bind their native IDs")

    def inspect(self, target, runtime):
        sid = native_id(target["native_id"])
        with AppTools(target) as host:
            result = host.call("read_thread", {"threadId": sid, "hostId": target["connection"].get("host_id", "local"),
                "turnLimit": 1, "includeOutputs": False, "maxOutputCharsPerItem": 1})
        evidence = metadata(target)
        thread = result.get("thread", {})
        if thread.get("id") and thread["id"] != sid:
            raise ToolError("identity_mismatch", "App Tools returned a different native chat")
        if thread.get("id") == sid and thread.get("cwd"):
            if Path(thread["cwd"]).resolve() != Path(target["cwd"]).resolve():
                raise ToolError("workspace_mismatch", "App native cwd differs from configured cwd")
            evidence.update(identity="native", cwd="native", workspace_source="app_tools")
        if evidence["identity"] != "native":
            raise ToolError("unverified_workspace", "App chat is accessible but native session metadata/cwd is unavailable")
        # Do not infer idle from the absence of a status or from historical turn summaries.
        status = thread.get("status", result.get("status"))
        status = status.get("type") if isinstance(status, dict) else status
        state = {"active": "running", "running": "running", "idle": "idle", "completed": "idle", "stopped": "stopped"}.get(status, "unknown")
        return {"native_id": sid, "state": state, "verification": evidence, "host_accessible": True}

    def send(self, target, message, runtime, *, request_id):
        sid = native_id(target["native_id"])
        self.inspect(target, runtime)
        arguments = {"threadId": sid, "hostId": target["connection"].get("host_id", "local"), "prompt": message}
        if target["native"].get("model"):
            arguments["model"] = target["native"]["model"]
        if target["native"].get("reasoning_effort"):
            arguments["thinking"] = target["native"]["reasoning_effort"]
        with AppTools(target) as host:
            if "send_message_to_thread" not in host.catalog:
                raise ToolError("unsupported", "Installed App Tools cannot send a message")
            try:
                result = host.call("send_message_to_thread", arguments)
            except ToolError as exc:
                # A host error may occur after enqueueing. Never retry it automatically.
                exc.uncertain = True
                raise
        return {"accepted": True, "native_id": sid, "confirmation": "app_tools_returned_success",
                "execution_complete": False, "native_status": result.get("status")}
