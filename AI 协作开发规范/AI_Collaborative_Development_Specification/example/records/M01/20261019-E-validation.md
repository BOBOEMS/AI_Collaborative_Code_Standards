# M01 E 验证与针对复测：教学记录

本记录和原始日志、CSV 全为合成演示，没有执行上板。术语见[总体方案](../../PROJECT.md#术语与阅读说明)，步骤和停止条件见 [CASES.md](../../milestones/M01/CASES.md)。

## R01

按场景内 C 批准组合，对 DEMO-M01-R1 执行 T01～T06。T05 观测为无合格备份仍发生 App 改写，判 FAIL，停止受影响维修操作，保留前后状态并报告 C/同步 A。其他独立场景在按既定办法安全退出和移交条件具备后完成。

数据：[results.csv](../../evidence/M01/R01/results.csv)、[observations.log](../../evidence/M01/R01/observations.log)。教学提交 DEMO-COMMIT-E-01，原失败未删除或改写。

## R02

D 修正、C 针对审核后，E 对 DEMO-M01-R2 重测 T02/T04/T05，三项 PASS。按 C-REUSE-01，T01/T03/T06 采用 R01，范围和依据见 [REVIEW.md](../../milestones/M01/REVIEW.md)。

数据：[results.csv](../../evidence/M01/R02/results.csv)、[observations.log](../../evidence/M01/R02/observations.log)，[summary.json](../../evidence/M01/R02/summary.json)逐项保留来源。教学提交 DEMO-COMMIT-E-02，当前报告交 C 审核证据并同步 A。

## 限制

离线 [E 工具](../../tools/M01/E-01/INDEX.md)只从合成 CSV 整理汇总，不能生成设备观测。实际掉电、完整矩阵、4G、URL 及完整业务未执行，不能把本阶段结果扩展为版本验收。
