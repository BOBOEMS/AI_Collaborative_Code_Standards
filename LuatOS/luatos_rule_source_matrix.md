# LuatOS / Lua 嵌入式规范：规则来源矩阵

> **状态**：V1.3 配套文件
> **主规范**：[luatos-embedded-team-standard-v1.md](luatos-embedded-team-standard-v1.md)
> **依据清单**：[../规范依据/LuatOS/SOURCES.md](../规范依据/LuatOS/SOURCES.md)

本矩阵区分官方 API/运行事实、旧嵌入式项目经验和本规范作出的产品裁决。它不是 LuatOS、Lua 或 C 的官方合规声明。

| 标记 | 含义 |
| --- | --- |
| `P` | 对应工具或平台的官方资料直接描述的 API、注解语义、运行模型或工程事实。 |
| `E` | 来自既有 MCU/FreeRTOS 产品的可维护性和可靠性经验，经 Lua/LuatOS 调整。 |
| `T` | 本规范根据嵌入式产品风险作出的决定，不宣称来自官方原文。 |
| `PROJECT` | 必须由具体模组、固件、硬件、产品需求或项目负责人确定。 |

## 1. 来源代号

| 代号 | 来源 | 用途 |
| --- | --- | --- |
| `L-SYS` | [LuatOS `sys` 库](https://wiki.luatos.com/api/sys.html) | task、wait、timer、publish/subscribe、`sys.run()` 和回调上下文。 |
| `L-TASK` | [LuatOS LuaTask](https://wiki.luatos.com/luaGuide/luatask.html) | Lua 协作式任务模型。 |
| `L-I2C` | [LuatOS `i2c`](https://wiki.luatos.com/api/i2c.html) | `setup`、`readReg`、`writeReg`、`transfer` 的参数和文档返回语义。 |
| `L-GPIO` | [LuatOS `gpio`](https://wiki.luatos.com/api/gpio.html) | GPIO 输入、输出、中断、唤醒脚和返回句柄。 |
| `L-PM` | [LuatOS `pm`](https://wiki.luatos.com/api/pm.html) | 电源和低功耗 API 入口；具体能力仍依赖模组和固件。 |
| `L-FOTA` | [LuatOS `fota`](https://wiki.luatos.com/api/fota.html) | FOTA 初始化、写入、完成状态和返回值入口。 |
| `L-FSKV` | [LuatOS `fskv`](https://wiki.luatos.com/api/fskv.html) | KV 初始化、读写和返回值入口。 |
| `L-PROJ` | [LuatOS User Project](https://wiki.luatos.org/develop/cli/project.html) | 入口、模块加载和工具化组织参考。 |
| `LUALS` | [LuaLS 注解](https://luals.github.io/wiki/annotations/) | `@param`、`@return`、`@class`、`@field`、可空类型和 `@cast` 的静态语义。 |
| `C-EXPERIENCE` | [嵌入式 C 团队代码规范](../C/embedded-c-team-standard-v1.md) 及项目既有 MCU/FreeRTOS 结构 | 显式分层、资源所有权、错误恢复和发布可追溯。 |
| `TEAM` | 本规范和具体项目记录 | Lua 特性边界、简化接口、测试分工和资源上限。 |

官方网页会变化；项目必须在技术配置中固定实际使用的模组、固件、LuaTools 和验证结果。

## 2. 规则映射

<!-- RULE-MATRIX-BEGIN -->
| 主规范规则 | 性质 | 精确来源 | 项目验证要求 |
| --- | --- | --- | --- |
| `LUA-ARC-001~004`、`LUA-ARC-007` | `P/E/T` | `L-SYS`、`L-PROJ`、`C-EXPERIENCE` | 核对真实入口、打包映射和调用方向。 |
| `LUA-ARC-005~006` | `E/T/PROJECT` | `C-EXPERIENCE`、`TEAM` | 按当前板级连接和实例数量确认配置边界、单例及点/冒号调用。 |
| `LUA-LANG-001~003` | `E/T/PROJECT` | `TEAM` | 核对目标固件 Lua 语义和实际启用库。 |
| `LUA-STYLE-001~010` | `E/T` | `C-EXPERIENCE`、`TEAM` | 全部为 `MUST`；参考阈值按完整语义检查，不机械卡数字。 |
| `LUA-TYPE-001~003` | `P/T` | `LUALS`、`TEAM` | LuaLS 诊断通过，注解与所有返回分支一致；注解不算运行时证据。 |
| `LUA-TYPE-004` | `E/T` | `C-EXPERIENCE`、`TEAM` | 列出不可信入口并确认类型、范围和长度只在正确边界检查。 |
| `LUA-API-001~002` | `T` | `TEAM` | 核对调用方变量位置、错误分支和固定返回槽位。 |
| `LUA-API-003` | `P/T/PROJECT` | `L-I2C`、`L-GPIO` 及功能所用官方 API | 固定模组/固件，保存与文档一致或不一致的实测结果。 |
| `LUA-API-004~005` | `E/T` | `L-SYS`、`C-EXPERIENCE`、`TEAM` | 验证失败状态、有限重试、退避和最终处理。 |
| `LUA-TASK-001~006` | `P/E/T` | `L-SYS`、`L-TASK`、`C-EXPERIENCE` | 验证任务让出、回调禁止等待、超时、所有者和停止路径。 |
| `LUA-RES-001~005` | `P/E/T` | `L-FSKV`、`C-EXPERIENCE`、`TEAM` | 测量实际上限、峰值、超限策略和掉电恢复。 |
| `LUA-PRD-001~002` | `P/E/T/PROJECT` | `L-I2C`、`L-GPIO`、`C-EXPERIENCE` | 保存设备 ID、关键回读、连续样本以及已知 BSP/API 差异。 |
| `LUA-PRD-003~004` | `E/T/PROJECT` | `C-EXPERIENCE`、`TEAM` | 使用当前网络/安全 API 资料，验证业务 ACK、身份和敏感信息边界。 |
| `LUA-PRD-005~007` | `P/E/T/PROJECT` | `L-PM`、`L-FOTA`、`C-EXPERIENCE` | 在指定模组/固件上验证休眠恢复、空间、完整性和失败恢复。 |
| `LUA-DIA-001~002` | `E/T` | `C-EXPERIENCE`、`TEAM` | 检查稳定 TAG、日志所有者、频率和脱敏。 |
| `LUA-VER-001~005` | `E/T/PROJECT` | `C-EXPERIENCE`、`TEAM` | 静态、LuaTools 和实板证据分开；负责人未反馈前保持待验证。 |
| `LUA-SRC-001` | `E/T` | `L-PROJ`、`C-EXPERIENCE`、`TEAM` | 记录 demo、旧项目、第三方和 AI 代码的版本与适用边界。 |
<!-- RULE-MATRIX-END -->

## 3. 使用边界

1. `P` 只表示来源直接支持该 API 或运行事实，不表示来源要求本规范的目录、命名、返回架构或测试流程。
2. `T` 表示本规范结合嵌入式风险和当前项目习惯作出的裁决；这类规则不得伪装成 LuatOS 官方要求。
3. `PROJECT` 内容必须绑定模组、固件、硬件、LuaTools 和原始证据。官方文档与实测冲突时保留最小复现和已验证替代路径，不把单一固件异常写成通用结论。

## 4. 维护要求

- 主规范增加、删除或修改规则含义时，同步更新本矩阵、开发自检表和项目配置模板。
- 官方资料改变任务、回调、存储、低功耗或升级语义时，先核对目标固件，再调整项目和规范。
- 旧项目仍引用 V1.0 规则编号时，按规则含义迁移，不进行无判断的编号替换。
- 不复制或再发布官方文档全文；使用厂商 demo 和第三方代码前核对来源及许可边界。
