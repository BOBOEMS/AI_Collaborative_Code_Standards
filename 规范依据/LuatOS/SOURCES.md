# LuatOS 规范依据：来源与使用边界

> **用途**：为 [LuatOS / Lua 嵌入式产品规范](../../LuatOS/luatos-embedded-team-standard-v1.md) 提供可追溯的官方 API 与工程资料入口。
> **访问日期**：2026-07-27。
> **边界**：本目录只保存来源清单，不镜像会持续更新的官方网页，也不把网页内容当作离线构建依赖。项目发布时应保存实际使用的固件、工具、demo 和测试证据。

| 代号 | 官方来源 | 用于支持的事实/规则 | 使用边界 |
| --- | --- | --- | --- |
| `L-SYS` | [sys 库](https://wiki.luatos.com/api/sys.html) | `sys.taskInit`、`sys.wait`、`sys.waitUntil`、timer、publish/subscribe、`sys.run` 的 API 语义和“回调不能直接 wait”限制。 | API 可用性和参数以目标固件实际文档为准。 |
| `L-TASK` | [LuaTask 框架](https://wiki.luatos.com/luaGuide/luatask.html) | LuatOS 以 Lua 协程实现脚本任务、在 `sys.run()` 中运行、等待与消息传递的模型。 | 用于解释协作式调度，不替代目标板性能测量。 |
| `L-FSKV` | [fskv KV 数据库](https://wiki.luatos.com/api/fskv.html) | 初始化和读写均有返回值、键和值限制、掉电存储的 API 入口。 | 不把 KV 文档解释为无限队列或完整事务保证。 |
| `L-PROJ` | [LuatOS User Project](https://wiki.luatos.org/develop/cli/project.html) | 用户项目的 `main.lua` 入口、项目配置与工具化组织参考。 | 具体打包/上传目录以项目工具版本和配置为准。 |
| `C-EXPERIENCE` | [嵌入式 C 团队代码规范](../../C/embedded-c-team-standard-v1.md) | 显式分层、资源所有权、失败恢复、可复现发布和证据边界等工程经验。 | 不把 C 专有语言规则或共享治理流程自动套用为 Lua 硬规则。 |

## 使用原则

1. 本规范对 LuatOS API 的约束只引用官方资料中能直接支持的行为；动态特性边界、资源上限、传统结构和验证分工等属于产品工程裁决，见 [规则来源矩阵](../../LuatOS/luatos_rule_source_matrix.md)。
2. 目标模组、`.soc`/固件版本、LuaTools/打包器版本、可选库和板级引脚必须记录在项目 `luatos_project_profile.md`，而不是从在线网页或 PC 解释器版本推断。
3. 复制官方 demo、配置或文档片段时，须先核对其许可证、归属和版本；本规范包默认只发布团队自编文档和官方链接。
4. 官方页面更新后，若影响返回值、任务上下文、存储/FOTA/低功耗语义，必须复核主规范、项目配置和测试证据。
