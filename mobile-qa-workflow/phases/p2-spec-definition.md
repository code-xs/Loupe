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
    <!--
    ========================================================================
    幂等性约束（V1.1 O6 / 过渡期约束 / O21 落地后失效）

    1. 同一 step 内对 workflow_status.current_state 的写入只允许一次（含 switch
       每个 case 内一次）；reviewer 应可一眼数清状态写入点位。
    2. 状态写入是幂等的：同值重写不影响下游编排器路由（参考 ADR-001 D1 协议）。
    3. 任何"phase 早退"必须配 <action>设置 current_phase_result = ABORT</action>
       单独动作（详见 ADR-001）；O21 宏标签落地后将自动展开此约束（详见 ADR-021）。
    4. 本注释块在 v4.2 PR-3（O21 宏标签）+ PR-6（D14 收口）合入后由 O21 宏标签
       自动覆盖，本 PR 仅作为过渡期约束保留；PR-6 合入后可由 cleanup PR 移除。
    ========================================================================
    -->
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
                <action>标记 [Spec-Uncertain]，列出多种可能的 Expected Behavior</action>
                <!-- ⚠️ v4.2 遗留 #6：本内联 <step-pause> 与编排器 step 4 case Spec-Uncertain
                     重复弹窗（已知 bug）；按 D14 收窄声明，v4.1 暂不动以避免 scope creep，
                     v4.2 整体迁出 phase 文件，由编排器统一调度。 -->
                <step-pause title="Spec 存在歧义，请确认 Expected Behavior：
{spec_options}
">
                    <option title="[1] {option_1}
"/>
                    <option title="[2] {option_2}
"/>
                    <option title="[S] Skip：先并行分析所有可能，后续确认
" action="确认前对每种可能 Spec 分别分析"/>
                </step-pause>
            </check>
            <action>逐项检查 Working-As-Designed / User-Misoperation / Environment-Specific / Known-Limitation / Duplicate</action>

            <!-- ──────────────────────────────────────────────────────────────────
                 v4.1 / B2 / B1* P2 / D14 / D17：Non-Bug 早退三步序列
                 ──────────────────────────────────────────────────────────────────
                 当 step 4 判定为 Non-Bug 时：
                   1) 生成 Non-Bug 判定文本并写入 workflow_status.non_bug_context
                      （供编排器 case Non-Bug 的 step-pause 标题占位 {non_bug_context} 使用）
                   2) 设 current_state = Non-Bug
                   3) 设运行时变量 current_phase_result = ABORT
                 退出 phase（不再继续 step 5-9）；编排器 step 4 接管：
                   - 不追加 qa-spec-definition 到 stepsCompleted（ABORT 分支）
                   - 进入 case Non-Bug，由编排器统一发起确认 step-pause
                 D14 合规：本 PR **不新增** <step-pause>；phase 内现存的 1 处
                 Spec-Uncertain <step-pause> 作为 v4.2 遗留 #6 保持不动。
                 ────────────────────────────────────────────────────────────────── -->
            <check if="判定为 Non-Bug（命中 Working-As-Designed / User-Misoperation / Environment-Specific / Known-Limitation / Duplicate 之一）">
                <action>生成 Non-Bug Resolution Report 文本：包含
                        - 判定类别（5 选 1）
                        - 判定依据（对应 Spec 条款 / 复现路径 / 环境快照锚点）
                        - 沟通建议（一段面向 reporter 的回复要点，便于 step-pause 用户决策）
                        - 改进建议（可选；如对应 UX 工单 / Feature Request / 文档改进）</action>

                <action>更新 {workflow_status}：non_bug_context = {上述 Non-Bug Resolution Report 文本}
                        （D17：该字段是编排器 case Non-Bug step-pause 标题占位的唯一数据源；
                         文本应足够 self-contained，使用户仅凭 step-pause 标题即可做出 Accept / Reflow 决策）</action>

                <action>更新 {workflow_status}：current_state = Non-Bug</action>

                <action>设置 current_phase_result = ABORT
                        （D1：current_phase_result 是运行时变量，不入持久化 schema；
                         本动作必须在返回编排器之前显式赋值，否则编排器 step 4 会将
                         qa-spec-definition 错误追加到 stepsCompleted，B1* 主链路根因复发）</action>

                <action>退出 phase（不再继续 step 5-9）</action>
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

            <!-- ──────────────────────────────────────────────────────────────────
                 v4.1 / C5 / B1* 兜底：curation_confidence 三分支显式化
                 ──────────────────────────────────────────────────────────────────
                 v3 把三个分支折叠为一条自然语言 <action>，导致 "<0.4 → Curation-Failed"
                 仅写状态而未触发早退（B1* 漏标 ABORT），编排器 step 4 会把
                 qa-spec-definition 错误追加到 stepsCompleted，与 B1* 同源 bug。
                 本变更点把三分支显式化，并在 Curation-Failed 分支补齐 ABORT 早退。
                 ────────────────────────────────────────────────────────────────── -->
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
                    <action>更新 {workflow_status}：current_state = Curation-Failed
                            （C5：Curation-Failed 是 PR-1 schema 权威枚举集合内合法状态，
                             与 system-prompt.md Phase 2 字段集对齐）</action>
                    <action>设置 current_phase_result = ABORT
                            （D1 / B1* 兜底：与变更点 P2-1 同协议；不显式标 ABORT 会让
                             编排器把 qa-spec-definition 误追加到 stepsCompleted，
                             导致后续重入策展时 stepsCompleted 失锚）</action>
                    <action>退出 phase（不再继续 step 8-9）</action>
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
            <action>更新 {config_source}：增加 output_curation_report、output_spec、output_context_bundle 路径</action>
            <action>更新 {workflow_status}：current_state = RCA-Designing</action>
        </step>
    </workflow>
    ```
