---
name: f3-temporal-correlation
description: Stage 3 — 时序对齐与竞态剖析，识别偶发问题中的关键竞态窗口
---

# 参数
- workspace_folder：子工作区路径
- config_source：配置文件路径
- context_bundle：Context Bundle 文件路径
- topology_report：状态拓扑报告路径

# 全局静态变量
- output_file: '{workspace_folder}/concurrency-analysis-report.md'

```xml
<workflow>
    <step n="1" goal="加载规范和输入产物">
        <load target="mobile-qa-workflow/core/core-rules.xml" prompt="重新加载作为流程规范"/>
        <action>读取 {context_bundle} 和 {topology_report}</action>
    </step>

    <step n="2" goal="建立统一时间轴">
        <action>对齐用户操作、网络回调、线程/协程恢复点、生命周期回调</action>
        <action>依据证据可用性标注时间精度：Microsecond / Millisecond / Order-Only</action>
    </step>

    <step n="3" goal="扫描共享资源与竞态窗口">
        <action>定位共享资源读写点、锁保护、原子性缺失和先读后写漏洞</action>
        <action>输出高风险竞态窗口，并给出高概率复现路径与强制复现建议</action>
    </step>

    <step n="4" goal="输出并发分析报告">
        <template-output file="{output_file}" template="mobile-qa-workflow/functionality-deep-dive/templates/concurrency-analysis-report.md"/>
        <action>更新 {config_source}：output_concurrency_report = {output_file}</action>
        <action>更新 {workflow_status}：current_state = DD-InProgress</action>
    </step>
</workflow>
```
