# 示例项目 AI 入口

本目录模拟项目唯一的 `AI/` 协作文档目录，所有角色和工作树共用。采用[协议入口](../AGENT.md)及其四份正文，按任务读取；本项目 `README.md` 仅供介绍和学习。

## 1. 项目约定、授权与入口

本套为 OTA 教学材料。允许阅读、编辑及使用现有 Python 处理示例离线数据；未提供真实设备、会话或推送目标，不从占位参数推断运行权限。

| 材料 | 唯一入口 |
|---|---|
| 总体目标、版本范围和约束 | [PROJECT.md](PROJECT.md) |
| 里程碑及验证承接 | [PLAN.md](PLAN.md) |
| 当前阶段、任务、对象、结果和下一步 | [STATE.md](STATE.md)，并由其定位当前 DESIGN / CASES / REVIEW / TEST_REPORT |
| 项目协作选择 | [ROLES.md](ROLES.md) |
| 模型、真实绑定及唯一配置 | [SESSIONS.md](SESSIONS.md) → [project.sessions.json](project.sessions.json) |
| 共用技术约定 | [shared_design.md](shared_design.md) |
| 重要决定与事件、内部工具 | [records/INDEX.md](records/INDEX.md)、[tools/INDEX.md](tools/INDEX.md) |
| 会话调用 | [统一工具](../session_handover_tool/README.md)及[已有验证范围](../session_handover_tool/VALIDATION.md) |
| Git 配置 | `<实际项目仓库及已确认分支/上游配置>`；汇合及推送责任见 [ROLES.md](ROLES.md#project-git) |

教学实施授权仅覆盖 M01，依据为[范围确认](records/decisions/20261019-M01-scope.md#范围和确认依据)。后续阶段是否已获准启动沿 STATE 读取，不从计划存在推断授权。真实工程采用时在此补充源码、子目录细则、真实用户授权和上述 Git 入口，当前进度不写回本文件。

工具配置通过 `SESSION_TOOL_PROJECT_ROOT`、`SESSION_TOOL_DOCUMENTS_ROOT` 定位实际目录，运行位置沿唯一配置。本例授权和真实绑定为空，消息及回执均为合成材料，不能据此创建会话或派发实际任务。

## 2. 启动与恢复

执行[工作流的共同读取清单及角色/动作表](../多AI会话工作流规范.md#session-recovery)，按上表取得项目材料的相关当前原文；不在本入口重列清单。必须恢复当前任务依赖的总约束和共用契约，摘要只帮助定位。
