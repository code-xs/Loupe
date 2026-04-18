---
name: qa-fix-impl
description: Phase 5 — 修复实施，路由判定 + Coder SubAgent 调用 + 文件哨兵验收
---

# 参数
- workspace_folder：问题工作区路径
- config_source：配置文件路径

# 全局静态变量
- spec_file: '{workspace_folder}/spec.md'
- fix_design: '{workspace_folder}/fix-design.md'
- defensive_fix_design: '{workspace_folder}/defensive-fix-design.md'
- output_file: '{workspace_folder}/impl-report.md'
- workflow_status: '{workspace_folder}/workflow-status.yaml'

```xml
<workflow>
    <step n="1" goal="加载流程规范和上游产物">
        <load target="mobile-qa-workflow/core/core-rules.xml" prompt="重新加载作为流程规范"/>
        <action>读取 {fix_design} 和 {spec_file}</action>
        <load target="mobile-qa-workflow/reference/platform-checklist.md" prompt="加载平台检查清单和 API 版本合规检查"/>
    </step>

    <step n="2" goal="专项修复附录加载（Functionality Deep-Dive 专项）">
        <action>读取 {workflow_status}，检查 specialized_workflow 状态</action>

        <check if="specialized_workflow.mode == 'functionality-deep-dive' 且 specialized_workflow.status ∈ {DD-Completed, Merged}">
            <action>【加载防御性修复设计】
                1. 读取 {defensive_fix_design}（可选文件，不存在则跳过本步骤）
                2. 解析防御性修复条目列表，按 priority 字段分级：
                   - priority: critical → 必须实现（阻断级，缺失则标记 impl 不完整）
                   - priority: recommended → 根据修复范围酌情实现
                   - priority: optional → 记录但不强制要求
                3. 将防御性修复条目作为补充实施要求，与主 Fix Design 合并
            </action>
            <load target="{defensive_fix_design}" optional="true"
                  context="功能专家深度分析产出的防御性修复设计方案，包含熔断器、状态断言、防御性守卫等架构鲁棒性建议"/>
        </check>

        <check if="specialized_workflow.mode == null 或 specialized_workflow.status 不在 {DD-Completed, Merged} 中">
            <action>无专项修复附录，跳过本步骤，继续标准实施流程</action>
        </check>
    </step>

    <step n="3" goal="工作区初始化">
        <check if="{env_git} == true">
            <action>执行 Git 初始化：
                git pull
                git checkout -b fix/ai-issue-{issue_id}
            </action>
            <action>更新 {config_source}：fix_branch = fix/ai-issue-{issue_id}</action>
            <critical>禁止在主干分支直接修改代码</critical>
        </check>
        <check if="{env_git} == false">
            <action>标注：无 Git 环境，修复代码将以完整代码块形式输出，注明文件路径和修改位置</action>
        </check>
    </step>

    <step n="4" goal="修复路由判定 + 输出路径初始化">
        <check if="Fix Design 指向远端漂移/跨端协调/配置下发">
            <action>记录 Repair-Route = non-code-fix</action>
            <action>执行【非代码修复实施分支】：
                - 输出变更服务端配置、回滚 AB 实验或协调后端的具体指令和参数清单。
                - 如果必须在客户端做兼容兜底，则仅实现兜底逻辑，并标注 [Remote-Drift-Fallback]。
            </action>
            <goto step="7"/>
        </check>
        <check if="Fix Design 指向客户端代码缺陷">
            <action>记录 Repair-Route = code-fix</action>
            <action>【输出路径初始化】
                1. 从 {config_source} 读取 {workspace_folder}
                2. 赋值：
                   {output_impl_report}        = {workspace_folder}/impl-report.md
                   {output_contract_checklist}  = {workspace_folder}/contract-checklist.md
                   {output_error_dump}          = {workspace_folder}/error-dump.md
                3. 将上述路径写入 {config_source}（若尚未赋值）
            </action>
        </check>
    </step>

    <step n="5" goal="调用 Coder SubAgent">
        <check if="{env_subagent} == true">
            <invoke-subagent subagent_type="coder-agent" subagent_prompt="
                <load target='mobile-qa-workflow/core/core-rules.xml'
                      prompt='加载流程规范'/>
                <load target='mobile-qa-workflow/agents/coder-agent.md'
                      prompt='加载角色定义'/>
                [输入文档]
                - fix-design: {fix_design}
                - spec: {spec_file}
                - defensive-fix-design: {defensive_fix_design}
                - config_source: {config_source}
                - workspace_folder: {workspace_folder}
            "/>
        </check>
        <check if="{env_subagent} == false">
            <action>【降级模式：主 Agent 内联执行 Coder Agent 四阶段工作流】
                <load target="mobile-qa-workflow/agents/coder-agent.md" prompt="加载角色定义，在当前对话中内联执行四阶段工作流"/>
            </action>
        </check>
    </step>

    <step n="6" goal="SubAgent 结果接收与状态更新">
        <action>按返回判定协议检查文件哨兵：</action>

        <!-- 优先级 1：error-dump 存在 → Human-Review -->
        <check if="{output_error_dump} 文件存在">
            <action>Execution-Status = Human-Review</action>
            <action>读取 error-dump.md，输出 Human-Review 通知</action>
            <action>更新 {workflow_status}: current_state = Human-Review</action>
            <action>current_phase_result = ABORT</action>
            <goto step="8"/>
        </check>

        <!-- 优先级 2：impl-report 存在 且 error-dump 不存在 -->
        <check if="{output_impl_report} 文件存在 且 {output_error_dump} 不存在">
            <check if="Repair-Route = code-fix 且 {output_contract_checklist} 存在">
                <action>Execution-Status = Success</action>
                <action>验证 contract-checklist.md 满足最小必填字段规范（5 项：溯源项、源文件、期望值、实际值、匹配状态）</action>
                <!-- Success → 允许流入 Step 7 -->
            </check>
            <check if="Repair-Route = non-code-fix">
                <action>Execution-Status = Success</action>
                <!-- Success → 允许流入 Step 7 -->
            </check>
            <check if="Repair-Route = code-fix 且 {output_contract_checklist} 不存在">
                <action>Execution-Status = Incomplete</action>
                <action>标记 [MISSING-REQUIRED-ARTIFACT: contract-checklist.md]</action>
                <action>更新 {workflow_status}: current_state = Human-Review</action>
                <action>current_phase_result = ABORT</action>
                <goto step="8"/>
            </check>
        </check>

        <!-- 优先级 3：两个产物均不存在 -->
        <check if="{output_impl_report} 文件不存在 且 {output_error_dump} 不存在">
            <action>Execution-Status = Incomplete</action>
            <action>更新 {workflow_status}: current_state = Human-Review</action>
            <action>current_phase_result = ABORT</action>
            <goto step="8"/>
        </check>
    </step>

    <step n="7" goal="输出与状态流转">
        <action>确认 impl-report.md 中的 Execution-Status 和 Repair-Route 字段已正确填写</action>
        <check if="Repair-Route = non-code-fix 且 {output_file} 文件不存在">
            <template-output file="{output_file}" template="mobile-qa-workflow/templates/impl-report.md"/>
        </check>
        <check if="Repair-Route = code-fix">
            <action>保留 Coder Agent 已生成的 impl-report.md，禁止使用模板覆写实施结果</action>
        </check>
        <action>更新 {config_source}：
            output_impl_report = {output_file}
            output_contract_checklist = {output_contract_checklist}（若存在）
        </action>
        <action>更新 {workflow_status}：current_state = Verifying</action>
    </step>

    <step n="8" goal="失败路径收口">
        <action>保持当前阶段未完成，等待 Human-Review 处理后重新进入 qa-fix-impl</action>
    </step>
</workflow>
```
