---
name: u2-layout-topology
description: UI Deep-Dive Stage 2 — 布局拓扑与约束分析
---

```xml
<workflow>
    <step n="1" goal="分析布局拓扑">
        <load target="mobile-qa-workflow/core/core-rules.xml" prompt="重新加载作为流程规范"/>
        <load target="mobile-qa-workflow/ui-deep-dive/reference/ui-patterns.md" prompt="加载 UI 模式库"/>
        <check if="{env_subagent} == true">
            <invoke-subagent subagent_type="ui-structure-analyst" subagent_prompt="
                <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                <load target='mobile-qa-workflow/ui-deep-dive/agents/ui-structure-analyst.md' prompt='加载角色定义'/>
                分析布局层级、约束关系、资源链和关键尺寸偏差。"/>
        </check>
    </step>
</workflow>
