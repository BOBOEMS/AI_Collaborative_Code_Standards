# LuatOS / Lua 嵌入式规范包

本分册面向个人或小团队的 LuatOS 产品开发，支持“项目负责人设计和实机验证，AI 辅助编写与讲解代码”的协作方式。

核心原则：

> 保留 C 的组织方式，保留 Lua 的表达方式，遵守 LuatOS 的调度方式。

V1.3 进一步固定当前项目已经采用的接口习惯：公开驱动接口可使用 C 风格模块前缀，LuaLS 负责静态类型提示，运行时只在不可信边界校验；读取返回值固定为 `ok, data, error_code, error_context`，数据位置和错误位置不复用。

本版不强制 PC Mock、PR、多人评审、R0/R1/R2 或正式豁免。可靠性规则以及排版、命名、函数可读性、稳定错误码和具名状态均为正式 `MUST` 约定；规则中的目标值和明确例外按完整语义判断，不机械卡数字。

| 文件 | 用途 |
| --- | --- |
| [luatos-embedded-team-standard-v1.md](luatos-embedded-team-standard-v1.md) | V1.3 主规范：传统结构、LuaLS 类型边界、固定返回位置、模块边界、任务调度、资源、硬件、低功耗和验证分工。 |
| [luatos_pr_checklist.md](luatos_pr_checklist.md) | 开发自检和测试交接表；文件名为兼容旧链接保留。 |
| [luatos_project_profile_template.md](luatos_project_profile_template.md) | 记录模组、固件、目录、打包映射、硬件事实、API 差异、任务、资源和证据位置。 |
| [.editorconfig](.editorconfig) | 可选的 UTF-8/LF、4 空格和 100 列编辑器提示。 |
| [luatos_rule_source_matrix.md](luatos_rule_source_matrix.md) | 区分官方事实、旧嵌入式经验、团队裁决和项目事实。 |
| [validate_luatos_standard.ps1](validate_luatos_standard.ps1) | 校验编码、规则编号、矩阵/清单覆盖和本地 Markdown 链接。 |
| [../规范依据/LuatOS/SOURCES.md](../规范依据/LuatOS/SOURCES.md) | LuatOS 官方资料入口和引用边界。 |

## 首次采用

1. 项目尚无等价技术配置时，才从 [项目技术配置模板](luatos_project_profile_template.md) 建立一份；已有 `PROJECT_GUIDE`、板级说明或发布清单时只补缺失字段，不创建重复文档。未知硬件和协议事实保留“待确认”。
2. 根据已有习惯确定目录、公开函数命名、点/冒号调用和错误码来源；不需要一次创建所有目录。
3. 在公开接口和跨文件数据结构上启用 LuaLS 注解，并明确哪些入口仍需运行时校验。
4. 每次只实现一个可独立烧录、观察和失败的小单元。
5. AI 使用 [开发自检表](luatos_pr_checklist.md) 提供测试入口、步骤、预期日志和故障判断。
6. 项目负责人使用 LuaTools 环境或实板执行调试并反馈原始结果。
7. 未经负责人验证的功能保持“已编写，待验证”。

## 与 C 规范的关系

- C/FreeRTOS/MCU 工程继续使用 [C 分册](../C/README.md)。
- LuatOS 可以沿用 C 项目的应用、任务、协议、设备和外设分层，但不能照搬抢占式调度、阻塞等待和资源管理假设。
- [共享治理文件](../共享/README.md) 仍供需要正式团队流程的项目选用，LuatOS V1.3 不再默认依赖它。
- LuatOS API 是否可用以及实际返回行为，以项目固定的模组、固件、LuaTools、官方资料和负责人测试结果为准。
