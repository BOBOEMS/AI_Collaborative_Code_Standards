"""Contract tests use isolated projects and fake native endpoints, never live chats."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from session_handover_tool import SessionClient, ToolError
from session_handover_tool import config
from session_handover_tool.api import session_key
from session_handover_tool.sessions import read, save
from session_handover_tool.adapters.codex_cli import build_command, metadata, process_alive
from session_handover_tool.adapters.base import observed

MODULE = Path(__file__).resolve().parents[1]
TEST_ROOT = Path(os.environ.get("SESSION_TOOL_TEST_ROOT") or ("C:/bobo_worktool/session-handover-tool/tests" if os.name == "nt" else tempfile.gettempdir() + "/session-handover-tool-tests"))


class FakeAgent:
    def __init__(self):
        self.sessions, self.calls, self.failures = {}, [], {}
        self.creation_error = None
        self.verification = {"identity": "native", "cwd": "native"}

    def create(self, target, runtime, **kwargs):
        self.calls.append(("create", kwargs["request_id"]))
        sid = str(uuid.uuid4())
        self.sessions[sid] = {"native_id": sid, "cwd": target["cwd"], "state": "idle", "verification": self.verification}
        if self.creation_error:
            raise ToolError("creation_unknown", "lost creation reply", uncertain=True, details={"native_id": sid})
        return copy.deepcopy(self.sessions[sid])

    def inspect(self, target, runtime):
        sid = target["native_id"]
        if sid not in self.sessions:raise ToolError("not_found", "missing native session")
        if self.sessions[sid]["cwd"] != target["cwd"]:raise ToolError("workspace_mismatch", "wrong native cwd")
        return copy.deepcopy(self.sessions[sid])

    def send(self, target, message, runtime, **kwargs):
        sid = target["native_id"]
        self.calls.append(("send", sid, message, copy.deepcopy(target)))
        if sid in self.failures:raise self.failures[sid]
        return {"accepted": True, "native_id": sid, "execution_complete": False}


class Sessions(unittest.TestCase):
    def setUp(self):
        TEST_ROOT.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="case-", dir=TEST_ROOT)
        self.base = Path(self.temporary.name)
        self.project = self.base/"project-中文"; self.project.mkdir()
        self.path = self.project/"sessions.json"
        self.data = {"schema_version": 1, "project_id": "project-one", "project_root": str(self.project),
            "runtime_dir": str(self.base/"runtime"), "profiles": {
                "default": {"adapter": "codex_cli", "cwd": ".", "native": {"model": "test-model", "reasoning_effort": "low"}, "connection": {}},
                "replacement": {"adapter": "codex_cli", "cwd": ".", "native": {"model": "other-model", "reasoning_effort": "high"}, "connection": {}}},
            "roles": {r: "default" for r in "ABCDE"}, "authorization": {"reference": "test-only authorization", "allow": sorted(config.MUTATIONS), "actors": ["test"]}}
        save(self.path, self.data)
        self.agent = FakeAgent()
        self.client = SessionClient(self.path, actor="test", adapters={"codex_cli": self.agent})

    def tearDown(self):self.temporary.cleanup()
    def edit(self, fn):
        data = read(self.path); fn(data); save(self.path, data)
    def create(self, role="D", milestone="M01", profile=None, **kwargs):
        return self.client.create(profile, milestone=milestone, role=role, **kwargs)["session"]
    def assertCode(self, code, call):
        with self.assertRaises(ToolError) as caught:call()
        self.assertEqual(code, caught.exception.code)
        return caught.exception
    def dispatch(self):
        c, a, d = self.create("C"), self.create("A"), self.create("D")
        self.client.send("任务：只输出确认 🧪", task_id="T01", milestone="M01", role="D", report_to=["C", "A"])
        return c, a, d

    def test_five_roles_and_two_milestones_have_distinct_native_ids(self):
        refs = [self.create(r, m) for m in ("M01", "release_two") for r in "ABCDE"]
        self.assertEqual(10, len({r["native_id"] for r in refs}))

    def test_no_role_overwrite(self):
        self.create(); self.assertCode("already_bound", self.create)
        self.assertEqual(1, len(self.agent.calls))

    def test_no_cross_milestone_or_role_reuse(self):
        ref = self.create()
        self.assertCode("session_reused", lambda:self.client.bind(ref["native_id"], milestone="M02", role="D"))

    def test_historical_session_cannot_be_reused_by_later_milestone(self):
        ref = self.create()
        self.client.switch(milestone="M01",role="D",profile="replacement")
        self.assertCode("session_reused",lambda:self.client.bind(ref["native_id"],"default",milestone="M02",role="D"))

    def test_registered_native_settings_cannot_be_overwritten_by_bind(self):
        ref = self.create()
        self.assertCode("session_conflict",lambda:self.client.bind(ref["native_id"],"replacement"))

    def test_runtime_rejects_second_unique_config_source(self):
        self.create()
        duplicate = self.project/"duplicate.json"; save(duplicate,read(self.path))
        other = SessionClient(duplicate,actor="test",adapters={"codex_cli":self.agent})
        self.assertCode("config_conflict",lambda:other.create("default"))

    def test_unknown_creation_blocks_duplicate_and_exact_recovery(self):
        self.agent.creation_error = True
        error = self.assertCode("creation_unknown", lambda:self.create(request_id="lost"))
        self.assertTrue(error.uncertain)
        self.assertCode("request_pending", self.create)
        sid = error.details["native_id"]
        self.client.bind(sid, milestone="M01", role="D", recover_request="lost")
        self.assertEqual("recovered", self.client.receipt("lost")["status"])
        self.assertEqual(1, len(self.agent.calls))

    def test_recovery_cannot_select_another_profile(self):
        self.agent.creation_error = True
        error = self.assertCode("creation_unknown", lambda:self.create(request_id="lost"))
        self.assertCode("invalid_recovery", lambda:self.client.bind(error.details["native_id"], "replacement", milestone="M01", role="D", recover_request="lost"))

    def test_repeated_request_does_not_create_twice(self):
        self.client.create("default", request_id="one")
        self.assertCode("already_attempted", lambda:self.client.create("default", request_id="one"))
        self.assertEqual(1, len(self.agent.calls))

    def test_unverified_binding_rejected_and_created_id_preserved(self):
        self.agent.verification = {"identity": "native", "cwd": "unverified"}
        error = self.assertCode("unverified_workspace", self.create)
        self.assertTrue(error.uncertain)
        self.assertIn("native_id", error.details)

    def test_workspace_mismatch_cannot_bind(self):
        ref = self.create()
        self.agent.sessions[ref["native_id"]]["cwd"] = str(self.base)
        self.assertCode("workspace_mismatch", lambda:self.client.bind(ref["native_id"], "default"))

    def test_switch_requires_idle_and_preserves_history(self):
        old = self.create()
        self.agent.sessions[old["native_id"]]["state"] = "running"
        self.assertCode("busy", lambda:self.client.switch(milestone="M01", role="D", profile="replacement"))
        self.agent.sessions[old["native_id"]]["state"] = "idle"
        new = self.client.switch(milestone="M01", role="D", profile="replacement")["session"]
        self.assertNotEqual(old["native_id"], new["native_id"])
        self.assertEqual(old["native_id"], read(self.path)["milestones"]["M01"]["history"][0]["session"]["native_id"])

    def test_unknown_stop_requires_explicit_handover(self):
        old = self.create(); self.agent.sessions[old["native_id"]]["state"] = "unknown"
        self.assertCode("state_unknown", lambda:self.client.switch(milestone="M01", role="D", profile="replacement"))
        self.client.switch(milestone="M01", role="D", profile="replacement", confirmed_stopped=True)

    def test_changed_model_requires_switch_before_dispatch(self):
        self.create()
        self.edit(lambda d:d["profiles"]["default"]["native"].update(model="changed"))
        self.assertCode("switch_required", lambda:self.client.send("x", task_id="T01", milestone="M01", role="D"))
        self.assertFalse(any(c[0] == "send" for c in self.agent.calls))

    def test_changed_milestone_profile_requires_switch_before_dispatch(self):
        self.create()
        self.edit(lambda d:d["milestones"]["M01"]["role_profiles"].update(D="replacement"))
        self.assertCode("switch_required",lambda:self.client.send("x",task_id="T01",milestone="M01",role="D"))

    def test_cli_init_is_readonly_and_never_overwrites(self):
        path = self.project/"initialized.json"
        command = [sys.executable,"-B",str(MODULE/"session_tool.py"),"--config",str(path),"init",
            "--project-id","initialized","--project-root",str(self.project),"--runtime-dir",str(self.base/"new-runtime")]
        first = subprocess.run(command,capture_output=True,encoding="utf-8")
        self.assertEqual(0,first.returncode,first.stdout + first.stderr)
        self.assertEqual([],read(path)["authorization"]["allow"])
        original = path.read_bytes()
        second = subprocess.run(command,capture_output=True,encoding="utf-8")
        self.assertEqual(2,second.returncode)
        self.assertEqual(original,path.read_bytes())

    def test_duplicate_task_is_never_resent(self):
        self.dispatch()
        self.assertCode("already_attempted", lambda:self.client.send("duplicate", task_id="T01", milestone="M01", role="D"))
        self.assertEqual(1, len([c for c in self.agent.calls if c[0] == "send"]))

    def test_unknown_dispatch_keeps_snapshot(self):
        ref = self.create(); self.agent.failures[ref["native_id"]] = ToolError("timeout", "unknown", uncertain=True)
        self.assertCode("timeout", lambda:self.client.send("x", task_id="T01", milestone="M01", role="D", request_id="send-lost"))
        self.assertEqual("unknown", self.client.receipt("send-lost")["status"])
        self.assertTrue(self.client.store.task_path("M01", "T01").exists())

    def test_report_frozen_recipient_after_switch(self):
        c, a, d = self.dispatch()
        replacement = self.client.switch(milestone="M01", role="C", profile="replacement")["session"]
        self.client.report(milestone="M01", task_id="T01", summary="完成", sender=session_key(d))
        sent = [call[1] for call in self.agent.calls if call[0] == "send"]
        self.assertIn(c["native_id"], sent); self.assertNotIn(replacement["native_id"], sent)

    def test_report_payload_has_data_without_scheduling(self):
        c, a, d = self.dispatch()
        self.client.report(milestone="M01", task_id="T01", summary="待审查", sender=session_key(d))
        payload = json.loads(self.agent.calls[-1][2])
        self.assertEqual("delivery_notification", payload["kind"])
        self.assertNotIn("next_milestone", payload)

    def test_partial_report_retries_only_definitive_failed_recipient(self):
        c, a, d = self.dispatch()
        self.agent.failures[a["native_id"]] = ToolError("busy", "not sent")
        first = self.client.report(milestone="M01", task_id="T01", summary="done", delivery_id="report1")
        self.assertEqual("partial", first["status"])
        del self.agent.failures[a["native_id"]]
        second = self.client.report(milestone="M01", task_id="T01", summary="done", delivery_id="report1")
        self.assertEqual("accepted", second["status"])
        sends = [call[1] for call in self.agent.calls if call[0] == "send"]
        self.assertEqual(1, sends.count(c["native_id"])); self.assertEqual(2, sends.count(a["native_id"]))

    def test_unknown_report_is_not_resent(self):
        c, a, d = self.dispatch()
        self.agent.failures[a["native_id"]] = ToolError("timeout", "lost reply", uncertain=True)
        self.client.report(milestone="M01", task_id="T01", summary="done", delivery_id="one")
        del self.agent.failures[a["native_id"]]
        result = self.client.report(milestone="M01", task_id="T01", summary="done", delivery_id="one")
        self.assertEqual("unknown", result["recipients"][session_key(a)]["status"])
        self.assertEqual(1, len([call for call in self.agent.calls if call[0] == "send" and call[1] == a["native_id"]]))

    def test_delivery_id_conflict(self):
        self.dispatch()
        self.client.report(milestone="M01", task_id="T01", summary="one", delivery_id="same")
        self.assertCode("delivery_conflict", lambda:self.client.report(milestone="M01", task_id="T01", summary="two", delivery_id="same"))

    def test_wrong_sender_rejected(self):
        self.dispatch()
        self.assertCode("wrong_sender", lambda:self.client.report(milestone="M01", task_id="T01", summary="x", sender="unrelated"))

    def test_endpoint_refresh_keeps_identity_and_native_settings(self):
        c, a, d = self.dispatch()
        self.edit(lambda d:d["profiles"]["default"]["connection"].update(pipe_path="new-local-pipe"))
        self.client.report(milestone="M01", task_id="T01", summary="done")
        self.assertEqual("new-local-pipe", self.agent.calls[-1][3]["connection"]["pipe_path"])
        self.assertEqual(a["native_id"], self.agent.calls[-1][1])

    def test_removed_profile_does_not_retarget_historical_report(self):
        c, a, d = self.dispatch()
        def change(data):
            data["roles"] = {r:"replacement" for r in "ABCDE"}
            data["milestones"]["M01"]["role_profiles"] = {r:"replacement" for r in "ACD"}
            del data["profiles"]["default"]
        self.edit(change)
        self.assertEqual("accepted", self.client.report(milestone="M01", task_id="T01", summary="historical")["status"])

    def test_authorization_and_actor_gate(self):
        other = SessionClient(self.path, actor="intruder", adapters={"codex_cli": self.agent})
        self.assertCode("not_authorized", lambda:other.create("default"))
        self.edit(lambda d:d["authorization"].update(reference=""))
        self.assertCode("not_authorized", self.create)
        self.assertEqual([], self.agent.calls)

    def test_project_runtime_isolation(self):
        self.create()
        second = self.base/"other"; second.mkdir()
        data = read(self.path); data["project_root"] = str(second); data.pop("sessions"); data.pop("milestones")
        path = second/"sessions.json"; save(path, data)
        other = SessionClient(path, actor="test", adapters={"codex_cli": self.agent})
        self.assertNotEqual(self.client.store.root, other.store.root)
        self.assertCode("not_bound", lambda:other.inspect(milestone="M01", role="D"))

    def test_sync_preserves_surrounding_prose_and_never_updates_roles_or_state(self):
        self.create()
        output = self.project/"SESSIONS.md"
        output.write_text("# 手工说明\n\n结论由人审核。\n", encoding="utf-8")
        for name in ("ROLES.md", "STATE.md"):(self.project/name).write_text("unchanged", encoding="utf-8")
        self.client.sync(str(output)); self.client.sync(str(output))
        self.assertEqual(1, output.read_text(encoding="utf-8").count("<!-- session-tool:start -->"))
        self.assertIn("结论由人审核", output.read_text(encoding="utf-8"))
        for name in ("ROLES.md", "STATE.md"):self.assertEqual("unchanged", (self.project/name).read_text())

    def test_sync_cannot_overwrite_config_or_write_outside_documents(self):
        self.assertCode("invalid_target", lambda:self.client.sync(str(self.path)))
        self.assertCode("invalid_target", lambda:self.client.sync(str(self.base/"outside.md")))
        self.assertCode("invalid_target", lambda:self.client.sync(str(self.project/"STATE.md")))

    def test_sync_rejects_orphan_end_marker(self):
        output = self.project/"SESSIONS.md"; output.write_text("<!-- session-tool:end -->")
        self.assertCode("invalid_target",lambda:self.client.sync(str(output)))

    def test_path_traversal_request_and_task_ids_rejected(self):
        self.assertCode("invalid_config", lambda:self.client.receipt("../escape"))
        self.assertCode("invalid_config", lambda:self.client.store.task_path("../M", "task"))

    def test_native_settings_do_not_leak_between_agents(self):
        data = copy.deepcopy(self.data)
        data["profiles"]["default"]["adapter"] = "antigravity"
        self.assertCode("invalid_native_settings", lambda:config.validate(data))

    def test_secret_values_rejected(self):
        data = copy.deepcopy(self.data); data["profiles"]["default"]["connection"]["secret"] = "not-a-real-secret"
        self.assertCode("invalid_config", lambda:config.validate(data))

    def test_unintegrated_adapter_is_explicit(self):
        self.edit(lambda d:d["profiles"].update(future={"adapter":"command_code", "native":{}, "cwd":"."}))
        self.assertCode("unsupported_adapter", lambda:SessionClient(self.path, actor="test").create("future"))

    def test_codex_command_resume_exact_id_and_no_bypass(self):
        target = config.target(self.data, "default"); target["native_id"] = str(uuid.uuid4())
        command = build_command(target)
        self.assertIn("resume", command); self.assertIn(target["native_id"], command)
        self.assertNotIn("--last", command); self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", command)
        self.assertEqual(["--json", "-"], command[-2:])

    def test_codex_metadata_validates_native_workspace(self):
        home = self.base/"codex"; (home/"sessions").mkdir(parents=True)
        sid = str(uuid.uuid4()); path = home/"sessions"/(sid + ".jsonl")
        path.write_text(json.dumps({"type":"session_meta", "payload":{"id":sid,"cwd":str(self.base)}}) + "\n")
        target = config.target(self.data, "default"); target.update(native_id=sid, connection={"codex_home":str(home)})
        self.assertCode("workspace_mismatch", lambda:metadata(target))

    def test_native_unknown_state_is_not_idle(self):
        self.assertEqual("unknown", observed({"running":None})["state"])
        self.assertEqual("unknown", observed({"status":"NEW_UNKNOWN_ENUM"})["state"])

    def test_windows_process_observation(self):
        self.assertTrue(process_alive(os.getpid()))

    def test_cli_works_from_unrelated_directory_with_unicode_config(self):
        process = subprocess.run([sys.executable, "-B", str(MODULE/"session_tool.py"), "--config", str(self.path), "validate"],
            cwd=self.base, capture_output=True, encoding="utf-8")
        self.assertEqual(0, process.returncode, process.stdout + process.stderr)
        self.assertTrue(json.loads(process.stdout)["valid"])


if __name__ == "__main__":unittest.main()
