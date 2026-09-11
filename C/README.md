# C / FreeRTOS 分册

本分册只放 C/FreeRTOS/MCU 技术内容。规范同时面向人和 AI：人可阅读合订版，AI 通过轻量路由入口按任务读取权威分片。

## 人工阅读入口

| 文件 | 用途 |
| --- | --- |
| [embedded-c-team-standard-v1.md](embedded-c-team-standard-v1.md) | 由分片自动生成的完整合订版，保留原路径供人阅读和旧链接使用。 |
| [pr_checklist.md](pr_checklist.md) | 19 项 C 技术检查索引；适用项并入现有自检或评审，结果只记录一次。 |
| [project_profile_template.md](project_profile_template.md) | 工具链、芯片、FreeRTOS、IRQ/DMA、资源和构建字段；用于补齐现有项目配置。 |
| [rule_source_matrix.md](rule_source_matrix.md) | 规则来源、团队裁决、检查方式与许可边界映射。 |
| [.clang-format](.clang-format) | C 格式配置，固定 clang-format `19.1.7`。 |
| [error.h](error.h) | 可选的项目私有负值错误码完整目录；不能与 `<errno.h>` 的同名宏混用。 |
| [check_error_header_usage.ps1](check_error_header_usage.ps1) | 使用项目实际 GCC 参数检查一个或多个翻译单元的错误码包含链和最终宏值。 |

## AI 按需读取入口

[AGENTS.md](AGENTS.md) 是 C 规范专用的 AI 路由文件，不承载 AI 协作或权限规则。它要求所有 C/H 修改先读基础与注释分片，再根据接口、硬件并发、状态时间、存储升级或构建评审等任务内容读取专项分片。

`rules/` 中的文件是规则正文的唯一权威来源，`examples/` 中的文件是按需示例。当 AI 在其他项目目录工作时，该项目的入口文件应明确要求先读取本目录的 `AGENTS.md`；不应直接复制全部规范正文。

协作方式按 [共享治理入口](../共享/团队治理与评审基线.md) 在项目基线中明确一次。C 技术规则在两种方式下均适用；个人+AI 项目复用其已采用协作规范的自检、必要复审和记录，团队项目保留非作者人数及角色要求。具体检查依据按规则 ID 引用，不另建一套 C 审查流程。

## 规范维护

- 当前版本为 V2.1 试运行候选版；合订版保留原文件名以兼容旧链接。
- 规则正文只编辑 `rules/`，示例只编辑 `examples/`；相关模板、工具及来源矩阵同步维护，不直接维护合订版正文。
- 维护环境要求 PowerShell 7（命令 `pwsh`）和 clang-format `19.1.7`。中文脚本采用 UTF-8 无 BOM，不支持 Windows PowerShell 5.1 的 `powershell` 入口；脚本通过 `#requires` 声明最低版本。工具安装仍遵守本机工具目录约定。
- 在本目录运行 `pwsh -NoProfile -File .\build_standard.ps1` 重新生成合订版。
- 运行 `pwsh -NoProfile -File .\validate_c_standard.ps1` 检查分片、合订版、规则 ID、矩阵覆盖、链接、UTF-8、全部 C 示例格式及 `error.h` 宏契约。格式器不在 PATH 时传入 `-ClangFormatPath <完整路径>`。
- `checks/error_macro_contract.json` 固定现有宏的符号、数值和别名；常规规范维护及裁剪不得通过更新该基线来掩盖契约变化。文档校验通过不代表项目代码、目标构建或板端验证通过。

本节命令仅在维护规范时执行。普通业务代码修改使用项目已有检查入口；初始化时固定必要工具及配置，后续按实际变化维护，不因读取规范而自动安装工具或增加 CI。

### 项目错误码包含检查

GCC 项目可在其构建工作目录调用下列脚本，传入该翻译单元实际使用的预处理配置；`-CompilerArgument` 是独立参数数组，不是拼接的命令字符串。不要传入源文件、输出参数、`-c` 或响应文件，源文件由 `-SourcePath` 指定；包含目录、宏、CPU/ABI 参数及强制包含文件应与真实构建一致。

```powershell
& '<规范目录>/C/check_error_header_usage.ps1' `
    -CompilerPath '<工具链目录>/bin/arm-none-eabi-gcc.exe' `
    -ErrorHeaderPath './include/error.h' `
    -SourcePath './src/app_module.c' `
    -CompilerArgument @('-I./include', '-mcpu=cortex-m3', '-mthumb')
```

脚本只做预处理，不编译或链接，预处理警告按 `-Werror` 处理；没有使用指定 `error.h` 的翻译单元输出 `SKIP`。宏重定义、混入 `errno.h`、多个 `error.h`、裁剪破坏别名或最终宏值漂移均失败。项目须对所有相关翻译单元及受支持变体运行；该脚本不验证跨翻译单元适配函数的语义，也不代替项目警告差分检查，ARMCC 等工具链须使用等价的包含依赖和宏检查。

规则分级、责任、豁免和热修复的适用说明见 [共享目录](../共享/README.md)。首次采用时用基线与技术配置模板检查字段；已有 `PROJECT.md`、技术配置和里程碑记录可直接承载，缺少权威位置时才建立文件。
