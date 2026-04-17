---
name: qa-root-cause
description: Phase 3 — 根因分析，通过 OVHSC 推理链和多 Agent 对抗定位根因
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
        <action>读取 {issue_card}、{spec_file}、{context_bundle}</action>
    </step>

    <step n="2" goal="最小证据阈值检查">
        <action>检查 Context Bundle 中的证据质量：
            ✅ 通过: 至少 1 条 A 级证据，或 2 条 B 级证据
            ✅ 对应分类 Spec 扩展模块 ≥ 50% 关键字段已填充
        </action>
        <check if="纯 C 级证据，阈值未通过">
            <action>列出需要补充的具体证据项</action>
            <action>更新 {workflow_status}：current_state = Spec-Defining（回退补充证据）</action>
            <action>阶段结束，返回编排器</action>
        </check>
    </step>

    <step n="3" goal="Context Bundle 降维裁剪（Token 超限时）">
        <check if="上下文超过 80K tokens">
            <action>按优先级裁剪（从低到高保留）：
                1. A 级证据（完整保留）
                2. Spec Document 核心字段
                3. B 级证据（保留与假设相关部分）
                4. 相关代码（仅保留函数级）
                5. 高可疑度 Commit
                6. C 级证据（最先裁剪，头部标注 [已裁剪]）
            </action>
        </check>
    </step>

    <step n="4" goal="边界驱动路由与复杂度评估 (双层路由)">
        <action>【第一层路由：边界感知】读取 {issue_card} 中的 Issue_Boundary_Level 决定策略方向：
            - EXACT_MR -> Diff Focus Mode (聚焦变更、Diff与blame，强制覆盖相关代码)
            - VERSION_RANGE -> Commit Denoising Mode (基于多信号排序降噪后再分析)
            - HISTORICAL_UNCLEAR -> Dynamic Anchoring + Bottom-Up Mode (严格从锚点自底向上逆向回溯，禁止全局漫游)
        </action>

        <check if="Boundary_Confidence == 'Low' 且 Boundary_Alternative 不为空">
            <action>【双轨低成本验证】
                - 对主选边界和备选边界同时执行一次快速路径 (单视角 OVHSC) 分析。
                - 如果两轨结论一致：采信结论，Boundary_Confidence 升级为 Medium，继续后续流程。
                - 如果两轨结论不一致：不盲目选择，输出双轨对比报告，更新 {workflow_status}：current_state = Human-Review，并返回编排器。
            </action>
        </check>

        <action>【第二层路由：复杂度评估】读取 {issue_card} 中的主分类（category）和优先级（priority），按分类细化标准评估复杂度：

            【稳定性/性能类】
            - 简单：堆栈完整且直指业务代码；100%复现；单一触发路径
            - 中等：堆栈指向框架层需溯源；条件复现；涉及 2-3 模块
            - 复杂：无有效堆栈/堆栈被混淆；非确定性复现；跨进程/线程时序

            【功能类】
            - 简单：单一操作路径下结果明确错误；数据流可线性追踪；不涉及状态切换
            - 中等：多步骤操作后才出现异常；涉及状态机跳转；或涉及前后端交互
            - 复杂：偶发性数据异常；涉及并发写入/缓存一致性；多模块联动的状态耦合

            【UI/UX 类】
            - 简单：所有设备一致出现；肉眼可见的硬编码/资源错误；单一视图层级问题
            - 中等：特定屏幕尺寸/密度/系统配置才出现；涉及动态布局计算；交互与动画时序
            - 复杂：偶发布局错乱；异步数据加载后布局重排；多层嵌套滑动冲突；与系统行为耦合

            【网络类】
            - 简单：请求固定失败（4xx/5xx）；错误提示与错误码不匹配；明确的 Schema 不符
            - 中等：间歇性失败（超时/断连）；特定网络环境下出现；缓存未更新致数据陈旧
            - 复杂：偶发数据不一致；并发请求竞态；涉及 CDN/DNS/证书链；前后端均可能是根因

            【兼容性类】
            - 简单：明确的 API 不可用（NoSuchMethod/Unrecognized Selector）
            - 中等：特定厂商 ROM 行为差异；系统权限策略差异；第三方 SDK 在特定设备上的问题
            - 复杂：偶发于特定设备+特定 OS 版本组合；涉及厂商未公开的系统修改；多 SDK 间冲突

            记录评估结果：complexity_level = simple | medium | complex
        </action>

        <action>基于复杂度和上下文选择分析路径：

            【快速路径条件】complexity_level == simple
            - 堆栈完整 + 100% 复现 + A 级证据指向单一假设

            【深度路径触发条件】满足任一即进入深度路径：
            1. 快速路径反事实校验失败（必然触发，在 step 5 中自动升级）
            2. priority ∈ {P0, P1} 且 complexity_level ∈ {medium, complex}
            3. 问题涉及跨模块/跨端，且 Context Bundle 中存在矛盾证据
            4. 相似案例库中存在同类问题被误判的历史记录

            【不触发深度路径的排除情况】即使 complexity_level == medium：
            - priority ∈ {P2, P3} 且快速路径反事实校验通过 → 直接采信快速路径结论
            - Context Bundle 中 A 级证据充分且指向单一假设 → 无需多角度对抗
        </action>

        <switch condition="分析路径">
            <case if="快速路径">
                <action>标记 analysis_path = fast</action>
            </case>
            <case if="深度路径">
                <action>标记 analysis_path = deep</action>
                <action>检查深度路径额外证据阈值：至少 2 条 A 级，或 1A+2B</action>
            </case>
        </switch>
    </step>

    <step n="5" goal="执行 OVHSC 结构化推理链">
        <load target="mobile-qa-workflow/reference/reasoning-chain.md" prompt="加载推理链规范"/>
        <load target="mobile-qa-workflow/reference/platform-checklist.md" prompt="加载平台检查清单"/>

        <check if="analysis_path == fast">
            <action>单视角执行 OVHSC 五步推理：
                OBSERVE → HYPOTHESIZE → VERIFY → SCORE → CHAIN
            </action>
            <action>执行反事实校验</action>
            <check if="推演阶段 (VERIFY) 发现更精确边界线索 (如排查区间时锁定了特定 MR)">
                <action>【边界回溯与精化】更新 Issue_Boundary_Level 到更精确级别，更新 {workflow_status}：current_state = Boundary-Refined，阶段结束返回编排器重试路由。</action>
            </check>
            <check if="所有假设均被证伪 (归因失败)">
                <action>【策展回溯机制】从 Context Curation Report 的 pruned_contexts 中恢复被 Curator 剔除的上下文，重新执行一次 OVHSC 推理。</action>
            </check>
            <check if="反事实校验失败或策展回溯后仍失败">
                <action>升级到深度路径，analysis_path = deep</action>
            </check>
        </check>

        <check if="analysis_path == deep">
            <load target="mobile-qa-workflow/reference/analysis-strategies.md" prompt="加载分析策略池和对抗协议"/>

            <check if="{env_subagent} == true">
                <action>分配 2-3 个不同策略（1 通用 + 1-2 分类专项）</action>

                <invoke-subagent subagent_type="investigator" subagent_prompt="
                    <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                    <load target='mobile-qa-workflow/agents/investigator.md' prompt='加载角色定义'/>
                    <load target='mobile-qa-workflow/reference/reasoning-chain.md' prompt='加载推理链规范'/>
                    <load target='mobile-qa-workflow/reference/platform-checklist.md' prompt='加载平台检查清单'/>
                    使用策略 {strategy_a} 执行 OVHSC 推理链，分析：
                    - spec_file: {spec_file}
                    - context_bundle: {context_bundle}
                    - config_source: {config_source}"/>

                <invoke-subagent subagent_type="investigator" subagent_prompt="
                    <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                    <load target='mobile-qa-workflow/agents/investigator.md' prompt='加载角色定义'/>
                    <load target='mobile-qa-workflow/reference/reasoning-chain.md' prompt='加载推理链规范'/>
                    <load target='mobile-qa-workflow/reference/platform-checklist.md' prompt='加载平台检查清单'/>
                    使用策略 {strategy_b} 执行 OVHSC 推理链，分析：
                    - spec_file: {spec_file}
                    - context_bundle: {context_bundle}
                    - config_source: {config_source}"/>

                <invoke-subagent subagent_type="challenger" subagent_prompt="
                    <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                    <load target='mobile-qa-workflow/agents/challenger.md' prompt='加载角色定义'/>
                    场景: 归因质疑
                    对所有 Investigator 结论执行五维质疑协议：
                    因果充分性 / 因果必要性 / 证据可靠性 / 遗漏假设 / 平台盲区"/>

                <invoke-subagent subagent_type="arbiter" subagent_prompt="
                    <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                    <load target='mobile-qa-workflow/agents/arbiter.md' prompt='加载角色定义'/>
                    场景: 归因仲裁
                    汇总所有 Investigator 结论和 Challenger 质疑，执行：
                    一致性分析 → 质疑吸收 → 最终裁定 → 置信度校准
                    final_confidence = base_score × convergence_factor × challenge_survival_rate"/>
            </check>

            <check if="{env_subagent} == false">
                <action>【单对话降级模式】顺序模拟多视角分析：

                    【Investigator-A: {strategy_a}】
                    按 OVHSC 执行分析...

                    【Investigator-B: {strategy_b}】
                    按 OVHSC 执行分析...

                    【Challenger 质疑】
                    对每个结论执行：因果充分性/必要性/证据可靠性/遗漏/平台盲区

                    【Arbiter 裁定】
                    对比分析 → 置信度校准 → 最终结论
                </action>
            </check>

            <check if="对抗轮次超过 3 轮仍未收敛">
                <action>Arbiter 强制降级裁定：置信度降为 Low（&lt;0.5）</action>
                <action>更新 {workflow_status}：current_state = Human-Review</action>
                <action>阶段结束，返回编排器</action>
            </check>
        </check>
    </step>

    <step n="6" goal="专项子工作流路由决策 (Deep-Dive Routing)">
        <action>【专项路由评估】在深度路径 RCA 完成后（或快速路径升级深度路径后），评估是否需要触发功能疑难专项子工作流：

            【触发条件】满足以下 **任一** 即触发：
            1. 主分类 == 功能类 且 complexity_level == complex
            2. 深度路径 Arbiter 裁定中 convergence_factor &lt; 0.6（分析视角未收敛）
            3. 根因涉及状态机缺陷、生命周期竞态、缓存一致性中的 2 项及以上
            4. Challenger 质疑中存在 Critical 级别的"状态机一致性"或"并发时序漏洞"质疑未被消解

            【不触发条件】
            - analysis_path == fast 且反事实校验通过 → 直接跳到 step 7
            - 最终置信度 >= 0.8 且无 Critical 质疑残留 → 直接跳到 step 7
            - 非功能类问题（稳定性/性能/UI/网络/兼容性）→ 暂不触发（未来扩展 ui-deep-dive 等）
        </action>

        <check if="满足专项路由触发条件">
            <action>【启动功能疑难专项子工作流】
                1. 创建子工作区：{workspace_folder}/deep-dive/
                2. 更新 {workflow_status}：
                   - specialized_workflow.mode = functionality-deep-dive
                   - specialized_workflow.status = DD-InProgress
                   - specialized_workflow.sub_workspace = {workspace_folder}/deep-dive/
                3. 将当前 RCA 中间结论（假设列表、证据映射、Challenger 质疑）写入子工作区作为输入上下文
            </action>
            <load target="mobile-qa-workflow/functionality-deep-dive/core/workflow.xml" prompt="加载并执行功能疑难专项子工作流，传递参数：
                - config_source: {config_source}
                - workspace_folder: {workspace_folder}/deep-dive
                - issue_card: {issue_card}
                - spec_file: {spec_file}
                - context_bundle: {context_bundle}
                - workflow_status: {workspace_folder}/deep-dive/workflow-status.yaml"/>
        </check>

        <check if="不满足专项路由触发条件">
            <action>跳过专项子工作流，直接进入标准 RCA 输出</action>
        </check>
    </step>

    <step n="7" goal="回注专项结论（如有）并合并最终 RCA">
        <check if="specialized_workflow.status == DD-Completed">
            <action>【回注专项结论到主 RCA】
                1. 读取 {workspace_folder}/deep-dive/deep-dive-summary.md
                2. 读取 {workspace_folder}/deep-dive/functionality-deep-dive-rca.md
                3. 将专项结论合并到主 RCA：
                   - 若专项根因与主路径根因一致 → 提升置信度（convergence_factor += 0.1，上限 1.0）
                   - 若专项根因不同但互补 → 主根因取专项结论，原结论降为 Contributing Factor
                   - 若专项根因与主路径冲突 → 采信专项结论（专项分析更深入），标注冲突说明
                4. 更新 {workflow_status}：specialized_workflow.status = Merged
            </action>
        </check>

        <check if="specialized_workflow.status == DD-LowConfidence">
            <action>专项分析亦未收敛，保留主 RCA 结论，但在报告中附注专项分析的部分发现：
                1. 读取 {workspace_folder}/deep-dive/deep-dive-summary.md
                2. 将有价值的部分发现（环境因子、状态拓扑、竞态窗口）附加到 RCA 报告附录
                3. 置信度不变或下调
            </action>
        </check>
    </step>

    <step n="8" goal="客户端-服务端边界判定（功能类/网络类）">
        <check if="主分类 == 功能 或 网络">
            <action>边界判定三步法：
                1. 抓包/日志确认实际请求和响应内容
                2. 判定归属（客户端/服务端/契约歧义/跨端）
                3. 服务端问题 → 输出 Server-Side Issue Handoff 文档
            </action>
        </check>
    </step>

    <step n="9" goal="跨平台 Sub-Issue 判定">
        <check if="platform == Both 且根因指向平台特异性代码">
            <check if="{env_subagent} == true">
                <invoke-subagent subagent_type="investigator" subagent_prompt="
                    [Android 分析] 独立分析 Android 端根因"/>
                <invoke-subagent subagent_type="investigator" subagent_prompt="
                    [iOS 分析] 独立分析 iOS 端根因"/>
                <action>执行跨端 L2/L3 一致性对比</action>
            </check>
            <check if="{env_subagent} == false">
                <action>顺序执行：[Android 分析] → [iOS 分析] → 跨端一致性对比</action>
            </check>
        </check>
    </step>

    <step n="10" goal="输出 Root Cause Report">
        <template-output file="{output_file}" template="mobile-qa-workflow/templates/rca-report.md"/>
        <action>更新 {config_source}：output_rca_report = {output_file}</action>
        <check if="最终置信度 >= 0.5">
            <action>更新 {workflow_status}：current_state = Fix-Designing</action>
        </check>
        <check if="最终置信度 < 0.5">
            <action>更新 {workflow_status}：current_state = RCA-LowConfidence</action>
        </check>
    </step>
</workflow>
```
