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
        <action>读取 {spec_file}、{context_bundle}，如存在则读取 {environment_factor_report}</action>
    </step>

    <step n="2" goal="逆向状态机绘制">
        <action>定位所有相关的状态变量、Enum、Sealed Class、业务状态节点</action>
        <action>输出状态定义、状态转移、孤岛状态与非法跳转</action>
    </step>

    <step n="3" goal="数据流污点追踪与不可变性审查">
        <action>从数据源到消费端逐层追踪核心 Data Model 的流转路径</action>
        <action>识别异步闭包、回调、缓存更新中不可变性被破坏的位置</action>
        <action>若无法精确到代码行号，标记 [Line-Uncertain] 并说明依据</action>
    </step>

    <step n="4" goal="输出状态拓扑报告">
        <template-output file="{output_file}" template="mobile-qa-workflow/functionality-deep-dive/templates/deep-dive-topology.md"/>
        <action>更新 {config_source}：output_topology_report = {output_file}</action>
        <action>更新 {workflow_status}：current_state = DD-InProgress</action>
    </step>
</workflow>
```
