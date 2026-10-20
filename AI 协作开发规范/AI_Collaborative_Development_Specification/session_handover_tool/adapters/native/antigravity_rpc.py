"""Local authenticated Antigravity RPC, isolated from project workflow policy."""
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from session_handover_tool.errors import ToolError
from session_handover_tool.sessions import save

SERVICE = "/exa.language_server_pb.LanguageServerService/"


def uri_equal(a, b):
    return urllib.parse.unquote(a).rstrip("/").casefold() == urllib.parse.unquote(b).rstrip("/").casefold()


def select_catalog(target, response):
    entries = response.get("userStatus", {}).get("cascadeModelConfigData", {}).get("clientModelConfigs", [])
    matches = [m for m in entries if m.get("modelId") == target["model"] and m.get("label") == target["model_label"]]
    if len(matches) != 1:
        raise ToolError("model_unavailable", "Requested native model/label is not uniquely present in the live catalog")
    model = matches[0]
    if model.get("disabled") or model.get("modelOrAlias", {}).get("model") != target["native_model"]:
        raise ToolError("model_unavailable", "Antigravity model disabled or native mapping changed")
    return {"model_id": model["modelId"], "label": model["label"], "native_model": target["native_model"]}


class Antigravity:
    def __init__(self, target):
        self.target = target
        self.base = os.environ.get("ANTIGRAVITY_LS_ADDRESS", "")
        parsed = urllib.parse.urlsplit(self.base)
        if parsed.scheme != "http" or parsed.hostname != "127.0.0.1" or not parsed.port:
            raise ToolError("backend_unavailable", "Antigravity requires its existing loopback endpoint")
        token = os.environ.get("ANTIGRAVITY_CSRF_TOKEN")
        if not token:
            raise ToolError("backend_unavailable", "Antigravity authenticated host is unavailable")
        self.headers = {"Content-Type": "application/json", "X-Codeium-Csrf-Token": token}

    def call(self, method, body, mutation=False):
        request = urllib.request.Request(self.base + SERVICE + method,
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"), headers=self.headers)
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            # Do not print the host response: it can contain credentials or conversation text.
            raise ToolError("native_rejected", f"Antigravity {method}: HTTP {exc.code}",
                            uncertain=mutation and exc.code >= 500) from None
        except (OSError, ValueError) as exc:
            raise ToolError("native_unknown" if mutation else "backend_unavailable",
                            f"Antigravity {method}: {type(exc).__name__}", uncertain=mutation) from None

    def catalog(self):
        return select_catalog(self.target, self.call("GetUserStatus", {}))

    def metadata(self, sid):
        uuid.UUID(sid)
        meta = self.call("GetConversationMetadata", {"conversationId": sid}).get("metadata", {})
        actual = [w.get("workspaceFolderAbsoluteUri", "") for w in meta.get("workspaces", [])]
        if meta.get("projectId") != self.target["driver"]["project_id"] or not any(uri_equal(u, Path(self.target["cwd"]).resolve().as_uri()) for u in actual):
            raise ToolError("workspace_mismatch", "Antigravity native project/workspace differs from the configured target")
        return {"session_id": sid, "cwd": self.target["cwd"], "project_id": meta["projectId"], "workspace_uris": actual}

    def status(self, sid):
        rows = self.call("GetAllCascadeTrajectories", {}).get("trajectorySummaries", {})
        if sid not in rows:
            raise ToolError("not_found", "Antigravity session is absent from the native registry")
        row = rows[sid]
        return {"status": row.get("status"), "step_count": row.get("stepCount", 0), "title": row.get("annotations", {}).get("title")}

    def inspect(self, sid):
        result = {**self.metadata(sid), **self.status(sid)}
        # An exhausted/removed model must not prevent inspecting the old chat
        # for a handover. Availability is enforced separately by create/send.
        try:result["available_model"] = self.catalog()
        except ToolError as exc:result["model_catalog_error"] = exc.as_dict()
        try:
            trajectory = self.call("GetCascadeTrajectory", {"cascadeId": sid,
                "trajectoryVerbosity": "CLIENT_TRAJECTORY_VERBOSITY_PROD_UI"}).get("trajectory", {})
        except ToolError as exc:
            result["generator_observation_error"] = exc.as_dict()
            trajectory = {}
        result["generators"] = [
            {"model": entry["chatModel"].get("model"), "response_model": entry["chatModel"].get("responseModel"),
             "display_name": entry["chatModel"].get("modelDisplayName"), "error": bool(entry.get("error"))}
            for entry in trajectory.get("generatorMetadata", []) if entry.get("chatModel")]
        return result

    def create(self, title, runtime, request_id):
        catalog = self.catalog()
        sid = str(uuid.uuid4())
        save(Path(runtime)/"antigravity"/(request_id + ".intent.json"), {"candidate_native_id": sid})
        try:
            result = self.call("StartCascade", {"cascadeId": sid, "source": "CORTEX_TRAJECTORY_SOURCE_CASCADE_CLIENT",
                "requestedModel": self.target["native_model"], "projectEnvConfig": {
                    "projectId": self.target["driver"]["project_id"], "defaultProjectEnvironment": {}}}, mutation=True)
        except ToolError as exc:
            if exc.uncertain:
                exc.details["native_id"] = sid
            raise
        if result.get("cascadeId") != sid:
            raise ToolError("creation_unknown", "Native creation returned an unexpected identity", uncertain=True,
                            details={"native_id": sid})
        print(json.dumps({"created": True, "session_id": sid}), flush=True)
        if title:
            self.call("UpdateConversationAnnotations", {"cascadeId": sid,
                "annotations": {"title": title}, "mergeAnnotations": True}, mutation=True)
        return {**self.metadata(sid), **self.status(sid), "available_model": catalog}

    def send(self, sid, prompt):
        catalog = self.catalog()
        self.metadata(sid)
        if self.status(sid)["status"] != "CASCADE_RUN_STATUS_IDLE":
            raise ToolError("busy", "Antigravity session is not idle")
        native = self.target["native_model"]
        self.call("SendUserCascadeMessage", {"cascadeId": sid, "items": [{"text": prompt}],
            "cascadeConfig": {"plannerConfig": {"planModel": native, "requestedModel": {"model": native}}}}, mutation=True)
        return {"accepted": True, "session_id": sid, "requested_model": catalog, "execution_complete": False}


def main():
    request = json.loads(sys.stdin.buffer.read().decode("utf-8-sig"))
    agent = Antigravity(request["target"])
    action = request["action"]
    if action == "create":
        result = agent.create(request.get("title", ""), request["runtime_dir"], request["request_id"])
    elif action == "inspect":
        result = agent.inspect(request["target"]["session_id"])
    elif action == "send":
        result = agent.send(request["target"]["session_id"], request["prompt"])
    else:
        raise ToolError("unsupported", "Unknown Antigravity operation")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except ToolError as exc:
        print(json.dumps(exc.as_dict(), ensure_ascii=False)); sys.exit(1)
    except Exception as exc:
        print(json.dumps({"ok": False, "code": "bridge_unknown", "message": type(exc).__name__, "uncertain": True})); sys.exit(1)
