# 硬件与并发

> 涉及寄存器、IRQ、DMA、FreeRTOS、栈、堆、锁或队列时读取。

<!-- bundle-body-start -->

## 10. 中断、DMA 与硬件访问

- **[IRQ-001][REVIEW-BLOCK]** ISR 只允许确认/清除中断源、搬运最少数据、更新受控状态并通知任务；不得阻塞、延时、打印、访问文件系统、复杂解析或动态分配。
- **[IRQ-002][REVIEW-BLOCK]** ISR 与任务共享的数据必须说明生产者、消费者、原子性/临界区措施、缓存一致性和丢失策略；`volatile` 不能替代同步。
- **[IRQ-003][REVIEW-BLOCK]** 项目必须维护 IRQ 优先级表，记录 IRQ 名称、逻辑优先级、写入 NVIC 的编码值、是否调用 FreeRTOS API、最大执行时间和共享资源。
- **[IRQ-004][REVIEW-BLOCK]** 调用 FreeRTOS 的 ISR 必须只使用 `...FromISR()` API，并按需执行 `portYIELD_FROM_ISR()`；其抢占紧迫程度不得高于 `configMAX_SYSCALL_INTERRUPT_PRIORITY` 规定的系统调用上限。Cortex-M 项目必须同时核对 `configLIBRARY_MAX_SYSCALL_INTERRUPT_PRIORITY` 与实际 NVIC 编码，并启用 `configASSERT` 捕获非法优先级。
- **[IRQ-005][REVIEW-BLOCK]** DMA 缓冲区必须定义所有权、生命周期、对齐、缓存维护（适用时）和完成/错误/取消通知路径。超时或发出取消请求不等于 DMA 已停止访问；释放、复用或重新挂接缓冲区前，必须依据目标硬件及驱动契约确认 DMA 已停止访问，并处理可能迟到的中断/回调。停止完成的判据、缓存或屏障要求及停止失败的处理方式必须明确，禁止仅清软件标志就归还缓冲区。
- **[IRQ-006][REVIEW-BLOCK]** 寄存器访问仅允许在 BSP/驱动层；读改写前必须确认并发和硬件语义，包括写 1 清零、只写与保留位。
- **[IRQ-007][REVIEW-BLOCK]** 外设初始化、引脚复用、时钟和 IRQ 优先级必须集中配置；禁止不同模块重复初始化同一外设。

## 11. FreeRTOS、栈与堆

- **[RTOS-001][REVIEW-BLOCK]** 每个任务必须记录职责、阻塞条件/周期、优先级、栈预算、看门狗策略、输入队列和输出接口。
- **[RTOS-002][REVIEW-BLOCK]** 任务不得无延时忙等；周期任务使用 `vTaskDelayUntil()`，事件任务阻塞在队列、通知、信号量或事件组上。有响应期限、超时恢复或周期健康检查职责时，必须设置满足该职责的有限超时。没有待完成操作的事件任务可在设计论证后无限等待，但必须记录唤醒源、所持资源、健康监督方式及适用的取消/停机路径，不能持有其他任务继续运行所需的锁。使用 `portMAX_DELAY` 时须核对具体 API、内核版本和 `INCLUDE_vTaskSuspend` 配置下的实际语义；长期无事件不能被误判为任务失活。
- **[RTOS-003][REVIEW-BLOCK]** 队列传递指针时，接口必须声明对象生命周期、所有权转移和释放责任。
- **[RTOS-004][REVIEW-BLOCK]** 共享可变状态优先消息传递；确需共享时必须使用 mutex、临界区或经验证的原子操作。临界区不得包含日志、延时、外设等待或阻塞 API。
- **[RTOS-005][REVIEW-BLOCK]** Mutex 只能在任务上下文使用；ISR 与任务同步必须使用任务通知、队列或 ISR 安全的信号量 API。
- **[RTOS-006][REVIEW-BLOCK]** 项目必须为每个任务定义 `stack_budget_bytes` 和 `min_free_bytes` 验收阈值；在目标板压力场景测量高水位并统一换算为字节。未达到阈值不得发布。
- **[RTOS-007][AUTO-BLOCK]** FreeRTOS 项目必须启用 `configCHECK_FOR_STACK_OVERFLOW >= 2` 和栈溢出 Hook；启用堆时还必须启用 malloc-failed Hook。
- **[RTOS-008][REVIEW-BLOCK]** MSP/中断栈必须结合链接图、最大嵌套中断和最坏调用链设置预算，并在发布检查中保留余量证据。
- **[RTOS-009][REVIEW-BLOCK]** 使用 FreeRTOS heap 时必须固定 heap 实现、总预算、允许分配阶段和失败动作；发布测试必须记录最小历史剩余堆，低于项目阈值时阻断发布。
