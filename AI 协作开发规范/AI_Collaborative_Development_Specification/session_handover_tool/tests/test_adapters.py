import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from session_handover_tool import ToolError
from session_handover_tool import SessionClient
from session_handover_tool.sessions import save
from session_handover_tool.adapters.base import bridge
from session_handover_tool.adapters.codex_app import AppTools, CodexApp
from session_handover_tool.adapters.deepseek_harness import DeepSeekHarness
from session_handover_tool.adapters.native.antigravity_rpc import Antigravity, select_catalog

TEST_ROOT = Path(os.environ.get("SESSION_TOOL_TEST_ROOT") or ("C:/bobo_worktool/session-handover-tool/tests" if os.name == "nt" else tempfile.gettempdir() + "/session-handover-tool-tests"))
NODE = shutil.which("node")


class NativeContracts(unittest.TestCase):
    def setUp(self):
        TEST_ROOT.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="native-", dir=TEST_ROOT)
        self.root = Path(self.temporary.name)
        self.calls, self.running, self.selected, self.reject_rename = [], False, {}, False
        self.cursor, self.turns, self.events, self.force_unauthorized = 4, 0, [], False
        self.sid = "session-" + str(uuid.uuid4())
        owner = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):pass
            def do_POST(self):
                data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                if owner.force_unauthorized:
                    self.send_response(401); self.end_headers(); self.wfile.write(b'Unauthorized'); return
                endpoint = self.path.removeprefix("/api/")
                if self.path.startswith("/api/"):
                    args = data["payload"]["args"]; owner.calls.append((endpoint, args))
                    if endpoint == "workspace/create":value = {"workspace":{"workspaceId":"workspace-test"}}
                    elif endpoint == "session/create":value = {"sessionId":owner.sid}
                    elif endpoint == "session/rename" and owner.reject_rename:
                        self.send_response(503); self.end_headers(); return
                    elif endpoint == "session/list":value = {"items":[{"sessionId":owner.sid,"cwd":str(owner.root),"running":owner.running}]}
                    elif endpoint == "session/projections":value = {"asOfSeq":owner.cursor,"values":{"modelSelection":owner.selected,"sessionStats":{"turns":owner.turns}}}
                    elif endpoint == "session/page":value = {"records":owner.events,"hasMore":False}
                    elif endpoint == "session/selectModel":
                        owner.selected = {k:v for k,v in args["request"].items() if k != "sessionId"}
                        value = {"selected":owner.selected}
                    elif endpoint == "session/prompt":value = {"accepted":True}
                    else:value = {}
                    response = {"type":"server-response","result":{"ok":True,"value":value}}
                else:
                    endpoint = self.path.rsplit("/",1)[-1]; owner.calls.append((endpoint,data))
                    if endpoint == "GetUserStatus":response = owner.catalog
                    elif endpoint == "StartCascade":response = {"cascadeId":data["cascadeId"]}
                    elif endpoint == "GetConversationMetadata":response = {"metadata":{"projectId":"native-project","workspaces":[{"workspaceFolderAbsoluteUri":owner.root.as_uri()}]}}
                    elif endpoint == "GetAllCascadeTrajectories":response = {"trajectorySummaries":{owner.anti_sid:{"status":"CASCADE_RUN_STATUS_IDLE"}}}
                    elif endpoint == "GetCascadeTrajectory":response = {"trajectory":{}}
                    else:response = {}
                body = json.dumps(response).encode()
                self.send_response(200); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)
        self.server = ThreadingHTTPServer(("127.0.0.1",0),Handler)
        self.handler = Handler
        self.thread = threading.Thread(target=self.server.serve_forever,daemon=True); self.thread.start()
        self.authority = "127.0.0.1:" + str(self.server.server_port)
        credential = self.root/"test-credential.yaml"
        credential.write_text("secret: " + "A"*43, encoding="utf-8")
        self.target = {"adapter":"deepseek_harness","native_id":self.sid,"cwd":str(self.root),"native":{
            "provider":"fixture-provider","model":"fixture-model","reasoning_effort":"fixture-effort"},
            "connection":{"authority":self.authority,"credentials":str(credential),"node":NODE or "node"}}
        self.anti_sid = str(uuid.uuid4())
        self.catalog = {"userStatus":{"cascadeModelConfigData":{"clientModelConfigs":[{
            "modelId":"fixture-id","label":"Fixture High","modelOrAlias":{"model":"FIXTURE_NATIVE"}}]}}}
        self.anti_target = {"model":"fixture-id","model_label":"Fixture High","native_model":"FIXTURE_NATIVE",
            "cwd":str(self.root),"driver":{"project_id":"native-project"}}

    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join(timeout=2); self.temporary.cleanup()

    @unittest.skipUnless(NODE, "Node.js is unavailable")
    def test_deepseek_create_select_inspect_and_unicode_dispatch(self):
        agent = DeepSeekHarness()
        created = agent.create({k:v for k,v in self.target.items() if k != "native_id"}, self.root,
            request_id="create-test",title="隔离验证 🧪",message="")
        self.assertEqual(self.sid, created["native_id"])
        self.assertEqual("idle", created["state"])
        result = agent.send(self.target,"只回复确认，禁止读写文件 🧪",self.root,request_id="send-test")
        self.assertTrue(result["accepted"])
        prompt = next(args["request"] for endpoint,args in self.calls if endpoint == "session/prompt")
        self.assertIn("🧪",prompt["content"][0]["text"])
        self.assertEqual("UTC",prompt["clientTimeZone"])
        self.assertEqual("fixture-effort", self.selected["reasoningEffort"])
        created_args=next(args["request"] for endpoint,args in self.calls if endpoint=="session/create")
        self.assertEqual("workspace-test",created_args["workspaceId"])

    @unittest.skipUnless(NODE, "Node.js is unavailable")
    def test_deepseek_partial_create_retains_native_identity(self):
        self.reject_rename = True
        with self.assertRaises(ToolError) as caught:
            DeepSeekHarness().create(self.target,self.root,request_id="partial",title="test",message="")
        self.assertTrue(caught.exception.uncertain)
        self.assertEqual(self.sid,caught.exception.details["native_id"])
        self.assertEqual(1,len([x for x in self.calls if x[0] == "session/create"]))

    @unittest.skipUnless(NODE, "Node.js is unavailable")
    def test_deepseek_running_never_selects_or_sends(self):
        self.running = True
        with self.assertRaises(ToolError) as caught:DeepSeekHarness().send(self.target,"x",self.root,request_id="busy")
        self.assertEqual("busy",caught.exception.code)
        self.assertFalse(any(endpoint in ("session/selectModel","session/prompt") for endpoint,_ in self.calls))

    def native_events(self, turn=1, dispatch="fixture-send", reason="completed"):
        self.cursor,self.turns=9,turn
        self.events=[{"type":"event","event":{"type":kind,"seq":seq,"data":data}} for kind,seq,data in (
            ("turn/start",5,{"turn":turn}),
            ("request/header",6,{"header":"PRIVATE_FAKE_HEADER"}),
            ("user/message",7,{"content":[{"type":"text","text":"测试 🧪"}],"source":{"kind":"user","rpcId":dispatch}}),
            ("assistant/message",8,{"turn":turn,"message":{"content":[{"type":"text","text":"成功 🧪"}]}}),
            ("turn/end",9,{"turn":turn,"reason":{"kind":reason}}))]

    @unittest.skipUnless(NODE, "Node.js is unavailable")
    def test_deepseek_route_a_auto_discovery_authenticates_dynamic_port(self):
        target=json.loads(json.dumps(self.target)); target["connection"].pop("authority")
        target["connection"]["discovery_ports"]=[self.server.server_port]
        with patch.dict(os.environ,{},clear=False):
            os.environ.pop("DSH_AUTHORITY",None)
            result=DeepSeekHarness().probe(target,self.root)
        self.assertEqual(self.authority,result["authority"])
        self.assertEqual("auto_discovery",result["discovery_source"])
        self.assertTrue(result["connected"])

    @unittest.skipUnless(NODE, "Node.js is unavailable")
    def test_deepseek_environment_authority_and_explicit_precedence(self):
        target=json.loads(json.dumps(self.target)); target["connection"].pop("authority")
        with patch.dict(os.environ,{"DSH_AUTHORITY":self.authority}):
            result=DeepSeekHarness().probe(target,self.root)
        self.assertEqual("environment",result["discovery_source"])
        with patch.dict(os.environ,{"DSH_AUTHORITY":"127.0.0.1:1"}):
            result=DeepSeekHarness().probe(self.target,self.root)
        self.assertEqual("configured",result["discovery_source"])

    @unittest.skipUnless(NODE, "Node.js is unavailable")
    def test_deepseek_stale_explicit_endpoint_does_not_fall_back_and_mutate_another_host(self):
        import socket
        with socket.socket() as reserved:
            reserved.bind(("127.0.0.1",0)); closed_port=reserved.getsockname()[1]
        target=json.loads(json.dumps(self.target))
        target["connection"].update(authority="127.0.0.1:"+str(closed_port),discovery_ports=[self.server.server_port])
        with self.assertRaises(ToolError) as caught:
            DeepSeekHarness().create({k:v for k,v in target.items() if k!="native_id"},self.root,
                request_id="stale-host-create",title="must not create elsewhere",message="")
        self.assertEqual("backend_unavailable",caught.exception.code)
        self.assertFalse(self.calls)

    @unittest.skipUnless(NODE, "Node.js is unavailable")
    def test_deepseek_multiple_hosts_require_explicit_selection(self):
        second=ThreadingHTTPServer(("127.0.0.1",0),self.handler)
        thread=threading.Thread(target=second.serve_forever,daemon=True); thread.start()
        try:
            target=json.loads(json.dumps(self.target)); target["connection"].pop("authority")
            target["connection"]["discovery_ports"]=[self.server.server_port,second.server_port]
            with patch.dict(os.environ,{},clear=False):
                os.environ.pop("DSH_AUTHORITY",None)
                with self.assertRaises(ToolError) as caught:DeepSeekHarness().probe(target,self.root)
            self.assertEqual("ambiguous_host",caught.exception.code)
            self.assertEqual(2,len(caught.exception.details["authorities"]))
            self.assertFalse(any(method in ("workspace/create","session/create","session/prompt") for method,_ in self.calls))
        finally:second.shutdown();second.server_close();thread.join(timeout=2)

    @unittest.skipUnless(NODE, "Node.js is unavailable")
    def test_deepseek_http_401_alone_is_not_an_authenticated_host(self):
        self.force_unauthorized=True
        target=json.loads(json.dumps(self.target)); target["connection"].pop("authority")
        target["connection"]["discovery_ports"]=[self.server.server_port]
        with patch.dict(os.environ,{},clear=False):
            os.environ.pop("DSH_AUTHORITY",None)
            with self.assertRaises(ToolError) as caught:DeepSeekHarness().probe(target,self.root)
        self.assertEqual("backend_unavailable",caught.exception.code)

    @unittest.skipUnless(NODE, "Node.js is unavailable")
    def test_deepseek_default_credential_locator_uses_dsh_home(self):
        (self.root/".credentials.yaml").write_text("secret: "+"A"*43)
        target=json.loads(json.dumps(self.target)); target["connection"].pop("credentials")
        target["connection"]["dsh_home"]=str(self.root)
        with patch.dict(os.environ,{},clear=False):
            os.environ.pop("DSH_CREDENTIAL_FILE",None)
            self.assertTrue(DeepSeekHarness().probe(target,self.root)["connected"])

    @unittest.skipUnless(NODE, "Node.js is unavailable")
    def test_deepseek_reads_native_text_and_filters_request_headers(self):
        self.native_events()
        result=DeepSeekHarness().read(self.target,self.root,include_events=True)
        self.assertEqual("成功 🧪",result["assistant"])
        self.assertEqual("fixture-send",result["messages"][0]["request_id"])
        self.assertNotIn("PRIVATE_FAKE_HEADER",json.dumps(result))

    @unittest.skipUnless(NODE, "Node.js is unavailable")
    def test_deepseek_wait_rejects_idle_without_fresh_turn_end(self):
        ack=DeepSeekHarness().send(self.target,"测试",self.root,request_id="fixture-send")
        result=DeepSeekHarness().wait(self.target,self.root,timeout_seconds=0,dispatch=ack)
        self.assertTrue(result["timed_out"])
        self.assertTrue(result["idle"])
        self.assertFalse(result["turn_ended"])
        self.assertIsNone(result["execution_succeeded"])

    @unittest.skipUnless(NODE, "Node.js is unavailable")
    def test_deepseek_wait_accepts_fast_completed_turn_without_running_sample(self):
        ack=DeepSeekHarness().send(self.target,"测试",self.root,request_id="fixture-send")
        self.native_events()
        result=DeepSeekHarness().wait(self.target,self.root,timeout_seconds=0,dispatch=ack)
        self.assertTrue(result["turn_ended"])
        self.assertTrue(result["execution_succeeded"])
        self.assertEqual("native_request_id",result["request_association"])

    @unittest.skipUnless(NODE, "Node.js is unavailable")
    def test_deepseek_wait_does_not_reassociate_replayed_context_with_later_turn(self):
        ack=DeepSeekHarness().send(self.target,"测试",self.root,request_id="fixture-send")
        self.native_events(turn=2)
        result=DeepSeekHarness().wait(self.target,self.root,timeout_seconds=0,dispatch=ack)
        self.assertFalse(result["turn_ended"])
        self.assertTrue(result["timed_out"])

    @unittest.skipUnless(NODE, "Node.js is unavailable")
    def test_deepseek_native_error_end_is_not_success(self):
        ack=DeepSeekHarness().send(self.target,"测试",self.root,request_id="fixture-send")
        self.native_events(reason="failed")
        result=DeepSeekHarness().wait(self.target,self.root,timeout_seconds=0,dispatch=ack)
        self.assertTrue(result["turn_ended"])
        self.assertFalse(result["execution_succeeded"])

    @unittest.skipUnless(NODE, "Node.js is unavailable")
    def test_deepseek_wait_and_read_are_bounded(self):
        with self.assertRaises(ToolError) as caught:DeepSeekHarness().wait(self.target,self.root,timeout_seconds=46)
        self.assertEqual("invalid_request",caught.exception.code)
        with self.assertRaises(ToolError):DeepSeekHarness().read(self.target,self.root,limit=1001)

    @unittest.skipUnless(NODE, "Node.js is unavailable")
    def test_deepseek_cli_probe_read_and_wait_on_native_fixture(self):
        config=self.root/"sessions.json"
        save(config,{"schema_version":1,"project_id":"native-cli","project_root":str(self.root),"runtime_dir":str(self.root/"runtime"),
            "profiles":{"gui":{"adapter":"deepseek_harness","cwd":".","native":self.target["native"],"connection":self.target["connection"]}},
            "authorization":{"reference":"test-only","allow":["bind","send"]}})
        client=SessionClient(config)
        bound=client.bind(self.sid,"gui",request_id="bind-one")
        client.send("test",session=bound["session"],task_id="T01",request_id="fixture-send")
        self.native_events()
        tool=Path(__file__).resolve().parents[1]/"session_tool.py"
        for command in (["probe","--profile","gui"],["read","--session","deepseek_harness:"+self.sid,"--events"],
                        ["wait","--request-id","fixture-send","--timeout","0"]):
            with self.subTest(command=command):
                result=subprocess.run([sys.executable,"-B",str(tool),"--config",str(config),*command],capture_output=True,encoding="utf-8")
                self.assertEqual(0,result.returncode,result.stdout+result.stderr)
                data=json.loads(result.stdout)
                if command[0]=="wait":self.assertTrue(data["execution_succeeded"])
                if command[0]=="read":self.assertEqual("成功 🧪",data["assistant"])

    def test_antigravity_native_variant_catalog(self):
        self.assertEqual("FIXTURE_NATIVE", select_catalog(self.anti_target,self.catalog)["native_model"])
        self.catalog["userStatus"]["cascadeModelConfigData"]["clientModelConfigs"][0]["modelOrAlias"]["model"] = "CHANGED"
        with self.assertRaises(ToolError):select_catalog(self.anti_target,self.catalog)

    def test_antigravity_rpc_workspace_and_native_model_fields(self):
        with patch.dict(os.environ,{"ANTIGRAVITY_LS_ADDRESS":"http://"+self.authority,"ANTIGRAVITY_CSRF_TOKEN":"fixture-only"}):
            result = Antigravity(self.anti_target).send(self.anti_sid,"确认 🧪")
        self.assertTrue(result["accepted"])
        sent = next(body for method,body in self.calls if method == "SendUserCascadeMessage")
        self.assertEqual("FIXTURE_NATIVE",sent["cascadeConfig"]["plannerConfig"]["planModel"])
        self.assertEqual("确认 🧪",sent["items"][0]["text"])

    def test_antigravity_exhausted_model_does_not_block_stop_inspection(self):
        self.catalog["userStatus"]["cascadeModelConfigData"]["clientModelConfigs"][0]["disabled"] = True
        with patch.dict(os.environ,{"ANTIGRAVITY_LS_ADDRESS":"http://"+self.authority,"ANTIGRAVITY_CSRF_TOKEN":"fixture-only"}):
            result = Antigravity(self.anti_target).inspect(self.anti_sid)
            with self.assertRaises(ToolError):Antigravity(self.anti_target).send(self.anti_sid,"must not send")
        self.assertEqual("CASCADE_RUN_STATUS_IDLE",result["status"])
        self.assertEqual("model_unavailable",result["model_catalog_error"]["code"])
        self.assertFalse(any(method == "SendUserCascadeMessage" for method,_ in self.calls))

    def test_bridge_timeout_retains_intermediate_created_id(self):
        partial = (json.dumps({"created":True,"session_id":self.sid}) + "\n").encode()
        with patch("subprocess.run",side_effect=subprocess.TimeoutExpired("fixture",1,output=partial)):
            with self.assertRaises(ToolError) as caught:bridge(["unused"],self.target,"create",runtime=self.root)
        self.assertTrue(caught.exception.uncertain)
        self.assertEqual(self.sid,caught.exception.details["native_id"])

    def test_bridge_known_failure_not_unknown(self):
        result = subprocess.CompletedProcess([],1,stdout=b'{"ok":false,"code":"busy","message":"idle required","uncertain":false}\n')
        with patch("subprocess.run",return_value=result):
            with self.assertRaises(ToolError) as caught:bridge(["unused"],self.target,"send",runtime=self.root)
        self.assertFalse(caught.exception.uncertain)

    @unittest.skipUnless(NODE, "Node.js is unavailable")
    def test_app_jsonrpc_handshake_and_unicode_arguments(self):
        target = {"cwd":str(self.root),"connection":{"node":NODE,"server_script":str(Path(__file__).parent/"fixtures/app_tools.cjs"),"pipe_path":"fixture-pipe","pipe_path_env":"UNSET_TEST_PIPE"}}
        with AppTools(target) as host:
            result = host.call("send_message_to_thread",{"threadId":str(uuid.uuid4()),"prompt":"中文 🧪 $()"})
        self.assertEqual("中文 🧪 $()",result["echoed"])

    @unittest.skipUnless(NODE, "Node.js is unavailable")
    def test_app_native_metadata_and_idle_state(self):
        target = {"adapter":"codex_app","native_id":str(uuid.uuid4()),"cwd":str(self.root),"native":{"inherit_model":True},
            "connection":{"node":NODE,"server_script":str(Path(__file__).parent/"fixtures/app_tools.cjs"),
                "pipe_path":"fixture-pipe","pipe_path_env":"UNSET_TEST_PIPE","codex_home":str(self.root/"empty-home")}}
        result = CodexApp().inspect(target,self.root)
        self.assertEqual("idle",result["state"])
        self.assertEqual("app_tools",result["verification"]["workspace_source"])

    def test_app_creation_explicitly_unsupported(self):
        with self.assertRaises(ToolError) as caught:CodexApp().create()
        self.assertEqual("unsupported",caught.exception.code)


if __name__ == "__main__":unittest.main()
