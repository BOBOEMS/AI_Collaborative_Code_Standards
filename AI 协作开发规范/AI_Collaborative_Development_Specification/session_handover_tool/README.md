# 独立会话调用工具

此模块提供 Python API 和 CLI，按项目配置调用各 Agent 的原生会话。支持直接会话调用，以及“里程碑＋A/B/C/D/E”调用；负责身份核验、登记、显式派发、替换绑定和回报送达。流程安排、用户审批、Git 交付检查、审核结论及里程碑推进由调用者按[工作流规范](../多AI会话工作流规范.md)处理。

从 Reuse_RTU 的 `6.Tools/agents/` 提取已有原生调用方式，移除板卡、H 阶段、固定 C/D、固定模型和本机绑定。原项目工具及现行绑定未迁移、未修改。本模块运行时不读取旧项目配置。

## 文件入口

| 入口 | 用途 |
|---|---|
| [session_tool.py](session_tool.py) | 独立 CLI，可从任意工作目录以绝对路径运行 |
| [api.py](api.py) | `SessionClient` 公共 Python API |
| [examples/project.sessions.example.json](examples/project.sessions.example.json) | 四种适配器配置样例，默认只读，原生目录项及连接位置须按本机填写 |
| [adapters/](adapters/) | 分类适配器和 `native/` 桥接，不含项目流程调度 |
| [tests/](tests/) | stdlib unittest、隔离项目、本地模拟原生端点；固定样例在 `fixtures/` |
| [VALIDATION.md](VALIDATION.md) | 真实验证结果、支持边界和未验证项 |

需要 Python 3.10+，核心无需第三方 Python 包。Antigravity 另需 PowerShell 7；DeepSeek Harness/App Tools 另需 Node.js 和对应已认证的桌面服务。运行数据及测试临时目录默认放在 `C:/bobo_worktool/session-handover-tool/`，不写入协议目录。不需要把整套协议复制到业务项目。

## 原生能力与边界

| 适配器 | 创建 | 绑定/检查 | 发送及设置 |
|---|---|---|---|
| `codex_cli` | 初始消息启动首轮推理，返回真实 ID | 原生会话文件核验 ID/cwd；自有 worker 保存退出证据 | 精确 `exec resume ID`，消息走 stdin；原生模型、强度及可选上下文/压缩配置 |
| `codex_app` | 本版不提供，宿主创建后绑定 | 原生 `read_thread`，可用时补充本地模型观测 | 通过本机 App Tools 的 `send_message_to_thread`；不新启第二个推理 CLI |
| `antigravity` | `StartCascade` 创建空闲会话 | 原生项目、workspace、状态、模型目录和生成器元数据 | `SendUserCascadeMessage`；精确选择原生目录变体，High/Thinking 不转换成通用 effort |
| `deepseek_harness` | 桌面 API 建 workspace/session | 原生 ID、cwd、运行状态、modelSelection | `selectModel` 后 `session/prompt`；保留原生 provider/model/reasoningEffort |
| `command_code`、`grok` | — | — | 明确未接入，不退回其他 Agent |

Antigravity/Harness 创建不发送任务；传创建消息会拒绝，随后显式 `send`。Codex CLI 必须有初始消息，建议仅用于读入口和确认待命；正式任务再以 `task_id` 派发。CLI 的 `title` 不调用原生重命名接口。

`switch` 先确认旧会话停止，再创建或绑定替代会话、保留历史。本版不在原会话中修改模型、不主动停止进程、不迁移上下文。修改 profile 后不能用 `send` 绕过切换。

## 配置及文档归属

项目维护一份唯一结构化配置，例如 `AI/project.sessions.json`，工具把核验后的绑定登记回同一文件。`SESSIONS.md` 引用唯一来源，可 `sync` 展示；职责在 `ROLES.md`，进度在 `STATE.md`。项目内部审核、自测和验证脚本仍按[内部工具规则](../文档组织与维护.md#internal-tools)存放。

| 字段 | 含义 |
|---|---|
| `schema_version` | 当前为 `1`；不自动迁移旧项目配置 |
| `project_id` / `project_root` | 项目标识、已有绝对根目录；根目录不同的运行数据隔离 |
| `runtime_dir` | 模块之外的绝对路径；实际命名空间为项目 ID＋根目录摘要 |
| `documents_root` | `sync` 允许写入的目录，默认项目根目录 |
| `profiles` | 各适配器 `adapter/cwd/native/connection`；profile 名称不是会话 ID |
| `roles` | A～E 默认 profile；也可只用直接会话 API |
| `milestones` | 各里程碑的 `bindings`、`role_profiles`、`history` |
| `sessions` | `adapter:真实原生ID` 对应核验登记，含 cwd、目标设置、当时观测 |
| `authorization` | 授权依据 `reference`、动作 `allow`、可选调用者 `actors` |

项目/运行/文档根路径支持环境变量，未设置的占位符报错；profile 的 cwd 可相对项目根目录。连接路径填实际绝对位置，连接环境变量通过下述 `*_env` 字段引用。里程碑、任务、请求和 profile 名称用 ASCII 字母、数字、下划线、连字符，不限制为 H 阶段。不能用 `D-01` 等文档序号代替原生 ID。

`roles` 提供新里程碑默认值；已登记里程碑使用自身 `role_profiles`。调整当前里程碑的目标后须显式 `switch`，只改全局默认值不会替换已有绑定。

首次产生运行记录后，运行目录登记唯一配置路径，拒绝同项目同运行目录的第二份配置。搬迁时由维护者核对配置与运行记录后处理，不复制出第二个有效来源。

`allow` 支持 `create/bind/send/switch/report/sync`。默认空列表，只查询；启用前填写真实用户授权依据。`actors` 是调用方声明与项目约定的本地检查，不是操作系统身份认证；工具不绕过宿主限制，互发消息仍须用户授权。

各 Agent 分别配置：

- Codex：`model` 或 `inherit_model: true` 二选一；可选 `reasoning_effort`。CLI 另支持正整数 `context_window`、`auto_compact_limit`。实际模型/强度按原生日志观测，上下文及压缩阈值仅是请求配置，不保证宿主支持任意值。CLI 的 `execution` 可显式设 `sandbox`、`approval_policy`、`skip_git_repo_check`，默认继承本机，无内置绕过开关。
- Antigravity：`model/model_label/native_model` 来自当前原生目录。connection 填 `log/project_id`，可选 `powershell/python/process_id`；多个语言服务须指定唯一 PID。CSRF 只进子进程环境，不写配置和回执。
- Harness：`provider/model/reasoning_effort` 用原生值。connection 填 `authority`（仅 loopback）、`node`、`credentials` 文件路径或 `credentials_env` 环境变量名；可选 `time_zone`，默认 UTC。不复制凭据内容。
- App：connection 填 `node/server_script` 和可选 `host_id`。当前端点由 `pipe_path_env`（默认 `CODEX_APP_TOOLS_PIPE_PATH`）或显式 `pipe_path` 提供。调用方上下文由 `caller_thread_id_env`（默认 `CODEX_THREAD_ID`）或 `caller_thread_id` 提供，不拿接收方 ID 冒充调用方。`server_script` 指向已安装的 App Tools MCP 入口。

## CLI 使用

以下 PowerShell 变量指向模块和**业务项目**配置，路径按实际修改：

```powershell
$tool = 'C:/bobo_document/work/代码规范/AI 协作开发规范/AI_Collaborative_Development_Specification/session_handover_tool/session_tool.py'
$cfg = 'C:/projects/sample/AI/project.sessions.json'
python -B $tool capabilities
python -B $tool --config $cfg init --project-id sample --project-root C:/projects/sample --runtime-dir C:/bobo_worktool/session-handover-tool/runtime
python -B $tool --config $cfg validate
```

`init` 生成只读的 Codex 继承配置，不覆盖已有文件。维护者再填写 profiles、roles、授权；也可复制多适配器样例后按本机修改。样例不含已建会话。

```powershell
# Codex CLI 创建需要 UTF-8 初始消息文件；其他可创建适配器不传此参数
python -B $tool --config $cfg create --milestone M01 --role D --message-file C:/projects/sample/AI/bootstrap.txt --request-id m01-d-create

# 或绑定宿主已有、能核验 cwd 的原生会话
python -B $tool --config $cfg bind --milestone M01 --role C --native-id REAL_NATIVE_UUID --request-id m01-c-bind
python -B $tool --config $cfg inspect --milestone M01 --role D
python -B $tool --config $cfg send --milestone M01 --role D --task-id T01 --message-file C:/projects/sample/AI/task.txt --report-to C --report-to A --request-id m01-t01-send

# D 交付后通知；sender 取 create/bind 返回的 adapter:native_id
python -B $tool --config $cfg report --milestone M01 --task-id T01 --sender ADAPTER:REAL_NATIVE_ID --summary-file C:/projects/sample/AI/summary.txt --status needs_review --record C:/projects/sample/AI/records/T01.md --commit COMMIT_HASH --delivery-id t01-delivery

# 替换为另一已创建会话，也可不传 native-id 让适配器创建替代会话
python -B $tool --config $cfg switch --milestone M01 --role D --profile alternate --native-id REPLACEMENT_NATIVE_ID --request-id m01-d-switch
python -B $tool --config $cfg receipt m01-t01-send
python -B $tool --config $cfg sync --output C:/projects/sample/AI/SESSIONS.md
```

直接调用把 `--milestone/--role` 换成 `--session adapter:native_id`；创建/绑定用 `--profile`。不要求预建 ABCDE。角色模式每个里程碑角色使用独立原生会话，跨角色、跨里程碑重用会拒绝。

`send/switch --confirmed-stopped` 仅用于无法取得原生停止状态时，由调用者依据交接证据明确确认；已观测运行中仍拒绝。回报遇到接收方忙或状态未知保留其失败项，确认空闲后可用相同 delivery ID 重试。

输出 UTF-8 JSON。退出码：`0` 本次调用成功，`2` 确定拒绝/本地错误，`3` 部分回报，`4` 结果未知；参数格式错误为 argparse 帮助及退出码 2。消息作为文件内容或字符串传入，不拼进 shell 命令。

## Python 使用

将模块的父目录加入项目启动器的 Python 搜索路径：

```python
from session_handover_tool import SessionClient

client = SessionClient("C:/projects/sample/AI/project.sessions.json", actor="operator")
created = client.create("worker", milestone="M01", role="D", message="Read the entry and wait.")
# 待 inspect 确认首轮已结束后再执行下方派发；创建返回时可能仍在运行。
client.inspect(milestone="M01", role="D")
client.send("执行已获批任务。", milestone="M01", role="D", task_id="T01",
            report_to=["C", "A"], request_id="m01-t01")
client.report(milestone="M01", task_id="T01", sender="codex_cli:" + created["native_id"],
              summary="实现完成，等待独立审核。", status="needs_review",
              record="C:/projects/sample/AI/records/T01.md", commit="COMMIT_HASH")
```

公共方法为 `capabilities/validate/create/bind/inspect/send/switch/report/receipt/sync`，签名以 [api.py](api.py) 为准。捕获 `ToolError`，用 `code/uncertain/details.request_id` 判断下一步，不根据文本猜测重试。

## 回执与失败处理

1. 修改动作先写 `attempting`，再调用宿主；创建一旦得到 ID 即保存，后续失败不丢掉已知身份。只有原生 ID/cwd 核验后才登记，目标设置和实际观测分开保存。
2. 派发前固定任务的执行会话和接收会话，不随当前角色指针变化。相同任务 ID 拒绝再次派发；跨项目运行数据隔离。
3. 回报是含项目/里程碑/任务/记录/提交引用的数据通知，不检查文件是否已提交、不判断通过、不触发下一阶段。这些检查由项目调用层负责。
4. 每个接收者分别保存回执。成功、尝试中、未知者不会重发；仅确定失败者可用相同 delivery ID 重试。相同 delivery ID 的内容改变会拒绝。
5. 请求 ID 已存在时查原回执，不能直接换 ID 再试。`unknown` 不代表未执行；检查原生会话、worker 和已有进程后处理。角色创建未知且有 ID 时，可 `bind --recover-request 原请求ID`，须同一目标与 ID。没有 ID 的未知创建、未知 switch 由维护者核对宿主与配置处理，本版不自动补建、无强制清除命令。

`accepted` 依通道标明：CLI 为本地 worker 启动，App/Antigravity/Harness 为宿主返回成功。CLI 后续 `inspect.execution` 的退出码和 `turn_completed` 才说明执行结果；其他通道继续取原生结果或由执行者正式交付。发送被接受、实际执行、正式交付、审核通过分别记录。

CLI 状态主要覆盖本模块启动的 worker。其他客户端操作同一原生会话前须完成资源交接；项目锁只覆盖本模块的登记和发送确认，不锁定所有外部客户端。任务快照是工具约定不覆盖的记录，不是防篡改审计系统。

运行数据有 `config-source.json/requests/tasks/cli/antigravity`。CLI 请求和原生日志可能含任务文本，放在项目选定的运行/证据目录；不把真实绑定、pipe、凭据或私人文本提交到通用模块。

`sync` 只替换 `<!-- session-tool:start -->` 至 `<!-- session-tool:end -->` 的展示区，保留周边正文；这是目标配置及最后登记观测，不是实时进度。

## 验证与扩展

```powershell
python -B -m unittest discover -s 'C:/path/to/spec/session_handover_tool/tests' -v
```

测试临时文件默认在 `C:/bobo_worktool/session-handover-tool/tests/`，可通过 `SESSION_TOOL_TEST_ROOT` 指定其他允许目录。测试只用隔离项目、模拟端点和假凭据，不调用真实会话。真实宿主覆盖见 [VALIDATION.md](VALIDATION.md)。

增加 Agent 时补充 `adapters/`、能力注册、原生字段集合及身份/cwd/状态/部分失败测试。不支持的创建、停止、模型选择或证据读取明确返回不支持/未知，不借用其他 Agent 参数。私有原生接口可能随宿主升级变化，升级后需重验再更新支持状态。
