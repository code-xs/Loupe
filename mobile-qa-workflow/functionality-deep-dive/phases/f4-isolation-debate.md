---
name: f4-isolation-debate
description: Stage 4 — 隔离诊断与专项收敛，使用专项复合角色完成闭合 RCA
---

# 参数
- workspace_folder：子工作区路径
- config_source：配置文件路径
- environment_factor_report：环境因子报告路径（可选）
- topology_report：状态拓扑报告路径（可选）
- concurrency_report：并发分析报告路径（可选）

# 全局静态变量
- output_rca: '{workspace_folder}/functionality-deep-dive-rca.md'
- output_summary: '{workspace_folder}/deep-dive-summary.md'
- max_debate_rounds: 3

```xml
<workflow>
    <step n="1" goal="加载规范和专项产物">
        <load target="mobile-qa-workflow/core/core-rules.xml" prompt="重新加载作为流程规范"/>
        <load target="mobile-qa-workflow/functionality-deep-dive/reference/isolation-patterns.md" prompt="加载隔离诊断模式参考"/>
        <action>如存在则读取 {environment_factor_report}、{topology_report}、{concurrency_report}</action>
    </step>

    <step n="2" goal="隔离诊断与候选排序">
        <check if="{env_subagent} == true">
            <invoke-subagent subagent_type="deep-dive-race-and-isolation-analyst" subagent_prompt="
                <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                <load target='mobile-qa-workflow/functionality-deep-dive/agents/deep-dive-race-and-isolation-analyst.md' prompt='加载角色定义'/>
                <load target='mobile-qa-workflow/functionality-deep-dive/reference/isolation-patterns.md' prompt='加载隔离诊断模式参考'/>
                mode = isolation-debate
                执行 Mock / 断网 / 缓存 / 状态 / 逻辑隔离，形成主根因候选（<=3）与贡献因子候选排序，并解释时序窗口和状态异常闭环。"/>
        </check>
        <check if="{env_subagent} == false">
            <action>主 Agent 执行控制变量推演，形成候选根因排序与可证伪说明。</action>
        </check>
    </step>

    <step n="3" goal="专项质疑与仲裁收敛">
        <action>初始化 debate_round = 1</action>
        <check if="{env_subagent} == true">
            <invoke-subagent subagent_type="deep-dive-arbiter" subagent_prompt="
                <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                <load target='mobile-qa-workflow/agents/shared-challenger-base.md' prompt='加载共享 challenger 基座'/>
                <load target='mobile-qa-workflow/agents/shared-arbiter-base.md' prompt='加载共享 arbiter 基座'/>
                <load target='mobile-qa-workflow/functionality-deep-dive/agents/deep-dive-arbiter.md' prompt='加载专项收敛角色'/>
                scene = DEEP_DIVE
                dimension_set = deep-dive-7d
                target_list = 当前候选根因集合
                candidate_set = 当前候选根因集合
                challenge_reports = seven-dimension challenge
                comparison_focus = primary root cause selection | contributing factor grading | residual uncertainty
                输出七维质疑、质疑吸收、最终裁定、final_confidence、Need Human Review、Recommended Attachments。"/>
        </check>
        <check if="{env_subagent} == false">
            <action>顺序模拟专项七维质疑与最终裁定。</action>
        </check>
        <check if="Arbiter 裁定未收敛且 debate_round &lt; {max_debate_rounds}">
            <action>debate_round += 1，基于反馈调整候选后重新执行 step 3。</action>
            <goto step="3"/>
        </check>
        <check if="debate_round >= {max_debate_rounds} 且仍未收敛">
            <action>标记 forced_convergence = true，置信度降为 Low，并保留 Need Human Review = Yes。</action>
        </check>
    </step>

    <step n="4" goal="输出专项 RCA 与回注摘要">
        <template-output file="{output_rca}" template="mobile-qa-workflow/functionality-deep-dive/templates/functionality-deep-dive-rca.md"/>
        <template-output file="{output_summary}" template="mobile-qa-workflow/functionality-deep-dive/templates/deep-dive-summary.md"/>
        <action>更新 {config_source}：output_deep_dive_rca = {output_rca}, output_deep_dive_summary = {output_summary}</action>
        <check if="最终置信度 &lt; 0.5">
            <action>更新 {workflow_status}：current_state = DD-LowConfidence</action>
        </check>
        <check if="最终置信度 &gt;= 0.5">
            <action>更新 {workflow_status}：current_state = DD-Completed, artifacts += [functionality-deep-dive-rca.md, deep-dive-summary.md]</action>
        </check>
    </step>
</workflow>
```
