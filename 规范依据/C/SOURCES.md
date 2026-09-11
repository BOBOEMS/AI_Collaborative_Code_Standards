# 代码规范依据：来源与使用边界

下载日期：2026-07-22（Asia/Shanghai）  
用途：为仓库中的 `embedded-c-team-standard-v1.md` 提供离线、可追溯的参考资料；这些上游资料不是本项目的直接构建依赖。

## 1. BARR-C:2018

- 文件：`BARR-C/BARR-C-2018-Embedded-C-Coding-Standard.pdf`
- 官方来源：<https://barrgroup.com/sites/default/files/barr_c_coding_standard_2018.pdf>
- SHA-256：`D9465E8EABB67243DF8D581992653A2C37D517C9328656CD12DA3B946674E7D4`
- 用途：嵌入式 C 的数据类型、函数、宏、命名、可维护性与常见缺陷防护实践。
- 使用限制：该 PDF 受 Barr Group 版权保护。仅供团队内部参考；不得把该副本或其全文对外发布、再分发。对外公开仓库只应保留团队自行编写的规范和指向官方来源的链接。

## 2. Zephyr：工程约束与检查配置

上游仓库：<https://github.com/zephyrproject-rtos/zephyr>  
下载时分支：`main`，当时远端提交：`be2ec6abf535885f22f11836adac7db8dedd7759`

| 本地文件 | 上游原始文件 | SHA-256 | 用途 |
| --- | --- | --- | --- |
| `Zephyr/zephyr-coding-guidelines.rst` | `doc/contribute/coding_guidelines/index.rst` | `54E7F730EA0229E0EA8C3A4847097D3CF28FEB27F8F6B78C0D3AFCAA10F650F5` | 基于 MISRA-C 子集的工程规则、错误处理与可追溯性。 |
| `Zephyr/zephyr-style-index.rst` | `doc/contribute/style/index.rst` | `504F117C92550CBE505C231E6267DB63B3FF245E634ADA53FFCC457997FA9290` | 风格工具、checkpatch 与 clang-format 的使用说明。 |
| `Zephyr/zephyr-c-code-style.rst` | `doc/contribute/style/code.rst` | `67817D170E6B3453B13A3E7BBA7C6A2492161AA10768013376675549C7760416` | C 代码布局与注释风格。 |
| `Zephyr/zephyr-naming-conventions.rst` | `doc/contribute/style/naming.rst` | `977478E5CBDB40051237CF60FF44F25B738A97FFA17CEAD3874FF13E7965CC4E` | 命名规则。 |
| `Zephyr/zephyr-clang-format` | `.clang-format` | `57BC87DC3A2C04AAB21FC65EE2AC9F9B433DC2D0A63D4DC8A1A527EF387479AD` | 格式配置的对照样本；不可直接覆盖本项目。 |
| `Zephyr/zephyr-checkpatch.conf` | `.checkpatch.conf` | `48F6BB16AE1586CAEFF5BC8A1B69896959B4D27CEEE15314CBB800D475C5E212` | checkpatch 例外配置的对照样本。 |
| `Zephyr/LICENSE` | `LICENSE` | `C6596EB7BE8581C18BE736C846FB9173B69ECCF6EF94C5135893EC56BD92BA08` | Zephyr 仓库在该提交下的 Apache-2.0 许可证文本。 |

上游文件固定链接以该提交为准，例如：<https://github.com/zephyrproject-rtos/zephyr/blob/be2ec6abf535885f22f11836adac7db8dedd7759/doc/contribute/coding_guidelines/index.rst>。

## 3. OpenTitan：格式与命名参考

上游仓库：<https://github.com/lowRISC/opentitan>  
下载时分支：`master`，当时远端提交：`720d7242d4661b94564e0bd9ed0c4d451bc5710b`

| 本地文件 | 上游原始文件 | SHA-256 | 用途 |
| --- | --- | --- | --- |
| `OpenTitan/opentitan-c-cpp-coding-style.md` | `doc/contributing/style_guides/c_cpp_coding_style.md` | `A9F1CAD8808A6C2BC0E8A2BFD8FA408519E6237D4890781EB07926D0BFB851FD` | C/C++ 格式、命名、注释、头文件与静态检查实践。 |
| `OpenTitan/opentitan-clang-format` | `.clang-format` | `9CB9A3B87019858BE4FE7E9369A70E2CC9B362080ADF3A83564AE484B8A29C95` | 格式配置的对照样本；不可直接覆盖本团队配置。 |
| `OpenTitan/LICENSE` | `LICENSE` | `CFC7749B96F63BD31C3C42B5C471BF756814053E847C10F3EB003417BC523D30` | OpenTitan 仓库在该提交下的 Apache-2.0 许可证文本。 |

上游文件固定链接以该提交为准，例如：<https://github.com/lowRISC/opentitan/blob/720d7242d4661b94564e0bd9ed0c4d451bc5710b/doc/contributing/style_guides/c_cpp_coding_style.md>。

## 4. 使用原则

1. `embedded-c-team-standard-v1.md` 是团队执行规范；上游文件只作为依据，不以“照抄上游”替代团队决策。
2. 任何自动格式化配置须先在一个独立分支、少量自研模块上试运行，再纳入仓库；不要格式化厂商库、FreeRTOS、CMSIS 或生成文件。
3. 若重新下载上游资料，须更新本清单中的日期、上游提交和 SHA-256；未经复核不得把 `main` 或 `master` 的新内容当作既有规范依据。
