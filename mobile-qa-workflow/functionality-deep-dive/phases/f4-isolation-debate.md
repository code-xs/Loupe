---
name: f4-isolation-debate
description: Stage 4 — 隔离诊断与多 Agent 对抗，收敛出主根因与贡献因子
---

# 参数
- workspace_folder：子工作区路径
- config_source：配置文件路径
- environment_factor_report：环境因子报告路径（可选）
- topology_report：状态拓扑报告路径
- concurrency_report：并发分析报告路径

# 全局静态变量
- output_rca: '{workspace_folder}/functionality-deep-dive-rca.md'
- output_summary: '{workspace_folder}/deep-dive-summary.md'

```xml
<workflow>
    <step n="1" goal="加载规范和专项产物">
        <load target="mobile-qa-workflow/core/core-rules.xml" prompt="重新加载作为流程规范"/>
        <action>读取 {topology_report}、{concurrency_report}，如存在则读取 {environment_factor_report}</action>
    </step>

    <step n="2" goal="隔离诊断与假设生成">
        <action>通过 Mock、断网、缓存隔离、逻辑隔离等方式做控制变量推演</action>
        <action>形成候选根因集合，并区分主根因候选与贡献因子候选</action>
    </step>

    <step n="3" goal="多 Agent 对抗与仲裁">
        <check if="{env_subagent} == true">
            <invoke-subagent subagent_type="general_purpose_task" subagent_prompt="使用功能疑难专项视角执行状态拓扑与时序分析复核，输出可证伪根因候选"/>
            <invoke-subagent subagent_type="general_purpose_task" subagent_prompt="作为 Challenger，对当前候选根因执行因果充分性、必要性、生命周期盲区、缓存一致性和并发时序漏洞质疑"/>
        </check>
        <action>收敛为 Primary Root Cause + Contributing Factors，并标注置信度与残余不确定性</action>
    </step>

    <step n="4" goal="输出专项 RCA 与回注摘要">
        <template-output file="{output_rca}" template="mobile-qa-workflow/functionality-deep-dive/templates/functionality-deep-dive-rca.md"/>
        <template-output file="{output_summary}" template="mobile-qa-workflow/functionality-deep-dive/templates/deep-dive-summary.md"/>
        <action>更新 {config_source}：output_deep_dive_rca = {output_rca}, output_deep_dive_summary = {output_summary}</action>
        <check if="最终置信度 &lt; 0.5">
            <action>更新 {workflow_status}：current_state = DD-LowConfidence</action>
        </check>
        <check if="最终置信度 &gt;= 0.5">
            <action>更新 {workflow_status}：current_state = DD-Completed</action>
        </check>
    </step>
</workflow>
```
