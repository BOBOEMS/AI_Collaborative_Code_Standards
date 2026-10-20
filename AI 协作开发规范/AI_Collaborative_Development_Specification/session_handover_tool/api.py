"""Public API: explicit calls, project-owned bindings, no workflow scheduler."""
import copy
import hashlib
import json
from pathlib import Path
import uuid

from . import config
from .errors import ToolError
from .sessions import Store, now, read, save


def session_key(ref):
    return ref["adapter"] + ":" + ref["native_id"]


class SessionClient:
    def __init__(self, config_path, *, actor=None, adapters=None):
        self.path = Path(config_path).resolve()
        self.actor, self._adapters = actor, adapters
        self.store = Store(config.load(self.path))

    def _load(self):
        data = config.load(self.path)
        if Store(data).root != self.store.root:
            raise ToolError("invalid_config", "Project identity/runtime changed; reopen the client")
        owner = self.store.root / "config-source.json"
        if owner.is_file() and Path(read(owner)["config"]).resolve() != self.path:
            raise ToolError("config_conflict", "This project runtime belongs to another unique config source")
        return data

    def _adapter(self, target):
        if self._adapters is not None and target["adapter"] in self._adapters:
            return self._adapters[target["adapter"]]
        from .adapters import get_adapter
        return get_adapter(target["adapter"])

    def capabilities(self):
        from .adapters import capabilities
        return capabilities()

    def validate(self):
        data = self._load()
        return {"valid": True, "project_id": data["project_id"],
                "profiles": {name: config.target(data, name)["adapter"] for name in data["profiles"]}}

    def _desired(self, data, profile, milestone, role):
        if role is not None:
            if role not in config.ROLES or not milestone:
                raise ToolError("invalid_target", "Role calls require milestone and A/B/C/D/E")
            config.identifier(milestone, "milestone")
            profile = profile or data.get("milestones", {}).get(milestone, {}).get("role_profiles", {}).get(role) or data.get("roles", {}).get(role)
        if not profile:
            raise ToolError("invalid_target", "Choose a profile or configured milestone/role")
        return config.target(data, profile)

    def _resolve(self, data, session=None, milestone=None, role=None):
        if role:
            if role not in config.ROLES or not milestone:
                raise ToolError("invalid_target", "Role calls require milestone and A/B/C/D/E")
            try:
                key = data["milestones"][milestone]["bindings"][role]
            except KeyError as exc:
                raise ToolError("not_bound", "Role has no verified session binding") from exc
        elif isinstance(session, dict):
            key = session_key(session)
        elif isinstance(session, str):
            key = session
        else:
            raise ToolError("invalid_target", "Choose an exact registered session or milestone/role")
        try:
            ref = copy.deepcopy(data["sessions"][key])
        except KeyError as exc:
            raise ToolError("not_bound", "Session is not registered in this project") from exc
        if isinstance(session, dict) and not config.same_identity(session, ref):
            raise ToolError("wrong_project", "Session identity does not belong to this project")
        return self._refresh_connection(data, ref)

    @staticmethod
    def _refresh_connection(data, ref):
        # Endpoint refresh may not select a different Agent, cwd or recipient.
        if ref["profile"] not in data["profiles"]:
            return ref
        current = config.target(data, ref["profile"])
        if current["adapter"] == ref["adapter"] and Path(current["cwd"]) == Path(ref["cwd"]):
            ref["connection"] = current["connection"]
        return ref

    def inspect(self, *, session=None, milestone=None, role=None):
        data = self._load()
        ref = self._resolve(data, session, milestone, role)
        result = self._adapter(ref).inspect(ref, self.store.root)
        return {"session": ref, "observed_at": now(), **result}

    def probe(self, profile):
        data = self._load()
        target = config.target(data, profile)
        method = getattr(self._adapter(target), "probe", None)
        if method is None:
            raise ToolError("unsupported", "This adapter does not expose native host discovery")
        return {"profile": profile, **method(target, self.store.root)}

    def read(self, *, session=None, milestone=None, role=None, limit=200, include_events=False):
        ref = self._resolve(self._load(), session, milestone, role)
        method = getattr(self._adapter(ref), "read", None)
        if method is None:
            raise ToolError("unsupported", "This adapter does not expose native history reading")
        return {"session": ref, "observed_at": now(),
                **method(ref, self.store.root, limit=limit, include_events=include_events)}

    def wait(self, *, session=None, milestone=None, role=None, request_id=None, timeout_seconds=30):
        data = self._load()
        dispatch = None
        if request_id:
            receipt = self.receipt(request_id)
            if receipt.get("action") != "send" or receipt.get("status") != "accepted" or not receipt.get("session"):
                raise ToolError("invalid_request", "Wait requires a confirmed dispatch with a frozen session snapshot")
            ref = self._resolve(data, session=receipt["session"])
            if session or role:
                requested = self._resolve(data, session, milestone, role)
                if not config.same_identity(ref, requested):
                    raise ToolError("wrong_target", "Wait request belongs to a different native session")
            dispatch = receipt["acknowledgement"]
            if dispatch.get("dispatch_id") != request_id or type(dispatch.get("baseline_seq")) is not int:
                raise ToolError("unsupported", "This dispatch has no native turn/cursor acknowledgement for waiting")
        else:
            ref = self._resolve(data, session, milestone, role)
        method = getattr(self._adapter(ref), "wait", None)
        if method is None:
            raise ToolError("unsupported", "This adapter does not expose bounded native waiting")
        return {"session": ref, "observed_at": now(),
                **method(ref, self.store.root, timeout_seconds=timeout_seconds, dispatch=dispatch)}

    def receipt(self, request_id):
        path = self.store.request_path(request_id)
        if not path.is_file():
            raise ToolError("not_found", "Request receipt does not exist")
        return read(path)

    def _request(self, action, request_id, **details):
        self.store.claim_config(self.path)
        request_id = request_id or uuid.uuid4().hex
        path = self.store.request_path(request_id)
        if path.exists():
            raise ToolError("already_attempted", "Inspect the existing receipt before any retry",
                            details={"request_id": request_id, "receipt": read(path)})
        row = {"request_id": request_id, "action": action, "status": "attempting", "created_at": now(), **details}
        save(path, row)
        return path, row

    @staticmethod
    def _failed(path, row, exc):
        row.update(status="unknown" if exc.uncertain else "failed", updated_at=now(), error=exc.as_dict())
        if exc.details.get("native_id"):
            row["native_id"] = exc.details["native_id"]
        save(path, row)
        exc.details.setdefault("request_id", row["request_id"])
        raise exc

    @staticmethod
    def _idle(observed, confirmed_stopped=False):
        state = observed.get("state", "unknown")
        if state == "running":
            raise ToolError("busy", "Native session is still running")
        if state not in ("idle", "stopped") and not confirmed_stopped:
            raise ToolError("state_unknown", "Native stop state is unknown; require an explicit handover confirmation")

    def _register(self, data, ref, *, milestone=None, role=None, replacing=False):
        key = session_key(ref)
        existing = data.get("sessions", {}).get(key)
        if existing and any(existing[k] != ref[k] for k in ("adapter", "cwd", "native")):
            raise ToolError("session_conflict", "Existing native session/settings cannot be overwritten; bind a replacement session")
        if role:
            row = data.setdefault("milestones", {}).setdefault(milestone, {})
            bindings = row.setdefault("bindings", {})
            old = bindings.get(role)
            if old and not replacing:
                raise ToolError("already_bound", "Use switch for an existing role binding")
            family = lambda adapter: "codex" if adapter in ("codex_cli", "codex_app") else adapter
            for other_milestone, other in data["milestones"].items():
                for other_role, other_key in other.get("bindings", {}).items():
                    other_ref = data.get("sessions", {}).get(other_key, {})
                    identical = (family(other_ref.get("adapter")), other_ref.get("native_id")) == (family(ref["adapter"]), ref["native_id"])
                    if identical and (other_milestone, other_role) != (milestone, role):
                        raise ToolError("session_reused", "Each milestone role needs its own native session")
                for historical in other.get("history", []):
                    historical_ref = historical["session"]
                    identical = (family(historical_ref["adapter"]), historical_ref["native_id"]) == (family(ref["adapter"]), ref["native_id"])
                    if identical and (other_milestone, historical["role"]) != (milestone, role):
                        raise ToolError("session_reused", "Historical ownership remains with its original milestone/role")
            if old:
                row.setdefault("history", []).append({"role": role, "session": copy.deepcopy(data["sessions"][old]), "replaced_at": now()})
            bindings[role] = key
            row.setdefault("role_profiles", {})[role] = ref["profile"]
        data.setdefault("sessions", {})[key] = copy.deepcopy(ref)
        save(self.path, data)
        return ref

    def create(self, profile=None, *, milestone=None, role=None, title="", message="", request_id=None):
        return self._install("create", profile, milestone=milestone, role=role, title=title,
                             message=message, request_id=request_id)

    def bind(self, native_id, profile=None, *, milestone=None, role=None, request_id=None, recover_request=None):
        return self._install("bind", profile, milestone=milestone, role=role, native_id=native_id,
                             request_id=request_id, recover_request=recover_request)

    def switch(self, *, milestone, role, profile, native_id=None, title="", message="",
               request_id=None, confirmed_stopped=False):
        return self._install("switch", profile, milestone=milestone, role=role, native_id=native_id,
                             title=title, message=message, request_id=request_id, confirmed_stopped=confirmed_stopped)

    def _install(self, action, profile, *, milestone=None, role=None, native_id=None, title="", message="",
                 request_id=None, confirmed_stopped=False, recover_request=None):
        with self.store.lock():
            data = self._load()
            auth = config.authorize(data, action, self.actor)
            target = self._desired(data, profile, milestone, role)
            adapter = self._adapter(target)
            if role:
                old_key = data.get("milestones", {}).get(milestone, {}).get("bindings", {}).get(role)
                if old_key and action != "switch":
                    raise ToolError("already_bound", "Use switch; do not overwrite an existing binding")
                if action == "switch":
                    old = self._resolve(data, milestone=milestone, role=role)
                    if native_id and old["native_id"] == native_id and old["adapter"] == target["adapter"]:
                        raise ToolError("invalid_target", "Switch binds a replacement session; it does not reconfigure the existing one")
                    self._idle(self._adapter(old).inspect(old, self.store.root), confirmed_stopped)
                pending = self.store.pending_role(milestone, role)
                if pending and pending["request_id"] != recover_request:
                    raise ToolError("request_pending", "Previous creation is unresolved; inspect/recover that request",
                                    details={"request_id": pending["request_id"]})
            if recover_request:
                pending = self.receipt(recover_request)
                if action != "bind" or pending.get("status") != "unknown" or pending.get("native_id") != native_id or (pending.get("milestone"), pending.get("role")) != (milestone, role):
                    raise ToolError("invalid_recovery", "Recovery must bind the ID returned by this exact unresolved creation")
                if any(pending.get("target", {}).get(k) != target.get(k) for k in ("adapter", "cwd", "native")):
                    raise ToolError("invalid_recovery", "Recover the same Agent/workspace/settings as the unresolved creation")
            path, receipt = self._request(action, request_id, milestone=milestone, role=role, target=target, authorization=auth)
            created = False
            try:
                if native_id:
                    ref = {**target, "native_id": native_id}
                    observed = adapter.inspect(ref, self.store.root)
                else:
                    observed = adapter.create(target, self.store.root, request_id=receipt["request_id"], title=title, message=message)
                    created = True
                    native_id = observed.get("native_id")
                    if not native_id:
                        raise ToolError("creation_unknown", "Agent did not return a native ID", uncertain=True)
                    receipt.update(native_id=native_id, status="attempting")
                    save(path, receipt)
                verification = observed.get("verification", {})
                if observed.get("native_id") != native_id:
                    raise ToolError("identity_mismatch", "Native observation returned a different session identity")
                if verification.get("identity") != "native" or verification.get("cwd") != "native":
                    raise ToolError("unverified_workspace", "Binding requires native identity and workspace evidence")
                ref = {**target, "native_id": native_id, "registered_at": now(), "observed": observed}
                self._register(data, ref, milestone=milestone, role=role, replacing=action == "switch")
                receipt.update(status="registered", native_id=native_id, session=ref, updated_at=now())
                save(path, receipt)
                if recover_request:
                    pending.update(status="recovered", recovery_request=receipt["request_id"])
                    save(self.store.request_path(recover_request), pending)
                return receipt
            except ToolError as exc:
                if native_id:
                    exc.details.setdefault("native_id", native_id)
                    # A created session still exists if local registration fails.
                    if created:
                        exc.uncertain = True
                self._failed(path, receipt, exc)
            except Exception as exc:
                self._failed(path, receipt, ToolError("operation_unknown", type(exc).__name__, uncertain=True,
                                                     details={"native_id": native_id} if native_id else None))

    def send(self, message, *, task_id, session=None, milestone=None, role=None, report_to=(),
             request_id=None, confirmed_stopped=False, record=None):
        if not isinstance(message, str) or not message.strip():
            raise ToolError("invalid_request", "Dispatch message must be nonempty text")
        milestone = config.identifier(milestone or "direct", "milestone")
        config.identifier(task_id, "task_id")
        with self.store.lock():
            data = self._load()
            auth = config.authorize(data, "send", self.actor)
            target = self._resolve(data, session, milestone, role)
            desired = self._desired(data, None, milestone, role) if role else config.target(data, target["profile"])
            if (desired["adapter"], desired["cwd"], desired["native"]) != (target["adapter"], target["cwd"], target["native"]):
                raise ToolError("switch_required", "Desired Agent/model/settings differ from the registered target")
            adapter = self._adapter(target)
            self._idle(adapter.inspect(target, self.store.root), confirmed_stopped)
            task_path = self.store.task_path(milestone, task_id)
            if task_path.exists():
                raise ToolError("already_attempted", "Task ID already has a dispatch snapshot; inspect it instead of resending")
            receivers = [self._resolve(data, milestone=milestone, role=r) if r in config.ROLES
                         else self._resolve(data, session=r) for r in report_to]
            path, receipt = self._request("send", request_id, milestone=milestone, role=role,
                                          task_id=task_id, session=target, authorization=auth)
            task = {"milestone": milestone, "task_id": task_id, "target": target, "report_to": receivers,
                    "message_sha256": hashlib.sha256(message.encode("utf-8")).hexdigest(),
                    "record": str(record) if record else None, "request_id": receipt["request_id"], "created_at": now()}
            save(task_path, task)
            try:
                result = adapter.send(target, message, self.store.root, request_id=receipt["request_id"])
                if result.get("accepted") is not True:
                    raise ToolError("not_accepted", "Agent did not acknowledge the dispatch", uncertain=result.get("accepted") is not False)
                receipt.update(status="accepted", acknowledgement=result, updated_at=now())
                save(path, receipt)
                return receipt
            except ToolError as exc:
                self._failed(path, receipt, exc)
            except Exception as exc:
                self._failed(path, receipt, ToolError("dispatch_unknown", type(exc).__name__, uncertain=True))

    def report(self, *, milestone, task_id, summary, status="delivery", record=None, commit=None,
               delivery_id=None, sender=None):
        with self.store.lock():
            data = self._load()
            auth = config.authorize(data, "report", self.actor)
            path = self.store.task_path(milestone, task_id)
            if not path.is_file():
                raise ToolError("not_found", "Report requires an existing dispatch snapshot")
            task = read(path)
            if sender and sender != session_key(task["target"]):
                raise ToolError("wrong_sender", "Report sender differs from the dispatched native session")
            if not task["report_to"]:
                raise ToolError("no_report_route", "This task has no report recipients")
            payload = {"kind": "delivery_notification", "project_id": data["project_id"],
                       "milestone": milestone, "task_id": task_id, "sender": session_key(task["target"]),
                       "status": status, "summary": summary, "record": str(record) if record else None, "commit": commit}
            text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
            digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
            delivery_id = config.identifier(delivery_id or digest[:24], "delivery_id")
            request_id = "report-" + hashlib.sha256((milestone + "/" + task_id + "/" + delivery_id).encode()).hexdigest()[:32]
            receipt_path = self.store.request_path(request_id)
            if receipt_path.exists():
                receipt = read(receipt_path)
                if receipt.get("payload_sha256") != digest:
                    raise ToolError("delivery_conflict", "Delivery ID already identifies a different report")
            else:
                _, receipt = self._request("report", request_id, milestone=milestone,
                                           payload_sha256=digest, recipients={}, authorization=auth)
            for frozen in task["report_to"]:
                key = session_key(frozen)
                previous = receipt["recipients"].get(key, {})
                if previous.get("status") in ("accepted", "unknown", "attempting"):
                    continue
                # Refresh this same native identity, never resolve today's role pointer.
                canonical = data.get("sessions", {}).get(key, frozen)
                target = canonical if config.same_identity(canonical, frozen) else frozen
                target = self._refresh_connection(data, copy.deepcopy(target))
                item = {"status": "attempting", "attempts": previous.get("attempts", 0) + 1}
                receipt["recipients"][key] = item
                save(receipt_path, receipt)
                try:
                    adapter = self._adapter(target)
                    self._idle(adapter.inspect(target, self.store.root))
                    result = adapter.send(target, text, self.store.root,
                                                        request_id=request_id + "-" + hashlib.sha256(key.encode()).hexdigest()[:8])
                    if result.get("accepted") is not True:
                        raise ToolError("not_accepted", "Recipient did not acknowledge the delivery", uncertain=result.get("accepted") is not False)
                    item.update(status="accepted", acknowledgement=result)
                except ToolError as exc:
                    item.update(status="unknown" if exc.uncertain else "failed", error=exc.as_dict())
                except Exception as exc:
                    item.update(status="unknown", error={"code": "delivery_unknown", "message": type(exc).__name__})
                save(receipt_path, receipt)
            states = [item["status"] for item in receipt["recipients"].values()]
            receipt.update(status="accepted" if states and all(s == "accepted" for s in states) else "partial",
                           updated_at=now())
            save(receipt_path, receipt)
            return receipt

    def sync(self, output):
        with self.store.lock():
            data = self._load()
            config.authorize(data, "sync", self.actor)
            self.store.claim_config(self.path)
            output = config.absolute(output)
            docs = config.absolute(data.get("documents_root", data["project_root"]))
            if output == self.path or docs not in output.parents:
                raise ToolError("invalid_target", "Session display must be a separate file under documents_root")
            if output.suffix.lower() != ".md" or output.name.upper() in ("ROLES.MD", "STATE.MD", "AGENT.MD", "AGENTS.MD"):
                raise ToolError("invalid_target", "Write the session display to its own Markdown document")
            def cell(value):
                return str(value).replace("|", "\\|").replace("\n", " ")
            start, end = "<!-- session-tool:start -->", "<!-- session-tool:end -->"
            lines = [start, "## 工具同步的目标配置", "", "唯一来源：" + str(self.path), "",
                     "| 角色 | Agent 连接 | 目标原生设置 |", "|---|---|---|"]
            for role, name in sorted(data.get("roles", {}).items()):
                target = config.target(data, name)
                lines.append(f"| {role} | {target['adapter']} | {cell(json.dumps(target['native'], ensure_ascii=False))} |")
            for milestone, group in data.get("milestones", {}).items():
                lines += ["", "### " + milestone, "", "| 角色 | 当前目标 profile / 原生设置 | 已登记 Agent / 原生会话 ID | 工作目录 | 登记时设置 / 状态（非实时） |", "|---|---|---|---|---|"]
                for role, key in sorted(group.get("bindings", {}).items()):
                    ref = data["sessions"][key]
                    desired = self._desired(data, None, milestone, role)
                    desired_text = desired["profile"] + " / " + json.dumps(desired["native"], ensure_ascii=False)
                    registered_text = json.dumps(ref["native"], ensure_ascii=False) + " / " + ref.get("observed", {}).get("state", "unknown")
                    lines.append(f"| {role} | {cell(desired_text)} | {cell(ref['adapter'])} / {ref['native_id']} | {cell(ref['cwd'])} | {cell(registered_text)} |")
                for old in group.get("history", []):
                    lines.append(f"\n替换记录：{old['role']} / {old['session']['adapter']} / {old['session']['native_id']} / {old['replaced_at']}")
            lines += [end, ""]
            block = "\n".join(lines)
            text = output.read_text(encoding="utf-8-sig") if output.exists() else "# 会话配置与登记\n\n"
            if start in text or end in text:
                if text.count(start) != 1 or text.count(end) != 1 or text.index(end) < text.index(start):
                    raise ToolError("invalid_target", "Session display has malformed generated markers")
                text = text[:text.index(start)] + block + text[text.index(end) + len(end):].lstrip("\n")
            else:
                text = text.rstrip() + "\n\n" + block
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(text, encoding="utf-8", newline="\n")
            return {"status": "synchronized", "output": str(output)}
