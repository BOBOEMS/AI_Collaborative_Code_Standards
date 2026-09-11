# 基础、范围与命名

> 所有 C/H 修改必读。

<!-- bundle-body-start -->

> **适用范围**：裸机或 FreeRTOS 的 MCU 固件，尤其是 GD32/STM32、ARMCC5/Keil、GCC Arm Embedded 工程。
>
> **生效范围**：自批准日起约束新文件和新改动。芯片厂商库、CMSIS、FreeRTOS 内核、第三方库、自动生成代码不做无关重排；团队新增的包装层、补丁和业务代码执行本规范。
>
> **试运行建议**：先执行 4 周，按规则 ID 记录误报、豁免、评审耗时及发现的缺陷；复盘时优先澄清适用条件和删除低收益要求，再决定是否正式批准。
>
> **共享治理**：协作方式、规则执行级别及团队人数/角色的适用边界见 [共享目录](../../共享/README.md)。C 技术要求适用于个人+AI 与多人团队；项目确认的方式决定复审与批准流程，不改变技术验收要求。

| 文档元数据 | 当前值 |
| --- | --- |
| 状态 | V2.1 试运行候选版，尚未正式批准 |
| 规范维护人 | 待团队指定 |
| 批准人 | 待团队指定 |
| 试运行起止日期 | 待填写，周期为 4 周 |
| 下次复盘日期 | 待填写 |

## 1. 目标、规则编号与共用治理

本规范按以下顺序优化：**安全可维护、可验证、便于协作、风格一致**。它吸收 BARR-C 的嵌入式实践、Zephyr 的工程约束，并把 OpenTitan 仅作为自动格式配置的参考；本规范不是 MISRA 合规声明，也不替代产品安全认证。

每条可执行规则使用稳定 ID。ID 发布后不复用；删除的 ID 保留在变更记录中。`AUTO-BLOCK`、`REVIEW-BLOCK`、`ADVISORY` 的含义以及冲突优先级统一见 [团队治理与评审基线](../../共享/团队治理与评审基线.md)。

同一次自检或评审核对本次适用的技术规则，共用已有有效结果；`REVIEW-BLOCK` 不表示每条规则都要独立 AI 复审。规范核对发现需要补充接口、状态、超时或恢复等设计时，先按项目流程提出并确认，不直接增加未获确认的实现。

- **[GOV-001][REVIEW-BLOCK]** 不能满足阻断规则时，必须按 [共用豁免流程](../../共享/豁免与紧急修复流程.md) 获得有期限的豁免；口头约定不算豁免。
- **[GOV-002][REVIEW-BLOCK]** 规则与自动工具冲突时，必须修正规范或工具配置；修复前按 `GOV-001` 临时豁免，不得长期依赖人工忽略。

### 1.1 C/FreeRTOS 的 R2 扩展

除共享基线外，Boot/链接、时钟/电源、IRQ/DMA/并发、FreeRTOS 栈/heap、NVM、OTA、看门狗、安全、协议兼容和资源预算的变更均为 R2；具体验证要求见第 16 节和 [C 合并检查表](../pr_checklist.md)。

## 2. 适用边界与目录责任

### 2.1 上游代码

- **[SRC-001][REVIEW-BLOCK]** 芯片厂商库、CMSIS、FreeRTOS 内核及 portable 层、第三方协议栈、启动文件、链接脚本和生成代码必须在仓库说明中记录来源、版本、许可证及本地补丁。
- **[SRC-002][REVIEW-BLOCK]** 修改上游代码时，必须把本地补丁限制在需求范围内，并保留可识别的差异和验证证据；禁止仅为符合团队格式而重排上游文件。

### 2.2 分层规则

推荐调用方向：

```text
业务/状态机/协议  ->  服务层  ->  驱动抽象层  ->  BSP/HAL/寄存器
                                  ->  FreeRTOS/芯片库
```

- **[ARC-001][REVIEW-BLOCK]** 生产业务代码不得直接读写寄存器或调用厂商 HAL，必须经驱动或 BSP 接口。板级 bring-up、诊断程序和遗留适配层如需例外，必须隔离目录、明确退出产品构建的方式，或取得有范围和到期日的豁免。
- **[ARC-002][REVIEW-BLOCK]** 驱动不得包含产品流程、联网协议或业务策略；BSP 只处理板级引脚、时钟、电源和外设实例差异。
- **[ARC-003][AUTO-BLOCK]** 模块只能暴露头文件声明的接口；模块私有函数和状态必须使用 `static`。

## 3. 文件、编码与格式

### 3.1 文件规则

- **[FMT-001][ADVISORY]** 一个功能模块通常由一对 `module_name.c` 和 `module_name.h` 组成。
- **[FMT-002][AUTO-BLOCK]** 新文件名、目录名和 `#include` 路径必须使用 ASCII `lower_snake_case`；符号命名按第 4 节分别处理，不适用“一律小写”。
- **[FMT-003][AUTO-BLOCK]** 团队自研的新增 `.c` 和 `.h` 文件必须使用 UTF-8（无 BOM）；同一文件内换行符必须一致，禁止提交无关的编码或换行转换。
- **[FMT-004][AUTO-BLOCK]** 每个头文件必须有唯一 include guard，例如 `RTU_DRV_ADC_H`；项目不依赖 `#pragma once`。
- **[FMT-010][REVIEW-BLOCK]** 现有非 UTF-8 自研文件需要新增或修改中文注释时，必须先通过独立的编码迁移改动转换为 UTF-8（无 BOM），并完成该项目要求的基础构建或语法检查；编码迁移不得与功能修改混合。厂商库、第三方代码和自动生成代码保持上游编码，除非取得有范围的豁免。
- **[FMT-011][REVIEW-BLOCK]** 团队自研头文件必须自行包含声明所需的类型和宏定义，不得依赖调用方先包含其他头文件；在项目声明支持的配置下，以仅包含该头文件的最小翻译单元验证语法。依赖生成配置的头文件必须明确生成前置步骤。

### 3.2 排版规则

- **[FMT-005][AUTO-BLOCK]** 缩进为 4 个空格，禁止 Tab；自动格式目标列宽为 100。
- **[FMT-006][AUTO-BLOCK]** 函数及控制语句的左花括号同行，块内语句另起一行；右花括号另起一行，`else`、`else if`、`do` 对应的 `while` 以及类型声明尾部按团队 `Attach` 配置紧随右花括号。
- **[FMT-007][REVIEW-BLOCK]** `if`、`else`、`for`、`while`、`do` 和 `switch` 的所有分支必须使用花括号；格式化工具不能替代此项语义检查。
- **[FMT-008][AUTO-BLOCK]** 二元运算符两侧、逗号后和关键字后各留一个空格；指针星号贴近变量名，如 `uint8_t *buffer`。
- **[FMT-009][REVIEW-BLOCK]** `.c` 文件的 include 顺序为：本模块头文件、C 标准库头文件、项目头文件、第三方/RTOS 头文件、芯片/系统头文件，各组之间空一行。团队格式化配置保留现有 include 顺序，因此由评审检查此项。

```c
#include "drv_adc.h"

#include <stdbool.h>
#include <stdint.h>

#include "app_fault.h"
#include "board_config.h"

#include "FreeRTOS.h"
#include "task.h"

#include "gd32f30x_adc.h"
```

## 4. 命名规则

- **[NAM-001][REVIEW-BLOCK]** 名称必须表达业务含义和单位；禁止使用 `data1`、`temp2`、`flag` 等无上下文名称。
- **[NAM-002][REVIEW-BLOCK]** 缩写只使用团队词汇表中的通用缩写；有物理单位的变量必须在名称中写明单位，例如 `timeout_ms`、`voltage_mv`。
- **[NAM-003][REVIEW-BLOCK]** 布尔量使用肯定式名称，如 `is_ready`、`has_fault`、`enable_logging`。

| 对象 | 规则 | 示例 |
| --- | --- | --- |
| 文件 | `lower_snake_case` | `drv_adc.c` |
| 变量、参数、结构体成员 | `lower_snake_case` | `retry_count`、`timeout_ms` |
| `const` 对象、对象式宏、编译期开关 | 带模块前缀的 `lower_snake_case` | `drv_adc_timeout_ms` |
| 函数式宏 | 带模块前缀的 `lower_snake_case` | `drv_bit_mask(bit_index)` |
| 团队自研函数 | `Module[_Feature]_VerbObject` | `CardReader_OTA_GetState()`、`DrvADC_ReadVoltageMV()` |
| 结构体、联合体类型 | `UpperCamelCase_t` | `DrvRS485Config_t` |
| 枚举类型 | `UpperCamelCaseEnum_t` | `SystemStateEnum_t` |
| 枚举值 | 带模块或类型前缀的 `UPPER_SNAKE_CASE` | `SYSTEM_STATE_IDLE` |
| 其他类型别名 | `lower_snake_case_t` | `rtu_status_t` |
| 文件内静态变量 | `s_` 前缀 | `s_sample_count` |
| 跨模块全局变量 | 原则上禁用；批准后使用 `g_模块_含义` | `g_system_uptime_ms` |

- **[NAM-004][AUTO-BLOCK]** 团队自定义的变量、`const` 对象和宏必须匹配 `[a-z][a-z0-9]*(?:_[a-z0-9]+)*`；宏必须带模块前缀，文件内静态变量必须带 `s_` 前缀。禁止使用行首、行尾或连续双下划线形式的团队自定义标识符。
- **[NAM-005][REVIEW-BLOCK]** 跨模块可变全局变量默认禁止；确需使用时必须说明并发、初始化、所有权和修改入口。
- **[NAM-006][ADVISORY]** 不为基本类型创建无抽象价值的 `typedef`，也不以大小写差异表达不同语义。
- **[NAM-007][REVIEW-BLOCK]** 团队自研函数统一使用 `Module[_Feature]_VerbObject`：所属模块在前，可选功能域居中，动作和对象在末尾；普通单词使用大驼峰，团队词汇表认可的 `OTA`、`UART`、`CRC` 等缩写保持全大写。函数名必须包含明确动作，禁止使用缺少动作的 `CardReader_OTA()` 或缺少所属模块且含义模糊的 `Get_OTA_Flag()`。
- **[NAM-008][REVIEW-BLOCK]** C 标准入口、启动文件、ISR、RTOS/HAL 回调、芯片库和第三方接口按其固定签名和名称保留；include guard 保持大写。完整或裁剪的 `error.h` 必须保留既有 errno 风格符号，作为 `NAM-004` 的明确命名例外；符号同名不表示与标准库 errno 数值或返回约定兼容，隔离要求见 `API-008`。
- **[NAM-009][REVIEW-BLOCK]** 结构体和联合体类型使用 `UpperCamelCase_t`，枚举类型使用 `UpperCamelCaseEnum_t`；团队词汇表认可的缩写保持全大写。枚举值使用带模块或类型前缀的 `UPPER_SNAKE_CASE`。例如 `DrvRS485Config_t`、`SystemStateEnum_t` 和 `SYSTEM_STATE_IDLE`。
