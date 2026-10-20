# 独立调用模块验证记录

日期：2026-10-20。对象：本目录 `1.0.0`，Windows、本机 Python 3.12、Node.js、PowerShell 7；原生 Codex CLI 0.162.0，App Tools MCP 0.1.6。

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
| Antigravity | **真实服务验证未完成** | 本机未发现唯一的运行中语言服务，返回 `backend_unavailable`；未向旧会话发送、未创建替代会话。RPC 字段、目录映射、身份/cwd 和发送方式仅通过本地模拟端点验证 |
| DeepSeek Harness | **真实服务验证未完成** | 已配置的本机桌面 API 返回 `ECONNREFUSED`；未创建真实会话或发送任务。创建、选择、检查、中文派发、忙拒绝和部分创建恢复仅通过本地模拟端点验证 |

App Tools 初次调用发现须传递调用方 `_meta.threadId/callId`，已按本机安装桥接代码修正；后续原生检查和发送通过。App 状态读取使用 `thread.status.type`，未将字段缺失或未加载解释为空闲。

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

旧项目配置仅在人工验证脚本中用于定位本机已安装服务的文件位置；未使用旧任务绑定和接收方，不构成新模块的运行依赖。真实 ID、pipe 及本机凭据不纳入本记录。

## 尚未覆盖

Antigravity/Harness 真实服务恢复后的目录、认证、配额、实际推理及模型一致性；任意模型和上下文配置的可用性；跨 Agent 的真实多接收者回报、配额耗尽后替换和整套项目交付/审核/接续。后面三类目前只有核心契约与模拟端点证据。宿主升级后应重新核验私有接口。

这些限制不影响已通过的通用契约及 Codex 专用会话验证；项目采用时应按所选适配器补齐实际宿主验证，再据项目完成条件判断结果。
