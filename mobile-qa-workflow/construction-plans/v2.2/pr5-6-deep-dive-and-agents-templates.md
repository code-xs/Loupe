# PR-5+6 · Deep-Dive 默认落盘 + agents/templates 治理（v2.2 实施期合并施工单）

> **主文档**：[`../../QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md`](../../QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md) §3 PR-5 / §3 PR-6 / §4
> **子文档骨架**：[`README.md` §2](./README.md)
> **协议依赖**：附录 C **D1 / D9 / D14 / D19**（PR-5 侧）+ 主文档 §3 PR-6 评审重点（C2-wrapper / C9-template）
> **强前置 PR**：PR-1（schema 协议层）已合入；PR-2 / PR-3 / PR-4 与本 PR 无字段依赖（拓扑允许并行；D9 顺序在 PR-3 之后、PR-7 之前）
> **Review 基线**：合入 [`pr5-6-deep-dive-and-agents-templates-REVIEW-2026-04-20.md`](./pr5-6-deep-dive-and-agents-templates-REVIEW-2026-04-20.md) **全部 4 项 findings + 1 附注**（1 Critical + 3 Major + 1 次级一致性）。
> **状态**：✅ V1（v2.2，2026-04-20；初稿 v1 → V1 接纳 review 后重新发布）

---

## V1 修订摘要（合入 review 2026-04-20 的 4 项 findings + 1 附注）

> **审阅文档**：[`pr5-6-deep-dive-and-agents-templates-REVIEW-2026-04-20.md`](./pr5-6-deep-dive-and-agents-templates-REVIEW-2026-04-20.md)
> **审阅结论**：4 项 findings + 1 附注全部成立，本 V1 全部接纳并落地。下表给出每条的判定与修订动作。

| # | 严重度 | Finding 摘要 | V1 判定 | V1 修订动作 |
|---|---|---|---|---|
| 1 | 🔴 Critical | C9 模板"中间态/正态条件渲染"在当前协议层无支持机制：`<template-output>` 仅 file/template 两参，p6 成功/失败同模板，模板纯静态；初稿"按 verification_failure_type 选择是否渲染"自证不能 | ✅ **接纳（取方案 A）** | **重写 §2.B.3 模板段** — 删除"验证通过场景下可省略"与"中间态/正态切换下沉到本模板内由 phase 调用方根据 verification_failure_type 选择渲染"全部表述；明确 v4.1 范围内**三必填字段始终物理存在**：成功路径填 `N/A`（含 evidence/repro_path 标准 `N/A` 占位文本）、失败路径必填实际内容；保留"v4.2 条件渲染机制"作为遗留 #4 的 follow-up（不在本 PR 范围）。同步修订 §3.B 第 7-9 项 DoD 与 §3.D 用例 F 的"省略"语义 |
| 2 | 🟠 Major | §2.A.3 把"真实性"建立在原始命令 `grep -rn '<step-pause' ...` 上并写"实际命中 2 条"，但 raw grep 实际命中 5 行（含 p2 注释续行 3 处）；只有自检脚本 §5.A.5 偷偷加了 `^\s*<step-pause` 过滤才得 2 | ✅ **接纳** | **重写 §2.A.3 盘点真实性段** — 把过滤条件 `^\s*<step-pause` **前置**到盘点段而非藏在 §5；显式列出 raw grep 5 行命中明细（p2 L50/L53/L77/L78 + p4 L136），并说明"过滤后真实开标签命中 = 2"；§3.A 第 4 项 DoD 的"当前 grep `<step-pause` 命中数 = 2"统一改写为"过滤后命中数 = 2，过滤命令同 §5.A.5"；统一盘点方法与 PR-8 CI 验收方法的语义 |
| 3 | 🟠 Major | "6 文件"与 §4.D commit 3（README + 主文档 §4 联动）口径不一致；当前仓库基线两处索引已被 PE 阶段联动小修过，commit 3 没有可提交内容 | ✅ **接纳** | **重写 §1 元信息"涉及文件"行 + §4.D + 新增 §3.C 第 8 项** — §1 涉及文件保持"6 个（实施期改动文件）"，但加注"另含 PE 阶段已合入到 main 的 2 处 index-only 联动（README L11 / 主文档 §4 PR-5/PR-6 行），不计入实施期 PR 文件数与工作量"；§4.D 拆 commit 策略改写为"基于当前 main 基线，本 PR 仅需 commit 1（§A）+ commit 2（§B）共 2 个子提交；commit 3 已由 PE 阶段联动小修在 main 上完成，**不再需要在本 PR 内提交**；若 review 确认本 PR 应基于 PE 联动前的旧基线，再补 commit 3"；§3.C 新增"基线对齐断言"DoD 一项 |
| 4 | 🟠 Major | 子文档两处把"allowlist 缺失时 PR-8 CI 应降级 warn 不阻塞"写为既定前提，但主文档 §3 PR-8 评审重点 6 + §5.1 明确"必须存在且非空"（缺失即 fail）；擅自代 PR-8 决策 CI 行为 | ✅ **接纳** | **删除 §2.A.3 兼容性影响第 2 段与 §4.A 影响范围内的"PR-8 应自身具备降级 warn 鲁棒性"两处表述**；改写为中性："allowlist 缺失后的 PR-8 CI 行为以主文档 §3 PR-8 评审重点 6 + §5.1 第 17 项口径为权威（当前定义：必须存在且非空，缺失则 fail）；本 PR 回滚后预期 PR-8 CI fail，**需联动评估是否同步回滚 PR-8**，不在本 PR 内承诺任何 CI 降级语义" |
| 附注 | 🟢 次级一致性 | 子文档多次引用"§2.2 联动小修"，但本子文档无 §2.2 章节（"§2.2"是上游 PE 文档章节号泄漏） | ✅ **接纳** | **全局替换"§2.2 联动小修"** → "PE 阶段 README + 主文档 §4 索引联动"或"§4.D 末尾 commit 3 描述"，按上下文选择更准确的指向；移除子文档对 PE 文档章节号的所有隐式依赖 |

> **V1 不引入的范围扩张**：
> - 不引入 `<template-output>` 协议层条件渲染机制（C9 方案 B 留作 v4.2 遗留 #4 候选；本 V1 取方案 A）
> - 不修改 PR-8 子文档（即使 Finding 4 涉及 PR-8 CI 行为口径，仅在本子文档内删除越权假设，不去 PR-8 落地实现）
> - 不修改主文档 §3 PR-5 / PR-6 描述本体（与初稿一致）
> - 不动 PE 阶段已合入 main 的 README + 主文档 §4 索引联动（Finding 3 修订动作仅在本子文档内调整口径，不再二次修改 README / §4）
> - 不引入 v4.2 遗留新条目（C9 方案 B 候选挂在已有 v4.2 遗留 #4 下，不新建）
>
> **V1 的承诺边界**：本 PR 在物理上仍是 6 文件 / 0.95d / 2 个 commit 子提交（commit 3 已由 PE 联动小修完成）；C9 在 v4.1 范围内只承诺"模板增段 + 成功路径 N/A 占位"的方案 A 闭环，不再声称"完整 C9 闭环"；allowlist 盘点 / DoD / 自检脚本三处的 grep 语义已统一为"`^\s*<step-pause` 过滤后命中"。

---

## 0. 实施期合并声明

### 0.1 合并依据（全部来自主文档既定事实，非新决定）

| 维度 | 客观事实 | 主文档锚点 |
|---|---|---|
| 字段依赖 | PR-6 与 PR-1~5 无字段依赖 | §2.1 拓扑约束第 5 条 |
| 合入顺序 | D9 中 PR-5 / PR-6 均在 PR-7 / PR-8 之前，相对顺序无强约束 | 附录 C D9 |
| 工作量 | PR-5 0.45d + PR-6 0.5d = 0.95d，落在 0.5-1.5d 合理 PR 区间 | §1.1.3 + §3 PR-5/PR-6 |
| 文件量 | 6 个文件（PR-5 3 个 + PR-6 3 个），与 PR-1（4 个）/ PR-4（3 个）同量级 | §3 PR-5 / §3 PR-6 |

### 0.2 合并不引入的 5 项范围扩张红线

- ❌ **不修改主文档 §3 的 8 PR 切分**：主文档保持设计层叙事；合并是 §4 索引层的实施决定
- ❌ **不动 PR-7 / PR-8 任何范围**：PR-7 是聚合派生（必须等 PR-3/4/5 全部合入后再 rebase）、PR-8 是 CI 收尾，均不可前置
- ❌ **不引入主文档未登记的修复条目**：合并不是"机会扩张"，本 PR 修复条目严格 = B3 + C11 phase 内盘点（v4.2 遗留 #6 登记）+ C2-wrapper + C9-template + D19 allowlist
- ❌ **不享受任何"合并红利预算"**：工作量仍按 0.95d 计入主文档 §1.1.3，buffer 0.3d 不变
- ❌ **不修改主文档附录 C 的 D1-D19 任何决定**

### 0.3 双层 DoD / 双套回滚 / 双 Reviewer 归属保留

为确保**单边回滚能力**与**评审责任清晰**，本 PR 在物理上是一个 commit / 一个 merge，但在文档结构上严格保留 PR-5 / PR-6 双层叙事：

- §2 文件级 diff：`§2.A` = 原 PR-5 / `§2.B` = 原 PR-6
- §3 DoD：`§3.A` = 原 PR-5 / `§3.B` = 原 PR-6 / `§3.C` = 跨 §A/§B 联合断言
- §4 回滚：`§4.A` 单独回滚 PR-5 / `§4.B` 单独回滚 PR-6 / `§4.C` 整体回滚 / `§4.D` 单边回滚操作指引
- §5 grep 自检：按 §A / §B 分组命令清单

**Reviewer 必看分配**：
- **phase owner**：必看 §2.A + §3.A + §4.A + §5.A（B3 落盘 + 现状盘点 + allowlist + D14 反向断言）
- **agents/templates owner**：必看 §2.B + §3.B + §4.B + §5.B（wrapper Schema-Violation + 中间态模板 + 三必填字段）
- **协议 owner（任一 Reviewer 兼任）**：必看 §3.C 双归属断言（D14 / D19 守门是否未被合并叙事稀释）

---

## 1. PR 元信息

| 项 | 值 |
|---|---|
| 分支命名 | `feat/qa-workflow-v4.1-pr5-6-deep-dive-and-agents-templates` |
| Base | PR-1 合入后的 `main`（PR-2/3/4 与本 PR 无字段依赖，rebase 无强约束；建议 rebase 到当前 `main` HEAD） |
| 层级 | 🟠 phase 层（§A）+ 🟡 agents/templates 层（§B）— **双层级** |
| 目标合入顺序 | **PR-1 → PR-2 → PR-4 → PR-3 → PR-5+6 → PR-7 → PR-8**（D9，PR-5+6 合并占据原 PR-5 / PR-6 两个槽位） |
| Reviewer | **2 名**：① phase owner（必看 §2.A + §3.A + §4.A + §5.A）；② agents/templates owner（必看 §2.B + §3.B + §4.B + §5.B）；任一兼任协议 owner（必看 §3.C） |
| 关联 issue | v4.1 主修复条目 / 配套：**B3**（Deep-Dive F1/F2/F3 默认落盘）、**C11 phase 内盘点**（v4.2 遗留 #6 登记，本 PR 仅盘点不修改）、**C2-wrapper**（shared-arbiter / shared-challenger Schema-Violation）、**C9-template**（verification-report 中间态段）、**D19**（`legacy-phase-step-pause-allowlist.txt` 实体化交付） |
| 工作量 | **0.95d**（PR-5 0.45d + PR-6 0.5d；与主文档 §3 一致，无合并红利） |
| 涉及文件 | **6 个实施期改动文件**，按 §A / §B 分组：<br/>**§A · 原 PR-5（3 个）**：`functionality-deep-dive/core/default-config.yaml`（修改）/ `core/default-config.yaml`（修改）/ `mobile-qa-workflow/scripts/legacy-phase-step-pause-allowlist.txt`（**新增**）<br/>**§B · 原 PR-6（3 个）**：`agents/shared-arbiter-base.md`（修改）/ `agents/shared-challenger-base.md`（修改）/ `templates/verification-report.md`（修改）<br/>**另含 PE 阶段已合入到 main 的 2 处 index-only 联动**（V1 / Finding 3 接纳）：`mobile-qa-workflow/construction-plans/v2.2/README.md` L11 + `mobile-qa-workflow/QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md` §4 PR-5/PR-6 索引行；这 2 个文件**不计入本 PR 实施期文件数与 0.95d 工作量**（PE 阶段已完成、当前基线已对齐），仅在回滚预案 §4.C 中作为联动评估对象出现 |
| 不在本 PR 范围 | ① **PR-7 入口文档同步**（SKILL.md / system-prompt.md / PLATFORM-GUIDE.md，由 PR-7 承担） ② **PR-8 CI 守门实现**（包括 D14/D15/D16/D19 的 grep 脚本与 GitHub Actions，本 PR 仅交付 allowlist 文件，由 PR-8 消费） ③ **M11**（verification-report 三类回流分类，v4.2 遗留 #4） ④ **M14**（knowledge-card L3-Dynamic 双写去重，v4.2 遗留 #4） ⑤ **主文档修订**（§3 PR-5/PR-6 描述本体不动；附录 C D1-D19 不动；仅 §4 索引层做合并指向） ⑥ **修改 phase 内现存 `<step-pause>` 属性**（v4.2 遗留 #6 一并迁出，本 PR 仅盘点登记） ⑦ 任何 `core/**` 改动（PR-1/PR-2 范围） ⑧ 任何 `phases/p2,p3,p4,p6` 改动（PR-2/3/4 范围） ⑨ M16 全量 schema CI（v1.2.1 §七 #20，已延后） |

---

## 2. 文件级 diff 列表

> 下文每个变更点格式：**原文锚点（startLine:endLine:filepath）→ 新文 → 修订理由 → 兼容性影响**。

### 2.A 原 PR-5 范围（B3 / C11 phase 内盘点 / D19 allowlist）

#### 2.A.1 变更点 PR5-1 · `functionality-deep-dive/core/default-config.yaml`（B3 默认值翻 true）

**原文（行号锚点 L16-18）**：

```16:18:mobile-qa-workflow/functionality-deep-dive/core/default-config.yaml
emit_environment_factor_report: false
emit_topology_report: false
emit_concurrency_report: false
```

**新文**：

```yaml
# v4.1 / B3 修复：F1/F2/F3 默认产物落盘（Deep-Dive F4 isolation-debate 强依赖三件套作为输入）
# 之前 false 导致 F4 入参缺失，与 v1.2.1 §三 B3 描述一致；翻 true 让 F1-F3 默认输出物理文件。
emit_environment_factor_report: true
emit_topology_report: true
emit_concurrency_report: true
```

**修订理由**：

- **B3（v1.2.1 §三 B3 / §七 #3）**：`emit_*` 三个开关默认 `false` 导致 Deep-Dive F1/F2/F3 不落盘，F4 isolation-debate 阶段读取 `output_*` 为 null 时无法对照拓扑/并发/环境因子证据，造成"调试可见但产物丢失"的 B3 主链路 bug。本变更点是 B3 的最小表层修复（v4.1 范围口径 D4：仅做表层默认值翻转，主子配置键名映射统一延后 v4.2 遗留 #1）。
- **范围严格性**：本变更点**仅翻三个布尔默认值**，不动 `output_*` 字段（运行时由 phase 写入实际路径）、不动其它 `emit_*` 之外的字段、不重命名（D4 决定）。

**兼容性影响**：

- 已有 issue 实例（schema_version=3 → 4 已迁移完成）：F1/F2/F3 重新进入会从 default-config 复制 `emit_*` 默认值；旧实例若已显式覆盖为 `false`，覆盖优先，不受影响。
- 全新 issue 实例：直接生效，F4 入参齐全。
- 回滚兼容：`git revert` 后默认值回 `false`，行为退回 v3，B3 复发。

---

#### 2.A.2 变更点 PR5-2 · `core/default-config.yaml`（B3 同步 + 漂移注释）

**原文（行号锚点 L21-42）**：

```21:42:mobile-qa-workflow/core/default-config.yaml
output_environment_factor_report: null
output_topology_report: null
output_concurrency_report: null
output_deep_dive_rca: null
output_deep_dive_summary: null
output_defensive_fix_design: null

env_file_system: true
env_git: true
env_lint_tools: true
env_subagent: true
routing_policy_version: "abc-1"
active_fanout_policy: "dynamic-p3-p4"
active_fix_strategy_policy: "risk-and-confidence"
output_runtime_compat_report: null
output_reroute_trace: null

deep_dive_optional_artifacts:
  environment_factor_report: true
  deep_dive_topology: true
  concurrency_analysis_report: true
```

**新文**（在 `deep_dive_optional_artifacts:` 块上方追加 v4.2 遗留 #1 漂移注释；不改任何键值）：

```yaml
output_environment_factor_report: null
output_topology_report: null
output_concurrency_report: null
output_deep_dive_rca: null
output_deep_dive_summary: null
output_defensive_fix_design: null

env_file_system: true
env_git: true
env_lint_tools: true
env_subagent: true
routing_policy_version: "abc-1"
active_fanout_policy: "dynamic-p3-p4"
active_fix_strategy_policy: "risk-and-confidence"
output_runtime_compat_report: null
output_reroute_trace: null

# ⚠️ v4.2 遗留 #1（D4 决定 / 主文档 §1.2.2）：
# 本块键名为 environment_factor_report / deep_dive_topology / concurrency_analysis_report，
# 子配置 functionality-deep-dive/core/default-config.yaml 的对应键名为
# emit_environment_factor_report / emit_topology_report / emit_concurrency_report。
# 两套命名存在键名漂移；v4.1 PR-5 仅做 B3 表层修复（子配置三个 emit_* 默认值翻 true），
# 主子键名映射统一机制延后到 v4.2 遗留 #1（关联 M9）。
deep_dive_optional_artifacts:
  environment_factor_report: true
  deep_dive_topology: true
  concurrency_analysis_report: true
```

**修订理由**：

- **B3 主子同步（v1.2.1 §三 B3 Compatibility 方案 A）**：本变更点的实际语义影响为 0（键值未改），**仅注入注释**作为 v4.2 遗留 #1 的现场登记，避免后续 reviewer 质疑"为什么主子键名不一致 / 为什么 PR-5 只翻子配置不动主配置"。
- **D4 范围声明**：键名映射统一明确属 v4.2，不在本 PR 范围；注释把这一决定锚定在文件原位，便于 v4.2 实施时 grep 定位。

**兼容性影响**：

- 0 行为变更（仅注释）；100% 向前兼容；回滚 `git revert` 后注释丢失但功能等价。

---

#### 2.A.3 变更点 PR5-3 · `mobile-qa-workflow/scripts/legacy-phase-step-pause-allowlist.txt`（**新增**，D19）

**原文**：文件不存在。

**新文**（基于本 PR 起草前实际 grep 结果生成）：

```text
# legacy-phase-step-pause-allowlist.txt
#
# 用途（D19 / 主文档附录 C / 主文档 §5.1）：
# - PR-8 CI 消费本文件实现 D14 守门（phases/** 与 functionality-deep-dive/phases/** 内
#   <step-pause> 命中必须出现在本白名单内；不在白名单的视为新增 → CI fail）
# - 本白名单 = "v2.1 之前已存在、登记为 v4.2 遗留 #6 待整改" 的 phase 内 step-pause 全集
# - v4.2 D14 整改完成时，本文件应被清空并删除
#
# 维护规约：
# - 任何向 phases/** 新增 <step-pause> 的提案一律按 D14 改为 "phase 设
#   current_state + ABORT，编排器 step 4 新 case 触发 step-pause" 模式；
#   绝不通过往本白名单追加新条目来"绕过" D14
# - 条目修改（如位置漂移）不视为新增，但需在同一 PR 内同步更新本文件
#
# 条目格式：<repo-relative-path>:<line>:<semantic-id>
# - <line> 为标签起始行（容许 ±5 行漂移；CI 仅校验文件路径与 semantic-id）
# - <semantic-id> 为人类可读的步骤定位（如 "step4-spec-uncertain"）
#
# 现状盘点（grep '<step-pause' mobile-qa-workflow/phases/ \
#                                 mobile-qa-workflow/functionality-deep-dive/phases/）：
# - 共 2 条 phase 内 step-pause；functionality-deep-dive/phases/** 0 条
#
# v4.2 遗留 #6 整改候选：以下 2 条全部迁移到编排器 step 4 case 路由

mobile-qa-workflow/phases/p2-spec-definition.md:53:step4-spec-uncertain
mobile-qa-workflow/phases/p4-fix-design.md:136:step6-fix-design-confirm
```

**修订理由**：

- **D19（v2.2 主文档附录 C）**：本文件是 PR-8 CI 实施 D14 守门的**权威输入**。主文档 §5.1 明确 "step-pause 调度作用域（v2.1 D14 硬守门）：grep `phases/**/*.md` 与 `functionality-deep-dive/phases/**/*.md` 中的 `<step-pause`，所有命中必须出现在 `mobile-qa-workflow/scripts/legacy-phase-step-pause-allowlist.txt` 中"，本变更点交付该文件首版。
- **盘点真实性（v2.2 D19 + v2.1 D14；V1 / Finding 2 接纳：raw grep 与过滤 grep 必须区分）**：

  现状盘点的**权威方法**是"只统计真实 XML 开标签，不统计注释/说明文字中的字面量 `<step-pause>`"，即必须使用过滤命令 `^\s*<step-pause`，与 §5.A.5 自检脚本及 PR-8 CI 验收方法严格同源。

  **过滤后命令（权威）**：

  ```bash
  grep -rnE '^\s*<step-pause' mobile-qa-workflow/phases/ \
                              mobile-qa-workflow/functionality-deep-dive/phases/
  ```

  **过滤后实际命中（= 2，allowlist 首版条目数严格匹配）**：
  - `mobile-qa-workflow/phases/p2-spec-definition.md:53` — Spec-Uncertain（v3 已有，PR-3 V1 §0 finding #4 已声明保持不动）
  - `mobile-qa-workflow/phases/p4-fix-design.md:136` — Fix Design 论证后确认 step-pause（Continue/Revise）
  - `functionality-deep-dive/phases/**` — **0 条**

  **raw grep 命令（仅供对比，不作为盘点依据）**：

  ```bash
  grep -rn '<step-pause' mobile-qa-workflow/phases/ \
                          mobile-qa-workflow/functionality-deep-dive/phases/
  ```

  **raw grep 实际命中 = 5 行**（含 PR-3 V1 在 p2 内引入的 3 处注释续行 / 说明文字字面量；这些**不是**真实 XML 开标签，**不应**计入 allowlist）：

  | # | 文件 | 行号 | 性质 | 是否计入 allowlist |
  |---|---|---|---|---|
  | 1 | `phases/p2-spec-definition.md` | L50 | 注释行 `<!-- ⚠️ v4.2 遗留 #6：本内联 <step-pause> 与编排器...` | ❌ 不计入 |
  | 2 | `phases/p2-spec-definition.md` | L53 | **真实开标签** `<step-pause title="Spec 存在歧义..."` | ✅ 计入 |
  | 3 | `phases/p2-spec-definition.md` | L77 | 注释续行 `D14 合规：本 PR **不新增** <step-pause>；phase 内现存的 1 处` | ❌ 不计入 |
  | 4 | `phases/p2-spec-definition.md` | L78 | 注释续行 `Spec-Uncertain <step-pause> 作为 v4.2 遗留 #6 保持不动。` | ❌ 不计入 |
  | 5 | `phases/p4-fix-design.md` | L136 | **真实开标签** `<step-pause title="Fix Design 四重论证完成..."` | ✅ 计入 |

  **盘点方法 vs CI 验收方法语义同源**：本段权威方法（`^\s*<step-pause`）与 §5.A.5 自检 / PR-8 CI 守门规则使用**完全相同**的过滤模式；DoD §3.A 第 4 项的"过滤后命中数 = 2"也遵循同一语义，不存在"人工盘点通过、CI 数量不一致"的争议风险。

- **与主文档描述的事实差异**（必须如实登记，避免 review 质疑）：
  1. 主文档 §3 PR-5 描述 "至少包含 phases/p2-spec-definition.md Spec-Uncertain / phases/p4-fix-design.md **step 5** / functionality-deep-dive/phases/f4-isolation-debate.md 中断决策等"。**实际**：p4 step-pause 位于 step **6**（不是 step 5；语义为"四重论证完成确认"，非 step 5"是否进入修复"）；f4-isolation-debate.md 当前**不含** `<step-pause>`。
  2. 本盘点表如实反映现状（2 条），不向白名单追加"主文档曾推测但实际不存在"的条目。
  3. 主文档 §3 PR-5 描述行的 step 编号 / f4 推测与实际不一致 → **follow-up：建议 PR-7 文档同步阶段或独立 doc-fix 小 PR 修订主文档；本 PR 不修主文档以避免 scope creep**（与 PR-3 V1 §0 finding #3 同款处理基调）。

**兼容性影响**：

- 文件首次新增，无回滚兼容性问题；`git revert` 后文件被删除，PR-8 CI 失去 D14 守门权威输入。**allowlist 缺失后的 PR-8 CI 行为以主文档 §3 PR-8 评审重点 6 + §5.1 第 17 项为权威**（当前主文档口径：allowlist 必须"存在且非空"，缺失即 fail）；本 PR **不承诺**任何 CI 降级语义，也**不替** PR-8 决策"缺失时是否降级 warn"（V1 / Finding 4 接纳，删除越权假设）。
- 与 PR-3 / PR-4 解耦：PR-3 V1 §3.1 第 1 项 DoD 引用本文件；若本 PR 晚于 PR-3 合入，PR-3 的 DoD 仍可在 PR-3 PR description 勾选完成（grep 命中 1 即可），无需本文件已合入。

---

#### 2.A.4 PR description 必含"phase 内 step-pause 现状盘点表"（C11 phase 内盘点登记 v4.2 遗留 #6）

PR description 必须包含与 §2.A.3 allowlist 条目**1:1 对应**的现状盘点表（markdown 表格形式）：

| # | 文件 | 行号 | semantic-id | 触发场景 | v4.2 整改方案（D14） |
|---|---|---|---|---|---|
| 1 | `phases/p2-spec-definition.md` | L53 | `step4-spec-uncertain` | step 4 Spec 来源冲突，列出多种 Expected Behavior 候选 | phase 改写 `current_state = Spec-Uncertain + ABORT`；编排器 step 4 case Spec-Uncertain 已存在，复用即可 |
| 2 | `phases/p4-fix-design.md` | L136 | `step6-fix-design-confirm` | step 6 Fix Design 四重论证完成后的人工确认（Continue/Revise） | 编排器 step 4 当前**不含** `case if="Fix-Confirming"`；v4.2 需新增此 case + 在 PR-1 顶层镜像白名单或 user_inputs 加 `fix_design_confirm_action` 字段 |

**强制声明**：本 PR 不修改这 2 处现存 `<step-pause>` 的任何属性、文本或位置；修改属于 v4.2 遗留 #6 范围。

---

### 2.B 原 PR-6 范围（C2-wrapper / C9-template）

#### 2.B.1 变更点 PR6-1 · `agents/shared-arbiter-base.md`（C2 缺 `base_score` 输出 `[Schema-Violation]`）

**原文（行号锚点 L5-11）**：

```5:11:mobile-qa-workflow/agents/shared-arbiter-base.md
## 输入契约
- `scene`: `RCA` / `FIX` / `DEEP_DIVE`
- `candidate_set`: Investigator、Fix-Proposer、专项分析角色的候选结论集合
- `challenge_reports`: Challenger 或专项挑战结果
- `comparison_focus`: 本次裁定的关键对比维度
- `base_score`: 候选结论基础评分或原始置信度
```

**新文**（在"## 输入契约"段尾追加"## 入参完整性校验（C2 wrapper）"小节）：

```markdown
## 输入契约
- `scene`: `RCA` / `FIX` / `DEEP_DIVE`
- `candidate_set`: Investigator、Fix-Proposer、专项分析角色的候选结论集合
- `challenge_reports`: Challenger 或专项挑战结果
- `comparison_focus`: 本次裁定的关键对比维度
- `base_score`: 候选结论基础评分或原始置信度

## 入参完整性校验（v4.1 / C2 wrapper）

> 本节为 C2 修复的 wrapper 端实现：调用方（PR-4 P3/P4 已落地）必须在 invoke 前注入
> `base_score`；若 wrapper 在执行前检测到该入参缺失或类型非数值，必须**立即停止推理**
> 并输出标准化错误标签，便于 PR-8 CI / 后续 trace 定位调用方缺陷。

执行任何"统一裁定协议"步骤之前，必须按以下顺序自检入参：

1. 若 `base_score` 缺失（未提供 / 为 null / 为空字符串）：
   - 输出固定文本：`[Schema-Violation: missing base_score]`
   - 不再继续后续推理；不产出 `## Arbiter Ruling` 任何字段
2. 若 `base_score` 存在但非数值（无法被解析为浮点数）：
   - 输出固定文本：`[Schema-Violation: invalid base_score type]`
   - 不再继续后续推理
3. `scene` / `candidate_set` / `challenge_reports` / `comparison_focus` 缺失暂不视为
   Schema-Violation（v4.1 范围口径 D5：仅 C2 必修 `base_score`，其它入参治理延后 v4.2）

> **校验失败的语义**：`[Schema-Violation: missing base_score]` 是调用方契约错误，
> 不是裁定不确定（不应转为 `[Arbiter-Uncertain]` 或 Human-Review）；调用方必须修复后重试。
```

**修订理由**：

- **C2-wrapper（v1.2.1 §三 C2 Fix Sketch / §七 #5 wrapper 端）**：v3 的 arbiter 文档只声明 `base_score` 是输入契约，但 wrapper 在 LLM 执行时不做缺参检测，导致调用方（PR-3 之前的 P3/P4）忘记注入时 wrapper 会"硬编码 base_score = 0.5"或直接幻觉，污染 `final_confidence` 计算。本变更点把"必须存在 base_score"从隐式契约提升为显式失败标签。
- **C2 调用方端在 PR-4**：PR-4 已在 P3/P4 调用 arbiter 时显式注入 `base_score`（**C2 角色驱动**，详见主文档 §3 PR-4）；本变更点是 wrapper 端的"防御性兜底"，与 PR-4 调用方端构成**完整 C2 闭环**。
- **范围严格性**：仅校验 `base_score`（C2 主修目标）；其它入参（`scene` / `candidate_set` 等）不在本次范围（v4.1 D5 范围口径）。

**兼容性影响**：

- 调用方 PR-4 已落地：本变更点 100% 兼容；wrapper 检测路径永远不命中（DoD §3.B 第 3 项联调验证）。
- 调用方未落地（极端回滚场景）：wrapper 直接输出 `[Schema-Violation]` 标签 + 停止推理，调用方会观察到明确错误而非沉默幻觉，**比 v3 行为更安全**。
- `git revert` 后 wrapper 恢复 v3 沉默接收 → 与 v3 行为等价。

---

#### 2.B.2 变更点 PR6-2 · `agents/shared-challenger-base.md`（C2 缺 `confidence_input` 输出 `[Schema-Violation]`）

**原文（行号锚点 L5-11）**：

```5:11:mobile-qa-workflow/agents/shared-challenger-base.md
## 输入契约
- `scene`: `RCA` / `FIX` / `DEEP_DIVE`
- `dimension_set`: `rca-5d` / `fix-4a` / `deep-dive-7d`
- `target_list`: 被质疑对象列表；每个对象必须包含结论摘要、证据摘要与关键不确定性
- `supporting_context`: 引用的 Spec、RCA、Fix Design、专项报告或验证结论
- `confidence_input`: 被质疑对象原始置信度或原始评分
```

**新文**（在"## 输入契约"段尾追加"## 入参完整性校验"小节，与 arbiter 同构）：

```markdown
## 输入契约
- `scene`: `RCA` / `FIX` / `DEEP_DIVE`
- `dimension_set`: `rca-5d` / `fix-4a` / `deep-dive-7d`
- `target_list`: 被质疑对象列表；每个对象必须包含结论摘要、证据摘要与关键不确定性
- `supporting_context`: 引用的 Spec、RCA、Fix Design、专项报告或验证结论
- `confidence_input`: 被质疑对象原始置信度或原始评分

## 入参完整性校验（v4.1 / C2 wrapper）

> 本节为 C2 修复的 wrapper 端实现：调用方（PR-4 P3/P4 已落地）必须在 invoke 前注入
> `confidence_input`；若 wrapper 在执行前检测到该入参缺失或类型非数值，必须**立即停止推理**
> 并输出标准化错误标签。与 `agents/shared-arbiter-base.md` 同构。

执行任何"统一执行协议"步骤之前，必须按以下顺序自检入参：

1. 若 `confidence_input` 缺失（未提供 / 为 null / 为空字符串）：
   - 输出固定文本：`[Schema-Violation: missing confidence_input]`
   - 不再继续后续推理；不产出 `## Challenge Report` 任何字段
2. 若 `confidence_input` 存在但非数值：
   - 输出固定文本：`[Schema-Violation: invalid confidence_input type]`
   - 不再继续后续推理
3. `scene` / `dimension_set` / `target_list` / `supporting_context` 缺失暂不视为
   Schema-Violation（v4.1 范围口径 D5）

> **校验失败的语义**：`[Schema-Violation: missing confidence_input]` 是调用方契约错误，
> 不是质疑不确定；不应转为 `[No Issue Found]` 或 Human-Review；调用方必须修复后重试。
```

**修订理由 / 兼容性影响**：

- 与 §2.B.1 完全同构（C2 wrapper 端 challenger 一侧）；调用方注入 `confidence_input` 由 PR-4 落地，本变更点是 wrapper 防御性兜底，构成 C2 完整闭环的另一半。
- 范围严格性：仅校验 `confidence_input`，其它入参 v4.2 遗留。

---

#### 2.B.3 变更点 PR6-3 · `templates/verification-report.md`（C9 新增"中间态报告"段）

**原文（行号锚点 L92-104）**：

```92:104:mobile-qa-workflow/templates/verification-report.md
> **说明**：L3-Dynamic 各项在当前 AI 静态分析阶段无法完成，标记为 `[Pending-CI]`。
> 这些指标应由 CI 流水线在部署后自动收集，或由开发人员在真机验证阶段补充填写。
> L3-Dynamic 的 `[Pending-CI]` 状态不阻塞问题进入闭环，但应在 Knowledge Card 中记录需 CI 回填。

---

### 验证总结
- **L1 通过**: [是/否]
- **契约溯源交叉验证**: [PASS/WARNING/FAIL/SKIPPED]
- **L2 通过**: [是/否]
- **L3-Static 通过**: [是/否]
- **L3-Dynamic 状态**: [Pending-CI]
- **总体判定**: [L1+L2+L3-Static 全部通过 → 进入闭环 / 未通过 → 回退到 Phase 4]
- **回退原因**（若未通过）: [具体说明哪层哪项未通过，以及建议的修复方向]
```

**新文**（V1 / Finding 1 接纳后口径：在"### 验证总结"段**之前**插入"### 中间态报告（v4.1 范围 — 始终物理存在；成功填 N/A，失败必填）"新段；不动其他段落）：

```markdown
> **说明**：L3-Dynamic 各项在当前 AI 静态分析阶段无法完成，标记为 `[Pending-CI]`。
> 这些指标应由 CI 流水线在部署后自动收集，或由开发人员在真机验证阶段补充填写。
> L3-Dynamic 的 `[Pending-CI]` 状态不阻塞问题进入闭环，但应在 Knowledge Card 中记录需 CI 回填。

---

### 中间态报告（v4.1 范围 — 始终物理存在；成功填 N/A，失败必填）

> **协议层现状声明（V1 / Finding 1 接纳 / 方案 A）**：
> 当前 `<template-output>` 在 `core/core-rules.xml` 仅有 `file` / `template` 两个参数（无模式 / 变量绑定 / 条件块 / 分支渲染能力），P6 成功与失败路径调用同一模板，模板本身为静态 markdown。
> 因此 v4.1 范围**不能**实现"成功路径不渲染本段"的条件渲染；本段在所有验证场景下均会物理出现于生成的 verification-report.md。
> v4.1 取**方案 A**：三必填字段始终物理存在，**成功路径填标准 `N/A` 占位**、**失败路径必填实际内容**。"协议层条件渲染机制"（方案 B）作为 v4.2 遗留 #4 的 follow-up 候选（不在本 PR 范围）。
>
> **三必填字段**（缺一项视为 C9 校验失败 — 无论成功/失败场景；成功场景的 `N/A` 占位也算"已填"）：

- **failure_classification**: 失败分类
  - 成功场景填：`N/A (verification passed)`
  - 失败场景必须从以下集合中选择并填写：
    - `L1-Spec-Mismatch`：L1 Spec 静态符合性验证未通过
    - `L1-Contract-Trace-Fail`：契约溯源交叉验证 FAIL
    - `L2-Regression-Risk`：L2 静态影响面或回归测试设计未通过
    - `L3-Static-Lint-Regress`：L3-Static Lint / 安全扫描出现新增问题
    - `L3-Static-Api-Compat`：L3-Static API 版本合规出现风险
    - `Root-Cause-Not-Closed`：验证发现修复未真正闭合根因（建议回退到 Phase 3 重做 RCA）
    - `Other`：上述均不适用时使用，并在 evidence 字段补充说明
- **evidence**: 失败证据
  - 成功场景填：`N/A (verification passed)`
  - 失败场景必须包含：
    - 触发失败的具体验证项（引用 L1/L2/L3-Static 表格中的行）
    - 期望值与实际值的并列对照（若适用）
    - 关联代码位置（`file:line`）或日志锚点
- **repro_path**: 复现路径
  - 成功场景填：`N/A (verification passed)`
  - 失败场景必须包含：
    - 复现步骤（最小化序列）
    - 复现环境（平台 / 版本 / 配置 / 必要前置数据）
    - 期望复现结果（与 evidence 中"实际值"一致）

#### 中间态报告 Markdown 块（成功场景）

```markdown
### 中间态报告

- **failure_classification**: N/A (verification passed)
- **evidence**: N/A (verification passed)
- **repro_path**: N/A (verification passed)
```

#### 中间态报告 Markdown 块（失败场景）

```markdown
### 中间态报告

- **failure_classification**: [L1-Spec-Mismatch / L1-Contract-Trace-Fail / L2-Regression-Risk / L3-Static-Lint-Regress / L3-Static-Api-Compat / Root-Cause-Not-Closed / Other]
- **evidence**:
  - [触发失败的验证项 + 期望/实际对照]
  - [关联代码位置 file:line 或日志锚点]
- **repro_path**:
  - [复现步骤]
  - [复现环境]
  - [期望复现结果]
```

> **与 PR-4 的协作**（主文档 §3 PR-4 v2.3 微调）：PR-4 在 `phases/p6-verification.md` 失败
> 分支已确保先调用 `<template-output file="…/verification-report.md" template="…/verification-report.md"/>`
> 再回流；成功分支同样调用同一模板。本 PR 不引入 `mode='intermediate'` 之类自定义 DSL 属性
> （v1.0 子文档曾设计但已撤销，避免与 `core/core-rules.xml` `<template-output>` DSL 漂移）。
> v4.1 不承诺"成功路径省略本段"的条件渲染语义；该能力归 v4.2 遗留 #4 候选（方案 B）。

---

### 验证总结
- **L1 通过**: [是/否]
- **契约溯源交叉验证**: [PASS/WARNING/FAIL/SKIPPED]
...
```

**修订理由**：

- **C9-template（v1.2.1 §三 C9 Fix Sketch / §七 #7 模板侧）**：v3 的 verification-report.md 没有"中间态报告"段，P6 失败回流时无产物可填，证据丢失。本变更点新增的三必填字段（`failure_classification` / `evidence` / `repro_path`）与 PR-4 在 P6 失败分支的 template-output 调用构成**v4.1 范围内的最大化 C9 闭环（方案 A）**。
- **不引入自定义 DSL（V1 / Finding 1 接纳）**：主文档 §3 PR-4 v2.3 微调明确"v1.0 子文档曾设计 `mode='intermediate'` 属性，已撤销，避免与 `<template-output>` DSL 漂移"；当前 `core/core-rules.xml` `<template-output>` 仅有 `file` / `template` 两参数，**不具备**任何条件渲染 / 变量绑定 / 分支能力。本 V1 不绕开协议层暗装条件渲染机制，改取**方案 A**：三字段始终物理存在，由 phase 调用方在写入时决定是 N/A 占位还是实际内容。
- **范围严格性**：仅新增"中间态报告"一段；**不动**契约溯源、L1/L2/L3 既有结构、Code Review Summary 等任何 v3 段落（M11 verification-report 三类回流分类延后 v4.2 遗留 #4 / D10 决定）。条件渲染机制（方案 B）作为 v4.2 遗留 #4 的 follow-up 候选。

**兼容性影响**：

- **成功场景（V1 行为差异）**：模板物理输出"中间态报告"段，三字段均为 `N/A (verification passed)`。与 v3 相比，verification-report.md 新增 ~6 行 N/A 占位；不影响 L1+L2+L3-Static 总体判定逻辑；下游 knowledge-card 等消费方读取 `failure_classification == "N/A (verification passed)"` 时应等价于"无失败"处理（不在本 PR 范围；若下游消费方需要适配，登记 PR-7 文档同步阶段或独立小 PR）。
- **失败场景**：模板物理输出"中间态报告"段，三字段为实际内容 → C9 数据产物从 0 到 1。
- 现有 issue 实例的历史 verification-report.md 文件不受影响（模板仅作用于新生成实例）。
- `git revert` 后模板回到 v3，C9 失败现场证据再次丢失；成功场景 N/A 占位也消失（行为与 v3 等价）。

---

## 3. PR-level DoD 子集（双层保留，不合并）

> 本 PR 在 PR description 必须勾选下列条目；横切契约（D14/D15/D16/D19 完整 CI 守门、迁移脚本、回归矩阵）见主文档 §5。

### 3.A 原 PR-5 DoD（B3 / 现状盘点表 / allowlist）

- [ ] **B3 默认值翻 true**：`functionality-deep-dive/core/default-config.yaml` 中 `emit_environment_factor_report` / `emit_topology_report` / `emit_concurrency_report` 三个键的 default 值均为 `true`（grep 验证）
- [ ] **B3 主子漂移注释**：`core/default-config.yaml` `deep_dive_optional_artifacts:` 块上方含 "v4.2 遗留 #1" 与 "D4 决定" 字样的注释（grep `v4.2 遗留 #1` 命中 ≥ 1）
- [ ] **D19 allowlist 文件存在且非空**：`mobile-qa-workflow/scripts/legacy-phase-step-pause-allowlist.txt` 物理存在，非注释行 ≥ 1
- [ ] **allowlist 与盘点表 1:1 对应（V1 / Finding 2 接纳，统一过滤后命中口径）**：allowlist 中非注释/非空行的条目数 = PR description 现状盘点表行数 = `grep -rnE '^\s*<step-pause' mobile-qa-workflow/phases/ mobile-qa-workflow/functionality-deep-dive/phases/ | wc -l` = **2**（"过滤后命中"，与 §2.A.3 权威盘点命令、§5.A.5 自检脚本、PR-8 CI 验收方法严格同源；raw `grep -rn '<step-pause' …` 会得 5，不能作为该 DoD 的判定基线）
- [ ] **allowlist 条目格式合规**：每条非注释行匹配 `<repo-relative-path>:<digit>+:<semantic-id>` 模式
- [ ] **PR description 含现状盘点表**：包含 §2.A.4 所示 markdown 表格（5 列：# / 文件 / 行号 / semantic-id / 触发场景 / v4.2 整改方案）
- [ ] **未修改任何 phase 文件内现存 `<step-pause>`**：grep diff 中 `phases/**/*.md` 与 `functionality-deep-dive/phases/**/*.md` 命中 0 行（v4.2 遗留 #6 不动）
- [ ] **未引入 phase 文件新增 `<step-pause>`**：本 PR diff 不向 `phases/**` / `functionality-deep-dive/phases/**` 添加任何 `<step-pause` 字符串
- [ ] **登记主文档与现状的事实差异**：PR description 必须显式说明"主文档 §3 PR-5 描述行的 p4 step 编号（实际 step 6 而非 step 5）与 f4 推测（实际 f4 不含 step-pause）与现状不一致 → follow-up 留给 PR-7 文档同步或独立 doc-fix"

### 3.B 原 PR-6 DoD（wrapper Schema-Violation / 中间态模板）

- [ ] **arbiter wrapper 校验存在**：`agents/shared-arbiter-base.md` 包含 `[Schema-Violation: missing base_score]` 字符串（grep 命中 ≥ 1）
- [ ] **arbiter wrapper 校验文本完整**：包含"立即停止推理"或等价语义 + "不产出 `## Arbiter Ruling`"
- [ ] **challenger wrapper 校验存在**：`agents/shared-challenger-base.md` 包含 `[Schema-Violation: missing confidence_input]` 字符串
- [ ] **challenger wrapper 校验文本完整**：包含"立即停止推理"或等价语义 + "不产出 `## Challenge Report`"
- [ ] **wrapper 范围严格性**：本 PR 仅校验 `base_score` / `confidence_input` 两个字段；不引入对 `scene` / `candidate_set` / `dimension_set` 等其它入参的校验（v4.1 D5 范围口径）
- [ ] **中间态报告段存在（V1 / Finding 1 接纳，方案 A）**：`templates/verification-report.md` 包含 "### 中间态报告（v4.1 范围 — 始终物理存在；成功填 N/A，失败必填）" 标题
- [ ] **三必填字段齐全**：中间态报告段同时含 `failure_classification` / `evidence` / `repro_path` 三字符串
- [ ] **failure_classification 7 个枚举完整**：包含 `L1-Spec-Mismatch` / `L1-Contract-Trace-Fail` / `L2-Regression-Risk` / `L3-Static-Lint-Regress` / `L3-Static-Api-Compat` / `Root-Cause-Not-Closed` / `Other`
- [ ] **成功/失败二态 markdown 块齐全（V1 / Finding 1 接纳）**：模板同时给出"成功场景"与"失败场景"两段示例 markdown 块；前者三字段均为字面量 `N/A (verification passed)`；后者三字段为占位变量；明确"v4.1 不承诺成功路径省略本段"
- [ ] **未引入 `<template-output>` 自定义属性**：本 PR diff 不出现 `mode='intermediate'` 或 `mode="intermediate"` 字符串（v2.3 微调撤销）
- [ ] **未引入协议层条件渲染机制（V1 / Finding 1 接纳）**：本 PR diff 不修改 `core/core-rules.xml`、不向 `<template-output>` 添加任何条件分支语法、不在 phase 调用方根据 `verification_failure_type` 选择是否调用 template-output；条件渲染（方案 B）作为 v4.2 遗留 #4 候选
- [ ] **未触碰 v3 既有段落**：契约溯源 / L1 / L2 / L3-Static / L3-Dynamic / 验证总结 / Code Review Summary 七段未修改
- [ ] **PR description 显式登记 M11 / M14 顺延**：必须列出"M11（verification-report 三类回流分类）/ M14（knowledge-card L3-Dynamic 双写去重）→ v4.2 遗留 #4，本 PR 不做"

### 3.C 跨 §A/§B 双归属断言（合并叙事不得稀释）

- [ ] **PR description 4 类修复条目独立列出**：B3 / C11 phase 内盘点 / C2-wrapper / C9-template 必须分 4 行列出，不能合并叙述为"Deep-Dive 与 agents/templates 治理"等模糊表述
- [ ] **未触碰 `core/**`**：grep diff 路径过滤 `^mobile-qa-workflow/core/` 命中 = 1（仅 `core/default-config.yaml` 注释；不动 `core-rules.xml` / `workflow.xml` / `workflow-status-template.yaml` / `config-schema.yaml`）
- [ ] **未触碰 `phases/p2,p3,p4,p5,p6` 内容（除盘点观察外）**：grep diff 路径过滤 `^mobile-qa-workflow/phases/` 命中 = 0
- [ ] **未修改主文档 §3 / 附录 C（除 PE 阶段已合入的 §4 索引行联动外）**：grep 当前 PR diff（不含 PE 阶段已在 main 上的索引联动 commit），路径过滤 `^mobile-qa-workflow/QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md` 命中 = 0；不触碰 §3 PR-5 / §3 PR-6 段落本体或附录 C 任何 D 决定
- [ ] **未修复 P2 step 9 `RCA-InProgress` 残留**：本 PR diff 不出现 `RCA-InProgress` 字符串（与 PR-3 V1 §3.1 同款基调，归属候选 v4.2 遗留 #8）
- [ ] **工作量记账与主文档一致**：PR description 工作量声明 "0.95d（PR-5 0.45d + PR-6 0.5d，无合并红利预算）"
- [ ] **双 Reviewer 必看分配显式声明**：PR description 必须显式分配 phase owner 必看 §A / agents owner 必看 §B / 任一兼任协议 owner 必看 §3.C
- [ ] **基线对齐断言（V1 / Finding 3 接纳）**：PR 提交前必须验证 `main` 基线上以下 2 处索引联动**已存在**（PE 阶段已合入），否则需补 commit 3：① `mobile-qa-workflow/construction-plans/v2.2/README.md` L11 出现 "PR-5 + PR-6（实施期合并）" 单行清单；② `mobile-qa-workflow/QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md` §4 PR-5 / PR-6 两行均指向 `pr5-6-deep-dive-and-agents-templates.md` 且加注 "**实施期合并**"。Reviewer 应使用 `git log --oneline -- README.md QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md` 验证 PE 联动 commit 已存在于 base 之前

### 3.D 动态用例（链接到主文档 §5.2）

- [ ] **用例 E（§5.2.5 B3 Deep-Dive 落盘）**：本 PR 是该用例关键前置 — 联调验证触发 F1→F2→F3→F4 链路后，`topology_report.md` / `concurrency_report.md` / `environment_factor_report.md` 三个文件物理存在
- [ ] **用例 F（§5.2.6 C9 P6 失败分支产物）**：本 PR 与 PR-4 的 P6 失败分支调用方共同支撑 — 联调验证 P6 验证失败后 `verification-report.md` 物理存在且包含 `failure_classification` / `evidence` / `repro_path` 三字段（V1 / Finding 1 接纳：方案 A 下成功路径同样物理存在三字段，值为 `N/A (verification passed)`；联调验证应同时覆盖成功 / 失败两条路径，并断言成功路径三字段值精确等于 `N/A (verification passed)`）

---

## 4. PR-level 回滚动作（双套独立回滚）

> 主文档 §7.5（PR-5）与 §7.6（PR-6）的两套描述在合并 PR 下需通过"拆 commit"或"分文件 revert"实现单边回滚能力。

### 4.A 原 PR-5 单独回滚

- **影响范围**：仅 §2.A 三个变更点
- **回滚后状态**：
  - F1/F2/F3 默认产物落盘关闭 → F4 输入再次丢失（B3 复发）
  - `core/default-config.yaml` 漂移注释丢失（v4.2 遗留 #1 标识弱化，0 行为影响）
  - `legacy-phase-step-pause-allowlist.txt` 文件被删除 → PR-8 CI 失去 D14 守门权威输入；按主文档 §3 PR-8 评审重点 6 + §5.1 第 17 项当前口径（必须存在且非空）→ **PR-8 CI 预期 fail**；**需联动评估是否同步回滚 PR-8**（V1 / Finding 4 接纳，不再擅自承诺降级 warn）
- **风险等级**：🟢 低（与主文档 §7.5 一致）
- **回滚命令**（按"拆 commit"策略，见 §4.D）：`git revert <PR-5-subcommit-sha>`

### 4.B 原 PR-6 单独回滚

- **影响范围**：仅 §2.B 三个变更点
- **回滚后状态**：
  - arbiter / challenger wrapper 不再校验 `[Schema-Violation]` → 调用方缺参时回到 v3 沉默接收（C2 wrapper 端失效；调用方端 PR-4 仍生效，但失去防御性兜底）
  - `templates/verification-report.md` 失去"中间态报告"段 → C9 失败现场证据再次丢失
- **风险等级**：🟢 低（与主文档 §7.6 一致）
- **回滚命令**：`git revert <PR-6-subcommit-sha>`

### 4.C 整体回滚（§A + §B 一起）

- **影响范围**：本合并 PR 6 个实施期文件
- **回滚后状态**：§4.A + §4.B 影响域并集
- **关于 README + 主文档 §4 索引联动的处置（V1 / Finding 3 接纳）**：这两处 index-only 联动**已由 PE 阶段在 main 上单独 commit 完成**，不在本 PR 的 commit 范围内；整体回滚本 PR 后，索引行**仍指向**已被 revert 的子文档，会出现"索引悬挂"。处置策略：
  - **若仅短期回滚（<1 周，预期重新前进）**：保留索引悬挂（README / §4 仍指向本子文档路径），文档侧短暂不一致可接受
  - **若长期回滚或废弃**：需**额外** revert PE 阶段的两个索引联动 commit（`git log --oneline -- README.md QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md` 定位 PE 联动 commit sha 后 `git revert <sha>`），让 README 与 §4 回到 "PR-5 / PR-6 → 待展开" 双行状态
- **风险等级**：🟢 低
- **回滚命令**：`git revert <commit-1-sha> <commit-2-sha>`（按 §4.D 拆 commit 后逐个 revert；不再有 commit 3）

### 4.D 单边回滚操作指引（强约束 — 拆 commit 策略；V1 / Finding 3 接纳）

为保证单边回滚能力，本合并 PR **必须**在物理 commit 层做如下拆分（在同一 PR / 同一 base 上的相邻 commit）：

- **commit 1（subcommit-pr5）**：仅包含 §2.A 三个文件变更（`functionality-deep-dive/core/default-config.yaml` + `core/default-config.yaml` + `mobile-qa-workflow/scripts/legacy-phase-step-pause-allowlist.txt`），message 前缀 `[PR-5/合并子提交]`
- **commit 2（subcommit-pr6）**：仅包含 §2.B 三个文件变更（`agents/shared-arbiter-base.md` + `agents/shared-challenger-base.md` + `templates/verification-report.md`），message 前缀 `[PR-6/合并子提交]`
- ~~commit 3（索引联动）~~：**当前基线下不需要**。README + 主文档 §4 PR-5/PR-6 索引行的联动已由 PE 阶段在 main 上单独完成（参见 §1 涉及文件行末的 "另含 PE 阶段已合入" 说明）；本 PR commit 范围内**无该项**。
  - **例外**：若 review 确认本 PR 应基于 PE 联动**之前**的旧基线（rebase 撤销 PE 联动），则需补回 commit 3，message 前缀 `[PR-5+6/索引层联动]`，仅含 README + 主文档 §4 索引行变更
  - 当前基线（已含 PE 联动）下，§3.C 第 8 项"基线对齐断言"DoD 必须勾选通过

**禁止**：把 §A / §B 文件混在同一个 commit 内（会破坏单边 `git revert` 能力）。

**Reviewer 必检**：评审时使用 `git log --oneline <base>..HEAD` 验证 **≥ 2** 个相邻 commit 且按 `[PR-5/...]` / `[PR-6/...]` 前缀分组；不满足则要求拆分后重提。若出现 commit 3（前缀 `[PR-5+6/索引层联动]`），必须同时验证 §3.C 第 8 项基线对齐断言**未通过**（即确实基于 PE 联动前的旧基线）。

---

## 5. §5.1 静态契约校验自检（grep 脚本 — 按 §A / §B 分组）

> 下列 grep 命令在 PR 提交前由开发者本地执行；PR-8 CI 落地后会以更结构化方式覆盖。

### 5.A 原 PR-5 范围 grep 自检

```bash
# A1. B3 子配置默认值翻 true（命中 = 3 行 "*: true"）
grep -n 'emit_environment_factor_report\|emit_topology_report\|emit_concurrency_report' \
    mobile-qa-workflow/functionality-deep-dive/core/default-config.yaml
# 期望：3 行命中，且每行末尾为 ': true'
# 失败诊断：若仍为 ': false'，B3 修复未生效；检查变更点 PR5-1

# A2. B3 主配置漂移注释存在
grep -n 'v4.2 遗留 #1\|D4 决定' mobile-qa-workflow/core/default-config.yaml
# 期望：≥ 1 行命中（"v4.2 遗留 #1" 与 "D4 决定" 至少各 1 处）
# 失败诊断：若 0 行命中，变更点 PR5-2 注释未注入或位置错误

# A3. allowlist 文件存在且非空
test -s mobile-qa-workflow/scripts/legacy-phase-step-pause-allowlist.txt && echo OK
# 期望：输出 OK（文件存在且大小 > 0）
# 失败诊断：文件不存在或空文件，D19 交付失败

# A4. allowlist 非注释行计数
grep -cv '^\(#\|$\)' mobile-qa-workflow/scripts/legacy-phase-step-pause-allowlist.txt
# 期望：2（与 A5 现状盘点 grep 命中数一致）
# 失败诊断：数字不等于 2 → 与现状盘点不一致；检查 §2.A.3

# A5. 现状盘点验证：phases 内 <step-pause> 真实开标签命中数
# 使用 ^\s*<step-pause 严格匹配"行首仅前导空白后立即出现 <step-pause"，
# 自动排除 PR-3 V1 在 p2 内引入的注释续行（含 "Spec-Uncertain <step-pause>" / "D14 合规：本 PR **不新增** <step-pause>" 等内联 mention）
grep -rnE '^\s*<step-pause' mobile-qa-workflow/phases/ \
    mobile-qa-workflow/functionality-deep-dive/phases/ 2>/dev/null \
    | wc -l
# 期望：2（p2-spec-definition.md:53 Spec-Uncertain + p4-fix-design.md:136 Fix Design Confirm）
# 失败诊断：
#   - 若 = 3 且新行在 functionality-deep-dive/phases/**：违反 D14，必须打回
#   - 若 ≠ 2 但仅 phases/p* 内：有人新增/删除了 phase 内 step-pause，需与 §2.A.3 allowlist 同步

# A6. allowlist 条目格式合规（path:line:semantic-id）
grep -v '^\(#\|$\)' mobile-qa-workflow/scripts/legacy-phase-step-pause-allowlist.txt \
    | grep -vE '^[^:]+:[0-9]+:[a-z0-9-]+$' \
    | wc -l
# 期望：0（所有非注释行都匹配 path:line:semantic-id 格式）
# 失败诊断：> 0 表示有不合规条目，PR-8 CI 将无法机械消费
```

### 5.B 原 PR-6 范围 grep 自检

```bash
# B1. arbiter wrapper Schema-Violation 文本
grep -n 'Schema-Violation: missing base_score' \
    mobile-qa-workflow/agents/shared-arbiter-base.md
# 期望：≥ 1 行命中
# 失败诊断：变更点 PR6-1 未落地或文本拼写错误

# B2. challenger wrapper Schema-Violation 文本
grep -n 'Schema-Violation: missing confidence_input' \
    mobile-qa-workflow/agents/shared-challenger-base.md
# 期望：≥ 1 行命中
# 失败诊断：变更点 PR6-2 未落地或文本拼写错误

# B3. wrapper 范围严格性反向断言（不应出现对其它入参的校验）
grep -nE 'Schema-Violation: missing (scene|candidate_set|challenge_reports|comparison_focus|dimension_set|target_list|supporting_context)' \
    mobile-qa-workflow/agents/shared-arbiter-base.md \
    mobile-qa-workflow/agents/shared-challenger-base.md
# 期望：0 行命中（v4.1 D5 范围口径，仅 base_score / confidence_input 必修）
# 失败诊断：若有命中，wrapper 范围越界，必须打回

# B4. 中间态报告段标题与三必填字段（V1 / Finding 1 接纳，方案 A）
grep -n '中间态报告\|failure_classification\|evidence\|repro_path\|N/A (verification passed)' \
    mobile-qa-workflow/templates/verification-report.md
# 期望：≥ 5 行命中（新标题 1 + 三字段各 ≥ 1 + N/A 占位文本 ≥ 1）
# 失败诊断：
#   - 缺三字段任一 → 变更点 PR6-3 不完整
#   - 缺 'N/A (verification passed)' → 成功场景 markdown 块未给出，方案 A 闭环未完成
#   - 仍出现 mode='intermediate' 或 mode="intermediate" → v2.3 撤销决定被违反

# B5. failure_classification 7 个枚举完整性
for kw in L1-Spec-Mismatch L1-Contract-Trace-Fail L2-Regression-Risk \
          L3-Static-Lint-Regress L3-Static-Api-Compat Root-Cause-Not-Closed Other; do
    grep -q "$kw" mobile-qa-workflow/templates/verification-report.md \
        || echo "MISSING: $kw"
done
# 期望：无 MISSING 输出
# 失败诊断：缺枚举值则 C9 分类不完整

# B6. 未引入 <template-output> 自定义属性反向断言
grep -nE "mode\s*=\s*['\"]intermediate['\"]" \
    mobile-qa-workflow/templates/verification-report.md \
    mobile-qa-workflow/phases/p6-verification.md 2>/dev/null
# 期望：0 行命中（v2.3 微调已撤销 mode='intermediate' 设计）
# 失败诊断：若有命中，与 <template-output> DSL 漂移；必须打回
```

### 5.C 跨 §A/§B 双归属反向断言

```bash
# C1. 未触碰 core/**（除 core/default-config.yaml 注释外）
git diff --name-only <base>..HEAD | grep '^mobile-qa-workflow/core/' \
    | grep -v 'mobile-qa-workflow/core/default-config.yaml'
# 期望：0 行命中
# 失败诊断：若命中 core-rules.xml / workflow.xml / workflow-status-template.yaml /
#         config-schema.yaml 任一文件，越界到 PR-1 / PR-2 范围，必须打回

# C2. 未触碰 phases/**（PR-2/3/4 范围 + v4.2 遗留 #6 不动）
git diff --name-only <base>..HEAD | grep '^mobile-qa-workflow/phases/'
# 期望：0 行命中
# 失败诊断：若命中任一 phase 文件，越界（PR-2/3/4 已承担 / v4.2 遗留 #6 不动），必须打回

# C3. 未修改主文档 §3 / 附录 C（仅 §4 索引层变更允许）
git diff mobile-qa-workflow/QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md \
    | grep -E '^[+-]' | grep -E 'PR-5 ·|PR-6 ·|附录 C|^[+-]\| \*\*D[0-9]+\*\*'
# 期望：0 行命中（§3 PR-5/PR-6 段落本体不动，附录 C D1-D19 不动）
# 失败诊断：若命中，越界到设计层，必须打回

# C4. 未修复 P2 step 9 RCA-InProgress 残留
git diff <base>..HEAD | grep -E '^[+-].*RCA-InProgress'
# 期望：0 行命中（与 PR-3 V1 §3.1 同款基调）
# 失败诊断：若有 + 行（修改 RCA-InProgress），越界候选 v4.2 遗留 #8

# C5. commit 拆分（§4.D 单边回滚硬约束；V1 / Finding 3 接纳）
git log --oneline <base>..HEAD | wc -l
# 期望：== 2（commit 1 [PR-5/合并子提交] + commit 2 [PR-6/合并子提交]）
#       commit 3 [PR-5+6/索引层联动] 已由 PE 阶段在 main 上完成，本 PR 范围内无该项
# 失败诊断：
#   - 若 < 2 或 commit message 未含 [PR-5/合并子提交] / [PR-6/合并子提交] 前缀
#     → 单边回滚能力丢失，必须重新拆分
#   - 若 == 3 且第三条 message 前缀为 [PR-5+6/索引层联动]
#     → 仅在本 PR 基于 PE 联动前的旧基线时合理；必须同步验证 §3.C 第 8 项基线对齐断言未通过
```

---

> **施工单版本**：**V1**（v2.2，2026-04-20；初稿 v1.0 → V1 接纳 [`pr5-6-deep-dive-and-agents-templates-REVIEW-2026-04-20.md`](./pr5-6-deep-dive-and-agents-templates-REVIEW-2026-04-20.md) **全部 4 项 findings + 1 附注**后重新发布）
> **V1 主要变更**：① C9 取方案 A — 三必填字段始终物理存在，成功填 `N/A`，失败必填，不绕开协议层暗装条件渲染；② allowlist 盘点命令前置 `^\s*<step-pause` 过滤，明列 raw=5/过滤=2 命中明细，与 §5.A.5 自检 / PR-8 CI 验收方法同源；③ §1 涉及文件加注 PE 阶段已合入的 2 处 index-only 联动（不计入实施期 PR 文件数与工作量），§4.D commit 3 改为"基线对齐时不需要"，§3.C 新增基线对齐断言 DoD；④ 删除"PR-8 CI 缺失 allowlist 时降级 warn"全部表述，改为中性"按主文档口径 fail，需联动评估是否同步回滚 PR-8"；附注：全局清除"§2.2 联动小修"PE 文档章节号泄漏。
> **V1 不变项**：6 文件 / 0.95d / 双层 DoD 与回滚结构 / 无范围扩张 / 无新 v4.2 遗留条目（C9 方案 B 候选挂在已有 v4.2 遗留 #4 下）。
