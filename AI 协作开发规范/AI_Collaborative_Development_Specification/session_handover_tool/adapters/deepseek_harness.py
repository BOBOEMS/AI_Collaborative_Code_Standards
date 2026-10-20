from .base import NATIVE, bridge, observed
from ..errors import ToolError


class DeepSeekHarness:
    def _call(self, target, action, runtime, **kwargs):
        command = [target["connection"].get("node", "node"), str(NATIVE / "deepseek_desktop.cjs")]
        return bridge(command, target, action, runtime=runtime, **kwargs)

    def create(self, target, runtime, *, request_id, title, message):
        if message:
            raise ToolError("invalid_request", "DeepSeek Harness creates an idle chat; use send for its first message")
        return observed(self._call(target, "create", runtime, request_id=request_id, title=title))

    def inspect(self, target, runtime):
        return observed(self._call(target, "inspect", runtime))

    def send(self, target, message, runtime, *, request_id):
        return self._call(target, "send", runtime, request_id=request_id, prompt=message)

    def probe(self, target, runtime):
        return self._call(target, "probe", runtime)

    def read(self, target, runtime, *, limit=200, include_events=False):
        return self._call(target, "read", runtime, options={"limit": limit, "includeEvents": include_events})

    def wait(self, target, runtime, *, timeout_seconds=30, dispatch=None):
        options = {"timeoutSeconds": timeout_seconds}
        if dispatch:
            options.update(baselineSeq=dispatch.get("baseline_seq"), expectedTurn=dispatch.get("expected_turn"),
                           dispatchId=dispatch.get("dispatch_id"))
        return self._call(target, "wait", runtime, options=options)
