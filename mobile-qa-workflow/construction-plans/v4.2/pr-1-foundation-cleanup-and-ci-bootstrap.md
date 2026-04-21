# PR-1 · 基础整改 + ADR 化 + CI 4 件套首批（v4.2 详细施工单 / **v1.0 历史快照**）

> ⚠️ **本文档已被 v1.1 取代** —— 当前生效版本：[`./pr-1-foundation-cleanup-and-ci-bootstrap-v1.1.md`](./pr-1-foundation-cleanup-and-ci-bootstrap-v1.1.md)
>
> **取代原因**：本 v1.0 经 [`./pr-1-foundation-cleanup-and-ci-bootstrap-REVIEW-2026-04-21.md`](./pr-1-foundation-cleanup-and-ci-bootstrap-REVIEW-2026-04-21.md) 评审，发现 2 项阻断级 + 3 项高优先级问题，主要为 O3 目标文件路径错位、`check-io-contract.sh` / `check-system-prompt-sync.sh` 校验模型与现网 DSL 不匹配、phase 文件清单与现网不一致、PR-1 "零运行时变更" 定性遗漏 O3 legacy 恢复链路。详见 v1.1 文档 §0 修订摘要与 Changelog。
>
> **保留原因**：① 维持 review 报告引用链不断；② 后续 reviewer 可对照查证 v1.0 → v1.1 的精确演化点；③ 与 v2.2/PR-1（`pr1-schema-protocol-v1.md` / `-v1.2.md` / 无后缀.md 三件并存）体例一致。

---



> **主控文档**：[`./README.md`](./README.md)（§6 PR-1 / §3 H4 / §4 CI 守门表）
> **方案文档**：[`../../../doc/MOBILE_QA_WORKFLOW_STATE_SYNC_OPTIMIZATION_V1.1_2026-04-21.md`](../../../doc/MOBILE_QA_WORKFLOW_STATE_SYNC_OPTIMIZATION_V1.1_2026-04-21.md) §3.1 / §3.2.22
> **关联 V1.1 项**：O1 + O2 + O3 + O4+ + O5(部分: 2 个 sync 脚本 + AUTOGEN 头) + O6 + O22(部分: 4 个 CI 脚本 + workflow 集成)
> **状态**：📐 已展开（v4.2，2026-04-21）
> **唯一职责**：把 v4.2 收敛方案中 **零运行时变更** 的"地基整改 + 文档结构化 + CI 兜底首批"一次性合入，作为后续 PR-2 ~ PR-7 的前置依赖（H4：ADR 必须先于代码 PR；CI 首批必须先于 enum / 契约 / 宏标签变更）。本 PR **不动** `core/workflow.xml` 任何运行时分支、**不动** 任何 phase 内 `<step-pause>`、**不动** 任何 wrapper 输入契约；所有改动均为：① 单值漂移修正（O1/O2，纯 enum 对齐）② 废弃文件归档（O3/O4+，禁止物理删除）③ ADR 目录基础设施（O4+，含 ADR-010 / ADR-021 草稿）④ phase 文件幂等性注释（O6）⑤ 顶部同步声明 + 4 个 CI 守门脚本（O5/O22，全部默认 error 等级，但 `check-system-prompt-sync.sh` PR-1 阶段降级为 warning，PR-2 合入后升级 error，详见主控 §4）。

---

## 1. PR 元信息

| 项 | 值 |
|---|---|
| 分支命名 | `feat/qa-workflow-v4.2-pr1-foundation-cleanup-and-ci-bootstrap` |
| Base | 当前 `main`（无前置 PR） |
| 层级 | 🟢 文档 + CI 层（运行时零改动；无任何 phase 内 step-pause / wrapper 输入契约改动） |
| 目标合入顺序 | **PR-1 → PR-2 → (PR-3 ‖ PR-4) → PR-5 → PR-6 → PR-7**（详见主控 §2 依赖图） |
| Reviewer | 1 名方案 owner（必看 ADR-021 首段命名冲突规避是否到位 / ADR-010 草稿与 O10+ Stage-1 对齐 / 4 CI 脚本 grep 模式正确性）+ 1 名平台 owner（必看 O3 归档后 v3-legacy 会话回放可用 / system-prompt.md 顶部 AUTOGEN 头部不破坏现有 Limited 平台单 prompt 注入） |
| 关联 V1.1 项 | O1（P2 单值漂移）/ O2（P1 + system-prompt 重复 step 编号）/ O3（5 个 deep-dive agent 归档）/ O4+（17 份历史文档归档 + `doc/adr/` 建立 + 21 个 ADR 文件 + 散布注释**短引用化**仅做不删长块）/ O5（顶部 AUTOGEN 声明 + 2 个 sync 脚本）/ O6（7 个 phase 文件加幂等性约束注释）/ O22（4 个 CI 脚本 + `.github/workflows/qa-workflow-schema-check.yml` 集成） |
| 工作量 | **0.9d**（O1/O2 ≈ 0.05d / O3 ≈ 0.1d / O4+ Step 1+2 ≈ 0.4d / O4+ Step 3（短引用化）≈ 0.1d / O5+O22 4 件套 ≈ 0.2d / O6 ≈ 0.05d） |
| 涉及文件 | **新增**：`doc/adr/000-index.md` + `doc/adr/001-current-phase-result-runtime-only.md` + `doc/adr/008-step-pause-userinputs-namespace.md` + `doc/adr/014-step-pause-scope-restriction.md` + `doc/adr/015-userinputs-mirror-allowlist.md` + `doc/adr/016-step-pause-required-params.md` + `doc/adr/017-non-bug-context-persistence.md` + `doc/adr/018-parse-error-circuit-breaker.md` + `doc/adr/019-legacy-step-pause-allowlist.md` + `doc/adr/010-step-pause-registry-data-driven.md`（**草稿，PR-5 落地依赖**）+ `doc/adr/021-phase-abort-macro-tags.md`（**草稿，PR-3 落地依赖；首段命名冲突规避**）+ ~10 个 D2-D13 ADR 文件（兜底）+ `mobile-qa-workflow/scripts/check-state-enum.sh` + `mobile-qa-workflow/scripts/check-system-prompt-sync.sh` + `mobile-qa-workflow/scripts/check-io-contract.sh` + `mobile-qa-workflow/scripts/check-subagent-params.sh` + `mobile-qa-workflow/archive/v4.1-history/`（17 份历史文档归档目标目录）+ `mobile-qa-workflow/functionality-deep-dive/agents/archive/v3-legacy/`（5 个 agent 归档目标目录）。**修改**：`mobile-qa-workflow/phases/p2-spec-definition.md`（O1）+ `mobile-qa-workflow/system-prompt.md`（O2 + O5 顶部声明 + O4+ 短引用化）+ `mobile-qa-workflow/functionality-deep-dive/core/core-rules.xml`（O3 加 deprecated 属性）+ `mobile-qa-workflow/functionality-deep-dive/agents/README.md`（O3 退役标注升级）+ 7 个 `mobile-qa-workflow/phases/p{1..6}-*.md` + `mobile-qa-workflow/phases/p4-implementation.md`（O6 注释；按实际 phase 文件清单对齐）+ `.github/workflows/qa-workflow-schema-check.yml`（追加 4 个 CI step）+ `mobile-qa-workflow/QUALITY-AUDIT-*.md` 等 17 份历史文档（移动到 archive 目录）+ `mobile-qa-workflow/functionality-deep-dive/agents/{context-reconstructor,state-analyst,temporal-analyst,challenger,arbiter}.md` 5 个文件（移动到 archive 目录）。**删除**：无（O3 + O4+ 全部"归档而非删除"，禁止物理删除 / V1.1 §3.1 / F2 finding）。 |
| 不在本 PR 范围 | ① O4+ Step 3 中"长注释整体删除"（依赖 O21 宏标签，留待 PR-3 + PR-6）② `core/workflow.xml` 任何运行时改动（PR-2 + PR-5 范围）③ system-prompt.md 自动构建（PR-2 交付生成器、PR-6 首次构建）④ Spec-Uncertain 契约统一（PR-4 范围）⑤ phase 出口宏标签改写（PR-3 范围）⑥ wrapper 输入契约 `[Schema-Violation]` 校验（PR-7 范围）⑦ `check-build-system-prompt-precondition.sh` / `check-phase-abort-structure.sh` / `check-step-pause-registry.sh`（分别由 PR-2 / PR-3 / PR-5 启用，详见主控 §4） |

---

## 2. 文件级 diff 列表

> 本 PR 共 **6 类变更点**，按"先单值修正 → 再归档 → 再 ADR 基建 → 再 CI 兜底 → 再注释收口"的顺序排列：
>
> | 编号前缀 | 含义 | 数量 |
> |---|---|---|
> | **P2-S1** | O1 单值漂移修正 | 1 |
> | **P1-S1 / SP-S1** | O2 重复 step 编号修正 | 2 |
> | **DD-A1~A5 / DD-D1 / DD-R1** | O3 deep-dive agent 归档 + 退役标注 | 7 |
> | **DOC-A1 / ADR-D1~D11** | O4+ 历史文档归档 + ADR 目录建立 + 散布注释短引用化 | 13 |
> | **SP-H1 / SP-A1 / CI-N1~N4 / CI-W1** | O5 顶部声明 + O22 4 件套 + workflow 集成 | 7 |
> | **PHASE-C1~C7** | O6 7 个 phase 文件幂等性约束注释 | 7 |
>
> **变更点编号约定**：S\* = 单值漂移修正 / A\* = 文件归档 / D\* = 文件级属性或 ADR 草稿 / R\* = README 升级 / H\* = 头部 AUTOGEN 声明 / N\* = 新增 CI 脚本 / W\* = workflow yml 集成 / C\* = 注释级幂等性约束。

---

### 2.1 文件 A · `mobile-qa-workflow/phases/p2-spec-definition.md`（修改 / O1）

#### 2.1.1 变更点 P2-S1 · 末尾 `current_state = RCA-InProgress` → `RCA-Designing`（O1 / C5 状态枚举权威源对齐）

**原文（行号锚点 L186-188）**：

```186:188:mobile-qa-workflow/phases/p2-spec-definition.md
        <step n="9" goal="输出产物">
            ...
            <action>更新 {workflow_status}：current_state = RCA-InProgress</action>
```

**新文**（仅替换 `RCA-InProgress` → `RCA-Designing`）：

```xml
        <step n="9" goal="输出产物">
            ...
            <action>更新 {workflow_status}：current_state = RCA-Designing</action>
```

**修订理由**：
- `core/workflow-status-template.yaml` 头部 enum 集**不包含** `RCA-InProgress`（合法集为 `RCA-Designing` / `RCA-LowConfidence`）；当前写入是 v3 字面残留，依赖编排器 default → goto step 2 的"按 stepsCompleted 推断"兜底语义。
- 与本仓库 v2.2 PR-4 子文档 §2.3.1 P6-A6（`RCA-InProgress → RCA-Designing` 收口）形成"P2 写入端 + P6 写入端"的 C5 完整闭环；之后 `check-state-enum.sh`（变更点 CI-N1）才能在 main 分支零失败。

**兼容性影响**：编排器 step 2 已存在 `RCA-Designing` case 映射到 P3 入口，路由结果完全等价；与 PR-2 / PR-3 / PR-5 / PR-6 全部解耦。

---

### 2.2 文件 B · `mobile-qa-workflow/phases/p1-intake.md`（**核查后判定**）+ `mobile-qa-workflow/system-prompt.md`（修改 / O2）

> **核查现状**：`phases/p1-intake.md` 当前仅 1 处 `step n="5"`（见 L74，"最小信息集门禁"），**已不存在重复**；V1.1 §3.1 O2 描述的 L200-206 重复是 v3 残留口径。本 PR 仅在 `system-prompt.md` 中处理仍然存在的 7 处 `step n="5"`（其中 P1 phase 内的 L200 + L203 仍是重复，需要修正）。

#### 2.2.1 变更点 P1-S1 · `phases/p1-intake.md` 仅做核查断言（O2 phase 侧 / 无 diff）

**新文**：无文件改动，但在 PR description 与 §3 DoD 中显式断言：
- `phases/p1-intake.md` grep `^\s*<step n="5"` 命中精确 **1 处**（L74 单 step）；如核查发现 ≥ 2 处，立即按 V1.1 §3.1 O2 改写"重复 step 5 → step 6 + 后续整体重新编号 6 → 7"，并补 P1-S1' 子变更点。
- 本 PR 提交的实际 PR description 必须附 `grep -nE '^\s*<step n="5"' mobile-qa-workflow/phases/p1-intake.md` 输出结果（≤ 1 行）。

**修订理由**：消除 V1.1 文档与现网 main 的口径漂移（V1.1 是基于较旧快照编写）；本 PR 的 §3 DoD 第 1 项以 grep 命中数为唯一断言。

---

#### 2.2.2 变更点 SP-S1 · `system-prompt.md` P1 phase 内 `step n="5"` 重复修正（O2 system-prompt 侧）

**原文（行号锚点 L200-206）**：

```200:206:mobile-qa-workflow/system-prompt.md
    <step n="5" goal="优先级评估">
        ...
    </step>
    <step n="5" goal="输出 Issue Card">
```

**新文**（**仅** 把 L203 的 `step n="5"` 改写为 `step n="6"`；后续如有 `step n="6"`/`step n="7"` 顺延整体重新编号 6→7、7→8 ...，按 phase 内实际 step 总数对齐）：

```xml
    <step n="5" goal="优先级评估">
        ...
    </step>
    <step n="6" goal="输出 Issue Card">
```

**修订理由**：
- `step n` 编号仅作 LLM 顺序提示，不参与运行时分支判断；修正后避免"第 5 步执行两次"的潜在歧义（V1.1 §3.1 O2）。
- 仅修复 P1 phase 内的 1 处明显重复；其余 6 处 `step n="5"`（L255 / L296 / L337 / L399 / L444 等）分布在 P2 ~ P6 的不同 phase 内，**不属重复**（每个 phase 各自从 step 1 开始编号），不在本 PR 范围。

**兼容性影响**：纯文档行号调整；下游 LLM 推理读到连续编号的 step 列表，行为完全等价。`check-system-prompt-sync.sh`（CI-N2）在 PR-1 阶段为 warning 等级，本变更点不会被反向阻塞。

---

### 2.3 文件 C · O3 deep-dive agent 归档 + 退役标注（5 个文件移动 + 2 个文件修改）

> **修复条目锚点**：V1.1 §3.1 O3（F2 修订：归档而非物理删除）

#### 2.3.1 变更点 DD-A1 ~ DD-A5 · 5 个废弃 agent 文件归档（O3 Step 1）

**操作**：把以下 5 个文件**移动**到 `mobile-qa-workflow/functionality-deep-dive/agents/archive/v3-legacy/` 子目录（git mv，保持历史）：

| 序号 | 源路径 | 目标路径 |
|---|---|---|
| DD-A1 | `mobile-qa-workflow/functionality-deep-dive/agents/context-reconstructor.md` | `mobile-qa-workflow/functionality-deep-dive/agents/archive/v3-legacy/context-reconstructor.md` |
| DD-A2 | `mobile-qa-workflow/functionality-deep-dive/agents/state-analyst.md` | 同上目录 |
| DD-A3 | `mobile-qa-workflow/functionality-deep-dive/agents/temporal-analyst.md` | 同上目录 |
| DD-A4 | `mobile-qa-workflow/functionality-deep-dive/agents/challenger.md`（**注意**：是 deep-dive 子目录下的 challenger.md，**不要**误移主流程 `mobile-qa-workflow/agents/challenger.md`） | 同上目录 |
| DD-A5 | `mobile-qa-workflow/functionality-deep-dive/agents/arbiter.md`（同样仅限 deep-dive 子目录） | 同上目录 |

**修订理由**：
- F2 finding：子编排器 `functionality-deep-dive/core/workflow.xml:21-30` 仍包含老会话恢复逻辑（按 `workflow_version=v3-legacy` 与 `legacy_flow_mode=true` 走老路径），物理删除会破坏 v3-legacy 会话恢复（V1.1 §3.1 O3）。
- 归档后老会话恢复路径中的 `<load target="archive/v3-legacy/...">` 调整后仍能加载，行为等价。

**兼容性影响**：核心兼容性事项。本 PR 必须**同步更新** `functionality-deep-dive/core/workflow.xml` 内 `<load target="agents/...">` 引用路径（如有显式引用这 5 个文件），改为 `<load target="agents/archive/v3-legacy/...">`；如未显式引用而是按 `<agent>` 声明动态加载，则由变更点 DD-D1 同步处理。**核查方法**：grep `functionality-deep-dive/core/workflow.xml` 中是否含 `context-reconstructor` / `state-analyst` / `temporal-analyst` 等字符串；如命中，本 PR 必须同步路径修正（属本变更点的强制配套动作，不单独编号）。

---

#### 2.3.2 变更点 DD-D1 · `functionality-deep-dive/core/core-rules.xml` 5 行 `<agent>` 声明加 `deprecated` 属性（O3 Step 2）

**原文（行号锚点 L92-96，按 V1.1 §3.1 O3 描述；实际行号在本 PR 启动时重新对齐 main）**：

```xml
    <agent name="context-reconstructor" file="agents/context-reconstructor.md"/>
    <agent name="state-analyst" file="agents/state-analyst.md"/>
    <agent name="temporal-analyst" file="agents/temporal-analyst.md"/>
    <agent name="challenger" file="agents/challenger.md"/>
    <agent name="arbiter" file="agents/arbiter.md"/>
```

**新文**（5 行**保留**，每行加 `deprecated="true" recovery_only="true"` 属性 + `file` 路径同步指向 archive 目录 + 单行尾注释）：

```xml
    <agent name="context-reconstructor" file="agents/archive/v3-legacy/context-reconstructor.md" deprecated="true" recovery_only="true"/>  <!-- 仅供 v3-legacy 会话恢复，新会话禁用 / ADR-019 -->
    <agent name="state-analyst" file="agents/archive/v3-legacy/state-analyst.md" deprecated="true" recovery_only="true"/>  <!-- 同上 -->
    <agent name="temporal-analyst" file="agents/archive/v3-legacy/temporal-analyst.md" deprecated="true" recovery_only="true"/>  <!-- 同上 -->
    <agent name="challenger" file="agents/archive/v3-legacy/challenger.md" deprecated="true" recovery_only="true"/>  <!-- 同上 -->
    <agent name="arbiter" file="agents/archive/v3-legacy/arbiter.md" deprecated="true" recovery_only="true"/>  <!-- 同上 -->
```

**修订理由**：
- `deprecated="true"` 让 LLM 在静态读 core-rules.xml 时明确这 5 个 agent 已退役；`recovery_only="true"` 进一步说明仅供 v3-legacy 会话恢复使用。
- 配合后续 v4.3 物理删除时的 grep 守门（前提：所有会话 schema_version ≥ 4 + 90 天无 v3-legacy 流量），属性可被脚本识别。
- ADR-019 引用是 D19 legacy step-pause allowlist 的语义复用（"已退役但保留兼容"），与 O3 的归档语义一致。

**兼容性影响**：纯属性新增；现有 LLM 静态读 core-rules.xml 不报错。CI 守门（变更点 CI-N1 `check-state-enum.sh` 不涉及该文件，不影响）。

---

#### 2.3.3 变更点 DD-R1 · `functionality-deep-dive/agents/README.md` 退役标注升级（O3 Step 3）

**操作**：把现有 L10-17 的"已废弃但保留兼容"段落升级为：

```markdown
## 已退役（仅 v3-legacy 会话恢复）

以下 5 个 agent 在 v4 之后**新会话不再使用**，文件已归档至 `archive/v3-legacy/`：

- context-reconstructor
- state-analyst
- temporal-analyst
- challenger（deep-dive 子目录下，**不影响**主流程 `mobile-qa-workflow/agents/challenger.md`）
- arbiter（deep-dive 子目录下，**不影响**主流程 `mobile-qa-workflow/agents/arbiter.md`）

**退役原因**：deep-dive 子工作流 v4 已收敛为 4 个新 agent（详见本目录其余文件 + `core/workflow.xml`）。

**v4.3 物理删除前提**（来自 V1.1 §3.1 O3）：
1. 所有持久化会话的 `schema_version ≥ 4`（CI 守门：`check-state-enum.sh` 兜底）
2. 90 天内零 v3-legacy 流量（按 `workflow_version=v3-legacy` 与 `legacy_flow_mode=true` 标记的会话计数为 0）
3. 主流程与 deep-dive 子流程均无 `<load target="archive/v3-legacy/...">` 残留引用（grep 验证）

**当前状态**：archive + deprecated + recovery_only 三重标注（v4.2 PR-1 落地）；物理删除推迟到 v4.3 立项。
```

**修订理由**：把"已废弃但保留兼容"的口头约束升级为"退役条件 + 删除前提"的可验证清单，与 ADR-019 语义对齐；明确**不影响**主流程同名 agent，避免 reviewer 误读为"主流程 challenger / arbiter 也被退役"。

**兼容性影响**：纯文档改写；不影响任何运行时。

---

### 2.4 文件 D · O4+ 历史文档归档 + ADR 目录建立 + 散布注释短引用化

> **修复条目锚点**：V1.1 §3.1 O4+（三步走：归档 + ADR 化 + 散布注释外迁）；本 PR 落地 Step 1 + Step 2 全量、Step 3 仅做"短注释引用化"（长注释删除依赖 O21 / 留待 PR-3 + PR-6）

#### 2.4.1 变更点 DOC-A1 · 17 份 QUALITY-AUDIT 历史文档归档（O4+ Step 1）

**操作**：把 `mobile-qa-workflow/` 根目录下的以下 17 份历史文档**移动**到 `mobile-qa-workflow/archive/v4.1-history/`（git mv，保持历史；按当前 main 实际清单对齐，估计 17 份）：

```
QUALITY-AUDIT-CONSTRUCTION-PLAN.md
QUALITY-AUDIT-CONSTRUCTION-PLAN-v1.md / -v1-REVIEW.md
QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.md / -v2-REVIEW.md / -v2.1.md / -v2.1-REVIEW.md
QUALITY-AUDIT-CONSTRUCTION-PLAN-REVIEW-2026-04-20.md
QUALITY-AUDIT-REPORT.md / -v1.1.md / -v1.1-REVIEW.md / -v1.2.md / -v1.2-REVIEW.md / -v1.2.1-REVIEW.md
QUALITY-AUDIT-REVIEW.md
... 其余按 main 实际清单
```

**根目录保留**（V1.1 §3.1 O4+ Step 1 明确）：
- `QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md`（当前版主控）
- `QUALITY-AUDIT-REPORT-v1.2.1.md`（当前审计源）
- `PLATFORM-GUIDE.md` / `SKILL.md` / `system-prompt.md`（运行时 / Skill 入口必需，不属"历史文档"范畴）

**修订理由**：消除根目录 17 份历史文档对 reviewer / Skill 用户的视觉干扰；归档后路径仍可被显式 `<load>` 加载（与 O3 归档语义一致），行为完全等价。

**兼容性影响**：grep 全仓库验证：`QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2` 与 `QUALITY-AUDIT-REPORT-v1.2.1` 是被引用最多的两份（约 N 处，按实际 grep 数量），均保留在原位；其余 17 份的引用预期 ≤ 5 处（多为 v1.0/v1.1 历史 review 内部交叉引用），归档后链接需修正为 `archive/v4.1-history/...`，作为本变更点的强制配套修复（PR description 附 grep 修正清单）。

---

#### 2.4.2 变更点 ADR-D1 ~ ADR-D11 · `doc/adr/` 目录建立 + 21 个 ADR 文件首批落地（O4+ Step 2 / H4 ADR 必须先于代码 PR）

**操作**：

1. 新建 `doc/adr/` 目录 + `doc/adr/000-index.md`（ADR 索引文件，列出 D1-D19 + 新增 D20+ 的映射）
2. 按 V1.1 §3.1 O4+ Step 2 的命名规范（`<NNN>-<slug>.md`）落地以下 21 个 ADR 文件：

| ADR 编号 | 决定锚点 | 文件名 | 状态 | 备注 |
|---|---|---|---|---|
| ADR-001 | D1 / `current_phase_result` 运行时变量 | `001-current-phase-result-runtime-only.md` | active | 内容直接复用 V1.1 §2.5 + v2.2 PR-4 §1.1 解释 |
| ADR-002 ~ ADR-007 | D2 ~ D7 | `002-*.md` ~ `007-*.md` | active | 每个 ADR ≤ 50 行；按"背景 / 决定 / 替代方案 / 影响 / 状态"五段结构 |
| ADR-008 | D8 / step-pause user_inputs 命名空间 | `008-step-pause-userinputs-namespace.md` | active | — |
| ADR-009 | D9 / 合入顺序约束 | `009-merge-order-constraint.md` | active | 内容引用 v2.2 README §"Merge Order" |
| **ADR-010** | **D10 + V1.1 O10+ Stage-1 / step-pause-registry 数据驱动** | **`010-step-pause-registry-data-driven.md`** | **draft（PR-5 落地依赖）** | **首段必须显式说明：本 ADR 描述的 `step-pause-registry.yaml` 由 PR-5 实际交付；本 PR 仅落地草稿提供 H4 前置依赖** |
| ADR-011 ~ ADR-013 | D11 ~ D13 | `011-*.md` ~ `013-*.md` | active | — |
| ADR-014 | D14 / step-pause 调度作用域 | `014-step-pause-scope-restriction.md` | active | **本 ADR 是 O4+ 散布注释短引用化的高频引用目标**（约 ~50 处 `<!-- ADR-014 -->` 替换） |
| ADR-015 | D15 / user_inputs 镜像白名单 | `015-userinputs-mirror-allowlist.md` | active | — |
| ADR-016 | D16 / step-pause 必填参数 | `016-step-pause-required-params.md` | active | — |
| ADR-017 | D17 / Non-Bug 上下文持久化 | `017-non-bug-context-persistence.md` | active | — |
| ADR-018 | D18 / parse-error 熔断 | `018-parse-error-circuit-breaker.md` | active | — |
| ADR-019 | D19 / legacy step-pause allowlist | `019-legacy-step-pause-allowlist.md` | active | 与 O3 退役标注语义复用 |
| ADR-020 | （v4.3 长期演进 / O20）| `020-v43-long-term-evolution.md` | superseded-by-v4.3-plan | 占位，PR-8 启动时升级 |
| **ADR-021** | **V1.1 O21 / `<phase-abort>` / `<phase-complete>` 宏标签** | **`021-phase-abort-macro-tags.md`** | **draft（PR-3 落地依赖）** | **首段必须显式区分宏标签与 v2.2 PR-4 子文档名 `phase-abort-fanout-isolation.md` 的差异（详见主控 §3 H4 / V1.1 §3.2.21 末尾"命名冲突规避"），否则本 PR 不予合入** |

**ADR 文件统一结构模板**（每个 ADR 文件遵守，避免风格漂移）：

```markdown
# ADR-NNN: <标题>

> **状态**：active | draft | superseded（如 superseded，附"被 ADR-XXX 取代"说明）
> **关联决定**：D<n>（来自 V1.1 §2 决定列表 / v2.2 §6 D 表）
> **关联 PR**：PR-N（如属 draft，必须列明落地 PR）

## 1. 背景
（≤ 5 句话，描述决策上下文与替代方案讨论起点）

## 2. 决定
（核心结论 + 关键约束 + 反向断言）

## 3. 替代方案
（曾被讨论但被拒绝的方案 + 拒绝理由）

## 4. 影响
（对协议层 / 编排器 / phase / wrapper / CI / 跨平台的影响清单）

## 5. 引用
（关联的 V1.1 章节 / v2.2 PR / 散布注释外迁清单 / 后续依赖 PR）
```

**ADR-021 首段命名冲突规避示例文本**（必须逐字落地）：

```markdown
# ADR-021: <phase-abort> / <phase-complete> 宏标签

> **命名冲突规避声明**：本 ADR 描述的 `<phase-abort>` / `<phase-complete>` 是
> **核心 DSL 宏标签**（V1.1 O21 / §3.2.21 / PR-3 落地），用于声明式表达 phase 出口
> 的"state / fields / ABORT / 退出"4 步动作；这与 v2.2 PR-4 子文档名
> `phase-abort-fanout-isolation.md` 描述的"phase 内 ABORT 标记 + fanout 字段隔离"
> 是**完全不同范畴**的工作 —— 后者是 v4.1 protocol-level B1\* 修复，使用 v3 既有
> `<action>设置 current_phase_result = ABORT</action>` 写法；本 ADR 描述的宏标签
> 是 v4.2 在该 protocol 之上新增的"声明式语法糖"，用宏一行展开后等价于
> v2.2 PR-4 写入的"5 步咒语"。
```

**修订理由**：
- H4 强约束：ADR-010 / ADR-021 必须先于 PR-3 / PR-5 任何代码改动落地（主控 §3 H4）。本 PR 把这两个 ADR 以草稿形式落地，提供 H4 前置依赖。
- ADR-021 命名冲突规避：避免 reviewer / 后续 PR 实施者把"宏标签"误读为"v2.2 PR-4 已完成的工作"导致 PR-3 被错误关闭。
- 21 个 ADR 文件首批落地为后续 V1.1 散布注释外迁（Step 3）提供"引用锚点池"。

**兼容性影响**：纯文档新增；ADR 文件在 LLM 推理时**不被加载**（除非显式 `<load>`），不增加任何运行时 token 预算。

---

#### 2.4.3 变更点 ADR-D11' · 散布注释短引用化（O4+ Step 3 / 仅"短引用化"，长注释删除留待 PR-3 + PR-6）

**操作**：

1. 全仓库扫描以下两类形式的散布注释：
   - XML 内：`<!-- D\d+: <一句话解释> -->`（单行短注释）
   - YAML 内：`# D\d+: <一句话解释>`（单行短注释）
2. 替换为 `<!-- ADR-NNN -->` / `# ADR-NNN` 单行引用（保留 ID 锚点，删除冗余解释文本）
3. **本 PR 不动**长注释块（≥ 5 行的注释段，如 P2 step 4 的 45 行 Non-Bug 解释）—— 这些块的整体删除依赖 O21 `<phase-abort reason="ADR-014">` 已落地（PR-3）+ Fix-Confirming 收口（PR-6）；保留为后续 PR 范围。

**预期影响**（V1.1 §3.1 O4+ Step 3 给出的总目标 ~165 行净减，本 PR 仅吃下其中"短引用化"部分，约 30~50 行）：
- `core/workflow.xml`：约 -20 行（短引用化）
- `core/core-rules.xml`：约 -10 行
- `core/workflow-status-template.yaml`：约 -10 行
- 各 phase 文件：合计 -10 行（只动短注释；长注释保留）

**修订理由**：
- 短引用化是 O4+ Step 3 的"无依赖最小子集"，可在本 PR 一次性吃下；长注释删除有 O21 硬依赖，强行做会引入回滚风险。
- 替换后 LLM 看到 `ADR-014` 引用可主动读 `doc/adr/014-*.md` 追溯历史，但默认推理不需要，token 预算不变。

**兼容性影响**：纯注释修改；不影响任何 XML / YAML parse 行为；不影响任何 LLM 推理结果。

---

### 2.5 文件 E · O5 头部 AUTOGEN 声明 + O22 4 个 CI 脚本 + workflow 集成

> **修复条目锚点**：V1.1 §3.1 O5（顶部声明 + 2 个 sync 脚本）+ §3.2.22（4 件套补全）；与主控 §4 CI 守门表"PR-1 启用 4 项"完全对齐

#### 2.5.1 变更点 SP-H1 · `system-prompt.md` 头部加 AUTOGEN 声明（O5 Step 1）

**原文（行号锚点 L1-3，按 main 实际首部）**：

```markdown
# Mobile QA Workflow — System Prompt
（原首段）
```

**新文**（在 H1 标题之前**插入** AUTOGEN 声明块；H1 标题与原内容保持不动）：

```markdown
<!--
========================================================================
AUTOGEN-FROM:
  core/core-rules.xml
  core/workflow.xml
  core/workflow-status-template.yaml
  core/default-config.yaml
  core/workflow-model.yaml
  (PR-5 起增加：core/step-pause-registry.yaml)

@ schema_version=4
@ sync-check=2026-04-21（PR-1 落地基线）

⚠️ 本文件当前为"手维护"状态：
   - PR-2 起：CI `check-system-prompt-sync.sh` 升级为 error，本文件任何手改必须同步更新 core/
   - PR-2 起：交付 `scripts/build-system-prompt.py` 生成器（仅交付脚本，不替换本文件）
   - PR-6 起：本文件由生成器**首次自动构建并替换**；之后禁止手改
========================================================================
-->

# Mobile QA Workflow — System Prompt
（原首段）
```

**修订理由**：
- V1.1 §3.1 O5：让漂移在 PR Review 阶段就被发现而非上线后才暴露；声明明确本文件的"PR-2 警告 / PR-6 禁手改"演进路径，避免后续 PR 实施者误以为本文件可任意手改。
- `sync-check` 时间戳为 PR-1 合入日期，作为 `check-system-prompt-sync.sh` 的"基线 token 哈希"参考起点。

**兼容性影响**：纯注释新增；HTML 注释格式（`<!-- ... -->`）不影响 markdown 渲染或 LLM 推理。

---

#### 2.5.2 变更点 CI-N1 · `mobile-qa-workflow/scripts/check-state-enum.sh` 新建（O22 #1 / O5 配套）

**新文件内容**（约 ~40 行 bash，要点）：

```bash
#!/usr/bin/env bash
# check-state-enum.sh
# 守门：current_state 写入值必须落在 workflow-status-template.yaml 头部 enum 集内
# 关联：V1.1 §3.1 O5 配套 / §3.2.22 / 主控 §4 PR-1 启用
# 等级：error（PR-1 启用即生效）

set -euo pipefail
cd "$(dirname "$0")/.."

# 1. 从 core/workflow-status-template.yaml 头部注释提取 v4.1 完整枚举集
ENUM_FILE="core/workflow-status-template.yaml"
ALLOWED=$(awk '/v4.1 完整集合/,/^[^#]/' "$ENUM_FILE" \
  | grep -oE '[A-Z][A-Za-z-]+' | sort -u)

# 2. grep 全仓库 phase 文件 + system-prompt.md + workflow.xml 中的写入
HITS=$(grep -rEn 'current_state\s*=\s*[A-Z][A-Za-z-]+' \
  phases/ system-prompt.md core/workflow.xml \
  | sed -E 's/.*current_state\s*=\s*([A-Z][A-Za-z-]+).*/\1/' | sort -u)

# 3. diff：HITS 中的任何项不在 ALLOWED 内则 fail
fail=0
for v in $HITS; do
  if ! echo "$ALLOWED" | grep -qx "$v"; then
    echo "::error::非法 current_state 写入: $v（不在 $ENUM_FILE 头部 enum 集内）"
    fail=1
  fi
done

[ $fail -eq 0 ] && echo "✅ check-state-enum.sh 通过（HITS=$(echo "$HITS" | wc -w) / ALLOWED=$(echo "$ALLOWED" | wc -w)）"
exit $fail
```

**修订理由**：
- V1.1 §3.1 O5 配套；与变更点 P2-S1（`RCA-InProgress → RCA-Designing`）形成"代码修正 + CI 守门"完整闭环；P2-S1 落地后本脚本必须在 main 上零失败，否则本 PR 不予合入。
- 默认 error 等级（主控 §4），强制兜底所有后续 PR 不再写入非法状态值。

**兼容性影响**：纯 CI 守门，不改运行时；脚本失败 → CI 红 → PR 阻断。

---

#### 2.5.3 变更点 CI-N2 · `mobile-qa-workflow/scripts/check-system-prompt-sync.sh` 新建（O22 #2 / O5 配套 / PR-1 默认 warning）

**新文件内容**（约 ~50 行 bash，要点）：

```bash
#!/usr/bin/env bash
# check-system-prompt-sync.sh
# 守门：system-prompt.md 与 core/ 关键 token 必须同步
# 关联：V1.1 §3.1 O5 配套 / 主控 §4 PR-1 启用为 warning，PR-2 升级为 error

set -euo pipefail
cd "$(dirname "$0")/.."

# 严重度：默认 warning（PR-1）；PR-2 合入后由 workflow yml 切换为 error
SEVERITY="${SP_SYNC_SEVERITY:-warning}"

# 1. 关键 token 1：current_state enum 集
ENUM_CORE=$(awk '/v4.1 完整集合/,/^[^#]/' core/workflow-status-template.yaml \
  | grep -oE '[A-Z][A-Za-z-]+' | sort -u)
ENUM_SP=$(grep -oE 'current_state\s*[:=]\s*[A-Z][A-Za-z-]+' system-prompt.md \
  | sed -E 's/.*\s+([A-Z][A-Za-z-]+).*/\1/' | sort -u)

# 2. 关键 token 2：Spec-Uncertain 弹窗 allowed_values（PR-2 强 error 兜底由 check-build-system-prompt-precondition.sh 承担）
SPEC_UNCERTAIN_CORE=$(grep -oE 'allowed_values=[^"]*' core/workflow.xml | head -1)
SPEC_UNCERTAIN_SP=$(grep -oE 'allowed_values=[^"]*' system-prompt.md | head -1)

# 3. diff：任一关键 token 不一致 → 按 SEVERITY 报错
fail=0
if [ "$ENUM_CORE" != "$ENUM_SP" ]; then
  echo "::${SEVERITY}::system-prompt.md 中 current_state enum 与 core/workflow-status-template.yaml 头部不一致"
  [ "$SEVERITY" = "error" ] && fail=1
fi
# ... 其余 token 校验同理

[ $fail -eq 0 ] && echo "✅ check-system-prompt-sync.sh 通过（severity=$SEVERITY）"
exit $fail
```

**修订理由**：
- V1.1 §3.1 O5 + 主控 §4：PR-1 启用为 warning（避免 PR-1 自身被本脚本反向阻塞，因 system-prompt.md 中已知存在 v3 残留 token）；PR-2 合入 system-prompt 生成器后升级为 error。
- 严重度通过环境变量 `SP_SYNC_SEVERITY` 切换，workflow yml 集成时由 PR-2 PR description 显式更新。

**兼容性影响**：PR-1 阶段为 warning，本 PR 不会被自身阻塞；PR-2 升级 error 时由 PR-2 PR description 同步切换。

---

#### 2.5.4 变更点 CI-N3 · `mobile-qa-workflow/scripts/check-io-contract.sh` 新建（O22 #3）

**新文件内容**（约 ~40 行 bash + python 混合，要点）：

```bash
#!/usr/bin/env bash
# check-io-contract.sh
# 守门：workflow.xml <io-contract> 声明的 file 必须在某个 phase <template-output> 内被实际输出
# 关联：V1.1 §3.2.22 第 3 项 / 主控 §4 PR-1 启用为 error

set -euo pipefail
cd "$(dirname "$0")/.."

# 1. 从 core/workflow.xml 抽取所有 <io-contract> 内的 file 属性
DECLARED=$(python3 -c "
import re, sys
content = open('core/workflow.xml').read()
# 找 <io-contract> ... </io-contract> 块内的 file 属性
m = re.search(r'<io-contract>(.*?)</io-contract>', content, re.S)
if m:
    files = re.findall(r'file=\"([^\"]+)\"', m.group(1))
    for f in files: print(f)
")

# 2. 从所有 phase 文件抽取所有 <template-output ... file=...> 中的 file 属性
ACTUAL=$(grep -hoE '<template-output[^/]*file="[^"]+"' phases/*.md \
  | sed -E 's/.*file="([^"]+)".*/\1/' | sort -u)

# 3. DECLARED 中的每一项必须在 ACTUAL 中出现
fail=0
for f in $DECLARED; do
  if ! echo "$ACTUAL" | grep -qx "$f"; then
    echo "::error::声明的 io-contract file 未被任何 phase 输出: $f"
    fail=1
  fi
done

[ $fail -eq 0 ] && echo "✅ check-io-contract.sh 通过（DECLARED=$(echo "$DECLARED" | wc -l) / ACTUAL=$(echo "$ACTUAL" | wc -l)）"
exit $fail
```

**修订理由**：
- V1.1 §3.2.22 第 3 项：消除"workflow.xml 声明产物但 phase 漏输出"的契约漂移类 bug。
- 反向校验（"phase 输出但 workflow.xml 未声明"）作为 warning 级建议，本 PR 不引入避免阻塞。

**兼容性影响**：纯 CI 守门；如本 PR 落地时 workflow.xml 已存在该类漂移，本 PR description 必须列出修复清单（建议归入 PR-2 处理，PR-1 可临时降级 SEVERITY 通过 ENV）。

---

#### 2.5.5 变更点 CI-N4 · `mobile-qa-workflow/scripts/check-subagent-params.sh` 新建（O22 #4）

**新文件内容**（约 ~50 行 bash，要点）：

```bash
#!/usr/bin/env bash
# check-subagent-params.sh
# 守门：invoke-subagent 调用必须含 confidence_input（challenger）/ base_score（arbiter）
# 关联：V1.1 §3.2.22 第 4 项 / C2 类 Schema-Violation / 主控 §4 PR-1 启用为 error

set -euo pipefail
cd "$(dirname "$0")/.."

fail=0

# 1. 所有 challenger 调用必须含 confidence_input
CH_HITS=$(grep -B0 -A30 'subagent_type="challenger"' phases/*.md \
  | awk 'BEGIN{RS="--"} /subagent_type="challenger"/' )
echo "$CH_HITS" | awk 'BEGIN{RS="--"} {
  if ($0 ~ /subagent_type="challenger"/) {
    if ($0 !~ /confidence_input/) {
      print "::error::challenger 调用缺 confidence_input 注入:";
      print substr($0, 1, 200);
      exit_code = 1;
    }
  }
} END { exit exit_code+0 }' || fail=1

# 2. 所有 arbiter 调用必须含 base_score（同理）
# ... 略

[ $fail -eq 0 ] && echo "✅ check-subagent-params.sh 通过"
exit $fail
```

**修订理由**：
- V1.1 §3.2.22 第 4 项 / C2 类 Schema-Violation 静态守门；与 v2.2 PR-4 已落地的"调用方按角色注入"形成 CI 兜底闭环。
- 当前 main 上 v2.2 PR-4 已合入，所有 challenger / arbiter 调用应已注入正确字段；本 PR 启用脚本为 error 不会引入回归。

**兼容性影响**：纯 CI 守门；如本 PR 落地时发现 v2.2 PR-4 后又有新 challenger/arbiter 调用未注入，本 PR description 必须列出修复清单。

---

#### 2.5.6 变更点 CI-W1 · `.github/workflows/qa-workflow-schema-check.yml` 集成 4 个 CI step（O22 / 主控 §4）

**操作**：在现有 8 项 schema/protocol 守门 step 之后**追加** 4 个 step（顺序与 §4 表对齐）：

```yaml
      # ════════════════════════════════════════════════════════════════
      # 检查 9（PR-1 启用）：state enum 守门
      # 关联：V1.1 §3.1 O5 / §3.2.22 / 本 v4.2 PR-1
      # 等级：error
      # ════════════════════════════════════════════════════════════════
      - name: Check 9 — state enum 守门
        run: bash mobile-qa-workflow/scripts/check-state-enum.sh

      # ════════════════════════════════════════════════════════════════
      # 检查 10（PR-1 启用 warning，PR-2 升级 error）：system-prompt sync 守门
      # ════════════════════════════════════════════════════════════════
      - name: Check 10 — system-prompt sync 守门（PR-1: warning）
        env:
          SP_SYNC_SEVERITY: warning
        run: bash mobile-qa-workflow/scripts/check-system-prompt-sync.sh

      # ════════════════════════════════════════════════════════════════
      # 检查 11（PR-1 启用）：io-contract 守门
      # ════════════════════════════════════════════════════════════════
      - name: Check 11 — io-contract 守门
        run: bash mobile-qa-workflow/scripts/check-io-contract.sh

      # ════════════════════════════════════════════════════════════════
      # 检查 12（PR-1 启用）：subagent-params 守门
      # ════════════════════════════════════════════════════════════════
      - name: Check 12 — subagent-params 守门
        run: bash mobile-qa-workflow/scripts/check-subagent-params.sh
```

**修订理由**：与主控 §4 表 4 项 PR-1 启用一一对应；每个 step 的`name`、严重度、关联锚点全部按主控表逐字对齐，避免后续 reviewer 走两份口径。

**兼容性影响**：CI 总耗时增加约 ~10 秒（4 个脚本均为 grep/python 单文件解析，无网络依赖）；不影响其余 8 项现有 step。

---

### 2.6 文件 F · O6 phase 文件级幂等性约束注释（7 个 phase 文件 / PHASE-C1 ~ C7）

> **修复条目锚点**：V1.1 §3.1 O6（注释级幂等性约束 / 与 O21 协同：O21 落地后 O6 自动失效，本 PR 仅做过渡期约束）

#### 2.6.1 变更点 PHASE-C1 ~ C7 · 7 个 phase 文件头部加注释（统一文本）

**操作**：在以下 7 个 phase 文件的 `<workflow-phase>` 根元素**之前**插入统一注释块（文件内容除注释外不动）：

| 编号 | 文件 |
|---|---|
| PHASE-C1 | `mobile-qa-workflow/phases/p1-intake.md` |
| PHASE-C2 | `mobile-qa-workflow/phases/p2-spec-definition.md` |
| PHASE-C3 | `mobile-qa-workflow/phases/p3-root-cause.md` |
| PHASE-C4 | `mobile-qa-workflow/phases/p4-fix-design.md` |
| PHASE-C5 | `mobile-qa-workflow/phases/p4-implementation.md`（如存在；按 main 实际清单对齐） |
| PHASE-C6 | `mobile-qa-workflow/phases/p5-fix-implementation.md` 或类似（按 main 实际清单） |
| PHASE-C7 | `mobile-qa-workflow/phases/p6-verification.md` |

**统一注释块文本**：

```xml
<!--
========================================================================
幂等性约束（V1.1 O6 / 过渡期约束 / O21 落地后失效）

1. 同一 step 内对 workflow_status.current_state 的写入只允许一次（含 switch
   每个 case 内一次）；reviewer 应可一眼数清状态写入点位。
2. 状态写入是幂等的：同值重写不影响下游编排器路由（参考 ADR-001 D1 协议）。
3. 任何"phase 早退"必须配 <action>设置 current_phase_result = ABORT</action>
   单独动作（详见 ADR-001）；O21 宏标签落地后将自动展开此约束（详见 ADR-021）。
4. 本注释块在 v4.2 PR-3（O21 宏标签）+ PR-6（D14 收口）合入后由 O21 宏标签
   自动覆盖，本 PR 仅作为过渡期约束保留；PR-6 合入后可由 cleanup PR 移除。
========================================================================
-->
```

**修订理由**：
- V1.1 §3.1 O6：把 v3 的"口头约束"显化为文件头注释，让 reviewer 与后续 PR 实施者读 phase 文件时即知约束；与 O21 的"结构性消除"形成"过渡期口头约束 + 长期结构约束"两段式演进。
- 7 个文件统一文本，避免风格漂移；引用 ADR-001 / ADR-021 形成与 O4+ Step 2 的引用闭环。

**兼容性影响**：纯注释新增；不影响任何运行时与 LLM 推理。

---

## 3. PR-level DoD 子集（链接到主控 §5）

> 完整跨平台矩阵见主控 [§5 跨平台回归矩阵](./README.md#5-跨平台回归矩阵每-pr-必跑)；本节仅列 PR-1 必须满足的子集。

### 3.1 静态契约校验（PR-1 必跑子集）

- [ ] **O1 落地**：grep `phases/p2-spec-definition.md` 中 `current_state\s*=\s*RCA-InProgress` 命中 **0 处**；`current_state\s*=\s*RCA-Designing` 命中 **≥ 1 处**（变更点 P2-S1）
- [ ] **O2 phase 侧核查**：grep `^\s*<step n="5"` 在 `phases/p1-intake.md` 命中 **≤ 1 处**（变更点 P1-S1）
- [ ] **O2 system-prompt 侧落地**：`system-prompt.md` 中原 L200/L203 重复的 `step n="5"` 已修正为 `step n="5"` + `step n="6"`（变更点 SP-S1）
- [ ] **O3 归档完整**：`mobile-qa-workflow/functionality-deep-dive/agents/archive/v3-legacy/` 目录存在且含 5 个 agent 文件；原路径下 5 个文件不再存在（git mv 后）；`functionality-deep-dive/core/core-rules.xml` 中 5 行 `<agent>` 声明全部加 `deprecated="true" recovery_only="true"` 属性 + `file` 路径指向 archive 目录；`functionality-deep-dive/agents/README.md` 退役标注升级完成（变更点 DD-A1~A5 + DD-D1 + DD-R1）
- [ ] **O4+ Step 1 + Step 2 落地**：`mobile-qa-workflow/archive/v4.1-history/` 目录存在且含 ~17 份历史文档；`doc/adr/` 目录存在且含 `000-index.md` + 21 个 ADR 文件（含 ADR-010 / ADR-021 草稿）；ADR-021 首段的"命名冲突规避声明"逐字落地（grep 验证 `命名冲突规避声明` 命中 1 处）
- [ ] **O4+ Step 3 短引用化**：grep 全仓库（除 `archive/`）中 `<!-- D\d+:` 与 `# D\d+:` 形式的散布注释命中 **0 处**（已全部替换为 `<!-- ADR-NNN -->` / `# ADR-NNN`）；预期净减行数 ≥ 30
- [ ] **O5 头部声明**：`system-prompt.md` 头部含 `AUTOGEN-FROM:` 块（变更点 SP-H1）
- [ ] **O6 注释**：7 个 phase 文件头部均含"幂等性约束"统一注释块（变更点 PHASE-C1~C7 / grep `幂等性约束（V1.1 O6` 命中 **7 处**）
- [ ] **O22 4 件套落地**：`mobile-qa-workflow/scripts/check-{state-enum,system-prompt-sync,io-contract,subagent-params}.sh` 4 个文件存在且 `chmod +x`；本地手跑 4 个脚本均退出码 0（其中 `check-system-prompt-sync.sh` 以 `SP_SYNC_SEVERITY=warning` 跑通即可）
- [ ] **CI 集成**：`.github/workflows/qa-workflow-schema-check.yml` 含 4 个新增 step（变更点 CI-W1）；CI 跑全绿（其中 system-prompt-sync 为 warning）

### 3.2 动态用例（PR-1 必跑子集）

- [ ] **跨平台回归**（主控 §5 PR-1 行）：
  - Cursor / Claude Code（Full）：eval-cases 全量通过
  - Trae（Full）：eval-cases 全量通过
  - Dify / Coze（Limited）：抽 1 用例通过
  - 单 prompt LLM（Minimal）：抽 1 用例通过
- [ ] **老会话回放兼容**（V1.1 §3.1 O3 / 主控 §6 PR-1 DoD）：选 1 个 v3-legacy 历史会话（按 `workflow_version=v3-legacy` 标记）回放完整 P1-P6 流程，确认 deep-dive 子工作流仍能从 `archive/v3-legacy/` 加载 5 个废弃 agent，行为与归档前完全一致
- [ ] **通用门禁**（主控 §5 末段 / V1.1 §4.2）：
  1. `eval-framework/artifact_checker.py` 全量通过
  2. `eval-cases/seed-10` chains A/B `mean_score` 不降（容许 ±5% 抖动）；零分 case 不增
  3. 路由层抽 5 case 人工读 `workflow-status.yaml` 一致性

> **PR-1 不验收的 §5 项**（由后续 PR 联动）：
> - 跨平台 Limited / Minimal 全量回归 → PR-2 + PR-6（O7/O8/O17+ 后高风险点）
> - phase 出口宏标签人工抽查 → PR-3 启用后承接
> - Spec-Uncertain 弹窗双侧一致性 → PR-4 承接
> - step-pause-registry 三类校验 → PR-5 启用后承接
> - system-prompt 自动构建 diff → PR-6 启用后承接

---

## 4. PR-level 回滚动作（链接主控 §3 H4 / §6 PR-1）

> 主控 §6 PR-1 描述："回滚 = 单 PR 回滚（无运行时变更，零阻塞影响）"。具体动作：

- **回滚命令**：`git revert <PR-1-merge-commit>`
- **回滚后状态**：
  - `phases/p2-spec-definition.md` 末尾 `current_state` 恢复为 `RCA-InProgress`（C5 漂移复发，但因编排器 default 兜底不影响运行时）
  - `system-prompt.md` 内 P1 phase 内 step n="5" 重复恢复（语义歧义复发，但不影响 LLM 顺序执行）
  - 5 个 deep-dive agent 文件回到原路径；`<agent>` 声明 `deprecated` 属性消失；README 退役标注回退（v3-legacy 兼容性不变 — 归档前后对老会话恢复均可用）
  - `doc/adr/` 目录消失 → **所有 ADR 引用断链**（包括 ADR-001/008/014/015/016/017/018/019 的"短引用化"替换会变为 `<!-- ADR-NNN -->` 引用空目标）→ 需要同步把 O4+ Step 3 的引用化全部回退为原解释文本
  - 4 个 CI 脚本文件消失；`.github/workflows/qa-workflow-schema-check.yml` 4 个 step 消失；CI 不再守门 state-enum / system-prompt-sync / io-contract / subagent-params
  - 17 份历史文档回到 `mobile-qa-workflow/` 根目录（视觉干扰复发）
- **下游影响**：
  - **PR-2**（同步债清理 + system-prompt 生成器）：强依赖 PR-1 的 ADR 目录与 4 个 CI 脚本；PR-1 回滚后 PR-2 必须**同步回滚或推迟**
  - **PR-3**（phase 出口宏标签）：强依赖 PR-1 的 ADR-021 草稿；PR-1 回滚后 PR-3 启动需先恢复 ADR-021
  - **PR-5**（step-pause-registry）：强依赖 PR-1 的 ADR-010 草稿；同上
  - **PR-4 / PR-6 / PR-7**：弱依赖 PR-1 的 CI 守门；PR-1 回滚后这些 PR 自身的 CI 守门会缺少 state-enum / io-contract / subagent-params 兜底，需 PR description 显式提示 reviewer 加强人工 review
- **风险等级**：🟢 **极低**（全部为文档 + CI 守门 + 单值修正；无运行时变更，无 protocol 改动，无跨平台行为漂移）
- **存量会话兼容**：纯加项；存量会话不受影响（state-enum 守门是新会话的写入校验，不读取已持久化的旧状态值；如旧会话残留 `RCA-InProgress`，由迁移脚本另行处理，本 PR 不涉及）

---

## 5. §4 CI 守门自检（PR-1 视角）

> 按主控 §4 CI 守门启用时间表 7 项逐项核查 PR-1 是否落地或留待后续 PR。✅ = 本 PR 启用；⏸ = 不在本 PR 范围（标注承接 PR）。

| 主控 §4 脚本 | PR-1 状态 | 落地证据 / 承接 PR |
|---|---|---|
| `check-state-enum.sh` | ✅ error | 变更点 CI-N1 + CI-W1 集成；落地配套修正 P2-S1 |
| `check-system-prompt-sync.sh` | ✅ warning（PR-2 升级 error） | 变更点 CI-N2 + CI-W1 集成；通过 `SP_SYNC_SEVERITY` 环境变量切换严重度 |
| `check-io-contract.sh` | ✅ error | 变更点 CI-N3 + CI-W1 集成 |
| `check-subagent-params.sh` | ✅ error | 变更点 CI-N4 + CI-W1 集成；与 v2.2 PR-4 角色驱动注入闭环 |
| `check-build-system-prompt-precondition.sh` | ⏸ | PR-2 启用为 error（H1 守门：Spec-Uncertain `allowed_values` 必须为 `1\|2\|S`） |
| `check-phase-abort-structure.sh` | ⏸ | PR-3 启用为 warning，PR-6 升级 error（H2 降级路径） |
| `check-step-pause-registry.sh` | ⏸ | PR-5 启用为 error（含硬编码 case 禁出） |

**自检结论**：PR-1 落地主控 §4 中 PR-1 启用列的 **4/7 项**（前 4 项），全部按主控表口径（严重度 / 启用 PR）一一对齐；后 3 项明确承接 PR。

---

## 6. Reviewer 议题汇总（PR-1 启动期）

| # | 议题 | 状态 | 影响范围 |
|---|---|---|---|
| 1 | V1.1 §3.1 O2 描述 P1 phase 内 L200-206 重复 step n="5"，但 main 实际仅 1 处（L74）— 现状已修正还是 V1.1 文档基于旧快照？ | 📝 **建议本 PR 启动时再次 grep 核查** main 上 `phases/p1-intake.md`；若确认无重复，本 PR 仅落地 §2.2 P1-S1（核查断言）+ SP-S1（system-prompt 修正）；若发现重复则补 P1-S1' 子变更点 | O2 phase 侧落地完整性 |
| 2 | V1.1 §3.1 O4+ Step 3 总目标 ~165 行净减，本 PR 仅吃下"短引用化"约 30~50 行；剩余 ~115 行的"长注释整体删除"是否需在 PR-1 同步登记到 PR-3 / PR-6 的 TODO 列表？ | 📝 **建议本 PR 在 PR description 内显式登记** PR-3（O21 宏标签落地后 P2 step 4 的 45 行 Non-Bug 注释删除）+ PR-6（D14 收口后 phase 内联注释删除）的剩余指标，避免长注释删除被遗漏 | O4+ 总目标完整覆盖 |
| 3 | ADR-010 / ADR-021 以"draft"状态落地，是否需要在 ADR 文件首段加显式"PR-N 落地依赖"标记？ | ✅ **本 PR 已采纳** — 在 §2.4.2 表中明确 ADR-010 注明"PR-5 落地依赖"、ADR-021 注明"PR-3 落地依赖"；ADR 文件统一结构模板的"关联 PR"字段强制填写 | H4 前置依赖完整性 |
| 4 | ADR-021 首段命名冲突规避声明的强制度 | ✅ **本 PR 已升级为合入门禁** — §2.4.2 末段明确"否则本 PR 不予合入"；reviewer 必须 grep `命名冲突规避声明` 命中 1 处 | 跨 PR 文档清晰度 |
| 5 | 4 个 CI 脚本启用后是否会反向阻塞本 PR 自身合入？（如 system-prompt.md 已存在 sync 漂移）| 📝 **建议本 PR 启动时本地预跑 4 个脚本**：`check-system-prompt-sync.sh` 默认 warning 不阻塞；其余 3 个脚本如发现已存在漂移，本 PR description 必须列出修复清单（建议 enum 漂移由 P2-S1 一并修复 / io-contract 漂移归入 PR-2 / subagent-params 漂移归入 PR-2 review） | PR-1 自身合入可行性 |

---

## Changelog

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-04-21 | 初版。基于主控 v4.2 README §6 PR-1 + V1.1 §3.1 O1/O2/O3/O4+/O5/O6 + §3.2.22 O22(4 件套) 完整展开；6 类共 ~30 个变更点；体例参考 v2.2/pr4-phase-abort-fanout-isolation.md 但精简到 ~500 行（适配 PR-1 零运行时变更性质）；ADR-010 / ADR-021 草稿落地满足主控 §3 H4 前置依赖。 |
