# 示例：中文注释

> 需要文件、函数、类型、宏或关键逻辑模板时读取。

<!-- bundle-body-start -->

`/**` 和 `*/` 仅作为边界，中间行不添加装饰性 `*`。文件职责注释示例：

```c
/**
 @file drv_rs485.c
 @brief 实现 RS485 半双工收发、方向控制和 DMA 完成处理。
 @note 本文件只负责驱动层，不解析 Modbus 或 OTA 业务协议。
 */
```

函数注释示例：

```c
/**
 @brief 查看指定卡片的余额。
 @param card_id 输入的卡片标识符缓冲区，不得为 NULL。
 @param card_id_size card_id 的长度，单位为字节，必须符合卡片协议要求。
 @param balance 输出余额，单位为分，不得为 NULL。
 @return 成功时返回 0；失败时返回负值。
 @note 仅允许在任务上下文调用，不得从 ISR 调用。
 */
int32_t CardReader_ReadBalance(const uint8_t *card_id, size_t card_id_size, uint32_t *balance);
```

结构体和枚举注释示例：

```c
/**
 @brief RS485 驱动初始化配置。
 @note 调用方负责初始化；初始化函数只复制成员值，不保存本结构体指针。
 */
typedef struct {
    uint32_t baud_rate;  /* 串口波特率，单位为 bit/s。 */
    uint32_t timeout_ms; /* 接收超时，单位为 ms；依据需求 RS485-REQ-003。 */
    uint8_t *rx_buffer;  /* 接收缓冲区，由调用方持有，不得为 NULL。 */
    size_t rx_capacity;  /* rx_buffer 的容量，单位为字节。 */
} DrvRS485Config_t;

/**
 @brief OTA 接收状态。
 @note 仅由 OTA 任务修改；不得按枚举底层宽度直接写入协议或 Flash。
 */
typedef enum {
    OTA_STATE_IDLE = 0,  /* 尚未开始接收。 */
    OTA_STATE_RECEIVING, /* 正在接收并校验数据包。 */
    OTA_STATE_COMPLETE,  /* 镜像接收和完整性校验已经完成。 */
    OTA_STATE_FAILED,    /* 接收失败，等待上层执行恢复。 */
} OTAStateEnum_t;
```

宏、关键逻辑和临时事项分别说明用途/依据、原因/约束以及追踪信息：

```c
/**
 @brief BootLoader 的 Flash 起始地址。
 @note 依据链接脚本 bootloader.ld 中的 FLASH_BOOT 区域和分区表 V2.1 表 3。
 */
#define bootloader_start_addr UINT32_C(0x08000000)

/**
 @brief 将位号转换为 32 位掩码。
 @param bit_index 位号，取值范围为 0～31。
 @return 对应的 32 位无符号掩码。
 @note 参数只能是无副作用表达式；能使用 static inline 时优先使用函数。
 */
#define drv_bit_mask(bit_index) (UINT32_C(1) << (bit_index))

/* 先暂停 Modbus 查询，避免将 RS485 回声误判为 OTA 响应。 */
Modbus_PausePolling();

/* TODO(ota-owner, 2026-09-30): 补充断电恢复测试; CR-123. */
```
