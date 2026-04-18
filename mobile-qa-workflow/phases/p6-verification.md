---
name: qa-verification
description: Phase 6 — 验证与闭环，执行三层验证模型并生成 Knowledge Card
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
<workflow>
    <step n="1" goal="加载流程规范和上游产物">
        <load target="mobile-qa-workflow/core/core-rules.xml" prompt="重新加载作为流程规范"/>
        <action>读取 {spec_file}、{fix_design}、{impl_report}</action>
        <action>从 {impl_report} 元信息区提取 Repair-Route 和 Execution-Status 字段</action>
    </step>

    <step n="2" goal="L1 — Spec 静态符合性验证 + 契约溯源交叉验证">
        <!-- V3 新增：Repair-Route 三分支判定 -->
        <switch condition="Repair-Route">
            <case if="code-fix">
                <check if="contract-checklist.md 存在">
                    <!-- 契约溯源交叉验证 -->
                    <action>逐条验证 contract-checklist.md 中的溯源记录：
                        - 源文件路径是否真实存在
                        - 行号/位置引用是否准确
                        - 期望值与实际值是否匹配
                        - 溯源记录条数是否 ≥ fix-design 中跨模块引用数
                    </action>
                    <action>异常等级映射：
                        - **PASS**：所有溯源项匹配状态均为 ✅
                        - **WARNING**（SUSPICIOUS）：存在标记为「待确认」的项，但无明确不匹配
                        - **FAIL**（INSUFFICIENT）：溯源记录条数 < fix-design 跨模块引用数
                        - **FAIL**（MISMATCH）：存在期望值与实际值不匹配的项
                        - **FAIL**（MISSING）：溯源记录为空或关键字段缺失
                    </action>
                </check>
                <check if="contract-checklist.md 不存在">
                    <action>标记 [MISSING-REQUIRED-ARTIFACT]: contract-checklist.md</action>
                    <action>L1 判定结果 = FAIL（code-fix 路径必须提供契约溯源检查清单）</action>
                    <goto step="6"/>
                </check>
            </case>
            <case if="non-code-fix">
                <action>契约溯源交叉验证 = SKIPPED（非代码修复路径，无需溯源验证）</action>
            </case>
        </switch>

        <!-- 原有 L1 验证逻辑 -->
        <check if="Impl Report 为远端变更指令">
            <action>验证指令内容是否完整覆盖 Spec 差异，配置下发条件是否正确，是否需要灰度等。</action>
            <goto step="5"/>
        </check>
        <action>通过 AI 代码走查，对照 Spec Document 逐条验证：
            - 逐条验证每个 Expected Behavior 是否被代码满足（引用具体代码行 + 逻辑推导）
            - 逐条验证每个 Invariant 是否被维护
            - 验证方式：静态代码分析（不需要运行时）
        </action>
    </step>

    <step n="3" goal="L2 — 静态影响面 & 回归安全性验证">
        <action>
            - 基于调用图分析修改函数的上下游影响范围
            - 确认没有破坏关键不变量
            - 对照 Fix Design 中的回归测试设计逐项核对
            - 验证跨平台一致性（代码逻辑层面）
        </action>
    </step>

    <step n="4" goal="L3-Static — 静态发布质量验证">
        <action>
            - [ ] Lint Error 数未增加（对比 Impl Report 中的验证结果）
            - [ ] 新增 Lint Warning 均已列出并评估可接受性
            - [ ] API 最低版本合规
            - [ ] 无新增明显安全问题
        </action>
    </step>

    <step n="5" goal="L3-Dynamic 标注（不阻塞闭环）">
        <action>以下指标标注 [Pending-CI]，由 CI 流水线或真机测试补充：
            - 关键链路性能（P95）
            - 内存占用（Heap Dump）
            - Crash Free Rate（发布后 APM 监控）
        </action>
    </step>

    <step n="6" goal="验证判定">
        <action>若存在失败项，先进行失败分类并写回 {workflow_status}：
            - design_insufficient：修复方案覆盖不足、风险论证不完整、回归设计缺失
            - root_cause_not_closed：修复后仍无法闭合原始因果链，或验证暴露新的上游根因缺口
            - implementation_mismatch：方案正确但实现与设计不一致或落地遗漏
        </action>
        <check if="L1 + L2 + L3-Static 全部通过">
            <action>更新 {workflow_status}：verification_failure_type = null, reroute_reason = null, reroute_target_phase = null</action>
            <action>验证通过，继续生成 Knowledge Card</action>
        </check>
        <check if="任一层未通过">
            <action>列出失败项，附修复方向建议</action>
            <switch condition="{verification_failure_type}">
                <case if="design_insufficient">
                    <action>更新 {workflow_status}：
                        - current_state = Fix-Designing
                        - reroute_reason = verification_design_insufficient
                        - reroute_from_phase = qa-verification
                        - reroute_target_phase = qa-fix-design
                        - fix_retry_count += 1
                    </action>
                </case>
                <case if="root_cause_not_closed">
                    <action>更新 {workflow_status}：
                        - current_state = RCA-InProgress
                        - verification_failure_type = root_cause_not_closed
                        - fanout_mode = escalate-required
                        - reroute_reason = verification_root_cause_not_closed
                        - reroute_from_phase = qa-verification
                        - reroute_target_phase = qa-root-cause
                        - rca_retry_count += 1
                    </action>
                </case>
                <case if="implementation_mismatch">
                    <action>更新 {workflow_status}：
                        - current_state = Fix-Designing
                        - reroute_reason = verification_implementation_mismatch
                        - reroute_from_phase = qa-verification
                        - reroute_target_phase = qa-fix-design
                        - fix_retry_count += 1
                    </action>
                </case>
                <default>
                    <action>更新 {workflow_status}：current_state = Human-Review</action>
                </default>
            </switch>
            <action>阶段结束，返回编排器</action>
        </check>
    </step>

    <step n="7" goal="输出 Verification Report">
        <template-output file="{output_verification}" template="mobile-qa-workflow/templates/verification-report.md"/>
        <action>更新 {config_source}：output_verification_report = {output_verification}</action>
    </step>

    <step n="8" goal="生成 Knowledge Card">
        <action>将具体实例的根因、修复模式抽象为可迁移的通用模式</action>
        <template-output file="{output_knowledge}" template="mobile-qa-workflow/templates/knowledge-card.md"/>
        <action>更新 {config_source}：output_knowledge_card = {output_knowledge}</action>
    </step>

    <step n="9" goal="PR/MR 生成">
        <check if="{env_git} == true">
            <action>创建 PR：
                标题：fix: [一句话描述] (issue-{issue_id})
                描述：Root Cause 摘要 + Fix Design 摘要 + Verification Report 链接
            </action>
        </check>
        <check if="{env_git} == false">
            <action>输出 Code Review Summary 文档，供人工创建 PR 时使用</action>
        </check>
        <action>更新 {workflow_status}：current_state = Closed</action>
    </step>
</workflow>
```
