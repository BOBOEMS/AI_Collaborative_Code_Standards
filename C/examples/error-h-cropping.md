# 示例：error.h 宏定义裁剪

> 仅在裁剪 error.h 时读取；不得改用枚举。

<!-- bundle-body-start -->

### 6.1 资源受限项目的 `error.h` 裁剪示例

以下示例适用于任何经评估需要缩减 Flash 或 RAM 占用的项目，例如 BootLoader、小容量 MCU 应用、恢复固件或出厂测试固件。裁剪对象是本目录已提供的宏定义版 `error.h`，不改用枚举。

`error.h` 裁剪只能删除未使用项，不得改变文件引用方式及保留项的符号、数值、别名或语义。

本文件是项目私有负值目录，`EPERM` 等名称只沿用 errno 风格；它不兼容标准库的正值 errno 约定。同一翻译单元不得同时包含两套同名宏，也不得通过 `#undef` 或调整包含顺序覆盖；适配层须在不同翻译单元中按错误含义映射，不能假设数值简单取负就匹配。按 `API-008` 检查实际包含链和最终宏值。

“未使用项”还须排除被保留别名依赖的宏：例如保留 `EWOULDBLOCK` 时必须同时保留其目标 `EAGAIN`；保留 `EDEADLOCK` 时必须同时保留 `EDEADLK`。

完整版 `error.h` 片段：

```c
#define ERROR_OK 0     /* 成功。 */
#define EPERM -1       /* 操作不允许。 */
#define ENOENT -2      /* 对象不存在。 */
#define EIO -5         /* 输入输出失败。 */
#define ENOMEM -12     /* 内存不足。 */
#define EINVAL -22     /* 参数非法。 */
#define ETIMEDOUT -110 /* 操作超时。 */
```

某个资源受限固件只使用其中五项时，项目内同名 `error.h` 只删除 `ENOENT` 和 `ENOMEM`：

```c
#define ERROR_OK 0     /* 成功。 */
#define EPERM -1       /* 操作不允许。 */
#define EIO -5         /* 输入输出失败。 */
#define EINVAL -22     /* 参数非法。 */
#define ETIMEDOUT -110 /* 操作超时。 */
```

业务代码不区分完整版或裁剪版，调用方式保持不变：

```c
#include "error.h"

/**
 @brief 擦除指定地址所在的 Flash 扇区。
 @param flash_address 待擦除扇区的起始地址。
 @return 成功时返回 ERROR_OK；地址非法时返回 EINVAL；写保护时返回 EPERM；擦除失败时返回 EIO。
 @note 地址必须按芯片扇区边界对齐，且不得指向当前固件的受保护代码区。
 */
int32_t Storage_Flash_EraseSector(uint32_t flash_address) {
    if (!Flash_IsAddressValid(flash_address)) {
        return EINVAL;
    }

    if (Flash_IsWriteProtected(flash_address)) {
        return EPERM;
    }

    if (Flash_EraseSector(flash_address) != ERROR_OK) {
        return EIO;
    }

    return ERROR_OK;
}
```

宏定义本身不单独占用 Flash。若裁剪后 Flash 实测减小，应在相同工具链和优化选项下对比 MAP 与 BIN 结果，并记录随未使用错误码一同被移除的错误文本、映射表、分支、模块代码或其他段与符号。禁止为了裁剪将错误码宏改写为枚举；这会改变错误码的声明和类型模型，并可能在特定工具链或用法下增加 Flash 或 RAM 占用。
