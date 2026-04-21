# PR-1 · 基础整改 + ADR 化 + CI 4 件套首批（v4.2 详细施工单 / **v1.1 当前生效版**）

> **主控文档**：[`./README.md`](./README.md)（§6 PR-1 / §3 H4 / §4 CI 守门表）
> **方案文档**：[`../../../doc/MOBILE_QA_WORKFLOW_STATE_SYNC_OPTIMIZATION_V1.1_2026-04-21.md`](../../../doc/MOBILE_QA_WORKFLOW_STATE_SYNC_OPTIMIZATION_V1.1_2026-04-21.md) §3.1 / §3.2.22
> **关联 V1.1 项**：O1 + O2 + O3 + O4+ + O5(部分: 2 个 sync 脚本 + AUTOGEN 头) + O6 + O22(部分: 4 个 CI 脚本 + workflow 集成)
> **历史版本**：[`./pr-1-foundation-cleanup-and-ci-bootstrap.md`](./pr-1-foundation-cleanup-and-ci-bootstrap.md)（v1.0 快照，已 superseded）+ [`./pr-1-foundation-cleanup-and-ci-bootstrap-REVIEW-2026-04-21.md`](./pr-1-foundation-cleanup-and-ci-bootstrap-REVIEW-2026-04-21.md)（v1.0 review 报告 / 2 阻断 + 3 高优）
> **状态**：📐 已展开（v1.1，2026-04-21；review 整体修订后）
> **唯一职责**：把 v4.2 收敛方案中 **主路径零运行时变更** 的"地基整改 + 文档结构化 + CI 兜底首批"一次性合入，作为后续 PR-2 ~ PR-7 的前置依赖（H4：ADR 必须先于代码 PR；CI 首批必须先于 enum / 契约 / 宏标签变更）。本 PR **不动** `core/workflow.xml` 任何运行时分支、**不动** 任何 phase 内 `<step-pause>`、**不动** 任何 wrapper 输入契约；所有改动按 v1.0 → v1.1 修订后分类如下：① 单值漂移修正（O1/O2，纯 enum 对齐）② **legacy agent 文件归档（O3，⚠️ 兼容性敏感 — 触达主流程 + deep-dive 双侧 legacy 恢复链路，需本地回放验证）** ③ ADR 目录基础设施（O4+，含 ADR-010 / ADR-021 草稿）④ phase 文件幂等性注释（O6，**6 个**主流程 phase 文件）⑤ 顶部同步声明 + 4 个 CI 守门脚本（O5/O22，全部默认 error 等级，但 `check-system-prompt-sync.sh` 与 `check-io-contract.sh` PR-1 阶段降级为 warning，PR-2 评估升级 error，详见主控 §4 + 本文 §2.5）。

---

## 0. v1.0 → v1.1 修订摘要（按 review 4 项 Patch 块组织）

> 本节是 v1.1 相对 v1.0 的**结构性变化总览**，便于 reviewer 快速定位增量；具体改动文本见对应章节。**v1.0 主体骨架完全保留**，本次仅做"事实对齐 + CI 重设计 + 定性修订 + 议题补全"四类改动，**未引入新的 V1.1 项**。

| Patch 块 | 触发 review 项 | 改动章节 | 改动性质 |
|---|---|---|---|
| **A — 结构对齐** | F3.1 阻断 / F4.1 高优 | §1 涉及文件清单 / §2.3 O3 三个变更点 / §2.6 phase 清单 | 事实对齐：删除不存在的 `functionality-deep-dive/core/core-rules.xml`；O3 改回主流程 `core/core-rules.xml`；不引入新 `<agent file=...>` 属性；phase 清单按 ls 实际：6 个文件且 P5 实名 `p5-fix-impl.md` |
| **B — CI 重设计** | F3.2 阻断 / F4.2 高优 / F5.1 次要 | §2.5.3 `check-system-prompt-sync.sh` / §2.5.4 `check-io-contract.sh` / §2.5.5 `check-subagent-params.sh` | CI 算法重写：sync 脚本改为"声明块对声明块"+ PR-1 阶段只校验高风险 token 白名单；io-contract 脚本改为"basename 匹配模型"；subagent-params 补完整 arbiter 实现 + 反向断言。`check-io-contract.sh` 与 `check-system-prompt-sync.sh` 严重度 PR-1 降为 warning |
| **C — 定性修订** | F4.3 高优 | §1 顶部"唯一职责" / §1 元信息表"层级"列 / §3.2 老会话回放升级 | "零运行时变更"改为"**主路径零运行时 + O3 legacy 恢复链路兼容性触达**"；§1 层级 🟢 → 🟡；§3.2 v3-legacy 老会话回放从动态用例升级为**合入门禁**，且回放范围扩展到主流程 + deep-dive 双侧 |
| **D — 议题与隐藏风险** | F5.2 次要 + 隐藏 H1-H4 | §6 议题汇总（5 项 → 9 项） | 新增 H1 同名 agent 误移防御 / H2 主流程 `workflow_version=legacy` 与 deep-dive `workflow_version=v3-legacy` 双侧默认值差异 / H3 `functionality-deep-dive/core/workflow.xml` load 引用核查 / H4 system-prompt.md P1 phase step 编号修复细节简化 + 工作量必做/follow-up 拆分 |

**v1.0 → v1.1 量化对比**：
- 总章节结构不变（§1 ~ §6 + Changelog）
- 变更点编号约定不变（S/A/D/R/H/N/W/C 前缀）
- 总变更点数：30 → ~28（PHASE-C7 删除；DD-D1 由"新增 file 属性"改为"升级文本内容"，等价点数 -1；§2.5 CI 脚本设计重写但点数不变）
- 工作量上限保持 0.9d（含 §6 议题 #6 必做/follow-up 拆分作为兜底）

---

## 1. PR 元信息

| 项 | 值 |
|---|---|
| 分支命名 | `feat/qa-workflow-v4.2-pr1-foundation-cleanup-and-ci-bootstrap` |
| Base | 当前 `main`（无前置 PR） |
| 层级 | 🟡 **文档 + CI 层 + legacy 兼容触达**（v1.1 修订）：主路径零运行时改动；O3 移动 5 个废弃 agent 文件 + 修订对应声明文本时**触达主流程 + deep-dive 双侧 legacy 恢复链路**（详见 §6 议题 H1/H2/H3） |
| 目标合入顺序 | **PR-1 → PR-2 → (PR-3 ‖ PR-4) → PR-5 → PR-6 → PR-7**（详见主控 §2 依赖图） |
| Reviewer | 1 名方案 owner（必看 ADR-021 首段命名冲突规避是否到位 / ADR-010 草稿与 O10+ Stage-1 对齐 / 4 CI 脚本算法正确性 — 含 v1.1 重设计后的 io-contract basename 匹配模型与 sync 声明块比对模型）+ 1 名平台 owner（必看 O3 归档后 v3-legacy 会话**主流程 + deep-dive 双侧**回放可用 / system-prompt.md 顶部 AUTOGEN 头部不破坏现有 Limited 平台单 prompt 注入） |
| 关联 V1.1 项 | O1（P2 单值漂移）/ O2（P1 + system-prompt 重复 step 编号）/ O3（5 个 deep-dive agent 归档 + **现存元素文本升级**，**不引入新 DSL 属性**）/ O4+（17 份历史文档归档 + `doc/adr/` 建立 + 21 个 ADR 文件 + 散布注释**短引用化**仅做不删长块）/ O5（顶部 AUTOGEN 声明 + 2 个 sync 脚本，含 v1.1 重设计的"声明块对声明块"算法）/ O6（**6 个**主流程 phase 文件加幂等性约束注释）/ O22（4 个 CI 脚本 + `.github/workflows/qa-workflow-schema-check.yml` 集成；`check-io-contract.sh` 与 `check-system-prompt-sync.sh` PR-1 阶段为 warning） |
| 工作量 | **0.9d**（v1.1 拆分必做 / follow-up：必做 ≈ 0.7d；follow-up 候选 ≈ 0.2d，详见 §6 议题 #6） |
| 涉及文件 | **新增**：`doc/adr/000-index.md` + `doc/adr/001-current-phase-result-runtime-only.md` + `doc/adr/008-step-pause-userinputs-namespace.md` + `doc/adr/014-step-pause-scope-restriction.md` + `doc/adr/015-userinputs-mirror-allowlist.md` + `doc/adr/016-step-pause-required-params.md` + `doc/adr/017-non-bug-context-persistence.md` + `doc/adr/018-parse-error-circuit-breaker.md` + `doc/adr/019-legacy-step-pause-allowlist.md` + `doc/adr/010-step-pause-registry-data-driven.md`（**草稿，PR-5 落地依赖**）+ `doc/adr/021-phase-abort-macro-tags.md`（**草稿，PR-3 落地依赖；首段命名冲突规避**）+ ~10 个 D2-D13 ADR 文件（兜底）+ `mobile-qa-workflow/scripts/check-state-enum.sh` + `mobile-qa-workflow/scripts/check-system-prompt-sync.sh` + `mobile-qa-workflow/scripts/check-io-contract.sh` + `mobile-qa-workflow/scripts/check-subagent-params.sh` + `mobile-qa-workflow/archive/v4.1-history/`（17 份历史文档归档目标目录）+ `mobile-qa-workflow/functionality-deep-dive/agents/archive/v3-legacy/`（5 个 agent 归档目标目录）。**修改**：`mobile-qa-workflow/phases/p2-spec-definition.md`（O1）+ `mobile-qa-workflow/system-prompt.md`（O2 + O5 顶部声明 + O4+ 短引用化）+ **`mobile-qa-workflow/core/core-rules.xml`**（v1.1 修订：O3 5 个 legacy agent 文本升级，**保留 `<agent name=... scenario=...>文本</agent>` 现有结构，不引入 `file=` / `deprecated=` 属性**）+ `mobile-qa-workflow/functionality-deep-dive/agents/README.md`（O3 退役标注升级；v1.1 修订：**同时补齐当前缺失的 challenger / arbiter 到清单**）+ **`mobile-qa-workflow/functionality-deep-dive/core/workflow.xml`**（v1.1 修订：仅当 grep 命中 5 个废弃 agent 名字符串时才修订；详见 §2.3.1 备注 + §6 议题 H3）+ **6 个** `mobile-qa-workflow/phases/p{1-intake,2-spec-definition,3-root-cause,4-fix-design,5-fix-impl,6-verification}.md`（O6 注释；按 ls 实际清单 6 个，**v1.1 修订**：v1.0 误写 7 个）+ `.github/workflows/qa-workflow-schema-check.yml`（追加 4 个 CI step）+ `mobile-qa-workflow/QUALITY-AUDIT-*.md` 等 17 份历史文档（移动到 archive 目录）+ `mobile-qa-workflow/functionality-deep-dive/agents/{context-reconstructor,state-analyst,temporal-analyst,challenger,arbiter}.md` 5 个文件（移动到 archive 目录；**v1.1 修订**：明确"仅 deep-dive 子目录下的 challenger/arbiter，不要误移主流程同名 agent"，详见 §6 议题 H1）。**删除**：无（O3 + O4+ 全部"归档而非删除"，禁止物理删除 / V1.1 §3.1 / F2 finding）。 |
| 不在本 PR 范围 | ① O4+ Step 3 中"长注释整体删除"（依赖 O21 宏标签，留待 PR-3 + PR-6）② `core/workflow.xml` 任何运行时改动（PR-2 + PR-5 范围）③ system-prompt.md 自动构建（PR-2 交付生成器、PR-6 首次构建）④ Spec-Uncertain 契约统一（PR-4 范围）⑤ phase 出口宏标签改写（PR-3 范围）⑥ wrapper 输入契约 `[Schema-Violation]` 校验（PR-7 范围）⑦ `check-build-system-prompt-precondition.sh` / `check-phase-abort-structure.sh` / `check-step-pause-registry.sh`（分别由 PR-2 / PR-3 / PR-5 启用，详见主控 §4）⑧ **新增 DSL 属性如 `<agent file=...>` / `deprecated=...`**（v1.1 修订：明确不在本 PR 范围；如未来需要由专门的 DSL 升级 PR 单独评估） |

---

## 2. 文件级 diff 列表

> 本 PR 共 **6 类变更点**（v1.1 修订后总数 ~28 个），按"先单值修正 → 再归档 → 再 ADR 基建 → 再 CI 兜底 → 再注释收口"的顺序排列：
>
> | 编号前缀 | 含义 | 数量（v1.1） |
> |---|---|---|
> | **P2-S1** | O1 单值漂移修正 | 1 |
> | **P1-S1 / SP-S1** | O2 重复 step 编号修正 | 2 |
> | **DD-A1~A5 / DD-D1 / DD-R1** | O3 deep-dive agent 归档 + 退役标注（v1.1 重写 DD-D1） | 7 |
> | **DOC-A1 / ADR-D1~D11'** | O4+ 历史文档归档 + ADR 目录建立 + 散布注释短引用化 | 13 |
> | **SP-H1 / CI-N1~N4 / CI-W1** | O5 顶部声明 + O22 4 件套（v1.1 重写 N2/N3/N4）+ workflow 集成 | 6 |
> | **PHASE-C1~C6** | O6 **6 个**主流程 phase 文件幂等性约束注释（v1.1 修订：v1.0 误写 7 个） | 6 |
>
> **变更点编号约定**：S\* = 单值漂移修正 / A\* = 文件归档 / D\* = 文件级声明或 ADR 草稿 / R\* = README 升级 / H\* = 头部 AUTOGEN 声明 / N\* = 新增 CI 脚本 / W\* = workflow yml 集成 / C\* = 注释级幂等性约束。

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

### 2.2 文件 B · `mobile-qa-workflow/phases/p1-intake.md`（核查后判定）+ `mobile-qa-workflow/system-prompt.md`（修改 / O2）

#### 2.2.1 变更点 P1-S1 · `phases/p1-intake.md` 仅做核查断言（O2 phase 侧 / 无 diff）

**说明**：`phases/p1-intake.md` 当前 grep `^\s*<step n="5"` 命中精确 1 处（L74，"最小信息集门禁"），**已不存在重复**；V1.1 §3.1 O2 描述的 L200-206 重复是 v3 残留口径。本 PR 不动 phase 文件，仅在 PR description 与 §3 DoD 中显式断言。

**新文**：无文件改动；PR description 必须附 `grep -nE '^\s*<step n="5"' mobile-qa-workflow/phases/p1-intake.md` 输出（≤ 1 行）作为核查证据。

---

#### 2.2.2 变更点 SP-S1 · `system-prompt.md` P1 phase 内 `step n="5"` 重复修正（O2 system-prompt 侧 / **v1.1 简化**）

**原文（行号锚点 L200-206）**：

```200:206:mobile-qa-workflow/system-prompt.md
    <step n="5" goal="优先级评估">
        ...
    </step>
    <step n="5" goal="输出 Issue Card">
```

**新文**（**仅** 把 L203 的 `step n="5"` 改写为 `step n="6"`；**v1.1 修订**：经 grep 核查，P1 phase 内仅这 2 个 step 编号、**无后续 step 6/7 需要顺延** — v1.0 描述的"如有 step 6/7 则顺延"已确认为冗余说法，删除）：

```xml
    <step n="5" goal="优先级评估">
        ...
    </step>
    <step n="6" goal="输出 Issue Card">
```

**修订理由**：
- `step n` 编号仅作 LLM 顺序提示，不参与运行时分支判断；修正后避免"第 5 步执行两次"的潜在歧义（V1.1 §3.1 O2）。
- 仅修复 P1 phase 内的 1 处明显重复；其余 6 处 `step n="5"`（L255 / L296 / L337 / L399 / L444 等）分布在 P2 ~ P6 的不同 phase 内，**不属重复**（每个 phase 各自从 step 1 开始编号），不在本 PR 范围。

**兼容性影响**：纯文档行号调整；下游 LLM 推理读到连续编号的 step 列表，行为完全等价。

---

### 2.3 文件 C · O3 deep-dive agent 归档 + 退役标注（5 个文件移动 + 2 个文件修改 / **v1.1 修订**）

> **修复条目锚点**：V1.1 §3.1 O3（F2 修订：归档而非物理删除）
> **v1.1 修订重点**：DD-D1 完全重写（不引入 `file=` / `deprecated=` 属性 — 见 review F3.1）；DD-R1 同时补齐 README 现存的 challenger / arbiter 缺失项；DD-A4/A5 增加"不要误移主流程同名 agent"反向断言

#### 2.3.1 变更点 DD-A1 ~ DD-A5 · 5 个废弃 agent 文件归档（O3 Step 1）

**操作**：把以下 5 个文件**移动**到 `mobile-qa-workflow/functionality-deep-dive/agents/archive/v3-legacy/` 子目录（git mv，保持历史）：

| 序号 | 源路径 | 目标路径 | 备注（v1.1 新增） |
|---|---|---|---|
| DD-A1 | `mobile-qa-workflow/functionality-deep-dive/agents/context-reconstructor.md` | `.../archive/v3-legacy/context-reconstructor.md` | 当前 200+ 行有效定义（QUALITY-AUDIT-REPORT.md L196 描述） |
| DD-A2 | `mobile-qa-workflow/functionality-deep-dive/agents/state-analyst.md` | 同上目录 | 同上 |
| DD-A3 | `mobile-qa-workflow/functionality-deep-dive/agents/temporal-analyst.md` | 同上目录 | 同上 |
| DD-A4 | `mobile-qa-workflow/functionality-deep-dive/agents/challenger.md` | 同上目录 | ⚠️ **仅限 deep-dive 子目录下的文件**；**不要误移**主流程 `mobile-qa-workflow/agents/challenger.md`（同名但是主流程现役 agent）；当前为 Legacy Wrapper 薄文件（QUALITY-AUDIT-REPORT.md L137） |
| DD-A5 | `mobile-qa-workflow/functionality-deep-dive/agents/arbiter.md` | 同上目录 | ⚠️ **仅限 deep-dive 子目录下的文件**；**不要误移**主流程 `mobile-qa-workflow/agents/arbiter.md`；当前为 Legacy Wrapper 薄文件 |

**v1.1 修订强制断言**（PR description 必须附 grep 证据）：
1. `git diff --name-status` 中**不包含** `mobile-qa-workflow/agents/challenger.md` 或 `mobile-qa-workflow/agents/arbiter.md`（防止误移主流程文件）
2. `mobile-qa-workflow/functionality-deep-dive/agents/archive/v3-legacy/` 目录下精确含 5 个文件（git mv 完整性）

**修订理由**：
- F2 finding：子编排器 `functionality-deep-dive/core/workflow.xml:21-30` 仍包含老会话恢复逻辑（按 `workflow_version=v3-legacy` 与 `legacy_flow_mode=true` 走老路径），物理删除会破坏 v3-legacy 会话恢复（V1.1 §3.1 O3）。
- 归档后老会话恢复路径若依赖动态 agent name 解析，仍可加载（与变更点 DD-D1 文本升级配套生效）。

**兼容性影响**（v1.1 修订 / 重要变化）：
- **核查方法**（必跑）：`grep -nE 'context-reconstructor|state-analyst|temporal-analyst' mobile-qa-workflow/functionality-deep-dive/core/workflow.xml`
- **二选一处理**：
  - 若 grep 命中 → DD-A1~A3 路径修正（属 `<load target="archive/v3-legacy/...">` 这类显式引用）必须作为本变更点的强制配套动作（不单独编号），且本 PR description 必须附 grep 命中清单 + 修正 diff
  - 若 grep 未命中 → deep-dive 子工作流按动态 name 解析或主 core-rules.xml 派发，归档后行为等价；本 PR description 显式注明"grep 全空，无路径修正"
- 详见 §6 议题 H3

---

#### 2.3.2 变更点 DD-D1 · `mobile-qa-workflow/core/core-rules.xml` L92-96 文本升级（O3 Step 2 / **v1.1 完全重写**）

> **v1.1 重写说明**：v1.0 把目标文件错写为 `functionality-deep-dive/core/core-rules.xml`（不存在）+ 引入 `<agent file=... deprecated=... recovery_only=...>` 新 DSL 属性（review F3.1 阻断）；v1.1 改为：① 目标文件改回主流程 `mobile-qa-workflow/core/core-rules.xml`；② **保留** `<agent name=... scenario=...>文本内容</agent>` 现有元素结构；③ 仅升级**文本内容**为更明确的退役标注；④ **不引入任何新 DSL 属性**。

**原文（行号锚点 L92-96）**：

```92:96:mobile-qa-workflow/core/core-rules.xml
                        <agent name="context-reconstructor" scenario="兼容旧会话">已废弃，仅供历史会话恢复</agent>
                        <agent name="state-analyst" scenario="兼容旧会话">已废弃，仅供历史会话恢复</agent>
                        <agent name="temporal-analyst" scenario="兼容旧会话">已废弃，仅供历史会话恢复</agent>
                        <agent name="challenger" scenario="兼容旧会话">已废弃，仅供历史会话恢复</agent>
                        <agent name="arbiter" scenario="兼容旧会话">已废弃，仅供历史会话恢复</agent>
```

**新文**（5 行**保留 DSL 结构**，仅升级文本内容；**不**新增任何属性）：

```xml
                        <agent name="context-reconstructor" scenario="兼容旧会话">已退役（v3-legacy 会话恢复专用 / 物理文件已归档至 functionality-deep-dive/agents/archive/v3-legacy/ / 详见 ADR-019）；新会话禁用</agent>
                        <agent name="state-analyst" scenario="兼容旧会话">已退役（v3-legacy 会话恢复专用 / 物理文件已归档至 functionality-deep-dive/agents/archive/v3-legacy/ / 详见 ADR-019）；新会话禁用</agent>
                        <agent name="temporal-analyst" scenario="兼容旧会话">已退役（v3-legacy 会话恢复专用 / 物理文件已归档至 functionality-deep-dive/agents/archive/v3-legacy/ / 详见 ADR-019）；新会话禁用</agent>
                        <agent name="challenger" scenario="兼容旧会话">已退役（v3-legacy 会话恢复专用 / 物理文件已归档至 functionality-deep-dive/agents/archive/v3-legacy/ / 详见 ADR-019）；新会话禁用 / 与同 agent-group main-workflow 中的 challenger 同名但隔离</agent>
                        <agent name="arbiter" scenario="兼容旧会话">已退役（v3-legacy 会话恢复专用 / 物理文件已归档至 functionality-deep-dive/agents/archive/v3-legacy/ / 详见 ADR-019）；新会话禁用 / 与同 agent-group main-workflow 中的 arbiter 同名但隔离</agent>
```

**修订理由**：
- **v1.1 核心变化**：目标文件改回主流程 `core/core-rules.xml`（review F3.1 阻断）；保持 DSL 结构纯净，**不引入新属性**——后续如有 DSL 升级需求（如 `deprecated="true"` 元属性），由专门的 DSL 升级 PR 单独评估，不在 PR-1 范围。
- 文本内容升级承担三重信息：① 退役状态明确化；② 物理路径指向 archive 目录（与 DD-A1~A5 配套）；③ ADR-019 引用作为 D19 legacy step-pause allowlist 语义复用；④ challenger / arbiter 显式标注与 main-workflow 同名 agent 的隔离关系（防止 LLM 解析时误派发）。

**兼容性影响**：
- **纯文本内容修改 + 零属性变更** → DSL parser 无任何感知；现有 LLM 静态读 core-rules.xml 不报错。
- LLM 动态派发时若按 `name` + `agent-group` 双键解析（实际 deep-dive vs main-workflow 各自有独立 group 容器），新会话将永远命中 main-workflow 内的 challenger/arbiter，不会落到 deep-dive 退役项；老会话按 `workflow_version` 路由命中 deep-dive group 后仍可加载 archive/v3-legacy/ 路径下的物理文件。
- CI 守门 CI-N1 (`check-state-enum.sh`) 不涉及该文件；`check-system-prompt-sync.sh` (CI-N2) v1.1 重设计后比对的是"权威枚举声明块"，与 agent 声明无关，不会反向阻塞本变更点。

---

#### 2.3.3 变更点 DD-R1 · `functionality-deep-dive/agents/README.md` 退役标注升级（O3 Step 3 / **v1.1 修订**）

> **v1.1 修订**：当前 README L11-13 仅列了 3 个废弃 agent（context-reconstructor / state-analyst / temporal-analyst），与 `core/core-rules.xml` L92-96 列出的 5 个不一致；本变更点同步补齐 challenger / arbiter，消除仓库现存口径漂移。

**操作**：把现有 L10-17 的"已废弃但保留兼容"段落升级为：

```markdown
## 已退役（仅 v3-legacy 会话恢复 / v4.2 PR-1 落地）

以下 5 个 agent 在 v4 之后**新会话不再使用**，物理文件已归档至 `archive/v3-legacy/`：

- `context-reconstructor.md`
- `state-analyst.md`
- `temporal-analyst.md`
- `challenger.md`（**v1.1 新增到清单** — deep-dive 子目录下，**不影响**主流程 `mobile-qa-workflow/agents/challenger.md`；当前为 Legacy Wrapper 薄文件）
- `arbiter.md`（**v1.1 新增到清单** — deep-dive 子目录下，**不影响**主流程 `mobile-qa-workflow/agents/arbiter.md`；当前为 Legacy Wrapper 薄文件）

**退役原因**：deep-dive 子工作流 v4 已收敛为本目录其余 5 个新 agent（详见 README 上半段 + `core/workflow.xml`）。

**v4.3 物理删除前提**（来自 V1.1 §3.1 O3）：
1. 所有持久化会话的 `schema_version ≥ 4`（CI 守门：`check-state-enum.sh` 兜底）
2. 90 天内零 v3-legacy 流量（按 `workflow_version=v3-legacy` 与 `legacy_flow_mode=true` 标记的会话计数为 0；**注意**：主流程 `core/workflow.xml` 的 v3 兼容默认值是 `workflow_version = legacy`，与 deep-dive 的 `v3-legacy` 是不同字符串值，统计时需双侧累加；详见本 PR §6 议题 H2）
3. 主流程与 deep-dive 子流程均无 `<load target="archive/v3-legacy/...">` 残留引用（grep 验证）

**当前状态**（v4.2 PR-1 落地）：
- 物理文件位置：`functionality-deep-dive/agents/archive/v3-legacy/` 下 5 个 .md
- DSL 声明位置：主流程 `core/core-rules.xml` L92-96，5 个 `<agent name=... scenario="兼容旧会话">` 元素，文本内容已升级为"已退役（v3-legacy 会话恢复专用 / 详见 ADR-019）；新会话禁用"
- 物理删除推迟到 v4.3 立项
```

**修订理由**：
- 把"已废弃但保留兼容"的口头约束升级为"退役条件 + 删除前提"的可验证清单。
- **v1.1 修订重点**：补齐 README 缺失的 challenger / arbiter，消除仓库现存口径漂移；明确**不影响**主流程同名 agent，避免 reviewer 误读。
- 显式标注主流程 `legacy` 与 deep-dive `v3-legacy` 是**不同字符串值**（来自核查：主流程 `core/workflow.xml` L30 写 `workflow_version = legacy`，deep-dive `functionality-deep-dive/core/workflow.xml` L27 写 `workflow_version = v3-legacy`），为 v4.3 流量统计提供准确口径。

**兼容性影响**：纯文档改写；不影响任何运行时。

---

### 2.4 文件 D · O4+ 历史文档归档 + ADR 目录建立 + 散布注释短引用化

> **本节 v1.0 → v1.1 无实质改动**（review 未对 §2.4 提出 finding；ADR-021 命名冲突规避声明、ADR-010/021 草稿状态、短引用化范围全部保留）。
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

**修订理由 / 兼容性影响**：与 v1.0 一致 —— 消除根目录视觉干扰；归档后路径仍可被显式 `<load>` 加载；grep 全仓库验证两份核心文档保留在原位，其余 17 份的引用预期 ≤ 5 处需修正为 `archive/v4.1-history/...`，作为本变更点的强制配套修复（PR description 附 grep 修正清单）。

---

#### 2.4.2 变更点 ADR-D1 ~ ADR-D11 · `doc/adr/` 目录建立 + 21 个 ADR 文件首批落地（O4+ Step 2 / H4 ADR 必须先于代码 PR）

**操作**：

1. 新建 `doc/adr/` 目录 + `doc/adr/000-index.md`（ADR 索引文件，列出 D1-D19 + 新增 D20+ 的映射）
2. 按 V1.1 §3.1 O4+ Step 2 的命名规范（`<NNN>-<slug>.md`）落地以下 21 个 ADR 文件（与 v1.0 表完全一致，此处不再重复展开 — 详见 v1.0 §2.4.2 表）

**ADR-021 首段命名冲突规避示例文本**（必须逐字落地，与 v1.0 一致）：

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

**修订理由 / 兼容性影响**：与 v1.0 一致 —— 满足主控 §3 H4 强约束；ADR 文件不增加运行时 token 预算。

---

#### 2.4.3 变更点 ADR-D11' · 散布注释短引用化（O4+ Step 3 / 仅"短引用化"，长注释删除留待 PR-3 + PR-6）

**操作 / 修订理由 / 兼容性影响**：与 v1.0 一致 —— 全仓库扫描 `<!-- D\d+: ... -->` 与 `# D\d+: ...` 形式的短注释，替换为 `<!-- ADR-NNN -->` / `# ADR-NNN` 单行引用；本 PR 不动长注释块（≥ 5 行），留待 PR-3 / PR-6 由 O21 宏标签自然吃下；预期净减 30~50 行（v1.0 给出的细化估算保留）。

---

### 2.5 文件 E · O5 头部 AUTOGEN 声明 + O22 4 个 CI 脚本 + workflow 集成（**v1.1 重写 N2/N3/N4**）

> **修复条目锚点**：V1.1 §3.1 O5（顶部声明 + 2 个 sync 脚本）+ §3.2.22（4 件套补全）；与主控 §4 CI 守门表"PR-1 启用 4 项"对齐
> **v1.1 重写说明**：基于 review F3.2 阻断 + F4.2 高优 + F5.1 次要，重写 CI-N2（声明块对声明块）、CI-N3（basename 匹配模型）、CI-N4（补完整 arbiter 实现 + 反向断言）；CI-N2 与 CI-N3 的 PR-1 阶段严重度从 error 降为 warning，PR-2 评估升级 error。

#### 2.5.1 变更点 SP-H1 · `system-prompt.md` 头部加 AUTOGEN 声明（O5 Step 1 / **v1.1 增补 ENUM 声明块要求**）

> **v1.1 修订**：在 v1.0 基础上**额外**要求 system-prompt.md 内含一个被 `<!-- ENUM-DECLARATION-BLOCK -->` ... `<!-- /ENUM-DECLARATION-BLOCK -->` 包裹的权威枚举声明块（供 CI-N2 比对）。

**新文**（在 H1 标题之前**插入** AUTOGEN 声明块 + ENUM 声明块）：

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

<!-- ENUM-DECLARATION-BLOCK -->
<!--
本块由 CI `check-system-prompt-sync.sh` 与 core/workflow-status-template.yaml 头部 enum 集做"声明块对声明块"严格比对。
本块内容必须与 core/workflow-status-template.yaml 头部 v4.1 完整集合 100% 一致（含顺序 + 名称大小写）。
v4.1 完整集合（按 workflow-status-template.yaml 头部顺序）：
  Intake, Spec-Defining, Spec-Uncertain, Context-Curating, Curation-Failed, Boundary-Refined,
  Non-Bug, Info-Insufficient, RCA-Designing, RCA-LowConfidence, Fix-Designing, Fix-Implementing,
  Verifying, Human-Review, Done
-->
<!-- /ENUM-DECLARATION-BLOCK -->

# Mobile QA Workflow — System Prompt
（原首段）
```

**修订理由**：
- v1.0 首版只加 AUTOGEN 头；v1.1 同步落地 ENUM 声明块，让 CI-N2 v1.1 重设计的"声明块对声明块"算法有可比对的目标。
- ENUM 声明块完整列出 15 个 v4.1 状态名（按 `core/workflow-status-template.yaml` 头部注释口径），作为 single source of truth 的 mirror。

**兼容性影响**：纯注释新增；HTML 注释不影响 markdown 渲染或 LLM 推理。

---

#### 2.5.2 变更点 CI-N1 · `mobile-qa-workflow/scripts/check-state-enum.sh` 新建（O22 #1 / O5 配套 / **v1.1 无变化**）

**新文件内容**（约 ~40 行 bash，要点 — 与 v1.0 一致）：

```bash
#!/usr/bin/env bash
# check-state-enum.sh
# 守门：current_state 写入值必须落在 workflow-status-template.yaml 头部 enum 集内
# 关联：V1.1 §3.1 O5 配套 / §3.2.22 / 主控 §4 PR-1 启用
# 等级：error（PR-1 启用即生效）

set -euo pipefail
cd "$(dirname "$0")/.."

ENUM_FILE="core/workflow-status-template.yaml"
ALLOWED=$(awk '/v4.1 完整集合/,/^[^#]/' "$ENUM_FILE" \
  | grep -oE '[A-Z][A-Za-z-]+' | sort -u)

HITS=$(grep -rEn 'current_state\s*=\s*[A-Z][A-Za-z-]+' \
  phases/ system-prompt.md core/workflow.xml \
  | sed -E 's/.*current_state\s*=\s*([A-Z][A-Za-z-]+).*/\1/' | sort -u)

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

**修订理由 / 兼容性影响**：与 v1.0 一致；与变更点 P2-S1 形成"代码修正 + CI 守门"完整闭环。

---

#### 2.5.3 变更点 CI-N2 · `mobile-qa-workflow/scripts/check-system-prompt-sync.sh` 新建（O22 #2 / **v1.1 完全重写**）

> **v1.1 重写说明**：v1.0 用"赋值集对完整 enum 集"对比（review F4.2 高优：长期告警噪音）；v1.1 改为"权威枚举声明块对声明块" + PR-1 阶段只校验 2 个高风险 token（兜底），严重度 PR-1 = warning（PR-2 升级 error 由 PR-2 PR description 切换）。

**新文件内容**（约 ~70 行 bash + python 混合）：

```bash
#!/usr/bin/env bash
# check-system-prompt-sync.sh (v1.1)
# 守门：system-prompt.md 与 core/ 关键 token 必须同步
# 关联：V1.1 §3.1 O5 配套 / 主控 §4 PR-1 启用为 warning，PR-2 升级为 error
# v1.1 算法：声明块对声明块 + 高风险 token 白名单

set -euo pipefail
cd "$(dirname "$0")/.."

SEVERITY="${SP_SYNC_SEVERITY:-warning}"
fail=0

# ──────────────────────────────────────────────────────────
# 校验 1：ENUM 声明块严格相等
# 提取 system-prompt.md 中 <!-- ENUM-DECLARATION-BLOCK --> ... <!-- /ENUM-DECLARATION-BLOCK -->
# 内的状态名集合，与 core/workflow-status-template.yaml 头部 enum 集做集合相等比对
# ──────────────────────────────────────────────────────────
ENUM_CORE=$(awk '/v4.1 完整集合/,/^[^#]/' core/workflow-status-template.yaml \
  | grep -oE '[A-Z][A-Za-z-]+' | sort -u)

ENUM_SP=$(python3 -c "
import re, sys
content = open('system-prompt.md').read()
m = re.search(r'<!-- ENUM-DECLARATION-BLOCK -->(.*?)<!-- /ENUM-DECLARATION-BLOCK -->', content, re.S)
if not m:
    print('__MISSING__'); sys.exit(0)
names = re.findall(r'\b([A-Z][A-Za-z-]+)\b', m.group(1))
# 过滤非状态名 token（如 'PR-1' / 'workflow-status' 等小写或带数字）
states = sorted(set(n for n in names if not any(c.isdigit() for c in n) and '-' not in n[:1]))
for s in states: print(s)
")

if [ "$ENUM_SP" = "__MISSING__" ]; then
  echo "::${SEVERITY}::system-prompt.md 缺少 ENUM-DECLARATION-BLOCK 注释块（v1.1 PR-1 SP-H1 落地后必须存在）"
  [ "$SEVERITY" = "error" ] && fail=1
elif [ "$ENUM_CORE" != "$ENUM_SP" ]; then
  echo "::${SEVERITY}::ENUM-DECLARATION-BLOCK 与 core/workflow-status-template.yaml 头部 enum 集不一致"
  echo "core 独有: $(comm -23 <(echo "$ENUM_CORE") <(echo "$ENUM_SP") | tr '\n' ' ')"
  echo "sp 独有:   $(comm -13 <(echo "$ENUM_CORE") <(echo "$ENUM_SP") | tr '\n' ' ')"
  [ "$SEVERITY" = "error" ] && fail=1
fi

# ──────────────────────────────────────────────────────────
# 校验 2：高风险 token 白名单（PR-1 阶段兜底，PR-2 全量声明块比对后可降为可选）
# 2a) Spec-Uncertain allowed_values：当前 main 是 Confirm（v3 残留），PR-4 改为 1|2|S
#     PR-1 阶段不强校验取值，但要求 system-prompt.md 与 core/workflow.xml 出现的取值"字面一致"
# 2b) 关键 stop_state：Non-Bug / RCA-LowConfidence / Curation-Failed / Human-Review 必须在 system-prompt.md 中至少出现 1 次（基本完整性）
# ──────────────────────────────────────────────────────────
# 2a)
SU_CORE=$(grep -oE 'allowed_values=[^"]*' core/workflow.xml | head -1 || echo "")
SU_SP=$(grep -oE 'allowed_values=[^"]*' system-prompt.md | head -1 || echo "")
if [ -n "$SU_CORE" ] && [ -n "$SU_SP" ] && [ "$SU_CORE" != "$SU_SP" ]; then
  echo "::${SEVERITY}::Spec-Uncertain allowed_values 字面不一致 (core: $SU_CORE / sp: $SU_SP)"
  [ "$SEVERITY" = "error" ] && fail=1
fi

# 2b)
for state in "Non-Bug" "RCA-LowConfidence" "Curation-Failed" "Human-Review"; do
  if ! grep -q "$state" system-prompt.md; then
    echo "::${SEVERITY}::system-prompt.md 缺关键 stop_state 引用: $state"
    [ "$SEVERITY" = "error" ] && fail=1
  fi
done

[ $fail -eq 0 ] && echo "✅ check-system-prompt-sync.sh (v1.1) 通过（severity=$SEVERITY）"
exit $fail
```

**修订理由**：
- review F4.2：把"赋值集对完整集"改为"声明块对声明块"+"高风险 token 白名单"双校验，杜绝长期告警噪音。
- PR-1 阶段 severity = warning（避免被自身阻塞，因 system-prompt.md 中已知存在 v3 残留 token，需 PR-4 完成 Spec-Uncertain 契约统一才能消除 2a 校验项的可能告警）；PR-2 合入 system-prompt 生成器后，由 PR-2 PR description 把 severity 切到 error 并把校验 2 缩窄到"自动构建产物 diff = 0"。
- 严重度通过环境变量 `SP_SYNC_SEVERITY` 切换，workflow yml 集成时传 `warning`。

**兼容性影响**：PR-1 阶段为 warning，本 PR 不会被自身阻塞；如校验 2a 在 PR-1 落地时报告差异（Spec-Uncertain `Confirm` vs `1|2|S` 现状漂移），属预期 warning，由 PR-4 修复后自然消失。

---

#### 2.5.4 变更点 CI-N3 · `mobile-qa-workflow/scripts/check-io-contract.sh` 新建（O22 #3 / **v1.1 完全重写**）

> **v1.1 重写说明**：v1.0 假设 `<io-contract>` 内含 `file=` 属性（review F3.2 阻断：实际是 `output="basename列表"`，会得空集假绿）；v1.1 改为"basename 匹配模型"——把 `<io-contract>` 内每个 `<phase>` 的 `output` 属性按 `,` 拆分为 basename 列表（去掉前缀修饰词），对每个 basename grep 全 phase 文件中是否被任何 `<template-output>` 实际产出。严重度 PR-1 = warning（PR-2 评估是否升级 error）。

**新文件内容**（约 ~55 行 bash + python 混合）：

```bash
#!/usr/bin/env bash
# check-io-contract.sh (v1.1)
# 守门：core/workflow.xml <io-contract> 中每个 <phase output="..."> 声明的 basename
#       必须能在某个 phase 文件的 <template-output ... file="..."> 中被实际产出
# 关联：V1.1 §3.2.22 第 3 项 / 主控 §4 PR-1 启用为 warning（PR-2 评估升级 error）
# v1.1 算法：basename 匹配模型（兼容变量化路径如 file="{output_file}" / file="{workspace_folder}/spec.md"）

set -euo pipefail
cd "$(dirname "$0")/.."

SEVERITY="${IO_CONTRACT_SEVERITY:-warning}"

# ──────────────────────────────────────────────────────────
# Step 1：从 <io-contract> 中提取每个 <phase> 的 output 属性，
#         按 ',' 拆分并清理修饰词（"可选: " / "条件必需: " / "条件生成: " 等）
# ──────────────────────────────────────────────────────────
DECLARED=$(python3 - <<'PYEOF'
import re
content = open('core/workflow.xml').read()
m = re.search(r'<io-contract\b[^>]*>(.*?)</io-contract>', content, re.S)
if not m:
    raise SystemExit("ERROR: 未找到 <io-contract> 块")
phases = re.findall(r'<phase\s+name="([^"]+)"[^>]*output="([^"]+)"', m.group(1))
basenames = set()
for _, out in phases:
    # 去掉中文/英文修饰前缀
    out = re.sub(r'(可选|条件必需|条件生成)\s*[:：]\s*', '', out)
    for token in out.split(','):
        token = token.strip()
        # 抽出 *.md 类 basename
        bn = re.findall(r'[\w-]+\.md', token)
        basenames.update(bn)
for b in sorted(basenames): print(b)
PYEOF
)

# ──────────────────────────────────────────────────────────
# Step 2：从所有 phase 文件 + system-prompt.md 抽取 <template-output ... file="...">
#         的 file 属性，提取其中的 basename（含变量化路径的尾段）
# ──────────────────────────────────────────────────────────
ACTUAL=$(grep -hoE '<template-output[^/]*file="[^"]+"' phases/*.md system-prompt.md 2>/dev/null \
  | sed -E 's/.*file="([^"]+)".*/\1/' \
  | sed -E 's@.*/@@' \
  | grep -oE '[A-Za-z_-]+\.md|\{[a-z_]+\}' \
  | sort -u)

# ──────────────────────────────────────────────────────────
# Step 3：对每个 DECLARED basename，要么在 ACTUAL 中直接命中，
#         要么 ACTUAL 中存在变量化路径（{output_*}）—— PR-1 阶段允许变量化路径作为 wildcard 命中
# ──────────────────────────────────────────────────────────
fail=0
HAS_VARIABLE=$(echo "$ACTUAL" | grep -c '^{' || true)
for b in $DECLARED; do
  if echo "$ACTUAL" | grep -qx "$b"; then
    continue
  fi
  if [ "$HAS_VARIABLE" -gt 0 ]; then
    # 存在变量化路径时，PR-1 阶段降级为 info（PR-2 评估是否切到 strict 模式）
    echo "::notice::声明的 io-contract basename 未直接命中，但存在变量化路径兜底: $b"
    continue
  fi
  echo "::${SEVERITY}::声明的 io-contract basename 未被任何 phase 输出: $b"
  [ "$SEVERITY" = "error" ] && fail=1
done

[ $fail -eq 0 ] && echo "✅ check-io-contract.sh (v1.1) 通过（DECLARED=$(echo "$DECLARED" | wc -w) / ACTUAL=$(echo "$ACTUAL" | wc -w) / SEVERITY=$SEVERITY）"
exit $fail
```

**修订理由**：
- review F3.2：`<io-contract>` 实际写法核查后，重写为 basename 匹配模型；兼容变量化路径（如 `file="{output_file}"` 与 `output="spec.md"` 通过 `{output_*}` 通配符 wildcard 命中）。
- PR-1 阶段 severity = warning，避免现网未对齐情况下反向阻塞本 PR；PR-2 阶段（O7/O8 字段瘦身）评估升级 error 时机。
- 引入 `IO_CONTRACT_SEVERITY` 环境变量切换，与 `SP_SYNC_SEVERITY` 同款机制。

**兼容性影响**：PR-1 阶段为 warning；如本 PR 落地时发现 io-contract 与 phase 输出不一致（属现网历史漂移），本 PR description 必须列出"可接受 warning 清单"+"修复责任方（建议归 PR-2 处理）"。

---

#### 2.5.5 变更点 CI-N4 · `mobile-qa-workflow/scripts/check-subagent-params.sh` 新建（O22 #4 / **v1.1 补完整 arbiter + 反向断言**）

> **v1.1 重写说明**：v1.0 仅给 challenger 校验骨架，arbiter 侧写"略"（review F5.1 次要：error 级 CI 必须可被验证）；v1.1 补完整 arbiter 实现 + 反向断言（防 v2.2 PR-4 review Finding 2 角色驱动矩阵反转复发）。

**新文件内容**（约 ~70 行 bash + python 混合）：

```bash
#!/usr/bin/env bash
# check-subagent-params.sh (v1.1)
# 守门：invoke-subagent 调用按角色驱动注入 — challenger → confidence_input；arbiter → base_score
# 关联：V1.1 §3.2.22 第 4 项 / C2 类 Schema-Violation / 主控 §4 PR-1 启用为 error
# v1.1 增强：补完整 arbiter 实现 + 双向反向断言（角色字段矩阵反转 = error）

set -euo pipefail
cd "$(dirname "$0")/.."

fail=0

python3 - <<'PYEOF' || fail=$?
import re, glob, sys

err_count = 0
total_ch = 0
total_ar = 0

for fp in glob.glob('phases/*.md'):
    content = open(fp).read()
    # 抽出每个 <invoke-subagent ... /> 块（含跨行）
    blocks = re.findall(r'<invoke-subagent\b[^>]*?(?:subagent_type="(?P<type>[^"]+)")[^>]*?>.*?</invoke-subagent>|<invoke-subagent\b[^/]*?subagent_type="(?P<type2>[^"]+)"[^/]*?/>',
                        content, re.S)
    # 退化方案：按 subagent_type=" 切分块
    pieces = re.split(r'(?=subagent_type=")', content)
    for piece in pieces:
        m = re.match(r'subagent_type="([^"]+)"', piece)
        if not m: continue
        st = m.group(1)
        # 取本 invoke-subagent 块的合理上下文（到下一个 invoke-subagent 或 1000 字符截断）
        block = piece[:1000]

        if st == 'challenger':
            total_ch += 1
            if 'confidence_input' not in block:
                print(f"::error::{fp} : challenger 调用缺 confidence_input 注入")
                err_count += 1
            if 'base_score' in block:
                print(f"::error::{fp} : challenger 调用错误注入 base_score（角色矩阵反转 / v2.2 PR-4 review Finding 2）")
                err_count += 1

        elif st == 'arbiter':
            total_ar += 1
            if 'base_score' not in block:
                print(f"::error::{fp} : arbiter 调用缺 base_score 注入")
                err_count += 1
            if 'confidence_input' in block:
                print(f"::error::{fp} : arbiter 调用错误注入 confidence_input（角色矩阵反转 / v2.2 PR-4 review Finding 2）")
                err_count += 1

print(f"check-subagent-params.sh (v1.1): challenger={total_ch} / arbiter={total_ar} / errors={err_count}", file=sys.stderr)
sys.exit(1 if err_count else 0)
PYEOF

[ $fail -eq 0 ] && echo "✅ check-subagent-params.sh (v1.1) 通过"
exit $fail
```

**修订理由**：
- review F5.1：补完整 arbiter 校验逻辑，与 challenger 完全对偶。
- 双向反向断言：challenger 块内不得含 `base_score`、arbiter 块内不得含 `confidence_input`，防止 v2.2 PR-4 review 已经修复过的"角色驱动字段矩阵反转"复发。
- 当前 main 上 v2.2 PR-4 已合入，所有 challenger / arbiter 调用应已正确注入；本 PR 启用 error 不会引入回归（除非有未对齐残留）。

**兼容性影响**：纯 CI 守门；如本 PR 落地时发现 v2.2 PR-4 后又有新 challenger/arbiter 调用未注入，本 PR description 必须列出修复清单（建议归 PR-2 处理）。

---

#### 2.5.6 变更点 CI-W1 · `.github/workflows/qa-workflow-schema-check.yml` 集成 4 个 CI step（O22 / **v1.1 调整 N3 严重度**）

**操作**：在现有 8 项 schema/protocol 守门 step 之后**追加** 4 个 step：

```yaml
      # ════════════════════════════════════════════════════════════════
      # 检查 9（PR-1 启用）：state enum 守门 / V1.1 §3.1 O5 / 主控 §4 / 等级：error
      # ════════════════════════════════════════════════════════════════
      - name: Check 9 — state enum 守门
        run: bash mobile-qa-workflow/scripts/check-state-enum.sh

      # ════════════════════════════════════════════════════════════════
      # 检查 10（PR-1 启用 warning，PR-2 升级 error）：system-prompt sync 守门（v1.1 算法 = 声明块对声明块 + 高风险 token 白名单）
      # ════════════════════════════════════════════════════════════════
      - name: Check 10 — system-prompt sync 守门（PR-1: warning）
        env:
          SP_SYNC_SEVERITY: warning
        run: bash mobile-qa-workflow/scripts/check-system-prompt-sync.sh

      # ════════════════════════════════════════════════════════════════
      # 检查 11（PR-1 启用 warning，PR-2 评估升级 error）：io-contract 守门（v1.1 算法 = basename 匹配 + 变量化路径兜底）
      # ════════════════════════════════════════════════════════════════
      - name: Check 11 — io-contract 守门（PR-1: warning）
        env:
          IO_CONTRACT_SEVERITY: warning
        run: bash mobile-qa-workflow/scripts/check-io-contract.sh

      # ════════════════════════════════════════════════════════════════
      # 检查 12（PR-1 启用）：subagent-params 守门（v1.1 含双向反向断言）/ 等级：error
      # ════════════════════════════════════════════════════════════════
      - name: Check 12 — subagent-params 守门
        run: bash mobile-qa-workflow/scripts/check-subagent-params.sh
```

**修订理由**：
- v1.1 把 Check 11 (io-contract) 严重度从 error 降为 warning（review F3.2 阻断 + 现网未对齐风险）；同时主控 §4 表 PR-1 行的"`check-io-contract.sh` 默认 error"建议在 v4.2 README 联动登记摘要中同步调整为"PR-1 warning，PR-2 评估升级 error"（详见 §6 议题 #5 联动登记建议）。
- Check 9 / Check 12 仍为 error；Check 10 与 v1.0 一致仍为 warning。

**兼容性影响**：CI 总耗时增加 ~10-15 秒（v1.1 比 v1.0 增加 python 解析步骤）；不影响其余 8 项现有 step。

---

### 2.6 文件 F · O6 phase 文件级幂等性约束注释（**6 个**主流程 phase 文件 / PHASE-C1 ~ C6 / **v1.1 修订**）

> **v1.1 修订**：v1.0 误写 7 个 phase（含臆造的 `p4-implementation.md` / `p5-fix-implementation.md`），review F4.1 高优指出实际清单只有 6 个；v1.1 按 `ls phases/` 实际清单对齐。

#### 2.6.1 变更点 PHASE-C1 ~ C6 · 6 个主流程 phase 文件头部加注释（统一文本）

**操作**：在以下 6 个 phase 文件的 `<workflow-phase>` 根元素**之前**插入统一注释块：

| 编号 | 文件 |
|---|---|
| PHASE-C1 | `mobile-qa-workflow/phases/p1-intake.md` |
| PHASE-C2 | `mobile-qa-workflow/phases/p2-spec-definition.md` |
| PHASE-C3 | `mobile-qa-workflow/phases/p3-root-cause.md` |
| PHASE-C4 | `mobile-qa-workflow/phases/p4-fix-design.md` |
| PHASE-C5 | `mobile-qa-workflow/phases/p5-fix-impl.md` |
| PHASE-C6 | `mobile-qa-workflow/phases/p6-verification.md` |

**统一注释块文本**（与 v1.0 一致）：

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

**修订理由 / 兼容性影响**：与 v1.0 一致；v1.1 仅修正 phase 清单为 6 个（删除臆造的 PHASE-C5 `p4-implementation.md` 与 PHASE-C7，重新编号为 C1~C6）。

---

## 3. PR-level DoD 子集（链接到主控 §5）

> 完整跨平台矩阵见主控 [§5 跨平台回归矩阵](./README.md#5-跨平台回归矩阵每-pr-必跑)；本节仅列 PR-1 必须满足的子集。**v1.1 修订**：phase 注释 7 处 → 6 处；老会话回放升级为合入门禁。

### 3.1 静态契约校验（PR-1 必跑子集）

- [ ] **O1 落地**：grep `phases/p2-spec-definition.md` 中 `current_state\s*=\s*RCA-InProgress` 命中 **0 处**；`current_state\s*=\s*RCA-Designing` 命中 **≥ 1 处**（变更点 P2-S1）
- [ ] **O2 phase 侧核查**：grep `^\s*<step n="5"` 在 `phases/p1-intake.md` 命中 **≤ 1 处**（变更点 P1-S1）
- [ ] **O2 system-prompt 侧落地**：`system-prompt.md` 中原 L200/L203 重复的 `step n="5"` 已修正为 `step n="5"` + `step n="6"`（变更点 SP-S1）
- [ ] **O3 归档完整（v1.1 修订）**：
  - `mobile-qa-workflow/functionality-deep-dive/agents/archive/v3-legacy/` 目录存在且含 5 个 agent 文件；原路径下 5 个文件不再存在（git mv 后）
  - **v1.1 反向断言**：`git diff --name-status` 不包含 `mobile-qa-workflow/agents/challenger.md` 或 `mobile-qa-workflow/agents/arbiter.md`（防误移主流程同名 agent）
  - **主流程 `core/core-rules.xml` L92-96** 5 行 `<agent>` 文本内容已升级为"已退役（v3-legacy 会话恢复专用 / ...）"；**未引入新属性**（grep `deprecated="true"` 与 `recovery_only="true"` 在该 5 行内命中 0 处；grep `\bfile="agents/` 在 L92-96 范围内命中 0 处）（变更点 DD-D1）
  - `functionality-deep-dive/agents/README.md` 退役清单含 5 个 agent（含本次 v1.1 补齐的 challenger / arbiter）（变更点 DD-R1）
- [ ] **O4+ Step 1 + Step 2 落地**：`mobile-qa-workflow/archive/v4.1-history/` 目录存在且含 ~17 份历史文档；`doc/adr/` 目录存在且含 `000-index.md` + 21 个 ADR 文件（含 ADR-010 / ADR-021 草稿）；ADR-021 首段的"命名冲突规避声明"逐字落地（grep 验证 `命名冲突规避声明` 命中 1 处）
- [ ] **O4+ Step 3 短引用化**：grep 全仓库（除 `archive/`）中 `<!-- D\d+:` 与 `# D\d+:` 形式的散布注释命中 **0 处**；预期净减行数 ≥ 30
- [ ] **O5 头部声明（v1.1 增补）**：`system-prompt.md` 头部含 `AUTOGEN-FROM:` 块 **+ ENUM-DECLARATION-BLOCK 块**（含 15 个 v4.1 状态名）（变更点 SP-H1）
- [ ] **O6 注释（v1.1 修订）**：**6 个**主流程 phase 文件头部均含"幂等性约束"统一注释块（grep `幂等性约束（V1.1 O6` 命中 **6 处**）
- [ ] **O22 4 件套落地**：`mobile-qa-workflow/scripts/check-{state-enum,system-prompt-sync,io-contract,subagent-params}.sh` 4 个文件存在且 `chmod +x`；本地手跑 4 个脚本均退出码 0（其中 sync 与 io-contract 以 warning 严重度跑通即可）
- [ ] **CI 集成（v1.1 修订）**：`.github/workflows/qa-workflow-schema-check.yml` 含 4 个新增 step（变更点 CI-W1）；CI 跑全绿（其中 Check 10 与 Check 11 为 warning）

### 3.2 动态用例（PR-1 必跑子集 / **v1.1 修订**）

- [ ] **跨平台回归**（主控 §5 PR-1 行）：Cursor / Trae 全量 + Dify 抽 1 + 单 prompt LLM 抽 1
- [ ] ⚠️ **【v1.1 升级为合入门禁】legacy 恢复链路双侧回放**（V1.1 §3.1 O3 / review F4.3 / 详见 §6 议题 H2）：
  - **主流程侧**：选 1 个标记 `workflow_version = legacy` 的历史会话（来自 `core/workflow.xml` L30 v3 兼容默认值），回放完整 P1-P6 流程，确认主流程编排器仍能从 `core/core-rules.xml` 主流程 agent-group 内派发；与归档前完全一致
  - **deep-dive 侧**：选 1 个标记 `workflow_version = v3-legacy` 的历史会话（来自 `functionality-deep-dive/core/workflow.xml` L27 v3 兼容默认值），触达专项子工作流，确认能从 `functionality-deep-dive/agents/archive/v3-legacy/` 加载 5 个废弃 agent，行为与归档前完全一致
  - **未通过 → 阻止 PR-1 合入**（v1.0 是动态用例项不阻断；v1.1 升级为门禁）
- [ ] **通用门禁**（主控 §5 末段 / V1.1 §4.2）：`eval-framework/artifact_checker.py` 全量通过 + `eval-cases/seed-10` chains A/B `mean_score` 不降 + 路由层抽 5 case 人工读 `workflow-status.yaml` 一致性

> **PR-1 不验收的 §5 项**（由后续 PR 联动）：与 v1.0 一致 — 跨平台 Limited / Minimal 全量 → PR-2/6；phase 出口宏抽查 → PR-3；Spec-Uncertain 双侧 → PR-4；step-pause registry → PR-5；system-prompt 自动构建 diff → PR-6

---

## 4. PR-level 回滚动作（链接主控 §3 H4 / §6 PR-1）

> 主控 §6 PR-1 描述："回滚 = 单 PR 回滚（**主路径无运行时变更，O3 涉及 legacy 兼容触达**）"。具体动作 — v1.1 在 v1.0 基础上补充 legacy 回滚验证：

- **回滚命令**：`git revert <PR-1-merge-commit>`
- **回滚后状态**（与 v1.0 大体一致，v1.1 增补）：
  - `phases/p2-spec-definition.md` 末尾 `current_state` 恢复为 `RCA-InProgress`（C5 漂移复发，但因编排器 default 兜底不影响运行时）
  - `system-prompt.md` 内 P1 phase step n="5" 重复恢复（语义歧义复发，但不影响 LLM 顺序执行）
  - 5 个 deep-dive agent 文件回到原路径；`core/core-rules.xml` L92-96 文本内容回退到"已废弃"短句；README 退役清单回退到 3 项（**v1.1 修订**：回滚后 README 与 core-rules.xml 的"3 vs 5 不一致"现存漂移会复发）
  - **v1.1 增补**：legacy 恢复链路兼容性回退到归档前形态 — **必须重新跑一次主流程 + deep-dive 双侧 v3 / v3-legacy 老会话回放**作为回滚后验证步骤
  - `doc/adr/` 目录消失 → 所有 ADR 引用断链；4 个 CI 脚本文件消失；workflow yml 4 个 step 消失
- **下游影响**：与 v1.0 一致（PR-2/3/5 强依赖；PR-4/6/7 弱依赖）
- **风险等级**：🟡 **低**（v1.0 评估为 🟢 极低；v1.1 修订：因 O3 触达 legacy 恢复链路，升级为低 — 需要回滚后重新执行老会话回放验证）
- **存量会话兼容**：v1.1 修订 — 主流程 `legacy` 会话与 deep-dive `v3-legacy` 会话双侧均不受影响（state-enum 守门是新会话写入校验，不读已持久化旧状态值）

---

## 5. §4 CI 守门自检（PR-1 视角 / **v1.1 修订**）

> 按主控 §4 CI 守门启用时间表 7 项逐项核查 PR-1 是否落地或留待后续 PR。✅ = 本 PR 启用；⏸ = 不在本 PR 范围（标注承接 PR）。

| 主控 §4 脚本 | PR-1 状态 | 落地证据 / 承接 PR |
|---|---|---|
| `check-state-enum.sh` | ✅ error | 变更点 CI-N1 + CI-W1 集成；落地配套修正 P2-S1 |
| `check-system-prompt-sync.sh` | ✅ warning（PR-2 升级 error） | 变更点 CI-N2（**v1.1 重写为声明块对声明块 + 高风险 token 白名单**） + CI-W1 集成；通过 `SP_SYNC_SEVERITY` 环境变量切换严重度 |
| `check-io-contract.sh` | ✅ **warning**（**v1.1 修订**：v1.0 误标 error） | 变更点 CI-N3（**v1.1 重写为 basename 匹配模型 + 变量化路径兜底**）+ CI-W1 集成；通过 `IO_CONTRACT_SEVERITY` 环境变量切换；PR-2 评估升级 error |
| `check-subagent-params.sh` | ✅ error | 变更点 CI-N4（**v1.1 补完整 arbiter + 双向反向断言**）+ CI-W1 集成 |
| `check-build-system-prompt-precondition.sh` | ⏸ | PR-2 启用为 error |
| `check-phase-abort-structure.sh` | ⏸ | PR-3 启用 warning，PR-6 升级 error |
| `check-step-pause-registry.sh` | ⏸ | PR-5 启用为 error |

**自检结论**：PR-1 落地主控 §4 中 PR-1 启用列的 **4/7 项**；其中 `check-io-contract.sh` 严重度由 v1.0 的 error 调整为 v1.1 的 warning（建议主控 §4 表同步联动登记，详见 §6 议题 #5）。

---

## 6. Reviewer 议题汇总（v1.1 扩展为 9 项）

| # | 议题 | v1.1 状态 | 影响范围 |
|---|---|---|---|
| 1 | V1.1 §3.1 O2 描述 P1 phase 内 L200-206 重复 step n="5"，但 main 实际仅 1 处（L74） | ✅ **v1.1 已确认 — main 已修复，P1-S1 仅做核查断言** | O2 phase 侧落地完整性 |
| 2 | V1.1 §3.1 O4+ Step 3 总目标 ~165 行净减，PR-1 仅吃下"短引用化"约 30~50 行；剩余 ~115 行长注释删除 | 📝 **PR description 内显式登记 PR-3 + PR-6 的剩余指标** | O4+ 总目标完整覆盖 |
| 3 | ADR-010 / ADR-021 以 draft 状态落地的 PR-N 落地依赖标记 | ✅ **v1.0 已采纳** — §2.4.2 表强制 | H4 前置依赖完整性 |
| 4 | ADR-021 首段命名冲突规避声明的强制度 | ✅ **v1.0 已升级为合入门禁** | 跨 PR 文档清晰度 |
| 5 | **v1.1 新增**：v1.1 把 `check-io-contract.sh` 严重度由主控 §4 表的 error 调整为 warning，是否同步登记主控 README §4 表？ | 📝 **强烈建议**：在主控 README §4 表的 `check-io-contract.sh` 行加备注"PR-1 实施期降为 warning，PR-2 评估升级 error" — 与 v2.2 PR-4 子文档 §7 v2.3 主文档变更摘要的联动登记机制对齐 | 主控/子文档口径一致性 |
| 6 | **v1.1 新增**：工作量必做 / follow-up 拆分（review F5.2） | ✅ **v1.1 采纳**：必做（≈ 0.7d） = O1/O2/O3 含双侧回放/O4+ Step 1+2/O5 头部声明/O6/CI-N1/CI-N4；follow-up 候选（≈ 0.2d，如 0.9d 兜不住可迁到 PR-1.1 hotfix） = O4+ Step 3 短引用化 / CI-N2 v1.1 算法调试 / CI-N3 v1.1 算法调试 | 工作量风险控制 |
| **H1** | **v1.1 隐藏问题**：deep-dive 子目录下 challenger.md / arbiter.md 与主流程 `agents/` 同名，git mv 时易误移 | ✅ **v1.1 已采纳**：§2.3.1 表"备注"列加"⚠️ 仅限 deep-dive 子目录"+ §3.1 DoD 加 `git diff --name-status` 反向断言 | 防 O3 误操作 |
| **H2** | **v1.1 隐藏问题**：主流程 `core/workflow.xml` L30 v3 兼容默认值是 `workflow_version = legacy`；deep-dive 子流程 `functionality-deep-dive/core/workflow.xml` L27 是 `workflow_version = v3-legacy` — 两个不同字符串值 | ✅ **v1.1 已采纳**：§3.2 老会话回放门禁明确"双侧回放"；DD-R1 README 补齐"双侧累加"统计口径说明 | legacy 恢复链路兼容性完整性 |
| **H3** | **v1.1 隐藏问题**：`functionality-deep-dive/core/workflow.xml` 是否含 5 个废弃 agent 名字符串的显式 `<load>` 引用？ | 📝 **本 PR 启动时必须先 grep**：`grep -nE 'context-reconstructor\|state-analyst\|temporal-analyst' mobile-qa-workflow/functionality-deep-dive/core/workflow.xml`；命中 → 路径修正作为 DD-A1~A3 强制配套；未命中 → PR description 显式注明"grep 全空" | DD-A1~A5 操作完整性 |
| **H4** | **v1.1 隐藏问题**：v1.0 §2.2.2 描述"如有 step 6/7 则顺延"是基于错误假设；P1 phase 内仅有 step 5/5 两个，无后续 step | ✅ **v1.1 已简化** — §2.2.2 删除冗余顺延描述 | SP-S1 文本精确性 |

---

## Changelog

| 版本 | 日期 | 变更 |
|---|---|---|
| **v1.1** | 2026-04-21 | **基于 [`pr-1-foundation-cleanup-and-ci-bootstrap-REVIEW-2026-04-21.md`](./pr-1-foundation-cleanup-and-ci-bootstrap-REVIEW-2026-04-21.md) 4 项 Patch 块整体修订**（2 阻断 + 3 高优 + 4 隐藏问题）：① **Patch A 结构对齐**：§1 涉及文件清单删除不存在的 `functionality-deep-dive/core/core-rules.xml`，O3 目标改回主流程 `mobile-qa-workflow/core/core-rules.xml`；§2.3.2 DD-D1 完全重写 — 保留现有 `<agent name=... scenario=...>文本</agent>` 结构 + 仅升级文本内容，**不引入** `file=` / `deprecated=` 属性；§2.3.3 DD-R1 同时补齐 README 当前缺失的 challenger / arbiter；§2.6 phase 清单从 v1.0 错写的 7 个修正为按 ls 实际的 6 个（PHASE-C1~C6，且 P5 实名 `p5-fix-impl.md`）。② **Patch B CI 重设计**：§2.5.3 CI-N2 从"赋值集对完整 enum 集"改为"声明块对声明块 + 高风险 token 白名单"双校验，PR-1 阶段 warning；§2.5.1 SP-H1 同步增补 `<!-- ENUM-DECLARATION-BLOCK -->` 注释块作为比对目标；§2.5.4 CI-N3 从"file 属性直接相等"改为"basename 匹配模型 + 变量化路径兜底"，严重度由 v1.0 的 error 调整为 PR-1 阶段 warning（联动登记建议见 §6 议题 #5）；§2.5.5 CI-N4 补完整 arbiter 实现 + 双向反向断言（防角色矩阵反转复发）；§2.5.6 CI-W1 调整 Check 11 严重度为 warning。③ **Patch C 定性修订**：§1 顶部"零运行时变更"改为"主路径零运行时 + O3 legacy 恢复链路兼容性触达"；§1 元信息表"层级"列由 🟢 升级为 🟡；§3.2 老会话回放从动态用例升级为合入门禁，且回放范围扩展到主流程（`workflow_version=legacy`）+ deep-dive（`workflow_version=v3-legacy`）双侧；§4 风险等级由 🟢 极低升级为 🟡 低。④ **Patch D 议题与隐藏风险**：§6 议题汇总从 5 项扩展为 9 项 — 新增 H1 同名 agent 误移防御 / H2 主流程 vs deep-dive workflow_version 默认值差异 / H3 deep-dive workflow.xml load 引用核查 / H4 SP-S1 顺延描述简化；新增议题 #5 主控 §4 联动登记建议 / #6 工作量必做与 follow-up 拆分（review F5.2）。⑤ §0 新增 v1.0 → v1.1 修订摘要表（按 4 个 Patch 块组织）。⑥ §2.4 全节无实质改动（review 未对该节提 finding）。⑦ Changelog 含完整 v1.0 → v1.1 演化点。 |
| v1.0 | 2026-04-21 | 初版（已 **superseded by v1.1**）。基于主控 v4.2 README §6 PR-1 + V1.1 §3.1 O1/O2/O3/O4+/O5/O6 + §3.2.22 O22(4 件套) 完整展开；6 类共 ~30 个变更点；体例参考 v2.2/pr4-phase-abort-fanout-isolation.md 但精简到 ~700 行；ADR-010 / ADR-021 草稿落地满足主控 §3 H4 前置依赖。**review 阻断原因**：见 [`pr-1-foundation-cleanup-and-ci-bootstrap-REVIEW-2026-04-21.md`](./pr-1-foundation-cleanup-and-ci-bootstrap-REVIEW-2026-04-21.md) §3-§4。 |
