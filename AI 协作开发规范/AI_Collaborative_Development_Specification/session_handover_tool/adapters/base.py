import json
import os
from pathlib import Path
import subprocess
import uuid

from ..errors import ToolError

NATIVE = Path(__file__).resolve().parent / "native"


def native_id(value, prefix=""):
    try:
        if prefix and not value.startswith(prefix):
            raise ValueError()
        uuid.UUID(value[len(prefix):])
    except (ValueError, TypeError, AttributeError) as exc:
        raise ToolError("invalid_native_id", "Use this Agent's exact native session ID") from exc
    return value


def bridge(command, target, action, *, runtime, request_id="inspect", **kwargs):
    if target.get("native_id"):
        native_id(target["native_id"], "session-" if target["adapter"] == "deepseek_harness" else "")
    native_target = {**target["native"], "cwd": target["cwd"], "driver": target["connection"],
                     "session_id": target.get("native_id")}
    request = {"action": action, "target": native_target, "runtime_dir": str(runtime),
               "request_id": request_id, **kwargs}
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    try:
        result = subprocess.run(command, input=json.dumps(request, ensure_ascii=False).encode("utf-8"),
                                capture_output=True, cwd=target["cwd"], env=env, timeout=65,
                                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        raw = result.stdout.decode("utf-8-sig", errors="replace")
    except (OSError, subprocess.TimeoutExpired) as exc:
        raw = getattr(exc, "stdout", None) or b""
        raw = raw.decode("utf-8-sig", errors="replace") if isinstance(raw, bytes) else raw
        events = _events(raw)
        created = next((e for e in events if e.get("created")), {})
        raise ToolError("bridge_unknown" if action in ("create", "send") else "backend_unavailable",
                        type(exc).__name__, uncertain=isinstance(exc, subprocess.TimeoutExpired) and action in ("create", "send"),
                        details={"native_id": created["session_id"]} if created else None) from exc
    events = _events(raw)
    created = next((e for e in events if e.get("created")), {})
    last = events[-1] if events else {}
    if result.returncode or last.get("ok") is False:
        error = last.get("error", last)
        details = {"native_id": created["session_id"]} if created else {
            k: v for k, v in error.get("details", {}).items() if k == "native_id"}
        raise ToolError(error.get("code", "bridge_unknown"), error.get("message", "Native bridge failed; inspect its host"),
                        uncertain=bool(created) or error.get("uncertain", action in ("create", "send")), details=details)
    if not last:
        raise ToolError("bridge_unknown", "Native bridge returned no structured acknowledgement", uncertain=action in ("create", "send"))
    if created:
        last.setdefault("session_id", created["session_id"])
    return last


def _events(raw):
    events = []
    for line in raw.splitlines():
        try:
            value = json.loads(line)
            if isinstance(value, dict):events.append(value)
        except ValueError:
            pass
    return events


def observed(result):
    if type(result.get("running")) is bool:
        state = "running" if result["running"] else "idle"
    elif result.get("status") == "CASCADE_RUN_STATUS_IDLE":
        state = "idle"
    elif result.get("status") in ("CASCADE_RUN_STATUS_RUNNING", "CASCADE_RUN_STATUS_CANCELING"):
        state = "running"
    else:
        state = "unknown"
    return {"native_id": result.get("session_id"), "state": state,
            "verification": {"identity": "native", "cwd": "native", "settings": "see_native_evidence"},
            "native": result}
