# Codex CLI

> 核对日期：2026-10-13；本机版本：0.162.0。
> 用户确认可用、效果满足预期。本轮只读核对帮助和配置，未启动模型任务。
> 返回：[Agent 唤醒手册](../多会话工作流-Agent唤醒手册.md)。

## 基本信息与前提

- 入口：PATH 中的 `codex`；本机解析到 `C:/Users/BOBO/AppData/Roaming/npm/codex.ps1`。
- 命令从目标工作目录运行，或在支持的位置使用 `-C "<工作目录>"`。
- 沿用已有登录和配置。会话材料位于 `~/.codex/sessions/` 等 Codex 管理目录。

## 配置

角色当前选型以角色总表为准；以下记录工具配置入口、示例或历史快照，项目实际参数由其执行配置维护。角色操作见 [命令表](../命令表.md)。

| 配置名称 | 实际配置入口 | 模型 | 推理强度 |
|---|---|---|---|
| default | `~/.codex/config.toml` | `gpt-6.1-sol` | `xhigh` |
| luna | `~/.codex/luna.config.toml`，启动时 `-p luna` | `gpt-6-luna` | `max` |

以上为本轮读取的配置快照；保持已有配置内容。`luna` 是实际 CLI profile，叠加在基础配置上。

本机配置快照中的 default context/auto-compact 为 526000/500000，luna 为 1050000/1000000；这些是文件设置，不单独证明已运行会话的实际上下文或自动压缩行为。

| 参数 / 设置 | 用途 |
|---|---|
| `-p` / `--profile` | 选择 CLI profile，不能当作 print 参数 |
| `-m` / `--model` | 为本次启动指定模型 |
| `model_reasoning_effort` | 配置推理强度，可用 `-c 'model_reasoning_effort="xhigh"'` 设置本次值 |
| `-C` / `--cd` | 设置工作根目录；续接子命令接受的参数按各自帮助核对 |
| `--dangerously-bypass-approvals-and-sandbox` | 跳过权限确认并取消命令沙箱，保留原常用命令的设置 |
| `--json` | exec 输出 JSONL 事件 |
| `-o` / `--output-last-message` | 将最终回复写到指定文件 |

## 启动命令

角色操作与底层调用参考见 [命令表](../命令表.md)。本页补充工具操作机制、交互入口和输出选项。

```powershell
# 交互启动
codex
codex -p luna

# 单轮任务，结构化输出
codex exec --dangerously-bypass-approvals-and-sandbox --json "<任务内容>"

# 为本次任务显式设置模型和推理强度
codex exec -m gpt-6.1-sol -c 'model_reasoning_effort="xhigh"' --dangerously-bypass-approvals-and-sandbox "<任务内容>"
```

`exec` 用于执行一轮任务并输出结果；交互入口用于在终端持续对话。配置与模型效果沿用已确认用法，本轮未重新比较。

## 会话操作

```powershell
# 交互会话：按 ID 或名称续接
codex resume "<会话ID或会话名>" "<继续内容>"

# 最近交互会话 / 会话选择器
codex resume --last "<继续内容>"
codex resume

# 选择器包含非交互会话
codex resume --include-non-interactive

# 非交互会话：指定 ID 续接
codex exec resume --dangerously-bypass-approvals-and-sandbox "<会话ID>" "<继续内容>"

# 最近一次已记录会话
codex exec resume --last "<继续内容>"
```

`--last` 适合已经明确最近会话的人工操作；多会话时保存并使用明确 ID。`--all` 会扩大目录范围；`--include-non-interactive` 在交互 resume 中包含非交互会话。本机 exec resume 不直接列出 `-p`，需要 profile 时将它放在父级 `codex exec -p luna ... resume`。

在正在运行的交互界面追加内容；非交互进程结束后通过 resume 续接。中断当前终端进程后，核对实际输出与会话状态再继续。

## 输出与状态

默认输出可读文本；`--json` 输出 JSONL 事件，记录返回的会话标识；`-o "<结果文件>"` 保存最终回复。不要把 CLI 退出或收到最终文本单独当作任务验收。

本机帮助核对范围：`codex --help`、`codex exec --help`、`codex exec resume --help`、`codex resume --help`。语法核对不代表本轮执行了所有启动方式。

## 注意事项与来源

- profile、默认配置与本次覆盖值可能共同影响运行参数；核对实际会话显示或事件，文件快照不替代运行事实。
- 需要可续接记录时保留正常会话持久化，避免误用 `--ephemeral`。
- agent-canvas 的现有 `codex-strong` 是辅助通道 profile 名称，接入说明见手册；本轮未重新验证该通道。

参数与 exec / JSONL 说明参照 [official OpenAI documentation](https://learn.chatgpt.com/docs/developer-commands#codex-exec)，具体可用参数同时以本机版本帮助为准。
