# C-01 审核辅助工具

| 脚本 | 用途 |
|---|---|
| [verify_evidence.py](verify_evidence.py) | 独立检查教学汇总的六项覆盖、原始行、结果、候选、允许复用清单和日志存在性 |

来源：为本整套示例编写，不调用 E 的解析代码。使用 Python 标准库：

```text
python -B tools/M01/C-01/verify_evidence.py
python -B tools/M01/C-01/verify_evidence.py --summary <待核对汇总文件>
```

脚本只读，检查通过返回 0，不一致或证据文件缺失返回非零。最终候选和允许复用清单取自本例 [C-REUSE-01](../../../milestones/M01/REVIEW.md#3-复用依据-c-reuse-01)。

本工具证明的只是教学材料关联。它不证明日志真实、不证明目标条件确已发生、不审核生产源码，也不能替代 E 实测或 C 人工判断。
