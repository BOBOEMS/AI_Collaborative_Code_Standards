# 嵌入式代码规范

目录按“AI 协作、共享治理、语言分册、规范依据”组织，避免把不同用途和语言的规则混在根目录。

```text
代码规范/
├─ AI 协作开发规范/ # AI 权限、方案冻结、验证证据与任务模板
├─ 共享/           # 风险、评审、责任、豁免、热修
├─ C/              # C / FreeRTOS / MCU 技术规范与工具配置
├─ LuatOS/         # LuatOS / Lua 技术规范与编辑器配置
└─ 规范依据/       # 按 C、LuatOS 分开的追溯资料
```

## 入口

| 入口 | 用途 |
| --- | --- |
| [嵌入式 AI 协作开发规范 V1.2](AI%20协作开发规范/embedded-ai-development-protocol-v1.2.md) | AI 的 A0–A3 权限、方案批准、任务切片和 E0–E4 证据边界；含 AGENTS.md 与任务卡模板入口。 |
| [共享/README.md](共享/README.md) | 可选的团队治理文件：规则级别、R0/R1/R2、责任、豁免与热修。C 分册默认使用；LuatOS V1.2 按需选用。 |
| [C/README.md](C/README.md) | C/FreeRTOS 分册入口。 |
| [LuatOS/README.md](LuatOS/README.md) | LuatOS/Lua 分册入口。 |
| [规范依据/README.md](规范依据/README.md) | C 与 LuatOS 依据的分类索引。 |

## 使用顺序

1. AI 参与分析或修改时，先按 [嵌入式 AI 协作开发规范](AI%20协作开发规范/embedded-ai-development-protocol-v1.2.md) 确认权限和证据边界。
2. 进入对应语言分册，阅读该分册的适用范围和技术规则。
3. C 项目按 C 分册和共享治理文件建立项目基线、责任与评审流程。
4. LuatOS 项目使用 LuatOS 技术配置和开发自检表；个人或小团队不强制使用共享治理流程。
5. 需要正式多人评审、风险分级、豁免或紧急修复流程时，再选用 [共享治理与评审基线](共享/团队治理与评审基线.md) 和 [共用流程](共享/豁免与紧急修复流程.md)。

不应跨语言照搬技术规则：C 的 IRQ/FreeRTOS/链接规则不适用于 Lua；LuatOS 的协作式任务、打包映射和低功耗规则也不适用于 C 工程。

## 开源发布边界

- 本仓库发布团队自编规范、模板和检查脚本。
- `规范依据/C/Zephyr/` 与 `规范依据/C/OpenTitan/` 是 Apache-2.0 上游快照，保留其 LICENSE。
- BARR-C:2018 PDF 受版权保护，不入库；官方链接与本地获取说明见 [规范依据/C/BARR-C/README.md](规范依据/C/BARR-C/README.md)。
- 已填写的项目配置、编辑器缓存、操作系统垃圾文件和密钥由根目录 `.gitignore` 排除。
