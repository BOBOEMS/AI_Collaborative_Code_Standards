"""Explicit adapter registry; unsupported Agents never fall back to another one."""
from ..errors import ToolError


def get_adapter(name):
    if name == "codex_cli":
        from .codex_cli import CodexCLI
        return CodexCLI()
    if name == "codex_app":
        from .codex_app import CodexApp
        return CodexApp()
    if name == "antigravity":
        from .antigravity import Antigravity
        return Antigravity()
    if name == "deepseek_harness":
        from .deepseek_harness import DeepSeekHarness
        return DeepSeekHarness()
    raise ToolError("unsupported_adapter", f"Adapter is not integrated: {name}")


def capabilities():
    return {
        "codex_cli": {"operations": ["create", "bind", "inspect", "send"], "platform": "Windows", "stop_evidence": "owned worker or explicit handover", "create_requires_message": True},
        "codex_app": {"operations": ["bind", "inspect", "send"], "platform": "Windows", "requires": "existing authenticated host and native metadata", "create": False, "stop": False},
        "antigravity": {"operations": ["create", "bind", "inspect", "send"], "platform": "Windows", "requires": "running authenticated language server; exact native catalog variant"},
        "deepseek_harness": {"operations": ["probe", "create", "bind", "inspect", "send", "read", "wait"],
                             "platform": "Windows", "transport": "route-a-gui-host", "requires": "running authenticated GUI host",
                             "discovery": "configured authority, environment, then authenticated loopback discovery",
                             "wait": "bounded; accepted dispatch requires a fresh native turn/end; idle alone is not task completion"},
        "command_code": {"operations": [], "status": "not_integrated"},
        "grok": {"operations": [], "status": "not_integrated"},
    }
