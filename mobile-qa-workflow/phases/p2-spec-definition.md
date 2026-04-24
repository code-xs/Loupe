    ---
    name: qa-spec-definition
    description: Phase 2 — Spec 定义与上下文收集，建立行为规约并输出复杂度判定
    ---

    # 参数
    - workspace_folder：问题工作区路径
    - config_source：配置文件路径
    - issue_card：Issue Card 文件路径

    # 全局静态变量
    - output_spec: '{workspace_folder}/spec.md'
    - output_context_bundle: '{workspace_folder}/context-bundle.md'
    - workflow_status: '{workspace_folder}/workflow-status.yaml'

    ```xml
    <workflow>
        <step n="1" goal="加载流程规范和上游产物">
            <load target="mobile-qa-workflow/core/core-rules.xml" prompt="重新加载作为流程规范，并严格遵守"/>
            <action>读取 {issue_card} 获取分类、平台、优先级、复现性与边界信息</action>
        </step>

        <step n="2" goal="填写 Spec 基础三要素">
            <action>基于 Issue Card 和上下文信息填写：Expected Behavior / Actual Behavior / Invariant</action>
        </step>

        <step n="3" goal="加载分类扩展模块">
            <load target="mobile-qa-workflow/templates/spec.md" prompt="加载模板中的分类扩展模块定义"/>
            <switch condition="{主分类}">
                <case if="功能">
                    <action>填写：业务规则、状态转换图、I/O Mapping、数据流检查点</action>
                </case>
                <case if="UI/UX">
                    <critical>结构化数据优先，截图仅作 C 级辅助</critical>
                    <action>填写：视觉参照、布局约束定义、适配场景矩阵</action>
                </case>
                <case if="网络">
                    <action>填写：API 契约、错误处理链、环境依赖、并发与时序</action>
                </case>
                <case if="兼容性">
                    <action>填写：问题设备画像、API 可用性对照、SDK 版本矩阵</action>
                </case>
            </switch>
        </step>

        <step n="4" goal="Spec 校准与非 Bug 判定">
            <action>确定 Spec 来源优先级：PRD(1) > 设计稿(2) > 竞品(3) > 用户口述(4)</action>
            <check if="Spec 存在模糊性或来源冲突">
                <action>标记 [Spec-Uncertain]，列出多种可能的 Expected Behavior，
                        将候选选项数组命名为 `{spec_options}`，并同时生成 `{option_1}` / `{option_2}` 两段文本（供弹窗选项标题占位使用）。
                        为避免把临时渲染字段写入 workflow_status 顶层 schema（Check 15 顶层字段断言），
                        本分支把三段值写入 workflow_status.user_inputs.* 命名空间（与 D15 单写协议一致）。</action>
                <!-- v4.2 PR-6 / O13 / ADR-014 §7：D14 整改清零 — 删除内联 step-pause；
                     由编排器 step 4c 命中 step-pause-registry.yaml `state: Spec-Uncertain` 项统一发起 step-pause。 -->
                <phase-abort state="Spec-Uncertain"
                             fields='{"user_inputs": {"spec_options": "{spec_options}", "option_1": "{option_1}", "option_2": "{option_2}"}}'
                             reason="ADR-014"/>
            </check>
            <action>逐项检查 Working-As-Designed / User-Misoperation / Environment-Specific / Known-Limitation / Duplicate</action>

            <!-- Non-Bug 早退三步序列（v4.1 B2/D14/D17 / ADR-014）：
                 1) 写 non_bug_context  2) 设 state=Non-Bug  3) ABORT 退出 phase；编排器 step 4 接管。 -->
            <check if="判定为 Non-Bug（命中 Working-As-Designed / User-Misoperation / Environment-Specific / Known-Limitation / Duplicate 之一）">
                <action>生成 Non-Bug Resolution Report 文本，**将该段文本命名为 `{report_text}`**（供下方 phase-abort 宏 fields 字面引用），内容包含：
                        - 判定类别（5 选 1）
                        - 判定依据（对应 Spec 条款 / 复现路径 / 环境快照锚点）
                        - 沟通建议（一段面向 reporter 的回复要点，便于 step-pause 用户决策）
                        - 改进建议（可选；如对应 UX 工单 / Feature Request / 文档改进）</action>

                <!-- v4.2 PR-3' / O21 / ADR-014 / v1.2 review Finding #1 收口：
                     `{report_text}` 是上一 <action> 显式命名的本轮局部变量（非 workflow_status 字段），
                     宏展开第 2 步将其原文写入 workflow_status.non_bug_context，
                     供 D17 协议下编排器 case Non-Bug 的 step-pause 标题占位 `{non_bug_context}` 使用 -->
                <phase-abort state="Non-Bug"
                             fields='{"non_bug_context": "{report_text}"}'
                             reason="ADR-014"/>
            </check>
        </step>

        <step n="5" goal="输出复杂度判定与建议 Fan-out">
            <action>基于主分类、优先级、证据锚点、模块数量、状态/并发特征，输出：
                - Analysis Complexity = simple | medium | complex
                - Complexity Confidence = High | Medium | Low
                - Suggested Fan-out Mode = simple-single | medium-challenge | complex-arbitrated
                - Complexity Rationale = 解释判定依据
            </action>
            <action>更新 {workflow_status}：
                - analysis_complexity = {Analysis Complexity}
                - analysis_complexity_confidence = {Complexity Confidence}
                - fanout_mode = {Suggested Fan-out Mode}
            </action>
        </step>

        <step n="6" goal="候选证据搜集">
            <check if="{env_subagent} == true">
                <invoke-subagent subagent_type="search" subagent_prompt="
                    当前任务：请根据 {issue_card} 中记录的问题描述（Actual Behavior）和预期行为（Expected Behavior），在代码库中进行全面检索。
                    请执行以下任务：
                    1. 检索与 Actual Behavior 相关的代码位置。
                    2. 检索与 Expected Behavior 相关的已有代码或预埋逻辑。
                    3. 分析相关类和方法之间的依赖关系，追踪可能的逻辑流或数据流。
                    4. 返回结构化的候选上下文清单，包含关键文件路径、类名、方法名以及相关性说明。
                "/>
            </check>
            <check if="{env_subagent} == false">
                <action>根据分类和边界信息搜集可能的代码位置、日志和配置快照，先构建 candidate_contexts 集合。</action>
            </check>
        </step>

        <step n="7" goal="上下文策展">
            <action>更新 {workflow_status}：current_state = Context-Curating
                    （C5：Context-Curating 是策展执行中的中间态，不引发 ABORT；
                     仅当下方 curation_confidence < 0.4 才转入 Curation-Failed 早退）</action>
            <check if="{env_subagent} == true">
                <invoke-subagent subagent_type="curator" subagent_prompt="
                    <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                    <load target='mobile-qa-workflow/agents/curator.md' prompt='加载角色定义'/>
                    对候选上下文集合进行策展，包含去重、存活性校验、保守配置掩码、动态映射。
                    输出符合 context-curation-report.md 模板的报告。
                "/>
            </check>
            <check if="{env_subagent} == false">
                <action>执行单对话策展降级模式：主 Agent 自行完成 Curator 的 5 项能力。</action>
            </check>

            <!-- curation_confidence 三分支显式化（v4.1 C5/B1* 兜底）：<0.4 → Curation-Failed + ABORT 早退。 -->
            <action>读取 curation_confidence</action>
            <switch condition="curation_confidence">
                <case if=">= 0.7">
                    <action>正常继续，进入 step 8</action>
                </case>
                <case if=">= 0.4 且 < 0.7">
                    <action>在策展报告中标记 [Curation-Partial]，正常继续进入 step 8
                            （部分置信度路径不早退；后续 step 9 仍输出三件套）</action>
                </case>
                <case if="< 0.4">
                    <!-- v4.2 PR-3' / O21 / ADR-001：B1* 兜底，避免 stepsCompleted 错追加 -->
                    <phase-abort state="Curation-Failed" reason="ADR-001"/>
                </case>
            </switch>
        </step>

        <step n="8" goal="二维证据分级与 Bundle 生成">
            <action>按 Reliability × Liveness 对证据分级，Dead 证据不进入推理。</action>
            <action>整理 Config_Snapshot_Metadata（Mask_Decision_Reason 必填，其他字段尽力获取）</action>
        </step>

        <step n="9" goal="输出产物">
            <template-output file="{workspace_folder}/context-curation-report.md" template="mobile-qa-workflow/templates/context-curation-report.md"/>
            <template-output file="{output_spec}" template="mobile-qa-workflow/templates/spec.md"/>
            <template-output file="{output_context_bundle}" template="mobile-qa-workflow/templates/context-bundle.md"/>

            <!-- v4.2 PR-3' / O21 / ADR-021 -->
            <phase-complete state="RCA-Designing"
                            update_config='{"output_curation_report": "{workspace_folder}/context-curation-report.md",
                                            "output_spec": "{output_spec}",
                                            "output_context_bundle": "{output_context_bundle}"}'/>
        </step>
    </workflow>
    ```
