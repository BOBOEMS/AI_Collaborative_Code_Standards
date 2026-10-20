from .base import NATIVE, bridge, observed
from ..errors import ToolError


class Antigravity:
    def _call(self, target, action, runtime, **kwargs):
        command = [target["connection"].get("powershell", "pwsh"), "-NoProfile", "-File", str(NATIVE / "antigravity_launcher.ps1")]
        return bridge(command, target, action, runtime=runtime, **kwargs)

    def create(self, target, runtime, *, request_id, title, message):
        if message:
            raise ToolError("invalid_request", "Antigravity creates an idle chat; use send for its first message")
        # Creation is separate from dispatch; the native host can create an idle chat.
        return observed(self._call(target, "create", runtime, request_id=request_id, title=title))

    def inspect(self, target, runtime):
        return observed(self._call(target, "inspect", runtime))

    def send(self, target, message, runtime, *, request_id):
        return self._call(target, "send", runtime, request_id=request_id, prompt=message)
