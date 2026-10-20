# DeepSeek Harness 路线 A

适用模块版本：`1.1.0`。2026-10-20 完成原脚本和集成后的真实开发测试，2026-10-21 整理交付。

此适配器连接正在运行的 Harness GUI 宿主，通过其本机 HTTP API 操作 GUI 内的 workspace/session。模型推理由 GUI 使用自己的认证与 provider 设置执行；调用方不需要配置模型 API Key。统一入口仍需 Python 3.10+，原生桥接需要 Node.js 18+，仅使用内置库。

## 实现来源和入口

按用户提供的 `C:/bobo_document/temp/agent开发/deepseek harness启动方式.md` 中路线 A 集成，参考该文档同目录 `agent-hub/scripts/` 下的 `discover-dsh-host.cjs`、`dsh-host-client.cjs`、`dsh-drive.cjs`。先运行原脚本确认真实回复，再实现本模块并实测。

| 文件 | 职责 |
|---|---|
| [adapters/deepseek_harness.py](adapters/deepseek_harness.py) | 统一 Python 适配器入口 |
| [adapters/native/dsh_discovery.cjs](adapters/native/dsh_discovery.cjs) | 本机端口发现、宿主认证筛选和多宿主拒绝 |
| [adapters/native/dsh_host_client.cjs](adapters/native/dsh_host_client.cjs) | 浏览器会话认证、原生 HTTP 调用、历史解析和有限等待 |
| [adapters/native/deepseek_desktop.cjs](adapters/native/deepseek_desktop.cjs) | create/inspect/send/probe/read/wait 命令桥接 |

这些文件随模块提供，运行时不依赖上述临时目录、`agent-hub` 或旧 Reuse_RTU 工具。创建通过 `workspace/create` 返回的 `workspaceId` 调用 `session/create`，保持 GUI 工作区归组；不从外部改写 GUI 的 `workspace.json`。

## 配置

在业务项目唯一 `project.sessions.json` 的 `profiles` 中加入以下 profile。`cwd` 相对该配置的 `project_root`，目录须已存在。以下 provider/model/effort 是本次实测值，其他选择应填写当前 Harness 支持的原生值。

```json
"dsh-flash": {
  "adapter": "deepseek_harness",
  "cwd": ".",
  "native": {
    "provider": "cmdc",
    "model": "deepseek/deepseek-v4.1-flash",
    "reasoning_effort": "max"
  },
  "connection": {"node": "node", "time_zone": "Asia/Shanghai"}
}
```

新配置仍按 [README](README.md) 填写 `project_id/project_root/runtime_dir/sessions/authorization` 等公共字段。查询无需写动作授权；创建和发送须有项目中登记的实际用户授权，示例不能代替授权依据。

宿主选择顺序：

1. `connection.authority`，格式只接受 `127.0.0.1:port`。
2. `connection.authority_env` 指定的环境变量，未指定时读取 `DSH_AUTHORITY`。
3. 自动发现。Windows 优先从 `netstat.exe` 读取本机监听端口；无法取得候选时使用来源脚本的历史端口区间。探测只向 loopback 发只读请求，再用浏览器会话认证验证原生 `session/list` 结构。401 响应本身不足以判定宿主。

发现多个已认证宿主返回 `ambiguous_host` 及候选地址，调用者显式选择。显式或环境地址失效会直接报错，不转向其他宿主重做创建或发送。`connection.discovery_ports` 可限制自动发现候选，为 1～1024 个合法端口的数组；不指定时按上述默认发现。

凭据文件定位顺序：显式 `connection.credentials`；`connection.credentials_env` 指定的环境变量（显式配置后未设置会拒绝）；未配置前两项时读取 `DSH_CREDENTIAL_FILE`；最后读取 `connection.dsh_home`、`DSH_HOME` 或 `~/.dsh` 下的 `.credentials.yaml`。只提取用于本机浏览器会话 cookie 的签名字段，cookie 绑定所选宿主地址，不提取模型 Key 字段，不把凭据值写入配置、回执或日志。

仅接入路线 A，不启动路线 B 推理进程，也不自动设置模型 Key、改写 provider 配置或在失败时切换到其他 Agent。

## 调用及结果判定

以下命令的路径按实际业务项目修改。先开启 Harness GUI 并完成其自身认证。

```powershell
$tool = 'C:/bobo_document/work/代码规范/AI 协作开发规范/AI_Collaborative_Development_Specification/session_handover_tool/session_tool.py'
$cfg = 'C:/projects/sample/AI/project.sessions.json'
python -B $tool --config $cfg probe --profile dsh-flash

# 只创建空闲会话；记录返回 session.native_id
python -B $tool --config $cfg create --profile dsh-flash --title 'Sample worker' --request-id sample-create-01
$session = 'deepseek_harness:REAL_NATIVE_SESSION_ID'
python -B $tool --config $cfg send --session $session --task-id T01 --message-file C:/projects/sample/AI/task.txt --request-id sample-send-01

# 查询原请求，不重复 send；超时后可再次执行同一 wait
python -B $tool --config $cfg wait --request-id sample-send-01 --timeout 30
python -B $tool --config $cfg read --session $session --limit 1000 --events
```

角色方式可以用 `--milestone M01 --role D` 替换 `--session`，由项目配置决定 D 的 profile。已有绑定换 Agent/模型沿公共 `switch` 流程处理；`send` 不能绕过绑定设置变化。

```python
from session_handover_tool import SessionClient

client = SessionClient("C:/projects/sample/AI/project.sessions.json")
created = client.create("dsh-flash", title="Sample worker", request_id="sample-create-01")
session = "deepseek_harness:" + created["native_id"]
sent = client.send("执行已获批任务并报告实际结果。", session=session,
                   task_id="T01", request_id="sample-send-01")
result = client.wait(request_id=sent["request_id"], timeout_seconds=30)
# result["timed_out"] 为真时，后续继续 wait 同一 request_id。
history = client.read(session=session, limit=1000, include_events=True)
```

命令和 Python 示例是两种替代用法；不要把同一创建/派发执行两次。创建不发送初始任务，忙状态下发送会被拒绝；派发采用原生 `queue`。本模块未开放 cancel、steer、archive、fork 等控制能力。

| 结果 | 可得出的结论 |
|---|---|
| `probe.connected=true` | 选定宿主的认证只读调用成功，未创建或发送 |
| `send.status=accepted` | 宿主接受消息；回执固定原会话、原生基线 cursor、预计 turn 和 dispatch ID |
| `wait --request-id` 的 `turn_ended=true`、`idle=true` | 基线之后的对应 turn 已结束，且当前原生会话空闲 |
| `execution_succeeded=true` | 该原生 turn 的结束原因为 `completed`；代码正确性仍需读取产物和独立核验 |
| `request_association=native_request_id` | 历史中的用户消息 rpcId 与本次派发匹配；原生关联不可见时标为 `expected_turn` |
| `timed_out=true` | 本次有限等待尚未取得完成证据；不代表失败或未执行，不触发重发 |
| 不带 request ID 的 `wait` | 仅观察当前空闲，`execution_succeeded=null`，不能归因到某个任务 |

单次 `wait` 的观察窗口为 0～45 秒，不是后台定时器。查询本身成功时 CLI 返回 0，包括 `timed_out=true`；自动化必须检查结果字段。按请求等待固定原派发会话，角色后来切换不改变等待对象；同时指定了不一致会话会拒绝。未知或未确认的派发不能通过 `wait` 自动转成已确认派发。

`read` 的 limit 为 1～1000 条原生记录，返回文本消息、turn 结束摘要、cursor 和 `has_more`。默认不输出原始事件；`--events` 只附加 message/tool/turn/step 类事件，不附加 request/header/system 消息。长任务可能截断，应检查 `has_more`，本版未提供向前翻页接口。等待使用最多 1000 条记录及回执中的预计 turn；缺少对应结束证据时保持未完成，不用暂时空闲推断成功。证据可能包含业务任务和工具输出，保存位置由项目决定。

## 实测结果与证据

本次使用已运行的 Windows GUI 宿主，按用户文档所述的路线 A 协议驱动；不把文档中 CLI 版本号当作已验证的 GUI 包版本号。真实验证配置未填写固定端口或凭据文件路径，调用者未设置 `CMDC_API_KEY`。原脚本和集成模块都成功自动发现当前 GUI。

- 原脚本创建专用会话并实际返回 `DSH_ROUTE_A_REFERENCE_OK`，原生 `lastUsed` 为 `cmdc / deepseek/deepseek-v4.1-flash / max`。
- 集成后创建另一个独立 GUI workspace/session，实际读取任务、修复 Python 分块函数、执行失败基线与修复后测试、生成报告。基线 11 个测试方法含 15 个失败子项和 1 个错误；修复后外层独立复测 **11 项通过**。审阅原生历史，存在 9 次实际工具调用。
- 文件哈希核验：仅获准的 `chunking.py` 与新建 `RESULT.md` 改变，测试文件和任务约定保持不变。报告中的基线、修复后命令及退出结果与独立证据一致。
- 第一轮等待曾在任务运行时超时；未重发，继续查询原请求，最终确认 turn 1 原生正常结束。随后同一会话实际完成第二轮复核回复 `DSH_ROUTE_A_REVIEW_OK`，文件保持不变；两轮都通过原生 request ID 关联，最终空闲、实际模型/强度保持上述设置。
- 模块自动测试 **68 项通过**；覆盖动态端口、认证筛选、显式地址失效不转发、多宿主拒绝、原生消息解析、暂时空闲、快速完成、失败结束、重放上下文不误关联，以及角色切换后等待原请求等契约。多宿主和失效转发场景使用模拟端点。

原始材料在 `C:/bobo_worktool/session-handover-tool/validation/20261020/deepseek-route-a/`，不提交真实会话配置、ID 或认证材料：

| 材料 | 内容 |
|---|---|
| `reference-stdout.json` / `reference-page.json` | 原脚本实际回复及原生模型观测 |
| `module-probe.json` / `created.json` / `sent.json` | 集成后的发现、创建和派发回执 |
| `wait-latest.json` / `history-latest.json` | 第一轮结束、真实工具执行及回复 |
| `baseline-unittest.log` / `independent-unittest.log` | 失败基线和外层独立复测 |
| `baseline-files.json` / `independent-verification.json` | 允许修改范围、模型及执行核验 |
| `followup-sent.json` / `followup-wait.json` / `final-verification.json` | 同会话第二轮、结束关联和最终文件哈希核验 |
| `cli-final-wait.json` | 从无关工作目录调用 CLI，读取同一第二轮的原生完成证据 |
| `module-unittest-final.log` / `static-checks.json` | 模块自动测试与语法/样例检查 |
| `project.sessions.json` / `runtime/` / `module-workspace/` | 专用验证配置、请求/任务快照和实际开发产物 |

覆盖限于上述模型的两轮隔离开发/复核任务。其他模型、额度耗尽后的真实替换、跨 Agent 多接收者回报、取消/steer 和完整项目工作流未由本次实测证明。GUI 私有接口升级后应重新验证。四通道既有证据及其边界见 [VALIDATION.md](VALIDATION.md)。
