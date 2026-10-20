"""One explicit project config; no project names, live bindings or credentials here."""
import copy
import json
import os
from pathlib import Path
import re

from .errors import ToolError

ROLES = set("ABCDE")
MUTATIONS = {"create", "bind", "send", "switch", "report", "sync"}
NATIVE_FIELDS = {
    "codex_cli": {"model", "inherit_model", "reasoning_effort", "context_window", "auto_compact_limit"},
    "codex_app": {"model", "inherit_model", "reasoning_effort"},
    "antigravity": {"model", "model_label", "native_model"},
    "deepseek_harness": {"provider", "model", "reasoning_effort"},
}


def identifier(value, what="identifier"):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,119}", value):
        raise ToolError("invalid_config", f"{what} must use ASCII letters, digits, underscore or hyphen")
    return value


def absolute(value, base=None):
    expanded = os.path.expandvars(os.path.expanduser(str(value)))
    if "${" in expanded or re.search(r"%[A-Za-z_]+%", expanded):
        raise ToolError("invalid_config", "An environment placeholder is unset")
    path = Path(expanded)
    if not path.is_absolute() and base is not None:
        path = Path(base) / path
    if not path.is_absolute():
        raise ToolError("invalid_config", "Use an absolute runtime/project path or a project-relative cwd")
    return path.resolve()


def load(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise ToolError("invalid_config", f"Cannot read project config: {type(exc).__name__}") from exc
    validate(data)
    return data


def validate(data):
    if not isinstance(data, dict):
        raise ToolError("invalid_config", "Project config must be an object")
    if data.get("schema_version") != 1:
        raise ToolError("invalid_config", "schema_version must be 1")
    identifier(data.get("project_id"), "project_id")
    root, runtime = absolute(data.get("project_root", "")), absolute(data.get("runtime_dir", ""))
    if not root.is_dir():
        raise ToolError("invalid_config", "project_root must be an existing directory")
    module = Path(__file__).resolve().parent
    if runtime == module or module in runtime.parents:
        raise ToolError("invalid_config", "Runtime data must live outside the protocol module")
    profiles = data.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        raise ToolError("invalid_config", "profiles must contain at least one Agent profile")
    for key in ("roles", "milestones", "sessions", "authorization"):
        if not isinstance(data.get(key, {}), dict):
            raise ToolError("invalid_config", key + " must be an object")
    for name in profiles:
        target(data, name)
    for role, name in data.get("roles", {}).items():
        if role not in ROLES or name not in profiles:
            raise ToolError("invalid_config", "roles map A/B/C/D/E to profile names")
    for milestone, row in data.get("milestones", {}).items():
        identifier(milestone, "milestone")
        if not isinstance(row, dict) or not isinstance(row.get("bindings", {}), dict):
            raise ToolError("invalid_config", "Milestone bindings must be an object")
        for role, key in row.get("bindings", {}).items():
            if role not in ROLES or key not in data.get("sessions", {}):
                raise ToolError("invalid_config", "Milestone binding references an unknown role/session")
        if not isinstance(row.get("role_profiles", {}), dict):
            raise ToolError("invalid_config", "role_profiles must be an object")
        for role, name in row.get("role_profiles", {}).items():
            if role not in ROLES or name not in profiles:
                raise ToolError("invalid_config", "Milestone role_profiles references an unknown role/profile")
    auth = data.get("authorization", {})
    if not isinstance(auth.get("allow", []), list) or any(not isinstance(x, str) or x not in MUTATIONS for x in auth.get("allow", [])):
        raise ToolError("invalid_config", "Unknown authorized action")
    if auth.get("reference") and not isinstance(auth["reference"], str):
        raise ToolError("invalid_config", "authorization.reference must describe the actual authorization")
    if "actors" in auth and (not isinstance(auth["actors"], list) or any(not isinstance(x, str) for x in auth["actors"])):
        raise ToolError("invalid_config", "authorization.actors must be a list of caller names")
    for ref in data.get("sessions", {}).values():
        if not isinstance(ref, dict) or any(not ref.get(k) for k in ("adapter", "native_id", "cwd", "profile")):
            raise ToolError("invalid_config", "Stored sessions require adapter/native_id/cwd/profile")
    return data


def target(data, name):
    identifier(name, "profile")
    try:
        profile = copy.deepcopy(data["profiles"][name])
    except KeyError as exc:
        raise ToolError("invalid_config", f"Unknown profile: {name}") from exc
    if not isinstance(profile, dict):
        raise ToolError("invalid_config", "Profile must be an object")
    adapter, native = profile.get("adapter"), profile.setdefault("native", {})
    if not isinstance(native, dict) or not isinstance(profile.setdefault("connection", {}), dict):
        raise ToolError("invalid_config", "native and connection must be objects")
    if set(profile["connection"]) & {"secret", "api_key", "token", "csrf_token", "cookie", "authorization"}:
        raise ToolError("invalid_config", "Use credential file/environment locators, not credential values")
    if adapter in NATIVE_FIELDS:
        unknown = set(native) - NATIVE_FIELDS[adapter]
        if unknown:
            raise ToolError("invalid_native_settings", f"{adapter} does not accept: {sorted(unknown)}")
        required = {"antigravity": {"model", "model_label", "native_model"},
                    "deepseek_harness": {"provider", "model", "reasoning_effort"}}.get(adapter, set())
        if any(not isinstance(native.get(key), str) or not native[key].strip() for key in required):
            raise ToolError("invalid_native_settings", f"{adapter} requires its native fields: {sorted(required)}")
        if adapter.startswith("codex") and bool(native.get("model")) == bool(native.get("inherit_model")):
            raise ToolError("invalid_native_settings", "Codex requires model OR inherit_model=true")
        if "inherit_model" in native and type(native["inherit_model"]) is not bool:
            raise ToolError("invalid_native_settings", "inherit_model must be a boolean")
        for key in ("model", "reasoning_effort"):
            if key in native and (not isinstance(native[key], str) or not native[key].strip()):
                raise ToolError("invalid_native_settings", key + " must be a nonempty native string")
        for key in ("context_window", "auto_compact_limit"):
            if key in native and (type(native[key]) is not int or native[key] <= 0):
                raise ToolError("invalid_native_settings", f"{key} must be a positive integer")
        if adapter == "codex_cli":
            for key in ("model", "reasoning_effort"):
                if native.get(key) and (not isinstance(native[key], str) or not re.fullmatch(r"[A-Za-z0-9_./:+-]+", native[key])):
                    raise ToolError("invalid_native_settings", f"Invalid Codex {key}")
    elif not isinstance(adapter, str) or not adapter:
        raise ToolError("invalid_config", "Every profile needs an adapter name")
    profile["cwd"] = str(absolute(profile.get("cwd", "."), absolute(data["project_root"])))
    if not Path(profile["cwd"]).is_dir():
        raise ToolError("invalid_config", "Profile cwd must exist")
    profile["profile"] = name
    return profile


def authorize(data, action, actor=None):
    auth = data.get("authorization", {})
    if action not in auth.get("allow", []) or not auth.get("reference"):
        raise ToolError("not_authorized", f"Project authorization does not permit {action}")
    if auth.get("actors") and actor not in auth["actors"]:
        raise ToolError("not_authorized", "Caller is not an authorized project operator")
    return {"reference": auth["reference"], "actor": actor, "identity_source": "caller_or_host"}


def same_identity(a, b):
    return (a["adapter"], a["native_id"], Path(a["cwd"]).resolve()) == (b["adapter"], b["native_id"], Path(b["cwd"]).resolve())
