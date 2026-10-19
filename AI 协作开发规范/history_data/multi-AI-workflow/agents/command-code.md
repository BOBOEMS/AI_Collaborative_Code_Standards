# Command Code CLI

> 核对日期：2026-10-13；本机版本：1.79.2。
> 本轮核对 CLI 帮助，未重新执行模型任务、登录或额度检查。
> 返回：[Agent 唤醒手册](../多会话工作流-Agent唤醒手册.md)。

## 基本信息与前提

- 使用 PATH 中的 `cmdc`；本机解析到 `C:/Users/BOBO/AppData/Roaming/npm/cmdc.ps1`。
- `commandcode` 为另一个可用入口；Windows 下优先用 `cmdc` 避免与系统 `cmd.exe` 混淆。
- 从目标工作目录运行，沿用已有登录。会话通常存入 `~/.commandcode/projects/<项目slug>/` 的转录及元数据。

## 配置

角色当前选型以角色总表为准；以下记录工具配置入口、示例或历史快照，项目实际参数由其执行配置维护。角色操作见 [命令表](../命令表.md)。

| 配置名称 | 模型参数 | 推理参数 | 轮次参数 |
|---|---|---|---|
| deepseek-flash | `--model deepseek/deepseek-v4.1-flash` | `--effort high` | 沿 CLI 默认 |
| glm-flash | `--model z-ai/glm-5.3-flash` | `--effort max` | `--max-turns 80` |

这些名称是本手册的参数组合，不是 CLI profile 名。模型及推理强度保持原目标配置；帮助确认参数存在，不证明账号可用模型或每个模型支持所有强度。

| 参数 | 用途 |
|---|---|
| `-p` / `--print` | 非交互执行一轮，输出并退出 |
| `-n` / `--name` | 设置会话显示名 |
| `-r` / `--resume` | 按 ID 或名称继续会话 |
| `--session` | 按转录路径或唯一 ID 前缀续接 |
| `--effort` | 设置推理强度，具体值依模型支持 |
| `--max-turns` | 限制非交互轮次；帮助记载默认 100、达到上限退出码 8 |
| `--tools-all` | 启用非交互模式下原本 withheld 的工具 |
| `--skip-onboarding` | 跳过偏好 onboarding |
| `--trust` | 自动信任当前项目 |
| `--yolo` | 跳过权限提示 |
| `--output-format json` | 非交互输出 NDJSON 事件及最终结果 |

## 启动命令

角色操作与底层参数组合见 [命令表](../命令表.md)。

```powershell
# 交互启动
cmdc

# 非交互结构化输出
cmdc --model deepseek/deepseek-v4.1-flash --effort high --output-format json -p "<任务内容>"

# 查看支持参数或模型入口
cmdc --help
cmdc --list-models
```

模型列表查询命令只作为入口记录，本轮未查询实时模型列表。

## 会话操作

```powershell
cmdc -c
cmdc -r "<会话ID或会话名>"
cmdc --yolo -n "<会话名>" -r "<会话ID或会话名>" -p "<继续内容>"
cmdc --session "<转录路径或ID前缀>" -p "<继续内容>"

# ACP 通道
commandcode acp
```

已有会话优先使用明确 ID 或完整名称；带空格的名称需引用。交互界面的 `/session-file` 可查看会话 ID 和路径，`/model`、`/effort` 可查看或调整对应配置。

## 输出与状态

`-p` 默认输出文本，`--output-format json` 输出 NDJSON。运行结束后立即记录进程退出码与实际输出；达到轮次上限属于明确中断，不能仅凭部分回复声明任务完成。

## 注意事项与验证状态

- 本轮 `cmdc --help`、`cmdc --version` 已通过，完整模型执行未重新验证。
- 登录、额度或网络失败以实际错误为依据；旧使用记录不作为当前账号状态证明。
- `cmdc /usage` 是旧手册保留的额度查看入口，本轮未执行。
- 终止当前 CLI 时只处理自己启动的进程，续接前核对保存的会话对象。
- ACP 参数与辅助交互面见手册，接口名称和业务分工无绑定。
