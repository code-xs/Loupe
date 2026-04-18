    ---
    name: qa-fix-design
    description: Phase 4 — 修复方案设计，按风险与置信度动态选择 proposer 模式
    ---

    # 参数
    - workspace_folder：问题工作区路径
    - config_source：配置文件路径

    # 全局静态变量
    - issue_card: '{workspace_folder}/issue-card.md'
    - spec_file: '{workspace_folder}/spec.md'
    - rca_report: '{workspace_folder}/rca-report.md'
    - deep_dive_summary: '{workspace_folder}/deep-dive/deep-dive-summary.md'
    - ui_deep_dive_summary: '{workspace_folder}/ui-deep-dive/ui-deep-dive-summary.md'
    - output_file: '{workspace_folder}/fix-design.md'
    - workflow_status: '{workspace_folder}/workflow-status.yaml'

    ```xml
    <workflow>
        <step n="1" goal="加载流程规范和上游产物">
            <load target="mobile-qa-workflow/core/core-rules.xml" prompt="重新加载作为流程规范"/>
            <action>读取 {issue_card}、{spec_file}、{rca_report}；若存在则读取 {deep_dive_summary} 与 {ui_deep_dive_summary}</action>
            <load target="mobile-qa-workflow/reference/fix-strategies.md" prompt="加载修复策略知识库"/>
        </step>

        <step n="2" goal="修复路径选择与策略分层">
            <critical>必须优先选择治本策略；治标策略仅在真因短期无法修改时使用，且必须说明原因</critical>
            <action>若根因涉及远端配置、服务端契约变更或第三方依赖漂移，优先选择跨端协调 / 远端修复策略，不可盲目修改客户端代码。</action>
            <action>综合根因置信度、修改范围、共享状态、并发/状态恢复风险与验证回流信息，输出：
                - fix_risk_level = low | medium | high
                - fix_strategy_mode = single-proposer | challenged-proposer | contested-arbitrated
            </action>
            <action>更新 {workflow_status}：
                - fix_risk_level = {fix_risk_level}
                - fix_strategy_mode = {fix_strategy_mode}
                - fanout_mode = {fix_strategy_mode}
                - reroute_reason = null
            </action>
        </step>

        <step n="3" goal="执行动态 Proposal Fan-out">
            <check if="fix_strategy_mode == single-proposer">
                <check if="{env_subagent} == true">
                    <invoke-subagent subagent_type="fix-proposer" subagent_prompt="
                        <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                        <load target='mobile-qa-workflow/agents/fix-proposer.md' prompt='加载角色定义'/>
                        <load target='mobile-qa-workflow/reference/fix-strategies.md' prompt='加载修复策略知识库'/>
                        [Single-Proposer] 基于 {rca_report}、{spec_file}、{issue_card}、{config_source} 输出单方案设计，完成四重论证与回归测试设计。"/>
                </check>
                <check if="{env_subagent} == false">
                    <action>主 Agent 独立完成单方案四重论证。</action>
                </check>
            </check>

            <check if="fix_strategy_mode == challenged-proposer">
                <check if="{env_subagent} == true">
                    <invoke-subagent subagent_type="fix-proposer" subagent_prompt="
                        <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                        <load target='mobile-qa-workflow/agents/fix-proposer.md' prompt='加载角色定义'/>
                        <load target='mobile-qa-workflow/reference/fix-strategies.md' prompt='加载修复策略知识库'/>
                        [Challenged-Proposer] 基于 {rca_report}、{spec_file}、{issue_card} 独立设计修复方案，完成四重论证与回归测试设计。"/>
                    <invoke-subagent subagent_type="challenger" subagent_prompt="
                        <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                        <load target='mobile-qa-workflow/agents/shared-challenger-base.md' prompt='加载共享 challenger 基座'/>
                        <load target='mobile-qa-workflow/agents/challenger.md' prompt='加载主流程 challenger 包装层'/>
                        scene = FIX
                        dimension_set = fix-4a
                        target_list = 当前 Fix-Proposer 方案
                        supporting_context = {rca_report}, {spec_file}
                        输出四重攻击结果与 confidence_impact。"/>
                </check>
                <check if="{env_subagent} == false">
                    <action>顺序模拟 Fix-Proposer + Challenger，保留四重攻击结果。</action>
                </check>
                <check if="challenger 出现 Critical">
                    <action>更新 {workflow_status}：fix_strategy_mode = contested-arbitrated, fanout_mode = contested-arbitrated, reroute_reason = challenged_fix_escalated</action>
                    <action>goto step="3"</action>
                </check>
            </check>

            <check if="fix_strategy_mode == contested-arbitrated">
                <check if="{env_subagent} == true">
                    <invoke-subagent subagent_type="fix-proposer" subagent_prompt="
                        <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                        <load target='mobile-qa-workflow/agents/fix-proposer.md' prompt='加载角色定义'/>
                        <load target='mobile-qa-workflow/reference/fix-strategies.md' prompt='加载修复策略知识库'/>
                        [Proposer-A] 基于 {rca_report}、{spec_file}、{issue_card} 独立设计方案 A，完成全部四重论证。"/>
                    <invoke-subagent subagent_type="fix-proposer" subagent_prompt="
                        <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                        <load target='mobile-qa-workflow/agents/fix-proposer.md' prompt='加载角色定义'/>
                        <load target='mobile-qa-workflow/reference/fix-strategies.md' prompt='加载修复策略知识库'/>
                        [Proposer-B] 必须尝试与 A 不同的策略路径，独立设计方案 B，完成全部四重论证。"/>
                    <invoke-subagent subagent_type="challenger" subagent_prompt="
                        <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                        <load target='mobile-qa-workflow/agents/shared-challenger-base.md' prompt='加载共享 challenger 基座'/>
                        <load target='mobile-qa-workflow/agents/challenger.md' prompt='加载主流程 challenger 包装层'/>
                        scene = FIX
                        dimension_set = fix-4a
                        target_list = 所有 Fix-Proposer 方案
                        supporting_context = {rca_report}, {spec_file}
                        输出四重攻击结果。"/>
                    <invoke-subagent subagent_type="arbiter" subagent_prompt="
                        <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                        <load target='mobile-qa-workflow/agents/shared-arbiter-base.md' prompt='加载共享 arbiter 基座'/>
                        <load target='mobile-qa-workflow/agents/arbiter.md' prompt='加载主流程 arbiter 包装层'/>
                        scene = FIX
                        comparison_focus = root-cause coverage | side-effect risk | minimality | rollback safety
                        candidate_set = 所有 Fix-Proposer 方案
                        challenge_reports = Challenger 输出
                        输出最终方案裁定、评估矩阵与 final_confidence。"/>
                </check>
                <check if="{env_subagent} == false">
                    <action>顺序模拟 Proposer-A -> Proposer-B -> Challenger -> Arbiter。</action>
                </check>
            </check>
        </step>

        <step n="4" goal="方案确认与评估矩阵">
            <action>汇总最终方案，按根因覆盖度 / 副作用风险 / 变更最小性 / 跨平台一致性 / 可回滚性 / 长期可维护性 形成评估矩阵。</action>
        </step>

        <step n="5" goal="跨平台一致性评估与专项附录整合">
            <check if="platform == Both">
                <action>执行 L1-视觉一致性 / L2-行为一致性 / L3-容错一致性 评估。</action>
            </check>
            <action>若专项摘要存在，则在 Fix Design 中整合必要附录引用与风险说明。</action>
        </step>

        <step n="6" goal="回归测试设计与输出">
            <action>基于 Spec 和修改范围设计 TC1（直接验证）/ TC2（边界验证）/ TC3（回归验证）/ TC4（跨平台验证）/ TC5（专项附录验证，按需）。</action>
            <template-output file="{output_file}" template="mobile-qa-workflow/templates/fix-design.md"/>
            <action>更新 {config_source}：output_fix_design = {output_file}</action>
            <step-pause title="Fix Design 四重论证完成，请确认是否进入修复实施：
">
                <option title="[C] Continue：论证通过，进入 Phase 5 修复实施
" action="更新 {workflow_status}：current_state = Fix-Implementing, reroute_reason = null, reroute_target_phase = null"/>
                <option title="[R] Revise：修改方案后重新论证
" action="goto step 2"/>
            </step-pause>
        </step>
    </workflow>
    ```
