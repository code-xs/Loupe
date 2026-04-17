---
name: qa-spec-definition
description: Phase 2 — Spec 定义与上下文收集，建立行为规约并收集分析证据
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
        <action>读取 {issue_card} 获取分类、平台、优先级等元信息</action>
    </step>

    <step n="2" goal="填写 Spec 基础三要素">
        <action>基于 Issue Card 和上下文信息填写：
            - Expected Behavior：在什么条件下，系统应该如何表现
            - Actual Behavior：系统实际表现了什么，差异点
            - Invariant：系统必须满足的约束条件
        </action>
    </step>

    <step n="3" goal="加载分类扩展模块">
        <action>根据主分类（+ 次分类）加载对应扩展字段，次分类存在时同时加载两者</action>
        <load target="mobile-qa-workflow/templates/spec.md" prompt="加载模板中的分类扩展模块定义"/>

        <switch condition="{主分类}">
            <case if="功能">
                <action>填写：业务规则（Business Rules）、状态转换图、I/O Mapping、数据流检查点</action>
            </case>
            <case if="UI/UX">
                <critical>必须以结构化数据（Layout Inspector / ConstraintLayout XML / AutoLayout 代码约束）为主要证据，截图仅作 C 级辅助</critical>
                <action>填写：视觉参照（精确差异数值）、布局约束定义、适配场景矩阵</action>
            </case>
            <case if="网络">
                <action>填写：API 契约、错误处理链、环境依赖、并发与时序</action>
            </case>
            <case if="兼容性">
                <action>填写：问题设备画像、API 可用性对照、SDK 版本矩阵</action>
            </case>
        </switch>
    </step>

    <step n="4" goal="Spec 校准">
        <action>确定 Spec 来源优先级：PRD(1) > 设计稿(2) > 竞品(3) > 用户口述(4)</action>
        <check if="Spec 存在模糊性或来源冲突">
            <action>标记 [Spec-Uncertain]，列出多种可能的 Expected Behavior</action>
            <step-pause title="Spec 存在歧义，请确认 Expected Behavior：\n{spec_options}\n">
                <option title="[1] {option_1}\n"/>
                <option title="[2] {option_2}\n"/>
                <option title="[S] Skip：先并行分析所有可能，后续确认\n" action="确认前对每种可能 Spec 分别分析"/>
            </step-pause>
        </check>
    </step>

    <step n="5" goal="非 Bug 判定检查">
        <action>逐项检查：
            - Working-As-Designed: 行为符合设计，用户预期与设计不一致
            - User-Misoperation: 用户操作方式不在预期使用路径内
            - Environment-Specific: 仅在用户特殊环境下出现（Root/越狱/非法改装）
            - Known-Limitation: 已知限制，在文档中有声明
            - Duplicate: 与已有 Issue 重复
        </action>
        <check if="判定为非 Bug">
            <action>输出 Non-Bug Resolution Report，包含：
                - 判定类别
                - 判定依据（引用设计文档/产品确认）
                - 用户沟通建议（如何向用户解释）
                - 改进建议（是否值得优化体验）
            </action>
            <action>执行体验改进路由：
                - 多用户同一误解 → 高信号 → 生成 UX Improvement 工单
                - 明确期望差异 → 中信号 → 生成 Feature Request
                - 仅个人偏好 → 低信号 → 跳过
            </action>

            <step-pause title="判定为非 Bug（{non_bug_category}），请确认：\n{non_bug_summary}\n">
                <option title="[A] Accept：确认非 Bug，关闭问题\n" action="更新 {workflow_status}：current_state = Non-Bug"/>
                <option title="[R] Reflow：用户提出异议，提供新证据重新评估\n" action="
                    读取 {workflow_status} 中的 non_bug_reflow_count：
                    - 若 < 2：在 Issue Card 中标注 [Re-Evaluated]，保留原判定记录，
                      non_bug_reflow_count += 1，goto step 1 重新评估
                    - 若 >= 2：触发 Human-Review（同一问题最多回流 2 次）"/>
            </step-pause>
        </check>
    </step>

    <step n="6" goal="候选证据搜集">
        <check if="{env_subagent} == true">
            <invoke-subagent subagent_type="search" subagent_prompt="
                当前任务：请根据 {issue_card} 中记录的问题描述（Actual Behavior）和预期行为（Expected Behavior），在代码库中进行全面检索。
                请执行以下任务：
                1. 检索与 Actual Behavior 相关的代码位置（例如：相关的 UI 组件、业务逻辑类、网络请求或数据模型等）。
                2. 检索与 Expected Behavior 相关的已有代码或预埋逻辑（如果适用）。
                3. 分析相关类和方法之间的依赖关系，追踪可能的逻辑流或数据流。
                4. 总结并返回一个结构化的候选上下文清单，包含关键文件路径、类名、方法名以及它们与问题的相关性说明。
            "/>
        </check>
        <check if="{env_subagent} == false">
            <action>根据分类和边界信息，初步搜集所有可能的代码位置、日志和配置快照。此时不急于过滤，仅构建 candidate_contexts 集合。</action>
        </check>
    </step>

    <step n="7" goal="上下文策展 (Context Curation)">
        <action>更新 {workflow_status}：current_state = Context-Curating</action>
        <check if="{env_subagent} == true">
            <invoke-subagent subagent_type="curator" subagent_prompt="
                <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
                <load target='mobile-qa-workflow/agents/curator.md' prompt='加载角色定义'/>
                对候选上下文集合进行策展，包含去重、存活性校验、保守配置掩码、动态映射。
                输出符合 context-curation-report.md 模板的报告。
            "/>
        </check>
        <check if="{env_subagent} == false">
            <action>执行单对话策展降级模式：主 Agent 自行执行 Curator 的 5 项能力，不调用子 Agent，直接输出 context-curation-report.md 报告内容。</action>
        </check>
        <action>读取输出的 curation_confidence：
            - 若 >= 0.7: 策展成功，正常继续。
            - 若 >= 0.4 且 &lt; 0.7: 标记 [Curation-Partial]，正常继续。
            - 若 &lt; 0.4: 更新 {workflow_status}：current_state = Curation-Failed，并结束当前执行，由 workflow.xml 接管跳转。
        </action>
    </step>

    <step n="8" goal="二维证据分级与 Bundle 生成">
        <action>基于策展结果 (Context Curation Report)，对证据进行二维分级 (Reliability × Liveness)：
            Reliability (A/B/C)：
            A 级: 稳定复现堆栈/日志、抓包、Layout Inspector
            B 级: 偶现日志、用户截图、服务端日志、Git blame
            C 级: 用户口述、AI 推断、未验证相似案例

            Liveness (Live/Suspect/Dead)：
            Live: 明确存活且激活
            Suspect: 无法确定的配置或无明确调用链的候选
            Dead: 明确废弃或未命中配置（记录在 pruned_contexts，不进入后续推理）
        </action>
        <action>整理 Config_Snapshot_Metadata（Mask_Decision_Reason 必填，其他字段尽力获取，取不到标 [Unavailable]）</action>
    </step>

    <step n="9" goal="输出产物">
        <template-output file="{workspace_folder}/context-curation-report.md" template="mobile-qa-workflow/templates/context-curation-report.md"/>
        <template-output file="{output_spec}" template="mobile-qa-workflow/templates/spec.md"/>
        <template-output file="{output_context_bundle}" template="mobile-qa-workflow/templates/context-bundle.md"/>
        <action>更新 {config_source}：增加 output_curation_report={workspace_folder}/context-curation-report.md，以及 output_spec 和 output_context_bundle 路径</action>
        <action>更新 {workflow_status}：current_state = RCA-InProgress</action>
    </step>
</workflow>
```
