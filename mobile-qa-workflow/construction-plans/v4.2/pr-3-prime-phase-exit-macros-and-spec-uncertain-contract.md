# PR-3' · phase 出口宏标签 + Spec-Uncertain 契约统一（v4.2 加速档合并 PR）

> **主控文档**：[`./README.md`](./README.md)（§6 PR-3 + PR-4 合并 / §3 H2/H3 / §4 CI 守门表）
> **方案文档**：[`../../../doc/MOBILE_QA_WORKFLOW_STATE_SYNC_OPTIMIZATION_V1.1_2026-04-21.md`](../../../doc/MOBILE_QA_WORKFLOW_STATE_SYNC_OPTIMIZATION_V1.1_2026-04-21.md) §3.2.13a / §3.2.21 / §4.1.0 H1+H2
> **附录文档**：[`./pr-3-prime-appendix-phase-rewrites.md`](./pr-3-prime-appendix-phase-rewrites.md)（11 处 ABORT + 5 处 phase-complete 完整字面对照 + SP-N1 sp 插入文本完整版；本主文档与附录**必须同 PR 同 commit 段提交**）
> **关联 V1.1 项**：O21（`<phase-abort>` / `<phase-complete>` 宏 + 6 phase 全部出口改写 + 6 phase 顶部幂等性注释块外迁）+ O22（`check-phase-abort-structure.sh`，warning 起步）+ **O13a（Spec-Uncertain 回复契约统一为 `1|2|S` 三选）**
> **状态**：📐 已展开（v1.1，2026-04-21；严格对齐原 README §6 PR-3 DoD「全部出口」+ H2「sp 置顶完整展开规则」两项约束）
> **合并依据**：主控时间轴本身标注「PR-3 与 PR-4 可并行」；O21（结构改动）与 O13a（契约改动）**关注点正交**（宏展开 vs 契约语义），合并后 review/回归各节省 1 次。**严守 H3 边界**：PR-5（O10+ registry）/ PR-6（O13/O14 + 首次构建）仍**严格串行**，不在本 PR 范围。
>
> **唯一职责（双段顺序施工）**：
> - **Seg-1（O21 + O22 / B2.5 范围）**：在 `core-rules.xml` `<supported-tags>` 内引入 `<phase-abort>` / `<phase-complete>` 宏（TAG-N1+N2）+ 把主链路 6 个 phase 共 **11 处 ABORT 出口（ABORT-D1~D11）** + **5 处 phase-complete 出口（COMP-D1~D5，P4 因内联 step-pause 留 PR-6）** 改写为宏 + 删除 6 个 phase 顶部「幂等性约束」过渡注释块（CMT-D1~D6 / O4+ Step 3 联动）+ 新建 `check-phase-abort-structure.sh`（SCRIPT-N1，warning）+ ADR-021 状态 `draft → active`（ADR-D1）+ 索引同步（ADR-IDX1 第 1 行）
> - **Seg-2（O13a / B3 第一步）**：`core/workflow.xml` 编排器 step 4 case Spec-Uncertain 改写 `allowed_values=Confirm` → `1|2|S` 三选（CONTRACT-D1）+ `system-prompt.md` 顶部插入 ADR-021 完整展开规则 § 0.2 章节（**SP-N1**，28 行 markdown / **sp 唯一编辑** — 详见 §2.6 v1.2 修订）+ `workflow-status-template.yaml` 新增 `selected_spec_index` 字段（CONTRACT-D3）+ ADR-014 追加 v4.2 修订段落（ADR-D2）+ 索引同步（ADR-IDX1 第 2 行）+ PR-2 留下的 `check-build-system-prompt-precondition.sh` 自动转 notice（CI-N2）
>
> **不在本 PR 范围**：① O10+ registry（PR-5）② O13 / O14 phase 内联 step-pause 删除 + Fix-Confirming + system-prompt 首次构建（PR-6）③ O15 P3 三档升级路径合并 + P4 phase-complete 改写（PR-6 删除内联后由 PR-7 完成）④ check-phase-abort-structure.sh 升级 error（PR-6 完成 D14 收口后再升级）

---

## 1. PR 元信息

| 项 | 值 |
|---|---|
| 分支命名 | `feat/qa-workflow-v4.2-pr3-prime-phase-macros-and-spec-uncertain` |
| Base | PR-2 合入后的 `main` |
| 层级 | 🟡 **协议级 + 用户可见行为变化**：① O21 改 phase 文件结构（中风险，依赖 LLM 宏展开正确性）② O13a 改 Cursor 用户可见的 Spec-Uncertain 弹窗选项（中风险，恢复 Limited 平台原有的三选语义）|
| 目标合入顺序 | PR-1 → PR-2 → **PR-3'** → PR-5 → PR-6 → PR-7 |
| Reviewer | 1 名方案 owner（必看：① ADR-021 §2 4/5 步展开规则与 SP-N1 § 0.2 + 附录 §1/§2 字面 100% 一致 ② 11 处 ABORT 改写后 `state` 取值全部在权威 enum 集内或为占位字面 `{...}` ③ Seg-2 selected_spec_index 字段类型 + 下游消费方约定）+ 1 名平台 owner（必看：① CI Check 15 在干净主干输出零 warning ② Cursor + Dify 双侧 Spec-Uncertain 弹窗截图人工 ≥ 3 例一致 ③ Limited 平台抽 1 用例 LLM 宏展开记录人工抽查 ≥ 5 例 0 漏展开） |
| 关联 V1.1 项 | **Seg-1**：O21 + O22(`check-phase-abort-structure.sh`，warning) + O4+ Step 3（注释外迁）；**Seg-2**：O13a + SP-N1（H1 守门继续保留，待 PR-6 按既定计划移除） |
| **工作量** | **1.7d**（合并节省 ~0.5d；严格对齐 DoD 增加 ~0.2d；拆分：Seg-1 宏定义 + 11+5 处改写 + 注释删除 + CI 脚本 ≈ 1.2d / Seg-2 编排器 case 改写 + sp 单处编辑 + 字段新增 + ADR-014 修订 ≈ 0.5d；跨平台回归 + 人工抽查叠加 ≈ 0d；v1.2 review 收口 CONTRACT-D2 撤销 / COMP-D4 拆条件 ≈ -0.1d） |
| 涉及文件 | **新增**：`mobile-qa-workflow/scripts/check-phase-abort-structure.sh`（SCRIPT-N1）。**修改**（Seg-1）：`core/core-rules.xml`（TAG-N1+N2）+ 6 个 phase 文件（CMT-D1~D6 + ABORT-D1~D11 + COMP-D1~D5）+ `doc/adr/021-phase-abort-macro-tags.md`（ADR-D1）+ `doc/adr/000-index.md`（ADR-IDX1 第 1 行）+ `.github/workflows/qa-workflow-schema-check.yml`（Check 15 集成）。**修改**（Seg-2）：`core/workflow.xml`（CONTRACT-D1）+ `core/workflow-status-template.yaml`（CONTRACT-D3）+ `system-prompt.md`（**单处编辑：仅 SP-N1 在 L86 后插入 § 0.2，~28 行净增**；CONTRACT-D2 在 v1.2 已撤销 — sp 内与 Spec-Uncertain 契约直接相关的 `allowed_values=Confirm` / `spec_uncertain_choice=Confirm` 零命中 / 详见 §2.6）+ `doc/adr/014-step-pause-scope-restriction.md`（ADR-D2）+ `doc/adr/000-index.md`（ADR-IDX1 第 2 行 / 与 Seg-1 同文件不同行）+ `.github/workflows/qa-workflow-schema-check.yml`（Check 13 保持执行，口径说明更新）。 |

---

## 2. 文件级 diff 列表

> 本 PR 共 **6 类变更点 30 个**（v1.2：CONTRACT-D2 撤销，从 31 减为 30），按"先协议（宏定义）→ phase 改写（ABORT + complete）→ 注释外迁 → 契约改写 → ADR 同步 → CI"顺序：
>
> | 编号前缀 | 含义 | 数量 | 段 | 完整字面位置 |
> |---|---|---|---|---|
> | **TAG-N1~N2** | core-rules.xml `<supported-tags>` 内新增 2 个宏标签 | 2 | Seg-1 | 主文档 §2.1 |
> | **ABORT-D1~D11** | P2/P3/P5/P6 共 **11 处** ABORT 出口宏改写 | 11 | Seg-1 | 命中表 §2.2；完整字面 → 附录 §1 |
> | **COMP-D1~D5** | P1/P2/P3/P5/P6 共 **5 处** phase-complete 出口宏改写（P4 留 PR-6）| 5 | Seg-1 | 命中表 §2.3；完整字面 → 附录 §2 |
> | **CMT-D1~D6** | 6 个 phase 顶部"幂等性约束"注释块删除（O4+ Step 3 联动）| 6 | Seg-1 | 命中表 §2.4 |
> | **CONTRACT-D1 + CONTRACT-D3 + SP-N1** | workflow.xml + sp 顶部插入 + status-template.yaml Spec-Uncertain 契约统一（**v1.2 撤销 CONTRACT-D2**：sp 内与 Spec-Uncertain 契约直接相关的 `allowed_values=Confirm` / `spec_uncertain_choice=Confirm` 零命中，无可改写落点） | 3 | Seg-2 | §2.5~§2.7；SP-N1 完整字面 → 附录 §3 |
> | **ADR-D1~D2 + ADR-IDX1 + SCRIPT-N1 + CI-N1~N2** | ADR finalize + 索引同步 + CI 脚本 + workflow yml 集成 | 6 | Seg-1+2 | §2.8~§2.9 |
>
> **变更点编号约定**：N\* = 新建 / D\* = diff 改写 / IDX\* = ADR 索引同步。**Seg 标记**：Seg-1 = O21 + O22；Seg-2 = O13a + sp 顶部 SP-N1。两段 commit 必须分别 push 与 review；附录 §1/§2 进 Seg-1 commit，附录 §3（SP-N1）进 Seg-2 commit。

---

### 2.1 文件 A · `core/core-rules.xml`（Seg-1 / TAG-N1 + TAG-N2）

#### 2.1.1 变更点 TAG-N1 + TAG-N2 · `<supported-tags>` 内 `<execution>` 块新增 2 个宏标签

**操作**：在 `core/core-rules.xml` 现有 `<execution>` 块末尾（`<template-output>` 之后、`</execution>` 之前）追加 2 个 `<tag>` 块。

**新文（追加）**：

```xml
            <tag name="phase-abort">
                <rules>
                    <rule>Phase 早退的声明式宏标签（v4.2 / O21 / 详见 ADR-021）。</rule>
                    <rule critical="true">展开等价于以下 4 个动作（LLM 必须按顺序逐个执行，不得跳过）：
                        1. <action>更新 {workflow_status}：current_state = {state}（state 以 `{` 开头时表示沿用上文已写值）</action>
                        2. <action>更新 {workflow_status}：{fields} 中的全部 key-value（"+1" 表示自增）</action>（仅当属性存在）
                        3. <action>设置 current_phase_result = ABORT</action>
                        4. <action>退出本 phase（编排器 step 4 case 接管，按 current_state 路由）</action>
                    </rule>
                    <rule>禁止在 phase-abort 之后继续执行任何 step。</rule>
                </rules>
                <params>
                    <param name="state" required="true">目标 current_state（必须在权威枚举集内 / 或形如 `{workflow_status}.current_state` 的占位字面）</param>
                    <param name="fields" required="false">附加写回字段，JSON 字面量（支持 "+1" 自增）</param>
                    <param name="reason" required="false">触发原因引用（建议用 ADR-XXX 形式）</param>
                </params>
            </tag>

            <tag name="phase-complete">
                <rules>
                    <rule>Phase 正常完成的声明式宏标签（v4.2 / O21 / 详见 ADR-021）。</rule>
                    <rule critical="true">展开等价于以下 5 个动作：
                        1. <action>更新 {workflow_status}：current_state = {state}</action>
                        2. <action>更新 {workflow_status}：{fields} 中的全部 key-value</action>（仅当属性存在）
                        3. <action>更新 {workflow_status}.phase_history：append {append_history}</action>（仅当属性存在）
                        4. <action>更新 {config_source}：{update_config} 中的全部 key-value</action>（仅当属性存在）
                        5. <action>退出本 phase（按 D1 默认 OK，编排器追加 stepsCompleted）</action>
                    </rule>
                </rules>
                <params>
                    <param name="state" required="true">目标 current_state</param>
                    <param name="fields" required="false">JSON 字面量</param>
                    <param name="append_history" required="false">phase_history 追加项 JSON 字面量</param>
                    <param name="update_config" required="false">config_source 批量注册项 JSON 字面量</param>
                </params>
            </tag>
```

**修订理由（H1 接纳 / V1.1 §3.2.21）**：在 `<supported-tags>` 内显式定义两个新 `<tag>` 块，与 `<workflow-status-routing>` 同款先例（详见 core-rules.xml L100-106），让 LLM 在加载 core-rules 时一次性看到展开协议，不依赖"内化记忆"。

**兼容性影响**：仅新增 2 个标签定义；旧 phase 文件中尚未改写的 5 步咒语写法**继续兼容运行**。CI Check 15 按 warning 起步，不阻塞旧写法。

---

### 2.2 文件 B · 11 处 ABORT 出口改写（Seg-1 / ABORT-D1 ~ D11）

#### 2.2.1 改写命中表

| # | 文件 | 锚点行 | 目标 state | reason | 完整字面对照 |
|---|---|---|---|---|---|
| ABORT-D1 | `phases/p2-spec-definition.md` | L93-112 | `Non-Bug` | ADR-014 | 附录 §1.2 |
| ABORT-D2 | `phases/p2-spec-definition.md` | L178-187 | `Curation-Failed` | ADR-001 | 附录 §1.3 |
| ABORT-D3 | `phases/p3-root-cause.md` | L39-44 | `Spec-Defining` | ADR-001 | 附录 §1.4 |
| ABORT-D4 | `phases/p3-root-cause.md` | L77-87 | `RCA-Designing`（fanout→medium）| ADR-015 | 附录 §1.5 |
| ABORT-D5 | `phases/p3-root-cause.md` | L116-126 | `RCA-Designing`（fanout→complex）| ADR-015 | 附录 §1.6 |
| ABORT-D6 | `phases/p3-root-cause.md` | L167-178 | `Human-Review`（multi-view 不收敛）| ADR-015 | 附录 §1.7 |
| ABORT-D7 | `phases/p3-root-cause.md` | L240-245 | `RCA-LowConfidence` | ADR-001 | 附录 §1.8 |
| ABORT-D8 | `phases/p6-verification.md` | L82-114 | `{workflow_status}.current_state`（占位字面 / 沿用 switch 上文）| ADR-001 | 附录 §1.9 |
| **ABORT-D9** | `phases/p5-fix-impl.md` | L121-127 | `Human-Review`（error-dump 存在）| ADR-001 | 附录 §1.10 |
| **ABORT-D10** | `phases/p5-fix-impl.md` | L140-146 | `Human-Review`（contract-checklist 缺失）| ADR-001 | 附录 §1.11 |
| **ABORT-D11** | `phases/p5-fix-impl.md` | L150-155 | `Human-Review`（两产物均不存在）| ADR-001 | 附录 §1.12 |

#### 2.2.2 通用改写规约（必读）

每处 ABORT 出口改写**强制**遵循（详见附录 §1.1）：
1. **保留**业务计算 `<action>`（生成报告、列出缺失项、写入说明字段）
2. **删除**原 `<action>设置 current_phase_result = ABORT</action>` 行（已被宏第 3 步覆盖）
3. **删除**原 `<action>更新 {workflow_status}：current_state = ...</action>` 行（已被宏第 1 步覆盖）
4. **追加** `<!-- v4.2 PR-3' / ADR-XXX -->` 单行注释引用 reason 对应 ADR

**ABORT-D8 特殊性**：P6 失败回流路径用占位字面 `state="{workflow_status}.current_state"`，配合 ADR-021 §2 落地纪要"state 以 `{` 开头时沿用上文"约定 + Check 15 脚本兼容跳过 enum 校验。
**ABORT-D9~D11 特殊性**：P5 原写法用 `<goto step="8">` 跳到 step 8 失败收口段；改宏后 goto 删除（宏第 4 步「退出本 phase」让 step 8 不可达），step 8 整段保留作为文档说明（PR-7 清理）。

---

### 2.3 文件 C · 5 处 phase-complete 出口改写（Seg-1 / COMP-D1 ~ D5）

#### 2.3.1 改写命中表

| # | 文件 | 锚点行 | 目标 state | 含 fields/history/config 属性 | 完整字面对照 |
|---|---|---|---|---|---|
| COMP-D1 | `phases/p3-root-cause.md` | L226-238 | `Fix-Designing` | fields(reroute_*) + append_history(qa-root-cause) + update_config(output_rca_report) | 附录 §2.2 |
| **COMP-D2** | `phases/p1-intake.md` | L113-120 | `Spec-Defining` | fields(Issue_Boundary_Level 等 3 个) + update_config(output_issue_card 等 3 个) | 附录 §2.3 |
| **COMP-D3** | `phases/p2-spec-definition.md` | L196-202 | `RCA-Designing` | update_config(output_curation_report 等 3 个) | 附录 §2.4 |
| **COMP-D4** | `phases/p5-fix-impl.md` | L158-171 | `Verifying` | update_config(`output_impl_report` 唯一 key) + 宏外 `<check>` 写入 `output_contract_checklist`（v1.2 review Finding #3 收口：宏不支持按单 key 跳过） | 附录 §2.5 |
| **COMP-D5** | `phases/p6-verification.md` | L125-136 | `Done` | (无附加属性) | 附录 §2.6 |

#### 2.3.2 P4 phase-complete 留 PR-6 的明确说明

P4 step 6 成功路径 `current_state = Fix-Implementing` 写入在内联 `<step-pause>` 的 `<option action="...">` 属性内（详见 `legacy-phase-step-pause-allowlist.txt:26`），**不是** step 末的独立 `<action>`。本 PR **不重构**内联 step-pause（D14 整改由 PR-6 完成）；P4 phase-complete 改写**留 PR-6**（在删除内联 step-pause 的同一 commit 内顺手改）。

CI Check 15 对 P4 末 step 输出 `::notice::` 提示"phase-complete 留 PR-6"，**不阻塞**本 PR。

---

### 2.4 文件 D · 6 个 phase 顶部"幂等性约束"注释块删除（Seg-1 / CMT-D1 ~ D6）

#### 2.4.1 改写命中表

| # | 文件 | 锚点行（注释块行号） | 操作 |
|---|---|---|---|
| CMT-D1 | `phases/p1-intake.md` | L17-29 | 整段删除 |
| CMT-D2 | `phases/p2-spec-definition.md` | L17-29 | 整段删除 |
| CMT-D3 | `phases/p3-root-cause.md` | L18-30 | 整段删除 |
| CMT-D4 | `phases/p4-fix-design.md` | L19-31 | 整段删除 |
| CMT-D5 | `phases/p5-fix-impl.md` | L17-29 | 整段删除 |
| CMT-D6 | `phases/p6-verification.md` | L20-32 | 整段删除 |

> **边界**：6 个 phase 文件全部删除"幂等性约束"过渡注释块（共 ~80 行），由 ADR-021 + SP-N1 § 0.2 取代。**不删除**：phase 内的业务级注释（如 P3 step 5 的 OVHSC 注释、P6 step 6 的 C9 模板注释）。注释块内文字本身明确写了"O21 落地后将自动覆盖"，符合外迁条件。

**修订理由 / 兼容性影响**：纯文档清理，无运行时影响；信噪比显著提升。

---

### 2.5 文件 E · `core/workflow.xml` Spec-Uncertain 契约统一（Seg-2 / CONTRACT-D1）

#### 2.5.1 变更点 CONTRACT-D1 · case Spec-Uncertain 改写为 `1|2|S` 三选

**原文锚点**：`core/workflow.xml` L184-207（含 PR-2 已加的 `<!-- ANCHOR: spec-uncertain-allowed-values -->` L184）

**改写要点**（保留 ANCHOR-N2 锚点 + parse_error_count 重置；改写 step-pause 标题与 allowed_values；扩展下游 switch 为 3 个 case）：

```xml
                    <!-- ANCHOR: spec-uncertain-allowed-values -->
                    <case if="Spec-Uncertain">
                        <action>更新 {workflow_status}：parse_error_count = 0</action>

                        <!-- v4.2 PR-3' / Seg-2 / O13a / ADR-014 v4.2 修订：契约统一 Confirm 单选 → 1|2|S 三选；
                             与 phases/p2-spec-definition.md L66-75 内联段（PR-6 删除前）契约一致。
                             P2 进入本 case 前必须已写入 spec_options 与 option_1 / option_2 字面。 -->
                        <step-pause title="Spec 存在歧义，请确认 Expected Behavior：
{spec_options}

[result_field=spec_uncertain_choice]
[allowed_values=1|2|S]
请用 spec_uncertain_choice=&lt;value&gt; 回复"
                                    result_field="spec_uncertain_choice"
                                    allowed_values="1|2|S">
                            <option title="[1] {option_1}（采纳第 1 种 Expected Behavior 继续）" action="spec_uncertain_choice=1"/>
                            <option title="[2] {option_2}（采纳第 2 种 Expected Behavior 继续）" action="spec_uncertain_choice=2"/>
                            <option title="[S] Skip：先并行分析所有可能，后续确认" action="spec_uncertain_choice=S"/>
                        </step-pause>

                        <switch condition="{user_inputs.spec_uncertain_choice}">
                            <case if="1">
                                <action>更新 {workflow_status}：current_state = Spec-Defining, selected_spec_index = 1</action>
                                <action>清空 {workflow_status}.user_inputs.spec_uncertain_choice</action>
                                <goto step="2"/>
                            </case>
                            <case if="2">
                                <action>更新 {workflow_status}：current_state = Spec-Defining, selected_spec_index = 2</action>
                                <action>清空 {workflow_status}.user_inputs.spec_uncertain_choice</action>
                                <goto step="2"/>
                            </case>
                            <case if="S">
                                <action>更新 {workflow_status}：current_state = Spec-Defining, selected_spec_index = parallel</action>
                                <action>清空 {workflow_status}.user_inputs.spec_uncertain_choice</action>
                                <goto step="2"/>
                            </case>
                        </switch>
                    </case>
```

**修订理由（v1.2 review Finding #2 收口 — 收窄为"仅统一交互契约"）**：与 V1.1 §3.2.0 / §3.2.13a F1 finding 完全对齐 — 选项从单选 `Confirm` 改为 `1|2|S` 三选，恢复"列出多种可能 spec 的**用户交互界面**"。**本 PR 范围严格限定**：① 编排器写入 `selected_spec_index` 字段（取值 1 / 2 / parallel）；② P2 实际行为变化（按 `selected_spec_index` 决定走"采纳 spec 1 / spec 2 / 并行分析"路径）**留 PR-7 O15 收敛**，本 PR **不引入 P2 行为变化**（`selected_spec_index` 在 v4.2 阶段为"协议显式化字段"，写入但暂不消费 — 详见 §2.7 CONTRACT-D3 注释 + §6 议题 #3）。

**兼容性影响**：① Cursor / Trae（Full）从单次确认变为三选 — 属"**UI 层恢复语义**"（V1.1 §3.2.0 论证），P2 内联段（PR-6 删除前）继续按当前逻辑执行，**不会因为用户选 `1` 或 `2` 触发不同的 P2 分析路径**（PR-7 O15 接入后才生效）② Dify / Coze（Limited）原本 sp 路由表（L196）描述就是 `1|2|S`，本 PR 让 core 与 sp 完全一致 ③ 存量会话进入 case 时本来就重新走 step 4 路由，无"已暂停态"兼容问题 ④ 已写 `user_inputs.spec_uncertain_choice = Confirm` 的极端 case 命中 default → 重发起 step-pause，不卡死。

---

### 2.6 文件 F · `system-prompt.md` 单处编辑（Seg-2 / 仅 SP-N1 / v1.2 review Finding #1 收口）

> **重要约束（PR-2 H1 守门继续保留）**：本 PR 是**首次合法**对 `system-prompt.md` 做实质改动的 PR。**v1.2 修订**：经 review Finding #1 静态核对，sp 内与 Spec-Uncertain 契约直接相关的 `allowed_values=Confirm` / `spec_uncertain_choice=Confirm` **零命中**（详见下方 §2.6.2），原 v1.1 设计的 CONTRACT-D2「ANCHOR-N1 窗口内 Spec-Uncertain 详写段 `Confirm` → `1|2|S` 改写」**已撤销**。**sp 在 PR-3' Seg-2 中的唯一编辑** = SP-N1。

#### 2.6.1 唯一编辑 · SP-N1（在 sp L86 后插入 § 0.2 章节，约 28 行 markdown）

**插入位置**：`system-prompt.md` L86 之后（即 `</core-rules>` 标签之后、`## 0.1 角色口径` 之前），新增 `## 0.2 Phase 出口宏标签展开规则（O21 / ADR-021 / v4.2 PR-3'）` 章节。

**完整插入文本**：详见**附录 §3.2**（28 行 markdown 逐字写入；含 `<phase-abort>` 4 步展开 + `<phase-complete>` 5 步展开 + 4 条绝对禁止清单）。

**修订理由（H2 强约束）**：原 PR-3 README §6 H2 明确要求「`system-prompt.md` 置顶位置写入完整展开规则——不只是引用」。本 SP-N1 是 **Limited 平台 / 小 LLM 的兜底执行规则**，让"加载 sp 即可独立执行宏改写后的 phase 文件"，不依赖外部 ADR-021 文档可达性。

**兼容性影响**：① Limited 平台收益：B2.5 H3"Limited 平台漏展开抽查"风险显著下降 ② Full 平台：Cursor / Trae 直接 load core-rules.xml，sp § 0.2 是冗余兜底，不重复执行 ③ PR-6 兼容：生成器需识别 § 0.2 章节并保留（生成器策略：sp 内手维护章节用 `## 0.x` 编号，自动生成内容用 `## N.x` 编号 N≥1；§ 0.2 归入 builder 函数 `build_l0_identity` 内联）— 本 PR 不交付 builder 适配，留 PR-6 同步。

**sp 改动总行数**：仅 SP-N1 = **~28 行净增量**。

#### 2.6.2 CONTRACT-D2 撤销说明（v1.2 review Finding #1 静态核对）

**v1.1 设想**：在 sp ANCHOR-N1（L195）之后扫描"Spec-Uncertain 详写段"，把 `allowed_values=Confirm` 改为 `1|2|S`，作为 sp 的第二处编辑。

**v1.2 静态核对结果**（基于真实 sp 文件 grep）：
- sp 内与 Spec-Uncertain 契约直接相关的 `allowed_values=Confirm` / `spec_uncertain_choice=Confirm` **零命中**（注：`Fix-Confirming` 等其他语义无关字面不纳入本核对口径）；
- ANCHOR-N1 之后的 L196 路由表行已经是 `allowed_values=1|2|S`（PR-2 已对齐 — 不动）；
- sp L260-275 的 P2 内联段（`step-pause title="Spec 存在歧义..."`）本就**不带** `[allowed_values=]` 标签，选项已经是 `[1] {option_1}` / `[2] {option_2}` / `[S] Skip` —— 与 `1|2|S` 三选完全一致；
- 因此 sp 中**不存在** `CONTRACT-D2` 的合法落点，强行新增内容会违反"`system-prompt.md` 改动仅限白名单"约束。

**结论**：**CONTRACT-D2 撤销**；sp 侧的 `1|2|S` 已由 PR-2 对齐，core 侧的 `1|2|S` 由本 PR 的 CONTRACT-D1 完成对齐；SP-N1 仅负责补充宏展开规则，**不引入也不修改** Spec-Uncertain 的 `allowed_values` 字面。

#### 2.6.3 H1 守门 PASS 验证

`check-build-system-prompt-precondition.sh`（PR-2 加入）的 H1 守门：sp ANCHOR-N1 窗口内 `allowed_values` 必须为 `1|2|S` —— PR-2 合入时已对齐，本 PR 不触及该窗口；H1 守门继续 PASS + step 4 输出 notice "PR-6 内可解除本守门" 自动生效（CI-N2）。

---

### 2.7 文件 G · `core/workflow-status-template.yaml` 新增 `selected_spec_index` 字段（Seg-2 / CONTRACT-D3）

**操作**：在"路由（RCA）"分组附近（建议紧邻 `analysis_complexity_confidence` 之后），新增 1 字段 + 注释块。

```yaml
# v4.2 PR-3' / Seg-2 / O13a / ADR-014 v4.2 修订（v1.2 review Finding #2 收口：仅协议显式化，无消费方）：
# Spec-Uncertain step-pause 用户回复后由编排器 step 4 case Spec-Uncertain 写入；
# 取值含义：1 = 采纳第 1 种 Expected Behavior / 2 = 采纳第 2 种 / parallel = 先并行分析所有可能；
# v4.2 阶段：本字段仅"写入"，P2 暂不消费，不引入 P2 行为变化（用户在 Cursor 选 1 / 2 / S 仅影响弹窗 UI，
# 实际 P2 内联段继续按当前逻辑执行）；P2 实际按 selected_spec_index 路由的能力留 PR-7 O15 收敛。
# 兼容性：v3 / v4 老会话 selected_spec_index 字段不存在 → default 视作 null。
selected_spec_index: null
```

**修订理由 / 兼容性影响**：纯字段新增；不引入路由分支变更；存量会话默认 null 即可。`check-state-enum.sh` 仅校验 enum 字段（current_state），新字段不在校验范围。

---

### 2.8 文件 H · ADR 同步（Seg-1+2 / ADR-D1 + ADR-D2 + ADR-IDX1）

| # | 文件 | 操作 | Seg |
|---|---|---|---|
| ADR-D1 | `doc/adr/021-phase-abort-macro-tags.md` | 顶部 `> **状态**：**draft** ...` 改 `**active**（v4.2 PR-3' 已落地）`；末尾追加"PR-3' 落地纪要"段（含 11 处 ABORT + 5 处 phase-complete 命中点 + ABORT-D8 「state 占位字面」补充约定 + COMP / ABORT 改写后的"绝对禁止清单"摘要）| Seg-1 |
| ADR-D2 | `doc/adr/014-step-pause-scope-restriction.md` | 末尾追加"v4.2 PR-3' 修订 — Spec-Uncertain 契约统一"段：① 1\|2\|S 三选 ② Limited 平台已有的三选行为升格为跨平台权威 ③ Cursor 用户从单选变三选属"恢复语义" ④ 关联 PR-6 删除 P2 phase 内联 step-pause 的依赖关系 | Seg-2 |
| ADR-IDX1 | `doc/adr/000-index.md` | ① ADR-021 行：状态列 `**draft**` → `active`，落地 PR 列 `**v4.2 PR-3（落地依赖）**` → `v4.2 PR-3'（已合入）`；② ADR-014 行：落地 PR 列末尾追加 ` + v4.2 PR-3' 修订` | Seg-1+2 各 1 行（git 自然合并） |

---

### 2.9 文件 I · `scripts/check-phase-abort-structure.sh` 新建 + CI 集成（Seg-1 / SCRIPT-N1 + CI-N1 + CI-N2）

#### 2.9.1 SCRIPT-N1 · `check-phase-abort-structure.sh`（warning 起步，约 80 行 bash + 内嵌 python）

**守门目标**（V1.1 §3.2.22）：
- ① `<phase-abort>` / `<phase-complete>` 的 `state` 必须在权威 enum 集内（占位字面 `{` 开头时跳过）
- ② `fields` key 必须在 `workflow-status-template.yaml` 字段表内
- ③ 每个 phase 末 step 应包含 `<phase-complete>` 或 `<phase-abort>`（PR-3' 仅 P1/P2/P3/P5/P6 已对齐，**P4 输出 notice 提示"留 PR-6"**，warning/error 切换由 `PHASE_ABORT_SEVERITY` 环境变量控制）

**核心算法**（与 PR-2 SCRIPT-FIX1 同款 python 严格模式提取 enum / 字段集）：

```bash
SEVERITY="${PHASE_ABORT_SEVERITY:-warning}"
ENUM_SET=$(python3 ... 提取 workflow-status-template.yaml 头部权威 enum 集)
FIELD_SET=$(python3 ... 提取 workflow-status-template.yaml 顶层字段集)

for phase_file in mobile-qa-workflow/phases/*.md; do
    while IFS= read -r macro; do
        state=$(echo "$macro" | grep -oE 'state="[^"]+"' | sed 's/state="//;s/"$//')
        if [ -n "$state" ] && [[ ! "$state" =~ ^\{ ]] && ! echo " $ENUM_SET " | grep -q " $state "; then
            echo "::${SEVERITY}::$phase_file: state='$state' 不在权威 enum 集内"
            [ "$SEVERITY" = "error" ] && fail=1
        fi
        # fields key 同款校验
    done < <(grep -E '<phase-(abort|complete)\b' "$phase_file")

    # 末 step 含宏校验：仅 P4 给出 notice，其余给出 warning
    if ! tail_step_contains_macro "$phase_file"; then
        if [[ "$phase_file" =~ p4-fix-design ]]; then
            echo "::notice::$phase_file: P4 末 step 未用宏（PR-6 删除内联 step-pause 后改写）"
        else
            echo "::${SEVERITY}::$phase_file: 末 step 未用 phase-complete/abort 宏"
        fi
    fi
done
```

#### 2.9.2 CI-N1 · `.github/workflows/qa-workflow-schema-check.yml` 集成 Check 15

```yaml
      # ════════════════════════════════════════════════════════════════
      # 检查 15（PR-3' 启用 warning）：phase-abort / phase-complete 宏结构守门
      # PR-6 合入后由 PHASE_ABORT_SEVERITY=error 升级
      # ════════════════════════════════════════════════════════════════
      - name: Check 15 — phase-abort/complete 宏结构守门
        env:
          PHASE_ABORT_SEVERITY: warning  # PR-3' 起步 warning，PR-6 升级 error
        run: bash mobile-qa-workflow/scripts/check-phase-abort-structure.sh
```

#### 2.9.3 CI-N2 · Check 13（H1 守门）转 notice

sp 与 core 的 `1|2|S` 一致性由两侧分别保障：sp 侧 = PR-2 已对齐；core 侧 = 本 PR CONTRACT-D1 改写 `Confirm` → `1|2|S`；SP-N1 仅新增宏展开规则且不触及 ANCHOR-N1 窗口。基于此，脚本继续跑，输出 PASS + notice "PR-6 内可解除本守门"。**Check 13 step 在本 PR 保留不动**；PR-6 完成首次构建后由该 PR 删除。

---

## 3. PR-level DoD 子集（链接到主控 §5）

### 3.1 静态契约校验

- [ ] **TAG-N1+N2 落地**：`core-rules.xml` `<execution>` 内 grep `<tag name="phase-abort">` + `<tag name="phase-complete">` 命中各 1；展开规则字面与 ADR-021 §2 + SP-N1 § 0.2 + 附录 §1.1/§2.1 三处 100% 一致
- [ ] **ABORT-D1 ~ D11 落地**：6 个 phase 文件中（P2/P3/P5/P6 共 11 处出口）原 `<action>设置 current_phase_result = ABORT</action>` 命中数 = **0**（ABORT-D8 因占位字面单计为已改写）；新出现 `<phase-abort>` 宏命中数 = **11**
- [ ] **COMP-D1 ~ D5 落地**：5 个 phase 文件（P1/P2/P3/P5/P6 各 1 处末 step）的 phase-complete 改写命中数 = **5**；P4 末 step 未含宏（CI Check 15 输出 notice 标"留 PR-6"）
- [ ] **CMT-D1 ~ D6 落地**：6 个 phase 文件顶部 grep `幂等性约束（V1.1 O6` 命中 = **0**
- [ ] **CONTRACT-D1 落地**：`core/workflow.xml` 内 grep `allowed_values="Confirm"` = **0**；grep `allowed_values="1\|2\|S"` = **1**（在 ANCHOR-N2 锚点窗口内）；下游 switch 内 `1` / `2` / `S` 3 个 case 全部存在
- [ ] **SP-N1 落地**：`system-prompt.md` 内 grep `## 0.2 Phase 出口宏标签展开规则` = **1**（在 § 0 与 § 0.1 之间）；§ 0.2 章节字面 28 行与附录 §3.2 完全一致；`bash check-system-prompt-sync.sh` 仍绿（§ 0.2 不在 ENUM-DECLARATION-BLOCK 与 ANCHOR-N1 窗口内，sync 检查不触发误报）
- [ ] **sp `1\|2\|S` 一致性（v1.2 修订 / 取代 CONTRACT-D2）**：`system-prompt.md` 内 grep `allowed_values=1\|2\|S` 命中 = **1**（仅 L196 路由表行 — PR-2 已对齐，本 PR **不动该窗口**）；grep `allowed_values=Confirm` = **0**；grep `spec_uncertain_choice=Confirm` = **0**；`bash check-build-system-prompt-precondition.sh` 输出 PASS + `notice::PR-6 内可解除本守门`；脚本退出 0
- [ ] **CONTRACT-D3 落地**：`workflow-status-template.yaml` 内 grep `^selected_spec_index:` = **1**；`check-state-enum.sh` 仍绿
- [ ] **ADR-D1 + ADR-D2 + ADR-IDX1 落地**：ADR-021 状态变 active + 含 PR-3' 落地纪要段；ADR-014 末尾含 v4.2 PR-3' 修订段；ADR-索引中 ADR-021 落地 PR 列含 `v4.2 PR-3'（已合入）`，ADR-014 落地 PR 列含 `+ v4.2 PR-3' 修订`
- [ ] **SCRIPT-N1 + CI-N1 + CI-N2 落地**：脚本文件存在 + 可执行权限；干净主干实跑零 `::warning::`（仅允许 1 处 `::notice::` — P4 末 step）；workflow yml 含 Check 15 step；Check 13 仍在并输出 notice
- [ ] **system-prompt.md 防误改（v1.2 收紧）**：本 PR diff 中 sp 改动**仅限 SP-N1 一处**（L86 后插入 § 0.2 章节，~28 行新增；零删除、零字符外修订）；reviewer 必贴 `git diff -- mobile-qa-workflow/system-prompt.md` 完整输出供审；任何 SP-N1 之外的 sp 行变动 = block

### 3.2 动态用例

- [ ] **跨平台回归（主控 §5 PR-3 + PR-4 行合并）**：
  - **Cursor**：eval-cases 全量 + 人工抽查 LLM 宏展开记录 ≥ 10 例（B2.5 H3 接纳）+ Spec-Uncertain 弹窗截图 ≥ 3 例（B3 PR-4 接纳）
  - **Trae**：eval-cases 全量 + 人工抽查宏展开 ≥ 5 例
  - **Dify（Limited，关键）**：eval-cases 全量 + Spec-Uncertain 弹窗截图人工 ≥ 3 例（与 Cursor 截图选项**完全一致**）+ **抽 1 用例验证 sp § 0.2 SP-N1 实际指导 LLM 完成宏展开 ≥ 5 例 0 漏展开**（H2 强约束硬验收）
  - 单 prompt LLM：抽 1 用例 + 人工 1 例宏展开
- [ ] **B2.5 验收硬门禁**：宏展开 4/5 步动作（state / fields / phase_history / config / ABORT 或退出）全部正确；漏一步即视为验收失败 → 触发 H2 降级路径（Seg-1 单独 revert，Seg-2 保留）
- [ ] **B3 PR-4 验收硬门禁（v1.2 收窄）**：Cursor + Dify 双侧 Spec-Uncertain 弹窗选项 100% 一致；用户回复 `1` / `2` / `S` 后 `workflow-status.yaml.selected_spec_index` 字段被编排器写入正确取值 ∈ {1, 2, parallel}；**不验收"P2 按 selected_spec_index 走差异化路径"**（该能力留 PR-7 O15）
- [ ] **通用门禁（V1.1 §4.2）**：`eval-framework/artifact_checker.py` 全量通过 + `eval-cases/seed-10` chains A/B `mean_score` 不降（容许 ±5%） + 路由层抽 5 case 人工读 `workflow-status.yaml` 一致性

> **PR-3' 不验收的 §5 项**：step-pause registry → PR-5；P2/P4 phase 内联 step-pause 删除 + Fix-Confirming + system-prompt 首次构建 → PR-6；O15 P3 升级路径合并 → PR-7

---

## 4. PR-level 回滚动作

### 4.1 单段回滚（推荐）

PR-3' 必须以 **2 个独立 commit 段**（Seg-1 / Seg-2）push，便于按段回滚。附录与主文档**同 PR 同 commit 段**（附录 §1+§2 进 Seg-1；附录 §3 进 Seg-2）。

| 失败场景 | 回滚命令 | 残留状态 |
|---|---|---|
| Seg-1 验收失败（B2.5 宏展开 < 90% 正确率 / Check 15 误报阻塞 / Limited 漏展开 > 5%） | `git revert <Seg-1-commit>`（保留 Seg-2） | TAG-N1+N2 + ABORT-D1~D11 + COMP-D1~D5 + CMT-D1~D6 + ADR-021 状态 + Check 15 全部撤回；O13a 契约统一仍生效（H1 守门转 noop）；附录 §1+§2 撤回 |
| Seg-2 验收失败（双侧 Spec-Uncertain 选项不一致 / SP-N1 § 0.2 触发 sp 其他段落渲染异常 / Cursor 用户回退要求） | `git revert <Seg-2-commit>`（保留 Seg-1） | core/workflow.xml 回退 Confirm 单选；sp 回退（**仅 SP-N1 § 0.2 撤回** — v1.2 已撤销 CONTRACT-D2，无需关联回退）；CONTRACT-D3 selected_spec_index 字段保留为 null（schema 兼容）；H1 守门重新生效 |
| 两段都失败（极小概率） | `git revert <PR-3'-merge-commit>` | 完全回到 PR-2 合入态 |

### 4.2 H2 降级路径（V1.1 §4.1.0）

若 Seg-1 验收失败触发 H2：
- PR-5 / PR-6 不阻塞，按 5 步咒语写法继续推进
- O21 推迟到 v4.3 评估
- V1.1 §5 量化对比表中"Phase 早退 ABORT 点平均行数"+"B1\* 类 bug 再现概率"两行收益降级为 0

### 4.3 下游影响

- **PR-5 弱依赖**：O10+ registry 不引用宏标签；本 PR 回滚不影响 PR-5
- **PR-6 强依赖 Seg-2**：① PR-6 触发 sp 首次构建依赖 sp 已对齐 `1|2|S`；Seg-2 回滚后 PR-6 必须等 PR-3'-v2 重新合入 ② PR-6 删除 P2 / P4 phase 内联 step-pause 时**顺便完成 P4 phase-complete 改写**（COMP-P4，本 PR 留下的唯一遗留项）③ PR-6 builder 函数 `build_l0_identity` 需识别 sp § 0.2 SP-N1 章节并保留
- **PR-7 弱依赖 Seg-1**：O15 P3 三档升级路径合并强烈推荐用 `<phase-abort>` 宏；Seg-1 回滚后 PR-7 退化为 5 步咒语写法

---

## 5. CI 守门自检（PR-3' 视角）

| 主控 §4 脚本 | PR-3' 状态 | 落地证据 / 承接 PR |
|---|---|---|
| `check-state-enum.sh` | ✅ error（PR-1 已启用） | 不变；CONTRACT-D3 新增字段不在 enum 校验范围 |
| `check-system-prompt-sync.sh` | ✅ error（PR-2 已升级） | 不变；SP-N1 在 § 0.2 章节，不触及 ENUM-DECLARATION-BLOCK / ANCHOR-N1 窗口；sp 侧 `1\|2\|S` 由 PR-2 已对齐，core 侧 `1\|2\|S` 由本 PR CONTRACT-D1 对齐（v1.2：CONTRACT-D2 已撤销） |
| `check-io-contract.sh` | ⏸ warning（PR-2 维持） | 不在本 PR 范围 |
| `check-subagent-params.sh` | ✅ error（PR-1 已启用） | 不变 |
| `check-build-system-prompt-precondition.sh`（H1 守门） | ✅ **继续为 error 守门（通过时附带 notice）** | H1 守门在本 PR **继续执行**：sp 侧 `1\|2\|S` 由 PR-2 已对齐，core 侧 `1\|2\|S` 由本 PR CONTRACT-D1 对齐；脚本在前置条件不满足时仍报错退出，仅在通过且 core 已统一时额外输出 `notice::PR-6 内可解除本守门`；**PR-6 内删除 Check 13 step** |
| `check-phase-abort-structure.sh` | ✅ **PR-3' 启用 warning** | SCRIPT-N1 + CI-N1；PR-6 升级 error；干净主干仅允许 1 处 P4 末 step notice |
| `check-step-pause-registry.sh` | ⏸ | PR-5 启用 error |

**自检结论**：PR-3' 落地主控 §4 中 PR-3 + PR-4 启用列的 **2 项**（Check 15 新增 warning + Check 13 继续作为 error 守门执行，满足条件时附带 notice）；CI 总耗时增加 ~10-20 秒。

---

## 6. Reviewer 议题汇总

| # | 议题 | 影响范围 | 处理建议 |
|---|---|---|---|
| 1 | **Seg-1 / Seg-2 commit 边界纪律 + 附录 commit 归属（v1.2 review Finding #4 收口）**：附录 §1+§2 进 Seg-1、附录 §3 进 Seg-2 — **唯一边界**（v1.1 附录 L7-9 描述自相矛盾，v1.2 已统一）；任何"顺手把 Seg-1 的小修补带进 Seg-2 commit"都会让按段 revert 失效 | 回滚可执行性 | PR description 必贴两个 commit 的 hash + 各自的 stat；CI 加 commit-message 校验（commit 1 必须以 `Seg-1` 开头，commit 2 以 `Seg-2` 开头）；附录 §3 改动行数必须与 sp SP-N1 改动行数一致（28 行 markdown） |
| 2 | **ABORT-D8（P6 失败回流）的 state 占位字面 `{workflow_status}.current_state`**：宏展开时 LLM 是否能正确"沿用上文已写值" | LLM 解释一致性 | 在 ADR-021 §2 落地纪要 + SP-N1 § 0.2 第 1 步 + 附录 §1.1 同步追加约定 — 三处一致：「当 state 取值以 `{` 开头时，LLM 应理解为'沿用本 step 内已写入的 current_state'」；CI Check 15 跳过该字面校验 |
| 3 | **CONTRACT-D3 selected_spec_index 字段下游消费方（v1.2 review Finding #2 收口）**：本 PR **仅由编排器 step 4 写入，P2 暂不消费**；是否构成"协议显式化但无消费方"的浮空字段？v1.1 曾在 §2.5 修订理由段写"下游 P2 重入按 selected_spec_index 决定走采纳 1 / 2 / 并行分析"，与 §2.7 yaml 注释"v4.2 暂不强制 P2 消费"自相矛盾；v1.2 已统一收窄为"仅协议显式化，无消费方" | 协议完备性 | 接受浮空：① ADR-014 v4.2 修订段落明确登记"未来 PR-7 O15 收敛时由 P2 消费"过渡字段；② 不消费不引入运行时风险（YAML 字段写入但读取方 default null）；③ PR-7 O15 落地时把 P2 step 4 内联 step-pause 改写为按 `selected_spec_index` 路由；④ B3 验收硬门禁同步收窄为"字段写入正确"，**不验收 P2 行为差异化** |
| 4 | **B2.5 + B3 验收叠加成本 + Limited 平台 SP-N1 实测**：合并 PR 后必须一次跑完 ① 宏展开人工抽查 ≥ 10 例 ② 双侧弹窗一致 ≥ 3 例 ③ Limited 平台 SP-N1 实测 ≥ 5 例 0 漏展开 — 验收清单是否过长？ | 验收执行性 | 接受叠加：① 三类抽查可由 owner / 平台 owner / QA 分工并行；② 叠加比拆开两个 PR 各跑一遍仍节省一次完整跨平台回归（~0.3d）；③ 任一项失败可触发 §4.1 单段回滚 |
| 5 | **CMT-D1~D6 删除幂等性注释块的"教育损失"** + SP-N1 § 0.2 是否替代教育职能 | 文档可达性 | SP-N1 § 0.2 28 行 markdown 已完整覆盖原幂等性注释块的核心约束（"current_state 单一写入 + 显式 ABORT + 退出 phase"），且对 Limited 平台直接可执行；phase 顶部信噪比提升对日常 review 收益 > 注释删除的教育成本 |
| 6 | **CONTRACT-D1 内 spec_options 占位 `{spec_options}` 与 `{option_1}` / `{option_2}`**：编排器 step 4 case 渲染 step-pause 标题时这些占位由谁注入？ | 协议完整性 | 由 P2 step 4 内联段（PR-6 删除前）写入 `workflow_status.spec_options` + 各 option 字面；本 PR Seg-2 仅改 step-pause 标题/option 字面；P2 内联段已写 `{option_1}` / `{option_2}` 占位，编排器 case 直接复用 |
| 7 | **PR-3' 跨段 ADR 改动协调**：ADR-021（Seg-1）+ ADR-014（Seg-2）+ ADR-索引（Seg-1+2）3 个 ADR 文件改动如何分到 2 个 commit？ | commit 纪律 | ADR-021 / ADR-索引（ADR-021 行）放 Seg-1 commit；ADR-014 / ADR-索引（ADR-014 行）放 Seg-2 commit；索引文件需在 2 个 commit 各改一行（git 自然合并，不冲突） |
| 8 | **ABORT-D9~D11（P5）的 goto step="8" 删除 + step 8 整段保留**：是否破坏 P5 现有失败收口语义？ | 协议完整性 | 不破坏。宏第 4 步「退出本 phase」让 step 8 不可达，但 step 8 内仅一句话「保持当前阶段未完成，等待 Human-Review 处理」— 该语义已被宏 + 编排器 step 4 case Human-Review 路由完整覆盖；step 8 整段保留作为文档说明，PR-7 清理；CI Check 15 给 P5 末 step 输出 OK（含宏） |
| 9 | **COMP-D4 条件写入显式拆出宏外（v1.2 review Finding #3 收口）**：P5 step 7 原写法 `output_contract_checklist = {output_contract_checklist}（若存在）` 是条件写入；v1.1 误把"若存在"压进宏 `update_config`，但宏 `update_config` 协议明确是"全部 key=value 写入"，没有"按单 key 视运行时值跳过"的规则 | 协议完整性 / 宏与实例契约一致性 | v1.2 已采纳 review 方案 A：**保留 `<check if="{output_contract_checklist} 文件存在">` 分支**，写入动作显式拆出宏外；宏 `update_config` 仅含 `output_impl_report` 一项；不动宏协议 / 不引入新 conditional 语法。reviewer 必读附录 §2.5 v1.2 新文以核对最终 xml |

---

## Changelog

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-04-21 | 初版。8 处 ABORT + 1 处 phase-complete 示范。漏算 P5 三处 ABORT 出口与原 PR-3 H2「sp 顶部展开规则」要求。 |
| **v1.1** | **2026-04-21** | **严格对齐原 PR-3 README §6 DoD「全部出口」+ H2「sp 置顶完整展开规则」两项约束**。变更点扩展：① ABORT 从 8 处补足为 **11 处**（新增 ABORT-D9~D11 = P5 step 6 三个失败分支）；② phase-complete 从 1 处示范补足为 **5 处**（新增 COMP-D2~D5 = P1/P2/P5/P6 末 step；P4 因内联 step-pause 留 PR-6）；③ 新增 **SP-N1**（sp L86 后插入 § 0.2 ADR-021 完整展开规则 28 行 markdown）；④ CMT 从 5 处扩为 **6 处**（CMT-D5 = P5 注释删除）；⑤ 单点改写示例（原 §2.2.2 / §2.3.1 / §2.4.2 共约 118 行）整体迁移至附录 [`./pr-3-prime-appendix-phase-rewrites.md`](./pr-3-prime-appendix-phase-rewrites.md)；⑥ 工作量从 1.5d 调至 **1.8d**（合并节省 0.5d - 严格对齐增加 0.3d）；⑦ DoD 增加 SP-N1 + Limited 平台 SP-N1 实测 ≥ 5 例 0 漏展开硬验收；⑧ Reviewer 议题 #1 收紧附录 commit 归属，#5 调整为 SP-N1 替代教育职能，新增 #8 P5 step 8 保留说明。 |
| **v1.2** | **2026-04-21** | **采纳 [质检报告 v1](./pr-3-prime-review-report-2026-04-21.md) 全部 4 个 Finding + 1 个次要观察**：① **Finding #1 / Blocking** — 撤销 `CONTRACT-D2`（sp 内与 Spec-Uncertain 契约直接相关的 `allowed_values=Confirm` / `spec_uncertain_choice=Confirm` 零命中、L196 路由表 PR-2 已对齐 / L260-275 P2 内联段不带 `[allowed_values=]` 标签），sp 改为**单处编辑**（仅 SP-N1 / ~28 行净增）；变更点总数 31 → 30；DoD「sp `1\|2\|S` 命中 ≥ 2」改为「= 1」；§2.6 全段重写。② **Finding #2 / Major** — `selected_spec_index` 语义统一收窄为"**仅协议显式化，无 P2 消费方**"（CONTRACT-D1 修订理由删除"下游 P2 按字段路由"承诺；§2.7 yaml 注释 + §3.2 B3 验收硬门禁 + §6 议题 #3 同步收紧）；P2 行为差异化能力留 PR-7 O15。③ **Finding #3 / Major** — `COMP-D4` 采纳方案 A：`output_contract_checklist` 条件写入**显式拆出宏外**（保留 `<check>` 分支），宏 `update_config` 仅含 `output_impl_report` 一项；不扩展宏协议；附录 §2.5 新文同步重写。④ **Finding #4 / Blocking** — 附录 Seg 边界统一为「§1+§2 进 Seg-1 / §3 进 Seg-2」唯一规则，附录开头 L7-9 矛盾描述 + §3 头部 Seg 标注全部修正；主文档 §6 议题 #1 同步声明。⑤ **次要观察** — 附录 §1.10 ABORT-D9 删除"保留 goto"句，与"新文已删 goto"代码对齐；ABORT-D10/D11 同此模式补充。⑥ 新增 §6 议题 #9（COMP-D4 拆条件交底）；工作量从 1.8d 略调至 **1.7d**（CONTRACT-D2 撤销节省 ~0.1d）。 |
