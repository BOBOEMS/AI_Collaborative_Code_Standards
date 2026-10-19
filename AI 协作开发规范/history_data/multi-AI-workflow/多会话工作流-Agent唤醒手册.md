# 多会话工作流：Agent 唤醒手册

> 2026-10-14 修订。工具索引、参数机制、会话操作和注意事项；角色操作命令集中在协议根目录命令表。
> 本机帮助核对与用户确认的范围见各 Agent 详情；本手册不规定角色分工或项目执行流程。
> 协议入口：[README.md](README.md)。`agents/` 的导航入口即本手册。

## 工具索引

| Agent | 详情 |
|---|---|
| Codex | [codex.md](agents/codex.md) |
| Antigravity | [antigravity.md](agents/antigravity.md) |
| Command Code | [command-code.md](agents/command-code.md) |
| Grok | [grok.md](agents/grok.md) |
| DeepSeek Harness | [deepseek-harness.md](agents/deepseek-harness.md) |

角色操作及原快速表内容见 [命令表](命令表.md)。本手册不再保留一份对应启动表。

## 配置与维护

角色默认的 Agent、模型、思考强度与要求由角色总表维护；角色操作只同步命令表。Agent 详情维护设置方法、工具限制及带日期的配置快照，示例不定义当前角色选型。项目真实运行配置继续由已有执行入口读取。

命令中的 `<任务内容>`、`<会话名>`、`<会话ID>` 均需替换。工具入口、配置文件和登录环境变化时更新对应详情，不把旧安装位置或旧端口当作固定不变的事实。

## 核验范围

| Agent | 当前记录范围 |
|---|---|
| Codex | 用户确认可用且效果满足预期；本轮核对 0.162.0 的帮助和本机模型配置，未重新执行模型任务 |
| Antigravity | 用户确认可用且效果满足预期；本轮核对已运行入口和 agentapi 帮助，未新建或发送会话消息 |
| Command Code | 本轮核对 1.79.2 帮助；模型任务、登录与额度未重新验证 |
| Grok | 本轮核对 1.0.50 帮助；模型任务与登录未验证 |
| DeepSeek Harness | 本轮核对 0.2.0-rc.2 启动器及 headless 帮助；续接的历史实跑范围见详情 |

## 辅助访问通道

agent-canvas 是统一交互面，辅助访问 Codex、Command Code、Grok 等工具。工具本身的参数仍按各 Agent 详情维护。

- 入口：`http://localhost:8000/`；实际端口以运行实例为准。
- 安装目录：`C:/bobo_worktool/agent-canvas/`；profile 在其 `agent-profiles/` 下。
- 现有接入说明：[multi-agent-interactive-access](../agent-hub/docs/multi-agent-interactive-access.md)。

```powershell
& 'C:/bobo_document/temp/agent开发/agent-hub/scripts/start-agent-canvas.ps1'
```

该启动脚本和接入说明本轮只核对存在，未重新拉起服务。各工具的 ACP 命令见详情。旧手册中尚无可复制实现的视觉/模拟键鼠设想不列为已验证启动命令。
