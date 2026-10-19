# DeepSeek Harness

> 核对日期：2026-10-13；本机启动器版本：0.2.0-rc.2。
> 本轮核对启动器及 headless 帮助，未执行模型任务或跨通道续接测试。
> 返回：[Agent 唤醒手册](../多会话工作流-Agent唤醒手册.md)。

## 基本信息与前提

- 入口：`C:/bobo_worktool/DeepSeek Harness/resources/runtime/cli/bin/dsh.cmd`。
- 启动器组合 profile 和 patch，再把其余参数传给对应应用。
- 从目标工作目录运行，沿用已有认证和 provider 配置。
- 旧会话入口为 `~/.dsh/sessions/--<工作目录slug>--/session-<id>/session.v4.jsonl.zstd`，实际 ID 和位置以运行返回为准。

```powershell
$dsh = 'C:/bobo_worktool/DeepSeek Harness/resources/runtime/cli/bin/dsh.cmd'
```

## 配置

角色当前选型以角色总表为准；以下记录工具配置入口、示例或历史快照，项目实际参数由其执行配置维护。角色操作见 [命令表](../命令表.md)。

| 配置名称 | 实际 profile | 模型 / 推理参数来源 |
|---|---|---|
| headless | `--profile headless` | 继承 profile、用户覆盖层及 patch 的有效 backend 配置 |

原目标记录为默认 GLM 系模型；本轮未读取有效 backend 型号或强度，不固定成未经核对的模型 ID。需要改模型时按实际 provider 的配置 schema 更新 profile/patch。

| 参数 | 用途 |
|---|---|
| `--profile` | 选择实际 profile；本手册采用已有 headless 用法 |
| `--patch` | 启动器在 profile 后叠加 patch，可重复 |
| `--dump-config-schema` | 查看当前配置和 patch 的 schema |
| `--json` | headless 输出逐行运行事件 |
| `--session-id` | headless 使用已持久化会话，未知 ID 报错 |
| `-` 任务内容 | headless 从标准输入读取任务 |

启动器和 profile 的参数分别看帮助，不把某个 profile 的参数直接套到其它 profile。

## 启动命令

```powershell
# 非交互单轮
& $dsh --profile headless --json "<任务内容>"

# 使用已有模型 patch
& $dsh --profile headless --patch '<模型patch.yml>' --json "<任务内容>"

# 查询帮助 / 配置 schema
& $dsh --help
& $dsh --profile headless --help
& $dsh --profile headless --dump-config-schema
```

模型 patch 的字段按实际 schema 和 provider 定义；本轮不新增 patch 文件，也不修改已有运行配置。

## 会话操作

```powershell
# 在返回的持久化会话上继续
& $dsh --profile headless --json --session-id "<会话ID>" "<继续内容>"
```

从首次运行返回的事件取得完整会话 ID，并在后续轮次继续用同一 ID。同一会话同一时刻保留一个 runner；中断时只处理自己启动的进程，续跑前确认实际保存对象。

旧手册记录 2026-10-11 的 headless 续接已实跑，GUI 会话跨到 headless 曾静默创建新会话。本轮只确认当前 headless 的 `--session-id` 语法，未重新验证跨 GUI 限制；常用基线仍采用 headless 创建的会话。

## 输出与状态

headless 默认把最终回复写到 stdout，诊断写到 stderr；`--json` 改为逐行 run events。记录会话标识、实际退出码、最终内容和错误；unknown ID 是具体错误，不能当作成功续接。

## 注意事项与验证状态

- launcher 帮助包含自定义 tui 示例，不证明本机已有可用 tui profile；本手册不保留未经核对的 `dsh tui` 启动指令。
- 旧手册的 web 启动参数与完整插话 API 仍待逐项核对，当前常用命令只采用已保留的 headless 方式。
- 不记录固定浏览器端口或项目角色的模型网关绑定；辅助访问方式按实际 profile 的帮助整理。
- 实际模型执行、登录和 GUI/headless 互通本轮未运行。
