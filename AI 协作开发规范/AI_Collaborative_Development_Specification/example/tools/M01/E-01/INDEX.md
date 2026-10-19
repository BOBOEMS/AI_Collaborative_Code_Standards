# E-01 正式验证材料辅助工具

| 脚本 | 用途 |
|---|---|
| [summarize_results.py](summarize_results.py) | 读取合成 CSV，按候选和明确复用清单整理六项结果，保留每项原始来源 |

来源：为本整套示例编写，使用 Python 标准库。默认只输出 JSON，不写文件：

```text
python -B tools/M01/E-01/summarize_results.py
python -B tools/M01/E-01/summarize_results.py --output evidence/M01/R02/summary.json
```

输出目标必须不存在，脚本拒绝覆盖旧文件。输入固定为本套示例 R01/R02，最终候选为 DEMO-M01-R2，复用 T01/T03/T06 依据 C-REUSE-01，详见 [REVIEW.md](../../../milestones/M01/REVIEW.md)。

正式步骤见 [CASES.md](../../../milestones/M01/CASES.md)。脚本不驱动或采集设备，只整理已有 DEMO 数据，不能将其运行认定为用例已真实执行；实际用例实现和采集工具须按真实环境补充。复制到新阶段时必须适配输入、候选、复用范围和输出位置。
