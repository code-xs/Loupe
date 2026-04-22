---
name: f3-temporal-correlation
description: Stage 3 — 时序对齐与竞态剖析
---

# 参数
- workspace_folder：子工作区路径
- config_source：配置文件路径
- context_bundle：Context Bundle 文件路径
- topology_report：状态拓扑报告路径（可选）

# 全局静态变量
- output_file: '{workspace_folder}/concurrency-analysis-report.md'

```xml
<workflow>
    <step n="1" goal="加载规范和输入产物">
        <load target="mobile-qa-workflow/core/core-rules.xml" prompt="重新加载作为流程规范"/>
        <load target="mobile-qa-workflow/functionality-deep-dive/reference/race-condition-patterns.md" prompt="加载竞态条件常见模式参考"/>
        <action>读取 {context_bundle}，如存在则读取 {topology_report}</action>
    </step>

    <step n="2" goal="建立统一时间轴与竞态扫描">
        <check if="{env_subagent} == true">
            <invoke-subagent subagent_type="deep-dive-race-and-isolation-analyst" subagent_prompt="
                <load target='mobile-qa-workflow/core/core-rules-subagent.xml' prompt='加载流程规范'/>
                <load target='mobile-qa-workflow/functionality-deep-dive/agents/deep-dive-race-and-isolation-analyst.md' prompt='加载角色定义'/>
                <load target='mobile-qa-workflow/functionality-deep-dive/reference/race-condition-patterns.md' prompt='加载竞态条件常见模式参考'/>
                mode = temporal-correlation
                输出统一时间轴、竞态窗口、共享资源读写点、复现建议，并标记 [Race-Confirmed] 或 [Race-Suspected]。"/>
        </check>
        <check if="{env_subagent} == false">
            <action>主 Agent 执行时序对齐与竞态扫描，输出时间精度、共享资源风险与复现建议。</action>
        </check>
    </step>

    <step n="3" goal="按需输出独立报告">
        <check if="deep_dive_optional_artifacts.concurrency_analysis_report == true">
            <template-output file="{output_file}" template="mobile-qa-workflow/functionality-deep-dive/templates/concurrency-analysis-report.md"/>
            <action>更新 {config_source}：output_concurrency_report = {output_file}</action>
            <action>更新 {workflow_status}：current_state = DD-InProgress, artifacts += [concurrency-analysis-report.md]</action>
        </check>
        <check if="deep_dive_optional_artifacts.concurrency_analysis_report != true">
            <action>将并发分析内容保留供 F4 回注到 RCA 附录，不强制独立落盘。</action>
            <action>更新 {workflow_status}：current_state = DD-InProgress</action>
        </check>
    </step>
</workflow>
```
