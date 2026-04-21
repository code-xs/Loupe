---
name: qa-verification
description: Phase 6 — 验证与闭环，执行失败分类并按类型回流 P3/P4
---

# 参数
- workspace_folder：问题工作区路径
- config_source：配置文件路径

# 全局静态变量
- spec_file: '{workspace_folder}/spec.md'
- fix_design: '{workspace_folder}/fix-design.md'
- impl_report: '{workspace_folder}/impl-report.md'
- contract_checklist: '{workspace_folder}/contract-checklist.md'
- output_verification: '{workspace_folder}/verification-report.md'
- output_knowledge: '{workspace_folder}/knowledge-card.md'
- workflow_status: '{workspace_folder}/workflow-status.yaml'

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
<workflow>
    <step n="1" goal="加载流程规范和上游产物">
        <load target="mobile-qa-workflow/core/core-rules.xml" prompt="重新加载作为流程规范"/>
        <action>读取 {spec_file}、{fix_design}、{impl_report}</action>
        <action>从 {impl_report} 元信息区提取 Repair-Route 和 Execution-Status 字段</action>
    </step>

    <step n="2" goal="L1 — Spec 静态符合性验证 + 契约溯源交叉验证">
        <switch condition="Repair-Route">
            <case if="code-fix">
                <check if="contract-checklist.md 存在">
                    <action>逐条验证 contract-checklist.md 中的溯源记录：源文件路径、定位、期望值与实际值、记录条数是否满足 fix-design 中跨模块引用数。</action>
                    <action>异常等级映射：PASS / WARNING / FAIL(INSUFFICIENT|MISMATCH|MISSING)。</action>
                </check>
                <check if="contract-checklist.md 不存在">
                    <action>标记 [MISSING-REQUIRED-ARTIFACT]: contract-checklist.md</action>
                    <action>L1 判定结果 = FAIL</action>
                    <goto step="6"/>
                </check>
            </case>
            <case if="non-code-fix">
                <action>契约溯源交叉验证 = SKIPPED（非代码修复路径）</action>
            </case>
        </switch>
        <check if="Impl Report 为远端变更指令">
            <action>验证指令是否完整覆盖 Spec 差异，配置下发条件是否正确，必要时是否灰度。</action>
            <goto step="5"/>
        </check>
        <action>通过 AI 代码走查，对照 Spec 逐条验证 Expected Behavior 与 Invariant。</action>
    </step>

    <step n="3" goal="L2 — 静态影响面 & 回归安全性验证">
        <action>基于调用图分析修改函数的上下游影响范围，确认没有破坏关键不变量，并对照 Fix Design 中的回归测试设计逐项核对。</action>
    </step>

    <step n="4" goal="L3-Static — 静态发布质量验证">
        <action>检查：Lint Error 数未增加、Warning 已评估、API 最低版本合规、无新增明显安全问题。</action>
    </step>

    <step n="5" goal="L3-Dynamic 标注（不阻塞闭环）">
        <action>以下指标标注 [Pending-CI]：关键链路性能（P95）、内存占用（Heap Dump）、Crash Free Rate。</action>
    </step>

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
                         本 case 写入 RCA-Designing：语义为"将状态机回退到 RCA 设计阶段，由 P3 step 1 起重入"，
                         与编排器 step 2/4 现有路由（按 reroute_target_phase = qa-root-cause）完全自洽，不引入新 case；
                         v3 字面残留的非枚举集状态值已收口替换。 -->
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
                 中间态/正态区分由模板内部按 verification_failure_type 是否为空切换段落（PR-6 落地），
                 PR-4 调用方仅传现有 file/template 两个属性，不引入 mode 属性（避免与 core-rules.xml
                 <template-output> 标签 DSL 漂移）。 -->
            <template-output file="{output_verification}" template="mobile-qa-workflow/templates/verification-report.md"/>
            <action>更新 {config_source}：output_verification_report = {output_verification}</action>

            <!-- B1*：P6 失败回流是 stop_state（current_state ∈ {Fix-Designing, RCA-Designing, Human-Review}），
                 按 D1 协议必须 ABORT；编排器 step 4 检测 ABORT 后不追加 qa-verification 到 stepsCompleted,
                 让回流目标 phase（qa-fix-design / qa-root-cause）能被重新执行。 -->
            <action>设置 current_phase_result = ABORT</action>
            <action>阶段结束，返回编排器</action>
        </check>
    </step>

    <step n="7" goal="输出 Verification Report 与 Knowledge Card">
        <template-output file="{output_verification}" template="mobile-qa-workflow/templates/verification-report.md"/>
        <action>更新 {config_source}：output_verification_report = {output_verification}</action>
        <template-output file="{output_knowledge}" template="mobile-qa-workflow/templates/knowledge-card.md"/>
        <action>更新 {config_source}：output_knowledge_card = {output_knowledge}</action>
    </step>

    <step n="8" goal="PR/MR 生成">
        <check if="{env_git} == true">
            <action>创建 PR：标题 fix: [一句话描述] (issue-{issue_id})；描述包含 RCA / Fix Design / Verification 链接。</action>
        </check>
        <check if="{env_git} == false">
            <action>输出 Code Review Summary 文档，供人工创建 PR 时使用。</action>
        </check>
        <!-- C5 收口延伸（与 P6-A6 同类）：current_state 终态必须落在 core/workflow-status-template.yaml
             权威枚举集内；Done 是工作流完成态对应的合法终值，与编排器 step 4 case Done 路由自洽；
             v3 字面残留的非枚举集终态值已收口替换。 -->
        <action>更新 {workflow_status}：current_state = Done</action>
    </step>
</workflow>
```
