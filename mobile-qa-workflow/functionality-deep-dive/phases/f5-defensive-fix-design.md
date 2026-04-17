---
name: f5-defensive-fix-design
description: Stage 5 — 防御性修复与架构演进建议，输出功能疑难问题的附录修复设计
---

# 参数
- workspace_folder：子工作区路径
- config_source：配置文件路径
- deep_dive_rca：专项 RCA 文件路径
- topology_report：状态拓扑报告路径
- concurrency_report：并发分析报告路径

# 全局静态变量
- output_file: '{workspace_folder}/defensive-fix-design.md'

```xml
<workflow>
    <step n="1" goal="加载专项 RCA 与重型产物">
        <load target="mobile-qa-workflow/core/core-rules.xml" prompt="重新加载作为流程规范"/>
        <action>读取 {deep_dive_rca}、{topology_report}、{concurrency_report}</action>
    </step>

    <step n="2" goal="生成防御性修复附录">
        <check if="{env_subagent} == true">
            <invoke-subagent subagent_type="defensive-fix-architect" subagent_prompt="
                <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                <load target='mobile-qa-workflow/functionality-deep-dive/agents/defensive-fix-architect.md' prompt='加载角色定义'/>
                基于专项 RCA 设计防御性修复附录：
                1. 给出状态机加固、守卫条件补全和非法跳转封堵方案
                2. 设计生命周期感知处理与任务取消/恢复策略
                3. 设计竞态收敛、缓存一致性保护和熔断器/断言点
                4. 修复设计必须区分止血方案与长期演进方案，避免过度设计
                5. 评估修复适度性（Proportionality Review）
                - deep_dive_rca: {deep_dive_rca}
                - topology_report: {topology_report}
                - concurrency_report: {concurrency_report}
                - config_source: {config_source}"/>
        </check>

        <check if="{env_subagent} == false">
            <action>【单对话降级模式】基于专项 RCA 设计防御性修复附录：
                1. 给出状态机加固、守卫条件补全和非法跳转封堵方案
                2. 设计生命周期感知处理与任务取消/恢复策略
                3. 设计竞态收敛、缓存一致性保护和熔断器/断言点
                4. 修复设计必须区分止血方案与长期演进方案，避免过度设计
                5. 评估修复适度性（Proportionality Review）</action>
        </check>
    </step>

    <step n="3" goal="输出防御性修复附录">
        <template-output file="{output_file}" template="mobile-qa-workflow/functionality-deep-dive/templates/defensive-fix-design.md"/>
        <action>更新 {config_source}：output_defensive_fix_design = {output_file}</action>
        <action>更新 {workflow_status}：current_state = DD-Completed, artifacts += [defensive-fix-design.md]</action>
    </step>
</workflow>
```
