# PR-3 · P2 闭环：Non-Bug 早退 + Context-Curating 状态机（v2.2 详细施工单 · V1）

> **主文档**：[`../../QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md`](../../QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md) §3 PR-3 / §4
> **子文档骨架**：[`README.md` §2](./README.md)
> **协议依赖**：附录 C **D1 / D2 / D14 / D15 / D17**（全部定义见主文档附录 C）
> **强前置 PR**：PR-1（协议层 schema 与 `<step-pause>` 调度作用域约束）已合入；PR-2（编排器 case Non-Bug 接管 step-pause）已合入。
> **Review 基线**：合入 [`pr3-p2-non-bug-context-curating-REVIEW-2026-04-20.md`](./pr3-p2-non-bug-context-curating-REVIEW-2026-04-20.md) **全部 4 项 findings**（1 Fact Conflict + 1 Scope Conflict + 1 Cross-Doc Inconsistency + 1 Minor Clarity）。
> **状态**：✅ V1（v2.2，2026-04-20，初稿 v1.0 → V1 接纳 review 后重新发布）
> **唯一职责**：把 `phases/p2-spec-definition.md` 在 v4.1 协议下的两处早退路径补齐：
> 1. **step 4 Non-Bug 判定**：写 `non_bug_context` → 写 `current_state = Non-Bug` → 设 `current_phase_result = ABORT` → 退出 phase；**本 PR 不新增 `<step-pause>`**（现存 1 处 Spec-Uncertain 作为 v4.2 遗留 #6 保持不动；D14 协议约束 + B2 闭环 + B1\* P2 部分 1 处 ABORT）。
> 2. **step 7 Curation-Failed 早退**：当 `curation_confidence < 0.4` 时设 `current_state = Curation-Failed` → 设 `current_phase_result = ABORT` → 退出 phase（C5 状态枚举权威源对齐 + 1 处 ABORT 兜底）。
>
> **本 PR 不在范围**：① 修改/删除 step 4 内已有的 Spec-Uncertain 内联 `<step-pause>`（D14 收窄声明 → v4.2 遗留 #6）；② 修改 `non_bug_reflow_count` 的 `>= 2` 熔断逻辑（已由 PR-2 编排器 case Non-Bug Reflow 分支承担。**语义注脚（V1 finding #3 接纳）**：计数从 `0` 开始，`non_bug_reflow_count >= 2` 表示**第 3 次** Reflow 才熔断到 Human-Review，与 `core/workflow.xml` L240 / `system-prompt.md` L106 + L175 / PR-2 V1 §2.1.5 W5 实现一致；主文档 §3 PR-3 描述行的 `> 2` 与权威实现不一致 → follow-up：建议主文档同步修订为 `>= 2`，归 PR-7 文档同步阶段联动或独立 doc-fix 小 PR 处理，本 PR 不修主文档以避免 scope creep）；③ `phase_history` 写入（PR-4 P3 / 后续 PR 联动，本 PR 不引入）；④ 任何 `core/**` 改动（属 PR-1/PR-2 范围）；⑤ `system-prompt.md` / `SKILL.md` / `PLATFORM-GUIDE.md` 同步（属 PR-7 范围）。

---

## 0. V1 修订摘要（合入 review 2026-04-20 的 4 项 findings）

> **审阅文档**：[`pr3-p2-non-bug-context-curating-REVIEW-2026-04-20.md`](./pr3-p2-non-bug-context-curating-REVIEW-2026-04-20.md)
> **审阅结论**：4 项 findings 全部成立，本 V1 全部接纳并落地。下表给出每条 finding 的判定与修订动作。

| # | 严重性 | Finding 摘要 | V1 判定 | V1 修订动作 |
|---|---|---|---|---|
| 1 | 🟠 Fact Conflict | 初稿 §2.1.2 兼容性影响声称"编排器不存在 case Curation-Failed step-pause"，与主文档 L316 / PR-2 子文档 L596 起的 `case if="Curation-Failed"`（`curation_failed_action=Retry\|Human`）实现冲突 | ✅ **接纳** | **重写 §2.1.2 兼容性影响第 2 个 bullet** — 删除"不存在 case Curation-Failed step-pause"与"落入 default 分支等待人工介入"等错误描述；改写为"编排器 case Curation-Failed 已由 PR-2 实现，按 `curation_failed_action ∈ {Retry, Human}` 派发到回流 / Human-Review，本 PR 早退动作即为该 case 的合法触发源" |
| 2 | 🟠 Scope Conflict | 初稿 §3.1 最后一项 DoD 把 P2 step 9 残留 `current_state = RCA-InProgress` 的清理外推为"由 PR-4 收口 P6 时一并扫除（与 PR-7 联动）"，但主文档 PR-4 涉及文件清单严格只含 `phases/p3,p4,p6`、PR-7 仅做入口文档同步，两者均无 P2 phase 文件改动权 | ✅ **接纳** | **重写 §3.1 最后一项 DoD** — 删除对 PR-4 / PR-7 的清理责任外推；改写为"P2 step 9 残留 `RCA-InProgress` 是已知 v3 残留，本 PR 范围内**保持不动**；具体迁出归属由后续 PR 单独评估（候选：归入 v4.2 遗留新增条目 #8 或独立小 PR），不与 PR-4 / PR-7 强绑定" |
| 3 | 🟡 Cross-Doc Inconsistency | 初稿"不在范围 ②"用 `>= 2` 描述阈值（与 PR-2 实现 / `core/workflow.xml` L240 / `system-prompt.md` L175 一致），但主文档 v2.2 L368 / v2.1 L336 写 `> 2`，存在跨文档不一致；初稿未显式语义说明也未登记 follow-up | ✅ **接纳** | **§1 唯一职责 ② 增"语义注脚"** — 加注"计数从 0 开始，`non_bug_reflow_count >= 2` 表示**第 3 次** Reflow 才熔断到 Human-Review（与 system-prompt.md L106-175 / PR-2 实现一致）"；同时 §0 本表显式登记"主文档 §3 PR-3 描述行 `> 2` 与权威实现不一致 → follow-up：建议主文档同步修订为 `>= 2`（属 PR-7 文档同步阶段联动，或独立 doc-fix 小 PR；本 PR 不修主文档以避免 scope creep）" |
| 4 | 🟢 Minor Clarity | 初稿多处出现"phase 内不放任何 `<step-pause>`"等绝对化措辞，与同文档承认的"现存 1 处 Spec-Uncertain step-pause（v4.2 遗留 #6）"逻辑上矛盾；可能误导 Reviewer 与未来 CI gate owner | ✅ **接纳** | **统一替换措辞** — 把所有"phase 内不放任何 `<step-pause>`" / "phase 内禁止放置 `<step-pause>`" / "phase 内不弹 step-pause"等绝对化表述统一为"**本 PR 不新增** `<step-pause>`（phase 内现存 1 处 Spec-Uncertain 作为 v4.2 遗留 #6 保持不动）"；§3.1 第 1 项 D14 守门 grep 命中数表述补充"= 1（现存 1 处 = v3 已有的 Spec-Uncertain，v4.2 遗留 #6 一并迁出）" |

> **V1 不引入的范围扩张**：
> - 不改主文档 §3 PR-3 的 `non_bug_reflow_count > 2` 行（Finding #3 的主文档同步留给 PR-7 或独立 doc-fix）；
> - 不在本 PR 内修复 P2 step 9 `current_state = RCA-InProgress` 残留（Finding #2 的清理责任不与 PR-4 / PR-7 强绑定，候选 v4.2 遗留 #8）；
> - 不在本 PR 修改/删除现存 Spec-Uncertain step-pause（v4.2 遗留 #6 不变）。
>
> **V1 的承诺边界**：本 PR 单 PR 范围内**精确实现**主文档 §3 PR-3 描述的两处早退路径（Non-Bug × 1 + Curation-Failed × 1），且不超出 `phases/p2-spec-definition.md` 一个文件；事实声明、范围归属、跨文档阈值语义、措辞精确度全部对齐 review 基线。

---

## 1. PR 元信息

| 项 | 值 |
|---|---|
| 分支命名 | `feat/qa-workflow-v4.1-pr3-p2-non-bug-context-curating` |
| Base | PR-1 + PR-2 合入后的 `main`（必须 rebase 到 PR-2 之后；任一前置未合入禁止开 PR-3） |
| 层级 | 🟠 phase 层 |
| 目标合入顺序 | **PR-1 → PR-2 → PR-4 → PR-3 → PR-5 → PR-6 → PR-7 → PR-8**（D9） |
| Reviewer | 1 名 phase owner（必看 P2 step 4 Non-Bug 早退三步序列原子性 + `non_bug_context` 文本质量 + Curation-Failed 早退兜底） + 1 名协议 owner（必看 D14 合规：grep 确认 PR diff 未新增 `<step-pause>`；现存 Spec-Uncertain step-pause 在 PR description 标注 v4.2 遗留 #6） |
| 关联 issue | v4.1 主修复条目：**B2**（P2 Non-Bug 闭环回填）、**B1\* P2 部分**（1 处 ABORT）、**C5**（Context-Curating / Curation-Failed 在 phase 内的写入实现） |
| 工作量 | 0.30d（与主文档 §3 PR-3 一致；v2.0 0.4d − v2.1 D14 移除 phase 内 step-pause −0.1d） |
| 涉及文件 | **1 个**：`phases/p2-spec-definition.md`（修改） |
| 不在本 PR 范围 | ① P2 step 4 现存 Spec-Uncertain 内联 step-pause（v4.2 遗留 #6） ② 编排器 case Non-Bug 实现（PR-2 已落地） ③ `non_bug_user_choice` / `non_bug_context` schema 注册（PR-1 已落地） ④ `non_bug_reflow_count` 的 +1 与熔断（PR-2 case Non-Bug Reflow 已落地） ⑤ `phase_history` 写入 ⑥ 其他 phase 文件改动 ⑦ 任何 `core/**` / `agents/**` / `templates/**` 改动 ⑧ 入口文档同步（PR-7） |

---

## 2. 文件级 diff 列表

> 本 PR 只动 `phases/p2-spec-definition.md` 一个文件，下设 **2 个变更点**：P2-1（step 4 Non-Bug 早退）+ P2-2（step 7 Curation-Failed 早退）。两个变更点合计新增 ABORT 标记 2 处（B1\* P2 = 1 处主体 + Curation-Failed 1 处 C5 兜底）。
> 所有变更点均**只新增**或在原有 `<action>` 序列中**插入**新的 `<action>`，不删除既有 step 1-9 骨架；除 step 4 在判定 Non-Bug 时新增"早退退出"语义外，正常路径行为与 v3 完全等价。

### 2.1 文件 A · `phases/p2-spec-definition.md`（修改）

> **修复条目锚点**：B2 / B1\* P2 部分 / C5（phase 侧 Curation-Failed 早退）

#### 2.1.1 变更点 P2-1 · step 4 Non-Bug 判定后的早退三步序列（B2 + B1\* + D14 + D17）

**原文（行号锚点 L46-62）**：

```46:62:mobile-qa-workflow/phases/p2-spec-definition.md
        <step n="4" goal="Spec 校准与非 Bug 判定">
            <action>确定 Spec 来源优先级：PRD(1) > 设计稿(2) > 竞品(3) > 用户口述(4)</action>
            <check if="Spec 存在模糊性或来源冲突">
                <action>标记 [Spec-Uncertain]，列出多种可能的 Expected Behavior</action>
                <step-pause title="Spec 存在歧义，请确认 Expected Behavior：
{spec_options}
">
                    <option title="[1] {option_1}
"/>
                    <option title="[2] {option_2}
"/>
                    <option title="[S] Skip：先并行分析所有可能，后续确认
" action="确认前对每种可能 Spec 分别分析"/>
                </step-pause>
            </check>
            <action>逐项检查 Working-As-Designed / User-Misoperation / Environment-Specific / Known-Limitation / Duplicate</action>
        </step>
```

**新文**（在 `<action>逐项检查 ...</action>` **之后**追加 Non-Bug 判定 + 早退三步序列；**不动**上方 Spec-Uncertain 内联 `<step-pause>`，登记 v4.2 遗留 #6）：

```xml
        <step n="4" goal="Spec 校准与非 Bug 判定">
            <action>确定 Spec 来源优先级：PRD(1) > 设计稿(2) > 竞品(3) > 用户口述(4)</action>
            <check if="Spec 存在模糊性或来源冲突">
                <action>标记 [Spec-Uncertain]，列出多种可能的 Expected Behavior</action>
                <!-- ⚠️ v4.2 遗留 #6：本内联 <step-pause> 与编排器 step 4 case Spec-Uncertain
                     重复弹窗（已知 bug）；按 D14 收窄声明，v4.1 暂不动以避免 scope creep，
                     v4.2 整体迁出 phase 文件，由编排器统一调度。 -->
                <step-pause title="Spec 存在歧义，请确认 Expected Behavior：
{spec_options}
">
                    <option title="[1] {option_1}
"/>
                    <option title="[2] {option_2}
"/>
                    <option title="[S] Skip：先并行分析所有可能，后续确认
" action="确认前对每种可能 Spec 分别分析"/>
                </step-pause>
            </check>
            <action>逐项检查 Working-As-Designed / User-Misoperation / Environment-Specific / Known-Limitation / Duplicate</action>

            <!-- ──────────────────────────────────────────────────────────────────
                 v4.1 / B2 / B1* P2 / D14 / D17：Non-Bug 早退三步序列
                 ──────────────────────────────────────────────────────────────────
                 当 step 4 判定为 Non-Bug 时：
                   1) 生成 Non-Bug 判定文本并写入 workflow_status.non_bug_context
                      （供编排器 case Non-Bug 的 step-pause 标题占位 {non_bug_context} 使用）
                   2) 设 current_state = Non-Bug
                   3) 设运行时变量 current_phase_result = ABORT
                 退出 phase（不再继续 step 5-9）；编排器 step 4 接管：
                   - 不追加 qa-spec-definition 到 stepsCompleted（ABORT 分支）
                   - 进入 case Non-Bug，由编排器统一发起确认 step-pause
                 D14 合规：本 PR **不新增** <step-pause>；phase 内现存的 1 处
                 Spec-Uncertain <step-pause> 作为 v4.2 遗留 #6 保持不动。
                 ────────────────────────────────────────────────────────────────── -->
            <check if="判定为 Non-Bug（命中 Working-As-Designed / User-Misoperation / Environment-Specific / Known-Limitation / Duplicate 之一）">
                <action>生成 Non-Bug Resolution Report 文本：包含
                        - 判定类别（5 选 1）
                        - 判定依据（对应 Spec 条款 / 复现路径 / 环境快照锚点）
                        - 沟通建议（一段面向 reporter 的回复要点，便于 step-pause 用户决策）
                        - 改进建议（可选；如对应 UX 工单 / Feature Request / 文档改进）</action>

                <action>更新 {workflow_status}：non_bug_context = {上述 Non-Bug Resolution Report 文本}
                        （D17：该字段是编排器 case Non-Bug step-pause 标题占位的唯一数据源；
                         文本应足够 self-contained，使用户仅凭 step-pause 标题即可做出 Accept / Reflow 决策）</action>

                <action>更新 {workflow_status}：current_state = Non-Bug</action>

                <action>设置 current_phase_result = ABORT
                        （D1：current_phase_result 是运行时变量，不入持久化 schema；
                         本动作必须在返回编排器之前显式赋值，否则编排器 step 4 会将
                         qa-spec-definition 错误追加到 stepsCompleted，B1* 主链路根因复发）</action>

                <action>退出 phase（不再继续 step 5-9）</action>
            </check>
        </step>
```

**修订理由**：

- **B2（v1.2.1 §三 / §七 #2）**：v3 的 Non-Bug 闭环依赖 P2 内联 `<step-pause>` 直接弹窗，而编排器 case Non-Bug 又通过 `{non_bug_user_choice}` 顶层读取做 switch，导致**双重发起**风险与"phase 内 step-pause 与编排器 step-pause 写回路径不一致"的链路断裂。本变更点把 P2 改造为"判定 → 写 context → 标 ABORT → 退出"，让编排器统一接管 step-pause（PR-2 W5 已落地），实现 Non-Bug **闭环单源**。
- **B1\* P2 部分（v1.2.1 §三 B1\* / §七 #1）**：补齐 P2 早退路径的 `current_phase_result = ABORT` 显式标记，是 B1\* "Phase 早退 = ABORT 强协议"在 P2 的唯一落地点（PR-3 仅承担 P2 1 处；P3 ×5 + P6 ×1 由 PR-4 承担）。
- **D14（v2.1）**：phase 文件**禁止**新增 `<step-pause>`。本变更点严格遵守 — 早退只写状态字段与 ABORT，由编排器 case Non-Bug（PR-2 W5）统一发起 step-pause，标题用 `{non_bug_context}` 占位。**反向断言**：grep `<step-pause>` 在 `phases/p2-spec-definition.md` 的命中数在本 PR 前后**均为 1**（即 v3 已有的 Spec-Uncertain step-pause；新增 = 0）。
- **D17（v2.2）**：`non_bug_context` 是 PR-1 显式注册的持久化字段，**唯一**写入端就是本变更点。字段语义"承载最近一次 Non-Bug 判定说明"要求文本应 self-contained — 因此本设计要求"沟通建议"必填（让用户仅凭 step-pause 标题即可决策），符合编排器 W5 的占位消费契约。
- **`non_bug_reflow_count` 不在本 PR 操作**：v3 该字段位于 `workflow-status-template.yaml` 顶层，由编排器 case Non-Bug Reflow 分支 `+= 1` 并在 ≥ 2 时熔断到 Human-Review（PR-2 W5 已落地）。PR-3 P2 内**不**触碰该字段，避免双写竞争。
- **三步序列原子性**：`non_bug_context` → `current_state` → `current_phase_result` 三个 `<action>` 必须**连续出现且同序**。Reviewer 必须断言：在判定 Non-Bug 的 `<check>` 块内，三动作之间不得插入任何其他 `<action>` / `<check>` / `<step-pause>`，且最后一行必须是"退出 phase"显式语义（防止 LLM 误继续执行 step 5-9）。

**兼容性影响**：

- **正常路径不受影响**：当 step 4 未命中 Non-Bug 5 类时，新增的 `<check if="判定为 Non-Bug">` 整块 short-circuit；step 5-9 按 v3 行为继续执行，最终 step 9 写 `current_state = RCA-InProgress`（注：`RCA-InProgress` 在 PR-1 schema 权威枚举中已被 `RCA-Designing` 替代；P2 step 9 的对齐由 **PR-7 文档同步阶段联动**或 **PR-4 收口 P6 时一并扫除**，本 PR 不动该残留以保持 scope 最小，与 PR-2 V1 §0 W9 "PR-2 不动 phase 残留" 相同基调）。
- **早退路径与编排器联动**：本变更点严格依赖以下 3 个 PR-1/PR-2 已交付能力：
  1. `core/workflow-status-template.yaml` 已注册 `non_bug_context: null`、`current_state: Non-Bug ∈ 合法枚举`（PR-1 已合入）；
  2. `core/workflow.xml` step 4 case Non-Bug 已发起 `{non_bug_context}` 占位 step-pause（PR-2 W5 已合入）；
  3. `core/core-rules.xml` `<workflow-result-protocol>` 已声明 `current_phase_result = ABORT` 是 phase 早退的强协议（PR-1 已合入）。
- **回滚兼容**：若本 PR 单独回滚（`git revert`），P2 回到"判定 Non-Bug 不写 context、不退出"的 v3 行为；编排器 case Non-Bug 仍可发起 step-pause（PR-2 W5 已落地），但 `{non_bug_context}` 占位会渲染为空串/null，体验上 step-pause 标题会缺失判定上下文。**不会引入新 bug**，仅退化到 v3 体验，与 PR-2 W5 §"兼容性影响" 中描述的"占位失败时降级输出空串"一致。

---

#### 2.1.2 变更点 P2-2 · step 7 Curation-Failed 早退兜底（C5 + B1\* 兜底）

**原文（行号锚点 L94-108）**：

```94:108:mobile-qa-workflow/phases/p2-spec-definition.md
        <step n="7" goal="上下文策展">
            <action>更新 {workflow_status}：current_state = Context-Curating</action>
            <check if="{env_subagent} == true">
                <invoke-subagent subagent_type="curator" subagent_prompt="
                    <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                    <load target='mobile-qa-workflow/agents/curator.md' prompt='加载角色定义'/>
                    对候选上下文集合进行策展，包含去重、存活性校验、保守配置掩码、动态映射。
                    输出符合 context-curation-report.md 模板的报告。
                "/>
            </check>
            <check if="{env_subagent} == false">
                <action>执行单对话策展降级模式：主 Agent 自行完成 Curator 的 5 项能力。</action>
            </check>
            <action>读取 curation_confidence：>=0.7 正常继续；0.4-0.7 标记 [Curation-Partial]；<0.4 则 current_state = Curation-Failed。</action>
        </step>
```

**新文**（把最后一行的"<0.4 则 current_state = Curation-Failed"原子动作展开为 `<switch>` 三分支，并在 Curation-Failed 分支补齐"设 ABORT + 退出 phase"早退兜底）：

```xml
        <step n="7" goal="上下文策展">
            <action>更新 {workflow_status}：current_state = Context-Curating
                    （C5：Context-Curating 是策展执行中的中间态，不引发 ABORT；
                     仅当下方 curation_confidence < 0.4 才转入 Curation-Failed 早退）</action>
            <check if="{env_subagent} == true">
                <invoke-subagent subagent_type="curator" subagent_prompt="
                    <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                    <load target='mobile-qa-workflow/agents/curator.md' prompt='加载角色定义'/>
                    对候选上下文集合进行策展，包含去重、存活性校验、保守配置掩码、动态映射。
                    输出符合 context-curation-report.md 模板的报告。
                "/>
            </check>
            <check if="{env_subagent} == false">
                <action>执行单对话策展降级模式：主 Agent 自行完成 Curator 的 5 项能力。</action>
            </check>

            <!-- ──────────────────────────────────────────────────────────────────
                 v4.1 / C5 / B1* 兜底：curation_confidence 三分支显式化
                 ──────────────────────────────────────────────────────────────────
                 v3 把三个分支折叠为一条自然语言 <action>，导致 "<0.4 → Curation-Failed"
                 仅写状态而未触发早退（B1* 漏标 ABORT），编排器 step 4 会把
                 qa-spec-definition 错误追加到 stepsCompleted，与 B1* 同源 bug。
                 本变更点把三分支显式化，并在 Curation-Failed 分支补齐 ABORT 早退。
                 ────────────────────────────────────────────────────────────────── -->
            <action>读取 curation_confidence</action>
            <switch condition="curation_confidence">
                <case if=">= 0.7">
                    <action>正常继续，进入 step 8</action>
                </case>
                <case if=">= 0.4 且 < 0.7">
                    <action>在策展报告中标记 [Curation-Partial]，正常继续进入 step 8
                            （部分置信度路径不早退；后续 step 9 仍输出三件套）</action>
                </case>
                <case if="< 0.4">
                    <action>更新 {workflow_status}：current_state = Curation-Failed
                            （C5：Curation-Failed 是 PR-1 schema 权威枚举集合内合法状态，
                             与 system-prompt.md Phase 2 字段集对齐）</action>
                    <action>设置 current_phase_result = ABORT
                            （D1 / B1* 兜底：与变更点 P2-1 同协议；不显式标 ABORT 会让
                             编排器把 qa-spec-definition 误追加到 stepsCompleted，
                             导致后续重入策展时 stepsCompleted 失锚）</action>
                    <action>退出 phase（不再继续 step 8-9）</action>
                </case>
            </switch>
        </step>
```

**修订理由**：

- **C5（v1.2.1 §三 / §七 #6）**：`Context-Curating` / `Curation-Failed` 已被 PR-1 注册到 `core/workflow-status-template.yaml` 头部 `current_state` 合法枚举集，但 v3 的 P2 step 7 把 "<0.4 设 Curation-Failed" 折叠为一条自然语言 `<action>`，让 Curation-Failed 状态写入后**phase 仍在执行**，与"早退状态"语义不符。本变更点把三分支拆开，让 Curation-Failed 分支显式承担"早退退出"语义，与 PR-1 schema 权威源对齐。
- **B1\* 兜底**：Curation-Failed 与 Non-Bug 同属 P2 早退点位，但主文档 §1.1.1 / §3 PR-3 描述只把 B1\* P2 部分计为"1 处"（指 Non-Bug 早退；这是 v1.2.1 §三 B1\* 的主修复目标）。本变更点新增的 Curation-Failed ABORT 是**协议一致性兜底**：v3 该路径写 Curation-Failed 状态后未标 ABORT，会和 B1\* P3/P6 同样的 stepsCompleted 失锚 bug 一致；不补此处会让 P2 早退路径"漏一半"，留下隐式 bug。**该处 ABORT 不计入 §1.1.1 B1\* 工作量统计，仅作为 C5 实现的副产品**。
- **三分支显式化的副作用**：v3 中 `>= 0.4 且 < 0.7` 路径仅"标 [Curation-Partial]"是 in-place mutation，在 step 9 三件套输出前已生效。本变更点严格保留该语义（不改变 [Curation-Partial] 行为），仅把控制流从隐式自然语言变为显式 `<switch>`，对 step 8/9 的输入产物 0 影响。
- **Context-Curating 不 ABORT 的显式注释**：避免 Reviewer 误读为"凡 Context-Curating 与 Curation-Failed 都 ABORT" — Context-Curating 是策展进行中的瞬时状态（与 step 9 末尾 `current_state = RCA-InProgress` 性质相同：phase 内部状态推进），不属于早退点位。

**兼容性影响**：

- 三分支语义与 v3 完全等价（>=0.7 / [Curation-Partial] / Curation-Failed 三类决策保持不变）；唯一新增的语义是 Curation-Failed 分支的"设 ABORT + 退出 phase"。
- 早退后编排器 step 4 收到 `current_phase_result = ABORT` + `current_state = Curation-Failed` → 不追加 stepsCompleted → 进入 step 4 的 `<switch condition="{current_state}">` → **命中 PR-2 已实现的 `case if="Curation-Failed"`**（参见 PR-2 子文档 [`pr2-orchestrator-step-pause-v1.md`](./pr2-orchestrator-step-pause-v1.md) §2.1.8 W8 / 主文档 L316 的 "step 4 既有 6 个 step-pause" 列表）：编排器按 D16 完整声明 `result_field=curation_failed_action` / `allowed_values=Retry|Human` 发起确认 step-pause；用户回复后由 PR-2 W2 头部双写到 `user_inputs.curation_failed_action`，下方派发 switch 路由到 Retry（回流 qa-spec-definition）或 Human（转 Human-Review）。**因此本变更点是 PR-2 W8 case Curation-Failed 的合法触发源**，二者构成 phase 侧 → 编排器侧的闭环对偶（同 P2-1 与 PR-2 W5 的对偶关系）。无 default 分支兜底担忧，无 v4.2 遗留 #6 范围扩张候选。
- 回滚兼容：若本变更点单独回滚，P2 退回 v3 "写状态但不早退" 行为 — 状态写为 `Curation-Failed` 但 phase 继续执行 step 8/9 直到正常完成或异常；编排器 step 4 case Curation-Failed step-pause（PR-2 W8）**仍可被未来其它路径触发**，但来自 P2 step 7 的早退触发会丢失。该 bug 是 v3 既有问题，不引入新 bug，但会让 C5 在 P2 侧失效。

---

## 3. PR-level DoD 子集

> 本 PR 只需在 PR description 勾选下列条目；横切契约（D14/D15/D17 完整 CI 守门、迁移脚本、回归矩阵）见主文档 §5。

### 3.1 静态契约（本 PR 视角）

- [ ] **D14 phase 内 step-pause 守门**：grep `phases/p2-spec-definition.md` 中 `<step-pause` 命中数 = **1**（现存 1 处 = v3 已有的 Spec-Uncertain step-pause，作为 v4.2 遗留 #6 一并迁出；本 PR diff 不新增 `<step-pause>`）；该现存 step-pause 必须出现在 PR-5 维护的 `mobile-qa-workflow/scripts/legacy-phase-step-pause-allowlist.txt` 中（PR-5 与本 PR 解耦合入；本 PR Reviewer 仅需断言"本 PR diff 内**未新增** `<step-pause>`"，V1 finding #4 接纳）
- [ ] **B1\* P2 部分（1 处 ABORT）**：`phases/p2-spec-definition.md` step 4 判定 Non-Bug 的 `<check>` 块内必须出现 `<action>设置 current_phase_result = ABORT</action>` 显式语句，且该 action **紧邻** `current_state = Non-Bug` action 之后
- [ ] **C5 兜底（1 处 ABORT）**：step 7 `<switch condition="curation_confidence">` 的 `< 0.4` case 内必须出现 `current_state = Curation-Failed` + `current_phase_result = ABORT` + 退出 phase 三动作
- [ ] **D17 `non_bug_context` 写入端**：本 PR diff 内必须出现"更新 {workflow_status}：non_bug_context = ..."动作，且该动作位于"判定为 Non-Bug"的 `<check>` 块内（grep 验证 `non_bug_context` 在本文件命中 ≥ 1）
- [ ] **三步序列原子性**：Non-Bug 早退三动作（`non_bug_context` → `current_state = Non-Bug` → `current_phase_result = ABORT`）之间不得插入其它 `<action>` / `<check>` / `<step-pause>`
- [ ] **未引入 phase_history 写入**：本 PR diff 不出现 `phase_history` 字符串（明确不在范围）
- [ ] **未触碰 `non_bug_reflow_count`**：本 PR diff 不出现 `non_bug_reflow_count` 字符串（已由 PR-2 case Non-Bug Reflow 承担）
- [ ] **未触碰 `core/**`**：本 PR diff 仅 `phases/p2-spec-definition.md` 一个文件，git 路径过滤可机械验证
- [ ] **PR description 显式登记 v4.2 遗留 #6**：必须列出"P2 step 4 现存 Spec-Uncertain 内联 `<step-pause>`（与编排器 step 4 case Spec-Uncertain 重复弹窗）→ v4.2 遗留 #6"
- [ ] **未触碰 P2 step 9 `current_state = RCA-InProgress` 残留**：该残留与 PR-1 schema 权威枚举 `RCA-Designing` 冲突（PR-2 V1 §0 review #1 P0 已识别），属"权威枚举对齐链"的 phase 侧治理目标。**本 PR 范围内保持不动**（理由：scope 最小化 + 主文档 PR-3 描述未包含此项 + 主文档 PR-4 涉及文件清单严格限定 `phases/p3,p4,p6` 不含 P2 + PR-7 仅做入口文档同步不动 phase 文件，因此既不能由 PR-4 也不能由 PR-7 顺手清理）。**归属候选**：建议作为 v4.2 遗留新增条目 #8 登记，或独立小 PR 处理；本 PR 既不承诺也不外推清理责任，避免留下"无主清理项"的合规盲区（V1 finding #2 接纳）

### 3.2 动态用例（链接到主文档 §5.2）

- [ ] **用例 B（§5.2.2 B2 P2 Non-Bug 反流）**：本 PR 是该用例的关键前置 — 需联调验证步骤 ①"P2 phase 内：写 `non_bug_context` → 写 `current_state = Non-Bug` → 设 `current_phase_result = ABORT` → 退出 phase（**本 PR 不新增 step-pause**；现存 1 处 Spec-Uncertain 不被 Non-Bug 路径触达）"
- [ ] **用例 D 反向断言（§5.2.4 D14）**：grep `phases/p2-spec-definition.md` 在 PR-3 合入前后 `<step-pause` 命中数**保持 = 1**（即本 PR diff 不新增 `<step-pause>`，V1 finding #4 接纳）

---

## 4. PR-level 回滚动作

> 详见主文档 §7.3 PR-3 回滚。

- **回滚命令**：`git revert <PR-3-merge-commit>`
- **回滚后状态**：
  - `phases/p2-spec-definition.md` 回到 v3 "判定 Non-Bug 不写 context、不退出" + "Curation-Failed 写状态但不 ABORT" 的双重 bug 态
  - 编排器 case Non-Bug step-pause（PR-2 W5）仍可发起，但 `{non_bug_context}` 占位渲染为空串 → step-pause 标题缺失判定上下文（体验退化但不破链路）
  - `non_bug_reflow_count` ≥ 2 熔断逻辑仍生效（PR-2 W5 自洽）
- **风险等级**：🟢 低（B2 闭环恢复 v1.2.1 描述的缺失态；不引入新 bug）
- **联动回滚提示**：本 PR 与 PR-2 W5 是协议层"闭环对偶" — 若 PR-2 W5 也需回滚，必须**同时**回滚（否则编排器会发起占位空的 step-pause）；与 PR-1 `non_bug_context` 字段注册无强联动（PR-1 字段保留 null 不影响其他流程）

---

## 5. §5.1 静态契约校验自检（本 PR 视角的 grep 脚本）

> 下列 grep 命令在 PR 提交前由开发者本地执行；PR-8 CI 落地后会以更结构化方式（D14/D15/D16 守门）覆盖。

```bash
# 1. D14 守门：phase 内 <step-pause> 命中数应保持 = 1（v3 已有的 Spec-Uncertain）
grep -c '<step-pause' mobile-qa-workflow/phases/p2-spec-definition.md
# 期望输出：1

# 2. B1* P2 ABORT 注入（Non-Bug 早退）
grep -n 'current_phase_result.*ABORT' mobile-qa-workflow/phases/p2-spec-definition.md
# 期望命中：≥ 2 行（变更点 P2-1 + P2-2 各 1 行）

# 3. D17 non_bug_context 写入端
grep -n 'non_bug_context' mobile-qa-workflow/phases/p2-spec-definition.md
# 期望命中：≥ 1 行（变更点 P2-1）

# 4. 三步序列原子性（Non-Bug 早退三动作连续）
grep -n -A 5 'current_state = Non-Bug' mobile-qa-workflow/phases/p2-spec-definition.md
# 期望：紧随其后的 5 行内出现 'current_phase_result = ABORT'

# 5. 范围最小化反向断言：本 PR 不动 phase_history / non_bug_reflow_count
grep -n 'phase_history\|non_bug_reflow_count' mobile-qa-workflow/phases/p2-spec-definition.md
# 期望：0 行命中 phase_history；non_bug_reflow_count 0 行命中（v3 该字段也不在 P2 内出现，由编排器维护）

# 6. C5 Curation-Failed 早退完整性
grep -n -A 3 'current_state = Curation-Failed' mobile-qa-workflow/phases/p2-spec-definition.md
# 期望：紧随其后 3 行内出现 'current_phase_result = ABORT' 与 '退出 phase'
```

---

> **施工单版本**：V1（v2.2，2026-04-20；初稿 v1.0 → V1 接纳 [`pr3-p2-non-bug-context-curating-REVIEW-2026-04-20.md`](./pr3-p2-non-bug-context-curating-REVIEW-2026-04-20.md) 全部 4 项 findings 后重新发布；与主文档 §3 PR-3 描述完全对齐，无范围扩张）
> **下一步**：本 PR 合入主干后，PR-5 接续展开（Deep-Dive 落盘 + step-pause 现状盘点 + allowlist 首版）。
