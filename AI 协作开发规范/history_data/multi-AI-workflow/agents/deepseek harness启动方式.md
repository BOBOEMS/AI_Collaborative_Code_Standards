# DeepSeek Harness 启动方式

> 本文件记录**这台机器上实际可用**的 DSH 启动与驱动方式，每条都经过实测；
> 未经实测的内容会明确标注「未实测」。
> 验证环境：Windows / DeepSeek Harness CLI **0.2.0-rc.2** / 2026-10-13。

---

## §0 快速复制区

只想知道敲什么，看这一段就够了；每条命令的逐项解释在 §2～§5。

```powershell
# ── 0. 变量（后面所有命令都基于它）──────────────────────────────
$DSH = 'C:\bobo_worktool\DeepSeek Harness\resources\runtime\cli\bin\dsh.cmd'

# ── 1. 桌面 GUI（日常用；它自带一个 19387 端口的 Web/API 宿主）──
#     直接双击快捷方式，或：
& 'C:\bobo_worktool\DeepSeek Harness\DeepSeek Harness.exe'

# ── 2. 另起一个网页版实例（独立端口，不动桌面那个）──────────────
powershell -File agent-hub\scripts\start-dsh-web-workspace.ps1 -Port 19391
#     等价的裸命令：
& $DSH --profile web --port 19391            # 会自动开浏览器，URL 带 ?token=
& $DSH --profile web --port 19391 --no-open  # 不开浏览器

# ── 3. 无人值守一次性跑一个任务（最常用于自动化）────────────────
& $DSH --profile headless "把 README 里的错误链接修掉"
'任务里有 < > | & 等符号或中文时，走 stdin：'
'把 X 改成 Y' | & $DSH --profile headless -

# ── 4. 续接已有会话接着跑 ──────────────────────────────────────
& $DSH --profile headless --session-id session-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx "继续，把测试补上"

# ── 5. 要机器可读的事件流（拿 sessionId、判断结束）──────────────
& $DSH --profile headless --json "跑一遍单元测试"

# ── 6. 以 ACP 服务器方式跑（给 Zed / JetBrains / acpx 等客户端用）──
& $DSH --profile acp

# ── 7. 驱动「正在运行的 GUI 宿主」建会话/下指令/读结果 ────────────
cd agent-hub
node scripts\dsh-drive.cjs probe                                    # 探活
node scripts\dsh-drive.cjs list  --cwd "C:\bobo_document\temp\agent开发"
node scripts\dsh-drive.cjs run   --cwd "C:\bobo_document\temp\agent开发" --prompt "你好" --json
node scripts\dsh-drive.cjs prompt --session session-xxxxxxxx-... --prompt "改用方案 B" --wait
node scripts\dsh-drive.cjs read   --session session-xxxxxxxx-... --tail 800
```

**最常用的三条**：

| 我想… | 命令 |
|---|---|
| 看界面、自己打字 | 开桌面 GUI（默认就有） |
| 让程序跑一个任务、拿结果 | `dsh --profile headless "任务"`（要 sessionId/事件流加 `--json`） |
| 在**你能看到的 GUI 里**建会话让我驱动 | `node scripts\dsh-drive.cjs run --cwd <目录> --prompt "任务"` |

---

## §1 基本信息与前提

| 项 | 内容 |
|---|---|
| 工具形态 | Electron 桌面应用（GUI）+ 同名 CLI（多 profile 启动器）+ VS Code 扩展 |
| CLI 版本 | **0.2.0-rc.2**（`dsh --version`） |
| CLI 入口 | `C:\bobo_worktool\DeepSeek Harness\resources\runtime\cli\bin\dsh.cmd` |
| 桌面程序 | `C:\bobo_worktool\DeepSeek Harness\DeepSeek Harness.exe` |
| 程序根目录 | `C:\bobo_worktool\DeepSeek Harness\`（内含 `resources\app.asar`） |
| **工作目录** | 决定 Agent 的 `cwd`，从而决定会话归属哪个工作区。GUI 里由「工作区」选择；CLI 里是**你执行命令时的当前目录** |
| 用户配置目录 | `C:\Users\BOBO\.dsh\`（= `$DSH_HOME`），可用 `--profile` 切换子目录 |
| 凭据文件 | `~/.dsh/.credentials.yaml`（模型 API Key + 浏览器会话签名密钥） |
| 会话存储 | `~/.dsh/sessions/\`（zstd 压缩 JSONL）+ `~/.dsh/storages/\`（工作区索引等） |
| 运行依赖 | 无需额外安装；CLI 由应用自带的 Electron/Node 运行（本机 Node v24.16.0 仅供脚本使用） |

### 前置条件

1. **模型凭据已就绪**：`~/.dsh/.credentials.yaml` 里有 `CMDC_API_KEY`（commandcode 网关）。
   凭据由 `dsh-credentials-local` 插件自动注入，**不需要**设环境变量。
2. **中文/长任务建议用 PowerShell 7（`pwsh`）**；用 Windows PowerShell 5.1 时必须注意编码（见 §6）。
3. **profile 存在**：`~/.dsh/profiles/` 下需有对应目录。本机现有：
   `desktop`、`web`、`headless`、`acp`。
   缺少时可用模板生成：`dsh <name> --from-default-profile web`。

### 四个 profile 的分工

| profile | 形态 | 用途 | 是否需要端口 |
|---|---|---|---|
| `desktop` | 桌面 GUI | 日常交互；**自带 19387 的 Web/API 宿主**（浏览器与 VS Code 都接它） | 19387（本机实测固定） |
| `web` | 浏览器 UI | 另起独立实例、给自动化/第二屏用 | 需要（默认 3080，本机脚本用 19391） |
| `headless` | 一次性命令 | 无人值守跑单个任务、脚本化驱动 | 不需要 |
| `acp` | stdio JSON-RPC | 供 Zed / JetBrains / acpx 等 ACP 客户端接入 | 不需要（走 stdin/stdout） |

---

## §2 模型与参数

### 2.1 配置位置（**不是**命令行参数）

模型**不在 CLI 参数里**，而在每个 profile 的用户补丁层：

```
~/.dsh/profiles/<profile>/cordis.patch.yml
```

profile 的加载顺序是：`package.json` 里的 bundles → `cordis.yml` → **`cordis.patch.yml`** → `--patch` 覆盖层。
所以要改模型就改 `cordis.patch.yml`，**不要**改 `cordis.yml`（那是空数组，只是根）。

### 2.2 已有预设（本机现状，2026-10-13 核实）

| profile | provider | model | 思考强度 |
|---|---|---|---|
| `desktop`（你日常 GUI） | `cmdc` | `deepseek/deepseek-v4.1-flash` | `max` |
| `web` | `cmdc` | `z-ai/glm-5.3-flash` | `max` |
| `headless` | `cmdc` | `z-ai/glm-5.3-flash` | `max` |
| `acp` | `cmdc` | `z-ai/glm-5.3-flash` | `max` |

`cmdc` = commandcode 网关（`https://api.commandcode.ai/provider/v1`，`api: openai-responses`）。

### 2.3 怎么改

只改默认模型，最小写法（追加到该 profile 的 `cordis.patch.yml`）：

```yaml
- id: agent-default-model
  name: "@deepseek-ai/dsh-agent-default-model"
  config:
    provider: cmdc
    model: z-ai/glm-5.3-flash
    reasoningEffort: max      # low | high | max
```

**两个必须知道的坑**：

1. 光有上面的行**不够**——还得同时有 `llm-pi-ai` 段把 provider 的网关地址与模型清单声明出来，
   否则 provider 认不出来。完整可用样例见
   [~/.dsh/profiles/web/cordis.patch.yml](file:///C:/Users/BOBO/.dsh/profiles/web/cordis.patch.yml)（44 行，可直接抄）。
2. **ACP profile 要额外写一处**：ACP 服务器用的是它自己插件头的配置，会盖掉
   `agent-default-model`。必须补：

   ```yaml
   - id: acp
     name: '@deepseek-ai/dsh-acp'
     config:
       provider: cmdc
       model: z-ai/glm-5.3-flash
   ```

   否则 `dsh --profile acp` 会拿 `deepseek-official`（无凭据）去发请求而挂住。

### 2.4 怎么确认生效（三种，按可信度从高到低）

1. **组合结果**：`dsh --dump-config` 打印合成后的 profile 树，搜 `agent-default-model` 看 config。
   （只证明"配置进去了"，不证明"模型答应了"。）
2. **会话内自问**：给会话发一句 `你现在用的是什么模型？`，看它自报。实测能答出
   `z-ai/glm-5.3-flash`。
3. **看投影（最硬）**：用宿主 API 读该会话的 `modelSelection`，它由 DSH 自己记：

   ```powershell
   node agent-hub\scripts\dsh-drive.cjs read --session <id> --json
   # → model.lastUsed = { provider: "cmdc", model: "…", reasoningEffort: "max" }
   ```

   > 实测样本：`{"provider":"cmdc","model":"deepseek/deepseek-v4.1-flash","reasoningEffort":"max"}`

**思考强度怎么看**：`reasoningEffort: max` 的直接表现是 headless `--json` 里出现大量
`{"type":"thinking",…}` 事件、且同一任务耗时明显变长；`low` 时思考事件很少。

---

## §3 启动命令

### 3.1 桌面 GUI

直接运行程序即可，无需参数：

```powershell
& 'C:\bobo_worktool\DeepSeek Harness\DeepSeek Harness.exe'
```

- 它内部会起一个 **Web/API 宿主在 `127.0.0.1:19387`**（本机实测，多次重启后端口一致）。
  这个宿主就是 `dsh-drive.cjs` 驱动的对象（§4.1 ③）。
- 浏览器访问 `http://127.0.0.1:19387/` 需要鉴权 cookie；正常入口是它自己打开的页面。
- **GUI 是"内存权威"的**：它读入 `workspace.json` 后就不再重读，外部改这个文件它不会看见（见 §6）。

**VS Code 也是同一个宿主的前端**（可选，已装好）：扩展
`lucasliang.harness-connector-deepseek` v0.2.2 附着到上面这个宿主，
侧栏里用 `DeepSeek Harness: Refresh Sessions` 重读会话列表——这是**不用按 F5** 的那条路。
刚装完/刚改完设置时需先 `Ctrl+Shift+P` → `Developer: Reload Window` 让它生效。

### 3.2 `dsh web` —— 另起一个网页实例

```powershell
& $DSH --profile web [--port <port>] [--host <host>] [--no-open] [--trusted-host <authority>...]
```

| 参数 | 解释 |
|---|---|
| `--port <port>` | 监听端口；**传 0 让系统分配空闲端口** |
| `--host <host>` | 绑定地址（默认回环） |
| `--no-open` | 不自动打开浏览器 |
| `--trusted-host <authority...>` | 额外信任的 authority（`/api` 的 Host/Origin 围栏用），可重复 |

- 启动后**第一行会打印带 `?token=` 的 URL**——这个 token 是换取鉴权 cookie 的入口，别丢。
- 本机封装脚本（已实测）：[start-dsh-web-workspace.ps1](<../../agent-hub/scripts/start-dsh-web-workspace.ps1)

  ```powershell
  powershell -File agent-hub\scripts\start-dsh-web-workspace.ps1 [-Port 19391] [-NoOpen]
  ```

  它带**端口占用防护**（已被占用时给警告而不是起第二个），前台运行、Ctrl+C 即停。

### 3.3 `dsh headless` —— 一次性任务（自动化主力）

```powershell
& $DSH --profile headless [--json] [--session-id <id>] <task...>
```

| 参数 | 解释 |
|---|---|
| `task...` | 任务文本，多个词用空格连接；**传 `-` 表示从 stdin 读** |
| `--json` | 输出 NDJSON 运行事件（而不是只输出最终消息） |
| `--session-id <id>` | **接着已有会话跑**；id 不存在会报错 |

- 退出码：成功 `0`；失败非 0。
- 答案走 stdout，诊断信息走 stderr。
- 本机封装脚本（已实测）：[dsh-headless-run.ps1](<../../agent-hub/scripts/dsh-headless-run.ps1)

  ```powershell
  powershell -File agent-hub\scripts\dsh-headless-run.ps1 -Task "任务"                    # 新会话
  powershell -File agent-hub\scripts\dsh-headless-run.ps1 -SessionId <id> -Task "继续"    # 续会话
  powershell -File agent-hub\scripts\dsh-headless-run.ps1 -Task "任务" -Json              # NDJSON
  ```

  它内部固定走 **stdin 模式 + 显式 UTF-8 管道编码**（就是为了绕开 §6 那两个坑），
  并且会把报错翻译成人话（如 `already owned by an active write handle` → 提示该会话正被 GUI 占用）。

### 3.4 `dsh acp` —— ACP 服务器

```powershell
& $DSH --profile acp
```

- 走 **stdio（stdin/stdout）的 JSON-RPC**，**没有端口、没有 URL**；由客户端进程拉起它。
- 唯一参数是 `-h/--help`；一切参数由 ACP 协议在会话里给（模型也可由客户端逐会话切换）。
- 实测能力：`initialize` 应答 `deepseek-harness-acp`；支持 `session/new`、`session/list`、
  `session/resume`、`session/close`；事件流有 `agent_thought_chunk` / `agent_message_chunk`。
- 已知短板（社区反馈，非本机实测范围）：没有 `session/load`、`session/list` 不回标题，
  部分客户端里会话会显示为空白/无标题。

### 3.5 `dsh plugin` —— 给 profile 装插件

```powershell
& $DSH plugin --profile <name> add <package>
```

### 3.6 启动器通用参数

| 参数 | 解释 |
|---|---|
| `--profile <name>` | 启动 `$DSH_HOME/profiles` 下哪个 profile |
| `--from-default-profile <name>` | 用内置模板初始化一个**新** profile |
| `--patch <path>` | 追加一层补丁覆盖（**可重复**，排在 profile 层之后） |
| `--dump-config` | 打印合成后的 profile 树后退出（**验证配置用**） |
| `--dump-config-schema` | 打印条目/补丁的 JSON Schema，不挂载 |
| `--dump-default-config` | 打印**不含**用户层与 `--patch` 的树 |

> 注意：`--profile` 之后的参数是**给被启动的 app** 的。例如
> `dsh --profile web --port 8080` 里的 `--port` 是 web app 的参数。

---

## §4 会话操作

| 操作 | 怎么做 | 状态 |
|---|---|---|
| **新建（GUI）** | GUI 里点「新会话」；归属当前工作区 | ✅ |
| **新建（CLI，一次性）** | `dsh --profile headless "任务"` | ✅ 实测 |
| **新建（进工作区、GUI 能看到）** | `dsh-drive.cjs run --cwd <目录> --prompt "…"` | ✅ 实测 |
| **新建（ACP）** | ACP `session/new` | ✅ 实测 |
| **指定会话续接（CLI）** | `dsh --profile headless --session-id <id> "继续"` | ✅ 实测（跨进程保留上下文） |
| **指定会话续接（GUI）** | 在会话列表点开它，直接打字 | ✅ |
| **指定会话续接（宿主 API）** | `dsh-drive.cjs prompt --session <id> --prompt "…"` | ✅ 实测 |
| **查询会话列表** | `dsh-drive.cjs list [--cwd <目录>]`（带标题/运行状态/cwd） | ✅ 实测 |
| **查询某会话内容** | `dsh-drive.cjs read --session <id> [--tail N]` | ✅ 实测 |
| **追加任务（排队）** | 同 `prompt`，默认 `mode: queue`（当前这轮跑完再接） | ✅ |
| **插话（打断当前轮）** | `prompt --steer`（`mode: steer`） | ✅ 接口支持（实测走的是 queue） |
| **中止** | 宿主 API `session/cancel`（`DshHostClient.cancel(id)`）；GUI 里也有停止按钮 | ⚠️ 接口存在，**未单独实测** |
| **重命名** | `DshHostClient.rename(id, title)` / GUI 里改 | ✅ 实测 |
| **归档 / 置顶 / 排序 / 派生(fork)** | 宿主 API：`workspace/archiveSession`、`workspace/pinSession`、`workspace/insertBefore`、`session/fork` | ⚠️ 接口存在，未实测 |
| **删除会话** | **宿主 API 没有 delete**；只能归档，或直接删 `~/.dsh/sessions/` 下的落盘文件（不建议，会让索引指向不存在的会话） | — |

### 4.1 三种驱动通道怎么选

```
① headless  —— 无人值守批处理。会话是独立宿主进程建的，GUI 列表里默认看不到。
② ACP       —— 给 ACP 客户端用（Zed / JetBrains / acpx）。语义级流式，但缺 session/load。
③ 宿主 API  —— 【推荐做协作】驱动「正在运行的 GUI 宿主」本身，
              会话诞生在 GUI 进程内 → 自动进工作区 → 你能看到也能插话。
```

③ 的入口就是 `dsh-drive.cjs`（底层 [dsh-host-client.cjs](<../../agent-hub/scripts/dsh-host-client.cjs)）：

```powershell
node scripts\dsh-drive.cjs run    --prompt "…" [--title "…"] [--cwd DIR] [--authority H:P] [--json]
node scripts\dsh-drive.cjs prompt --session <id> --prompt "…" [--steer] [--json] [--wait] [--timeout MS]
node scripts\dsh-drive.cjs read   --session <id> [--tail N] [--json]
node scripts\dsh-drive.cjs list   [--cwd DIR] [--json]
node scripts\dsh-drive.cjs wait   --session <id> [--timeout MS] [--json]
node scripts\dsh-drive.cjs probe
```

编程接口：

```js
const { DshHostClient } = require('./scripts/dsh-host-client.cjs');
const c = new DshHostClient({ authority: '127.0.0.1:19387' });
const ws = await c.ensureWorkspace('C:\\...\\agent开发');   // 幂等，拿到 workspaceId
const { sessionId } = await c.createSession({ workspaceId: ws.workspaceId });
await c.rename(sessionId, '协作方案2');
await c.prompt(sessionId, '你好');
await c.waitIdle(sessionId);                                  // 等跑完
const page = await c.page(sessionId);
console.log(DshHostClient.assistantText(page));               // 取助手文本
```

---

## §5 输出与状态

### 5.1 会话 ID 从哪里来

| 通道 | 取法 |
|---|---|
| **headless `--json`** | 事件流第一类事件就是它：`{"type":"session","sessionId":"session-…","cwd":"…"}` |
| **headless 人类模式** | stdout 只有最终答案；要 id 就加 `--json` |
| **宿主 API 建会话** | `session/create` 返回值 `{ sessionId, agentPreset }`；`dsh-drive.cjs run --json` 直接给出 |
| **GUI** | 会话列表里选中会话；`dsh-drive.cjs list` 也能列出全部 id |
| **ACP** | `session/new` / `session/list` 的返回 |
| **落盘** | 文件名就是 id：`~/.dsh/sessions/<sessionId>.jsonl.zst` |

id 形如 `session-dfe94afd-632a-4cc3-b578-215dbb42650f`（有的子代理是裸 UUID）。

### 5.2 结果怎么读

| 通道 | 读法 |
|---|---|
| headless（默认） | stdout 就是最终答案 |
| headless `--json` | NDJSON，逐行 parse；关注 `thinking` / `text` / `final` / `usage`；**最后一条 `final` 的 `text` 是答案** |
| 宿主 API | `session/page` 取事件页 → 抽 `assistant/message` 里的 text（`DshHostClient.assistantText(page)`） |
| GUI | 会话窗口里直接看（思考、工具调用、结果都在） |
| 落盘 | `~/.dsh/sessions/*.jsonl.zst`，**多 zstd 帧追加**，要逐帧解压再合并 |

### 5.3 怎么判断"跑完了"

| 通道 | 判据 |
|---|---|
| headless | **进程退出**，`$LASTEXITCODE` = 0 即成功；stderr 有诊断 |
| 宿主 API | 轮询会话列表里的 `running` 字段：**先变 true 再变 false = 这一轮结束**（`waitIdle()` 就是这个逻辑，带超时） |
| GUI | 列表行上显示「进行中」/状态图标 |

> 实测样本（`dsh-drive.cjs run`）：
> `session created: session-… → prompt accepted → idle（running=false）→ records=26`

---

## §6 注意事项与验证状态

### 6.1 Windows/PowerShell 三个必踩的坑

1. **PS 5.1 写文件默认带 BOM** —— `Set-Content -Encoding UTF8` 在 5.1 里是**带 BOM**，
   DSH 的存储层不剥 BOM 直接 `JSON.parse` → 抛 `malformed-medium`，整个存储域起不来。
   > 正确写法：`[System.IO.File]::WriteAllText($p, $t, (New-Object System.Text.UTF8Encoding($false)))`
   > 或直接改用 PowerShell 7（`pwsh`）。

2. **含非 ASCII 的 `.ps1` 必须存成 UTF-8 带 BOM** —— 否则 PS 5.1 按 ANSI/GBK 读，
   中文注释变乱码、脚本解析失败。本仓库的两个脚本都已是 BOM 格式（已核实）。

3. **任务文本里有 `< > | &` 会炸** —— `dsh.cmd` 经 `cmd.exe` 转发时这些是元字符。
   > 解法：走 stdin（`-`），并且显式 `$OutputEncoding = New-Object System.Text.UTF8Encoding $false`，
   > 否则中文经管道会被 PS 5.1 按 GBK 发出、dsh 按 UTF-8 读 → 乱码。

### 6.2 DSH 自身的结构性限制

1. **单写者**：一个会话同一时刻只能有一个写者。GUI 打开某会话并不等于占写权
   （实测在 GUI 打开的同时用宿主 API `session/prompt` 注入成功），
   但 headless 去写一个 GUI 正持有的会话可能报
   `already owned by an active write handle`。
2. **存储域只在进程内广播变更**（官方 README 明说）：
   `domain/changed` 是进程内事件，**另一个宿主进程或重连的 GUI 在跨进程修订方案落地前观察不到变更**；
   且 JSON 后端**以内存为权威、每次整体重写文件**。
   → 所以**外部进程写 `workspace.json` 登记会话是无效的**（GUI 不重读，还会被它覆盖）。
   → 正确做法：会话要进工作区，就用宿主 API 建（`workspaceId` 而不是只给 `cwd`）。
     **只给 `cwd` 的会话会落进侧栏的「未分组」**（默认折叠，看起来像没出现）。
3. **侧栏列表可能不实时刷新**：宿主确实把 `api-session/added`、工作区 `upsert`、`title` 投影都推给了
   浏览器（抓帧可见），但客户端有时不重渲染（上游讨论 #8392 的单飞卡死，UI 也没有"重新加载列表"入口）。
   → **补救：在那个页面按一次 F5**（实测 3/3 恢复），**不需要重启整个应用**。

### 6.3 常见问题与恢复

| 症状 | 原因 | 处理 |
|---|---|---|
| GUI 会话列表打不开 / 添加工作区报 `workspaceController is unavailable` | `workspace.json` 被写坏（通常是 BOM） | 用无 BOM 重写该文件，然后**完全退出并重开**桌面程序（存储域起不来不会自愈）；历史备份：`~/.dsh/storages/workspace.json.bak-*` |
| 列表里看不到外部建的会话 | 会话没进工作区（只给了 `cwd`） | 用宿主 API 的 `workspace/create` 拿 `workspaceId` 再建；或按 F5 看「未分组」 |
| 新会话建了但侧栏没有 | 客户端列表未重渲染 | 按 F5 |
| `already owned by an active write handle` | 该会话正被别的写者持有 | 关掉 GUI 里那个会话窗口，或改成用宿主 API 驱动 |
| 模型不对 / 请求挂住 | profile 补丁没生效；或 ACP 忘了补 `- id: acp` 那段 | `dsh --dump-config` 核对；见 §2.3 |
| 中文任务乱码 | 管道编码 | 见 §6.1 第 3 条 |
| 端口被占 | 已有实例在跑 | `Get-NetTCPConnection -LocalPort <port> -State Listen` 看 pid；或换端口 / 用 `--port 0` |
| 需要停止某个 web 实例 | — | `Stop-Process -Id <pid> -Force`（pid 来自上面那条命令） |

### 6.4 本例验证范围与日期

**验证日期：2026-10-13**（同一台机器、同一份配置）。实测覆盖：

| 项 | 结论 |
|---|---|
| CLI 版本与入口 | ✅ `dsh --version` = 0.2.0-rc.2；`dsh.cmd` 路径有效 |
| `--help` 系列 | ✅ 启动器 / web / headless / acp 四个 help 均已读取并据此撰写 §3 |
| 模型配置生效 | ✅ 会话自报 `z-ai/glm-5.3-flash`；投影 `modelSelection` 实测到 `cmdc / deepseek-v4.1-flash / max` |
| headless 新建任务 | ✅ `exit 0`，NDJSON 拿到 `sessionId`，`final.text = "可用"` |
| headless 续会话 | ✅ `--session-id` 跨进程保留上下文（前序轮次已验证 4 轮） |
| 宿主 API 建会话/下指令/读结果 | ✅ 建会话进工作区、`prompt` 19ms 受理、`waitIdle` 判定结束、`page` 读回文本 |
| 会话在 GUI 可见 + 可插话 | ✅ 浏览器实测（侧栏出现、点开、转写含注入内容；F5 恢复 3/3） |
| ACP 通道 | ✅ `initialize`/`session new·list·resume` 可用 |
| 中止 / 归档 / fork | ⚠️ 接口存在但**本次未实测** |
| 桌面 GUI 端口 | ✅ `127.0.0.1:19387`（多次重启后一致，但**未跨大版本升级验证**） |

### 6.5 相关文档

- 原理与协作方案：[gui-live-agent-collaboration.md](<../../agent-hub/docs/gui-live-agent-collaboration.md)
- VS Code 连接器安装/验证记录：同上文档 §6
- 工作区整体导航：[`../../README.md`](../../README.md)
- 通道脚本：[dsh-host-client.cjs](<../../agent-hub/scripts/dsh-host-client.cjs)、[dsh-drive.cjs](<../../agent-hub/scripts/dsh-drive.cjs)
- 封装脚本：[start-dsh-web-workspace.ps1](<../../agent-hub/scripts/start-dsh-web-workspace.ps1)、[dsh-headless-run.ps1](<../../agent-hub/scripts/dsh-headless-run.ps1)