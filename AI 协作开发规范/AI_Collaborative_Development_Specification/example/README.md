# 整套 OTA 项目文档示例

本目录模拟一个项目的 `AI/` 协作文档目录。`example/PROJECT.md` 对应实际项目 `AI/PROJECT.md`，其他文件同理。采用时先确定实际协作文档位置，调整链接和项目约定，不将示例状态当作真实结果。

## 阅读与对应关系

| 想了解的内容 | 文件 |
|---|---|
| AI 如何进入、恢复与取得约束 | [AGENT.md](AGENT.md) |
| 总目标与当前版本范围 | [PROJECT.md](PROJECT.md) |
| 里程碑如何划分和承接验证 | [PLAN.md](PLAN.md) |
| 当前做到哪里 | [STATE.md](STATE.md) |
| ABCDE 如何分工、读取和接续 | [ROLES.md](ROLES.md) |
| 工具/模型目标、参数及各阶段真实会话如何登记 | [SESSIONS.md](SESSIONS.md) |
| 少量共用约定如何集中维护 | [shared_design.md](shared_design.md) |
| 一个阶段如何具体设计和验证 | [M01 设计](milestones/M01/DESIGN.md)、[用例](milestones/M01/CASES.md)、[审核](milestones/M01/REVIEW.md)、[报告](milestones/M01/TEST_REPORT.md) |
| 决策、纠错和复测如何追溯 | [记录索引](records/INDEX.md) |
| 内部工具如何分目录和复用 | [工具索引](tools/INDEX.md) |

## 统一教学快照

本例采用 V1 深度，计划 M01 → M02 → M03 → M04 串行推进。采用 M01 本地安装恢复的教学过程，候选由 DEMO-M01-R1 修正为 DEMO-M01-R2；当前阶段和进度统一由 [STATE.md](STATE.md)维护。

演示过程为：B/用户确认 → D 实现和自测、E 准备用例 → C 审核 → E 发现无备份维修准入失败 → C 按既定需求交 D 修正 → C 针对复核 → E 针对复测 → C 核对证据 → A 收口并保存教学推送回执。原失败数据保留，未受影响结果由 C 明确说明复用依据。

所有候选名、会话占位符、提交/推送回执、日志和数据都是教学材料，均未执行真实会话创建、固件构建、烧录或板测。工具仅运行离线数据处理，不能把示例 PASS 当作真实产品验收。后续里程碑只保留计划，不预生成具体设计和会话。

<a id="source-facts"></a>

## 可选：源项目事实与边界

项目背景和技术目标参考 Reuse_RTU。源项目于 2026-10-16 按用户决定受限收口：H6-2 URL 保存保留 FAIL，H6-1 未测，H6-3 未整体验收，SYS 未测。本教学 M01 完成不改变这些事实，也没有修复真实 FRAM/驱动容量矛盾。

以下是协议目录之外的可选追溯材料，不是阅读示例的前置条件：

- [源项目设计入口](../../../../Reuse_RTU/5.Document/si/design/OVERVIEW.md)
- [源项目当前状态](../../../../Reuse_RTU/5.Document/si/STATE.md)
- [受限收口决定](../../../../Reuse_RTU/5.Document/si/records/V1-A-limited-closeout-20261016.md)

本例术语统一见 [PROJECT.md 的术语说明](PROJECT.md#术语与阅读说明)，各文件开头引用。示例 NOR 偏移和候选标识为教学假定，不能直接作为设备操作参数。
