# C 代码规范 AI 读取入口

本文件只管理 C/FreeRTOS/MCU 技术规范的按需读取，不包含、复制或替代任何 AI 协作规范。

## 基础读取

- 先根据用户请求、拟修改文件和必要调用链，以只读方式判断涉及的技术领域。
- 新增或修改任何 `.c`、`.h` 文件时，必须读取 `rules/00-core.md` 和 `rules/05-comments.md`。
- 同时涉及多个领域时，读取对应分片的并集。
- 编码前把已读取分片、版本或内容标识、适用规则及检查项关联到本次已有工作记录；已有记录可引用，不另建同内容报告。
- 当前上下文中已读取且版本、适用范围未变化的内容可复用；新会话或上下文恢复后重新读取所需分片，历史摘要和“以前读过”不代替原文。
- 只有全面规范审计、规范本身维护、无法确定适用分片或用户明确要求时，才读取 `embedded-c-team-standard-v1.md` 合订版。

## 专项路由

| 涉及内容 | 按需读取 |
| --- | --- |
| 类型、整数、位操作、函数、接口、返回值、错误码、指针、缓冲区、宏、控制流 | `rules/10-language-api.md` |
| 寄存器、GPIO、时钟、中断、ISR、DMA、FreeRTOS、任务、锁、队列、栈、堆 | `rules/20-hardware-concurrency.md` |
| 状态机、时间、超时、重试、看门狗、日志、断言、故障码 | `rules/30-state-protocol-time.md` |
| 协议、帧格式、字节序、CRC、RS485 或协议状态 | `rules/10-language-api.md` 和 `rules/30-state-protocol-time.md` |
| Flash、FRAM、EEPROM、NVM、OTA、Boot、分区、回滚、掉电恢复 | `rules/40-storage-ota-boot.md` |
| 构建、链接、启动文件、工具链、静态检查、CI、资源预算、安全、评审、发布、豁免、热修复 | `rules/50-build-review.md` |
| 规则来源、许可证边界、项目配置、规范变更 | `rules/90-reference.md` |

## 示例与附件

- 需要注释模板时读取 `examples/comment-templates.md`。
- 裁剪 `error.h` 时读取 `examples/error-h-cropping.md`；不得将错误码宏改为枚举。
- 集成标准库或第三方错误码时核对 `API-008`；GCC 项目可按 `README.md` 使用 `check_error_header_usage.ps1` 检查实际包含链。
- 新建 C 模块时读取 `examples/module-template.md`。
- 代码完成或执行评审时读取 `pr_checklist.md`，把适用门禁并入本次已有自检或评审；相同对象的有效结果和证据直接引用，不额外启动一轮 C 规范审查。
- 仅在项目初始化或技术配置变化时读取 `project_profile_template.md`，用于补齐现有权威配置的缺项，不默认复制新文件。
- 仅在追溯规则依据或处理规则冲突时读取 `rule_source_matrix.md`。

无法确定路由时，先读取最可能相关的分片；仍无法确定时再读取合订版。

`README.md` 中的合订版生成和规范包校验仅用于维护本规范；业务代码修改按项目检查入口执行，不因此重建或审计整个规范包。
