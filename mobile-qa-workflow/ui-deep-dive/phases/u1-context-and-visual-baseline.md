---
name: u1-context-and-visual-baseline
description: UI Deep-Dive Stage 1 — 视觉基线与设备环境重建
---

```xml
<workflow>
    <step n="1" goal="加载 UI 基线输入">
        <load target="mobile-qa-workflow/core/core-rules.xml" prompt="重新加载作为流程规范"/>
        <action>读取 issue_card、spec_file、context_bundle，重建设计稿、结构化视图树、设备差异与主题环境。</action>
    </step>
    <step n="2" goal="执行基线分析">
        <check if="{env_subagent} == true">
            <invoke-subagent subagent_type="ui-context-analyst" subagent_prompt="
                <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                <load target='mobile-qa-workflow/ui-deep-dive/agents/ui-context-analyst.md' prompt='加载角色定义'/>
                输出视觉基线、设备环境差异、关键结构化证据。"/>
        </check>
    </step>
</workflow>
```
