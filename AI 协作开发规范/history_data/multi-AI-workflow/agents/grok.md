# Grok CLI

> 核对日期：2026-10-13；本机版本：1.0.50（c58f321264ba）。
> 本轮核对 CLI、sessions list 和 agent stdio 帮助，未验证模型任务或当前登录。
> 返回：[Agent 唤醒手册](../多会话工作流-Agent唤醒手册.md)。

## 基本信息与前提

- 入口：`C:/Users/BOBO/.grok/bin/grok.exe`，可用 PATH 中的 `grok`。
- 从目标工作目录运行，或使用 `--cwd "<工作目录>"`。
- 需要已有有效登录。旧手册的登录结论为历史记录；当前登录方式和状态本轮未核对。
- 旧会话存储入口为 `~/.grok/sessions/<工作目录编码>/<id>/chat_history.jsonl`，实际位置以本机版本为准。

## 配置

角色当前选型以角色总表为准；以下记录工具配置入口、示例或历史快照，项目实际参数由其执行配置维护。角色操作见 [命令表](../命令表.md)。

| 配置名称 | 模型参数 | 推理参数 |
|---|---|---|
| grok-4.6-high | `-m grok-4.6` | `--reasoning-effort high`（别名 `--effort`） |

该名称是本手册的参数组合，保留原目标模型及强度。本轮帮助确认两个选项存在，未查询实时模型可用性。

| 参数 | 用途 |
|---|---|
| `-p` / `--single` | 单轮非交互任务 |
| `-r` / `--resume` | 按 ID 或标题恢复会话 |
| `-c` / `--continue` | 继续当前工作目录的最近会话 |
| `--cwd` | 设置目标工作目录 |
| `--output-format` | 非交互输出 plain、json、streaming-json 等格式 |
| `--max-turns` | 限制 Agent 轮次 |
| `--session-id` | 为新会话指定新 UUID，不用于恢复现有会话 |

## 启动命令

```powershell
# 交互启动
grok

# 单轮任务，沿原默认配置
grok -p "<任务内容>"

# 使用本手册参数组合
grok -m grok-4.6 --reasoning-effort high -p "<任务内容>"

# JSON 输出
grok --output-format json -p "<任务内容>"
```

## 会话操作

```powershell
grok -r "<会话ID或会话名>" "<继续内容>"
grok -c "<继续内容>"
grok -m grok-4.6 --reasoning-effort high -r "<会话ID或会话名>" -p "<继续内容>"
grok sessions list
grok models

# ACP 通道
grok agent stdio
```

本机帮助说明：非 UUID 的 resume 值按当前目录匹配标题，重复标题可能产生歧义；明确 ID 更便于指定对象。`--session-id` 创建新会话，恢复应使用 `--resume` 或 `--continue`。

## 输出与状态

plain 为默认非交互输出；json 用于结构化结果，streaming-json 为逐行 ACP session update。读取返回的会话标识、退出码和最终内容；模型列表与实际任务执行本轮未运行。

## 注意事项与验证状态

- 本轮帮助核对不证明已登录或某模型当前可用；失败以实际错误为依据。
- 旧手册的 `grok login` 未列在本机顶层帮助中，本轮不把它作为已核验登录指令。
- `--restore-code` 涉及恢复代码快照，普通续接示例不使用该参数。
- 当前 CLI 的中止在其运行终端处理，续接前核对保存会话。
- ACP 与统一交互面的接入说明见手册。
