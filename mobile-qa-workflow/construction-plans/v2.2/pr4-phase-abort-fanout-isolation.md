# PR-4 · P3/P4/P6 ABORT + 字段隔离 + base_score / confidence_input 注入（v2.2 详细施工单）

> **主文档**：[`../../QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md`](../../QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md) §4（索引行）
> **子文档骨架**：[README.md §2](./README.md)
> **协议依赖**：附录 C **D1 / D2 / D7 / D8 / D9 / D14 / D15 / D17**（全部定义见主文档附录 C）
> **强前置 PR**：PR-1（协议层）已合入；PR-2（编排器层）建议先合入但**不强阻塞**（D1 方案 A 红利：`current_phase_result` 是运行时变量，PR-4 可在 PR-2 未合入时也安全合入；详见 §1 元信息）
> **状态**：📐 已展开（v2.2，2026-04-20）
> **唯一职责**：把 PR-1 在 `core/core-rules.xml` 中固化的 **`<workflow-result-protocol>`**（D1）落到 phase 文件 P3/P6 的全部早退点位（B1\*，共 6 处 = P3 ×5 + P6 ×1）；把 PR-1 在 `core/workflow-status-template.yaml` 中新增的 **`fix_fanout_mode` / `rca_fanout_mode_snapshot` / `phase_history`** 字段（C10 / D7）在 P3 写入端、P4 写入端落地；把 **C2 共享基座所需的 `confidence_input`（注入给所有 challenger）/ `base_score`（注入给所有 arbiter）** —— **按"角色驱动"** 而非"场景驱动" —— 注入到 P3 / P4 调用 challenger / arbiter 的 subagent_prompt 中；把 **C9 P6 失败分支必输出 verification-report** 的中间态产出补齐。
> **本 PR 不动 phase 内 `<step-pause>`**（D14 协议约束 / v4.2 遗留 #6）；P4 step 6 末尾的现存 `<step-pause>` 由 PR-5 盘点登记 `legacy-phase-step-pause-allowlist.txt` 后由 v4.2 遗留 #6 整改。

---

## 1. PR 元信息

| 项 | 值 |
|---|---|
| 分支命名 | `feat/qa-workflow-v4.1-pr4-phase-abort-fanout-isolation` |
| Base | PR-1 合入后的 `main`（**强**前置）；PR-2 合入后的 `main`（**弱**前置 — 详见下"PR-2 解耦说明"） |
| 层级 | 🟠 phase 层（D9 合入顺序：PR-1 → PR-2 → **PR-4** → PR-3 → PR-5 → ...） |
| 目标合入顺序 | **PR-1 → PR-2 → PR-4 → PR-3 → PR-5 → PR-6 → PR-7 → PR-8**（D9） |
| Reviewer | 1 名 phase owner（必看 P3/P6 的 ABORT 标记完整性 = **6 处**、P4 内 `fanout_mode → fix_fanout_mode` 替换边界、P6-A6 内 `RCA-InProgress → RCA-Designing` 收口正确性）+ 1 名协议 owner（必看 D1/D7/C10 的 phase 落地；必看 step 10 RCA-LowConfidence 增补点位 = §2.1.5 决策；必看 C2 角色驱动注入矩阵 = §2 注入矩阵表） |
| 关联 issue | v4.1 主修复条目：**B1\***（P3/P6 显式 ABORT **6 处** = P3 ×5 + P6 ×1，含 v2.2 实施期增补 1 处 RCA-LowConfidence stop，详见 §2.1.5）/ **C2**（共享基座调用方注入，**按角色驱动**：所有 challenger（RCA / FIX 场景一致）注入 `confidence_input`；所有 arbiter（RCA / FIX 场景一致）注入 `base_score`；与 `agents/shared-challenger-base.md` / `agents/shared-arbiter-base.md` 输入契约逐字段对齐）/ **C9**（P6 失败分支必输出 verification-report，phase 侧补 template-output；模板侧由 PR-6 联动）/ **C10**（仅写入端：P3 写 `rca_fanout_mode_snapshot` + `phase_history`；P4 把 `fanout_mode = X` 全部改写为 `fix_fanout_mode = X`；保留 `fanout_mode` 为 RCA 字段不重命名 / D7） |
| 工作量 | 1.0d（v2.0 锁定，v2.1/v2.2 无调整；其中 P3 ABORT + phase_history + base_score 0.4d / P4 字段隔离 + confidence_input 0.3d / P6 ABORT + 中间态 template-output 0.3d） |
| 涉及文件 | **3 个**：`phases/p3-root-cause.md`（修改）/ `phases/p4-fix-design.md`（修改）/ `phases/p6-verification.md`（修改） |
| 不在本 PR 范围 | ① `core/workflow.xml` / `core/core-rules.xml` / `core/workflow-status-template.yaml` 任何修改（属 PR-1 / PR-2 范围）② `phases/p2-spec-definition.md` Non-Bug 早退（属 PR-3 范围）③ `templates/verification-report.md` 中间态报告段落新增（属 PR-6 范围；本 PR 仅在 P6 内**调用** template-output，模板自身段落由 PR-6 提供）④ `agents/shared-arbiter-base.md` / `agents/shared-challenger-base.md` 的 `[Schema-Violation]` 缺参输出（属 PR-6 范围；本 PR 仅在调用方**注入**字段，wrapper 端校验由 PR-6 实现）⑤ Deep-Dive `functionality-deep-dive/phases/**` 任何 ABORT / 字段隔离改动（属 v4.2 遗留 #6 / B1\* Deep-Dive 子工作流，主文档 §1.2.1 已声明本次不覆盖）⑥ phase 内现存或新增 `<step-pause>`（D14 协议约束；P4 step 6 现存 step-pause 登记到 PR-5 allowlist） |

### 1.1 PR-2 解耦说明（D1 方案 A 红利的具体落地证据）

主文档 §2.1 拓扑约束声明 "PR-2 不再是 PR-4 的强前置（v1.0 → v2.0 保持），方案 A 下 `current_phase_result` 为运行时变量，PR-4 可在 PR-2 未合入时也安全合入"。本 PR 落地后该解耦的物理机制如下：

- PR-4 在 phase 文件内写入 `<action>设置 current_phase_result = ABORT</action>` —— 这是 D1 协议要求的**纯运行时变量赋值**，编排器 `core/workflow.xml` step 4 既有 `<check if="{current_phase_result} == ABORT">` 分支（v3 已存在，PR-2 不动）即可消费。
- PR-4 不依赖 PR-2 的"step-pause 白名单受限双写"代码块 —— PR-4 内 P3/P6 的早退路径**全部不触发 step-pause**（早退后由编排器 step 4 路由到对应 case；其中 `current_state = RCA-LowConfidence` 由 PR-2 的变更点 W6 触发 step-pause，但 PR-4 自身只写 `current_state`，不直接发起 step-pause）。
- 因此 **PR-4 单独合入（PR-2 滞后）的最坏后果**：
  1. 编排器 step 4 case `RCA-LowConfidence` 的 `<step-pause>` 仍是 v3 缺 `result_field` / `allowed_values` 的旧形态 → 用户回复无法被结构化双写到 `user_inputs.rca_lowconf_action`，但 ABORT 标记本身仍然生效，B1\* 的"`stepsCompleted` 错锚"主缺陷已修复；
  2. C2 注入的 `base_score` / `confidence_input` 字段在 wrapper（agents/shared-\*-base.md）尚未被 PR-6 加 `[Schema-Violation]` 校验时，缺参不会被显式拒绝 —— 但调用方注入的字段被 wrapper 静默接受不会引发回归（**纯加项**）。
- **建议 Review 路径**：PR-4 与 PR-2 在同一 milestone 内合入，**优先按 D9 顺序**（PR-2 先，PR-4 后）；如出现 PR-2 评审长尾，PR-4 可先合入并以 PR description 显式标注"PR-2 滞后期间 RCA-LowConfidence 用户回复仍走 v3 自然语言路径，待 PR-2 合入后协议自洽"。

---

## 2. 文件级 diff 列表

> 本 PR 涉及 3 个文件、共 11 个变更点（**ABORT 计数 = 6 = P3 ×5 + P6 ×1**）：
> - `phases/p3-root-cause.md`：7 个变更点（**P3-A1~A4**：4 处主文档明确 ABORT；**P3-A5**：v2.2 实施期增补的 step 10 RCA-LowConfidence stop ABORT；**P3-H1**：step 10 完成时 `phase_history` append + `rca_fanout_mode_snapshot` 写入；**P3-C1/C2**：2 处 challenger 注入 `confidence_input`；**P3-C3**：1 处 arbiter 注入 `base_score`）
> - `phases/p4-fix-design.md`：5 个变更点（**P4-F1**：step 2 `fanout_mode = {fix_strategy_mode}` → `fix_fanout_mode`；**P4-F2**：step 3 challenged-proposer 升级 `fanout_mode = contested-arbitrated` → `fix_fanout_mode`；**P4-C4/C5**：2 处 challenger 注入 `confidence_input`；**P4-C6**：1 处 arbiter 注入 `base_score`）
> - `phases/p6-verification.md`：2 个变更点（**P6-A6**：step 6 失败回流早退点位 ABORT 标记 + 中间态 template-output 调用；**P6-T1**：与 P6-A6 合并描述，编号保留作为 §3 DoD grep 锚点；保留 case `root_cause_not_closed` 强制 `fanout_mode = complex-arbitrated` 的 RCA 升级语义不动）
>
> **变更点编号约定**：A\* = ABORT 标记 / H\* = 历史与快照写入 / C\* = subagent_prompt 注入（**角色驱动**：challenger → `confidence_input`；arbiter → `base_score`） / F\* = fanout 字段隔离 / T\* = template-output 中间态。
>
> **C2 注入矩阵**（与 wrapper 输入契约对齐）：
>
> | Phase × 角色 | 变更点 | 注入字段 | 取值来源 |
> |---|---|---|---|
> | P3 step 5 medium-challenge × challenger | P3-C1 | `confidence_input` | 上游 Investigator 输出的 `final_score`（OVHSC SCORE 步产物） |
> | P3 step 5 complex-arbitrated × challenger | P3-C2 | `confidence_input` | 上游 2 个 Investigator 输出的 `final_score` 列表 |
> | P3 step 5 complex-arbitrated × arbiter | P3-C3 | `base_score` | 候选 RCA 结论的基础评分（Investigator final_score 与 Challenger confidence_impact 的复合基线） |
> | P4 step 3 challenged-proposer × challenger | P4-C4 | `confidence_input` | 当前 Fix-Proposer 自评置信度 + 上游 P3 arbiter 的 final_confidence |
> | P4 step 3 contested-arbitrated × challenger | P4-C5 | `confidence_input` | Proposer-A / Proposer-B 自评置信度数组 + 上游 P3 arbiter 的 final_confidence |
> | P4 step 3 contested-arbitrated × arbiter | P4-C6 | `base_score` | 候选 Fix 方案的基础评分（Fix-Proposer 自评置信度与 Challenger confidence_impact 的复合基线） |

### 2.1 文件 A · `phases/p3-root-cause.md`（修改）

> **修复条目锚点**：B1\*（P3 早退 5 处 ABORT 标记，含 v2.2 实施期增补 1 处） / C2（调用方注入：challenger → `confidence_input` ×2；arbiter → `base_score` ×1） / C10 + D7（仅写入端：`rca_fanout_mode_snapshot` + `phase_history`，**不动** `fanout_mode` 字段名）

#### 2.1.1 变更点 P3-A1 · step 2 证据不足早退点 ABORT 标记（B1\*）

**原文（行号锚点 L24-31）**：

```24:31:mobile-qa-workflow/phases/p3-root-cause.md
    <step n="2" goal="最小证据阈值检查">
        <action>检查 Context Bundle 证据质量：至少 1 条 A 级证据，或 2 条 B 级证据；分类 Spec 扩展模块 >= 50% 关键字段已填充。</action>
        <check if="纯 C 级证据，阈值未通过">
            <action>列出需要补充的具体证据项</action>
            <action>更新 {workflow_status}：current_state = Spec-Defining</action>
            <action>阶段结束，返回编排器</action>
        </check>
    </step>
```

**新文**（在"阶段结束，返回编排器"之前**单行插入** ABORT 设值动作）：

```xml
    <step n="2" goal="最小证据阈值检查">
        <action>检查 Context Bundle 证据质量：至少 1 条 A 级证据，或 2 条 B 级证据；分类 Spec 扩展模块 >= 50% 关键字段已填充。</action>
        <check if="纯 C 级证据，阈值未通过">
            <action>列出需要补充的具体证据项</action>
            <action>更新 {workflow_status}：current_state = Spec-Defining</action>
            <action>设置 current_phase_result = ABORT</action>
            <action>阶段结束，返回编排器</action>
        </check>
    </step>
```

**修订理由**：
- B1\*（v1.2.1 §三 B1\* / 主文档 §1.1.1）：当前 phase 早退（写完 `current_state = Spec-Defining` 即返回编排器）但**未显式标记** `current_phase_result`，导致编排器 step 4 默认按"phase 正常完成"把 `qa-root-cause` 追加到 `stepsCompleted`，造成 stepsCompleted 错锚（B1\* 复发）。
- D1 协议层规则（PR-1 已固化在 `core/core-rules.xml` `<workflow-result-protocol>` 章节）："phase 早退（含 ABORT、RCA-LowConfidence、Curation-Failed、Non-Bug 等）必须在返回编排器之前显式写入 ABORT"。本变更点是该协议在 P3 第 1 处早退点的落地。

**兼容性影响**：
- 纯加项；PR-1 未合入时，`current_phase_result` 仍是运行时变量赋值（无 schema 字段），编排器 step 4 既有 `<check if="{current_phase_result} == ABORT">` 分支（v3 已存在）能识别；不引入回归。
- 与 PR-2 解耦：本变更点行为不依赖 PR-2 的双写代码（D1 方案 A 红利）。

---

#### 2.1.2 变更点 P3-A2 · step 5 simple-single 升级到 medium-challenge 早退点 ABORT 标记（B1\*）

**原文（行号锚点 L56-65）**：

```56:65:mobile-qa-workflow/phases/p3-root-cause.md
            <check if="反事实校验失败 或 最终置信度 < 0.70 或 出现新证据冲突">
                <action>更新 {workflow_status}：
                    - fanout_mode = medium-challenge
                    - reroute_reason = simple_path_not_closed
                    - reroute_from_phase = qa-root-cause
                    - reroute_target_phase = qa-root-cause
                    - rca_retry_count += 1
                </action>
                <action>阶段结束，返回编排器</action>
            </check>
```

**新文**：

```xml
            <check if="反事实校验失败 或 最终置信度 < 0.70 或 出现新证据冲突">
                <action>更新 {workflow_status}：
                    - fanout_mode = medium-challenge
                    - reroute_reason = simple_path_not_closed
                    - reroute_from_phase = qa-root-cause
                    - reroute_target_phase = qa-root-cause
                    - rca_retry_count += 1
                </action>
                <action>设置 current_phase_result = ABORT</action>
                <action>阶段结束，返回编排器</action>
            </check>
```

**修订理由**：与 P3-A1 同理。该早退点位的 `current_state` 在本 case 内未被显式重写，但 `reroute_target_phase = qa-root-cause` 暗含**重入 P3** 语义；按 D1 协议，重入前必须 ABORT 否则编排器会把上一轮 `qa-root-cause` 误算作完成态，导致 `stepsCompleted` 中混入两次 `qa-root-cause`。

**兼容性影响**：同 P3-A1。**注意**：本 case 写 `fanout_mode = medium-challenge` 是**升级 RCA 策略**的合法 RCA 字段写入（D7 决定下 `fanout_mode` 保留为 RCA 字段），与 C10 字段污染**无关**，本 PR 不动该写入语义。

---

#### 2.1.3 变更点 P3-A3 · step 5 medium-challenge 升级到 complex-arbitrated 早退点 ABORT 标记（B1\*）

**原文（行号锚点 L93-102）**：

```93:102:mobile-qa-workflow/phases/p3-root-cause.md
            <check if="challenger 出现 Critical 或 最终置信度 < 0.65">
                <action>更新 {workflow_status}：
                    - fanout_mode = complex-arbitrated
                    - reroute_reason = medium_path_escalated
                    - reroute_from_phase = qa-root-cause
                    - reroute_target_phase = qa-root-cause
                    - rca_retry_count += 1
                </action>
                <action>阶段结束，返回编排器</action>
            </check>
```

**新文**：

```xml
            <check if="challenger 出现 Critical 或 最终置信度 < 0.65">
                <action>更新 {workflow_status}：
                    - fanout_mode = complex-arbitrated
                    - reroute_reason = medium_path_escalated
                    - reroute_from_phase = qa-root-cause
                    - reroute_target_phase = qa-root-cause
                    - rca_retry_count += 1
                </action>
                <action>设置 current_phase_result = ABORT</action>
                <action>阶段结束，返回编排器</action>
            </check>
```

**修订理由**：与 P3-A2 同理；同样是合法的 `fanout_mode` RCA 升级写入，本 PR 仅补 ABORT 标记。

**兼容性影响**：同 P3-A1。

---

#### 2.1.4 变更点 P3-A4 · step 5 complex-arbitrated 对抗轮次超过 3 轮转 Human-Review 早退点 ABORT 标记（B1\*）

**原文（行号锚点 L141-151）**：

```141:151:mobile-qa-workflow/phases/p3-root-cause.md
            <check if="对抗轮次超过 3 轮仍未收敛">
                <action>更新 {workflow_status}：
                    - fanout_mode = complex-arbitrated
                    - reroute_reason = multi_view_non_convergent
                    - reroute_from_phase = qa-root-cause
                    - reroute_target_phase = qa-root-cause
                    - rca_retry_count += 1
                    - current_state = Human-Review
                </action>
                <action>阶段结束，返回编排器</action>
            </check>
```

**新文**：

```xml
            <check if="对抗轮次超过 3 轮仍未收敛">
                <action>更新 {workflow_status}：
                    - fanout_mode = complex-arbitrated
                    - reroute_reason = multi_view_non_convergent
                    - reroute_from_phase = qa-root-cause
                    - reroute_target_phase = qa-root-cause
                    - rca_retry_count += 1
                    - current_state = Human-Review
                </action>
                <action>设置 current_phase_result = ABORT</action>
                <action>阶段结束，返回编排器</action>
            </check>
```

**修订理由**：本 case 显式写 `current_state = Human-Review`（**stop_state**），按 D1 协议必须 ABORT；编排器 step 4 路由到 case Human-Review，由 PR-2 变更点 W7 的 step-pause 触发人工介入。

**兼容性影响**：同 P3-A1；本 case 写 `fanout_mode = complex-arbitrated` 是 P3 内合法 RCA 字段写入（与 P3-A3 同理），不属 C10 污染。

---

#### 2.1.5 变更点 P3-A5 · step 10 case "最终置信度 < 0.5" 早退点 ABORT 标记（B1\* 实施期增补 / **Reviewer 议题**）

> **本变更点是 v2.2 实施期发现的协议层 D1 一致性补全点位**，主文档 §3 PR-4 描述 v1.0 "P3 ×4" 仅显式列出 step 2 / step 5 内 4 处 "阶段结束，返回编排器"。本变更点是 step 10 case "最终置信度 < 0.5" 的 RCA-LowConfidence stop 路径，**该路径写完 `current_state = RCA-LowConfidence` 后 phase 自然结束**（step 10 是 P3 末步），编排器 step 4 默认按"phase 正常完成"追加 `qa-root-cause` 到 `stepsCompleted` —— **这是 B1\* 的核心复发场景**。**v2.0 子文档已 collapse 为"PR-4 直接落地"**（不再作为可选议题）；ABORT 总计数已统一为 **P3 ×5 + P6 ×1 = 6 处**；主文档 §3 PR-4 描述 / §1.1.1 表 / §7.4 回滚条目同步在 v2.3 微调登记。

**原文（行号锚点 L198-207）**：

```198:207:mobile-qa-workflow/phases/p3-root-cause.md
    <step n="10" goal="输出 Root Cause Report">
        <template-output file="{output_file}" template="mobile-qa-workflow/templates/rca-report.md"/>
        <action>更新 {config_source}：output_rca_report = {output_file}</action>
        <check if="最终置信度 >= 0.5">
            <action>更新 {workflow_status}：current_state = Fix-Designing, reroute_reason = null, reroute_target_phase = null</action>
        </check>
        <check if="最终置信度 < 0.5">
            <action>更新 {workflow_status}：current_state = RCA-LowConfidence, fanout_mode = complex-arbitrated, reroute_reason = low_final_confidence, reroute_from_phase = qa-root-cause, reroute_target_phase = qa-root-cause, rca_retry_count += 1</action>
        </check>
    </step>
```

**新文**（在 `current_state = RCA-LowConfidence` 写入后**追加** ABORT 设值动作；同时为 `current_state = Fix-Designing` 成功路径**显式不写** ABORT，让编排器按正常完成追加 `stepsCompleted`）：

```xml
    <step n="10" goal="输出 Root Cause Report">
        <template-output file="{output_file}" template="mobile-qa-workflow/templates/rca-report.md"/>
        <action>更新 {config_source}：output_rca_report = {output_file}</action>
        <check if="最终置信度 >= 0.5">
            <action>更新 {workflow_status}：current_state = Fix-Designing, reroute_reason = null, reroute_target_phase = null</action>
            <!-- 成功完成路径：不写 current_phase_result，按 D1 默认行为 OK，
                 编排器 step 4 把 qa-root-cause 追加到 stepsCompleted -->
        </check>
        <check if="最终置信度 < 0.5">
            <action>更新 {workflow_status}：current_state = RCA-LowConfidence, fanout_mode = complex-arbitrated, reroute_reason = low_final_confidence, reroute_from_phase = qa-root-cause, reroute_target_phase = qa-root-cause, rca_retry_count += 1</action>
            <action>设置 current_phase_result = ABORT</action>
            <!-- B1* 关键修复：RCA-LowConfidence 是 stop_state，phase 不应被算作完成；
                 编排器 step 4 case RCA-LowConfidence 由 PR-2 变更点 W6 触发 step-pause -->
        </check>
    </step>
```

**修订理由**：
- B1\* 协议一致性：D1 协议要求"phase 早退（含 ABORT、**RCA-LowConfidence**、Curation-Failed、Non-Bug 等）必须在返回编排器之前显式写入 ABORT"。`RCA-LowConfidence` 是被 D1 协议**显式列举**的 stop_state；step 10 case "最终置信度 < 0.5" 是该 stop_state 的**唯一**写入点（B1\* 复发的关键场景），如不补 ABORT 则 P3 任何"低置信完成"流程都会把 `qa-root-cause` 误追加到 `stepsCompleted`，下一轮编排器 step 2 会把 P3 视作已完成、跳过重新执行 → B1\* 失锚问题完全没有修复。
- 主文档 §3 PR-4 描述 v1.0 "P3 ×4 + P6 ×1 = 5 处" 是基于 grep "阶段结束，返回编排器" 的字面统计；step 10 case "最终置信度 < 0.5" 没有显式"阶段结束"动作（因为 step 10 是 phase 末步，phase 自然结束），所以未出现在 4 处之内。本变更点把该路径补齐为 "**P3 ×5 + P6 ×1 = 6 处**"，与 v1.2.1 §三 B1\* 的"隐式 stop_state"路径一致；主文档 §3 PR-4 描述 / §1.1.1 B1\* 行说明 / §7.4 回滚条目均已在 v2.3 微调统一为 6 处口径（详见 §7 v2.3 主文档变更摘要）。
- 与 §5.2.1 用例 A（B1\* P3 RCA 低置信回流）联动：本变更点是用例 A 期望"phase 内显式 `current_phase_result = ABORT` → 编排器 step 4 不追加 `qa-root-cause` 到 `stepsCompleted`"的**唯一**落地点，缺失则用例 A 必失败。

**兼容性影响**：
- `current_state = Fix-Designing` 成功路径**不写** ABORT 是有意为之，与 D1 协议第二条 rule "若未显式赋值则视作正常完成（current_phase_result = OK）"一致；这是 P3 唯一的"正常完成"出口，必须保持默认行为。
- 与 PR-2 解耦：本变更点行为不依赖 PR-2；PR-2 滞后时 case RCA-LowConfidence 走 v3 step-pause，但 ABORT 标记本身已生效，B1\* 主缺陷修复完成。

---

#### 2.1.6 变更点 P3-H1 · step 10 完成时 `phase_history` append + `rca_fanout_mode_snapshot` 写入（C10 兼容性方案 A + B 双保险）

> **主文档 §3 PR-4 原文写"step 7 新增"，本施工单修正为"step 10 完成时"**。修正理由见下"修订理由"末段，作为 Reviewer 议题暴露。

**原文（行号锚点 L198-207；与 P3-A5 共享原文段）**：

```198:207:mobile-qa-workflow/phases/p3-root-cause.md
    <step n="10" goal="输出 Root Cause Report">
        <template-output file="{output_file}" template="mobile-qa-workflow/templates/rca-report.md"/>
        <action>更新 {config_source}：output_rca_report = {output_file}</action>
        <check if="最终置信度 >= 0.5">
            <action>更新 {workflow_status}：current_state = Fix-Designing, reroute_reason = null, reroute_target_phase = null</action>
        </check>
        <check if="最终置信度 < 0.5">
            <action>更新 {workflow_status}：current_state = RCA-LowConfidence, fanout_mode = complex-arbitrated, reroute_reason = low_final_confidence, reroute_from_phase = qa-root-cause, reroute_target_phase = qa-root-cause, rca_retry_count += 1</action>
        </check>
    </step>
```

**新文**（与 P3-A5 同段编辑；为可读性此处展示完整 step 10 — 实际 PR diff 中 P3-A5 的 ABORT 行与本变更点的 H1 写入行**合并到一次 patch**，按"先 H1 再 A5"语义顺序排列；H1 写入既覆盖成功路径也覆盖 stop 路径，确保 P3 任何完成形态都有 history 与 snapshot）：

```xml
    <step n="10" goal="输出 Root Cause Report">
        <template-output file="{output_file}" template="mobile-qa-workflow/templates/rca-report.md"/>
        <action>更新 {config_source}：output_rca_report = {output_file}</action>

        <!-- C10 + D7：phase_history append + rca_fanout_mode_snapshot 写入；
             无论本次 P3 是成功完成（最终置信度 >= 0.5）还是 RCA-LowConfidence stop，
             都需要记录 P3 完成时的 fanout_mode 取值，供 P3 重入时（C10 兼容性方案 A）
             或迁移脚本反查（C10 兼容性方案 B）使用。
             phase_history 元素结构与 PR-1 注释一致：
               { phase: "qa-root-cause", timestamp: <now>, fanout_mode: <fanout_mode>, note: <stop 标签|null> }
        -->
        <action>更新 {workflow_status}：rca_fanout_mode_snapshot = {fanout_mode}</action>
        <action>更新 {workflow_status}.phase_history：append { phase: "qa-root-cause", timestamp: &lt;now ISO8601&gt;, fanout_mode: {fanout_mode}, note: null }</action>

        <check if="最终置信度 >= 0.5">
            <action>更新 {workflow_status}：current_state = Fix-Designing, reroute_reason = null, reroute_target_phase = null</action>
        </check>
        <check if="最终置信度 < 0.5">
            <action>更新 {workflow_status}：current_state = RCA-LowConfidence, fanout_mode = complex-arbitrated, reroute_reason = low_final_confidence, reroute_from_phase = qa-root-cause, reroute_target_phase = qa-root-cause, rca_retry_count += 1</action>
            <!-- RCA-LowConfidence stop 路径下 fanout_mode 已被强制重写为 complex-arbitrated；
                 phase_history 上方 append 时记录的 fanout_mode 是"重写之前"的取值，
                 这正是 C10 兼容性方案 A 期望的"P3 完成时 fanout_mode 的快照"语义；
                 下次 P3 重入时仍可通过 phase_history 末项还原 RCA 上下文。 -->
            <action>设置 current_phase_result = ABORT</action>
        </check>
    </step>
```

**修订理由**：
- C10（v1.2.1 §三 C10 / 主文档 §1.1.1）：P3→P4→P6→P3 链路下，P4 复用 `fanout_mode` 写入会污染 P3 重入时的字段值；C10 修复采用**双轨方案** —— 方案 A（`phase_history` 顺序记录）+ 方案 B（`rca_fanout_mode_snapshot` 单点快照）。本变更点是 P3 写入端的**唯一**落地点；P4 在变更点 P4-F1/F2 完成"不再污染 fanout_mode"的对偶；迁移脚本（PR-1 §2.5 `migrate-workflow-status-v3-to-v4.py`）的 `--restore-fanout-mode` 子命令依赖 `phase_history` 反查（主文档 §6.3）。
- D7（v2.0 决定）：`fanout_mode` 字段名**保留**为 RCA 字段，**不重命名**为 `rca_fanout_mode`；`rca_fanout_mode_snapshot` 仅作为快照辅助字段。本变更点严格遵守 D7。
- `phase_history` 元素结构与 PR-1 `core/workflow-status-template.yaml` 头部注释**逐字段对齐**：`{ phase, timestamp, fanout_mode, note }`；`note` 字段在本 PR 默认填 `null`，预留给 v4.2 整改时区分 stop 标签（如 `"RCA-LowConfidence stop"` / `"normal complete"`）。本 PR 不在 stop 路径写 `note: "RCA-LowConfidence"` 是出于**保守性**：避免在 phase_history 中混入"是否 stop"语义，让该字段保持纯执行历史；reviewer 如需该语义可在 v4.2 增加。
- **主文档 §3 PR-4 写"step 7"的修正说明**：P3 step 7 实际是"回注专项结论并合并 RCA"（deep-dive 合并步骤），仅当 `deep-dive-summary.md` 存在时才执行；P3 真正的"完成位置"是 step 10（输出 RCA Report 后写 `current_state = Fix-Designing` 或 `RCA-LowConfidence`）。本 PR 把写入位置修正到 step 10，**保证无论是否走 deep-dive 子工作流，phase_history 与 snapshot 都能稳定写入**。如 Reviewer 坚持 "step 7" 字面口径，则会出现"非 deep-dive 路径下 phase_history 永远为空"的协议缺口（C10 兼容性方案 A 失效），强烈不建议；建议 Reviewer 同周期更新主文档 §3 PR-4 描述（v2.3 微调）。

**兼容性影响**：
- 纯加项；旧 phase 不写 `phase_history` / `rca_fanout_mode_snapshot` 时迁移脚本注入默认值（`[] / null`），本变更点写入后字段从 default 升级到实际值，与读端（迁移脚本反查 / P3 重入时编排器读取）契约一致。
- 写入顺序：先 `rca_fanout_mode_snapshot`（覆盖式）后 `phase_history.append`（追加式），均在 RCA-LowConfidence stop 的 `fanout_mode = complex-arbitrated` **强制重写之前**执行，保证记录的是"P3 本次完成时" fanout_mode 的"自然取值"而非"被 stop 重写后的兜底取值"。这是 C10 兼容性方案 A 的关键语义点。
- 与 PR-2 解耦：本变更点行为完全不依赖 PR-2（不涉及 step-pause 或双写）。

---

#### 2.1.7 变更点 P3-C1 · step 5 medium-challenge challenger 注入 `confidence_input`（C2 调用方注入侧）

**原文（行号锚点 L79-89；medium-challenge 分支的 challenger invoke-subagent 块）**：

```79:89:mobile-qa-workflow/phases/p3-root-cause.md
                <invoke-subagent subagent_type="challenger" subagent_prompt="
                    <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                    <load target='mobile-qa-workflow/agents/shared-challenger-base.md' prompt='加载共享 challenger 基座'/>
                    <load target='mobile-qa-workflow/agents/challenger.md' prompt='加载主流程 challenger 包装层'/>
                    scene = RCA
                    dimension_set = rca-5d
                    target_list = 所有 Investigator 结论
                    supporting_context = {spec_file}, {context_bundle}
                    conditional_dimensions = temporal-drift | activation（仅在触发条件成立时执行）
                    输出 Challenge Report，保留 confidence_impact 字段。"/>
```

**新文**（在 `supporting_context` 行**之后**、`conditional_dimensions` 行**之前**插入 `confidence_input` 行；保留其余结构不变）：

```xml
                <invoke-subagent subagent_type="challenger" subagent_prompt="
                    <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                    <load target='mobile-qa-workflow/agents/shared-challenger-base.md' prompt='加载共享 challenger 基座'/>
                    <load target='mobile-qa-workflow/agents/challenger.md' prompt='加载主流程 challenger 包装层'/>
                    scene = RCA
                    dimension_set = rca-5d
                    target_list = 所有 Investigator 结论
                    supporting_context = {spec_file}, {context_bundle}
                    confidence_input = {上游 Investigator 输出的 final_score 列表（OVHSC SCORE 步产物，作为被质疑对象的原始置信度）}
                    conditional_dimensions = temporal-drift | activation（仅在触发条件成立时执行）
                    输出 Challenge Report，保留 confidence_impact 字段。"/>
```

**修订理由**：
- C2（v1.2.1 §三 C2 / 主文档 §1.1.1）：`agents/shared-challenger-base.md` 共享基座 wrapper 的输入契约**显式声明** `confidence_input = 被质疑对象原始置信度或原始评分`，该字段是 challenger 计算 `confidence_impact`（"挑战削弱原结论的程度"）的基线；当前 phase 调用方**完全没有注入该字段**，导致 wrapper 内的削弱量计算失锚。
- **C2 注入按"角色驱动"语义**（v2.0 修订）：所有 challenger（无论 RCA / FIX 场景）注入 `confidence_input`；所有 arbiter（无论 RCA / FIX 场景）注入 `base_score`。该映射与 `agents/shared-challenger-base.md` 与 `agents/shared-arbiter-base.md` 的输入契约**逐字段对齐**（v1.0 子文档把字段名按场景映射为"RCA → base_score / FIX → confidence_input"是错误设计，已被 PR-4 review 2026-04-20 Finding 2 纠正）。
- C2 由 **调用方注入侧（PR-4）+ wrapper 校验侧（PR-6）** 双侧落地：本 PR 负责调用方按角色注入；PR-6 在 `agents/shared-challenger-base.md` / `agents/shared-arbiter-base.md` 增加 `[Schema-Violation: missing confidence_input]` / `[Schema-Violation: missing base_score]` 缺参输出（C2-wrapper），形成"调用方必须按角色注入 → wrapper 校验缺参"双向闭环。
- `confidence_input` 取值来源：上游 Investigator 在 OVHSC 推理链的 SCORE 步输出 `final_score` 列表，作为"被质疑对象原始置信度"传给 challenger；本 PR prompt 内文字描述对齐 OVHSC 协议术语，与 `agents/investigator.md` 现有输出契约一致。

**兼容性影响**：
- 纯加项 prompt 字段；wrapper 在 PR-6 未合入前接受多余字段（LLM 自动忽略），不引入回归。
- PR-6 合入后 wrapper 将开始校验 `confidence_input` 缺参，本 PR 的注入是 PR-6 安全合入的**前置条件**（调用方先注入、wrapper 后校验，避免 PR-6 单独合入导致所有 challenger/arbiter 调用立即失败）。

---

#### 2.1.8 变更点 P3-C2 · step 5 complex-arbitrated challenger 注入 `confidence_input`（C2 调用方注入侧）

**原文（行号锚点 L119-127；complex-arbitrated 分支的 challenger invoke-subagent 块）**：

```119:127:mobile-qa-workflow/phases/p3-root-cause.md
                <invoke-subagent subagent_type="challenger" subagent_prompt="
                    <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                    <load target='mobile-qa-workflow/agents/shared-challenger-base.md' prompt='加载共享 challenger 基座'/>
                    <load target='mobile-qa-workflow/agents/challenger.md' prompt='加载主流程 challenger 包装层'/>
                    scene = RCA
                    dimension_set = rca-5d
                    target_list = 所有 Investigator 结论
                    supporting_context = {spec_file}, {context_bundle}
                    输出带 confidence_impact 的 Challenge Report。"/>
```

**新文**：

```xml
                <invoke-subagent subagent_type="challenger" subagent_prompt="
                    <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                    <load target='mobile-qa-workflow/agents/shared-challenger-base.md' prompt='加载共享 challenger 基座'/>
                    <load target='mobile-qa-workflow/agents/challenger.md' prompt='加载主流程 challenger 包装层'/>
                    scene = RCA
                    dimension_set = rca-5d
                    target_list = 所有 Investigator 结论
                    supporting_context = {spec_file}, {context_bundle}
                    confidence_input = {上游 2 个 Investigator 输出的 final_score 列表（OVHSC SCORE 步产物，按 Investigator 顺序合并；作为被质疑的双结论原始置信度）}
                    输出带 confidence_impact 的 Challenge Report。"/>
```

**修订理由**：与 P3-C1 同理（角色驱动：challenger → `confidence_input`），仅取值来源为**双 Investigator** 的合并列表（complex-arbitrated 模式下 Investigator-A + Investigator-B 各自独立产出 final_score）。

**兼容性影响**：同 P3-C1。

---

#### 2.1.9 变更点 P3-C3 · step 5 complex-arbitrated arbiter 注入 `base_score`（C2 调用方注入侧）

**原文（行号锚点 L128-136；complex-arbitrated 分支的 arbiter invoke-subagent 块）**：

```128:136:mobile-qa-workflow/phases/p3-root-cause.md
                <invoke-subagent subagent_type="arbiter" subagent_prompt="
                    <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                    <load target='mobile-qa-workflow/agents/shared-arbiter-base.md' prompt='加载共享 arbiter 基座'/>
                    <load target='mobile-qa-workflow/agents/arbiter.md' prompt='加载主流程 arbiter 包装层'/>
                    scene = RCA
                    comparison_focus = root-cause convergence | challenge absorption | confidence calibration
                    candidate_set = 所有 Investigator 结论
                    challenge_reports = Challenger 输出
                    按共享公式输出 final_confidence。"/>
```

**新文**：

```xml
                <invoke-subagent subagent_type="arbiter" subagent_prompt="
                    <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                    <load target='mobile-qa-workflow/agents/shared-arbiter-base.md' prompt='加载共享 arbiter 基座'/>
                    <load target='mobile-qa-workflow/agents/arbiter.md' prompt='加载主流程 arbiter 包装层'/>
                    scene = RCA
                    comparison_focus = root-cause convergence | challenge absorption | confidence calibration
                    candidate_set = 所有 Investigator 结论
                    challenge_reports = Challenger 输出
                    base_score = {候选 RCA 结论的基础评分 = 上游 2 个 Investigator 输出的 final_score 列表，作为 arbiter 加权裁决的原始评分基线}
                    按共享公式输出 final_confidence。"/>
```

**修订理由**：
- C2（角色驱动）：所有 arbiter（无论 RCA / FIX 场景）注入 `base_score`，与 `agents/shared-arbiter-base.md` 输入契约 `base_score = 候选结论基础评分或原始置信度` **逐字段对齐**。本 PR 是 P3 内**唯一**的 arbiter 调用点（complex-arbitrated 分支），缺参时 PR-6 的 wrapper 会输出 `[Schema-Violation: missing base_score]`。
- 与 P3-C1/C2 形成 RCA 角色矩阵闭环：challenger 拿 `confidence_input`（被质疑的原始置信度），arbiter 拿 `base_score`（候选结论的原始评分），二者语义并不冗余。

**兼容性影响**：同 P3-C1。

---

### 2.2 文件 B · `phases/p4-fix-design.md`（修改）

> **修复条目锚点**：C10 + D7（强制阶段间字段隔离：P4 内所有 `fanout_mode = X` 写入改为 `fix_fanout_mode = X`；**保留** P3/P6 内的 `fanout_mode` 写入不动） / C2（调用方注入：challenger → `confidence_input` ×2；arbiter → `base_score` ×1）

#### 2.2.1 变更点 P4-F1 · step 2 `fanout_mode = {fix_strategy_mode}` → `fix_fanout_mode`（C10 字段隔离）

**原文（行号锚点 L33-38）**：

```33:38:mobile-qa-workflow/phases/p4-fix-design.md
            <action>更新 {workflow_status}：
                - fix_risk_level = {fix_risk_level}
                - fix_strategy_mode = {fix_strategy_mode}
                - fanout_mode = {fix_strategy_mode}
                - reroute_reason = null
            </action>
```

**新文**（**仅替换** `fanout_mode = {fix_strategy_mode}` 一行为 `fix_fanout_mode = {fix_strategy_mode}`；其余 3 行保持）：

```xml
            <action>更新 {workflow_status}：
                - fix_risk_level = {fix_risk_level}
                - fix_strategy_mode = {fix_strategy_mode}
                - fix_fanout_mode = {fix_strategy_mode}
                - reroute_reason = null
            </action>
```

**修订理由**：
- C10（v1.2.1 §三 C10 / 主文档 §1.1.1）：v3 P4 step 2 复用 `fanout_mode` 字段写入 Fix 集取值（`single-proposer` / `challenged-proposer` / `contested-arbitrated`），导致：
  1. P4 完成后字段值变成 Fix 集，污染了 P3 完成时的 RCA 集快照（覆盖式破坏）；
  2. P4→P6→P3 失败回流到 P3 时，编排器/P3 step 4 依赖 `fanout_mode` 做升级判断，但读到的是 P4 留下的 Fix 集值 → switch 落入 default 分支 → C10 字段污染主缺陷复发。
- D7：保留 `fanout_mode` 为 RCA 字段不重命名；新增 `fix_fanout_mode` 承接 P4 的 Fix 集取值（PR-1 已在 `core/workflow-status-template.yaml` 注册 `fix_fanout_mode: null`）。本变更点是 D7 决定下 P4 写入端的**第 1 处**字段隔离落地。

**兼容性影响**：
- `fix_strategy_mode` 字段保持不变（v3 已存在，本 PR 不重命名）；本变更点仅把 `fanout_mode = X` 写入替换为 `fix_fanout_mode = X` 写入，逻辑层语义完全等价（同样标记本次 fix 的 fan-out 策略）。
- 迁移脚本（PR-1 §2.5）会把存量 v3 会话的 `fanout_mode` Fix 集取值拷贝到 `fix_fanout_mode`、清空原 `fanout_mode`、并尝试从 `phase_history` / `rca_fanout_mode_snapshot` 还原 RCA 集取值（详见主文档 §6.3）。本变更点保证存量会话迁移后字段写入路径与新会话一致。
- §5.1 第 7 项 / §5.3 回归矩阵第 6/7 行的"P4 不应裸写 fanout_mode"反向校验由 PR-8 CI 守门；本变更点是该守门的**对偶动作**。

---

#### 2.2.2 变更点 P4-F2 · step 3 challenged-proposer 升级到 contested-arbitrated 的 `fanout_mode` → `fix_fanout_mode`（C10 字段隔离）

**原文（行号锚点 L75-78；challenged-proposer 内 challenger 出现 Critical 时的升级动作）**：

```75:78:mobile-qa-workflow/phases/p4-fix-design.md
                <check if="challenger 出现 Critical">
                    <action>更新 {workflow_status}：fix_strategy_mode = contested-arbitrated, fanout_mode = contested-arbitrated, reroute_reason = challenged_fix_escalated</action>
                    <action>goto step="3"</action>
                </check>
```

**新文**（**仅替换** `fanout_mode = contested-arbitrated` 为 `fix_fanout_mode = contested-arbitrated`；其余字段不动）：

```xml
                <check if="challenger 出现 Critical">
                    <action>更新 {workflow_status}：fix_strategy_mode = contested-arbitrated, fix_fanout_mode = contested-arbitrated, reroute_reason = challenged_fix_escalated</action>
                    <action>goto step="3"</action>
                </check>
```

**修订理由**：与 P4-F1 同理；本 case 是 P4 内**第 2 处**（也是 v4.1 P4 内**最后一处**）`fanout_mode` 写入，必须同步迁移到 `fix_fanout_mode` 才能完成 C10 字段隔离闭环。grep `phases/p4-fix-design.md` 中的 `fanout_mode` 命中**应为 0**（替换后），这是 §5.1 第 7 项的核心断言。

**兼容性影响**：
- `goto step="3"` 自循环逻辑保持不变；升级到 contested-arbitrated 后重新进入 step 3，由 step 3 的 `<check if="fix_strategy_mode == contested-arbitrated">` 分支接管，行为完全等价。
- 与 P3 内合法的 `fanout_mode = complex-arbitrated`（变更点 P3-A2/A3/A4 涉及，本 PR 不动）严格区分：P3 写 `fanout_mode` 是 RCA 升级（合法），P4 写 `fix_fanout_mode` 是 Fix 升级（C10 隔离）。

---

#### 2.2.3 变更点 P4-C4 · step 3 challenged-proposer challenger 注入 `confidence_input`（C2 调用方注入侧）

**原文（行号锚点 L62-70；challenged-proposer 分支的 challenger invoke-subagent 块）**：

```62:70:mobile-qa-workflow/phases/p4-fix-design.md
                    <invoke-subagent subagent_type="challenger" subagent_prompt="
                        <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                        <load target='mobile-qa-workflow/agents/shared-challenger-base.md' prompt='加载共享 challenger 基座'/>
                        <load target='mobile-qa-workflow/agents/challenger.md' prompt='加载主流程 challenger 包装层'/>
                        scene = FIX
                        dimension_set = fix-4a
                        target_list = 当前 Fix-Proposer 方案
                        supporting_context = {rca_report}, {spec_file}
                        输出四重攻击结果与 confidence_impact。"/>
```

**新文**（在 `supporting_context` 行**之后**插入 `confidence_input` 行）：

```xml
                    <invoke-subagent subagent_type="challenger" subagent_prompt="
                        <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                        <load target='mobile-qa-workflow/agents/shared-challenger-base.md' prompt='加载共享 challenger 基座'/>
                        <load target='mobile-qa-workflow/agents/challenger.md' prompt='加载主流程 challenger 包装层'/>
                        scene = FIX
                        dimension_set = fix-4a
                        target_list = 当前 Fix-Proposer 方案
                        supporting_context = {rca_report}, {spec_file}
                        confidence_input = { rca_final_confidence: {上游 P3 arbiter 的 final_confidence}, fix_proposer_self_confidence: {当前 Fix-Proposer 自评置信度} }
                        输出四重攻击结果与 confidence_impact。"/>
```

**修订理由**：
- C2（角色驱动）：所有 challenger 注入 `confidence_input` —— 与 P3-C1/C2 共用同一字段名，区别仅在取值结构（FIX 场景下需同时携带"上游 RCA 的最终置信度"决定本次 fix 是否值得做、与"Fix-Proposer 自评置信度"决定方案本身的可信度基线）。`agents/shared-challenger-base.md` 共享公式以 `confidence_input` 为基线计算 `confidence_impact`，字段名按 wrapper 输入契约固定。
- 字段结构 `{ rca_final_confidence, fix_proposer_self_confidence }` 是 FIX 场景下 `confidence_input` 的复合取值，与 `agents/shared-challenger-base.md` 在 PR-6 中将引入的 `[Schema-Violation: missing confidence_input]` 缺参校验**逐字段对齐**（PR-6 仅校验顶层键 `confidence_input` 存在性，不校验子结构 — 子结构由 wrapper 内 OVHSC 推理自适配）。

**兼容性影响**：与 P3-C1 同理；纯加项，PR-6 未合入前 wrapper 接受多余字段，不引入回归；PR-6 合入后调用方注入即满足 wrapper 校验。

---

#### 2.2.4 变更点 P4-C5 · step 3 contested-arbitrated challenger 注入 `confidence_input`（C2 调用方注入侧）

**原文（行号锚点 L93-101；contested-arbitrated 分支的 challenger invoke-subagent 块）**：

```93:101:mobile-qa-workflow/phases/p4-fix-design.md
                    <invoke-subagent subagent_type="challenger" subagent_prompt="
                        <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                        <load target='mobile-qa-workflow/agents/shared-challenger-base.md' prompt='加载共享 challenger 基座'/>
                        <load target='mobile-qa-workflow/agents/challenger.md' prompt='加载主流程 challenger 包装层'/>
                        scene = FIX
                        dimension_set = fix-4a
                        target_list = 所有 Fix-Proposer 方案
                        supporting_context = {rca_report}, {spec_file}
                        输出四重攻击结果。"/>
```

**新文**：

```xml
                    <invoke-subagent subagent_type="challenger" subagent_prompt="
                        <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                        <load target='mobile-qa-workflow/agents/shared-challenger-base.md' prompt='加载共享 challenger 基座'/>
                        <load target='mobile-qa-workflow/agents/challenger.md' prompt='加载主流程 challenger 包装层'/>
                        scene = FIX
                        dimension_set = fix-4a
                        target_list = 所有 Fix-Proposer 方案
                        supporting_context = {rca_report}, {spec_file}
                        confidence_input = { rca_final_confidence: {上游 P3 arbiter 的 final_confidence}, fix_proposer_self_confidence: {Proposer-A 自评置信度 + Proposer-B 自评置信度 数组} }
                        输出四重攻击结果。"/>
```

**修订理由**：与 P4-C4 同理（角色驱动：challenger → `confidence_input`）；contested-arbitrated 模式下 `fix_proposer_self_confidence` 是 Proposer-A / Proposer-B 双方案的自评置信度数组（与 P3-C2 的双 Investigator 对偶）。

**兼容性影响**：同 P4-C4。

---

#### 2.2.5 变更点 P4-C6 · step 3 contested-arbitrated arbiter 注入 `base_score`（C2 调用方注入侧）

**原文（行号锚点 L102-110；contested-arbitrated 分支的 arbiter invoke-subagent 块）**：

```102:110:mobile-qa-workflow/phases/p4-fix-design.md
                    <invoke-subagent subagent_type="arbiter" subagent_prompt="
                        <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                        <load target='mobile-qa-workflow/agents/shared-arbiter-base.md' prompt='加载共享 arbiter 基座'/>
                        <load target='mobile-qa-workflow/agents/arbiter.md' prompt='加载主流程 arbiter 包装层'/>
                        scene = FIX
                        comparison_focus = root-cause coverage | side-effect risk | minimality | rollback safety
                        candidate_set = 所有 Fix-Proposer 方案
                        challenge_reports = Challenger 输出
                        输出最终方案裁定、评估矩阵与 final_confidence。"/>
```

**新文**：

```xml
                    <invoke-subagent subagent_type="arbiter" subagent_prompt="
                        <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                        <load target='mobile-qa-workflow/agents/shared-arbiter-base.md' prompt='加载共享 arbiter 基座'/>
                        <load target='mobile-qa-workflow/agents/arbiter.md' prompt='加载主流程 arbiter 包装层'/>
                        scene = FIX
                        comparison_focus = root-cause coverage | side-effect risk | minimality | rollback safety
                    candidate_set = 所有 Fix-Proposer 方案
                    challenge_reports = Challenger 输出
                    base_score = {候选 Fix 方案的基础评分 = Proposer-A / Proposer-B 自评置信度数组（作为 arbiter 加权裁决的原始评分基线）；可附 rca_final_confidence 作为权重缩放因子}
                    输出最终方案裁定、评估矩阵与 final_confidence。"/>
```

**修订理由**：
- C2（角色驱动）：所有 arbiter（无论 RCA / FIX 场景）注入 `base_score`，与 P3-C3 共用同一字段名 — 与 `agents/shared-arbiter-base.md` 输入契约 `base_score = 候选结论基础评分或原始置信度` **逐字段对齐**。本 PR 是 P4 内**唯一**的 arbiter 调用点（contested-arbitrated 分支），缺参时 PR-6 的 wrapper 会输出 `[Schema-Violation: missing base_score]`。
- 取值结构差异：FIX 场景下 `base_score` 主体是 Fix-Proposer 自评置信度数组（候选方案的原始评分），可在 wrapper 内附带 `rca_final_confidence` 作为权重缩放（与 challenger 的 `confidence_input` 复合结构对偶但角色用途不同）。
- v1.0 子文档把本变更点错配为 `confidence_input` 是 PR-4 review 2026-04-20 Finding 2 揭示的字段命名矩阵反转错误，已在 v2.0 纠正。

**兼容性影响**：同 P4-C4。

---

### 2.3 文件 C · `phases/p6-verification.md`（修改）

> **修复条目锚点**：B1\*（P6 失败回流早退点 ABORT 标记 1 处） / C9（失败分支必输出 verification-report 中间态；与 PR-6 模板侧的"中间态报告（失败回流时使用）"段落联动）

#### 2.3.1 变更点 P6-A6 · step 6 失败回流早退点 ABORT 标记 + 中间态 template-output（B1\* + C9）

**原文（行号锚点 L63-85）**：

```63:85:mobile-qa-workflow/phases/p6-verification.md
    <step n="6" goal="验证判定与回流">
        <action>若存在失败项，先分类：design_insufficient / root_cause_not_closed / implementation_mismatch。</action>
        <check if="L1 + L2 + L3-Static 全部通过">
            <action>更新 {workflow_status}：verification_failure_type = null, reroute_reason = null, reroute_target_phase = null</action>
        </check>
        <check if="任一层未通过">
            <switch condition="{verification_failure_type}">
                <case if="design_insufficient">
                    <action>更新 {workflow_status}：current_state = Fix-Designing, reroute_reason = verification_design_insufficient, reroute_from_phase = qa-verification, reroute_target_phase = qa-fix-design, fix_retry_count += 1</action>
                </case>
                <case if="root_cause_not_closed">
                    <action>更新 {workflow_status}：current_state = RCA-InProgress, verification_failure_type = root_cause_not_closed, fanout_mode = complex-arbitrated, reroute_reason = verification_root_cause_not_closed, reroute_from_phase = qa-verification, reroute_target_phase = qa-root-cause, rca_retry_count += 1</action>
                </case>
                <case if="implementation_mismatch">
                    <action>更新 {workflow_status}：current_state = Fix-Designing, reroute_reason = verification_implementation_mismatch, reroute_from_phase = qa-verification, reroute_target_phase = qa-fix-design, fix_retry_count += 1</action>
                </case>
                <default>
                    <action>更新 {workflow_status}：current_state = Human-Review</action>
                </default>
            </switch>
            <action>阶段结束，返回编排器</action>
        </check>
    </step>
```

**新文**（在"阶段结束，返回编排器"前插入 **(1) 中间态 template-output（C9）+ (2) ABORT 标记（B1\*）**；同时**最小修复**两处既有缺陷 — case `root_cause_not_closed` 的 `current_state = RCA-InProgress` → `RCA-Designing`（C5 状态枚举权威源对齐，PR-4 review 2026-04-20 Finding 1 直接对应）；保留 case `root_cause_not_closed` 强制 `fanout_mode = complex-arbitrated` 不动 — 这是合法 RCA 升级语义，不属 C10 污染范畴；保留 case `implementation_mismatch` / `design_insufficient` / default 不动）：

```xml
    <step n="6" goal="验证判定与回流">
        <action>若存在失败项，先分类：design_insufficient / root_cause_not_closed / implementation_mismatch。</action>
        <check if="L1 + L2 + L3-Static 全部通过">
            <action>更新 {workflow_status}：verification_failure_type = null, reroute_reason = null, reroute_target_phase = null</action>
        </check>
        <check if="任一层未通过">
            <switch condition="{verification_failure_type}">
                <case if="design_insufficient">
                    <action>更新 {workflow_status}：current_state = Fix-Designing, reroute_reason = verification_design_insufficient, reroute_from_phase = qa-verification, reroute_target_phase = qa-fix-design, fix_retry_count += 1</action>
                </case>
                <case if="root_cause_not_closed">
                    <!-- C5 收口：current_state 取值必须落在 core/workflow-status-template.yaml 头部注释列出的权威枚举集内；
                         RCA-InProgress 不在该集合内（合法集为 RCA-Designing / RCA-LowConfidence），属 v3 字面残留 —
                         本 PR 收口为 RCA-Designing：语义为"将状态机回退到 RCA 设计阶段，由 P3 step 1 起重入"，
                         与编排器 step 2/4 现有路由（按 reroute_target_phase = qa-root-cause）完全自洽，不引入新 case。 -->
                    <action>更新 {workflow_status}：current_state = RCA-Designing, verification_failure_type = root_cause_not_closed, fanout_mode = complex-arbitrated, reroute_reason = verification_root_cause_not_closed, reroute_from_phase = qa-verification, reroute_target_phase = qa-root-cause, rca_retry_count += 1</action>
                </case>
                <case if="implementation_mismatch">
                    <action>更新 {workflow_status}：current_state = Fix-Designing, reroute_reason = verification_implementation_mismatch, reroute_from_phase = qa-verification, reroute_target_phase = qa-fix-design, fix_retry_count += 1</action>
                </case>
                <default>
                    <action>更新 {workflow_status}：current_state = Human-Review</action>
                </default>
            </switch>

            <!-- C9：失败分支必先输出"中间态" verification-report 再回流；
                 模板段落"中间态报告（失败回流时使用）"由 PR-6 在 templates/verification-report.md 提供，
                 包含必填字段 failure_classification / evidence / repro_path。
                 注意：此处与 step 7 正常路径的 template-output 共享 {output_verification} 路径 —
                 中间态/正态区分由模板内部按 verification_failure_type 是否为空切换段落（PR-6 落地），
                 PR-4 调用方仅传现有 file/template 两个属性，不引入 mode 属性（避免与 core-rules.xml
                 <template-output> 标签 DSL 漂移；详见 §6 议题 #3 v2.0 收口）。 -->
            <template-output file="{output_verification}" template="mobile-qa-workflow/templates/verification-report.md"/>
            <action>更新 {config_source}：output_verification_report = {output_verification}</action>

            <!-- B1*：P6 失败回流是 stop_state（current_state ∈ {Fix-Designing, RCA-Designing, Human-Review}），
                 按 D1 协议必须 ABORT；编排器 step 4 检测 ABORT 后不追加 qa-verification 到 stepsCompleted,
                 让回流目标 phase（qa-fix-design / qa-root-cause）能被重新执行。 -->
            <action>设置 current_phase_result = ABORT</action>
            <action>阶段结束，返回编排器</action>
        </check>
    </step>
```

**修订理由**：
- B1\*（v1.2.1 §三 B1\* / 主文档 §1.1.1）：P6 失败回流是 stop_state；当前 v3 仅写 `current_state` 后直接"阶段结束，返回编排器"，编排器 step 4 默认按"phase 正常完成"追加 `qa-verification` 到 `stepsCompleted`，下一轮编排器 step 2 以为 P6 已完成 → 回流到 qa-fix-design 后再次回流到 P6 时直接跳过 → B1\* 失锚的次生症状。本变更点是 P6 内**唯一**早退点位的 ABORT 落地，与 P3-A1~A5 形成 B1\* 修复的完整闭环。
- C9（v1.2.1 §三 C9 / 主文档 §1.1.1）：当前 v3 的 `<template-output>`（step 7）只在"L1+L2+L3-Static 全部通过"路径下执行，失败回流时根本到不了 step 7 → 失败回流没有任何 verification-report 产物 → 用户和下游 phase 无从知道失败的具体证据。本变更点在失败分支**显式**调用一次 template-output（仅用现有 `file` / `template` 属性，无新属性引入），与 PR-6 在 `templates/verification-report.md` 新增的"中间态报告（失败回流时使用）"段落联动 — PR-6 模板内由 `verification_failure_type` 是否为空切换中间态/正态段落（v2.0 收口方案）。
- 字段保留说明 1：case `root_cause_not_closed` 强制 `fanout_mode = complex-arbitrated` 是**合法的 RCA 升级语义**（D7 决定下 `fanout_mode` 保留为 RCA 字段），与 C10 字段污染**无关**；本变更点严格保留该写入，不改为 `fix_fanout_mode`。
- **C5 状态枚举权威源对齐 — `RCA-InProgress` → `RCA-Designing` 收口**（v2.0 修订 / PR-4 review 2026-04-20 Finding 1 直接对应）：
  - **事实依据**：`core/workflow-status-template.yaml` 头部注释（PR-1 已固化）明确列出"v4.1 完整集合：Intake / Spec-Defining / Spec-Uncertain / Context-Curating / Curation-Failed / Boundary-Refined / Non-Bug / Info-Insufficient / **RCA-Designing** / **RCA-LowConfidence** / Fix-Designing / Fix-Implementing / Verifying / Human-Review / Done"，**不包含** `RCA-InProgress`；继续写入 `RCA-InProgress` 会导致 PR-8 CI 的"current_state 取值落在权威枚举集"静态校验（§5.1 第 1 项）必然失败。
  - **收口语义**：`RCA-Designing` 准确表达"将状态机回退到 RCA 设计阶段，由 P3 step 1 起重入"；编排器 step 2/4 按 `reroute_target_phase = qa-root-cause` 路由到 P3，与 `current_state` 的字面取值无关 — 因此本变更点**不需要在编排器 step 4 新增 case `RCA-Designing` 触发任何 step-pause**（P3 重入是直行路径，非用户交互），与 PR-2 编排器适配层完全自洽，不引入新依赖。
  - **v1.0 保守口径已撤销**：v1.0 子文档把本议题登记为"PR-4 不动、与 PR-2 review #1 合并、v4.1 hotfix 整改"。该口径会让 PR-4 的 §3.1 第 1 项 DoD（current_state 枚举合规）在 P6 失败回流路径下必然失败，等于**把已知协议违反留到 hotfix**，与 PR-4 review 2026-04-20 Finding 1 "Critical 等级、必须修复" 评估一致。v2.0 收口为 PR-4 内最小修复（仅替换 1 个状态字面值，不涉及编排器 / wrapper / 模板任何改动）。
- **`<template-output>` `mode` 属性 — 取消引入**（v2.0 修订 / PR-4 review 2026-04-20 Finding 3 直接对应）：
  - **事实依据**：`core/core-rules.xml` `<supported-tags>` 内 `<template-output>` 标签 DSL 仅声明 `file` / `template` 两个属性，未定义 `mode` 参数；v1.0 子文档引入 `mode="intermediate"` 等于在 PR-1 协议层未登记新属性的前提下让 PR-4 phase 调用方先用，会触发 PR-8 CI 的"DSL 标签属性合规"静态校验失败。
  - **收口方案 = 议题 #3 选项 (b)**：放弃 `mode` 属性，把"中间态 / 正态报告段落选择"逻辑下沉到 `templates/verification-report.md` 模板内部 — 由 PR-6 在该模板提供"中间态报告（失败回流时使用）"段落，开头以 `if {verification_failure_type} != null` 判定切换段落（PR-6 联动改动，不在本 PR 范围）。本 PR 调用方只传现有 `file` / `template` 两个属性，与现有 DSL 完全兼容，不依赖任何 PR-1 hotfix。
  - **v1.0 保守口径已撤销**：v1.0 子文档把本议题登记为"二选一 + 推荐 PR-1 hotfix"。该口径会让 PR-4 引入 1 处未登记属性，等于**把 DSL 漂移留到 hotfix**，与 PR-4 review 2026-04-20 Finding 3 "Major 等级、必须修复" 评估一致。v2.0 直接采纳兼容性更好的方案 (b)，与 PR-6 的模板段落联动方式不变。

**兼容性影响**：
- 纯加项（无新属性引入）；PR-6 未合入前 `templates/verification-report.md` 没有"中间态报告"段落 → template-output 会按现有模板结构输出（最坏后果是中间态字段为空），不引入回归。
- PR-6 合入后中间态段落落地，本 PR 的 template-output 调用立即生效，与 §5.2.6 用例 F（C9 P6 失败分支产物）完全对齐。
- ABORT 标记与 PR-2 完全解耦（D1 方案 A 红利）；PR-2 滞后时 case Human-Review / Fix-Designing / RCA-Designing 走 v3 step-pause（仅 Human-Review case 是 step-pause 触发点；Fix-Designing / RCA-Designing 不触发 step-pause 直接回流到对应 phase 重入），ABORT 行为本身不变。
- `RCA-InProgress → RCA-Designing` 收口与编排器 step 4 完全解耦：编排器按 `reroute_target_phase` 路由，不读 `current_state` 字面值做 case 分发（`current_state` 仅参与 step 2 的 case 选择，而 step 2 case 已存在 `RCA-Designing` 分支映射到 P3 入口）；存量 v3 会话迁移脚本（PR-1 §2.5）建议增加一行 `RCA-InProgress → RCA-Designing` 字符串替换（**Reviewer 议题 v2.3 微调**：建议主文档 §2.5 hotfix 时同步登记此规则，避免存量会话迁移到 v4 后 current_state 仍为 `RCA-InProgress` 残留）。

---

## 3. PR-level DoD 子集（链接到主文档 §5）

> 完整清单见主文档 [§5.1 静态契约校验](../../QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md#51-静态契约校验每个-pr-必跑) 与 [§5.2 动态用例](../../QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md#52-动态用例关键回归路径)。本节仅列 PR-4 必须满足的子集。

### 3.1 §5.1 静态契约校验（PR-4 必跑子集）

- [ ] **ABORT 标记完整**（§5.1 第 9 项 / B1\* 主链路 / **总计 6 处 = P3 ×5 + P6 ×1**）：
  - `phases/p3-root-cause.md` 中 grep `<action>设置 current_phase_result = ABORT</action>` **应命中精确 5 处**（变更点 P3-A1 ~ A5；其中 P3-A5 是 v2.2 实施期增补，已在 v2.0 子文档与 v2.3 主文档微调统一收录）；
  - `phases/p6-verification.md` 中 grep 应命中 **精确 1 处**（变更点 P6-A6）；
  - 任何 phase 文件内的"阶段结束，返回编排器"前必须有 ABORT 设值动作（除 step 10 case "最终置信度 >= 0.5" 这类**显式不写**的成功完成路径外）。
- [ ] **字段隔离**（§5.1 第 7 项 / C10 + D7）：
  - grep `phases/p4-fix-design.md` 中 `fanout_mode\s*=` 命中 **0 处**（变更点 P4-F1/F2 替换后），仅允许 `fix_fanout_mode = ...` 写入；
  - grep `phases/p3-root-cause.md` 与 `phases/p6-verification.md` 中 `fanout_mode\s*=` 仍可命中（合法 RCA 字段写入：P3 的 medium-challenge / complex-arbitrated 升级、P6 的 root_cause_not_closed 升级），**这些写入本 PR 不动**；
  - grep `fix_fanout_mode` 在 `phases/p4-fix-design.md` 命中 **2 处**（P4-F1 + P4-F2）。
- [ ] **不存在 `rca_fanout_mode` 裸字段**（§5.1 第 8 项 / D7 反向校验）：grep `phases/**/*.md` 中 `rca_fanout_mode\b` 命中 **0 处**（不允许出现 `rca_fanout_mode` 裸字段；`rca_fanout_mode_snapshot` 是合法的 snapshot 字段名，仅在 P3-H1 写入 1 处）。
- [ ] **`rca_fanout_mode_snapshot` 写入端落地**（§5.1 关联第 7 项 / C10 + D7）：grep `phases/p3-root-cause.md` 中 `rca_fanout_mode_snapshot` 命中 **1 处**（变更点 P3-H1，位于 step 10 内），位于 `current_state = Fix-Designing / RCA-LowConfidence` 写入**之前**；不允许在 P4 / P6 写入该字段。
- [ ] **`phase_history` append 元素结构合规**（§5.1 关联第 1/15 项 / 与 PR-1 头部注释一致）：grep `phases/p3-root-cause.md` 中 `phase_history` 命中 **1 处**（变更点 P3-H1），append 元素必须包含 4 个键：`phase` / `timestamp` / `fanout_mode` / `note`，且 `phase` 取值 = `"qa-root-cause"`、`note` 取值 = `null`（v4.1 保守口径）。
- [ ] **持久化字段表纯净性**（§5.1 第 15 项 / D1）：grep `phases/p{3,4,6}-*.md` 中 `current_phase_result` 仅作为**赋值动作**（`<action>设置 current_phase_result = ABORT</action>`）出现；**禁止**作为 `<action>更新 {workflow_status}：current_phase_result = ...</action>` 形式写入持久化文件。本 PR 引入的所有 ABORT 标记应均为前者（赋值动作）。
- [ ] **C2 调用方注入完整 — 角色驱动矩阵**（§5.1 关联第 5 项 / C2 / wrapper 输入契约 `agents/shared-{challenger,arbiter}-base.md`）：
  - **challenger 角色**（无论 RCA / FIX 场景）必须含 `confidence_input = ...` 行：
    - `phases/p3-root-cause.md` grep `subagent_type="challenger"` 命中 **2 处**（P3-C1 medium-challenge / P3-C2 complex-arbitrated），每处 prompt 内必须含 `confidence_input = ...`
    - `phases/p4-fix-design.md` grep `subagent_type="challenger"` 命中 **2 处**（P4-C4 challenged-proposer / P4-C5 contested-arbitrated），每处 prompt 内必须含 `confidence_input = ...`
    - 合计 challenger × `confidence_input` = **4 处**
  - **arbiter 角色**（无论 RCA / FIX 场景）必须含 `base_score = ...` 行：
    - `phases/p3-root-cause.md` grep `subagent_type="arbiter"` 命中 **1 处**（P3-C3 complex-arbitrated），prompt 内必须含 `base_score = ...`
    - `phases/p4-fix-design.md` grep `subagent_type="arbiter"` 命中 **1 处**（P4-C6 contested-arbitrated），prompt 内必须含 `base_score = ...`
    - 合计 arbiter × `base_score` = **2 处**
  - **反向断言**（防止字段命名矩阵反转复发，PR-4 review 2026-04-20 Finding 2 直接对应）：
    - challenger 块内 grep `base_score` **必须命中 0 处**（角色错配立即 fail）
    - arbiter 块内 grep `confidence_input` **必须命中 0 处**（角色错配立即 fail）
  - `subagent_type="fix-proposer"` 与 `subagent_type="investigator"` 不强制注入（这两类是基线产生者而非置信度计算者）；
- [ ] **C9 P6 失败分支产物**（§5.1 关联第 9 项 / C9 phase 侧）：grep `phases/p6-verification.md` step 6 内必须命中 **1 处** `<template-output ...verification-report.md...>`（变更点 P6-T1，与 step 7 内的另 1 处共 2 处 template-output；step 6 内的 1 处必须位于 `阶段结束，返回编排器` **之前**且位于 `设置 current_phase_result = ABORT` **之前**）。
- [ ] **D14 调度作用域守门间接达成**（§5.1 第 11 项 / D14）：本 PR 不在任何 phase 文件内**新增** `<step-pause>`；P4 step 6 末尾的现存 `<step-pause>`（v3 已存在，登记到 PR-5 allowlist）不动，本 PR diff 中 `<step-pause` 的命中数 = **0**。
- [ ] **D14 反向断言**：本 PR 不修改 `core/workflow.xml` / `core/core-rules.xml` / `core/workflow-status-template.yaml`（这些属于 PR-1 / PR-2 范围；如本 PR diff 命中这些路径，PR-8 CI 必须 fail）。

### 3.2 §5.2 动态用例（PR-4 必跑子集）

- [ ] **§5.2.1 用例 A · B1\* P3 RCA 低置信回流** 完整通过 — 这是 PR-4 的**核心验收用例**，必须在 PR description 附 LLM 重放 trace。期望路径：
  1. 模拟 P3 step 10 case "最终置信度 < 0.5"（变更点 P3-A5 落地）→ phase 内显式 `current_phase_result = ABORT`（LLM 输出中 grep 验证）；
  2. P3 完成时 `phase_history` append `{ phase: "qa-root-cause", ..., fanout_mode: <stop 之前的取值>, note: null }`（变更点 P3-H1 落地）；同时 `rca_fanout_mode_snapshot = <同 fanout_mode>`；
  3. 编排器 step 4 检测 ABORT，**不追加** `qa-root-cause` 到 `stepsCompleted`；
  4. 终态 `current_state = RCA-LowConfidence`、`stepsCompleted` 不包含 `qa-root-cause`；
  5. 编排器 step 4 case `RCA-LowConfidence` 触发 step-pause（PR-2 变更点 W6 提供）；用户回复 `rca_lowconf_action=Retry` → 进入 case Retry → `current_state = Spec-Defining` → P2 重新执行。
- [ ] **§5.2.3 用例 C · C10 P3→P4→P6→P3 字段污染** 完整通过 — PR-4 的**第二核心**验收用例，必须在 PR description 附 LLM 重放 trace。期望路径：
  1. P3 完成时 `phase_history` append `{ phase: "qa-root-cause", ..., fanout_mode: medium-challenge, ... }`（变更点 P3-H1 落地）；同时 `rca_fanout_mode_snapshot = medium-challenge`；
  2. P4 step 2 仅写 `fix_fanout_mode = single-proposer`（变更点 P4-F1 落地），**不动** `fanout_mode`（grep 验证 P4 内 `fanout_mode\s*=` 命中 0）；
  3. P6 失败回流到 P3 时强制 `fanout_mode = complex-arbitrated`（合法 RCA 路由，非污染）；
  4. P3 重入时读到的 `fanout_mode = complex-arbitrated`（被 P6 重写为合法 RCA 值）；如未被 P6 重写，则与 `rca_fanout_mode_snapshot` 一致。
- [ ] **§5.2.6 用例 F · C9 P6 失败分支产物** 完整通过（与 PR-6 联合验收）：
  1. 模拟 P6 step 6 触发 `verification_failure_type = design_insufficient` 失败回流；
  2. `verification-report.md` 物理存在（变更点 P6-T1 落地）；
  3. 文件内含 `failure_classification` / `evidence` / `repro_path` 三必填字段（PR-6 模板侧 `templates/verification-report.md` "中间态报告"段落提供）；
  4. PR-6 滞后时报告字段为空但文件存在（PR-4 单独验收点位）。
- [ ] **回归用例 1**（B1\* + ABORT 标记反向断言）：模拟 P3 step 10 case "最终置信度 >= 0.5"（成功完成路径）→ LLM 输出中 grep `current_phase_result` 应命中 **0 处**（成功路径不写 ABORT）→ 编排器 step 4 按正常完成追加 `qa-root-cause` 到 `stepsCompleted` → 进入 P4。如成功路径误写 ABORT，会导致 P3 永远无法完成，工作流死锁。
- [ ] **回归用例 2**（C2 + 调用方注入正向断言 — 角色驱动）：模拟 P3 step 5 complex-arbitrated 路径触发 challenger 与 arbiter 调用 → challenger 调用的 subagent_prompt 文本 grep `confidence_input` 命中 **1 次**（P3-C2），arbiter 调用的 subagent_prompt 文本 grep `base_score` 命中 **1 次**（P3-C3）；P4 step 3 contested-arbitrated 路径触发 challenger 与 arbiter 调用 → challenger grep `confidence_input` 命中 **1 次**（P4-C5），arbiter grep `base_score` 命中 **1 次**（P4-C6）；反向断言 challenger grep `base_score` = 0、arbiter grep `confidence_input` = 0（防字段命名矩阵反转复发）。

> **PR-4 不验收的 §5.x 项**（由后续 PR 联动）：
> - §5.1 第 1/2/3/4/5/6/8/10/11/12/13/14/16/17 项 → PR-1 / PR-2 / PR-3 / PR-5 / PR-7 / PR-8 承接（其中第 8 项 D7 反向校验由 PR-1 / PR-2 / PR-4 多方共同保证，PR-4 已在自身 DoD 第 3 条覆盖）
> - §5.2.2 用例 B（B2 P2 Non-Bug 反流） → PR-3 + PR-2 联合验收（PR-4 不涉及 P2）
> - §5.2.4 用例 D（C11 step-pause 编排器侧规范化） → PR-2 验收
> - §5.2.5 用例 E（B3 Deep-Dive 落盘） → PR-5 验收
> - §5.3 回归矩阵第 6/7 行（fanout_mode 在 RCA / Fix 集的写入隔离） → PR-4（本 PR）+ PR-1（迁移脚本反查能力）联合验收

---

## 4. PR-level 回滚动作（链接到主文档 §7）

完整回滚预案见主文档 [§7.4 PR-4 回滚](../../QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md#74-pr-4-回滚)，关键点摘录：

- **回滚命令**：`git revert <PR-4-merge-commit>`。
- **回滚后状态**：
  - P3/P6 的 ABORT 标记 **6 处全部消失**（P3 ×5 + P6 ×1，含 v2.2 实施期增补的 P3-A5）→ B1\* 主链路根因复发：编排器 step 4 把 `qa-root-cause` / `qa-verification` 误追加到 `stepsCompleted` → 后续 phase 跳过重试。
  - `fix_fanout_mode` 字段在 P4 内的写入消失 → C10 字段污染复发：P4 重新写 `fanout_mode = X`，P3 重入时 switch 落入 default 分支。
  - `phase_history` 与 `rca_fanout_mode_snapshot` 不再被 P3 写入 → C10 兼容性方案 A + B 双保险同时失效；迁移脚本（PR-1 §2.5）`--restore-fanout-mode` 子命令的反查依赖失效。
  - P6-A6 的 `current_state = RCA-Designing` 收口同时回滚为 v3 字面残留 `RCA-InProgress` → C5 状态枚举权威源漂移复发，PR-8 CI §5.1 第 1 项立即 fail。
  - P6 失败分支不再产出中间态 `verification-report.md` → 用户和下游 phase 无从知道失败证据。
  - challenger / arbiter 的 subagent_prompt 不再按角色驱动注入 `confidence_input` / `base_score` → 如 PR-6 已合入（增加了 wrapper 的 `[Schema-Violation]` 缺参校验），所有 P3 / P4 的 challenger / arbiter 调用立即失败；如 PR-6 未合入则静默回退到 v3 行为（confidence 计算失锚但不报错）。
- **下游影响**：
  - PR-3（P2 Non-Bug 闭环）独立于 PR-4，回滚 PR-4 不影响 PR-3 的 P2 早退路径；
  - PR-5（Deep-Dive 落盘）独立于 PR-4；
  - PR-6（C2-wrapper Schema-Violation）与 PR-4 强耦合：PR-4 回滚后 PR-6 的 wrapper 校验会让所有 P3/P4 challenger/arbiter 调用立即失败 → 必须**同步评估**是否回滚 PR-6（建议 PR-4 + PR-6 同周期回滚，或临时在 wrapper 内禁用 `[Schema-Violation]` 校验）；
  - PR-7（文档同步）的 `fix_fanout_mode` / `phase_history` / `rca_fanout_mode_snapshot` 字段说明不影响功能，可单独保留或同步回滚；
  - PR-8（CI 守门）的 §5.1 第 7/8/9 项断言会立即失败（因为 PR-4 引入的 `fanout_mode → fix_fanout_mode` 替换被回滚后，CI 会检测到 P4 内 `fanout_mode` 裸写）→ **PR-8 CI 会自动阻止 PR-4 单独回滚**，强制 reviewer 评估全链路影响。
- **风险等级**：🟡 **中**。
- **存量 v3 会话兼容**：迁移脚本不支持 v4 → v3 反向迁移；存量已迁移到 v4 的会话**仍然为 v4 schema**，但 `phase_history` 永远空 / `rca_fanout_mode_snapshot` 永远 null / P4 重新污染 `fanout_mode` → 这些会话需要手工编辑或恢复备份。

---

## 5. §5.1 静态契约校验自检（PR-4 视角）

> 按主文档 §5.1 17 项清单逐项核查 PR-4 是否落地或留待后续 PR 联动。✅ = 本 PR 满足；⏸ = 不在本 PR 范围（标注承接方）；➖ = 本 PR 不引入但需间接守住。

| § 5.1 校验项 | PR-4 状态 | 落地证据 / 承接方 |
|---|---|---|
| 1. Schema 自洽（current_state 取值有定义 / C5） | ✅ | 本 PR 引入或修订的 `current_state` 写入（`Spec-Defining` / `Human-Review` / `RCA-LowConfidence` / `Fix-Designing` / **`RCA-Designing`**（v2.0 由 `RCA-InProgress` 收口））**全部**落在 `core/workflow-status-template.yaml` 头部注释列出的 v4.1 完整枚举集内；P6-A6 的 `RCA-InProgress → RCA-Designing` 收口直接对应 PR-4 review 2026-04-20 Finding 1 |
| 2. Schema 版本升级显式（schema_version=4） | ⏸ | PR-1 承接 |
| 3. Non-Bug 上下文字段已注册（D17） | ➖ | 本 PR 不涉及 Non-Bug；字段注册由 PR-1 完成；写入端由 PR-3 完成；编排器消费由 PR-2 完成 |
| 4. parse-error 计数器已注册（D18） | ⏸ | PR-1 注册 + PR-2 编排器实现 |
| 5. 配置键名注册（config-schema） | ➖ | 本 PR 在 P3 step 10 / P6 step 6 写 `output_rca_report` / `output_verification_report`，均已在 PR-1 `core/config-schema.yaml` `allowed_keys` 内 |
| 6. 标签白名单（含 `<task>` + 边界声明） | ➖ | PR-1 承接；本 PR **不引入任何新标签或新属性**（v2.0 已撤销 v1.0 子文档中 `<template-output mode="intermediate">` 引入 `mode` 属性的设计，与 `core/core-rules.xml` `<supported-tags>` 现有 `<template-output>` DSL 完全兼容；中间态/正态切换下沉到 PR-6 模板内由 `verification_failure_type` 判断；直接对应 PR-4 review 2026-04-20 Finding 3） |
| 7. 字段隔离（fanout_mode 不重命名 / fix_fanout_mode 新增） | ✅ | 变更点 P4-F1/F2（`fanout_mode → fix_fanout_mode` 替换 2 处）+ P3-H1（`rca_fanout_mode_snapshot` 写入 1 处） |
| 8. ❌ 不存在 `rca_fanout_mode` 裸字段（D7 反向校验） | ✅ | grep `phases/**/*.md` 中 `rca_fanout_mode\b` 命中 0 处（仅 `rca_fanout_mode_snapshot` 合法） |
| 9. ABORT 标记完整（phases 6 处 = P3 ×5 + P6 ×1） | ✅ | 变更点 P3-A1 ~ A5（5 处，含 v2.2 实施期增补 P3-A5）+ P6-A6（1 处）合计 **6 处**；与 v2.3 主文档微调"P3 ×5 + P6 ×1 = 6 处"统一口径完全对齐 |
| 10. step-pause 参数表完整（D16） | ⏸ | PR-1 协议层定义 + PR-2 编排器实现；本 PR 不引入 step-pause |
| 11. step-pause 调度作用域守门（D14） | ✅ | 本 PR diff 中 `<step-pause` 命中 0 处；不修改 phase 内现存 step-pause（P4 step 6 末尾 1 处由 PR-5 登记 allowlist） |
| 12. step-pause 输入协议完整 | ⏸ | PR-1 + PR-2 承接 |
| 13. 顶层镜像白名单受限（D15） | ⏸ | PR-1 + PR-2 承接 |
| 14. parse-error 生命周期闭合 | ⏸ | PR-2 承接 |
| 15. 持久化字段表纯净性（无 `current_phase_result`） | ✅ | 本 PR 引入的所有 ABORT 标记均为 `<action>设置 current_phase_result = ABORT</action>` 赋值动作（运行时变量），**无任何**写入 `workflow_status.current_phase_result` 的 `<action>更新 {workflow_status}：...</action>` 形式 |
| 16. 顶层镜像字段过渡标注 | ⏸ | PR-1 完成；本 PR 不涉及 |
| 17. allowlist 交付完整（D19） | ⏸ | PR-5 生成首版 + PR-8 CI 消费；本 PR 不修改任何 phase 内 step-pause，但需在 PR description 显式注明 P4 step 6 末尾 1 处 step-pause 待 PR-5 登记 |

**自检结论**（v2.0 升级）：PR-4 落地主文档 §5.1 中 phase 层可独立验收的 **5/17 项**（第 1（C5 收口）/ 7 / 8 / 9 / 15 项），全部为 ✅；其余 12 项中 7 项 ➖（不引入但间接守住，本 PR diff 不破坏）、5 项 ⏸（明确承接方）。**PR-4 是 §5.1 第 1（部分覆盖 P6-A6 的 C5 收口）/ 7 / 8 / 9 / 15 五项的唯一落地点（其中第 1 项的余量由 PR-1 + PR-2 共同保证）**，PR Review 必须重点核查这五项的 grep 证据；其中第 1 项是 v2.0 由 PR-4 review 2026-04-20 Finding 1 触发的 ➖ → ✅ 升级。

---

## 6. Reviewer 议题汇总（v2.0 收口后）

> 本节集中列出 PR-4 实施期发现的、需要 Reviewer 关注的议题；v2.0（基于 PR-4 review 2026-04-20）已把 4 项原可选议题中的 3 项 collapse 为"v2.0 直接落地"或"v2.0 直接关闭"，仅保留对**主文档微调（v2.3）**与**协议层显式登记（PR-1 hotfix 候选）**的非阻塞建议。

| # | 议题 | v2.0 状态 | 影响范围 / 落地证据 |
|---|---|---|---|
| 1 | 变更点 **P3-A5**（step 10 case "最终置信度 < 0.5" ABORT 标记）是否归 PR-4 直接落地 | ✅ **已 collapse 为"v2.0 直接落地"** — 不再作为可选议题（B1\* 主缺陷复发场景 / D1 协议硬性要求）；主文档 §3 PR-4 描述 / §1.1.1 B1\* 行 / §7.4 回滚条目 ABORT 计数同步更新为 **6 处 = P3 ×5 + P6 ×1**（详见 v2.3 主文档微调） | §5.2.1 用例 A 通过 / B1\* 修复完整性 |
| 2 | 变更点 **P3-H1**（写入位置）：主文档 §3 PR-4 写"step 7"，本 PR 修正为"step 10" | ✅ **已 collapse 为"v2.0 直接采纳"** — 主文档 §3 PR-4 描述同步更新为"step 10"（详见 v2.3 主文档微调）；step 7 字面口径会让非 deep-dive 路径下的 phase_history 永远空，C10 兼容性方案 A 失效 | C10 兼容性方案 A 完整覆盖 |
| 3 | 变更点 **P6-A6** v1.0 引入的 `<template-output mode="intermediate">` `mode` 属性 | ✅ **已关闭 — v2.0 选定方案 (b)** — 撤销 `mode` 属性引入；中间态/正态切换下沉到 `templates/verification-report.md` 模板内由 `verification_failure_type` 判断（PR-6 联动改动，不在本 PR 范围）。直接对应 PR-4 review 2026-04-20 Finding 3，不再依赖任何 PR-1 hotfix | DSL 标签属性合规（§5.1 第 6 项） |
| 4 | 变更点 **P6-A6** 内 case `root_cause_not_closed` 写 `current_state = RCA-InProgress` 与权威枚举集 `RCA-Designing` 漂移 | ✅ **已关闭 — v2.0 PR-4 内最小修复** — 直接替换 `RCA-InProgress` → `RCA-Designing`，与 `core/workflow-status-template.yaml` 头部注释枚举集对齐；编排器 step 4 路由按 `reroute_target_phase` 不读 `current_state` 字面值，无需新增 case。直接对应 PR-4 review 2026-04-20 Finding 1（Critical 等级） | C5 状态枚举权威源（§5.1 第 1 项） |
| 5 | C2 注入字段命名 `confidence_input` 与 `base_score` 是否需要在 PR-1 协议层显式登记 | 📝 **保留为非阻塞建议**：建议 PR-1 hotfix 把这两个字段名作为 wrapper 期望参数加入 `core/core-rules.xml` 注释；PR-4 与 PR-6 各自按 `agents/shared-{challenger,arbiter}-base.md` 输入契约（已逐字段对齐）调用方/校验方，不会因协议层未登记而失败 | 协议契约完整性 |
| 6 | 存量 v3 → v4 迁移脚本是否需增加 `RCA-InProgress → RCA-Designing` 字符串替换 | 📝 **保留为非阻塞建议**：建议主文档 §2.5 / PR-1 §2.5 hotfix 时同步登记此规则；存量会话若残留 `RCA-InProgress`，PR-8 CI §5.1 第 1 项会在持久化文件载入时 fail（不影响新会话） | 存量会话 backward-compat |

---

## 7. v2.3 主文档变更摘要（联动登记）

> 本节登记本子文档 v2.0 修订**必须联动**的主文档 `QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md` 微调点位，作为 v2.3 主文档版本号 bump 的 patch list。所有修改均**不影响 19 项决策（D1-D19）任何一条的语义**，仅同步 ABORT 计数、写入位置与议题状态。

| # | 主文档位置 | v2.2 原文要点 | v2.3 修订后要点 | 触发原因 |
|---|---|---|---|---|
| M1 | §1.1.1 表 B1\* 行 | "B1\* / Phase 早退 = ABORT 强协议（运行时变量赋值） / 0.7d / PR-1 + PR-3 + PR-4" | 同左，补脚注 "PR-4 落地 6 处 = P3 ×5 + P6 ×1（含 v2.2 实施期增补 P3-A5 step 10 RCA-LowConfidence stop）" | 修订 4（ABORT 计数统一） |
| M2 | §3 PR-4 描述 · 目标行 | "完成 B1\* 主体（P3 ×4 + P6 ×1 共 5 处显式 ABORT 标记）+ ..." | "完成 B1\* 主体（**P3 ×5 + P6 ×1 共 6 处**显式 ABORT 标记，含 v2.2 实施期增补 P3-A5 step 10 RCA-LowConfidence stop）+ ..." | 修订 4 |
| M3 | §3 PR-4 描述 · 覆盖修复条目行 | "覆盖修复条目：B1\*（P3/P6 显式 ABORT 5 处）..." | "覆盖修复条目：B1\*（P3/P6 显式 ABORT **6 处**）..." | 修订 4 |
| M4 | §3 PR-4 描述 · 涉及文件 / `phases/p3-root-cause.md` 第 1 项 | "4 处 `阶段结束，返回编排器`（L29 / L64 / L101 / L150）前各插入 `<action>设置 current_phase_result = ABORT</action>`" | "**5 处** ABORT 标记（L29 / L64 / L101 / L150 + step 10 case '最终置信度 < 0.5' 写入 RCA-LowConfidence 之后）前各插入 `<action>设置 current_phase_result = ABORT</action>`" | 修订 4 |
| M5 | §3 PR-4 描述 · 涉及文件 / `phases/p3-root-cause.md` 第 2-3 项 | "step 7 新增 `rca_fanout_mode_snapshot` ... 同 step 7 增加 `phase_history` append" | "**step 10 新增**（v2.0 修正：step 7 仅 deep-dive 路径执行，写入会丢失非 deep-dive 路径下的 phase_history） `rca_fanout_mode_snapshot` ... 同 step 10 增加 `phase_history` append" | 修订 4 / 议题 #2 |
| M6 | §3 PR-4 描述 · 涉及文件 / `phases/p3-root-cause.md` 第 4 项 | "调用 investigator/challenger/arbiter 的 subagent_prompt 拼接 `base_score`" | "调用 challenger 注入 `confidence_input`、调用 arbiter 注入 `base_score`（**角色驱动**，与 `agents/shared-{challenger,arbiter}-base.md` 输入契约对齐；investigator/fix-proposer 不强制注入）" | 修订 1 / PR-4 review Finding 2 |
| M7 | §3 PR-4 描述 · 涉及文件 / `phases/p4-fix-design.md` 第 2 项 | "调用 fix-proposer/challenger/arbiter 的 subagent_prompt 拼接 `confidence_input`" | "调用 challenger 注入 `confidence_input`、调用 arbiter 注入 `base_score`（**角色驱动**，与 P3 共享同一映射规则）" | 修订 1 |
| M8 | §3 PR-4 描述 · 涉及文件 / `phases/p6-verification.md` 第 1 项 | "1 处 `阶段结束，返回编排器`（L83）前插入 `<action>设置 current_phase_result = ABORT</action>`" | 同左，**追加** "并把 case `root_cause_not_closed` 写入的 `current_state = RCA-InProgress` 收口为 `RCA-Designing`（C5 状态枚举权威源对齐）" | 修订 2 / PR-4 review Finding 1 |
| M9 | §3 PR-4 描述 · 涉及文件 / `phases/p6-verification.md` 第 2 项 | "失败分支必先调用 `<template-output ...>` 生成'中间态'报告再回流（与 PR-6 模板侧配合）" | 同左，**追加** "本 PR 调用方仅用现有 `file` / `template` 属性；中间态/正态切换下沉到 PR-6 模板内由 `verification_failure_type` 判断（v1.0 子文档曾设计 `mode='intermediate'` 属性，已撤销）" | 修订 3 / PR-4 review Finding 3 |
| M10 | §3 PR-4 描述 · 评审重点 | "5 处 ABORT 标记位置完整 ..." | "**6 处** ABORT 标记位置完整（P3 ×5 + P6 ×1）；P6-A6 内 `RCA-InProgress → RCA-Designing` 收口正确性；C2 角色驱动注入矩阵（challenger → confidence_input；arbiter → base_score）；其余不变" | 修订 1 / 修订 2 / 修订 4 |
| M11 | §7.4 PR-4 回滚 · revert 后状态 | "P3/P6 的 ABORT 标记 5 处全部消失 → B1\* 主链路根因复发；`fix_fanout_mode` 字段消失 → C10 字段污染复发；P6 失败分支不再产出 verification-report.md；`phase_history` / `rca_fanout_mode_snapshot` 不再被 P3 写入" | "P3/P6 的 ABORT 标记 **6 处**全部消失（P3 ×5 + P6 ×1，含 v2.2 实施期增补 P3-A5）→ B1\* 主链路根因复发；`fix_fanout_mode` 字段消失 → C10 字段污染复发；P6-A6 的 `current_state = RCA-Designing` 同时回滚为 `RCA-InProgress` → C5 权威源漂移复发；P6 失败分支不再产出 verification-report.md；`phase_history` / `rca_fanout_mode_snapshot` 不再被 P3 写入" | 修订 2 / 修订 4 |

> **登记建议**：v2.3 主文档微调请按上述 11 项 patch list 一次性提交（建议作为 PR-4 子文档 v2.0 的同 commit / 同 PR description 内联动改动），避免出现"子文档 v2.0 与主文档 v2.2 ABORT 计数不一致"的瞬时漂移。

---

## Changelog

| 版本 | 日期 | 变更 |
|---|---|---|
| v2.0 | 2026-04-20 | 基于 `pr4-phase-abort-fanout-isolation-REVIEW-2026-04-20.md` 4 项裁定（1 Critical + 3 Major）整体修订：① **修订 1（C2 字段命名矩阵反转）**：从 v1.0 的"场景驱动"（RCA → base_score / FIX → confidence_input）改为 v2.0 的"**角色驱动**"（challenger → `confidence_input` / arbiter → `base_score`），与 `agents/shared-{challenger,arbiter}-base.md` 输入契约**逐字段对齐**；具体改动 P3-C1/C2 → `confidence_input`、P4-C6 → `base_score`，§3.1 第 6 项 / §3.2 回归用例 2 同步更新角色驱动 grep 模式 + 反向断言；新增 §2 概述 C2 注入矩阵表。② **修订 2（C5 状态枚举权威源对齐）**：P6-A6 内 case `root_cause_not_closed` 的 `current_state = RCA-InProgress` 收口为 `RCA-Designing`，与 `core/workflow-status-template.yaml` 头部注释 v4.1 完整枚举集对齐；§5 自检表第 1 项 ➖ → ✅；议题 #4 关闭。③ **修订 3（DSL 标签属性合规）**：撤销 v1.0 引入的 `<template-output mode="intermediate">` `mode` 属性，下沉到 PR-6 模板内由 `verification_failure_type` 判断；不再依赖任何 PR-1 hotfix；§5 自检表第 6 项 ⏸ → ➖；议题 #3 关闭（选定方案 b）。④ **修订 4（ABORT 计数统一）**：子文档 §1 / §2 / §2.1.5 / §3.1 / §4 / §5 自检第 9 项全部统一为 "P3 ×5 + P6 ×1 = 6 处"；议题 #1（P3-A5 是否归 PR-4）已 collapse 为 v2.0 直接落地、议题 #2（H1 写入位置 step 7→step 10）已 collapse 为 v2.0 直接采纳，二者不再作为可选议题。⑤ 新增 §7 v2.3 主文档变更摘要（11 项 patch list M1-M11，覆盖主文档 §1.1.1 / §3 PR-4 / §7.4），登记联动登记必要性。⑥ §5.2.1 用例 A 期望路径 / §5.2.6 用例 F 描述无变化（修订 1-4 均不影响动态用例期望终态）。 |
| v1.0 | 2026-04-20 | 自主文档 v2.2 §3 PR-4 描述完整展开为子文档；引入 11 个变更点（P3-A1~A5 + P3-H1 + P3-C1/C2/C3 + P4-F1/F2 + P4-C4/C5/C6 + P6-A6/T1）+ Reviewer 议题汇总（5 项）+ PR-level DoD 子集 + 回滚动作 + §5.1 自检表；显式增补 v2.2 实施期发现的 P3-A5（step 10 RCA-LowConfidence stop ABORT，B1\* 主链路硬性要求）；修正主文档 §3 PR-4 描述"step 7"为"step 10"（C10 写入位置语义修复）；引入 `<template-output mode="intermediate">` 属性约定（依赖 PR-1 hotfix，登记为 Reviewer 议题 #3） |
