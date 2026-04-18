---
name: f1-context-reconstruction
description: Stage 1 — 环境与上下文重构，识别导致偶发功能异常的隐蔽环境因子
---

# 参数
- workspace_folder：子工作区路径
- config_source：配置文件路径
- issue_card：Issue Card 文件路径
- spec_file：Spec 文件路径
- context_bundle：Context Bundle 文件路径

# 全局静态变量
- output_file: '{workspace_folder}/environment-factor-report.md'

```xml
<workflow>
    <step n="1" goal="加载规范和输入产物">
        <load target="mobile-qa-workflow/core/core-rules.xml" prompt="重新加载作为流程规范"/>
        <load target="mobile-qa-workflow/functionality-deep-dive/reference/environment-factor-thresholds.md" prompt="加载环境因子阈值参考"/>
        <action>读取 {issue_card}、{spec_file}、{context_bundle}</action>
    </step>

    <step n="2" goal="执行环境与上下文重构">
        <check if="{env_subagent} == true">
            <invoke-subagent subagent_type="deep-dive-context-analyst" subagent_prompt="
                <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                <load target='mobile-qa-workflow/functionality-deep-dive/agents/deep-dive-context-analyst.md' prompt='加载角色定义'/>
                <load target='mobile-qa-workflow/functionality-deep-dive/reference/environment-factor-thresholds.md' prompt='加载环境因子阈值参考'/>
                重建环境因子、前后台切换、权限变更、系统资源回收、配置漂移，并输出环境基线与热点代码关联。"/>
        </check>
        <check if="{env_subagent} == false">
            <action>主 Agent 以降级模式执行环境因子重建，缺失项必须标 [Unavailable]。</action>
        </check>
    </step>

    <step n="3" goal="按需输出独立报告">
        <check if="emit_environment_factor_report == true">
            <template-output file="{output_file}" template="mobile-qa-workflow/functionality-deep-dive/templates/environment-factor-report.md"/>
            <action>更新 {config_source}：output_environment_factor_report = {output_file}</action>
            <action>更新 {workflow_status}：current_state = DD-InProgress, artifacts += [environment-factor-report.md]</action>
        </check>
        <check if="emit_environment_factor_report != true">
            <action>将环境因子内容保留供 F4 回注到 RCA 附录，不强制独立落盘。</action>
            <action>更新 {workflow_status}：current_state = DD-InProgress</action>
        </check>
    </step>
</workflow>
```
