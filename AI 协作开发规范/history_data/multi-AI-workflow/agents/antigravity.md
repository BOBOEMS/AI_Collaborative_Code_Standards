# Antigravity

> 核对日期：2026-10-13。用户确认可用、效果满足预期。
> 本轮核对已运行可执行文件和 `agentapi --help`，未新建会话、发送消息或重新比较模型效果。
> 返回：[Agent 唤醒手册](../多会话工作流-Agent唤醒手册.md)。

## 基本信息与前提

- Electron IDE；先打开并登录 IDE，打开目标工作区。
- 使用已登录 IDE 的 language server 入口。本机位置为 `C:/Users/BOBO/AppData/Local/Programs/Antigravity/resources/bin/language_server.exe`。
- agentapi 连接当前 IDE 实例，需要该实例的地址、CSRF token 和工程标识；这些运行值按当前实例取得。

```powershell
$antigravityLs = 'C:/Users/BOBO/AppData/Local/Programs/Antigravity/resources/bin/language_server.exe'

# 查询运行入口，不输出进程中的连接凭据
Get-CimInstance Win32_Process -Filter "Name='language_server.exe'" | Select-Object ExecutablePath

# 设置从当前已登录实例取得的值
$env:ANTIGRAVITY_LS_ADDRESS = '<当前实例HTTP地址>'
$env:ANTIGRAVITY_CSRF_TOKEN = '<当前实例CSRF token>'
$env:ANTIGRAVITY_PROJECT_ID = '<当前工程ID>'
```

旧手册记载连接地址与 token 来自当前进程参数，工程 ID 在 `.gemini/config/projects/`。多实例时匹配目标工程；本轮没有读取或记录实际 token，也没有重做连接探测。

## 配置

角色当前选型以角色总表为准；以下记录工具配置入口、示例或历史快照，项目实际参数由其执行配置维护。角色操作见 [命令表](../命令表.md)。

| 配置名称 | 模型设置 | 推理设置 |
|---|---|---|
| flash | `--model=flash` | 保留原 `high` 目标，在 IDE/配置中设置和核对 |

`flash` 是本手册的配置条目及实际模型别名，不是角色名称。本机帮助列出模型别名 `flash_lite / flash / pro`，但本手册只采用已有 flash 用法。

旧记录将 flash 对应到 Gemini 3.8 Flash；本轮未重新核对 UI 型号映射。`high` 未出现在本机 agentapi CLI 参数中，不添加猜测的 `--effort`。`--profile=<profile>` 只在已知真实 profile 时使用。

| 参数 / 环境 | 用途 |
|---|---|
| `--model` | 为新会话选择模型别名 |
| `--title` | 设置会话显示标题 |
| `--profile` | 选择实际存在的配置 profile；本轮只核对语法 |
| `ANTIGRAVITY_LS_ADDRESS` | 当前 IDE language server 的连接地址 |
| `ANTIGRAVITY_CSRF_TOKEN` | 对应实例的连接凭据 |
| `ANTIGRAVITY_PROJECT_ID` | 目标工程标识 |

## 启动命令

```powershell
# 新建会话，记录返回的 conversationId
& $antigravityLs agentapi new-conversation --model=flash --title="<会话名>" "<任务内容>"
```

命令创建 IDE 内的会话；返回会话标识后通过 metadata 查看运行状态，返回 ID 不等于任务已经完成。保留原已登录 IDE 的调用方式，不把独立 language server 进程当作已登录实例。

## 会话操作

```powershell
# 查询实际运行状态
& $antigravityLs agentapi get-conversation-metadata "<会话ID>"

# 在指定会话追加内容
& $antigravityLs agentapi send-message "<会话ID>" "<继续内容>"
```

当前帮助只列出 new-conversation、get-conversation-metadata、send-message 三个命令。需要中止时通过 IDE 中已用过的控制方式处理，本轮不补写未经核对的 CLI 停止命令。

## 输出与状态

保存 new-conversation 返回的完整 conversationId。查询 metadata 与查看 IDE 中该会话的实际输出；按返回字段和内容判断运行、结束或需输入的状态，未核对的字段不作为固定格式。

## 注意事项与验证状态

- 可用性与效果由用户确认；本轮帮助核对只确认语法。
- 入口路径、端口、token 和工程标识随安装或 IDE 重启可能变化，按当前实例准备。
- 保留原 IDE 自动执行/评审设置，具体枚举名称以当前 IDE 为准；旧 EAGER/TURBO 记录不作为全版本统一参数。
- 手册只记录工具会话标识，不指定项目的登记文件或阶段运行流程。
