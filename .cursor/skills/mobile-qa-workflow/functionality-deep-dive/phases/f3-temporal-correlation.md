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
        <load target="mobile-qa-workflow/functionality-deep-dive/reference/race-condition-patterns.md" prompt="加载竞态条件常见模式参考"/>
        <action>读取 {context_bundle} 和 {topology_report}</action>
    </step>

    <step n="2" goal="建立统一时间轴与竞态扫描">
        <check if="{env_subagent} == true">
            <invoke-subagent subagent_type="temporal-analyst" subagent_prompt="
                <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                <load target='mobile-qa-workflow/functionality-deep-dive/agents/temporal-analyst.md' prompt='加载角色定义'/>
                <load target='mobile-qa-workflow/functionality-deep-dive/reference/race-condition-patterns.md' prompt='加载竞态条件常见模式参考'/>
                执行时序对齐与竞态分析：
                1. 对齐用户操作、网络回调、线程/协程恢复点、生命周期回调
                2. 依据证据可用性标注时间精度：Microsecond / Millisecond / Order-Only
                3. 定位共享资源读写点、锁保护、原子性缺失和先读后写漏洞
                4. 结合状态拓扑中的脏写点和非法跳转，识别时序触发条件
                5. 输出高风险竞态窗口，并给出高概率复现路径与强制复现建议
                - context_bundle: {context_bundle}
                - topology_report: {topology_report}
                - config_source: {config_source}"/>
        </check>

        <check if="{env_subagent} == false">
            <action>【单对话降级模式】执行时序对齐与竞态分析：
                1. 对齐用户操作、网络回调、线程/协程恢复点、生命周期回调
                2. 依据证据可用性标注时间精度：Microsecond / Millisecond / Order-Only
                3. 定位共享资源读写点、锁保护、原子性缺失和先读后写漏洞
                4. 输出高风险竞态窗口，并给出高概率复现路径与强制复现建议</action>
        </check>
    </step>

    <step n="3" goal="竞态窗口与状态拓扑交叉验证">
        <action>将竞态窗口与 F2 状态拓扑中的关键转移交叉验证：
            - 竞态窗口是否发生在状态转移的守卫检查期间？
            - 非法跳转是否由时序漏洞导致？
            - 将时序敏感的脏写点标记为 [Race-Confirmed] 或 [Race-Suspected]
        </action>
    </step>

    <step n="4" goal="输出并发分析报告">
        <template-output file="{output_file}" template="mobile-qa-workflow/functionality-deep-dive/templates/concurrency-analysis-report.md"/>
        <action>更新 {config_source}：output_concurrency_report = {output_file}</action>
        <action>更新 {workflow_status}：current_state = DD-InProgress, artifacts += [concurrency-analysis-report.md]</action>
    </step>
</workflow>
```
