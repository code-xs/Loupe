---
name: f2-state-topology
description: Stage 2 — 状态机拓扑与数据流还原，建立功能问题的全局结构视图
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

    <step n="2" goal="逆向状态机绘制与数据流追踪">
        <check if="{env_subagent} == true">
            <invoke-subagent subagent_type="state-analyst" subagent_prompt="
                <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                <load target='mobile-qa-workflow/functionality-deep-dive/agents/state-analyst.md' prompt='加载角色定义'/>
                <load target='mobile-qa-workflow/functionality-deep-dive/reference/state-machine-patterns.md' prompt='加载状态机常见缺陷模式参考'/>
                执行状态机逆向与数据流分析：
                1. 定位所有相关的状态变量、Enum、Sealed Class、业务状态节点
                2. 输出 Mermaid 状态图，含状态定义、状态转移、守卫条件
                3. 标记孤岛状态与非法跳转
                4. 从数据源到消费端逐层追踪核心 Data Model 的流转路径
                5. 识别异步闭包、回调、缓存更新中不可变性被破坏的位置
                6. 若无法精确到代码行号，标记 [Line-Uncertain] 并说明依据
                - spec_file: {spec_file}
                - context_bundle: {context_bundle}
                - environment_factor_report: {environment_factor_report}
                - config_source: {config_source}"/>
        </check>

        <check if="{env_subagent} == false">
            <action>【单对话降级模式】执行状态机逆向与数据流分析：
                1. 定位所有相关的状态变量、Enum、Sealed Class、业务状态节点
                2. 输出状态定义、状态转移、孤岛状态与非法跳转
                3. 从数据源到消费端逐层追踪核心 Data Model 的流转路径
                4. 识别异步闭包、回调、缓存更新中不可变性被破坏的位置
                5. 若无法精确到代码行号，标记 [Line-Uncertain] 并说明依据</action>
        </check>
    </step>

    <step n="3" goal="交叉验证与环境因子关联">
        <action>将状态拓扑发现与 F1 环境因子报告（如存在）交叉验证：
            - 环境因子是否直接触发了特定状态转移？
            - 资源压力是否导致了守卫条件的竞态失效？
        </action>
    </step>

    <step n="4" goal="输出状态拓扑报告">
        <template-output file="{output_file}" template="mobile-qa-workflow/functionality-deep-dive/templates/deep-dive-topology.md"/>
        <action>更新 {config_source}：output_topology_report = {output_file}</action>
        <action>更新 {workflow_status}：current_state = DD-InProgress, artifacts += [deep-dive-topology.md]</action>
    </step>
</workflow>
```
