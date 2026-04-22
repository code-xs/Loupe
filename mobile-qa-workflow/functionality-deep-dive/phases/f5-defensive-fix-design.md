---
name: f5-defensive-fix-design
description: Stage 5 — 防御性修复附录，按需触发
---

# 参数
- workspace_folder：子工作区路径
- config_source：配置文件路径
- deep_dive_rca：专项 RCA 文件路径
- deep_dive_summary：专项摘要路径
- topology_report：状态拓扑报告路径（可选）
- concurrency_report：并发分析报告路径（可选）

# 全局静态变量
- output_file: '{workspace_folder}/defensive-fix-design.md'

```xml
<workflow>
    <step n="1" goal="加载专项 RCA 与摘要">
        <load target="mobile-qa-workflow/core/core-rules.xml" prompt="重新加载作为流程规范"/>
        <action>读取 {deep_dive_rca}、{deep_dive_summary}，如存在则读取 {topology_report} 与 {concurrency_report}</action>
    </step>

    <step n="2" goal="判定是否需要防御性附录">
        <check if="Need Defensive Fix != Yes 且 无高风险残余不确定性">
            <action>跳过附录生成，保留当前 RCA 结论即可。</action>
            <action>更新 {workflow_status}：current_state = DD-Completed</action>
            <action>阶段结束</action>
        </check>
    </step>

    <step n="3" goal="生成防御性修复附录">
        <check if="{env_subagent} == true">
            <invoke-subagent subagent_type="defensive-fix-architect" subagent_prompt="
                <load target='mobile-qa-workflow/core/core-rules-subagent.xml' prompt='加载流程规范'/>
                <load target='mobile-qa-workflow/functionality-deep-dive/agents/defensive-fix-architect.md' prompt='加载角色定义'/>
                基于专项 RCA 输出状态机加固、生命周期感知处理、竞态收敛与适度性评审，区分止血方案与长期方案。"/>
        </check>
        <check if="{env_subagent} == false">
            <action>主 Agent 以降级模式输出防御性附录。</action>
        </check>
    </step>

    <step n="4" goal="输出防御性修复附录">
        <template-output file="{output_file}" template="mobile-qa-workflow/functionality-deep-dive/templates/defensive-fix-design.md"/>
        <action>更新 {config_source}：output_defensive_fix_design = {output_file}</action>
        <action>更新 {workflow_status}：current_state = DD-Completed, artifacts += [defensive-fix-design.md]</action>
    </step>
</workflow>
```
