# D-01 开发辅助工具

| 脚本 / 数据 | 用途 |
|---|---|
| [check_layout.py](check_layout.py) | 检查区域数据的正整数长度、边界和不重叠 |
| [fixtures/layout.json](fixtures/layout.json) | 本例共用布局的教学配置，来源见 [shared_design.md](../../../shared_design.md) |

来源：为本整套示例编写的最小离线工具。使用现有 Python，无额外依赖：

```text
python -B tools/M01/D-01/check_layout.py
python -B tools/M01/D-01/check_layout.py --layout <另一个布局文件>
```

只读取输入并在标准输出报告，通过返回 0，输入或检查失败返回非零。不执行固件、不检查实际链接和擦写。本工具只覆盖配置数据，不能替代 D 的真实生产自测。调整布局或复用副本后，应核对当前约定和输入范围。
