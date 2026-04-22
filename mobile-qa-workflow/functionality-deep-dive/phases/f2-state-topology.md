---
name: f2-state-topology
description: Stage 2 — 状态机拓扑与数据流还原
---

# 参数
- workspace_folder：子工作区路径
- config_source：配置文件路径
- spec_file：Spec 文件路径
- context_bundle：Context Bundle 文件路径
- environment_factor_report：环境因子报告路径（可选）

# 全局静态变量
- output_file: '{workspace_folder}/deep-dive-topology.md'

```xml
<workflow>
    <step n="1" goal="加载规范和输入产物">
        <load target="mobile-qa-workflow/core/core-rules.xml" prompt="重新加载作为流程规范"/>
        <load target="mobile-qa-workflow/functionality-deep-dive/reference/state-machine-patterns.md" prompt="加载状态机常见缺陷模式参考"/>
        <action>读取 {spec_file}、{context_bundle}，如存在则读取 {environment_factor_report}</action>
    </step>

    <step n="2" goal="逆向结构拓扑与数据流">
        <check if="{env_subagent} == true">
            <invoke-subagent subagent_type="deep-dive-structure-analyst" subagent_prompt="
                <load target='mobile-qa-workflow/core/core-rules-subagent.xml' prompt='加载流程规范'/>
                <load target='mobile-qa-workflow/functionality-deep-dive/agents/deep-dive-structure-analyst.md' prompt='加载角色定义'/>
                <load target='mobile-qa-workflow/functionality-deep-dive/reference/state-machine-patterns.md' prompt='加载状态机常见缺陷模式参考'/>
                逆向状态机、守卫条件、数据流、缓存写入链与非法跳转，并输出后续时序分析需要重点验证的热点。"/>
        </check>
        <check if="{env_subagent} == false">
            <action>主 Agent 执行状态机与数据流分析，无法精确到代码行时标 [Line-Uncertain]。</action>
        </check>
    </step>

    <step n="3" goal="按需输出独立报告">
        <check if="deep_dive_optional_artifacts.deep_dive_topology == true">
            <template-output file="{output_file}" template="mobile-qa-workflow/functionality-deep-dive/templates/deep-dive-topology.md"/>
            <action>更新 {config_source}：output_topology_report = {output_file}</action>
            <action>更新 {workflow_status}：current_state = DD-InProgress, artifacts += [deep-dive-topology.md]</action>
        </check>
        <check if="deep_dive_optional_artifacts.deep_dive_topology != true">
            <action>将状态拓扑内容保留供 F4 回注到 RCA 附录，不强制独立落盘。</action>
            <action>更新 {workflow_status}：current_state = DD-InProgress</action>
        </check>
    </step>
</workflow>
```
