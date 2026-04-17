---
name: qa-fix-design
description: Phase 4 — 修复方案设计，执行四重形式化论证并生成 Fix Design Document
---

# 参数
- workspace_folder：问题工作区路径
- config_source：配置文件路径

# 全局静态变量
- issue_card: '{workspace_folder}/issue-card.md'
- spec_file: '{workspace_folder}/spec.md'
- rca_report: '{workspace_folder}/rca-report.md'
- output_file: '{workspace_folder}/fix-design.md'
- workflow_status: '{workspace_folder}/workflow-status.yaml'

```xml
<workflow>
    <step n="1" goal="加载流程规范和上游产物">
        <load target="mobile-qa-workflow/core/core-rules.xml" prompt="重新加载作为流程规范"/>
        <action>读取 {issue_card}、{spec_file}、{rca_report}</action>
        <load target="mobile-qa-workflow/reference/fix-strategies.md" prompt="加载修复策略知识库"/>
    </step>

    <step n="2" goal="修复路径选择与方案生成">
        <critical>必须优先选择治本策略；治标策略仅在真因短期无法修改时使用，且必须说明原因</critical>

        <action>【前置策略路由】读取 rca_report，若根因涉及远端配置、服务端契约变更或第三方依赖漂移 (Remote_Drift_Suspected)，必须优先选择「跨端协调/远端修复」策略，不可盲目修改客户端代码作为妥协。</action>

        <switch condition="根因置信度 + 子 Agent 能力">
            <case if="High（≥ 0.8）且因果链完整 且 {env_subagent} == false">
                <action>单方案论证模式（主 Agent 独立完成）</action>
                <action>【论证 1 — Completeness】逐环节标注因果链被切断环节，论证无绕过路径</action>
                <action>【论证 2 — Safety】调用链 + 共享状态 + 并发安全 + 平台差异</action>
                <action>【论证 3 — Correctness】逐条验证 Expected Behavior 和 Invariant</action>
                <action>【论证 4 — Minimality】是否有更小修改？有无搭便车改动？</action>
            </case>

            <case if="{env_subagent} == true（多 Agent 对抗模式）">
                <action>启动 2 个 Fix-Proposer 独立生成方案，再由 Challenger + Arbiter 评估</action>

                <invoke-subagent subagent_type="fix-proposer" subagent_prompt="
                    <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                    <load target='mobile-qa-workflow/agents/fix-proposer.md' prompt='加载角色定义'/>
                    <load target='mobile-qa-workflow/reference/fix-strategies.md' prompt='加载修复策略知识库'/>
                    [Proposer-A] 基于以下产物独立设计修复方案：
                    - rca_report: {rca_report}
                    - spec_file: {spec_file}
                    - issue_card: {issue_card}
                    - config_source: {config_source}
                    要求完成全部四重论证 + 回归测试设计"/>

                <invoke-subagent subagent_type="fix-proposer" subagent_prompt="
                    <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                    <load target='mobile-qa-workflow/agents/fix-proposer.md' prompt='加载角色定义'/>
                    <load target='mobile-qa-workflow/reference/fix-strategies.md' prompt='加载修复策略知识库'/>
                    [Proposer-B] 基于以下产物独立设计修复方案（尝试与 Proposer-A 不同的策略）：
                    - rca_report: {rca_report}
                    - spec_file: {spec_file}
                    - issue_card: {issue_card}
                    - config_source: {config_source}
                    要求完成全部四重论证 + 回归测试设计"/>

                <invoke-subagent subagent_type="challenger" subagent_prompt="
                    <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                    <load target='mobile-qa-workflow/agents/challenger.md' prompt='加载角色定义'/>
                    场景: 修复方案质疑
                    对所有 Fix-Proposer 方案执行四重攻击：
                    Completeness 攻击 / Safety 攻击 / Correctness 攻击 / Minimality 攻击"/>

                <invoke-subagent subagent_type="arbiter" subagent_prompt="
                    <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                    <load target='mobile-qa-workflow/agents/arbiter.md' prompt='加载角色定义'/>
                    场景: 修复方案仲裁
                    汇总所有 Fix-Proposer 方案和 Challenger 质疑，执行：
                    质疑吸收 → 评估矩阵打分 → 最终方案裁定
                    评估维度：根因覆盖度(30%) | 副作用风险(25%) | 变更最小性(15%) | 跨平台一致性(10%) | 可回滚性(10%) | 长期可维护性(10%)"/>
            </case>

            <case if="Medium（0.5-0.8）且 {env_subagent} == false（单对话降级）">
                <action>【单对话多方案竞争】顺序模拟多视角：

                    【Fix-Proposer-A】
                    设计修复方案 A + 四重论证...

                    【Fix-Proposer-B】
                    设计修复方案 B（不同策略）+ 四重论证...

                    【Challenger】
                    对 A 和 B 分别执行四重攻击...

                    【Arbiter】
                    评估矩阵打分 → 最终裁定
                </action>
            </case>
        </switch>
    </step>

    <step n="3" goal="方案确认与评估矩阵">
        <action>汇总最终方案（Arbiter 裁定结果 或 单方案论证结果），按评估矩阵确认：
            | 维度 | 权重 | 得分 |
            | 根因覆盖度 | 30% | |
            | 副作用风险 | 25% | |
            | 变更最小性 | 15% | |
            | 跨平台一致性 | 10% | |
            | 可回滚性 | 10% | |
            | 长期可维护性 | 10% | |
            最终得分 = SUM(评分 × 权重)
        </action>
    </step>

    <step n="4" goal="跨平台一致性评估">
        <check if="platform == Both">
            <action>按三层标准评估：
                L1-视觉一致性（允许原生控件风格差异）
                L2-行为一致性（同操作同结果，L2 优先级 > L1）
                L3-容错一致性（底线，无明确理由必须对齐）
            </action>
        </check>
    </step>

    <step n="5" goal="回归测试设计">
        <action>基于 Spec 和修改范围设计测试用例：
            TC1（直接验证）/ TC2（边界验证）/ TC3（回归验证）/ TC4（跨平台验证）
        </action>
    </step>

    <step n="6" goal="输出 Fix Design Document">
        <template-output file="{output_file}" template="mobile-qa-workflow/templates/fix-design.md"/>
        <action>更新 {config_source}：output_fix_design = {output_file}</action>

        <step-pause title="Fix Design 四重论证完成，请确认是否进入修复实施：\n">
            <option title="[C] Continue：论证通过，进入 Phase 5 修复实施\n" action="更新 {workflow_status}：current_state = Fix-Implementing"/>
            <option title="[R] Revise：修改方案后重新论证\n" action="goto step 2"/>
        </step-pause>
    </step>
</workflow>
```
