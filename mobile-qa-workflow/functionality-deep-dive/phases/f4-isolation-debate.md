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
- max_debate_rounds: 3

```xml
<workflow>
    <step n="1" goal="加载规范和专项产物">
        <load target="mobile-qa-workflow/core/core-rules.xml" prompt="重新加载作为流程规范"/>
        <load target="mobile-qa-workflow/functionality-deep-dive/reference/isolation-patterns.md" prompt="加载隔离诊断模式参考"/>
        <action>读取 {topology_report}、{concurrency_report}，如存在则读取 {environment_factor_report}</action>
    </step>

    <step n="2" goal="隔离诊断与假设生成">
        <action>基于三份专项报告执行控制变量推演：
            - **Mock 隔离**：替换外部依赖，确认功能路径是否独立异常
            - **断网隔离**：排除网络时序干扰
            - **缓存隔离**：清空本地缓存，观察行为差异
            - **状态隔离**：从已知正常状态强制进入可疑状态，观察转移结果
            - **逻辑隔离**：通过 Feature Flag 或条件编译隔离可疑模块
        </action>
        <action>形成候选根因集合：
            - Primary Root Cause Candidates（主根因候选，≤ 3 个）
            - Contributing Factor Candidates（贡献因子候选）
            每个候选必须关联到 topology_report 或 concurrency_report 中的具体发现</action>
    </step>

    <step n="3" goal="多 Agent 对抗与仲裁">
        <action>初始化对抗轮次：debate_round = 1</action>

        <check if="{env_subagent} == true">
            <invoke-subagent subagent_type="investigator" subagent_prompt="
                <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                <load target='mobile-qa-workflow/functionality-deep-dive/agents/state-analyst.md' prompt='加载状态分析专家角色作为补充视角'/>
                使用功能疑难专项视角，结合状态拓扑与时序分析结论，执行隔离推演：
                1. 对每个主根因候选执行控制变量推导
                2. 验证候选根因能否完整解释状态异常和时序窗口
                3. 输出可证伪的根因候选排序
                - topology_report: {topology_report}
                - concurrency_report: {concurrency_report}
                - config_source: {config_source}"/>

            <invoke-subagent subagent_type="challenger" subagent_prompt="
                <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                <load target='mobile-qa-workflow/functionality-deep-dive/agents/challenger.md' prompt='加载功能疑难专项质疑员角色'/>
                场景: 功能疑难专项质疑
                对当前候选根因执行七维质疑协议：
                因果充分性 / 因果必要性 / 证据可靠性 / 状态机一致性 / 生命周期盲区 / 缓存一致性攻击 / 并发时序漏洞
                - config_source: {config_source}"/>

            <invoke-subagent subagent_type="arbiter" subagent_prompt="
                <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                <load target='mobile-qa-workflow/functionality-deep-dive/agents/arbiter.md' prompt='加载功能疑难专项仲裁员角色'/>
                场景: 功能疑难专项仲裁
                汇总隔离分析结论和质疑结果，执行：
                收敛性判断 → 质疑吸收 → 主根因裁定 → 贡献因子定级 → 置信度校准
                final_confidence = base_score × convergence_factor × challenge_survival_rate
                - config_source: {config_source}"/>
        </check>

        <check if="{env_subagent} == false">
            <action>【单对话降级模式】顺序模拟三角色分析：

                【Investigator — 隔离推演】
                结合状态拓扑与时序分析结论，对每个主根因候选执行控制变量推导，
                验证候选根因能否完整解释状态异常和时序窗口，输出可证伪的根因候选排序。

                【Challenger — 七维质疑】
                对每个候选根因执行：因果充分性 / 因果必要性 / 证据可靠性 /
                状态机一致性 / 生命周期盲区 / 缓存一致性 / 并发时序漏洞

                【Arbiter — 专项仲裁】
                收敛性判断 → 质疑吸收 → 主根因裁定 → 贡献因子定级 → 置信度校准
            </action>
        </check>

        <check if="Arbiter 裁定未收敛且 debate_round &lt; {max_debate_rounds}">
            <action>debate_round += 1，基于 Arbiter 反馈调整假设后重新执行对抗</action>
            <goto step="3"/>
        </check>

        <check if="debate_round >= {max_debate_rounds} 且仍未收敛">
            <action>Arbiter 强制降级裁定：选择当前最优候选，置信度降为 Low</action>
            <action>标记 forced_convergence = true</action>
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
            <action>更新 {workflow_status}：current_state = DD-Completed, artifacts += [functionality-deep-dive-rca.md, deep-dive-summary.md]</action>
        </check>
    </step>
</workflow>
```
