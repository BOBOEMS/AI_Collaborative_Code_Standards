# 独立调用模块验证记录

日期：2026-10-20。对象：本目录 `1.0.0`，Windows、本机 Python 3.12、Node.js、PowerShell 7；原生 Codex CLI 0.162.0，App Tools MCP 0.1.6。

同日按用户要求补充 Antigravity 2.24.0、DeepSeek Harness 0.2.0-rc.2 的真实宿主验证。原生服务恢复后，两者均完成独立会话的创建、绑定、模型核验、两轮实际输出、重复请求拒绝及最终空闲状态核验；适配器代码无需修改。

随后单独完成 [Antigravity 真实开发执行验证](ANTIGRAVITY_WORKTEST.md)：实际读取、修复隔离代码并运行测试，外层独立复测 11 项通过；报告经两轮同会话补正后核验，最终停止。该项高于文本连通性证据，但仍是单个隔离任务的覆盖。

本轮完成通用接口内化与本地验证，未将 Reuse_RTU 现有流程迁移到新模块，未建立真实项目 ABCDE 组，未操作板卡。各类证据分开记录，不能据此宣布所有 Agent 或项目工作流已端到端通过。

## 自动验证

`python -B -m unittest discover -s <本目录>/tests -v`：**51 项通过**，无跳过。测试使用临时项目、假凭据、假 App Tools JSON-RPC 服务及 loopback HTTP 模拟端点。

覆盖：

- 两个项目运行数据隔离；A～E 及不同里程碑会话独立；历史会话的原始归属不被后续里程碑复用；唯一配置源冲突拒绝。
- 精确 ID/cwd 核验；运行中及状态未知的处理；原生字段不混用；修改当前目标后必须显式切换；保留替换历史。
- 创建回执丢失、已知 ID 恢复、部分创建失败保留 ID；请求/任务重复拒绝；未知派发保留原快照。
- 固定原任务回报接收者；切换角色后旧任务仍向旧会话回报；接收端点刷新不改变身份；部分成功仅重试确定失败者；未知送达不重发；delivery ID 内容冲突拒绝。
- 授权和调用者检查；目录穿越拒绝；凭据值不写入通用配置；不支持的 Agent 明确拒绝。
- UTF-8/非 BMP 文本跨 Python、Node、HTTP、JSON-RPC；CLI 精确 resume、无内置绕过选项；原生模型字段和运行状态检查。
- Antigravity 原模型禁用时仍可读取旧会话停止证据完成切换准备，但创建和发送继续校验模型可用性。
- CLI 从无关 cwd 使用中文路径配置；init 默认只读且不覆盖；SESSIONS 展示保留手工正文、标记错误拒绝、不得写入 ROLES/STATE。

Python AST、样例 JSON、Node 脚本语法、PowerShell AST 语法检查通过。源代码检查未发现原项目固定阶段、真实会话 ID、旧运行目录依赖或固定模型；README 仅保留来源说明。

## 真实宿主验证

| 通道 | 本轮结果 | 实际证据与限制 |
|---|---|---|
| Codex CLI | **创建、检查、精确续接通过** | 独立 workspace；只读 sandbox、禁止工具的最小文本任务；两次退出码 0、`turn_completed=true`；原生 ID/cwd 一致，分别返回 `SESSION_TOOL_CREATE_OK`、`SESSION_TOOL_RESUME_OK`。继承宿主模型，实际观测到 gpt-6.1-sol / xhigh；未验证任意其他模型或上下文阈值 |
| Codex App | **绑定、检查、发送、实际输出通过** | 复用同一个专用验证会话；App Tools 原生 read_thread 验证 ID/cwd；依据 CLI 已结束证据确认未加载会话停止后发送；原生会话实际返回 `SESSION_TOOL_APP_OK` 并变为空闲。未提供或验证 App 新建/强制停止能力 |
| Antigravity | **原生文本调用及隔离开发执行通过** | Gemini 3.8 Flash（High）映射和实际生成器均为 `MODEL_PLACEHOLDER_M318`；此前两轮文本及重复拒绝通过。新增开发会话实际读文件、改代码、运行失败基线及修复后测试，外层独立复测 11 项通过；两轮报告补正后最终空闲、46 步 DONE，详见[开发实测](ANTIGRAVITY_WORKTEST.md) |
| DeepSeek Harness | **创建、绑定、模型选择、检查、两轮实际输出通过** | 专用 workspace，`cmdc / deepseek/deepseek-v4.1-flash / max`；`lastUsed` 确认实际使用设置，两轮回复均为 `SESSION_TOOL_DSH_OK`；同一会话 ID/cwd，最终 `running=false`；重复 task/request 被拒绝 |

App Tools 初次调用发现须传递调用方 `_meta.threadId/callId`，已按本机安装桥接代码修正；后续原生检查和发送通过。App 状态读取使用 `thread.status.type`，未将字段缺失或未加载解释为空闲。

### Antigravity / Harness 补测范围

初次验证时两个服务未运行的证据保留在原 `native-host-preflight.json`；上表为恢复服务后的补测结果，不覆盖原失败记录。

1. 在工具运行目录建立独立 workspace。Antigravity 会话注册表初始为空，但 `ListProjects` 可读取原生项目；使用本机已安装前端所用的 `ReadProject/CreateProject` 契约建立独立测试项目、核验其 folder URI，未借用或修改 Reuse_RTU 原生项目。此准备未扩展为模块的自动项目创建能力。
2. 使用本模块 `SessionClient.create/inspect/send/bind` 驱动两个专用会话，原生 ID、cwd 和标题均核验。首轮为中文禁止工具的最小文本任务；第二轮含非 BMP 字符，要求复述上一轮标识，消息本身不再给出预期标识，验证同一原生会话的上下文连续性。
3. Antigravity 从 `GetCascadeTrajectory` 读取实际 planner response、步骤完成状态和生成器模型；后端返回的响应模型别名为 `gemini-3.8-flash-n`，High 选择的证据是实时目录映射与生成器枚举均为 `MODEL_PLACEHOLDER_M318`。不把后端别名自行解释成其他模型变体。
4. Harness 从自身桌面 API 的 `session/page` 读取实际 assistant message，`session/projections.modelSelection.lastUsed` 确认 provider/model/effort，未仅凭 `next` 或发送 accepted 判定推理通过。输出读取参考已有只读 host client；创建、选择和派发由本模块执行。
5. 两轮完成后，通过本模块显式绑定同一原生 ID；重复任务及重复创建 request ID 均得到确定的 `already_attempted`，没有发起第三轮测试或再建会话。两个原生会话最终均为空闲。

本次没有测试模型切换、额度耗尽、真实多接收者回报或项目工作流续派；通过范围限于表列的模型及文本调用链。

## 原始证据位置

本轮证据在 `C:/bobo_worktool/session-handover-tool/validation/20261020/`，不进入协议仓库：

| 文件/目录 | 内容 |
|---|---|
| `unittest.log` | 本轮完整自动测试结果 |
| `project.sessions.json` | 专用验证项目的唯一配置及真实测试会话登记 |
| `cli-create-result.json` / `cli-first-inspect.json` | 创建回执及第一轮原生退出证据 |
| `cli-resume-result.json` / `cli-resume-inspect.json` | 精确续接及第二轮原生退出证据 |
| `cli-output-verification.json` | 两个 CLI 返回文本及结束标志核对 |
| `app-readonly.json` | 当前调用会话的只读桥接检查；未给它发送验证消息 |
| `app-bind-result.json` / `app-send-result.json` | 专用测试会话的 App 绑定、发送回执 |
| `app-completion.json` | 专用会话实际返回及原生空闲状态 |
| `native-host-preflight.json` | Antigravity/Harness 当前服务不可用的原始错误分类 |
| `runtime/` | 请求回执、固定任务快照、CLI 原生 JSONL、worker PID/退出记录 |

补测材料在同一根目录的 `agents-live/`，真实 ID 和连接配置仅保存在这里：

| 文件/目录 | 内容 |
|---|---|
| `project.sessions.json` / `workspace/` | 专用验证配置与工作目录，独立于原项目配置 |
| `antigravity-preflight.json` / `antigravity-project.json` | 实时目录、原生项目查询及专用项目创建回执 |
| `anti-create.json` / `dsh-create.json` | 通过本模块创建并核验登记的回执 |
| `anti-send.json`、`anti-send2.json` / `dsh-send.json`、`dsh-send2.json` | 两个通道各两轮明确派发的原始回执 |
| `anti-trajectory-first.json` / `anti-trajectory-second.json` | 专用会话的原生轨迹、实际回复、完成状态及模型元数据 |
| `anti-observation-first.json` / `anti-observation-second.json` | 原生身份、目录、空闲状态与生成器观测 |
| `dsh-completion.json` / `dsh-completion-second.json` | 专用会话的实际 assistant message 及模型 lastUsed |
| `anti-bind.json` / `dsh-bind.json`、`anti-inspect.json` / `dsh-inspect.json` | 显式同 ID 绑定与最终原生状态 |
| `verified-results.json` | 两轮输出、模型、最终状态和重复拒绝断言的汇总 |
| `runtime/` | 本轮请求回执及固定任务快照 |

`run.py`、`probe.py`、`anti_result.py`、`check_results.py` 是本轮验证入口，不是通用模块依赖；重复执行修改动作须遵守已保存的 request/task 回执。`installed-source/` 只用于核对本机安装版本及原生接口，不纳入协议仓库。

旧项目配置仅在人工验证脚本中用于定位本机已安装服务的文件位置；未使用旧任务绑定和接收方，不构成新模块的运行依赖。真实 ID、pipe 及本机凭据不纳入本记录。

## 尚未覆盖

任意其他模型和上下文配置的可用性；跨 Agent 的真实多接收者回报、配额耗尽后替换、真实部分失败恢复和整套项目交付/审核/接续。这些流程目前只有相应核心契约或模拟端点证据，不能从上述两轮文本调用推导通过。宿主升级后应重新核验私有接口。

Antigravity 的单个隔离开发任务也不能扩展为上述流程或复杂开发能力已经通过；其首次报告的准确性问题和补正过程保留在专项记录。

这些限制不影响已通过的通用契约及四个通道的专用会话验证；项目采用时仍应按具体模型、权限与任务补齐项目验证，再据完成条件判断结果。
