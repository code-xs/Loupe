---
name: u4-ui-ruling
description: UI Deep-Dive Stage 4 — UI 专项裁定与回注摘要
---

# 全局静态变量
- output_rca: '{workspace_folder}/ui-deep-dive-rca.md'
- output_summary: '{workspace_folder}/ui-deep-dive-summary.md'

```xml
<workflow>
    <step n="1" goal="输出 UI 专项裁定">
        <load target="mobile-qa-workflow/core/core-rules.xml" prompt="重新加载作为流程规范"/>
        <check if="{env_subagent} == true">
            <invoke-subagent subagent_type="ui-deep-dive-arbiter" subagent_prompt="
                <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                <load target='mobile-qa-workflow/ui-deep-dive/agents/ui-deep-dive-arbiter.md' prompt='加载角色定义'/>
                汇总视觉基线、布局拓扑、渲染时序与交互分析，输出最终 UI 根因、关键证据、置信度和建议附件。"/>
        </check>
        <template-output file="{output_rca}" template="mobile-qa-workflow/ui-deep-dive/templates/ui-deep-dive-rca.md"/>
        <template-output file="{output_summary}" template="mobile-qa-workflow/ui-deep-dive/templates/ui-deep-dive-summary.md"/>
        <action>更新 {config_source}：output_ui_deep_dive_rca = {output_rca}, output_ui_deep_dive_summary = {output_summary}</action>
    </step>
</workflow>
```
