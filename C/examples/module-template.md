# 示例：新建 C 模块骨架

> 仅在新建 C 模块或审查模块骨架时读取。

<!-- bundle-body-start -->

## 附录 A：推荐的新模块骨架

```c
/**
 @file drv_example.h
 @brief 声明示例驱动的配置类型和公共接口。
 */
#ifndef RTU_DRV_EXAMPLE_H
#define RTU_DRV_EXAMPLE_H

#include <stddef.h>
#include <stdint.h>

#include "rtu_status.h"

/**
 @brief 示例驱动的初始化配置。
 */
typedef struct {
    uint32_t baud_rate;  /* 接口波特率，单位为 bit/s。 */
    uint32_t timeout_ms; /* 单次操作超时，单位为 ms。 */
} DrvExampleConfig_t;

/**
 @brief 初始化示例驱动。
 @param config 输入的初始化配置，不得为 NULL；函数只复制成员值。
 @return 成功时返回 rtu_status_ok；失败时返回项目错误码头文件定义的负数错误码。
 @note 仅允许在任务上下文调用；重复初始化的处理方式由项目配置规定。
 */
rtu_status_t DrvExample_Init(const DrvExampleConfig_t *config);

/**
 @brief 从示例驱动读取数据。
 @param buffer 输出缓冲区，不得为 NULL，由调用方持有。
 @param buffer_size buffer 的容量，单位为字节，必须大于 0。
 @param received_size 实际读取长度的输出地址，不得为 NULL。
 @return 成功时返回 rtu_status_ok；失败时返回项目错误码头文件定义的负数错误码。
 @note 仅允许在任务上下文调用；等待时间不超过配置的 timeout_ms。
 */
rtu_status_t DrvExample_Read(uint8_t *buffer, size_t buffer_size, size_t *received_size);

#endif /* RTU_DRV_EXAMPLE_H */
```

```c
/**
 @file drv_example.c
 @brief 实现示例驱动的初始化、数据收发和内部状态管理。
 */
#include "drv_example.h"

#include <stdbool.h>
#include <stddef.h>

static bool s_is_initialized;

rtu_status_t DrvExample_Init(const DrvExampleConfig_t *config) {
    if ((config == NULL) || (config->baud_rate == 0U)) {
        return rtu_status_invalid_argument;
    }

    /* 校验全部输入后再配置外设，避免无效配置留下部分初始化状态。 */
    s_is_initialized = true;
    return rtu_status_ok;
}
```
