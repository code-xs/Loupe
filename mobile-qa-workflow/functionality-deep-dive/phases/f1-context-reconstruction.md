---
name: f1-context-reconstruction
description: Stage 1 — 环境与上下文重构，识别导致偶发功能异常的隐蔽环境因子
---

# 参数
- workspace_folder：子工作区路径
- config_source：配置文件路径
- issue_card：Issue Card 文件路径
- spec_file：Spec 文件路径
- context_bundle：Context Bundle 文件路径

# 全局静态变量
- output_file: '{workspace_folder}/environment-factor-report.md'

```xml
<workflow>
    <step n="1" goal="加载规范和输入产物">
        <load target="mobile-qa-workflow/core/core-rules.xml" prompt="重新加载作为流程规范"/>
        <load target="mobile-qa-workflow/functionality-deep-dive/reference/environment-factor-thresholds.md" prompt="加载环境因子阈值参考"/>
        <action>读取 {issue_card}、{spec_file}、{context_bundle}</action>
    </step>

    <step n="2" goal="重建极端环境因子">
        <check if="{env_subagent} == true">
            <invoke-subagent subagent_type="context-reconstructor" subagent_prompt="
                <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                <load target='mobile-qa-workflow/functionality-deep-dive/agents/context-reconstructor.md' prompt='加载角色定义'/>
                <load target='mobile-qa-workflow/functionality-deep-dive/reference/environment-factor-thresholds.md' prompt='加载环境因子阈值参考'/>
                执行环境与上下文重构：
                1. 增量检查异常窗口内的环境因子：LMK / Thermal / 网络抖动 / 丢包 / CPU / 磁盘 / GPU 压力
                2. 检查异常前 10 秒内是否发生：前后台切换、权限撤销、配置变更、系统资源回收
                3. 标注环境因子与代码位置的关联关系，但禁止给出修复方案
                4. 若相关证据缺失，明确记录 [Unavailable]，不得臆测填充
                - issue_card: {issue_card}
                - spec_file: {spec_file}
                - context_bundle: {context_bundle}
                - config_source: {config_source}"/>
        </check>

        <check if="{env_subagent} == false">
            <action>【单对话降级模式】执行环境因子重建：
                增量检查异常窗口内的环境因子：LMK / Thermal / 网络抖动 / 丢包 / CPU / 磁盘 / GPU 压力
                若相关证据缺失，明确记录 [Unavailable]，不得臆测填充</action>
        </check>
    </step>

    <step n="3" goal="审查生命周期与系统干预">
        <action>检查异常前 10 秒内是否发生：前后台切换、权限撤销、配置变更、系统资源回收</action>
        <action>允许标注环境因子与代码位置的关联关系，但禁止给出修复方案</action>
    </step>

    <step n="4" goal="输出环境因子报告">
        <template-output file="{output_file}" template="mobile-qa-workflow/functionality-deep-dive/templates/environment-factor-report.md"/>
        <action>更新 {config_source}：output_environment_factor_report = {output_file}</action>
        <action>更新 {workflow_status}：current_state = DD-InProgress, artifacts += [environment-factor-report.md]</action>
    </step>
</workflow>
```
