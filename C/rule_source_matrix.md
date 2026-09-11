# 嵌入式 C 团队规范：规则来源矩阵

> 状态：V2.1 试运行候选版配套文件  
> 适用对象：5 人 MCU/FreeRTOS 固件团队  
> 权威规则：[`rules/`](rules/) 中的按主题分片  
> 完整合订版：[`embedded-c-team-standard-v1.md`](embedded-c-team-standard-v1.md)  
> 依据清单：[`../规范依据/C/SOURCES.md`](../规范依据/C/SOURCES.md)

## 1. 目的与标记

本矩阵用于回答三个问题：规则参考了哪里、团队做了什么裁决、如何检查。它不是
BARR-C、MISRA-C、Zephyr 或 OpenTitan 的合规声明；`rules/` 权威分片及其生成的合订版才是团队执行基线。

| 标记 | 含义 |
| --- | --- |
| `P` | 上游资料包含与团队规则直接一致或高度相近的原则。 |
| `A` | 团队借鉴上游思路后，按 MCU、FreeRTOS、Keil/ARMCC5 场景作了调整。 |
| `T` | 团队依据产品风险自行制定；不能声称由该上游规范直接要求。 |
| `—` | 当前离线资料未作为该类规则的依据。 |

“主规范规则 ID”使用权威分片中的稳定 ID 或连续范围。一个范围可能同时包含上游原则和
团队补强，最终裁决以“TEAM 裁决与最低检查方式”列为准；不得为了凑齐追溯关系而把团队规则
错误归因给上游。

## 2. 来源代号

| 代号 | 本地依据 | 主要用途 |
| --- | --- | --- |
| `BARR` | [`BARR-C-2018-Embedded-C-Coding-Standard.pdf`](../规范依据/C/BARR-C/BARR-C-2018-Embedded-C-Coding-Standard.pdf) | 嵌入式 C 的模块、类型、函数、命名、宏和缺陷防护实践。 |
| `Z-CG` | [`zephyr-coding-guidelines.rst`](../规范依据/C/Zephyr/zephyr-coding-guidelines.rst) | MISRA-C 子集式工程规则、严重度、可追溯性和可检查性。 |
| `Z-STYLE` | [`zephyr-c-code-style.rst`](../规范依据/C/Zephyr/zephyr-c-code-style.rst)、[`zephyr-naming-conventions.rst`](../规范依据/C/Zephyr/zephyr-naming-conventions.rst) | 新改动风格、命名、100 列、完整花括号和公共符号前缀。 |
| `Z-TOOL` | [`zephyr-clang-format`](../规范依据/C/Zephyr/zephyr-clang-format)、[`zephyr-checkpatch.conf`](../规范依据/C/Zephyr/zephyr-checkpatch.conf) | 自动检查的工程化方式；配置只作对照，不直接复制。 |
| `OT-STYLE` | [`opentitan-c-cpp-coding-style.md`](../规范依据/C/OpenTitan/opentitan-c-cpp-coding-style.md) | 指针、条件与循环、注释、API、C 命名、宏和静态声明。 |
| `OT-TOOL` | [`opentitan-clang-format`](../规范依据/C/OpenTitan/opentitan-clang-format) | Google 基线与右侧指针星号的配置对照；不直接复制。 |
| `TEAM` | 主规范、项目配置、评审与验证记录 | 产品、硬件、RTOS、工具链和团队流程的最终裁决。 |

上游版本和 SHA-256 以 `../规范依据/C/SOURCES.md` 为准；更新证据快照后必须重新审查本矩阵。

### 2.1 本次修订的补充依据

以下为公开链接，核对日期为 2026-09-10；未把它们加入离线快照或赋予现有快照的哈希。

| 依据 | 条款/内容 | 对应规则与团队裁决 |
| --- | --- | --- |
| [WG14 N1570 C11 委员会草案](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf) | §6.3.2.3 指针转换；§6.5.5 除法/取余；§6.7.6.2~3 数组与形参调整；§7.5 errno；§7.21.6.5 snprintf；§7.24.2.4 strncpy | `API-003/008`、`ERR-005`、`TYP-009`、`MEM-007/008`：C 语言行为是依据，隔离方式、默认禁用 VLA/alloca 及验证门禁是 TEAM 决策；不要求 ARMCC5 项目切换 C11。 |
| [FreeRTOS V10.0.0 参考手册](https://www.freertos.org/media/2018/FreeRTOS_Reference_Manual_V10.0.0.pdf) | 队列等 API 的 portMAX_DELAY 和 INCLUDE_vTaskSuspend 条件 | `RTOS-002`、`ERR-003`：允许有设计依据的无限事件等待，项目仍须核对所用内核版本和具体 API。 |
| [Microsoft PowerShell 字符编码说明](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_character_encoding) | Windows PowerShell 对无 BOM、含非 ASCII 字符脚本的解释方式 | 维护脚本最低 PowerShell 7，统一 `pwsh` 入口；不改变 C/H 的 UTF-8 无 BOM 约定。 |
| 项目选定的编译器、内核及 MCU 手册 | 目标项目记录精确版本和章节 | `IRQ-005`、`OTA-005`：DMA 停止访问及 Boot 交接的具体顺序按目标核对，通用规范只规定契约与验证内容。 |

## 3. 规则 ID 映射

| 主规范规则 ID | BARR | Zephyr | OpenTitan | TEAM 裁决与最低检查方式 |
| --- | --- | --- | --- | --- |
| `SRC-001~002` | `A` | `P`（只约束新增/修改代码） | `A` | 厂商库、CMSIS、FreeRTOS 内核、生成文件保持上游原貌；评审检查变更范围和来源。 |
| `ARC-001~003` | `P` | `A` | `P`（Static Declarations） | 业务、服务、驱动、BSP 单向依赖；架构评审和头文件接口检查。 |
| `FMT-001~004, FMT-009~011` | `P` | `A` | `P`（Included files） | ASCII 路径、自研新增 C/H 使用 UTF-8 无 BOM、非 UTF-8 自研文件独立迁移、显式 guard；头文件独立包含语法检查；include 分组由评审检查。 |
| `FMT-005~008` | `A` | `A` | `A` | 4 空格、禁 Tab、100 列、Attach、`uint8_t *buffer`；布局由团队 `.clang-format` 检查，完整花括号由评审检查。 |
| `NAM-001~009` | `P` | `P` | `P`（C naming） | `T`：变量、`const` 对象和宏使用带模块语义的小写下划线；函数使用 `Module[_Feature]_VerbObject`；结构体/联合体使用 `UpperCamelCase_t`，枚举使用 `UpperCamelCaseEnum_t`，认可的缩写保持全大写，枚举值使用带前缀的 `UPPER_SNAKE_CASE`。固定外部符号、include guard 和 `error.h` 的 errno 风格名属于明确例外；格式和语义由评审检查。 |
| `TYP-001~008` | `P` | `P` | `P`（Constants and Preprocessor Macros） | 协议/存储/寄存器使用明确宽度；编译警告、静态检查和边界测试。 |
| `TYP-009` | `—` | `—` | `—` | `T`：根据 C 运算语义检查除零及提升/转换后有符号结果不可表示的边界，保存边界测试。 |
| `API-001~007` | `P` | `P` | `P`（Public function documentation） | `T`：所有新增或有效代码发生修改的自研函数补齐中文函数注释；状态接口仅以 `0` 表示成功、以负数符号表示失败；完整 `error.h` 为可选目录，裁剪时只删除未使用项，保持宏定义形式、文件引用方式及保留项的符号、数值、别名和语义；同时检查指针方向、长度、上下文、副作用和失败路径。 |
| `API-003, API-008` | `—` | `—` | `—` | `T`：固定容量须有可验证契约，形参数组声明不证明容量；项目私有负值目录与外部同名宏按翻译单元隔离、显式适配；检查实际包含链、宏诊断、最终值与受支持变体。 |
| `ERR-001~005` | `P` | `P` | `P`（Formatting of loops and conditionals） | 一次操作等待有界，事件任务无限等待按 RTOS-002 论证；异常路径恢复资源；禁止未定义行为，实现定义行为须有工具链依据、封装和验证。 |
| `MEM-001~006` | `P` | `P` | `A` | 外部长度/索引先校验，运行期动态分配默认禁止；静态检查、边界测试和内存预算检查。 |
| `MEM-007~008` | `—` | `—` | `—` | `T`：VLA/alloca 默认禁用，豁免须证明最坏栈预算；字符串须验证终止、容量与截断，保存静态检查及边界测试。 |
| `PRE-001~004` | `P` | `P` | `P`（Constants and Preprocessor Macros） | 优先 `static inline`，宏参数单次求值；每个受支持构建变体必须被周期性构建。 |
| `IRQ-001~007` | `A` | `A` | `—` | `T`：基于 MCU/FreeRTOS 实际配置制定；IRQ 逻辑优先级与 NVIC 编码对照、DMA 停止访问及迟到通知处理；代码评审与目标板测量。 |
| `RTOS-001~009` | `—` | `A` | `—` | `T`：记录任务职责、优先级、栈和队列所有权；无限事件等待须有设计依据及健康监督；栈高水位、溢出 Hook 和并发测试。 |
| `TIM-002~004` | `A` | `P`（整数/控制流安全原则） | `—` | `T`：使用回绕安全比较，嵌套调用共享一个截止时间/预算；边界和回绕测试。 |
| `TIM-001, TIM-005~006` | `A` | `A` | `—` | `T`：显式状态/事件/超时，监督者喂狗；一次操作重试有次数或总时间上界及耗尽动作，长期重连单独设计退出和资源约束；故障注入和目标板验证。 |
| `TYP-007, MEM-004` | `P` | `P` | `A` | `T`：禁止直接把编译器布局当寄存器、协议或存储格式；序列化测试和兼容性审查。 |
| `NVM-001~005` | `A` | `A` | `—` | `T`：magic、版本、长度、序号、校验和原子更新；掉电注入、升级/降级兼容测试。 |
| `OTA-001~004` | `—` | `A` | `A` | `T`：校验目标、地址、长度、版本和完整性；联网产品用签名/MAC，CRC 不代替认证；目标板回滚测试。 |
| `OTA-005` | `—` | `—` | `—` | `T`：按具体 MCU/内核/编译器定义 Boot 交接，核验入口、初始栈、向量表、中断/DMA 及外设责任，保留目标板交接与拒绝路径证据。 |
| `DIA-001~004` | `A` | `A` | `P`（Comments/API/code lint 的相关实践） | 生产错误不能只靠 `assert`；日志分级且不得泄密；评审和故障测试。 |
| `DOC-001~010` | `P` | `P` | `P`（Comments、TODO、API documentation） | `T`：新增中文文件职责说明；新增或修改的函数、结构体/联合体、枚举和宏按适用字段说明；关键硬件、OTA、存储和恢复规则关联依据、需求与测试编号；评审检查内容有效性和链接可追踪性。 |
| `RTOS-006~009, BLD-007` | `A` | `A` | `—` | `T`：项目配置给出阈值和余量，发布构建保留 map/size 与目标板运行证据，超预算阻断发布。 |
| `REV-001~006` | `—` | `A` | `A` | `T`：团队模式保留非作者人数要求；个人+AI 以项目明确采用的协作流程执行。按技术风险核查，适用门禁与现有记录共用，不重复审查或填写表单。 |
| `REV-004, BLD-001~009` | `A` | `P` | `P`（Code Lint） | 主配置 clean build、差分零新增警告、改动文件格式检查、按风险保存测试证据。 |
| `GOV-001~002, HOT-001~004, EXC-001~004` | `A` | `P`（严重度/偏离管理思路） | `A` | 稳定规则 ID、原因、风险、替代措施、责任人与到期日；批准角色按项目方式，技术验证与回滚要求保留，现有等价记录可引用；季度或事故后复盘。 |
| `SRC-003~004` | `—` | `A` | `A` | 上游配置和资料保留许可证、归属、固定提交与哈希；对外发布前单独复核。 |

## 4. 格式冲突与团队裁决

团队 `.clang-format` 是独立编写的执行配置，以 clang-format `19.1.7` 的稳定选项表达团队规则；上游配置只作
对照。以下差异是有意裁决，不应通过复制上游配置覆盖：

| 项目 | Zephyr 快照 | OpenTitan 快照 | TEAM 裁决 |
| --- | --- | --- | --- |
| 基线 | LLVM | Google | LLVM，只选团队需要的稳定项。 |
| 缩进 | `IndentWidth: 8`，允许 Tab 用于缩进/续行 | Google 默认通常为 2 空格，快照未覆写 | 4 空格，`UseTab: Never`。 |
| 续行缩进 | 8 | 继承 Google | 4。 |
| 列宽 | 100 | 继承 Google 的较窄默认值 | 100。 |
| 花括号换行 | `BreakBeforeBraces: Linux` | 继承 Google | `Attach`，函数和控制语句的左花括号均不另起一行。 |
| 指针星号 | 快照未显式覆写 | `PointerAlignment: Right` | Right，写作 `uint8_t *buffer`。 |
| 短语句 | 禁短 block/case/enum/function/if/loop | 显式禁短 if/loop | 禁短 block/case/enum/function/if/loop。 |
| include | Zephyr 专用分类，禁止自动排序 | OpenTitan 生成寄存器头专用分类 | 保留项目已有分组和顺序；格式化器不排序。 |
| 注释 | C 代码禁止 `//` | 允许其风格指南中的形式 | 当前主规范允许普通注释使用 `//`；团队自研代码的新增或修改说明性注释使用中文，文件、函数、类型、宏及跨行关键逻辑优先使用块注释，块注释内部不使用行首 `*` 装饰；不得把 Zephyr 规则自动升级为团队规则。 |

`.clang-format` 只能统一排版，不能证明分支已经加花括号，也不能检查命名、超时、并发、
存储一致性或 OTA 安全。这些规则必须由编译器、静态检查、评审和测试共同覆盖。

## 5. 许可证与引用边界

1. BARR-C PDF 受 Barr Group 版权保护，只保留为团队内部证据；不得对外发布、再分发全文，
   团队规范只做自行表述和必要的短引用，并指向官方来源。
2. Zephyr 仓库顶层采用 Apache-2.0；本地许可证见 [`Zephyr/LICENSE`](../规范依据/C/Zephyr/LICENSE)。下载的 `zephyr-clang-format` 也明确带
   `SPDX-License-Identifier: Apache-2.0`。若复制或修改并分发其原文件，必须保留版权、
   许可证和适用的 NOTICE；`checkpatch` 工具本身为 GPL 许可，不把该工具源码并入本项目。
3. OpenTitan 仓库说明“除另有标注外”采用 Apache-2.0；本地许可证见 [`OpenTitan/LICENSE`](../规范依据/C/OpenTitan/LICENSE)。若复制或修改并分发其原文件，
   必须保留 Apache-2.0 许可证、版权和适用的 NOTICE，并先检查目标文件是否另有标注。
4. 本团队 `.clang-format` 由 LLVM 基线和团队明确决策独立编写，不是 Zephyr/OpenTitan
   配置的副本；本矩阵仍保留来源说明，以记录设计影响和差异。
5. `规范依据/` 中的上游快照仅作可追溯证据，不是构建依赖。对外发布规范包时，默认只
   发布团队自编文件和官方链接；是否附带上游原文必须经过许可证复核。
6. Apache-2.0 授权、BARR-C 参考或 Zephyr/OpenTitan 的规则映射，都不等于 MISRA、功能
   安全、网络安全或产品认证合规。

## 6. 维护事项

- 规则正文只在 `rules/` 权威分片中维护；修改后重新生成合订版，并运行 `validate_c_standard.ps1`。
- 项目确定主配置、编译器版本、Device Pack、FreeRTOS 配置和链接脚本后，将它们写入项目
  执行配置，而不是继续堆入通用规范。
- 若以后更换 clang-format 主版本，先在小范围自研模块验证差异，再更新配置头注释、CI
  固定版本和本矩阵；禁止直接全仓重排。
