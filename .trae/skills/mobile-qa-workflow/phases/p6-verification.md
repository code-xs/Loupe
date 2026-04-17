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
- output_verification: '{workspace_folder}/verification-report.md'
- output_knowledge: '{workspace_folder}/knowledge-card.md'
- workflow_status: '{workspace_folder}/workflow-status.yaml'

```xml
<workflow>
    <step n="1" goal="加载流程规范和上游产物">
        <load target="mobile-qa-workflow/core/core-rules.xml" prompt="重新加载作为流程规范"/>
        <action>读取 {spec_file}、{fix_design}、{impl_report}</action>
    </step>

    <step n="2" goal="L1 — Spec 静态符合性验证">
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
        <check if="L1 + L2 + L3-Static 全部通过">
            <action>验证通过，继续生成 Knowledge Card</action>
        </check>
        <check if="任一层未通过">
            <action>列出失败项，附修复方向建议</action>
            <action>更新 {workflow_status}：current_state = Fix-Designing（回退）</action>
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
