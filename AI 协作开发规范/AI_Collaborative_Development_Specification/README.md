# 嵌入式 AI 协作开发规范

本规范面向小团队产品开发，按“总体方案 → 里程碑划分与细化 → 多 AI 协作实现、审核和验证”逐步推进。V1 完成确认功能、完整链路及必要保护、审查和实物验证；V2 围绕实际问题优化回归；V3 按需要开展深度研究。

根目录是协议正文，AI 使用入口为 [AGENT.md](AGENT.md)。[example/](example/README.md) 展示一套完整的 OTA 项目文档，含总体方案、计划、角色配置、具体阶段设计、用例、审核、报告、工具及记录。

本文件用于介绍，AI 按需阅读。项目通过自己的 `AGENT.md` 声明采用范围和实际位置。独立会话调用的 Python API、CLI、原生适配器及验证边界见 [session_handover_tool/](session_handover_tool/README.md)，由项目显式配置和调用。
