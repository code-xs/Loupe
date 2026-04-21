# PR-3' 附录 · phase 改写完整字面对照 + system-prompt 顶部插入文本

> **关联主文档**：[`./pr-3-prime-phase-exit-macros-and-spec-uncertain-contract.md`](./pr-3-prime-phase-exit-macros-and-spec-uncertain-contract.md)
> **附录用途**：① 11 处 `<phase-abort>` 改写完整字面对照（ABORT-D1 ~ D11）② 5 处 `<phase-complete>` 改写完整字面对照（COMP-D1 ~ D5）③ `system-prompt.md` 顶部 SP-N1 插入文本完整版（O21 / ADR-021 H2 强约束）
> **审阅边界**：本附录是主文档变更点的"完整字面"补全，主文档已用命中表 + 通用规约约束行为；reviewer 必须主文档与附录两份合看，且 commit 时附录与主文档**同一 commit 内**（方便 git revert 单段回滚）。
>
> **Seg 划分纪律（与主文档一致 / v1.1 review Finding #4 收口）**：
> - **Seg-1 commit**：附录 §1 全部（ABORT-D1 ~ D11）+ 附录 §2 全部（COMP-D1 ~ D5）
> - **Seg-2 commit**：附录 §3 全部（SP-N1 sp 插入文本完整版）
> - **附录与主文档同段 commit**：reviewer 必须按段对齐查看（Seg-1 主文档段 ↔ 附录 §1+§2；Seg-2 主文档段 ↔ 附录 §3）

---

## §1 ABORT 改写完整字面对照（ABORT-D1 ~ D11，全部 Seg-1）

### §1.1 通用改写规约（先读再看 11 处对照）

每处 ABORT 出口改写**强制**遵循 4 条规约：
1. **保留**业务计算 `<action>`（如生成报告、列出缺失项、写入说明字段）— 这些是宏外的纯计算，不能省
2. **删除**原 `<action>设置 current_phase_result = ABORT</action>` 行（已被宏第 3 步覆盖）
3. **删除**原 `<action>更新 {workflow_status}：current_state = ...</action>` 行（已被宏第 1 步覆盖）
4. **追加** `<!-- v4.2 PR-3' / ADR-XXX -->` 单行注释，引用 reason 对应 ADR

### §1.2 ABORT-D1 · P2 Non-Bug（L93-112）

**原文**：

```93:112:mobile-qa-workflow/phases/p2-spec-definition.md
            <check if="判定为 Non-Bug（命中 Working-As-Designed / User-Misoperation / Environment-Specific / Known-Limitation / Duplicate 之一）">
                <action>生成 Non-Bug Resolution Report 文本：包含
                        - 判定类别（5 选 1）
                        - 判定依据（对应 Spec 条款 / 复现路径 / 环境快照锚点）
                        - 沟通建议（一段面向 reporter 的回复要点，便于 step-pause 用户决策）
                        - 改进建议（可选；如对应 UX 工单 / Feature Request / 文档改进）</action>

                <action>更新 {workflow_status}：non_bug_context = {上述 Non-Bug Resolution Report 文本}
                        ...</action>

                <action>更新 {workflow_status}：current_state = Non-Bug</action>
                <action>设置 current_phase_result = ABORT ...</action>
                <action>退出 phase（不再继续 step 5-9）</action>
            </check>
```

**新文**：

```xml
            <check if="判定为 Non-Bug（命中 Working-As-Designed / User-Misoperation / Environment-Specific / Known-Limitation / Duplicate 之一）">
                <action>生成 Non-Bug Resolution Report 文本：包含
                        - 判定类别（5 选 1）
                        - 判定依据（对应 Spec 条款 / 复现路径 / 环境快照锚点）
                        - 沟通建议（一段面向 reporter 的回复要点，便于 step-pause 用户决策）
                        - 改进建议（可选；如对应 UX 工单 / Feature Request / 文档改进）</action>

                <!-- v4.2 PR-3' / O21 / ADR-014：non_bug_context 是 D17 协议下编排器 case Non-Bug 的唯一数据源 -->
                <phase-abort state="Non-Bug"
                             fields='{"non_bug_context": "{report_text}"}'
                             reason="ADR-014"/>
            </check>
```

### §1.3 ABORT-D2 · P2 Curation-Failed（L178-187）

**原文**：4 个 `<action>`（更新 current_state + 设置 ABORT + 退出 phase + 协议说明）

**新文**：

```xml
                <case if="< 0.4">
                    <!-- v4.2 PR-3' / O21 / ADR-001：B1* 兜底，避免 stepsCompleted 错追加 -->
                    <phase-abort state="Curation-Failed" reason="ADR-001"/>
                </case>
```

### §1.4 ABORT-D3 · P3 step 2 纯 C 级证据阈值未通过（L39-44）

**原文**：4 个 `<action>`（列出补充项 + 更新 state + 设置 ABORT + 阶段结束）

**新文**：

```xml
        <check if="纯 C 级证据，阈值未通过">
            <action>列出需要补充的具体证据项</action>
            <!-- v4.2 PR-3' / O21 / ADR-001 -->
            <phase-abort state="Spec-Defining" reason="ADR-001"/>
        </check>
```

### §1.5 ABORT-D4 · P3 step 5 simple-single 升级（L77-87）

**原文**：1 个含 5 字段的多行 `<action>` + 设置 ABORT + 阶段结束

**新文**：

```xml
            <check if="反事实校验失败 或 最终置信度 < 0.70 或 出现新证据冲突">
                <!-- v4.2 PR-3' / O21 / ADR-015 -->
                <phase-abort state="RCA-Designing"
                             fields='{"fanout_mode": "medium-challenge",
                                      "reroute_reason": "simple_path_not_closed",
                                      "reroute_from_phase": "qa-root-cause",
                                      "reroute_target_phase": "qa-root-cause",
                                      "rca_retry_count": "+1"}'
                             reason="ADR-015"/>
            </check>
```

### §1.6 ABORT-D5 · P3 step 5 medium-challenge 升级（L116-126）

**新文**：

```xml
            <check if="challenger 出现 Critical 或 最终置信度 < 0.65">
                <!-- v4.2 PR-3' / O21 / ADR-015 -->
                <phase-abort state="RCA-Designing"
                             fields='{"fanout_mode": "complex-arbitrated",
                                      "reroute_reason": "medium_path_escalated",
                                      "reroute_from_phase": "qa-root-cause",
                                      "reroute_target_phase": "qa-root-cause",
                                      "rca_retry_count": "+1"}'
                             reason="ADR-015"/>
            </check>
```

### §1.7 ABORT-D6 · P3 step 5 complex-arbitrated 不收敛 → Human-Review（L167-178）

**新文**：

```xml
            <check if="对抗轮次超过 3 轮仍未收敛">
                <!-- v4.2 PR-3' / O21 / ADR-015 + ADR-014（Human-Review 协议触发） -->
                <phase-abort state="Human-Review"
                             fields='{"fanout_mode": "complex-arbitrated",
                                      "reroute_reason": "multi_view_non_convergent",
                                      "reroute_from_phase": "qa-root-cause",
                                      "reroute_target_phase": "qa-root-cause",
                                      "rca_retry_count": "+1"}'
                             reason="ADR-015"/>
            </check>
```

### §1.8 ABORT-D7 · P3 step 10 RCA-LowConfidence（L240-245）

**新文**：

```xml
        <check if="最终置信度 < 0.5">
            <!-- v4.2 PR-3' / O21 / ADR-001 + B1* 关键修复 -->
            <phase-abort state="RCA-LowConfidence"
                         fields='{"fanout_mode": "complex-arbitrated",
                                  "reroute_reason": "low_final_confidence",
                                  "reroute_from_phase": "qa-root-cause",
                                  "reroute_target_phase": "qa-root-cause",
                                  "rca_retry_count": "+1"}'
                         reason="ADR-001"/>
        </check>
```

### §1.9 ABORT-D8 · P6 step 6 失败回流（L82-114，特殊处理）

**特殊性**：原写法 3 个 `verification_failure_type` 子 case 各自写不同的 `current_state`（Fix-Designing / RCA-Designing / Human-Review），共用 1 个 ABORT 出口。本 PR **不重构** switch（避免 scope creep），仅在 switch 末尾用宏的"占位字面"形式替换"设置 ABORT + 阶段结束"两行。

**新文**（仅展示 switch 后的宏改写部分，3 个 case 内部保持原写法）：

```xml
        <check if="任一层未通过">
            <switch condition="{verification_failure_type}">
                <case if="design_insufficient">
                    <action>更新 {workflow_status}：current_state = Fix-Designing, ...</action>
                </case>
                <case if="root_cause_not_closed">
                    <action>更新 {workflow_status}：current_state = RCA-Designing, ...</action>
                </case>
                <case if="implementation_mismatch">
                    <action>更新 {workflow_status}：current_state = Fix-Designing, ...</action>
                </case>
                <default>
                    <action>更新 {workflow_status}：current_state = Human-Review</action>
                </default>
            </switch>

            <template-output file="{output_verification}" template="..."/>
            <action>更新 {config_source}：output_verification_report = {output_verification}</action>

            <!-- v4.2 PR-3' / O21 / ADR-001 / state 占位字面 = 沿用上文 switch 已写入的 current_state（详见 ADR-021 §2 落地纪要） -->
            <phase-abort state="{workflow_status}.current_state" reason="ADR-001"/>
        </check>
```

> **CI 兼容**：`check-phase-abort-structure.sh`（SCRIPT-N1）脚本第 3 段已含 `[[ ! "$state" =~ ^\{ ]]` 判断，跳过对占位字面的 enum 校验。

### §1.10 ABORT-D9 · P5 step 6 优先级 1（error-dump 存在 → Human-Review）（L121-127）

**原文**：

```121:127:mobile-qa-workflow/phases/p5-fix-impl.md
        <check if="{output_error_dump} 文件存在">
            <action>Execution-Status = Human-Review</action>
            <action>读取 error-dump.md，输出 Human-Review 通知</action>
            <action>更新 {workflow_status}: current_state = Human-Review</action>
            <action>current_phase_result = ABORT</action>
            <goto step="8"/>
        </check>
```

> **特殊性（v1.1 review 次要观察收口）**：P5 原写法用 `<goto step="8">` 跳到 step 8 失败收口段（仅一句话「保持当前阶段未完成」）。改宏后 **goto 删除**：宏第 4 步「退出本 phase」让 step 8 不可达；step 8 的语义已被宏 + 编排器 step 4 case Human-Review 路由完整覆盖。**step 8 整段保留作为文档说明**（不删除避免 scope creep；PR-7 可清理）。ABORT-D10 / ABORT-D11 同此模式。

**新文**：

```xml
        <check if="{output_error_dump} 文件存在">
            <action>Execution-Status = Human-Review</action>
            <action>读取 error-dump.md，输出 Human-Review 通知</action>
            <!-- v4.2 PR-3' / O21 / ADR-001 / goto step="8" 删除（宏第 4 步退出 phase 让 step 8 不可达） -->
            <phase-abort state="Human-Review" reason="ADR-001"/>
        </check>
```

### §1.11 ABORT-D10 · P5 step 6 优先级 2（code-fix 无 contract-checklist → Human-Review + Incomplete）（L140-146）

**新文**：

```xml
            <check if="Repair-Route = code-fix 且 {output_contract_checklist} 不存在">
                <action>Execution-Status = Incomplete</action>
                <action>标记 [MISSING-REQUIRED-ARTIFACT: contract-checklist.md]</action>
                <!-- v4.2 PR-3' / O21 / ADR-001 -->
                <phase-abort state="Human-Review" reason="ADR-001"/>
            </check>
```

### §1.12 ABORT-D11 · P5 step 6 优先级 3（两产物均不存在 → Human-Review + Incomplete）（L150-155）

**新文**：

```xml
        <check if="{output_impl_report} 文件不存在 且 {output_error_dump} 不存在">
            <action>Execution-Status = Incomplete</action>
            <!-- v4.2 PR-3' / O21 / ADR-001 -->
            <phase-abort state="Human-Review" reason="ADR-001"/>
        </check>
```

---

## §2 phase-complete 改写完整字面对照（COMP-D1 ~ D5，全部 Seg-1）

### §2.1 通用改写规约

每处 phase-complete 出口改写**强制**遵循：
1. **保留**业务计算与 `<template-output>` 不动
2. **合并**"current_state 写入" + "phase_history append（如有）" + "config 注册"为 1 行宏
3. 注释引用：`<!-- v4.2 PR-3' / O21 / ADR-021 -->`

> **未改写说明（P4 step 6 例外）**：P4 成功路径 `current_state = Fix-Implementing` 写入在内联 `<step-pause>` 的 `<option action="...">` 属性内（详见 `legacy-phase-step-pause-allowlist.txt:26`），不是 step 末的独立 `<action>`。本 PR 不重构内联 step-pause（D14 整改由 PR-6 完成）；P4 phase-complete 改写**留 PR-6**（在删除内联 step-pause 的同一 commit 内顺手改）。

### §2.2 COMP-D1 · P3 step 10 成功路径（L226-238，已在主文档示例）

详见主文档 §2.3.1。**注意**：保留原 `<template-output>` + 原 ADR-007 修订段注释；宏含 4 个属性（state / fields / append_history / update_config）。

### §2.3 COMP-D2 · P1 step 7 成功路径（L113-120）

**原文**：4 个 `<action>`（输出说明 + template-output + config 写入 + phase_meta 字段写入 + current_state 写入）

**新文**：

```xml
    <step n="7" goal="输出 Issue Card">
        <action>输出时须覆盖 issue-card 模板：「受理提交物」中注明系统判定场景（interactive / document）；「代码与文档上下文」完整；交互式可将多轮问答摘要写入「关键信息摘要」</action>
        <action>将 Issue_Boundary_Level, Boundary_Confidence, Boundary_Alternative, Runtime_Anchor_Availability 写入 Issue Card 的元数据区块</action>
        <template-output file="{output_file}" template="mobile-qa-workflow/templates/issue-card.md"/>

        <!-- v4.2 PR-3' / O21 / ADR-021：把"phase 元字段写回 + current_state 写入 + config 注册"3 个 action 合并为宏 -->
        <phase-complete state="Spec-Defining"
                        fields='{"Issue_Boundary_Level": "{Issue_Boundary_Level}",
                                 "Boundary_Confidence": "{Boundary_Confidence}",
                                 "Runtime_Anchor_Availability": "{Runtime_Anchor_Availability}"}'
                        update_config='{"output_issue_card": "{output_file}",
                                        "platform": "{platform}",
                                        "priority": "{priority}"}'/>
    </step>
```

### §2.4 COMP-D3 · P2 step 9 成功路径（L196-202）

**原文**：3 个 `<template-output>` + 1 个 config 更新 + 1 个 current_state 写入

**新文**：

```xml
    <step n="9" goal="输出产物">
        <template-output file="{workspace_folder}/context-curation-report.md" template="mobile-qa-workflow/templates/context-curation-report.md"/>
        <template-output file="{output_spec}" template="mobile-qa-workflow/templates/spec.md"/>
        <template-output file="{output_context_bundle}" template="mobile-qa-workflow/templates/context-bundle.md"/>

        <!-- v4.2 PR-3' / O21 / ADR-021 -->
        <phase-complete state="RCA-Designing"
                        update_config='{"output_curation_report": "{workspace_folder}/context-curation-report.md",
                                        "output_spec": "{output_spec}",
                                        "output_context_bundle": "{output_context_bundle}"}'/>
    </step>
```

### §2.5 COMP-D4 · P5 step 7 成功路径（L158-171，v1.1 review Finding #3 收口）

**原文**：4 个 `<action>` / `<check>`（impl-report 模板 + Coder 产物保护 + config 三字段写入 + current_state 写入）；其中 `output_contract_checklist` 在原文是「（若存在）」的条件写入语义。

**v1.1 修订（采纳 Finding #3 方案 A）**：宏 `update_config` 协议**没有**「按单 key 视运行时值跳过」机制，禁止把"若存在才写入"压进宏。**条件写入显式拆出宏外**，宏 `update_config` 仅含必写字段。

**新文**：

```xml
    <step n="7" goal="输出与状态流转">
        <action>确认 impl-report.md 中的 Execution-Status 和 Repair-Route 字段已正确填写</action>
        <check if="Repair-Route = non-code-fix 且 {output_file} 文件不存在">
            <template-output file="{output_file}" template="mobile-qa-workflow/templates/impl-report.md"/>
        </check>
        <check if="Repair-Route = code-fix">
            <action>保留 Coder Agent 已生成的 impl-report.md，禁止使用模板覆写实施结果</action>
        </check>

        <!-- v4.2 PR-3' / O21 / 条件写入显式拆出宏外（宏 update_config 不支持按单 key 跳过 / v1.1 review Finding #3） -->
        <check if="{output_contract_checklist} 文件存在">
            <action>更新 {config_source}：output_contract_checklist = {output_contract_checklist}</action>
        </check>

        <!-- v4.2 PR-3' / O21 / ADR-021 -->
        <phase-complete state="Verifying"
                        update_config='{"output_impl_report": "{output_file}"}'/>
    </step>
```

### §2.6 COMP-D5 · P6 step 8 成功完成路径（L125-136）

**原文**：3 个 `<check>` + `<action>`（PR/MR 生成分支）+ 1 个 current_state = Done

**新文**：

```xml
    <step n="8" goal="PR/MR 生成">
        <check if="{env_git} == true">
            <action>创建 PR：标题 fix: [一句话描述] (issue-{issue_id})；描述包含 RCA / Fix Design / Verification 链接。</action>
        </check>
        <check if="{env_git} == false">
            <action>输出 Code Review Summary 文档，供人工创建 PR 时使用。</action>
        </check>

        <!-- v4.2 PR-3' / O21 / ADR-021 + C5 收口 / Done 是工作流终态 -->
        <phase-complete state="Done"/>
    </step>
```

> **简化说明**：本宏不带 fields/append_history/update_config 任何附加属性；展开仅 = "更新 current_state = Done + 退出 phase"。编排器 step 4 case Done 接管输出最终摘要。

---

## §3 SP-N1 · `system-prompt.md` 顶部 ADR-021 展开规则插入（Seg-2 / 严格对齐原 PR-3 H2）

> **Seg 标注（v1.1 review Finding #4 收口）**：本 SP-N1 是 **sp 在 PR-3' Seg-2 中的唯一编辑**（CONTRACT-D2 已按 review Finding #1 撤销 — sp 内并不存在 Spec-Uncertain 相关的 `allowed_values=Confirm` / `spec_uncertain_choice=Confirm` 详写段可改写；详见主文档 §2.6 v1.1 修订）。归属 **Seg-2 commit**：附录 §3 与主文档 §2.6 SP-N1 段同 commit；revert Seg-2 时 sp 整体回退到 PR-2 合入态。

### §3.1 插入位置（精确锚点）

**插入位置**：`system-prompt.md` L86 后（即 `</core-rules>` 标签之后、`## 0.1 角色口径` 之前），新增 `## 0.2` 章节。

**操作**：在 L86 与 L88 之间插入空行 + `## 0.2 ...` 完整章节（约 28 行 markdown）。**禁止**修改 L87 之前任何字符；禁止修改 § 0.1 角色口径之后任何内容（保持 sp 其他段落零改动，便于 `git diff` 审查）。

### §3.2 插入文本完整版（28 行 markdown，逐字写入）

```markdown
## 0.2 Phase 出口宏标签展开规则（O21 / ADR-021 / v4.2 PR-3'）

> 本节为 Limited 平台（Dify / Coze / OpenAI Assistants 等）的兜底展开规则；Full 平台（Cursor / Trae）也建议保留作为 LLM 行为锚点。
> 任何 phase 文件（`mobile-qa-workflow/phases/**`）出现的 `<phase-abort>` / `<phase-complete>` 标签，LLM 必须按以下规则**原子展开**（每条 sub-action 必须在同一 LLM 输出轮次内全部执行，禁止跨轮次拆分）。

### `<phase-abort state="..." [fields="..."] [reason="..."] />` 4 步展开

1. `<action>更新 {workflow_status}：current_state = <state></action>`（**特例**：当 `state` 字面以 `{` 开头时，表示沿用本 step 内已写入的 current_state，不重新赋值，详见 ADR-021 §2 落地纪要）
2. `<action>更新 {workflow_status}：fields 内全部 key=value（特殊语法："+1" 表示对该字段自增 1）</action>`（仅当 `fields` 属性存在）
3. `<action>设置 current_phase_result = ABORT</action>`（**绝对禁止**漏写 — D1 协议依赖此变量决定 stepsCompleted 是否追加）
4. `<action>退出本 phase（编排器 step 4 case 接管，按 current_state 路由到对应 step-pause）</action>`

### `<phase-complete state="..." [fields="..."] [append_history="..."] [update_config="..."] />` 5 步展开

1. `<action>更新 {workflow_status}：current_state = <state></action>`
2. `<action>更新 {workflow_status}：fields 内全部 key=value</action>`（仅当 `fields` 属性存在）
3. `<action>更新 {workflow_status}.phase_history：append <append_history></action>`（仅当 `append_history` 属性存在；元素结构含 phase / timestamp / fanout_mode / note）
4. `<action>更新 {config_source}：update_config 内全部 key=value</action>`（仅当 `update_config` 属性存在）
5. `<action>退出本 phase（按 D1 默认 OK，编排器 step 4 追加本 phase 到 stepsCompleted）</action>`

### 绝对禁止清单

- ❌ 漏写 `<phase-abort>` 第 3 步 ABORT（违反 D1 → stepsCompleted 错误追加 → B1* 主链路 bug 复发）
- ❌ 把 `fields` 内字段拆出宏外单独写 `<action>` （违反原子性 → CI Check 15 报警）
- ❌ 在 `<phase-abort>` 与 `<phase-complete>` 之间互相嵌套（语义冲突 → 行为未定义）
- ❌ 跨 LLM 输出轮次拆分宏的 sub-action（每个宏必须在单轮内完成 4/5 步全部执行）
```

### §3.3 SP-N1 sp 编辑收敛纪律（v1.1 review Finding #1 收口）

**sp 在 PR-3' Seg-2 中的唯一编辑** = SP-N1（在 L86 后插入 § 0.2，约 28 行 markdown）。

**为何不再有 CONTRACT-D2**：v1.1 review Finding #1 静态核对发现，sp 内与 Spec-Uncertain 契约直接相关的 `allowed_values=Confirm` / `spec_uncertain_choice=Confirm` **均不存在** — ① ANCHOR-N1（L195）锚点之后的 L196 路由表行由 **PR-2** 已对齐为 `allowed_values=1|2|S`；② sp L260-275 P2 内联段（`step-pause title="Spec 存在歧义..."`）本就**不带** `[allowed_values=]` 标签，选项已是 `[1] {option_1}` / `[2] {option_2}` / `[S] Skip`。**因此 sp 不需要任何 `Confirm` → `1|2|S` 改写**；本 PR 中 `sp/core` 的 `1|2|S` 对齐责任分工为：sp 侧沿用 PR-2，core 侧由主文档 `CONTRACT-D1` 完成。

**diff 体积**：sp 改动总行数 = **28 行净增量**（仅 SP-N1）；CI Check 13（H1 守门）继续输出 PASS + notice（SP-N1 在 § 0.2 章节，不触及 ANCHOR-N1 窗口的 `allowed_values` 一致性校验）。

### §3.4 SP-N1 兼容性影响

- **Limited 平台收益**：原本依赖 ADR-021 ID 引用的 Limited 平台获得了 sp 内的完整展开规则，B2.5 H3"Limited 平台漏展开抽查"风险显著下降
- **Full 平台无影响**：Cursor / Trae 直接 load core-rules.xml，sp § 0.2 是冗余兜底，不会重复执行展开
- **PR-6 兼容**：PR-6 触发 `build-system-prompt.py` 首次构建时，生成器需识别 § 0.2 章节并保留（生成器策略：sp 内手维护章节用 `## 0.x` 编号，自动生成内容用 `## N.x` 编号 N≥1；§ 0.2 属于"core-rules 派生"，归入 L0/identity 输出片段，由 builder 函数 `build_l0_identity` 内联同款 28 行 markdown）— 本 PR 不交付 builder 适配，留 PR-6 同步

---

## §4 附录 changelog

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-04-21 | 初版。配套主文档 v1.1。包含 11 处 ABORT 完整字面对照（ABORT-D1 ~ D11，含新增 P5 三处 ABORT-D9~D11）+ 5 处 phase-complete 完整字面对照（COMP-D1 ~ D5，P4 因内联 step-pause 留 PR-6 改写）+ SP-N1 完整插入文本（28 行 markdown，插入到 sp L86 之后）。**严格对齐原 PR-3 README §6 DoD「全部出口」+ H2「sp 置顶完整展开规则」两项约束**。Seg 划分：§1 + §2 进 Seg-1 commit；§3 SP-N1 进 Seg-2 commit（与 CONTRACT-D2 同段，sp 一次性编辑）。 |
| **v1.1** | **2026-04-21** | **配套主文档 v1.2 收口** — ① §1.10 ABORT-D9 删除"保留 goto"句（与"新文已删 goto"代码对齐 / 主文档 review 次要观察）；② §2.5 COMP-D4 重写：`output_contract_checklist` 条件写入显式拆出宏外（保留 `<check>` 分支），宏 `update_config` 仅含 `output_impl_report` 一项（采纳主文档 v1.2 review Finding #3 方案 A，宏不支持按单 key 跳过）；③ §3 头部 Seg 标注 + 文档头部 L7-9 Seg 划分纪律统一为「§1+§2 进 Seg-1 / §3 进 Seg-2」唯一规则（采纳 v1.2 review Finding #4，原 v1.0 自相矛盾的"§3 也属 Seg-1"描述删除）；④ §3.3 重写：从「SP-N1 + CONTRACT-D2 双处编辑顺序」改为「SP-N1 sp 唯一编辑」+ 详述 CONTRACT-D2 撤销原因，并精确收窄为 Spec-Uncertain 相关 `Confirm` 契约字面、补齐 `PR-2（sp）/ CONTRACT-D1（core）` 的一致性责任分工（采纳主文档 v1.2 review Finding #1）。 |
