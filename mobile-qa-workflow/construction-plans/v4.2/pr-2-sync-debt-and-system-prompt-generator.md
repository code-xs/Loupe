# PR-2 · 同步债清理 + state 字段瘦身 + system-prompt 生成器交付（v4.2 详细施工单）

> **主控文档**：[`./README.md`](./README.md)（§6 PR-2 / §3 H1 / §4 CI 守门表）
> **方案文档**：[`../../../doc/MOBILE_QA_WORKFLOW_STATE_SYNC_OPTIMIZATION_V1.1_2026-04-21.md`](../../../doc/MOBILE_QA_WORKFLOW_STATE_SYNC_OPTIMIZATION_V1.1_2026-04-21.md) §3.2.7 / §3.2.8 / §3.2.9 / §3.2.17
> **关联 V1.1 项**：O5（脚本提取器修复 + 升级 error）+ O7（删 `rca_fanout_mode_snapshot` **+ 同步补 P3 重入读端**）+ O8（合并 `fix_strategy_mode` → `fix_fanout_mode`）+ O9（计数器注释归类）+ O17+（生成器**最小完整实现** + 单测，**不**替换 `system-prompt.md`）+ O22（新增 `check-build-system-prompt-precondition.sh`，**锚点提取式**实现）
> **状态**：📐 已展开（v1.2，2026-04-21；v1.1 经 [REVIEW v1.1 报告](./pr-2-sync-debt-and-system-prompt-generator-REVIEW-v1.1-2026-04-21.md) 复审后做收敛性小修：① regex 兼容 XML 引号 ② READ-N1/N2 真实落点对齐 ③ §2.5 范围描述自洽 ④ fixture 改名 ⑤ O7 DoD grep 口径精确化；详见 Changelog）
> **唯一职责**：**主路径零运行时分支变更**前提下，完成 v4.2 收敛的"同步债清理 + state 瘦身 + 生成器交付"三件事 ——
> ① 删除冗余字段 `rca_fanout_mode_snapshot`（O7，方案 A `phase_history` 反查已是主路径，snapshot 是冗余兜底）；**同步在 P3 step 4 / 编排器补一个最小读端**（v1.1 review Blocking 1 修订：选方案 B —— 不在 PR-2 内留下"写端在、读端不在"的协议缺口）
> ② 合并同义字段 `fix_strategy_mode` → `fix_fanout_mode`（O8，P4 内部 `fix_fanout_mode = {fix_strategy_mode}` 同值赋两次，本质是同一信息两个名字）
> ③ 给 5 个计数器加 `# group: retries` 注释归类（O9，**不动 schema**）
> ④ 交付 `scripts/build-system-prompt.py` **最小完整实现** + 单测（O17+ Stage 1，**不**首次构建并替换 `system-prompt.md`，等 PR-4 O13a 合入后由 PR-6 触发首次构建。v1.1 review Major 3 修订：写死"最小完整实现"，不再用"骨架"摇摆口径）
> ⑤ 修复 `check-system-prompt-sync.sh` 提取器缺陷（v1.1 review Blocking 2：当前主干 ENUM-DECLARATION-BLOCK / Spec-Uncertain `allowed_values` 提取均存在脆弱命中），**修完且实跑零 warning 后**再升级 severity warning → error
> ⑥ `check-io-contract.sh` **本 PR 不升级 error**（v1.1 review Major 1 修订：选选项 A —— 当前脚本 12/13 走变量化兜底，假绿守门价值不足，推迟到后续算法增强 PR；本 PR 维持 warning 现状）
> ⑦ 新增 `check-build-system-prompt-precondition.sh`（H1 守门，**锚点提取式**：先在 `system-prompt.md` / `core/workflow.xml` 的 Spec-Uncertain 段前各加一行稳定锚点注释，再按锚点 + N 行内提取 `allowed_values=`，缺锚点直接 error；v1.1 review Major 4 修订：彻底摆脱"head -1 取首次命中"的脆弱模式）

---

## 1. PR 元信息

| 项 | 值 |
|---|---|
| 分支命名 | `feat/qa-workflow-v4.2-pr2-sync-debt-and-system-prompt-generator` |
| Base | PR-1 合入后的 `main` |
| 层级 | 🟡 **schema 瘦身 + 工具交付 + 最小读端补齐**：state 字段瘦身有迁移脚本配套；O7 同步补 P3 重入读端（v1.1 review 修订点）；生成器交付为最小完整实现，不替换 system-prompt.md |
| 目标合入顺序 | PR-1 → **PR-2** → (PR-3 ‖ PR-4) → PR-5 → PR-6 → PR-7（详见主控 §2） |
| Reviewer | 1 名方案 owner（必看 O7/O8 字段瘦身全引用点扫净 + **P3 反查读端实现 + 回放用例 1 条** + 生成器 L0-L4 五个 builder 是否最小完整可跑）+ 1 名平台 owner（必看 H1 锚点守门脚本 + Limited 平台抽 1 用例验证迁移脚本不破坏 v3 会话） |
| 关联 V1.1 项 | O5（`check-system-prompt-sync.sh` **提取器修复 + 升级 error**）+ O7（删 `rca_fanout_mode_snapshot` 5 处引用 + **P3/编排器读端补齐 + 1 条回放用例** + 迁移脚本兼容）+ O8（合并 `fix_strategy_mode` → `fix_fanout_mode` 6 处引用 + 迁移脚本拷值）+ O9（5 个计数器加 `# group: retries` 注释，不动 schema）+ O17+ Stage 1（`scripts/build-system-prompt.py` **最小完整实现** + `tests/test_build_system_prompt.py`，**不**首次构建）+ O22（`check-build-system-prompt-precondition.sh` 新建为 error，**锚点提取式**）|
| 工作量 | **2.7d**（v1.1 上调 0.5d，拆分：O7/O8/O9 字段瘦身 ≈ 0.6d / **O7 P3 反查读端 + 回放用例 ≈ 0.3d** / O17+ 生成器最小完整实现 + 单测 ≈ 1.0d / **O5 脚本提取器修复 + 升级 + H1 锚点新增 ≈ 0.5d** / 跨平台回归 + Limited 验证 ≈ 0.3d）|
| 涉及文件 | **新增**：`mobile-qa-workflow/scripts/build-system-prompt.py` + `mobile-qa-workflow/scripts/tests/test_build_system_prompt.py` + `mobile-qa-workflow/scripts/check-build-system-prompt-precondition.sh` + `mobile-qa-workflow/scripts/tests/fixtures/p3-reentry-null-fanout-with-phase-history.yaml`（v1.1 新增 / v1.2 改名：P3 反查读端回放用例 fixture，文件名与"fanout_mode = null + phase_history 含末项"语义一致）+ `mobile-qa-workflow/scripts/tests/test_p3_reentry_replay.py`（v1.1 新增：调编排器/P3 路径模拟反查的最小回放脚本）。**修改**：`mobile-qa-workflow/core/workflow-status-template.yaml`（O7 删 `rca_fanout_mode_snapshot` + O8 删 `fix_strategy_mode` + O9 加注释）+ `mobile-qa-workflow/core/workflow.xml`（O8 把 **step 2** 读字段列表与 v3 兼容默认值中的 `fix_strategy_mode` 改为 `fix_fanout_mode`；**v1.1 新增**：① **step 2** 读字段列表追加 `phase_history`；② Spec-Uncertain 段前加锚点 `<!-- ANCHOR: spec-uncertain-allowed-values -->`；**v1.2 修订**：step 1/2 表述对齐真实文件结构 — step 1 仅 `<load>`，读字段列表实际在 step 2）+ `mobile-qa-workflow/phases/p3-root-cause.md`（O7 删 step 10 内 snapshot 写入行 + 注释收敛；**v1.1 新增**：step 4 头部追加"若 `fanout_mode` 缺失/null 则反查 `phase_history` 末项 `qa-root-cause` 元素的 `fanout_mode` 还原"逻辑）+ `mobile-qa-workflow/phases/p4-fix-design.md`（O8 删 step 2 内 `fix_strategy_mode` 赋值行，统一只写 `fix_fanout_mode`；step 3 内升级路径 `fix_strategy_mode = contested-arbitrated` 改为 `fix_fanout_mode = contested-arbitrated`）+ `mobile-qa-workflow/system-prompt.md`（O7 删 `rca_fanout_mode_snapshot` 字段表行 + O8 把 `fix_strategy_mode` 出现处改为 `fix_fanout_mode`；**v1.1 新增**：Spec-Uncertain 段前加锚点 `<!-- ANCHOR: spec-uncertain-allowed-values -->`；**禁止其他改动**）+ `mobile-qa-workflow/SKILL.md`（O7 删字段表 1 行 + O8 把 `fix_strategy_mode` 字段描述合并到 `fix_fanout_mode` 行）+ `mobile-qa-workflow/PLATFORM-GUIDE.md`（O7 删 `rca_fanout_mode_snapshot` 引用 2 处 + O8 删 `fix_strategy_mode` 引用 2 处）+ `mobile-qa-workflow/scripts/migrate-workflow-status-v3-to-v4.py`（**v4 内部清理增强**：增加 `--cleanup-v4-deprecated` 子命令，幂等地把存量会话的 `fix_strategy_mode` 值拷贝到 `fix_fanout_mode`、删除 `rca_fanout_mode_snapshot` 与 `fix_strategy_mode` 字段；**不**改 v3→v4 主路径；**v1.1 修订**：删除文件头 docstring 中"不实施 fanout_mode 反查还原逻辑"一句 — 该断言在本 PR 不再成立）+ `doc/adr/007-fanout-mode-no-rename.md`（追加 v4.2 修订段落，注明 `rca_fanout_mode_snapshot` 已废弃 / `fix_strategy_mode` 已合并 / **P3 反查读端落地**）+ `doc/adr/000-index.md`（ADR-007 备注列追加 "v4.2 PR-2 修订"）+ `mobile-qa-workflow/scripts/check-system-prompt-sync.sh`（**v1.1 修订**：脚本提取器需修复 — ENUM 集提取改用 python 严格抽 enum 注释块、Spec-Uncertain `allowed_values` 提取改用锚点定位；默认 SEVERITY warning → error）+ `.github/workflows/qa-workflow-schema-check.yml`（升级 Check 10 严重度 + 新增 Check 13/14；**v1.1 修订**：**不再**升级 Check 11 io-contract，保持 warning）。**删除**：无（`rca_fanout_mode_snapshot` / `fix_strategy_mode` 字段是从 schema 删除，不是文件删除）。 |
| 不在本 PR 范围 | ① **首次构建并替换 `system-prompt.md`**（H1：等 PR-4 O13a 合入后由 PR-6 触发）② Spec-Uncertain 契约 `Confirm` → `1\|2\|S` 改写（PR-4 范围）③ `<phase-abort>` / `<phase-complete>` 宏标签（PR-3 范围）④ step-pause-registry 数据化（PR-5 范围）⑤ phase 内联 step-pause 删除（PR-6 范围）⑥ `<core-rules-essential.xml>` / `coder-agent.md` 拆分（PR-7 范围）⑦ Schema 大版本号 bump（保持 `schema_version=4` 不动；本 PR 删除字段属于"v4 内部清理"，新增 `--cleanup-v4-deprecated` 子命令幂等处理）⑧ **`check-io-contract.sh` 升级 error**（v1.1 review Major 1：当前脚本变量化兜底过宽，先维持 warning，待后续算法增强 PR 一并升级）⑨ **`check-io-contract.sh` 算法重写**（同上，本 PR 不动脚本逻辑） |

---

## 2. 文件级 diff 列表

> 本 PR 共 **8 类变更点**（v1.1 合计 ~28 个），按"先 schema 瘦身 → 再下游引用扫净 → 再读端补齐 → 再迁移脚本兜底 → 再生成器交付 → 再脚本修复 + CI 升级 / 新增 → 再回放验证"顺序：
>
> | 编号前缀 | 含义 | 数量 |
> |---|---|---|
> | **TPL-S1~S3** | O7/O8/O9 schema 模板瘦身 | 3 |
> | **REF-D1~D7** | O7/O8 下游引用扫净（workflow.xml / phases / system-prompt / SKILL / PLATFORM-GUIDE） | 7 |
> | **READ-N1~N2**（v1.1 新增 / v1.2 落点修订） | O7 P3 重入读端补齐（P3 step 4 反查 + 编排器 step 2 字段声明联动） | 2 |
> | **MIG-N1** | O7/O8 迁移脚本兜底（v4 内部清理子命令） | 1 |
> | **ADR-D1 / ADR-IDX1** | ADR-007 v4.2 修订段落 + 索引同步 | 2 |
> | **GEN-N1~N3** | O17+ Stage 1 生成器**最小完整实现**（脚本 + 单测 + 头部模板片段） | 3 |
> | **ANCHOR-N1~N2**（v1.1 新增） | H1 锚点：`system-prompt.md` + `core/workflow.xml` 各加一行 Spec-Uncertain 锚点注释 | 2 |
> | **TEST-N1**（v1.1 新增） | P3 反查读端回放用例（fixture + test 脚本） | 1 |
> | **SCRIPT-FIX1**（v1.1 新增） | `check-system-prompt-sync.sh` 提取器修复（ENUM block 严格化 + Spec-Uncertain 锚点定位） | 1 |
> | **CI-U1a / CI-U1b / CI-N1 / CI-W1** | O5 拆分（U1a 脚本修复-合并入 SCRIPT-FIX1 / U1b severity 升级）+ O22 新增（H1 锚点守门）+ workflow yml 集成 | 4 |
>
> **变更点编号约定**：S\* = schema 模板修改 / D\* = 下游引用 diff / N\* = 新建文件 / U\* = 升级现有文件严重度 / W\* = workflow yml 集成 / **READ-\*** = 读端补齐（v1.1）/ **ANCHOR-\*** = 文档锚点新增（v1.1）/ **TEST-\*** = 回放用例新增（v1.1）/ **SCRIPT-FIX\*** = 现有脚本提取器修复（v1.1）。
>
> **v1.1 review 修订映射**（完整对照见 [REVIEW 报告](./pr-2-sync-debt-and-system-prompt-generator-REVIEW-2026-04-21.md)）：
> - **Blocking 1（O7 读端）** → 新增 READ-N1/N2 + TEST-N1
> - **Blocking 2（O5 直升 error）** → CI-U1 拆分为 SCRIPT-FIX1 + CI-U1b
> - **Major 1（io-contract 宽松）** → CI-U2 删除（推迟到后续 PR）
> - **Major 2（口径冲突）** → 顶部"涉及文件"列已重写至与各 §2.x 变更点完全一致
> - **Major 3（生成器口径）** → §1 题注 ④ + §2.9 标题写死"最小完整实现"
> - **Major 4（H1 脆弱）** → 新增 ANCHOR-N1/N2 + 重写 CI-N1 为锚点提取式

---

### 2.1 文件 A · `core/workflow-status-template.yaml`（schema 瘦身 / TPL-S1~S3）

#### 2.1.1 变更点 TPL-S1 · 删除 `rca_fanout_mode_snapshot` 字段（O7）

**原文（行号锚点 L35-37）**：

```35:37:mobile-qa-workflow/core/workflow-status-template.yaml
# C10 兼容性方案 B 兜底：P3 完成时 fanout_mode 的快照，用于 P3 重入时还原 RCA 上下文；
# 与 phase_history 中元素的 fanout_mode 字段双保险（迁移脚本 §6.3 利用该值还原 fanout_mode）。
rca_fanout_mode_snapshot: null
```

**新文**（**整段删除** 3 行：注释 2 行 + 字段 1 行）：

```yaml
# (删除：v4.2 PR-2 / O7 / 详见 ADR-007 v4.2 修订段落)
# rca_fanout_mode_snapshot 已废弃 — 方案 A (phase_history 反查) 已是主路径，
# snapshot 字段是冗余兜底；存量会话由 migrate-workflow-status-v3-to-v4.py
# --cleanup-v4-deprecated 子命令幂等清理。
```

**修订理由**：
- V1.1 §3.2.7：方案 A（`phase_history`）已是主路径；snapshot 仅在迁移脚本反查为空时兜底，但 PR-4 P3 写入端落地后 `phase_history` 永远非空，snapshot 是纯冗余。
- 删除后 `workflow-status-template.yaml` 顶层字段数 27 → 26。

**兼容性影响**：
- **新会话**：P3 不再写 snapshot；`phase_history` 反查仍是主路径；不影响路由。
- **存量会话**：`workflow-status.yaml` 中已存在 `rca_fanout_mode_snapshot: <value>` 不会自动消失，但读端（迁移脚本反查）改为只读 `phase_history`；变更点 MIG-N1 提供 `--cleanup-v4-deprecated` 幂等清理（删除该字段）。
- **迁移脚本主路径**：v3→v4 注入逻辑同步删除 `rca_fanout_mode_snapshot` 的注入条目（详见 MIG-N1）。

---

#### 2.1.2 变更点 TPL-S2 · 删除 `fix_strategy_mode` 字段（O8）

**原文（行号锚点 L39）**：

```39:39:mobile-qa-workflow/core/workflow-status-template.yaml
fix_strategy_mode: null
```

**新文**（**整行删除**；保留上下文 `fix_fanout_mode: null` 一行不动）：

```yaml
# (删除：v4.2 PR-2 / O8 / 详见 ADR-007 v4.2 修订段落)
# fix_strategy_mode 与 fix_fanout_mode 同义（P4 step 2 内 fix_fanout_mode = {fix_strategy_mode} 同值赋两次）；
# 保留 fix_fanout_mode 命名（与 RCA 字段 fanout_mode 命名对称，更清晰）；
# 存量会话由 --cleanup-v4-deprecated 子命令幂等迁移（拷值后删 fix_strategy_mode）。
```

**修订理由**：
- V1.1 §3.2.8：`p4-fix-design.md:33-37` 显式 `fix_fanout_mode = {fix_strategy_mode}`，两个字段语义重合。
- `fix_fanout_mode` 命名与 `fanout_mode` 对称（C10 字段隔离引入），保留它更清晰；删 `fix_strategy_mode` 即可。
- 删除后 `workflow-status-template.yaml` 顶层字段数 26 → 25。

**兼容性影响**：
- **新会话**：P4 只写 `fix_fanout_mode`；下游读端（PR-1 已合入的 `core/workflow.xml` step 1 / `system-prompt.md` 字段表）由 REF-D1 ~ D6 同步收敛。
- **存量会话**：MIG-N1 提供拷值迁移（`fix_strategy_mode` 值拷贝到 `fix_fanout_mode` 后删除 `fix_strategy_mode`）。

---

#### 2.1.3 变更点 TPL-S3 · 5 个计数器加 `# group: retries` 注释归类（O9）

**操作**：在 `non_bug_reflow_count` / `lint_retry_count` / `rca_retry_count` / `fix_retry_count` / `parse_error_count` 5 个字段附近添加统一注释块；**不动字段名 / 不动默认值 / 不需要迁移脚本**。

**新文**（在现有 `non_bug_reflow_count: 0` 之前插入；现有 `parse_error_count` 注释块保持不动 — 它已经有详细注释，本变更点仅在其前面追加 group 引用）：

```yaml
# ── group: retries（v4.2 PR-2 / O9 注释级归类，不动 schema） ──
# 5 个计数器顶层字段语义同属"重试 / 熔断"组：
#   · non_bug_reflow_count   — Non-Bug 跨轮回流次数（>= 2 → Human-Review）
#   · lint_retry_count       — coder-agent <try retry="3"> 内部隐式管理
#   · rca_retry_count        — RCA 升级 / 回流计数（> 2 → Human-Review）
#   · fix_retry_count        — Fix 升级 / 回流计数（> 2 → Human-Review）
#   · parse_error_count      — step-pause 连续解析失败熔断（>= 3 → Human-Review）
# 写入端 / 重置规则各自独立（详见 V1.1 §2.1.4 / 各 phase 文件）；本注释仅做 reviewer 归类提示。
non_bug_reflow_count: 0
lint_retry_count: 0
```

**修订理由**：
- V1.1 §3.2.9（跨平台调整版）：原版"统一为 `retries.{...}` 命名空间"对小 LLM 嵌套字段读取风险高；本 PR 只做注释级归类，不动 schema，跨平台零影响。
- reviewer 阅读 status 文件时一眼可识别这 5 个字段属于同一类语义。

**兼容性影响**：纯注释新增；YAML parser 无任何感知；零运行时影响。

---

### 2.2 文件 B · `core/workflow.xml`（O8 引用扫净 / REF-D1）

#### 2.2.1 变更点 REF-D1 · step 2 读字段列表与 v3 兼容默认值的 `fix_strategy_mode` 改为 `fix_fanout_mode`

> **v1.2 修订说明**：v1.0/v1.1 文中误称"step 1 读字段列表"。实际 `core/workflow.xml` step 1（L19-21）只做 `<load core-rules.xml>`；读 `{workflow_status}` 字段列表的动作位于 step 2（L28），v3 兼容默认值注入位于 step 2 内的 `<check>`（L30）。文本统一更正为 step 2，行号锚点不变。

**原文（行号锚点 L28 + L30，均位于编排器 step 2 内）**：

```28:30:mobile-qa-workflow/core/workflow.xml
                <action>读取 {workflow_status} 文件，获取 stepsCompleted、current_state、workflow_version、schema_version、analysis_complexity、fanout_mode、fix_strategy_mode、reroute_target_phase、rca_retry_count、fix_retry_count</action>
                <check if="状态文件无 workflow_version 或 workflow_version != 'v4'">
                    <action>将当前状态视为旧版状态文件，补充兼容默认值：workflow_version = legacy, schema_version = 1, fanout_mode = null, fix_strategy_mode = null, reroute_reason = null, reroute_target_phase = null, rca_retry_count = 0, fix_retry_count = 0</action>
```

**新文**（仅替换两处 `fix_strategy_mode` → `fix_fanout_mode`）：

```xml
                <action>读取 {workflow_status} 文件，获取 stepsCompleted、current_state、workflow_version、schema_version、analysis_complexity、fanout_mode、fix_fanout_mode、reroute_target_phase、rca_retry_count、fix_retry_count</action>
                <check if="状态文件无 workflow_version 或 workflow_version != 'v4'">
                    <action>将当前状态视为旧版状态文件，补充兼容默认值：workflow_version = legacy, schema_version = 1, fanout_mode = null, fix_fanout_mode = null, reroute_reason = null, reroute_target_phase = null, rca_retry_count = 0, fix_retry_count = 0</action>
```

**修订理由**：编排器 step 2 仅做读字段声明 + v3 兼容默认值注入，无路由分支改动；改名后行为完全等价。

**兼容性影响**：
- 主路径：编排器 step 2 注入的 `fix_fanout_mode = null` 与 v4 schema 默认值一致；后续 step 3 case 路由及下游 P4 读 `fix_fanout_mode` 行为与原读 `fix_strategy_mode` 一致（P4 内的 fan-out 决策字段语义不变）。
- v3 兼容路径：从读 `fix_strategy_mode = null` 改为读 `fix_fanout_mode = null`，若存量 v3 会话已经迁移到 v4 但未跑 `--cleanup-v4-deprecated`，会同时存在 `fix_strategy_mode` 与 `fix_fanout_mode` 两个字段；编排器只读 `fix_fanout_mode`，`fix_strategy_mode` 残留不污染路由（待下次 cleanup 自然消除）。

---

### 2.3 文件 C · `phases/p3-root-cause.md`（O7 引用扫净 / REF-D2）

#### 2.3.1 变更点 REF-D2 · step 10 内 `rca_fanout_mode_snapshot` 写入行 + 上方 C10 注释段删除

**原文（行号锚点 L222-228）**：

```222:228:mobile-qa-workflow/phases/p3-root-cause.md
        <!-- C10 + D7：兼容性方案 A（顺序历史）+ 方案 B（单点快照）双保险；
             无论本次 P3 是成功完成（最终置信度 >= 0.5）还是低置信 stop，
             都需要记录 P3 完成时的 fanout_mode 取值，供 P3 重入时或迁移脚本反查使用。
             写入顺序：先快照、后历史 append，均在下方 stop 路径强制重写之前执行，
             确保记录的是"P3 本次完成时 fanout_mode 的自然取值"。 -->
        <action>更新 {workflow_status}：rca_fanout_mode_snapshot = {fanout_mode}</action>
        <action>更新 {workflow_status}.phase_history：append { phase: "qa-root-cause", timestamp: &lt;now ISO8601&gt;, fanout_mode: {fanout_mode}, note: null }</action>
```

**新文**（删除快照写入行 + 注释段更新为只描述方案 A）：

```xml
        <!-- ADR-007 (v4.2 PR-2 修订)：方案 A (phase_history 顺序历史) 是主路径；
             snapshot 字段已删除（O7），P3 重入时由 phase_history 反查最近一条
             qa-root-cause 元素的 fanout_mode；写入顺序：phase_history.append 在下方
             stop 路径强制重写之前执行，确保记录的是"P3 本次完成时 fanout_mode 的自然取值"。 -->
        <action>更新 {workflow_status}.phase_history：append { phase: "qa-root-cause", timestamp: &lt;now ISO8601&gt;, fanout_mode: {fanout_mode}, note: null }</action>
```

**修订理由**：
- TPL-S1 删除 schema 字段后，本 phase 写入点必须同步删除（否则 `check-state-enum.sh` 会绿但实际写入到了不存在的字段，YAML parser 会接受但读端永远 null）。
- 注释段保留方案 A 描述（`phase_history.append` 写入顺序约束仍然有效）。

**兼容性影响**：与 TPL-S1 配套；P3 重入还原逻辑改由本 PR 的 **READ-N1（P3 step 4 反查 check）+ READ-N2（编排器 step 2 字段声明）** 联动落地（不再依赖 PR-1 已合入的迁移脚本反查 — 该脚本 docstring 自述"不实施反查还原"，是 v1.1 review Blocking 1 的根因）。

---

#### 2.3.2 变更点 READ-N1 · P3 step 4 头部追加"phase_history 反查 fanout_mode"读端逻辑（v1.1 新增 / O7 方案 B）

> **背景**：v1.1 review Blocking 1 — 删除 `rca_fanout_mode_snapshot` 后，必须有真实可定位的"读 phase_history 反查 fanout_mode"读端，否则 P3 重入时 `fanout_mode = null` 的边缘 case 失去还原依据。本 PR 选方案 B（PR-2 内补最小读端 + 1 条回放用例），不把 O7 推迟到后续 PR。

**操作**（v1.2 落点修订）：在 `phases/p3-root-cause.md` step 4 第一个边界策略动作 `<action>读取 {issue_card} 中的 Issue_Boundary_Level...</action>`（当前 L54）**之前**插入一段反查逻辑，仅当读到的 `fanout_mode` 缺失/null 且 `phase_history` 非空时执行；不影响新会话主路径（首次进入 P3 时 `phase_history` 空、由下方 spec 推断 `fanout_mode`，本逻辑跳过）。

> **v1.2 修订说明**：v1.1 描述误以为 step 4 头部存在"读取 `{issue_card}`"行，实际上 P3 在 step 1（L34）已读取 `{issue_card}、{spec_file}、{context_bundle}、{workflow_status}`，step 4 第一行就是"读取 Issue_Boundary_Level"（L54）。本反查 check 直接插在该行**之前**即可；P3 step 1 已加载 `{workflow_status}`，反查无需额外读文件动作。

**新文**（在 `step n="4"` 内、第一个 `<action>读取 {issue_card} 中的 Issue_Boundary_Level...</action>` 之前插入）：

```xml
        <!-- v4.2 PR-2 / O7 方案 B（READ-N1 / ADR-007 v4.2 修订段落）：
             P3 重入读端补齐 — 删除 rca_fanout_mode_snapshot 后，从 phase_history 反查还原。
             触发条件：fanout_mode 缺失或 null，且 phase_history 非空。
             首次进入 P3（phase_history 为空）时本逻辑跳过，由下方 spec 推断路径正常工作。 -->
        <check if="{workflow_status}.fanout_mode == null 且 {workflow_status}.phase_history 非空">
            <action>从 {workflow_status}.phase_history 末尾反向遍历，找到第一条 phase == "qa-root-cause" 的元素，取其 fanout_mode 字段写回 {workflow_status}.fanout_mode；若反向遍历完仍未命中（极端 case：phase_history 不含 qa-root-cause 元素），则保持 fanout_mode = null，由下方 spec 推断路径接管。</action>
        </check>
```

**修订理由**：
- 反查逻辑用 LLM 可执行的自然语言（与 P3 现有 `<action>` 风格一致），不引入 python/bash 依赖。
- 仅在 `fanout_mode == null` 时触发，新会话主路径**完全不受影响**；P3 → P4 → P3 重入时若 P4 误清了 `fanout_mode`（C10 历史 bug），由本逻辑兜底还原。
- 与 step 10 写端（`phase_history.append` 在 stop 路径强制重写之前执行）形成完整闭环：写端记录 fanout_mode 自然取值 → 读端反查恢复。

**兼容性影响**：
- **新会话**：首次 P3 时 `phase_history = []`，本 check 不命中；后续 P3 重入时若 fanout_mode 已被正常 spec 推断/写入，本 check 也不命中。仅在边缘 case（fanout_mode 被外部清空或 PR-2 删 snapshot 后的"老 v4 会话清理后首次重入"）触发还原。
- **存量会话**：跑过 `--cleanup-v4-deprecated` 的 v4 会话若处于"P3 → P4 → P3 重入中且 fanout_mode 缺失"状态，本逻辑可平滑还原，不需要人工干预。
- **风险**：反查取"末项 qa-root-cause" — 与 PR-1 写端契约（每次 P3 完成 append 一条）一致；若历史会话 phase_history 元素结构异常（缺 fanout_mode 字段），LLM 应识别为"无法还原"分支并继续走 spec 推断路径。READ-N1 的 LLM 描述应在 reviewer 端通过单 prompt 抽 1 用例验证。

---

#### 2.3.3 变更点 READ-N2 · 编排器 step 2 读字段列表追加 `phase_history`（v1.1 新增 / READ-N1 联动 / v1.2 落点修订）

> **v1.2 修订说明**：
> ① 落点更正 — 编排器读 `{workflow_status}` 字段列表的 `<action>` 位于 step 2（L28），不是 step 1（step 1 仅做 `<load core-rules.xml>`）；
> ② 必要性弱化 — P3 在自身 step 1（L34）已读取整个 `{workflow_status}`，可直接读到 `phase_history` 字段；本变更点的真实价值是**编排器 / Limited 平台层的显式字段声明**（让 Limited 平台在 prompt 注入阶段把 `phase_history` 一并注入，不依赖隐式整文件读取），**不是** P3 内部读 `phase_history` 的前提。

**操作**：在 `core/workflow.xml` step 2 读字段列表（即 REF-D1 已改名的同一行）末尾追加 `phase_history`（与已有 `fanout_mode`、`fix_fanout_mode` 等并列），让编排器在后续 step 3 case 路由前已显式声明该字段。

**原文（行号锚点 L28，与 REF-D1 同行；本变更点在 REF-D1 改完之后再追加 `phase_history`）**：

```xml
                <action>读取 {workflow_status} 文件，获取 stepsCompleted、current_state、workflow_version、schema_version、analysis_complexity、fanout_mode、fix_fanout_mode、reroute_target_phase、rca_retry_count、fix_retry_count</action>
```

**新文**（在末尾追加 `phase_history`）：

```xml
                <action>读取 {workflow_status} 文件，获取 stepsCompleted、current_state、workflow_version、schema_version、analysis_complexity、fanout_mode、fix_fanout_mode、reroute_target_phase、rca_retry_count、fix_retry_count、phase_history</action>
```

**修订理由**：
- 编排器层显式声明 `phase_history`，方便 Limited 平台 prompt 注入器把该字段当作"路由相关字段"一并送入；同时让 reviewer 在编排器侧一眼可见 P3 反查所依赖的字段已被声明。
- v3 兼容默认值无需追加（v3 无 phase_history 字段，迁移脚本注入 `[]`，编排器读到空数组即可，不影响主路径）。
- **不是 READ-N1 的硬前提** — 即使本变更点未落地，P3 step 1 整文件读 `{workflow_status}` 的语义已足以让 step 4 反查到 `phase_history`；本变更点是协议清晰度增强，不是功能补缺。

**兼容性影响**：
- 主路径：仅扩展读字段列表，没有路由分支变更。
- v3 兼容路径：迁移脚本已在 `NEW_FIELDS_DEFAULTS` 注入 `("phase_history", CommentedSeq())`，本 step 2 读到 `[]` 与新会话首次状态一致。

---

### 2.4 文件 D · `phases/p4-fix-design.md`（O8 引用扫净 / REF-D3 + REF-D4）

#### 2.4.1 变更点 REF-D3 · step 2 删除 `fix_strategy_mode` 写入行（保留 `fix_fanout_mode`）

**原文（行号锚点 L46-51）**：

```46:51:mobile-qa-workflow/phases/p4-fix-design.md
            <action>更新 {workflow_status}：
                - fix_risk_level = {fix_risk_level}
                - fix_strategy_mode = {fix_strategy_mode}
                - fix_fanout_mode = {fix_strategy_mode}
                - reroute_reason = null
            </action>
```

**新文**（删除 `fix_strategy_mode = {fix_strategy_mode}` 一行；`{fix_strategy_mode}` 模板变量保留为 step 2 输出的临时变量名 — 它仍然是 LLM 推理时的局部变量，只是不再写回 schema）：

```xml
            <action>更新 {workflow_status}：
                - fix_risk_level = {fix_risk_level}
                - fix_fanout_mode = {fix_strategy_mode}
                - reroute_reason = null
            </action>
```

**修订理由**：
- TPL-S2 删除 schema 字段后，写入点必须同步删除。
- step 2 上方 `<action>` 输出 `fix_strategy_mode = single-proposer | challenged-proposer | contested-arbitrated` **保留不动** —— 它是 LLM 局部决策变量，只是不再持久化到 schema；`fix_fanout_mode = {fix_strategy_mode}` 的模板插值保留，承接局部变量值。

**兼容性影响**：本 phase 写入端从两字段双写变为单字段写；下游 P5/P6 读端只读 `fix_fanout_mode`，行为等价。

---

#### 2.4.2 变更点 REF-D4 · step 3 升级路径 `fix_strategy_mode = contested-arbitrated` 改为 `fix_fanout_mode = contested-arbitrated`

**原文（行号锚点 L90）**：

```90:90:mobile-qa-workflow/phases/p4-fix-design.md
                    <action>更新 {workflow_status}：fix_strategy_mode = contested-arbitrated, fix_fanout_mode = contested-arbitrated, reroute_reason = challenged_fix_escalated</action>
```

**新文**（删除 `fix_strategy_mode = contested-arbitrated, ` 前缀，仅保留 `fix_fanout_mode = ...`）：

```xml
                    <action>更新 {workflow_status}：fix_fanout_mode = contested-arbitrated, reroute_reason = challenged_fix_escalated</action>
```

**修订理由**：与 REF-D3 同款收敛；step 3 升级路径写入逻辑不变，只是不再写废弃字段。

**兼容性影响**：升级到 `contested-arbitrated` 后 `goto step="3"`，由 step 3 的 `<check if="fix_fanout_mode == contested-arbitrated">` 分支接管 ——

⚠️ **联动校验**：`p4-fix-design.md` step 3 下方现有 `<check if="fix_strategy_mode == contested-arbitrated">` / `<check if="fix_strategy_mode == challenged-proposer">` / `<check if="fix_strategy_mode == single-proposer">` **共 3 个分支判断条件**仍然引用 `fix_strategy_mode`。这些是 LLM 局部变量级判断（step 2 内部输出的临时变量名），与 schema 字段无关；**不需要在本 PR 改写**。但 reviewer 必须确认：grep `fix_strategy_mode` 在 `p4-fix-design.md` 内剩余命中点全部位于 `<check if=...>` 分支或 `{fix_strategy_mode}` 模板变量，**不应再有 `<action>更新 {workflow_status}: fix_strategy_mode = ...>` 形式的写入**。

---

### 2.5 文件 E · `system-prompt.md`（仅允许 REF-D5 + ANCHOR-N1 两类改动 / v1.2 范围描述修订）

> **重要约束**（H1 守门 + V1.1 §4.1.0 H1 / v1.2 范围澄清）：本 PR **只允许**对 `system-prompt.md` 做 **REF-D5 + ANCHOR-N1** 两类改动，**禁止任何第三类改动**：
> - **REF-D5（O7/O8 引用扫净）** = 字段表删除 `rca_fanout_mode_snapshot` 行（O7） + 把"workflow-status 字段写回描述"中的 `fix_strategy_mode` 改为 `fix_fanout_mode`（O8）；保留 LLM 局部决策变量（"输出 X = …"类描述）中的 `fix_strategy_mode` 不动（详见 REF-D5 联动校验段）。
> - **ANCHOR-N1（H1 稳定锚点）** = 在 Spec-Uncertain 段（含 `allowed_values=1|2|S` 的位置）前插入 1 行 `<!-- ANCHOR: spec-uncertain-allowed-values -->` 注释，供 SCRIPT-FIX1 / CI-N1 锚点提取使用（详见 §2.10.3 ANCHOR-N1）。
>
> **特别强约束**：Spec-Uncertain 段落 `allowed_values=1|2|S` **必须保持不变**（PR-4 O13a 才统一）；任何对 `system-prompt.md` 的改动若不属于上述两类、或行变动数 > 3，必须显式批准。CI 守门 `check-build-system-prompt-precondition.sh`（CI-N1）兜底防止 `allowed_values` 漂移。
>
> **v1.2 修订说明**：v1.0/v1.1 §2.5 标题/约束写"只允许 O7/O8 字段名替换 + 不允许任何其他改动"，与 v1.1 后文新增的 ANCHOR-N1 + DoD §3.1 中"行变动数 ≤ 3（删 1 改 1 加 1）"硬上限自相矛盾。本节统一更正为"仅允许 REF-D5 + ANCHOR-N1 两类"。

#### 2.5.1 变更点 REF-D5 · 字段表 + LLM 描述行批量改名

**原文（行号锚点 L157-158 + L355 + L358）**：

```157:158:mobile-qa-workflow/system-prompt.md
| `fix_fanout_mode` | `null` | P4 修复路由模式（C10 字段隔离） | 与 RCA 字段 `fanout_mode` 物理隔离 |
| `rca_fanout_mode_snapshot` | `null` | P3 完成时 `fanout_mode` 的快照 | C10 兼容性方案 B 兜底 |
```

```355:358:mobile-qa-workflow/system-prompt.md
        <action>输出 `fix_risk_level = low | medium | high` 与 `fix_strategy_mode = single-proposer | challenged-proposer | contested-arbitrated`。</action>
        ...
        <action>将 `fix_strategy_mode`、`fix_risk_level`、必要的 `reroute_reason` 回写到 workflow-status。</action>
```

**新文**：

L157-158（删除 `rca_fanout_mode_snapshot` 行；保留 `fix_fanout_mode` 行不动）：

```markdown
| `fix_fanout_mode` | `null` | P4 修复路由模式（C10 字段隔离） | 与 RCA 字段 `fanout_mode` 物理隔离 |
```

L355（保留 `fix_strategy_mode` 作为 LLM 局部决策变量描述，不动 — 与 REF-D3/D4 联动校验一致）：

```xml
        <action>输出 `fix_risk_level = low | medium | high` 与 `fix_strategy_mode = single-proposer | challenged-proposer | contested-arbitrated`。</action>
```

L358（仅 `fix_strategy_mode` 改为 `fix_fanout_mode`；`fix_risk_level` / `reroute_reason` 不动）：

```xml
        <action>将 `fix_fanout_mode`、`fix_risk_level`、必要的 `reroute_reason` 回写到 workflow-status。</action>
```

**修订理由**：与 TPL-S1/S2 + REF-D2/D3/D4 同款收敛；保持 system-prompt.md 与 core/ 同步。

**兼容性影响**：
- Limited 平台读 system-prompt.md 时不会再看到已删除字段的描述；行为与 Full 平台对齐。
- L355 保留 LLM 局部变量描述（"输出 X = ..."），与 phase 文件 step 2 的 `<action>` 输出语义一致；reviewer 必须确认 `fix_strategy_mode` 在 system-prompt.md 内剩余命中只出现在"LLM 输出局部变量"类描述，不出现在"workflow-status 字段"类描述。

---

### 2.6 文件 F · `SKILL.md` + `PLATFORM-GUIDE.md`（O7 / O8 引用扫净 / REF-D6 + REF-D7）

#### 2.6.1 变更点 REF-D6 · `SKILL.md` 字段表收敛

**原文（行号锚点 L29-30）**：

```29:30:mobile-qa-workflow/SKILL.md
| `fix_fanout_mode` | `null` | P4 修复路由模式（C10 字段隔离，承接 `single-proposer` / `challenged-proposer` / `contested-arbitrated`），与 RCA 字段 `fanout_mode` 物理隔离 | v4.1 |
| `rca_fanout_mode_snapshot` | `null` | P3 完成时 `fanout_mode` 的快照，用于 P3 重入时还原 RCA 上下文（C10 兼容性方案 B 兜底） | v4.1 |
```

**新文**（删除 `rca_fanout_mode_snapshot` 行；`fix_fanout_mode` 行的"承接"描述追加 v4.2 修订标注）：

```markdown
| `fix_fanout_mode` | `null` | P4 修复路由模式（C10 字段隔离，承接 `single-proposer` / `challenged-proposer` / `contested-arbitrated`），与 RCA 字段 `fanout_mode` 物理隔离 | v4.1 / v4.2 PR-2 收敛 `fix_strategy_mode` |
```

**修订理由**：保持 SKILL.md 字段表与 schema 同步；删除冗余字段说明，合并同义字段说明。

---

#### 2.6.2 变更点 REF-D7 · `PLATFORM-GUIDE.md` 引用清理

**原文（行号锚点 L25 + L55-56）**：

```25:25:mobile-qa-workflow/PLATFORM-GUIDE.md
- `workflow-status.yaml` 是动态路由唯一可信状态源；`analysis_complexity`、`fanout_mode`、`fix_fanout_mode`、`fix_strategy_mode`、`reroute_target_phase`、重试计数、`phase_history`、`user_inputs`、`non_bug_context`、`parse_error_count`、`rca_fanout_mode_snapshot` 等字段由阶段文件写回，由主编排器读取并执行。
```

```55:56:mobile-qa-workflow/PLATFORM-GUIDE.md
  - **路由与计数**：`analysis_complexity`、`analysis_complexity_confidence`、`fanout_mode`、`fix_fanout_mode`、`fix_strategy_mode`、`fix_risk_level`、`reroute_target_phase`、`reroute_reason`、`rca_retry_count`、`fix_retry_count`、`non_bug_reflow_count`、`lint_retry_count`
  - **历史与快照**：`phase_history`（结构：`{phase, timestamp, fanout_mode, note?}`）、`rca_fanout_mode_snapshot`（P3 完成时 `fanout_mode` 快照，C10 兼容性方案 B 兜底）
```

**新文**：

L25（删除 `fix_strategy_mode、` 与 `、rca_fanout_mode_snapshot`）：

```markdown
- `workflow-status.yaml` 是动态路由唯一可信状态源；`analysis_complexity`、`fanout_mode`、`fix_fanout_mode`、`reroute_target_phase`、重试计数、`phase_history`、`user_inputs`、`non_bug_context`、`parse_error_count` 等字段由阶段文件写回，由主编排器读取并执行。
```

L55-56（删除 `fix_strategy_mode、` 与整行"历史与快照"中 `rca_fanout_mode_snapshot` 描述；保留 `phase_history` 描述）：

```markdown
  - **路由与计数**：`analysis_complexity`、`analysis_complexity_confidence`、`fanout_mode`、`fix_fanout_mode`、`fix_risk_level`、`reroute_target_phase`、`reroute_reason`、`rca_retry_count`、`fix_retry_count`、`non_bug_reflow_count`、`lint_retry_count`
  - **历史**：`phase_history`（结构：`{phase, timestamp, fanout_mode, note?}`，P3 写入端在每次 phase 完成时 append；P3 重入时反查最近一条 `qa-root-cause` 元素的 `fanout_mode` 还原）
```

**修订理由**：保持接入方文档与 schema 同步。

---

### 2.7 文件 G · `scripts/migrate-workflow-status-v3-to-v4.py`（v4 内部清理增强 / MIG-N1）

#### 2.7.1 变更点 MIG-N1 · 增加 `--cleanup-v4-deprecated` 子命令 + 主路径同步删除冗余字段注入

**操作**（两段改动组合，**不**改 v3→v4 主路径数据迁移逻辑）：

**改动 1：主路径 `NEW_FIELDS_DEFAULTS` 列表删除两条已废弃字段**

**原文（行号锚点 L49-57）**：

```49:57:mobile-qa-workflow/scripts/migrate-workflow-status-v3-to-v4.py
NEW_FIELDS_DEFAULTS: list[tuple[str, object]] = [
    ("fix_fanout_mode", None),
    ("rca_fanout_mode_snapshot", None),
    ("phase_history", CommentedSeq()),
    ("user_inputs", CommentedMap()),
    ("non_bug_context", None),
    ("parse_error_count", 0),
    ("non_bug_user_choice", None),
]
```

**新文**（删除 `("rca_fanout_mode_snapshot", None),` 一行；保留其余 6 条；同步更新文件头 docstring 的注入清单）：

```python
NEW_FIELDS_DEFAULTS: list[tuple[str, object]] = [
    ("fix_fanout_mode", None),
    ("phase_history", CommentedSeq()),
    ("user_inputs", CommentedMap()),
    ("non_bug_context", None),
    ("parse_error_count", 0),
    ("non_bug_user_choice", None),
]
# v4.2 PR-2 修订（O7 / ADR-007 v4.2 修订段落）：
# 已废弃字段不再注入：rca_fanout_mode_snapshot（删除）/ fix_strategy_mode（合并到 fix_fanout_mode）。
# 存量会话清理：使用 `--cleanup-v4-deprecated` 子命令幂等处理。
```

**改动 2：新增 `cleanup_v4_deprecated()` 函数 + CLI `--cleanup-v4-deprecated` flag**

```python
DEPRECATED_FIELDS_V4_2: list[str] = [
    "rca_fanout_mode_snapshot",
    "fix_strategy_mode",
]


def cleanup_v4_deprecated(doc: CommentedMap) -> dict:
    """v4 内部清理：幂等地把存量会话的 fix_strategy_mode 拷贝到 fix_fanout_mode（若后者为 null）+
    删除 rca_fanout_mode_snapshot 与 fix_strategy_mode 两个已废弃字段。

    返回操作摘要 dict，供 CLI 输出。
    """
    summary = {"copied_fix_mode": False, "removed_fields": []}

    # 1) 拷值优先：仅当 fix_fanout_mode 缺失/null 且 fix_strategy_mode 有值时拷贝
    if doc.get("fix_strategy_mode") is not None and not doc.get("fix_fanout_mode"):
        doc["fix_fanout_mode"] = doc["fix_strategy_mode"]
        summary["copied_fix_mode"] = True

    # 2) 删除两个已废弃字段（幂等：不存在则跳过）
    for field in DEPRECATED_FIELDS_V4_2:
        if field in doc:
            del doc[field]
            summary["removed_fields"].append(field)

    return summary


# CLI 集成（在 main() 中追加 --cleanup-v4-deprecated 互斥子命令）：
parser.add_argument(
    "--cleanup-v4-deprecated",
    action="store_true",
    help="对存量 v4 会话做 v4.2 PR-2 字段清理（拷值 fix_strategy_mode→fix_fanout_mode + 删除 rca_fanout_mode_snapshot/fix_strategy_mode），与主路径迁移互斥",
)
```

**修订理由**：
- 主路径修改保证新会话不再注入冗余字段。
- 子命令保证存量会话可平滑清理；幂等可重复执行（已清理过再跑无副作用）。
- 文件头 docstring 同步注明 v4.2 修订；ADR-013（迁移脚本路径锁定）不受影响。

**兼容性影响**：
- `--cleanup-v4-deprecated` 子命令与现有 `--dry-run` / `--no-strict` 兼容。
- 不引入 `schema_version` bump（保持 4 不变；本次清理属"v4 内部 schema 收敛"，与 PR-1 ADR-013 锁定的脚本路径一致）。

---

### 2.8 文件 H · ADR 同步（ADR-D1 + ADR-IDX1）

#### 2.8.1 变更点 ADR-D1 · `doc/adr/007-fanout-mode-no-rename.md` 追加 v4.2 修订段落

**操作**：在现有 ADR-007 文件末尾追加（不动现有正文）：

```markdown

---

## v4.2 PR-2 修订（2026-04-21）

**修订背景**：V1.1 §3.2.7 / §3.2.8 识别出 `rca_fanout_mode_snapshot` 与 `fix_strategy_mode` 是冗余字段：
- `rca_fanout_mode_snapshot`：方案 A（`phase_history` 反查）已是主路径，snapshot 字段是 C10 兼容性方案 B 兜底；PR-1 PR-4 P3 写入端落地后 `phase_history` 永远非空，snapshot 是纯冗余。
- `fix_strategy_mode`：与 `fix_fanout_mode` 同义（P4 step 2 内 `fix_fanout_mode = {fix_strategy_mode}` 同值赋两次）。

**修订决定**：
- **删除** `rca_fanout_mode_snapshot` schema 字段；P3 重入还原仅依赖 `phase_history` 反查。
- **合并** `fix_strategy_mode` → `fix_fanout_mode`（保留 `fix_fanout_mode` 命名，与 `fanout_mode` 命名对称）。
- **保留** D7 原决定不变：`fanout_mode` 字段名继续作 RCA 字段，**不重命名**为 `rca_fanout_mode`；DoD 反向校验"裸 `rca_fanout_mode` 必须打回"继续生效。
- **同步落地 P3 重入读端**（v1.1 review Blocking 1 修订 / O7 方案 B / v1.2 落点修订）：在 `phases/p3-root-cause.md` step 4 第一个边界策略动作之前追加"若 `fanout_mode` 缺失/null 则反查 `phase_history` 末项 `qa-root-cause` 元素的 `fanout_mode` 还原"逻辑，并在 `core/workflow.xml` **step 2** 读字段列表追加 `phase_history`（编排器层显式声明，方便 Limited 平台 prompt 注入器同步注入）；snapshot 字段删除后由本读端独立支撑 P3 重入兼容（旧 C10 兼容性方案 B 不再需要）。

**存量兼容**：v4.2 PR-2 同步交付 `migrate-workflow-status-v3-to-v4.py --cleanup-v4-deprecated` 子命令，幂等地拷值 + 删除两个废弃字段；同时迁移脚本文件头 docstring 删除"不实施 fanout_mode 反查还原逻辑"一句（该断言被 v4.2 PR-2 的 P3 step 4 反查读端取代）。

**关联 PR**：v4.2 PR-2（落地）；后续 PR-3/4/5/6/7 不再涉及这两个字段。
```

#### 2.8.2 变更点 ADR-IDX1 · `doc/adr/000-index.md` ADR-007 行追加备注

**操作**：在 ADR-007 行尾"落地 PR"列追加" + v4.2 PR-2 修订"。

**新文**（仅 ADR-007 行替换；其余行不动）：

```markdown
| [ADR-007](./007-fanout-mode-no-rename.md) | 保留 `fanout_mode` 不重命名 + 新增 `fix_fanout_mode` | active | D7 | v4.1 PR-1（已合入）+ v4.2 PR-2 修订 |
```

**修订理由 / 兼容性影响**：保持 ADR 索引追溯链完整；不影响运行时。

---

### 2.9 文件 I · `scripts/build-system-prompt.py` + 单测（O17+ Stage 1 / GEN-N1 ~ GEN-N3）

> **重要约束**（H1 + V1.1 §3.3.17 Stage 2 / §4.1.0 H1）：本 PR **只交付**生成器脚本 + 单测；**不**首次构建并替换 `system-prompt.md`。首次构建延迟到 PR-6（O13a 合入后），由 PR-6 触发 `python build-system-prompt.py --mode=full --output system-prompt.md` 并人工 diff 验证。
>
> **v1.1 写死口径**（review Major 3 修订）：本 PR 交付的是生成器**最小完整实现**，不是骨架。验收硬约束：
> - 5 个 builder（L0-L4）**全部可跑**，**禁止** NotImplementedError stub
> - 三种 mode（full / layered / verify）**全部可跑**
> - DoD §3.1 含 `python build-system-prompt.py --mode=verify` 退出 0、`--mode=layered --output-dir=/tmp/...` 输出 5 个 L\*.md 两条硬验收
> - 实施者发现某 builder 无法在分配的 0.5d / builder 内完成 → 必须升级评审，不允许私自降级为 stub（详见 reviewer 议题 #3）

#### 2.9.1 变更点 GEN-N1 · `scripts/build-system-prompt.py` 生成器最小完整实现

**新文件内容**（约 ~250 行 python；下方代码为骨架示例，**完整实现**以本 PR 落地代码为准 — 5 个 builder 必须替换 `# ...` 占位为可跑实现）：

```python
#!/usr/bin/env python3
"""build-system-prompt.py (v4.2 PR-2 / O17+ Stage 1)

从 core/ 各文件 + phases/ + agents/ 自动构建 system-prompt.md，输出 L0-L4 分层产物。

目标产物结构（与 V1.1 §3.3.17 Stage 2 表对齐）：
  L0: 核心身份（~30 行）— 角色定义 + 6 阶段序列 + 状态机转换图
  L1: 执行规则（~50 行）— 步骤顺序 + ABORT 协议 + step-pause 输入规范 + step-pause-registry 路由表（PR-5 后接入）
  L2: 当前阶段逻辑（~80 行）— 按 current_state 动态展开（决策树式，删除步骤式叙述）
  L3: 推理工具箱（~60 行）— OVHSC 五步 + 置信度公式 + 证据权重表 + Challenger 7 维 + Arbiter 公式
  L4: 平台知识（~40 行）— 分类策略引导（按命中分类注入）

输出策略：
  - --mode=full        生成 Limited 平台单 prompt 模式产物（L0+L1+L2 全量+L3+L4 全量）
  - --mode=layered     生成 5 个独立片段文件（L0.md / L1.md / ...），供支持多轮注入的平台
  - --mode=verify      仅校验 core/ 关键 token 一致性，不输出文件（用于 CI sync 守门）

用法：
  python build-system-prompt.py --mode=full --output=system-prompt.md
  python build-system-prompt.py --mode=layered --output-dir=build/system-prompt-layered/
  python build-system-prompt.py --mode=verify

⚠️ v4.2 PR-2 阶段：本脚本只交付，禁止运行 --mode=full 替换 system-prompt.md
   （H1 守门：见 check-build-system-prompt-precondition.sh）。
   首次构建并替换在 PR-6 内执行（依赖 PR-4 O13a 已合入）。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

try:
    from ruamel.yaml import YAML
except ImportError:
    sys.stderr.write("error: requires ruamel.yaml >= 0.17\n")
    sys.exit(2)


# ---- 各 L 层 builder ----

def build_l0_identity(repo_root: Path) -> str:
    """L0 核心身份：从 SKILL.md + workflow-model.yaml 提取角色定义 + 6 阶段序列 + 状态机转换图。"""
    skill_md = (repo_root / "mobile-qa-workflow" / "SKILL.md").read_text()
    model_yaml = YAML(typ="safe").load((repo_root / "mobile-qa-workflow" / "core" / "workflow-model.yaml").read_text())
    # ...（提取角色定义首段 + 阶段序列）
    return _render_l0_template(skill_md, model_yaml)


def build_l1_execution_rules(repo_root: Path) -> str:
    """L1 执行规则：从 core-rules.xml 提取 <WORKFLOW-RULES> + <workflow-result-protocol> + <input-protocol>。
    PR-5 合入后追加 step-pause-registry.yaml 内容渲染为路由表。
    """
    core_rules = (repo_root / "mobile-qa-workflow" / "core" / "core-rules.xml").read_text()
    # ...（XML parse + 提取关键块）
    return _render_l1_template(core_rules)


def build_l2_phase_logic(repo_root: Path, phase: Optional[str] = None) -> str:
    """L2 当前阶段逻辑：按 phase 名提取 phases/p{N}-*.md 关键决策树。
    - phase=None → 全量 6 阶段（Limited 单 prompt 模式）
    - phase=qa-root-cause → 仅 P3 + 前后 1 阶段（多轮注入模式）
    """
    # ...（按 phase 名定位文件 + 提取决策骨架）


def build_l3_reasoning_toolbox(repo_root: Path) -> str:
    """L3 推理工具箱：从 reference/reasoning-chain.md 提取 OVHSC + 公式
    （PR-7 拆分后改为读 reasoning-chain-core.md）。"""
    # ...


def build_l4_platform_knowledge(repo_root: Path, category: Optional[str] = None) -> str:
    """L4 平台知识：从 reference/platform-checklist.md 按命中分类注入。"""
    # ...


# ---- 一致性 verify 模式（CI 用） ----

def verify_core_consistency(repo_root: Path) -> list[str]:
    """校验 core/ 文件内 enum 集 + step-pause 协议关键 token 自洽，返回 issue 列表（空 = 通过）。"""
    issues = []
    enum_template = _extract_enum(repo_root / "mobile-qa-workflow" / "core" / "workflow-status-template.yaml")
    enum_workflow = _extract_state_writes(repo_root / "mobile-qa-workflow" / "core" / "workflow.xml")
    illegal = enum_workflow - enum_template
    if illegal:
        issues.append(f"workflow.xml 写入了不在 template enum 集内的 state: {sorted(illegal)}")
    # ...（其他 sync 校验）
    return issues


# ---- main ----

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["full", "layered", "verify"], default="verify")
    parser.add_argument("--output", type=Path, default=None, help="--mode=full 时的输出文件")
    parser.add_argument("--output-dir", type=Path, default=None, help="--mode=layered 时的输出目录")
    parser.add_argument("--phase", default=None, help="--mode=full/layered 时指定 phase（默认全量）")
    parser.add_argument("--category", default=None, help="L4 命中分类（functional/ui/network/compat）")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]

    if args.mode == "verify":
        issues = verify_core_consistency(repo_root)
        if issues:
            for issue in issues:
                print(f"::error::{issue}", file=sys.stderr)
            sys.exit(1)
        print("✅ build-system-prompt.py --mode=verify 通过")
        return

    if args.mode == "full":
        if args.output is None:
            sys.stderr.write("error: --mode=full 需要 --output\n"); sys.exit(2)
        # ⚠️ v4.2 PR-2 阶段：禁止运行 --mode=full 替换 system-prompt.md（H1 守门）
        # 由 CI check-build-system-prompt-precondition.sh 兜底防止误用；
        # PR-6 触发首次构建时通过环境变量 ALLOW_FIRST_BUILD=1 解锁
        import os
        if os.environ.get("ALLOW_FIRST_BUILD") != "1" and args.output.name == "system-prompt.md":
            sys.stderr.write(
                "error: v4.2 PR-2 阶段禁止 --mode=full 输出到 system-prompt.md；"
                "首次构建由 PR-6 触发（设置 ALLOW_FIRST_BUILD=1 解锁）\n"
            )
            sys.exit(3)
        full_content = "\n\n".join([
            build_l0_identity(repo_root),
            build_l1_execution_rules(repo_root),
            build_l2_phase_logic(repo_root, args.phase),
            build_l3_reasoning_toolbox(repo_root),
            build_l4_platform_knowledge(repo_root, args.category),
        ])
        args.output.write_text(full_content)
        print(f"✅ 写入 {args.output} ({len(full_content.splitlines())} 行)")
        return

    if args.mode == "layered":
        if args.output_dir is None:
            sys.stderr.write("error: --mode=layered 需要 --output-dir\n"); sys.exit(2)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        layers = {
            "L0-identity.md": build_l0_identity(repo_root),
            "L1-execution-rules.md": build_l1_execution_rules(repo_root),
            "L2-phase-logic.md": build_l2_phase_logic(repo_root, args.phase),
            "L3-reasoning-toolbox.md": build_l3_reasoning_toolbox(repo_root),
            "L4-platform-knowledge.md": build_l4_platform_knowledge(repo_root, args.category),
        }
        for name, content in layers.items():
            (args.output_dir / name).write_text(content)
        print(f"✅ 写入 {args.output_dir} (5 个分层文件)")


if __name__ == "__main__":
    main()
```

**修订理由**：
- V1.1 §3.3.17 Stage 1 + Stage 2：L0-L4 分层产物 + 三种输出模式（full / layered / verify）。
- `--mode=verify` 模式不产生输出文件，仅校验 core/ 一致性，可被 CI sync 守门复用（与 `check-system-prompt-sync.sh` 互补）。
- **禁止替换 system-prompt.md 的硬约束**通过双重兜底：① 脚本内 `ALLOW_FIRST_BUILD` 环境变量门 + 文件名守门；② CI `check-build-system-prompt-precondition.sh`（CI-N1）兜底。

**兼容性影响**：
- 仅交付脚本 + 单测，不替换 `system-prompt.md`；本 PR 合入后 main 上 `system-prompt.md` 与 PR-1 合入态完全一致（除本 PR 内 REF-D5 改动）。
- 依赖 `ruamel.yaml` 已在 `scripts/requirements.txt`（PR-1 已声明），不引入新 pip 依赖。

---

#### 2.9.2 变更点 GEN-N2 · `scripts/tests/test_build_system_prompt.py` 单元测试

**新文件内容**（约 ~150 行 python，覆盖 L0-L4 各 builder 与 verify 模式）：

```python
#!/usr/bin/env python3
"""test_build_system_prompt.py — build-system-prompt.py 单元测试

覆盖：
  - L0-L4 各 builder 输出格式断言（包含关键 token / 行数预算）
  - verify 模式：注入故意漂移（如 phases/ 内写入非法 state）后必须报错
  - --mode=full 在 ALLOW_FIRST_BUILD 未设置 + 输出 system-prompt.md 时必须退出 3
  - --mode=layered 输出 5 个分层文件且总行数 ≤ Limited 单 prompt 模式
"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "mobile-qa-workflow" / "scripts" / "build-system-prompt.py"


class TestVerifyMode(unittest.TestCase):
    def test_verify_passes_on_clean_main(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "--mode=verify"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, msg=f"stderr: {result.stderr}")

    def test_verify_fails_on_injected_drift(self):
        # （在临时副本中故意注入 illegal state，断言 verify 报错）
        ...


class TestFullMode(unittest.TestCase):
    def test_full_mode_blocked_when_targeting_system_prompt(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "system-prompt.md"
            env = os.environ.copy()
            env.pop("ALLOW_FIRST_BUILD", None)
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--mode=full", "--output", str(target)],
                capture_output=True, text=True, env=env,
            )
            self.assertEqual(result.returncode, 3, msg=f"stderr: {result.stderr}")
            self.assertIn("禁止", result.stderr)

    def test_full_mode_allowed_with_env_flag(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "system-prompt.md"
            env = os.environ.copy()
            env["ALLOW_FIRST_BUILD"] = "1"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--mode=full", "--output", str(target)],
                capture_output=True, text=True, env=env,
            )
            self.assertEqual(result.returncode, 0)
            self.assertTrue(target.exists())
            self.assertGreater(len(target.read_text().splitlines()), 100)

    def test_full_mode_allowed_for_other_filename(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "preview.md"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--mode=full", "--output", str(target)],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0)


class TestLayeredMode(unittest.TestCase):
    def test_layered_outputs_5_files(self):
        with tempfile.TemporaryDirectory() as td:
            outdir = Path(td) / "layered"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--mode=layered", "--output-dir", str(outdir)],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, msg=f"stderr: {result.stderr}")
            files = sorted(p.name for p in outdir.iterdir())
            self.assertEqual(files, ["L0-identity.md", "L1-execution-rules.md", "L2-phase-logic.md", "L3-reasoning-toolbox.md", "L4-platform-knowledge.md"])


class TestLayerBuilders(unittest.TestCase):
    def test_l0_contains_six_phase_sequence(self):
        ...  # 断言 L0 输出含 6 阶段序列

    def test_l1_contains_step_pause_protocol(self):
        ...  # 断言 L1 输出含 step-pause [result_field=...] / [allowed_values=...] 协议描述

    def test_l3_preserves_ovhsc_full(self):
        ...  # 断言 L3 输出含 OVHSC 五步 + 置信度公式（V1 §6 第 1 条不可触动）


if __name__ == "__main__":
    unittest.main()
```

**修订理由**：
- 关键 case：`test_full_mode_blocked_when_targeting_system_prompt` 直接验证 H1 守门（PR-2 阶段禁止替换）。
- L3 OVHSC 保留校验对应 V1.1 §6 第 14 条"OVHSC 推理工具箱完整保留"硬约束。

**兼容性影响**：unittest 标准库，不引入新依赖；在 CI 中 `python -m unittest discover mobile-qa-workflow/scripts/tests/` 即可跑全。

---

#### 2.9.3 变更点 GEN-N3 · `scripts/tests/__init__.py` + `scripts/tests/fixtures/` 占位

**操作**：新建 `mobile-qa-workflow/scripts/tests/__init__.py`（空文件，用于 unittest discover）+ `mobile-qa-workflow/scripts/tests/fixtures/.gitkeep`（用于 verify 模式注入漂移的临时 fixture 占位）。

**修订理由**：标准 python unittest 项目结构；fixtures 目录为后续 PR-6 首次构建产物 diff baseline 留位。

---

### 2.10 文件 J · CI 升级 + 新增（v1.1 修订：SCRIPT-FIX1 + CI-U1b + ANCHOR-N1/N2 + CI-N1 + TEST-N1 + CI-W1；~~CI-U2 已删除~~）

#### 2.10.1 变更点 SCRIPT-FIX1 · `check-system-prompt-sync.sh` 提取器修复（v1.1 新增 / O5 拆分第一步）

> **背景**：v1.1 review Blocking 2 — 当前主干干净工作树实跑 `bash mobile-qa-workflow/scripts/check-system-prompt-sync.sh` 仍输出 2 条 warning：① `ENUM-DECLARATION-BLOCK 与 core/workflow-status-template.yaml 头部 enum 集不一致` — `core 独有: FORMAT PLATFORM-GUIDE PR- PRESERVE SKILL`；② `Spec-Uncertain allowed_values 字面不一致`（命中的不是目标段）。两者都是 PR-1 v1.1 脚本提取器自身缺陷，必须先修才能升 error。

**操作**：把 PR-1 v1.1 脚本中两处脆弱提取改为严格提取 —— **两段改动**：

**改动 1：ENUM_CORE 严格抽取**（脚本 L18-19，原 awk 范围式 + 宽松 PascalCase 抓取）

**原文**：
```bash
ENUM_CORE=$(awk '/v4.1 完整集合/,/^[^#]/' core/workflow-status-template.yaml \
  | grep -oE '[A-Z][A-Za-z-]+' | sort -u)
```

**问题**：`awk '/v4.1 完整集合/,/^[^#]/'` 会把范围扩到 `# [PRESERVE_FORMAT]` / `# 任何 phase / 编排器 / 文档新增...` / `# SKILL.md / system-prompt.md / PLATFORM-GUIDE.md（PR-7 联动）` 这些注释行，再用 `grep -oE '[A-Z][A-Za-z-]+'` 抓出非 enum token：`PRESERVE`、`FORMAT`、`SKILL`、`PLATFORM-GUIDE`、`PR-`。

**新文**（改用 python，按"以 `#   Intake / ...` 开头的 enum 列表行"严格抽取，与 system-prompt 侧策略对称）：
```bash
ENUM_CORE=$(python3 - <<'PYEOF'
import re
content = open('core/workflow-status-template.yaml').read()
# 仅提取注释块中以 "#   " 开头且含 " / " 分隔符的 enum 列表行
# （v4.1 完整集合下方 5 行）
m = re.search(r'v4\.1\s*完整集合[^\n]*\n((?:#\s+\S.*\n)+)', content)
if not m:
    print('__MISSING__')
    raise SystemExit(0)
states = []
for line in m.group(1).splitlines():
    # 仅识别 "#   X / Y / Z" 形式；首字符必须大写、含 "/"
    body = re.sub(r'^#\s+', '', line)
    if '/' not in body:
        continue
    states += [s.strip() for s in body.split('/')]
states = sorted({s for s in states if re.fullmatch(r'[A-Z][A-Za-z-]+', s)})
for s in states: print(s)
PYEOF
)
```

**改动 2：Spec-Uncertain `allowed_values` 锚点定位**（脚本 L54-55，原 `head -1` 取首次命中）

**原文**：
```bash
SU_CORE=$(grep -oE 'allowed_values=[^"]*' core/workflow.xml | head -1 || echo "")
SU_SP=$(grep -oE 'allowed_values=[^"]*' system-prompt.md | head -1 || echo "")
```

**问题**：两个文件都含多处 `allowed_values=`（说明文本、规则文本、字段表），`head -1` 命中的不一定是 Spec-Uncertain 段。

**新文**（依赖 ANCHOR-N1/N2 新加的稳定锚点；缺锚点直接退出 error，避免静默漂移；**v1.2 修订**：regex 允许可选双引号包裹，兼容 `core/workflow.xml` 的 `allowed_values="Confirm"` 与 `system-prompt.md` 的 `allowed_values=1|2|S` 两种现实写法，sed 链路统一剥引号）：
```bash
# v4.2 PR-2 / SCRIPT-FIX1（v1.2 regex 修订）：依赖 ANCHOR-N1/N2 锚点定位（缺锚点直接 error）
# regex 同时兼容 allowed_values="Confirm" / allowed_values=1|2|S 两种写法
SU_CORE=$(awk '/<!-- ANCHOR: spec-uncertain-allowed-values -->/,/<\/step-pause>|<\/rule>|^[[:space:]]*$/' core/workflow.xml \
  | grep -oE 'allowed_values="?[^[:space:],"`<)]+"?' | head -1 \
  | sed -e 's/^allowed_values=//' -e 's/^"//' -e 's/"$//' || echo "")
SU_SP=$(awk '/<!-- ANCHOR: spec-uncertain-allowed-values -->/,/<\/step-pause>|<\/rule>|^[[:space:]]*$/' system-prompt.md \
  | grep -oE 'allowed_values="?[^[:space:],"`<)]+"?' | head -1 \
  | sed -e 's/^allowed_values=//' -e 's/^"//' -e 's/"$//' || echo "")
if [ -z "$SU_CORE" ] || [ -z "$SU_SP" ]; then
  echo "::${SEVERITY}::Spec-Uncertain ANCHOR 缺失或锚点窗口内未提取到 allowed_values（core: '$SU_CORE' / sp: '$SU_SP'）— 见 ANCHOR-N1/N2"
  [ "$SEVERITY" = "error" ] && fail=1
fi
```

> **v1.2 修订验证**：本地实跑 `echo 'allowed_values="Confirm"' | grep -oE 'allowed_values="?[^[:space:],"\`<)]+"?' | head -1 | sed -e 's/^allowed_values=//' -e 's/^"//' -e 's/"$//'` 输出 `Confirm`；`echo 'allowed_values=1|2|S' | …` 输出 `1|2|S`；两种写法均能正确剥到净值。

**修订理由**：
- 改动 1 让 ENUM 提取严格按"`#   <state> / <state> / ...`" 行格式，剔除非 enum 注释噪音；与 system-prompt 侧 `re.findall(r'\b([A-Z][A-Za-z-]+)\b', text)` 提取保持对称（system-prompt 侧已通过 `v4.1 完整集合` 锚点定位，与 core 侧基础对齐）。
- 改动 2 让 Spec-Uncertain 提取依赖 ANCHOR-N1/N2 稳定锚点（详见下方），消除 `head -1` 取首次命中的脆弱性。
- **修完后实跑必须为零 warning**（DoD §3.1 验收），才能进入 CI-U1b severity 升级。

**兼容性影响**：脚本只改提取逻辑、不改判定语义；修复后干净主干实跑应输出 `✅ check-system-prompt-sync.sh (v1.1) 通过`，零 warning。

---

#### 2.10.2 变更点 CI-U1b · `check-system-prompt-sync.sh` 默认严重度 warning → error（v1.1 新增 / O5 拆分第二步）

> **前置硬约束**：必须在 SCRIPT-FIX1 落地 + ANCHOR-N1/N2 落地 + 干净主干实跑零 warning 之后再做本变更点；reviewer 必跑 `bash mobile-qa-workflow/scripts/check-system-prompt-sync.sh` 验证零 warning，否则**本变更点不能合入**。

**操作**：脚本 L10 默认值 + workflow yml 侧 env 块两段改动。

**原文（脚本 L10）**：
```bash
SEVERITY="${SP_SYNC_SEVERITY:-warning}"
```

**新文**：
```bash
SEVERITY="${SP_SYNC_SEVERITY:-error}"  # v4.2 PR-2 / CI-U1b：升级默认 warning → error（前置：SCRIPT-FIX1 + ANCHOR-N1/N2 实跑零 warning）
```

**workflow yml 侧改动**（CI-W1 内）：删除 Check 10 step 的 `env: SP_SYNC_SEVERITY: warning` 块（默认值即 error）。

**修订理由**：
- PR-1 v1.1 阶段保持 warning 是为了让 PR-1 自身不被自身阻塞（system-prompt.md 中已知存在 v3 残留 token）；本 PR 通过 O7/O8 字段名同步 + SCRIPT-FIX1 提取器修复 + ANCHOR-N1/N2 稳定锚点三件套，把 sync 守门收敛到可升 error 的状态。

**兼容性影响**：升级后 CI 行为变更：未来 system-prompt.md 与 core/ 不同步将直接红 CI；新接入的状态名 / Spec-Uncertain 改写必须双侧同步落地。

---

#### 2.10.~~3~~ 变更点 ~~CI-U2~~（v1.1 删除 / Major 1 修订：选选项 A）

> **v1.1 修订说明**：v1.0 原计划把 `check-io-contract.sh` 严重度 warning → error。v1.1 review Major 1 实跑发现：当前脚本 13 个声明 basename 中 12 个走变量化路径兜底 notice（`存在变量化路径兜底: ...`），升 error 后只是把"宽松脚本"变成"强制通过"，守门价值不足。**本 PR 不再升级 io-contract 严重度，保持 warning 现状**；脚本算法增强（缩窄变量化兜底范围）推迟到后续独立 PR（建议放在 PR-3 或 PR-7 集中处理产物契约）。
>
> **本 PR 对 io-contract 不动**：脚本不动、workflow yml Check 11 不动、severity 不动。CI 自检表 §5 中 `check-io-contract.sh` 行从 v1.0 的 ⬆️ 改为 ⏸（详见 §5）。

---

#### 2.10.3 变更点 ANCHOR-N1 · `system-prompt.md` 添加 Spec-Uncertain 稳定锚点（v1.1 新增）

> **背景**：v1.1 review Major 4 — 旧 H1 守门用 `grep -oE 'Spec-Uncertain[^<]*allowed_values=[^,)<\s]*' ... | head -1` 取首次命中，与现有 sync 脚本同款脆弱。改用稳定锚点定位。

**操作**：在 `system-prompt.md` 现有 Spec-Uncertain 段落（含 `allowed_values=1|2|S` 的位置）前一行插入锚点注释。

**新文**（在原 Spec-Uncertain `<step-pause>` / 描述段前插入；具体行号以本 PR 落地时 grep 锁定为准，**只加 1 行**）：

```markdown
<!-- ANCHOR: spec-uncertain-allowed-values -->
```

**修订理由**：
- 锚点是 reviewer 可肉眼识别的稳定标识；H1 守门 + SCRIPT-FIX1 改动 2 共用此锚点，避免任意一方改动文案顺序导致脆弱。
- 锚点本身是注释，不影响 LLM 阅读 system-prompt.md 时的语义。
- **本 PR 唯一可对 system-prompt.md 做的"非 REF-D5 + 非 ANCHOR-N1"改动是零**（H1 守门兜底）。

**兼容性影响**：纯加项；`system-prompt.md` 行数 +1；REF-D5 改动后净行数变化为 -1（删 snapshot 字段表行）+ 1（加锚点） = 0。

---

#### 2.10.4 变更点 ANCHOR-N2 · `core/workflow.xml` 添加 Spec-Uncertain 稳定锚点（v1.1 新增 / ANCHOR-N1 联动）

**操作**：在 `core/workflow.xml` 现有 Spec-Uncertain 段落（含 `allowed_values="Confirm"` 的位置）前一行插入与 ANCHOR-N1 同名锚点。

**新文**：

```xml
<!-- ANCHOR: spec-uncertain-allowed-values -->
```

**修订理由**：
- 与 ANCHOR-N1 配对，让 SCRIPT-FIX1 改动 2 + CI-N1 守门可同时按锚点定位 core 与 sp 两侧 Spec-Uncertain 段。
- PR-4 改写 `Confirm` → `1|2|S` 时，锚点位置不动，只动 `allowed_values=` 取值；H1 守门自然解除（CI-N1 步骤 3 notice）。

**兼容性影响**：纯加项；不影响 LLM 解析 core/workflow.xml 行为。

---

#### 2.10.5 变更点 CI-N1 · `scripts/check-build-system-prompt-precondition.sh` 新建（H1 锚点提取式守门 / v1.1 重写）

> **v1.1 修订**：彻底改用锚点提取，缺锚点 / 锚点后未找到 `allowed_values=` 直接 error 退出，杜绝 v1.0 `head -1` 取首次命中的脆弱模式。

**新文件内容**（约 ~50 行 bash）：

```bash
#!/usr/bin/env bash
# check-build-system-prompt-precondition.sh (v4.2 PR-2 / O22 / H1 守门 / v1.1 锚点提取式)
# 守门：禁止 PR-2 阶段即兴运行 build-system-prompt.py --mode=full 替换 system-prompt.md
#   ① system-prompt.md 中 Spec-Uncertain 段落 allowed_values 必须保持为 1|2|S
#      （而非 core/workflow.xml 当前的 Confirm —— PR-4 O13a 完成后两者才能统一）
#   ② system-prompt.md 与 core/workflow.xml 的 Spec-Uncertain allowed_values
#      若两者一致（都是 1|2|S）说明 PR-4 已合入，可解除本守门
# 关联：V1.1 §4.1.0 H1 / 主控 §3 H1 / 主控 §4 PR-2 启用为 error
# 实现：依赖 ANCHOR-N1（system-prompt.md）+ ANCHOR-N2（core/workflow.xml）稳定锚点；缺锚点直接 error

set -euo pipefail
cd "$(dirname "$0")/.."

ANCHOR='<!-- ANCHOR: spec-uncertain-allowed-values -->'
fail=0

# ──────────────────────────────────────────────────────────
# 工具函数：按锚点定位 + 锚点后 N 行内提取首个 allowed_values=
# 设计要点：
#   · 锚点必须存在，否则 fail 并提示去 PR-2 加锚点（ANCHOR-N1/N2）
#   · 锚点后扫描窗口：默认 20 行（足以覆盖 step-pause 块 / 描述段）
#   · 提取目标：第一个 allowed_values=<TOKEN> 中的 TOKEN（终止于空白/逗号/双引号/反引号/尖括号/右括号）
# ──────────────────────────────────────────────────────────
extract_after_anchor() {
  local file="$1" window="${2:-20}"
  if ! grep -qF "$ANCHOR" "$file"; then
    echo "__MISSING_ANCHOR__"
    return
  fi
  # v1.2 修订：regex 允许可选双引号包裹，兼容 XML attribute (`allowed_values="Confirm"`)
  # 与 markdown 描述 (`allowed_values=1|2|S`) 两种写法；sed 链路统一剥 `allowed_values=` 与外围引号
  awk -v anchor="$ANCHOR" -v win="$window" '
    index($0, anchor) {hit=NR; next}
    hit && NR-hit <= win {print}
  ' "$file" | grep -oE 'allowed_values="?[^[:space:],"`<)]+"?' | head -1 \
    | sed -e 's/^allowed_values=//' -e 's/^"//' -e 's/"$//'
}

SP_SU=$(extract_after_anchor system-prompt.md)
CORE_SU=$(extract_after_anchor core/workflow.xml)

# 1) 锚点缺失硬约束
if [ "$SP_SU" = "__MISSING_ANCHOR__" ]; then
  echo "::error::system-prompt.md 缺 Spec-Uncertain 锚点（应为 '$ANCHOR'）— 见变更点 ANCHOR-N1"
  fail=1
fi
if [ "$CORE_SU" = "__MISSING_ANCHOR__" ]; then
  echo "::error::core/workflow.xml 缺 Spec-Uncertain 锚点（应为 '$ANCHOR'）— 见变更点 ANCHOR-N2"
  fail=1
fi
[ $fail -ne 0 ] && exit $fail

# 2) 锚点后无 allowed_values= 提取硬约束
if [ -z "$SP_SU" ]; then
  echo "::error::system-prompt.md 锚点后 20 行内未找到 allowed_values= 定义"
  fail=1
fi
if [ -z "$CORE_SU" ]; then
  echo "::error::core/workflow.xml 锚点后 20 行内未找到 allowed_values= 定义"
  fail=1
fi
[ $fail -ne 0 ] && exit $fail

# 3) PR-2 阶段强约束：system-prompt.md 必须为 1|2|S
if [ "$SP_SU" != "1|2|S" ]; then
  echo "::error::H1 守门违反：system-prompt.md 中 Spec-Uncertain allowed_values 应为 '1|2|S'，实际为 '$SP_SU'"
  echo "::error::原因：PR-2 阶段禁止运行 build-system-prompt.py --mode=full 替换 system-prompt.md（V1.1 §4.1.0 H1）"
  echo "::error::首次自动构建并替换由 PR-6 触发（依赖 PR-4 O13a 已合入）"
  fail=1
fi

# 4) 兜底提示：若 core/workflow.xml 也已是 1|2|S（PR-4 已合入），可在 PR-6 内解除本守门
if [ "$CORE_SU" = "1|2|S" ]; then
  echo "::notice::core/workflow.xml 中 Spec-Uncertain 已统一为 1|2|S（PR-4 O13a 已合入）；PR-6 内可解除本守门"
fi

[ $fail -eq 0 ] && echo "✅ check-build-system-prompt-precondition.sh 通过（sp=$SP_SU / core=$CORE_SU）"
exit $fail
```

**修订理由（v1.1）**：
- **锚点稳定性**：依赖 ANCHOR-N1/N2 的稳定字符串，比"`Spec-Uncertain[^<]*allowed_values=`"宽松正则鲁棒一个数量级。
- **缺锚点直接 error**：避免静默漂移 — 若 reviewer 误删了锚点，CI 立即红，强迫修复。
- **窗口式扫描**：锚点后 20 行作为提取窗口，比 `head -1` 全局取首次命中更具上下文确定性。
- **统一终止字符集**：`[^[:space:],"`<)]+` 兼容 markdown / xml / 代码块多种上下文。

**兼容性影响**：
- 纯 CI 守门，不影响运行时。
- PR-4 改写 `Confirm` → `1|2|S` 后，本脚本步骤 3/4 的 notice 自然提示"PR-6 可解除"；PR-6 解除时直接删除 CI workflow yml 的 Check 13 step 即可（本脚本可保留作为后续 invariant 校验）。

---

#### 2.10.6 变更点 TEST-N1 · P3 反查读端回放用例（v1.1 新增 / READ-N1+N2 验证）

> **背景**：v1.1 review Blocking 1 — O7 删除 `rca_fanout_mode_snapshot` 后必须有"回放用例证明 snapshot 已完全冗余"。本变更点提供该证明。

**操作**：新建 fixture + test 脚本，模拟"P3 → P4（误清 fanout_mode 的 C10 历史 bug）→ P3 重入"场景，断言 READ-N1 反查逻辑能从 phase_history 还原 fanout_mode。

**新增文件 1：`mobile-qa-workflow/scripts/tests/fixtures/p3-reentry-null-fanout-with-phase-history.yaml`**（v1.2 改名 / 边缘 case：P3 重入时 fanout_mode 已被清空，phase_history 含上一次 P3 完成时 append 的元素 — 文件名直白对应内容；v1.1 旧名 `p3-reentry-with-snapshot-but-no-history.yaml` 与内容语义相反，已废弃）

```yaml
# 模拟 v4 会话进入 P3 重入：
#   - fanout_mode 已被清空 (例如 P4 误清的 C10 历史 bug 触发)
#   - phase_history 含上一次 P3 完成时 append 的元素
# 期望：READ-N1 反查到 medium-challenge 写回 fanout_mode
issue_id: TEST-O7-READ-N1
current_state: RCA-Designing
schema_version: 4
workflow_version: v4
analysis_complexity: medium
fanout_mode: null
fix_fanout_mode: null
phase_history:
  - phase: qa-root-cause
    timestamp: "2026-04-21T10:00:00Z"
    fanout_mode: medium-challenge
    note: null
```

**新增文件 2：`mobile-qa-workflow/scripts/tests/test_p3_reentry_replay.py`**（约 ~80 行 python，纯 yaml 解析 + 断言反查算法等价；不需要真跑 LLM）

```python
#!/usr/bin/env python3
"""test_p3_reentry_replay.py — READ-N1 反查算法等价回放（v4.2 PR-2 / O7 方案 B）

不调用 LLM，仅用 python 实现 READ-N1 在 p3-root-cause.md step 4 的反查算法的等价副本，
对 fixture 跑一次，断言能从 phase_history 末项 qa-root-cause 元素还原 fanout_mode。
等价性约束：本脚本算法与 p3-root-cause.md step 4 的 LLM 描述必须保持文本对照可证，
任何描述层改动必须同步更新本脚本（reviewer 议题 #R3）。
"""
import unittest
from pathlib import Path
from ruamel.yaml import YAML

FIXTURE = Path(__file__).parent / "fixtures" / "p3-reentry-null-fanout-with-phase-history.yaml"


def reentry_restore_fanout_mode(status: dict) -> dict:
    """READ-N1 算法等价副本：fanout_mode == null 且 phase_history 非空时反查末项 qa-root-cause。"""
    if status.get("fanout_mode") is not None:
        return status
    history = status.get("phase_history") or []
    for item in reversed(history):
        if isinstance(item, dict) and item.get("phase") == "qa-root-cause" and item.get("fanout_mode"):
            status["fanout_mode"] = item["fanout_mode"]
            break
    return status


class TestP3ReentryReplay(unittest.TestCase):
    def test_restore_from_phase_history_last_item(self):
        yaml = YAML(typ="safe")
        status = yaml.load(FIXTURE.read_text())
        self.assertIsNone(status["fanout_mode"], "前置条件：fixture 应满足 fanout_mode == null")
        restored = reentry_restore_fanout_mode(status)
        self.assertEqual(restored["fanout_mode"], "medium-challenge",
                         msg="READ-N1 应从 phase_history 末项 qa-root-cause 还原 fanout_mode")

    def test_skip_when_fanout_mode_already_set(self):
        status = {"fanout_mode": "simple-single", "phase_history": [
            {"phase": "qa-root-cause", "fanout_mode": "medium-challenge"}
        ]}
        restored = reentry_restore_fanout_mode(status)
        self.assertEqual(restored["fanout_mode"], "simple-single",
                         msg="新会话主路径 fanout_mode 已写时不应被反查覆盖")

    def test_no_qa_root_cause_in_history_keeps_null(self):
        status = {"fanout_mode": None, "phase_history": [
            {"phase": "qa-spec-defining", "fanout_mode": None}
        ]}
        restored = reentry_restore_fanout_mode(status)
        self.assertIsNone(restored["fanout_mode"],
                          msg="phase_history 不含 qa-root-cause 时应保持 null，由 spec 推断路径接管")


if __name__ == "__main__":
    unittest.main()
```

**修订理由**：
- 三个 test case 覆盖主路径 + 边缘 case + 极端 case，证明 O7 删除 snapshot 后读端反查能完整接管 P3 重入还原。
- python 算法是 LLM 描述的"等价副本"：reviewer 议题 #R3 要求"任何 LLM 描述层改动必须同步更新本脚本"，避免描述与回放算法漂移。

**兼容性影响**：纯加项；与 GEN-N2 共用 `unittest discover` 入口；CI Check 14 自动跑。

---

#### 2.10.7 变更点 CI-W1 · `.github/workflows/qa-workflow-schema-check.yml` 升级 + 新增（v1.1 修订）

**操作**：在 PR-1 v1.1 已集成的 4 个 step 基础上做调整 ——

- **Check 10** 升级为 error（CI-U1b）
- **Check 11** **保持 warning 不变**（v1.1 review Major 1 修订：CI-U2 删除）
- **Check 13** 新增（CI-N1 锚点提取式 H1 守门）
- **Check 14** 新增（GEN-N2 + TEST-N1 单测合并）

```yaml
      # ════════════════════════════════════════════════════════════════
      # 检查 10（PR-2 升级 error）：system-prompt sync 守门
      # 前置：SCRIPT-FIX1 修复提取器 + ANCHOR-N1/N2 锚点已加 + 实跑零 warning
      # ════════════════════════════════════════════════════════════════
      - name: Check 10 — system-prompt sync 守门
        # v4.2 PR-2 / CI-U1b：删除 SP_SYNC_SEVERITY=warning，默认即 error
        run: bash mobile-qa-workflow/scripts/check-system-prompt-sync.sh

      # ════════════════════════════════════════════════════════════════
      # 检查 11（PR-2 维持 warning）：io-contract 守门
      # v1.1 review Major 1 修订：当前脚本变量化兜底过宽，假绿守门价值不足，
      # 推迟到后续算法增强 PR；本 PR 不动 severity，保持 PR-1 v1.1 配置。
      # ════════════════════════════════════════════════════════════════
      - name: Check 11 — io-contract 守门
        env:
          IO_CONTRACT_SEVERITY: warning  # v4.2 PR-2 不升级；待后续 PR 算法增强后再改 error
        run: bash mobile-qa-workflow/scripts/check-io-contract.sh

      # ════════════════════════════════════════════════════════════════
      # 检查 13（PR-2 启用 error）：build-system-prompt precondition 守门 / V1.1 §4.1.0 H1
      # 实现：锚点提取式（ANCHOR-N1/N2 联动），缺锚点直接 error
      # ════════════════════════════════════════════════════════════════
      - name: Check 13 — build-system-prompt precondition 守门
        run: bash mobile-qa-workflow/scripts/check-build-system-prompt-precondition.sh

      # ════════════════════════════════════════════════════════════════
      # 检查 14（PR-2 启用）：build-system-prompt 单测 + P3 反查回放用例
      # 同时跑 GEN-N2（生成器单测）+ TEST-N1（READ-N1 反查算法等价回放）
      # ════════════════════════════════════════════════════════════════
      - name: Check 14 — build-system-prompt + p3-reentry replay tests
        run: |
          pip install -r mobile-qa-workflow/scripts/requirements.txt
          python -m unittest discover -s mobile-qa-workflow/scripts/tests/ -v
```

**修订理由**：
- Check 10 升级 error 是 PR-1 留下的承诺；本 PR 通过 SCRIPT-FIX1 + ANCHOR-N1/N2 三件套兑现。
- Check 11 **不升级**：v1.1 review Major 1 实跑结论 — 现有脚本假绿，先不升 error。显式保留 `IO_CONTRACT_SEVERITY: warning` env 块作为"v1.1 主动决定"的标记，避免后续 reviewer 误以为漏改。
- Check 13 = 锚点提取式 H1 守门；Check 14 = 生成器单测 + READ-N1 反查回放；两者保证生成器与读端健康。

**兼容性影响**：CI 总耗时增加 ~30-60 秒（pip install + 单测）；可考虑 cache pip wheel 优化（不在本 PR 范围）。

---

## 3. PR-level DoD 子集（链接到主控 §5）

> 完整跨平台矩阵见主控 [§5 PR-2 行](./README.md#5-跨平台回归矩阵每-pr-必跑)；本节仅列必须满足的子集。

### 3.1 静态契约校验

- [ ] **O7 落地**（v1.2 grep 口径精确化）：`core/workflow-status-template.yaml` 内 `rca_fanout_mode_snapshot` **非注释行命中 0 处**（YAML 中以 `#` 开头的废弃说明注释允许保留；非注释字段定义行禁止出现）；`phases/p3-root-cause.md` 内 `rca_fanout_mode_snapshot` **非注释行命中 0 处**（XML 中 `<!-- ... -->` 注释段允许作为 ADR 链接说明保留）；`system-prompt.md` / `SKILL.md` / `PLATFORM-GUIDE.md` 各 **非注释正文命中 0 处**（即字段表行 / `<action>` 写入行 / 描述段全部清除）
- [ ] **READ-N1 落地（v1.1 新增）**：`phases/p3-root-cause.md` step 4 头部含 `<check if="{workflow_status}.fanout_mode == null 且 {workflow_status}.phase_history 非空">` 反查块；reviewer 单 prompt 抽 1 用例验证 LLM 能正确按描述执行反查
- [ ] **READ-N2 落地（v1.1 新增 / v1.2 落点修订）**：`core/workflow.xml` **step 2**（L28，与 REF-D1 同行）读字段列表末尾含 `phase_history`；v3 兼容默认值无需追加（迁移脚本已注入 `[]`）
- [ ] **O8 落地**：`core/workflow-status-template.yaml` 内 grep `^fix_strategy_mode\b` 命中 **0 处**；`phases/p4-fix-design.md` 内 grep `<action>更新.*fix_strategy_mode\s*=` 命中 **0 处**（`<check if="fix_strategy_mode == ...">` 与 `{fix_strategy_mode}` 模板变量保留）；`core/workflow.xml` / `system-prompt.md` / `SKILL.md` / `PLATFORM-GUIDE.md` 内"workflow-status 字段表 / 字段读写列表"中 `fix_strategy_mode` 命中 **0 处**
- [ ] **O9 落地**：`core/workflow-status-template.yaml` 含 `# ── group: retries` 注释块，5 个计数器字段名全部出现在该注释块下方说明中
- [ ] **MIG-N1 落地**：`migrate-workflow-status-v3-to-v4.py` 含 `--cleanup-v4-deprecated` flag + 文件头 docstring 删除"不实施 fanout_mode 反查还原逻辑"一句（v1.1 修订）；本地构造 1 份含 `rca_fanout_mode_snapshot` + `fix_strategy_mode` 的 v4 测试文件，运行 `--cleanup-v4-deprecated` 后两字段消失，`fix_fanout_mode` 值正确（拷自 `fix_strategy_mode`），可重复运行（幂等）
- [ ] **ADR-D1 + ADR-IDX1**：ADR-007 末尾含 v4.2 修订段落（含 P3 反查读端落地说明）；`doc/adr/000-index.md` 中 ADR-007 行的"落地 PR"列含 "v4.2 PR-2 修订"
- [ ] **GEN-N1 ~ GEN-N3 落地（v1.1 写死最小完整实现）**：`scripts/build-system-prompt.py` 5 个 builder（L0/L1/L2/L3/L4）**全部可跑**（不允许 NotImplementedError stub）+ 三种 mode（full/layered/verify）**全部可跑** + 文件存在；`python -m unittest discover -s mobile-qa-workflow/scripts/tests/` 全绿；`python build-system-prompt.py --mode=verify` 退出 0；`python build-system-prompt.py --mode=layered --output-dir=/tmp/pr2-test` 输出 5 个 L\*.md 文件
- [ ] **ANCHOR-N1 + ANCHOR-N2 落地（v1.1 新增）**：`system-prompt.md` 与 `core/workflow.xml` 各含 `<!-- ANCHOR: spec-uncertain-allowed-values -->` 字面注释 1 处（grep 命中各 1）；锚点紧邻 Spec-Uncertain 段；`bash mobile-qa-workflow/scripts/check-build-system-prompt-precondition.sh` 输出含 `sp=1|2|S / core=Confirm`
- [ ] **TEST-N1 落地（v1.1 新增 / v1.2 fixture 改名）**：`scripts/tests/fixtures/p3-reentry-null-fanout-with-phase-history.yaml` + `scripts/tests/test_p3_reentry_replay.py` 文件存在（fixture 文件名与"fanout_mode=null + phase_history 含末项"语义一致）；`python -m unittest discover` 包含 3 个 test_p3_reentry_replay 用例且全部通过
- [ ] **SCRIPT-FIX1 落地（v1.1 新增）**：`check-system-prompt-sync.sh` 中 `ENUM_CORE` 提取已切换为 python 严格模式（不含旧 `awk + grep -oE '[A-Z][A-Za-z-]+'`）；`SU_CORE/SU_SP` 提取已依赖 ANCHOR；**实跑零 warning**：`bash mobile-qa-workflow/scripts/check-system-prompt-sync.sh` 输出仅 `✅ check-system-prompt-sync.sh (v1.1) 通过（severity=error）`，**不允许**任何 `::warning::` 或 `::error::`
- [ ] **CI-U1b / CI-N1 / CI-W1 落地**：CI workflow yml 中 Check 10 默认 error（无 SP_SYNC_SEVERITY env block）；Check 11 显式 `IO_CONTRACT_SEVERITY: warning`（v1.1 维持）；Check 13 / 14 step 存在；本地手跑全部相关脚本均退出 0
- [ ] **system-prompt.md 防误改**：本 PR diff 中 `system-prompt.md` 的改动**仅限** REF-D5 涉及的字段表 + LLM 描述行 + ANCHOR-N1 1 行新加锚点；**禁止**任何其他改动（特别是 Spec-Uncertain 段落 `allowed_values=1|2|S` 必须保持原样）；reviewer 必贴 `git diff -- mobile-qa-workflow/system-prompt.md` 完整输出，行变动数 ≤ 3（删 1 行字段表 + 改 1 行 LLM 描述 + 加 1 行锚点）

### 3.2 动态用例

- [ ] **跨平台回归**（主控 §5 PR-2 行）：
  - Cursor / Trae / **Dify**（O7/O8 state 瘦身 + READ-N1 反查描述需双侧验证）三方各跑 eval-cases 全量
  - 单 prompt LLM 抽 1 用例
  - 生成器单测 100% 通过 + READ-N1 反查回放单测 100% 通过
- [ ] **存量会话迁移验证**：在 Limited 平台抽 1 个含 `rca_fanout_mode_snapshot` 与 `fix_strategy_mode` 的存量会话，运行 `migrate-workflow-status-v3-to-v4.py --cleanup-v4-deprecated`，验证：① 两字段消失；② `fix_fanout_mode` 值正确（若原 `fix_fanout_mode = null` 且 `fix_strategy_mode` 有值则拷值，否则保持原 `fix_fanout_mode` 值不变）；③ 主链路从 P3 重入到 Done 行为与迁移前一致；④ **新增（v1.1）**：抽 1 个 `fanout_mode = null` 且 `phase_history` 含 P3 末项的 v4 会话，验证 P3 重入 LLM 按 READ-N1 描述能正确还原 fanout_mode（与 TEST-N1 单测算法等价）
- [ ] **通用门禁**（V1.1 §4.2）：`eval-framework/artifact_checker.py` 全量通过 + `eval-cases/seed-10` chains A/B `mean_score` 不降 + 路由层抽 5 case 人工读 `workflow-status.yaml` 一致性

> **PR-2 不验收的 §5 项**：phase 出口宏 → PR-3；Spec-Uncertain 双侧 → PR-4；step-pause registry → PR-5；system-prompt 自动构建 diff → PR-6；**io-contract 升级 error → 后续独立 PR**（v1.1 review Major 1 修订）

---

## 4. PR-level 回滚动作

- **回滚命令**：`git revert <PR-2-merge-commit>`
- **回滚后状态**：
  - `rca_fanout_mode_snapshot` / `fix_strategy_mode` 两字段在 schema 中复活；P3/P4 写入端复活；下游 5 处文档引用复活
  - **READ-N1 / READ-N2 反查读端消失**（v1.1 新增）：P3 step 4 反查块消失、`core/workflow.xml` **step 2** 读字段列表 `phase_history` 消失；存量会话若处于"fanout_mode = null + phase_history 非空"状态将无法自动还原（**注意**：snapshot 字段也同步复活，C10 兼容性方案 B 兜底回归）
  - `migrate-workflow-status-v3-to-v4.py` 回到 PR-1 形态（`--cleanup-v4-deprecated` 子命令消失；存量会话已清理过的字段不会复活，主路径迁移仍正常）；docstring 中"不实施反查还原"句子复活
  - `build-system-prompt.py` + 单测文件消失；`check-build-system-prompt-precondition.sh` 消失；`tests/test_p3_reentry_replay.py` + fixture 消失
  - `check-system-prompt-sync.sh` 提取器回退到 PR-1 v1.1 形态（含已知噪音）；默认严重度回退到 warning
  - **`check-io-contract.sh` 不受回滚影响**（v1.1 review Major 1 修订：本 PR 未改它）
  - `system-prompt.md` 回到 PR-1 形态（含 `rca_fanout_mode_snapshot` 字段表行 + `fix_strategy_mode` 描述 + 不含 ANCHOR-N1 锚点）；`core/workflow.xml` 同步移除 ANCHOR-N2 锚点
- **下游影响**：
  - **PR-3 强依赖**：PR-3 的 `<phase-abort>` 宏标签改写依赖本 PR 的 state 字段瘦身后路径（特别是 P3 的早退点）；本 PR 回滚后 PR-3 内 P3 / P4 的宏标签写入还需要包含 `rca_fanout_mode_snapshot` / `fix_strategy_mode` 字段，与主控 §6 PR-3 描述不一致 → 必须同步评估是否回滚 PR-3
  - **PR-4 / PR-5 / PR-6 / PR-7 弱依赖**：状态字段瘦身仅影响 schema 干净度，不影响后续 PR 的运行时改动
  - **生成器消失**：PR-6 触发首次构建依赖本 PR 的 `build-system-prompt.py`；本 PR 回滚后 PR-6 必须等本 PR 重新合入才能继续
  - **READ-N1 消失但 snapshot 复活**：因为 v1.0 的方案 B（snapshot 兜底）会随 PR-2 回滚一同复活，C10 兼容性双轨在回滚后自动回到双保险状态；**不需要**额外回填 READ-N1 逻辑
- **风险等级**：🟡 **低**（schema 字段瘦身可逐字段回退；生成器是新增工具，回退无运行时影响；READ-N1 消失同时 snapshot 复活，总兼容性闭环不破）
- **存量会话兼容**：已运行 `--cleanup-v4-deprecated` 的存量会话不会因为本 PR 回滚而恢复字段；若同时处于"fanout_mode = null + phase_history 非空 + snapshot 已删"的边缘状态（极小概率），需要人工或后续 PR 补一次 spec 推断

---

## 5. §4 CI 守门自检（PR-2 视角，v1.1 修订）

| 主控 §4 脚本 | PR-2 状态 | 落地证据 / 承接 PR |
|---|---|---|
| `check-state-enum.sh` | ✅ error（PR-1 已启用） | 不变；本 PR 删除 schema 字段后该脚本仍绿 |
| `check-system-prompt-sync.sh` | ⬆️ warning → error（**前置**：SCRIPT-FIX1 提取器修复 + ANCHOR-N1/N2 锚点 + 实跑零 warning） | 变更点 SCRIPT-FIX1 + CI-U1b + CI-W1 |
| `check-io-contract.sh` | ⏸ **维持 warning（v1.1 review Major 1 修订）** | 不在本 PR 范围；后续算法增强 PR 内升级 |
| `check-subagent-params.sh` | ✅ error（PR-1 已启用） | 不变 |
| `check-build-system-prompt-precondition.sh` | ✅ **PR-2 启用为 error（锚点提取式）** | 变更点 ANCHOR-N1 + ANCHOR-N2 + CI-N1 + CI-W1 |
| `check-phase-abort-structure.sh` | ⏸ | PR-3 启用 warning，PR-6 升级 error |
| `check-step-pause-registry.sh` | ⏸ | PR-5 启用为 error |

**自检结论（v1.1）**：PR-2 落地主控 §4 中 PR-2 启用列的 **2 项**（CI-U1b 升级 + CI-N1 新增）；**v1.0 计划的 CI-U2 升级 io-contract 已删除**（v1.1 review Major 1）。CI-U1b 升级有"前置 SCRIPT-FIX1 + 实跑零 warning"硬约束，reviewer 必须按 §3.1 DoD 顺序验证。

---

## 6. Reviewer 议题汇总（v1.1 修订）

| # | 议题 | 影响范围 | 处理建议 |
|---|---|---|---|
| 1 | **`fix_strategy_mode` 模板变量保留 vs 删除**：本 PR 仅删除 schema 字段，保留 P4 / system-prompt 内的 `<check if="fix_strategy_mode == ...">` 与 `{fix_strategy_mode}` LLM 局部变量；是否会让 reviewer 误认为字段还存在？ | DoD 校验完整性 | 在 §3.1 DoD 中显式区分"workflow-status 字段表 / 字段读写列表" vs "LLM 局部变量 / check 分支条件"，grep 命中点必须人工逐一确认归属 |
| 2 | **MIG-N1 子命令是否需要 `--dry-run` 兼容**：现有迁移脚本支持 `--dry-run`；新增 `--cleanup-v4-deprecated` 是否复用？ | 迁移脚本可用性 | 推荐复用：`--cleanup-v4-deprecated --dry-run` 仅打印将要做的操作，不写盘 |
| 3 | **GEN-N1 生成器口径（v1.1 写死）**：v1.0 在"骨架"与"完整实现"摇摆；v1.1 写死为"**最小完整实现**"。reviewer 验收口径：5 个 builder 全部可跑（不允许 NotImplementedError stub）+ 三种 mode 全部可跑 + 单测覆盖 verify / full+H1 守门 / layered 三场景。 | 生成器交付质量 | 实施者按 v1.1 §1 题注 ④ + §2.9 标题 + §3.1 DoD 三处口径执行；如发现某 builder 无法在 0.5d 内完成，必须**升级评审**（不允许私自降级为 stub） |
| 4 | ~~CI-U2 升级 io-contract error 的前置条件~~（v1.1 删除）→ 改为：**v1.0 CI-U2 删除原因说明**：实跑发现 13/12 走变量化兜底，假绿守门价值不足；本 PR 维持 warning，等 io-contract 算法增强独立 PR | CI 守门策略 | reviewer 不必再为本 PR 跑 io-contract 验收；如有人后续提出"为什么不升 error"，请引用 v1.1 review Major 1 + 本 §6 第 4 条 |
| 5 | **system-prompt.md 防误改的硬约束（v1.1 强化）**：本 PR 唯一可改动 system-prompt.md 的地方是 REF-D5（删 1 行字段表 + 改 1 行 LLM 描述）+ ANCHOR-N1（加 1 行锚点）；如何防止 reviewer 在本 PR 内"顺手"改其他地方？ | H1 强约束 | ① CI Check 13（锚点提取式 H1 守门）兜底 Spec-Uncertain 段落不被改；② 本 PR description 必须附 `git diff -- mobile-qa-workflow/system-prompt.md` 完整输出供 reviewer 审；③ system-prompt.md 改动行数硬上限 = 3（删 1 + 改 1 + 加 1）；超出**必须**显式批准 |
| 6 | **生成器单测在 CI 内的执行环境**：Check 14 需要 `pip install ruamel.yaml`，CI 是否已有 python 环境？是否会拖慢 CI？ | CI 性能 | 当前 `qa-workflow-schema-check.yml` 已有 python3 环境（PR-1 v1.1 CI-N3 / CI-N4 内嵌 python）；本 PR 仅追加 1 个 pip install + 1 个 unittest（含 GEN-N2 + TEST-N1），预期 +30-60 秒；可后续 cache pip wheel 优化 |
| **R1**（v1.1 新增） | **READ-N1 LLM 描述与 TEST-N1 算法等价性**：P3 step 4 内反查 LLM 描述是自然语言；TEST-N1 是 python 等价副本。reviewer 如何确认两者算法一致？ | O7 方案 B 正确性 | ① 在 PR description 内贴出 `phases/p3-root-cause.md` step 4 反查段 + `test_p3_reentry_replay.py:reentry_restore_fanout_mode` 函数并排展示；② Limited 平台抽 1 用例 / Full 平台抽 1 用例分别让 LLM 跑 fixture，对比 fanout_mode 还原结果是否与 python 等价副本一致；③ 任何后续描述层改动必须同步更新 python 副本（写入 reviewer 议题模板） |
| **R2**（v1.1 新增） | **ANCHOR-N1/N2 锚点字符串硬编码风险**：5 处脚本（SCRIPT-FIX1 改动 2 / CI-N1）都依赖 `<!-- ANCHOR: spec-uncertain-allowed-values -->` 字面字符串；如果将来锚点重命名怎么办？ | 锚点维护性 | 接受字符串耦合（与文件路径硬编码同级风险）；如需重命名，必须**同周期**改 5 处 + 同步修改 system-prompt.md / core/workflow.xml 锚点；CI 缺锚点直接 error 是有意为之的"反静默漂移"机制 |
| **R3**（v1.1 新增） | **SCRIPT-FIX1 改动 1 ENUM 提取严格模式可能误漏**：新提取器只识别 `# <state> / <state> / ...` 行格式；如果将来 enum 注释格式变化（如改用 yaml 列表）怎么办？ | sync 守门稳健性 | 接受耦合：当前 enum 在 status template 头部就是 `#   X / Y / Z` 格式，改格式属于 PR-7 文档同步级别的改动，必须同步改本脚本；DoD §3.1 含"实跑零 warning"硬约束，格式变化会立刻被发现 |

---

## Changelog

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-04-21 | 初版。基于 v4.2 主控 README §6 PR-2 + V1.1 §3.2.7 / §3.2.8 / §3.2.9 / §3.2.17 / §4.1.0 H1 完整展开；6 类共 ~22 个变更点；体例参考 PR-1 v1.1 但精简到 ~500 行（核心约束：① schema 瘦身 + 下游引用扫净是机械执行类工作 ② 生成器交付是新增工具 ③ CI 升级是承接 PR-1 承诺）。**关键约束**：H1 守门 — `system-prompt.md` Spec-Uncertain `allowed_values` 必须保持 `1\|2\|S`，本 PR 不替换 system-prompt.md（首次构建延迟到 PR-6）。 |
| v1.1 | 2026-04-21 | 经 [REVIEW 报告](./pr-2-sync-debt-and-system-prompt-generator-REVIEW-2026-04-21.md) 评审修订（Reject for now → 修订后复审）。**6 处定向修订**：① **Blocking 1（O7 读端缺位）** — 选方案 B：新增 READ-N1（P3 step 4 反查块）+ READ-N2（编排器 step 1 读字段追加 phase_history）+ TEST-N1（python 等价副本 + 3 case 单测 + fixture），同步删除迁移脚本 docstring 中"不实施反查还原"断言；② **Blocking 2（O5 直升 error 必红 CI）** — 拆 CI-U1 → SCRIPT-FIX1（脚本提取器修复，ENUM 严格模式 + Spec-Uncertain 锚点定位）+ CI-U1b（severity 升级），加"实跑零 warning 才能进 U1b"硬约束；③ **Major 1（io-contract 假绿）** — 选选项 A：删除 CI-U2，本 PR 维持 warning，推迟到后续算法增强 PR；④ **Major 2（口径冲突）** — 重写顶部"涉及文件"列与各 §2.x 变更点完全一致，删除"脚本本身不动"伪声明；⑤ **Major 3（生成器口径摇摆）** — 写死"最小完整实现"，5 个 builder + 三种 mode 全部可跑，DoD 含硬约束；⑥ **Major 4（H1 脆弱）** — 新增 ANCHOR-N1/N2（system-prompt.md + core/workflow.xml 各加 1 行 `<!-- ANCHOR: spec-uncertain-allowed-values -->` 注释）+ 重写 CI-N1 为锚点提取式（缺锚点直接 error）。**结构变化**：变更点类别 6 → 8（新增 READ / ANCHOR / TEST / SCRIPT-FIX）；变更点数量 ~22 → ~28；工作量 2.2d → 2.7d；新增 Reviewer 议题 R1/R2/R3；保留 v1.0 全部 §2.1~2.9 mechanical changes 内容不变。 |
| v1.2 | 2026-04-21 | 经 [REVIEW v1.1 报告](./pr-2-sync-debt-and-system-prompt-generator-REVIEW-v1.1-2026-04-21.md) 复审做**收敛性小修**（Needs one more revision → 期望复审通过可开工）。**5 处定向修订，无新增变更点**：① **Blocking（regex 不兼容 XML 引号）** — SCRIPT-FIX1 / CI-N1 提取 regex 由 `allowed_values=[^[:space:],"<)]+` 改为 `allowed_values="?[^[:space:],"`<)]+"?` + sed 链路统一剥 `allowed_values=` 与外围引号，兼容 `core/workflow.xml` 中 `allowed_values="Confirm"` 与 `system-prompt.md` 中 `allowed_values=1|2|S` 两种现实写法；本地实跑两种格式均能正确剥到净值（`Confirm` / `1|2|S`）；② **Major 1（READ-N1 落点）** — 修正"step 4 头部、原 `读取 {issue_card}` 行不动"描述错误：实际 `读取 {issue_card}` 在 P3 step 1（L34），step 4 第一行就是 `读取 Issue_Boundary_Level`（L54）；新文落点改为"step 4 第一个边界策略动作之前"；③ **Major 1（READ-N2 / REF-D1 落点 + 必要性弱化）** — 全文统一把"编排器 step 1 读字段列表"更正为"编排器 step 2 读字段列表"（step 1 仅 `<load>`，读字段动作位于 step 2 / L28）；同步更新 §1 涉及文件、§2.2.1 标题、§2.3.3 标题与操作、§2.8.1 ADR-D1、§3.1 DoD、§4 回滚 6 处；并补一句"READ-N2 是编排器/Limited 平台显式字段声明，不是 P3 内部读 phase_history 的硬前提"，避免实施者误判；④ **Major 2（§2.5 范围描述自相矛盾）** — 把"只允许 O7/O8 字段名替换、不允许任何其他改动"改为"只允许 REF-D5 + ANCHOR-N1 两类改动"，与 v1.1 后文 ANCHOR-N1 + DoD 行变动数 ≤ 3 硬上限自洽；⑤ **Minor（fixture 改名 + DoD grep 口径）** — fixture `p3-reentry-with-snapshot-but-no-history.yaml` → `p3-reentry-null-fanout-with-phase-history.yaml`（与"fanout_mode=null + phase_history 含末项"内容语义一致），同步更新 §1 涉及文件 / §2.10.6 操作 / `test_p3_reentry_replay.py` FIXTURE 路径 / DoD 共 4 处；O7 DoD `命中 0 处（仅注释允许提及）` 改为 `非注释行命中 0 处`，避免逻辑矛盾。**结构不变**：变更点编号、类别、数量、工作量、CI 自检表、Reviewer 议题全部维持 v1.1 形态；本次仅对**描述层**做精确化修订，不动方案设计。 |
