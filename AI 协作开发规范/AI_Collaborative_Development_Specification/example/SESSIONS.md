# 会话配置与登记

更新日期：2026-10-21。规定位置：`AI/SESSIONS.md`。规则见[会话配置与登记](../多AI会话工作流规范.md#session-register)，工具用法见[统一入口](../session_handover_tool/README.md)。

本例的配置及实际绑定以 [project.sessions.json](project.sessions.json) 为唯一来源。配置包含占位符且写动作授权为空，尚未创建或绑定真实会话；本文件展示教学阅读方式，不是本次运行工具所得结果。协作规则见 [ROLES.md](ROLES.md)，任务进展见 [STATE.md](STATE.md)。

## 术语与阅读说明

| 名称 | 本文含义与定义来源 |
|---|---|
| profile / 原生设置 | profile 是调用配置名，不是会话 ID；原生设置描述工具自己的模型或继承方式，见[配置说明](../session_handover_tool/README.md#配置及文档归属) |
| `inherit_model` | 为真表示沿用宿主模型；本例 A/B/C 使用继承，不宣称已核验实际模型或强度 |
| `model` / `reasoning_effort` | 模型及思考设置使用对应 Agent 原生值；Antigravity 的目录变体与 Harness 设置分别按工具说明填写，不互相转换 |
| 原生会话 ID / 登记状态 | ID 由宿主返回，登记状态是最后观测，不是实时任务进度；职责和会话含义见 [ROLES](ROLES.md#术语与阅读说明) |

## 1. 唯一来源与维护

A 或获授权维护者填写真实工程、文档根目录、适配器连接及用户授权依据，工具写入实际绑定和替换历史。配置值只在 JSON 维护；`sync` 只替换下方标记区域，人工说明保留在区域外。配置及有意义的绑定变化按交付批次提交，不逐消息刷新文档。

本例通过 `SESSION_TOOL_PROJECT_ROOT`、`SESSION_TOOL_DOCUMENTS_ROOT` 指向实际位置，运行材料根目录沿配置使用。未填写占位符或没有实际授权时，不执行创建、派发等写动作，也不以本示例作为用户批准。

<a id="target-config"></a>

## 2. 角色目标的阅读展示

下方按工具 `sync` 的目标表结构编写教学示意，来源路径用相对链接表示；实际同步会输出实际配置路径。原生设置只维护于 JSON；此处为同一份配置的阅读展示，不是第二个可修改来源。

<!-- session-tool:start -->
## 工具同步的目标配置

唯一来源：[project.sessions.json](project.sessions.json)

| 角色 | Agent 连接 | 目标原生设置 |
|---|---|---|
| A | codex_cli | `{"inherit_model":true}` |
| B | codex_cli | `{"inherit_model":true}` |
| C | codex_app | `{"inherit_model":true}` |
| D | antigravity | `{"model":"CATALOG_MODEL_ID","model_label":"Exact native catalog label","native_model":"NATIVE_MODEL_ENUM"}` |
| E | deepseek_harness | `{"provider":"native-provider","model":"native-model","reasoning_effort":"native-effort"}` |
<!-- session-tool:end -->

D/E 中的原生目录和模型字段须按实际宿主填写；本例不指定通用生产模型。Command Code、Grok 仍是未接入的选型方向，不放入当前可调用角色配置，也不借用其他 Agent 的通道冒充。Codex App 的新 C 须由宿主创建后绑定；其他会话按工具支持方式建立。

<a id="milestone-m01"></a>

## 3. M01 教学组与实际绑定

M01 在教学场景中已结束并停手，实际原生会话均未创建。JSON 的 `milestones` 和 `sessions` 为空，不手工填虚构 ID；真实组只有创建或核验绑定成功后才写入唯一配置，再由工具展示。本例没有当前真实运行任务。

每个新里程碑仍建立五个全新会话，包括 A；不覆盖旧组或把旧任务改归新 ID。当前组编号和下一步由 [STATE.md](STATE.md)定位；真实执行前沿原配置取得本组身份，不从示意表推断运行就绪。

## 4. 替换与交接入口

同阶段替换会话时，先明确停点、资源及未完成任务归属，再沿 `switch` 创建或绑定替代者，保留旧绑定和原任务回报归属。改默认配置不代表已切换，压缩恢复不更换会话组。

`switch` 不改变旧任务执行者、冻结接收者或其送达状态。按[替换接续规则](../多AI会话工作流规范.md#session-replacement)在 STATE/已有交接中指定旧结果收集者；替换执行者时确认停手并派剩余工作新任务，结清旧任务的实际状态。当前采用方式及假设分支见 [ROLES.md](ROLES.md#handoff)。

本例没有实际替换或推送。当前阶段收口见[共享消息第 15 条](evidence/M01/communication/handover.txt)，复杂事件沿[记录索引](records/INDEX.md)取得；通信文件全部为合成教学材料。
