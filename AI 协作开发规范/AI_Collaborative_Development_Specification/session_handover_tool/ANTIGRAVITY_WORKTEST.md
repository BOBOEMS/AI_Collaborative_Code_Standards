# Antigravity 真实开发执行验证

日期：2026-10-20。通道：本模块 Antigravity 原生适配器；宿主 2.24.0，模型 Gemini 3.8 Flash（High），实时目录和实际生成器均对应 `MODEL_PLACEHOLDER_M318`。此记录补充此前两轮文本连通性验证。

## 对象与完成条件

用户要求先单独实测 Antigravity。本轮在现有专用原生项目下新建开发测试会话，使用隔离的二进制切块 Python 夹具，验证“接收任务 → 读取文件 → 执行失败基线 → 修改代码 → 执行测试 → 形成报告 → 外层独立核验”。不测试产品固件或板卡，不启动 DeepSeek Harness 任务，也不切换原项目角色绑定。

允许修改 `coding_case/chunking.py`，新建 `coding_case/RESULT.md`；`TASK.md`、`test_chunking.py` 保持不变。函数要求包括 bytes 输入、正整数块大小、bool 拒绝、空数据、完整块与不足块、任意二进制数据无损重组。执行前由外层保存工作目录文件哈希及明确失败的基线，执行者自行再运行基线并诊断。

## 已取得证据

| 检查 | 结果及证据 |
|---|---|
| 原生身份和目录 | 新建会话核验通过，cwd 对应专用 workspace；任务显式指定其中的 coding_case 目录 |
| 模型 | 实时目录匹配 Gemini High，实际生成器枚举为 `MODEL_PLACEHOLDER_M318`，生成器未报告错误 |
| 读取任务/代码/测试 | 原生轨迹包含已完成的 `VIEW_FILE` 步骤 |
| 失败基线 | 执行者实际运行 `python -B -m unittest -v`，退出码 1；11 项测试，15 个失败子项、1 个错误，与外层基线一致 |
| 修复 | 原生 `CODE_ACTION` 修改 chunking.py，补充类型/数值校验并修正迭代终点，保留完整块和尾部块 |
| 执行者自测 | 原生 `RUN_COMMAND` 记录同一测试命令退出码 0、11 项测试 OK |
| 实际文件范围 | 外层哈希对比仅发现 chunking.py 与 RESULT.md 变化；测试和 TASK 哈希未变，未见其他 workspace 文件变化 |
| 外层独立复测 | 重新运行原测试，11 项全部通过、退出码 0；该结果独立于 Agent 的文字结论 |
| 报告补正 | 同会话两轮补正后通过外层核验，区分原有行为、新增修复、首次代码修改和后续报告修改，补充附加命令失败记录 |
| 最终状态 | 原生会话空闲，46 个轨迹步骤全部 DONE；报告补正期间代码哈希未变，未重复运行测试 |

执行者额外运行了 `git status`（夹具非 Git 仓库，退出码 1）和 `Get-ChildItem`（退出码 0）。前者是附加只读命令失败，不属于函数测试失败；必须保留原始记录，不能用测试 OK 覆盖所有命令结果。

## 报告审核发现

首份 RESULT.md 将 `data=None` 和 `block_size=0` 混在缺失异常校验的描述中，表达不准确：原始代码已分别通过 `len(None)` 和零步长 `range` 抛出所需异常。实际需修复的行为包括 str/bytearray 未拒绝、bool 接受或异常类型错误、负数未拒绝，以及尾部数据丢失；新增显式校验应与原先已经符合的行为区分。

外层通过同一会话派发两轮仅修改报告的补正。第一轮修正异常行为并补充附加命令；第二轮消除“本轮补正未改代码”与“首次实现未改代码”的范围混淆，并将目录列表与外层文件哈希证据区分。最终报告满足上述要求，代码哈希与首次通过独立测试时一致。首份报告和首次补正保留供对比，不覆盖成最初即准确的结论。

## 证据与复用入口

本轮材料在 `C:/bobo_worktool/session-handover-tool/validation/20261020/antigravity-worktest/`，真实 ID、运行端点和轨迹不进入协议仓库：

| 文件 | 用途 |
|---|---|
| `drive.py` / `project.sessions.json` | 本轮独立调用入口及唯一测试配置；使用通用模块的 create/send/inspect |
| `created.json` / `sent.json` | 新会话创建登记与开发任务派发回执 |
| `baseline-files.json` / `baseline-unittest.log` | 修改前文件摘要及外层失败基线 |
| `trajectory-first.json` / `native-commands.json` | 原生首次交付轨迹，以及实际命令、退出码与输出摘要 |
| `report-first.md` / `source-after-first.json` | 首份报告及修复后代码摘要，供报告补正前后比较 |
| `independent-verification-first.json` / `independent-unittest.log` | 外层文件范围检查和独立复测结果 |
| `review-sent.json` | 同会话报告补正派发回执 |
| `review-final-sent.json` / `report-review-one.md` | 第二轮补正回执与首次补正报告快照 |
| `observation-latest.json` / `trajectory-latest.json` | 最近一次原生状态及完整原生轨迹 |
| `final-verification.json` | 最终范围、代码/测试哈希、原生模型和空闲状态、报告补正要求的核验，`passed=true` |

实际夹具在相邻的 `agents-live/workspace/coding_case/`。本轮驱动是项目运行材料；复用时建立自己的隔离对象、配置、request/task ID 和原生项目，不直接重复执行已有派发。

## 判定边界

**本例通过**：代码读取、修改、命令执行、执行者自测、外层独立测试以及同会话接收反馈、修改报告和停止，均取得真实证据。首份报告需要两轮校对，是本轮发现的交付质量限制；结果依赖外层独立审核，不能只凭执行者自称完成。

本例不证明复杂开发任务、模型切换、配额耗尽、跨 Agent 回报或整个项目工作流通过。
