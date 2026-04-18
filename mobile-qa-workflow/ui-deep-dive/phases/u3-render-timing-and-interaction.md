---
name: u3-render-timing-and-interaction
description: UI Deep-Dive Stage 3 — 渲染时序与交互分析
---

```xml
<workflow>
    <step n="1" goal="分析渲染时序与交互">
        <load target="mobile-qa-workflow/core/core-rules.xml" prompt="重新加载作为流程规范"/>
        <load target="mobile-qa-workflow/ui-deep-dive/reference/ui-patterns.md" prompt="加载 UI 模式库"/>
        <check if="{env_subagent} == true">
            <invoke-subagent subagent_type="ui-render-and-interaction-analyst" subagent_prompt="
                <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                <load target='mobile-qa-workflow/ui-deep-dive/agents/ui-render-and-interaction-analyst.md' prompt='加载角色定义'/>
                分析异步重排、动画、手势冲突与渲染回调窗口。"/>
        </check>
    </step>
</workflow>
