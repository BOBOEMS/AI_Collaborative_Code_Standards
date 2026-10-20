"""Asynchronous Codex CLI calls with durable native-ID and exit receipts."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import time

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from session_handover_tool.errors import ToolError, redact
    from session_handover_tool.sessions import save, read, now
    from session_handover_tool.adapters.base import native_id
else:
    from ..errors import ToolError, redact
    from ..sessions import save, read, now
    from .base import native_id


def build_command(target):
    connection, settings = target["connection"], target["native"]
    executable = connection.get("executable", "codex")
    executable = shutil.which(executable) or executable
    command = [executable, "exec"]
    if target.get("native_id"):
        native_id(target["native_id"])
        command += ["resume", target["native_id"]]
    if settings.get("model"):
        command += ["--model", settings["model"]]
    for field, key in (("reasoning_effort", "model_reasoning_effort"), ("context_window", "model_context_window"),
                       ("auto_compact_limit", "model_auto_compact_token_limit")):
        if field in settings:
            command += ["-c", key + "=" + json.dumps(settings[field])]
    execution = target.get("execution", {})
    if not isinstance(execution, dict) or set(execution) - {"sandbox", "approval_policy", "skip_git_repo_check"}:
        raise ToolError("invalid_config", "Unsupported Codex execution option")
    if "sandbox" in execution:
        if execution["sandbox"] not in ("read-only", "workspace-write", "danger-full-access"):
            raise ToolError("invalid_config", "Unknown Codex sandbox policy")
        command += ["-c", "sandbox_mode=" + json.dumps(execution["sandbox"])]
    if "approval_policy" in execution:
        if execution["approval_policy"] not in ("untrusted", "on-failure", "on-request", "never"):
            raise ToolError("invalid_config", "Unknown Codex approval policy")
        command += ["-c", "approval_policy=" + json.dumps(execution["approval_policy"])]
    if execution.get("skip_git_repo_check"):
        command.append("--skip-git-repo-check")
    command += ["--json", "-"]
    if os.name == "nt" and str(executable).lower().endswith((".cmd", ".bat")):
        # Only fixed/validated options pass through cmd; message text stays on stdin.
        if any(any(c in str(value) for c in "&|<>^%!\r\n") for value in command):
            raise ToolError("invalid_config", "Shell wrapper arguments contain unsupported characters")
        return [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/c", *command]
    return command


def worker(path):
    path = Path(path)
    request = read(path)
    target, process = request["target"], None
    exit_row = {"started_at": now(), "launched": False, "turn_completed": False}
    try:
        command = build_command(target)
        process = subprocess.Popen(command, cwd=target["cwd"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        save(path.with_suffix(".process.json"), {"worker_pid": os.getpid(), "pid": process.pid})
        exit_row["launched"] = True
        process.stdin.write(request["message"].encode("utf-8"))
        process.stdin.close()
        with path.with_suffix(".jsonl").open("wb") as output:
            for line in process.stdout:
                output.write(line); output.flush()
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                if event.get("type") == "thread.started":
                    sid = native_id(event["thread_id"])
                    if target.get("native_id") and sid != target["native_id"]:
                        exit_row["error"] = "Native session ID changed unexpectedly"
                    save(path.with_suffix(".native.json"), {"native_id": sid, "pid": process.pid})
                if event.get("type") == "turn.completed":
                    exit_row["turn_completed"] = True
                if event.get("type") in ("error", "turn.failed"):
                    exit_row["native_error"] = redact(event.get("message") or event.get("error", "Native turn failed"))
        exit_row["exit_code"] = process.wait()
    except Exception as exc:
        exit_row.update(exit_code=None, error=redact(type(exc).__name__ + ": " + str(exc)))
    finally:
        exit_row["ended_at"] = now()
        save(path.with_suffix(".exit.json"), exit_row)


def process_alive(pid):
    if not pid:return None
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel.GetExitCodeProcess.restype = wintypes.BOOL
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.OpenProcess(0x1000, False, int(pid))
        if not handle:return None
        try:
            code = wintypes.DWORD()
            if not kernel.GetExitCodeProcess(handle, ctypes.byref(code)):return None
            return code.value == 259
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(int(pid), 0)
        return True
    except ProcessLookupError:
        return False
    except OSError:
        return None


def metadata(target):
    sid = native_id(target["native_id"])
    home = Path(target["connection"].get("codex_home") or os.environ.get("CODEX_HOME") or Path.home()/".codex")
    paths = list((home/"sessions").rglob("*" + sid + ".jsonl"))
    for path in sorted(paths, key=lambda p:p.stat().st_mtime, reverse=True):
        with path.open("rb") as stream:
            head = stream.readline(65536)
            stream.seek(max(0, path.stat().st_size - 131072))
            tail = stream.read().decode("utf-8", errors="replace").splitlines()
        try:
            envelope = json.loads(head)
            meta = envelope.get("payload", {})
            if envelope.get("type") != "session_meta" or meta.get("id") != sid:continue
            if Path(meta.get("cwd", "")).resolve() != Path(target["cwd"]).resolve():
                raise ToolError("workspace_mismatch", "Codex native cwd differs from configured cwd")
            context = {}
            for line in reversed(tail):
                try:
                    row = json.loads(line)
                except ValueError:continue
                if row.get("type") == "turn_context":
                    context = row.get("payload", {});break
            return {"identity": "native", "cwd": "native", "effective_model": context.get("model"),
                    "effective_reasoning": context.get("effort", context.get("reasoning_effort")),
                    "settings": "partial_native_observation", "session_file": str(path)}
        except (ValueError, KeyError):continue
    return {"identity": "unverified", "cwd": "unverified", "settings": "configured_only"}


class CodexCLI:
    def _launch(self, target, message, runtime, request_id):
        if not message.strip():
            raise ToolError("invalid_request", "Codex CLI creation/dispatch requires an initial message")
        build_command(target)  # Validate before reserving a native worker.
        path = Path(runtime)/"cli"/(request_id + ".request.json")
        if path.exists():raise ToolError("already_attempted", "CLI request already exists")
        save(path, {"target": target, "message": message, "created_at": now()})
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1")
        try:
            subprocess.Popen([sys.executable, "-B", str(Path(__file__)), "--worker", str(path)], cwd=target["cwd"], env=env,
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        except OSError as exc:
            raise ToolError("backend_unavailable", "Cannot start the CLI worker") from exc
        return path

    def create(self, target, runtime, *, request_id, title, message):
        path = self._launch(target, message, runtime, request_id)
        deadline = time.monotonic() + min(float(target["connection"].get("creation_timeout", 20)), 60)
        while time.monotonic() < deadline:
            native = path.with_suffix(".native.json")
            if native.is_file():
                sid = read(native)["native_id"]
                return {"native_id": sid, "state": "running", "verification": metadata({**target, "native_id": sid}),
                        "job": str(path), "creation_message_is_first_turn": True}
            ended = path.with_suffix(".exit.json")
            if ended.is_file():
                result = read(ended)
                raise ToolError("creation_unknown" if result["launched"] else "backend_unavailable",
                                result.get("native_error") or result.get("error") or "CLI exited before returning a native ID",
                                uncertain=result["launched"])
            time.sleep(.1)
        raise ToolError("creation_unknown", "CLI native ID acknowledgement timed out; inspect the existing job", uncertain=True,
                        details={"job": str(path)})

    def inspect(self, target, runtime):
        evidence = metadata(target)
        matches = []
        for path in (Path(runtime)/"cli").glob("*.request.json"):
            request = read(path)
            result = path.with_suffix(".native.json")
            sid = read(result).get("native_id") if result.exists() else request["target"].get("native_id")
            if sid == target["native_id"] and Path(request["target"]["cwd"]) == Path(target["cwd"]):
                matches.append(path)
        state, result = "unknown", {}
        if matches:
            path = max(matches, key=lambda p:p.stat().st_mtime_ns)
            ended = path.with_suffix(".exit.json")
            if ended.exists():
                result = read(ended)
                state = "idle" if result.get("exit_code") == 0 and result.get("turn_completed") else "stopped"
            elif path.with_suffix(".process.json").exists():
                info = read(path.with_suffix(".process.json"))
                state = "running" if process_alive(info.get("pid")) is True else "unknown"
        if evidence["identity"] == "unverified" and not matches:
            raise ToolError("not_found", "Codex native session is not visible in the configured home/runtime")
        return {"native_id": target["native_id"], "state": state, "verification": evidence, "execution": result}

    def send(self, target, message, runtime, *, request_id):
        state = self.inspect(target, runtime)["state"]
        if state == "running":raise ToolError("busy", "Codex CLI session is still running")
        path = self._launch(target, message, runtime, request_id)
        return {"accepted": True, "confirmation": "local_worker_started", "job": str(path),
                "native_id": target["native_id"], "execution_complete": False}


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":worker(sys.argv[2])
    else:raise SystemExit("Internal CLI worker; use session_tool.py")
