---
name: qa-root-cause
description: Phase 3 — 根因分析，通过动态 fan-out 与专项路由定位根因
---

# 参数
- workspace_folder：问题工作区路径
- config_source：配置文件路径

# 全局静态变量
- issue_card: '{workspace_folder}/issue-card.md'
- spec_file: '{workspace_folder}/spec.md'
- context_bundle: '{workspace_folder}/context-bundle.md'
- output_file: '{workspace_folder}/rca-report.md'
- workflow_status: '{workspace_folder}/workflow-status.yaml'

```xml
<workflow>
    <step n="1" goal="加载流程规范和上游产物">
        <load target="mobile-qa-workflow/core/core-rules.xml" prompt="重新加载作为流程规范"/>
        <action>读取 {issue_card}、{spec_file}、{context_bundle}、{workflow_status}</action>
    </step>

    <step n="2" goal="最小证据阈值检查">
        <action>检查 Context Bundle 证据质量：至少 1 条 A 级证据，或 2 条 B 级证据；分类 Spec 扩展模块 >= 50% 关键字段已填充。</action>
        <check if="纯 C 级证据，阈值未通过">
            <action>列出需要补充的具体证据项</action>
            <action>更新 {workflow_status}：current_state = Spec-Defining</action>
            <action>阶段结束，返回编排器</action>
        </check>
    </step>

    <step n="3" goal="Context Bundle 降维裁剪（Token 超限时）">
        <check if="上下文超过 80K tokens">
            <action>按 A 级证据 > Spec 核心字段 > B 级证据 > 函数级代码 > 高可疑 Commit > C 级证据 的顺序裁剪。</action>
        </check>
    </step>

    <step n="4" goal="边界驱动路由与复杂度读取">
        <action>读取 {issue_card} 中的 Issue_Boundary_Level，选择边界策略：EXACT_MR -> Strategy-DiffFocus；VERSION_RANGE -> Strategy-CommitDenoise；HISTORICAL_UNCLEAR -> Strategy-DynamicBottomUp。</action>
        <action>优先读取 {spec_file} 中 Analysis Complexity / Complexity Confidence / Suggested Fan-out Mode；若缺失则按分类、优先级、模块数、状态/并发特征回退推断。</action>
        <action>将最终判定写回 {workflow_status}：analysis_complexity、analysis_complexity_confidence、fanout_mode。</action>
        <check if="reroute_reason == verification_root_cause_not_closed 或 reroute_reason == multi_view_non_convergent">
            <action>强制覆盖 fanout_mode = complex-arbitrated</action>
        </check>
    </step>

    <step n="5" goal="执行 RCA 动态 Fan-out">
        <load target="mobile-qa-workflow/reference/reasoning-chain.md" prompt="加载推理链规范"/>
        <load target="mobile-qa-workflow/reference/platform-checklist.md" prompt="加载平台检查清单"/>
        <load target="mobile-qa-workflow/reference/analysis-strategies.md" prompt="加载动态 fan-out 策略知识库"/>

        <check if="fanout_mode == simple-single">
            <action>单视角执行 OVHSC 五步推理：OBSERVE -> HYPOTHESIZE -> VERIFY -> SCORE -> CHAIN。</action>
            <action>执行反事实校验；若发现更精确边界，则 current_state = Boundary-Refined。</action>
            <check if="反事实校验失败 或 最终置信度 < 0.70 或 出现新证据冲突">
                <action>更新 {workflow_status}：
                    - fanout_mode = medium-challenge
                    - reroute_reason = simple_path_not_closed
                    - reroute_from_phase = qa-root-cause
                    - reroute_target_phase = qa-root-cause
                    - rca_retry_count += 1
                </action>
                <action>阶段结束，返回编排器</action>
            </check>
        </check>

        <check if="fanout_mode == medium-challenge">
            <check if="{env_subagent} == true">
                <invoke-subagent subagent_type="investigator" subagent_prompt="
                    <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                    <load target='mobile-qa-workflow/agents/investigator.md' prompt='加载角色定义'/>
                    <load target='mobile-qa-workflow/reference/reasoning-chain.md' prompt='加载推理链规范'/>
                    <load target='mobile-qa-workflow/reference/platform-checklist.md' prompt='加载平台检查清单'/>
                    使用策略 {strategy_a} 执行 OVHSC 推理链，分析：
                    - spec_file: {spec_file}
                    - context_bundle: {context_bundle}
                    - config_source: {config_source}"/>
                <invoke-subagent subagent_type="challenger" subagent_prompt="
                    <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                    <load target='mobile-qa-workflow/agents/shared-challenger-base.md' prompt='加载共享 challenger 基座'/>
                    <load target='mobile-qa-workflow/agents/challenger.md' prompt='加载主流程 challenger 包装层'/>
                    scene = RCA
                    dimension_set = rca-5d
                    target_list = 所有 Investigator 结论
                    supporting_context = {spec_file}, {context_bundle}
                    conditional_dimensions = temporal-drift | activation（仅在触发条件成立时执行）
                    输出 Challenge Report，保留 confidence_impact 字段。"/>
            </check>
            <check if="{env_subagent} == false">
                <action>顺序模拟 Investigator + Challenger：使用 1 个主策略完成 OVHSC，再执行 `rca-5d` 质疑。</action>
            </check>
            <check if="challenger 出现 Critical 或 最终置信度 < 0.65">
                <action>更新 {workflow_status}：
                    - fanout_mode = complex-arbitrated
                    - reroute_reason = medium_path_escalated
                    - reroute_from_phase = qa-root-cause
                    - reroute_target_phase = qa-root-cause
                    - rca_retry_count += 1
                </action>
                <action>阶段结束，返回编排器</action>
            </check>
        </check>

        <check if="fanout_mode == complex-arbitrated">
            <check if="{env_subagent} == true">
                <invoke-subagent subagent_type="investigator" subagent_prompt="
                    <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                    <load target='mobile-qa-workflow/agents/investigator.md' prompt='加载角色定义'/>
                    <load target='mobile-qa-workflow/reference/reasoning-chain.md' prompt='加载推理链规范'/>
                    <load target='mobile-qa-workflow/reference/platform-checklist.md' prompt='加载平台检查清单'/>
                    使用策略 {strategy_a} 执行 OVHSC 推理链，分析 {spec_file}、{context_bundle}、{config_source}"/>
                <invoke-subagent subagent_type="investigator" subagent_prompt="
                    <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                    <load target='mobile-qa-workflow/agents/investigator.md' prompt='加载角色定义'/>
                    <load target='mobile-qa-workflow/reference/reasoning-chain.md' prompt='加载推理链规范'/>
                    <load target='mobile-qa-workflow/reference/platform-checklist.md' prompt='加载平台检查清单'/>
                    使用与 strategy_a 独立的策略 {strategy_b} 执行 OVHSC 推理链，分析 {spec_file}、{context_bundle}、{config_source}"/>
                <invoke-subagent subagent_type="challenger" subagent_prompt="
                    <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                    <load target='mobile-qa-workflow/agents/shared-challenger-base.md' prompt='加载共享 challenger 基座'/>
                    <load target='mobile-qa-workflow/agents/challenger.md' prompt='加载主流程 challenger 包装层'/>
                    scene = RCA
                    dimension_set = rca-5d
                    target_list = 所有 Investigator 结论
                    supporting_context = {spec_file}, {context_bundle}
                    输出带 confidence_impact 的 Challenge Report。"/>
                <invoke-subagent subagent_type="arbiter" subagent_prompt="
                    <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                    <load target='mobile-qa-workflow/agents/shared-arbiter-base.md' prompt='加载共享 arbiter 基座'/>
                    <load target='mobile-qa-workflow/agents/arbiter.md' prompt='加载主流程 arbiter 包装层'/>
                    scene = RCA
                    comparison_focus = root-cause convergence | challenge absorption | confidence calibration
                    candidate_set = 所有 Investigator 结论
                    challenge_reports = Challenger 输出
                    按共享公式输出 final_confidence。"/>
            </check>
            <check if="{env_subagent} == false">
                <action>顺序模拟 2 个 Investigator + Challenger + Arbiter。</action>
            </check>
            <check if="对抗轮次超过 3 轮仍未收敛">
                <action>更新 {workflow_status}：
                    - fanout_mode = complex-arbitrated
                    - reroute_reason = multi_view_non_convergent
                    - reroute_from_phase = qa-root-cause
                    - reroute_target_phase = qa-root-cause
                    - rca_retry_count += 1
                    - current_state = Human-Review
                </action>
                <action>阶段结束，返回编排器</action>
            </check>
        </check>
    </step>

    <step n="6" goal="专项子工作流路由决策">
        <action>评估是否需要专项：
            - 功能类且复杂度高，或涉及状态机 / 生命周期 / 缓存一致性 / 并发的复合冲突 -> functionality-deep-dive
            - UI/UX 类且问题涉及布局拓扑、异步重排、渲染时序、交互冲突 -> ui-deep-dive
        </action>
        <check if="满足 functionality-deep-dive 触发条件">
            <action>创建子工作区 {workspace_folder}/deep-dive/，更新 {workflow_status}：specialized_workflow.mode = functionality-deep-dive, specialized_workflow.status = DD-InProgress, specialized_workflow.sub_workspace = {workspace_folder}/deep-dive/, specialized_workflow.trigger_reason = functional_complexity_or_conflict</action>
            <load target="mobile-qa-workflow/functionality-deep-dive/core/workflow.xml" prompt="加载并执行功能疑难专项子工作流，传递参数：
                - config_source: {config_source}
                - workspace_folder: {workspace_folder}/deep-dive
                - issue_card: {issue_card}
                - spec_file: {spec_file}
                - context_bundle: {context_bundle}
                - workflow_status: {workspace_folder}/deep-dive/workflow-status.yaml"/>
        </check>
        <check if="满足 ui-deep-dive 触发条件">
            <action>创建子工作区 {workspace_folder}/ui-deep-dive/，更新 {workflow_status}：specialized_workflow.mode = ui-deep-dive, specialized_workflow.status = DD-InProgress, specialized_workflow.sub_workspace = {workspace_folder}/ui-deep-dive/, specialized_workflow.trigger_reason = ui_complexity_or_render_conflict</action>
            <load target="mobile-qa-workflow/ui-deep-dive/core/workflow.xml" prompt="加载并执行 UI Deep-Dive 子工作流，传递参数：
                - config_source: {config_source}
                - workspace_folder: {workspace_folder}/ui-deep-dive
                - issue_card: {issue_card}
                - spec_file: {spec_file}
                - context_bundle: {context_bundle}
                - workflow_status: {workspace_folder}/ui-deep-dive/workflow-status.yaml"/>
        </check>
    </step>

    <step n="7" goal="回注专项结论并合并 RCA">
        <check if="{workspace_folder}/deep-dive/deep-dive-summary.md 存在">
            <action>读取 {workspace_folder}/deep-dive/deep-dive-summary.md 与 functionality-deep-dive-rca.md，合并主 RCA；若专项与主路径一致则提升置信度，若冲突则以专项为更深输入并解释覆盖理由。</action>
            <action>更新 {workflow_status}：specialized_workflow.status = DD-Completed, specialized_workflow.merge_strategy = merged-into-main-rca</action>
        </check>
        <check if="{workspace_folder}/ui-deep-dive/ui-deep-dive-summary.md 存在">
            <action>读取 {workspace_folder}/ui-deep-dive/ui-deep-dive-summary.md 与 ui-deep-dive-rca.md，将布局 / 渲染 / 交互专项结论回注主 RCA。</action>
            <action>更新 {workflow_status}：specialized_workflow.status = DD-Completed, specialized_workflow.merge_strategy = merged-into-main-rca</action>
        </check>
    </step>

    <step n="8" goal="客户端-服务端边界判定（功能类/网络类）">
        <check if="主分类 == 功能 或 网络">
            <action>抓包/日志确认实际请求和响应内容，判定归属（客户端/服务端/契约歧义/跨端）；服务端问题则输出 Handoff。</action>
        </check>
    </step>

    <step n="9" goal="跨平台 Sub-Issue 判定">
        <check if="platform == Both 且根因指向平台特异性代码">
            <check if="{env_subagent} == true">
                <invoke-subagent subagent_type="investigator" subagent_prompt="[Android 分析] 独立分析 Android 端根因"/>
                <invoke-subagent subagent_type="investigator" subagent_prompt="[iOS 分析] 独立分析 iOS 端根因"/>
                <action>执行跨端 L2/L3 一致性对比</action>
            </check>
            <check if="{env_subagent} == false">
                <action>顺序执行：[Android 分析] -> [iOS 分析] -> 跨端一致性对比</action>
            </check>
        </check>
    </step>

    <step n="10" goal="输出 Root Cause Report">
        <template-output file="{output_file}" template="mobile-qa-workflow/templates/rca-report.md"/>
        <action>更新 {config_source}：output_rca_report = {output_file}</action>
        <check if="最终置信度 >= 0.5">
            <action>更新 {workflow_status}：current_state = Fix-Designing, reroute_reason = null, reroute_target_phase = null</action>
        </check>
        <check if="最终置信度 < 0.5">
            <action>更新 {workflow_status}：current_state = RCA-LowConfidence, fanout_mode = complex-arbitrated, reroute_reason = low_final_confidence, reroute_from_phase = qa-root-cause, reroute_target_phase = qa-root-cause, rca_retry_count += 1</action>
        </check>
    </step>
</workflow>
```
