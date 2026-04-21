---
name: qa-intake
description: Phase 1 — 问题受理与分类，将用户非结构化问题描述转化为标准 Issue Card
---

# 参数
- workspace_folder：问题工作区路径
- config_source：配置文件路径
- issue_description：用户原始问题描述（交互式可为多轮累计；文档式可为「见下文」+ 全文或 URL）

# 全局静态变量
- output_file: '{workspace_folder}/issue-card.md'
- intake_form_template: 'mobile-qa-workflow/templates/intake-form.md'
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
    <step n="1" goal="加载流程规范">
        <load target="mobile-qa-workflow/core/core-rules.xml" prompt="重新加载作为流程规范，并严格遵守"/>
    </step>

    <step n="2" goal="双场景信息获取（自动判定）">
        <action>【场景自动判定】
            - 若用户已提供问题描述清单/成篇文档（全文、附件、或 `intake_document_url`）→ 按 `document` 场景处理，文档为**首要事实来源**。
            - 若未提供成篇文档，仅有口头/分段描述 → 按 `interactive` 场景处理。
        </action>
        <action>【document：解析】
            - 对全文、附件或（可访问时）URL 做字段抽取，映射到 Issue Card；标注 [User-Provided]。
            - 文档未写明的项勿臆造；标 [Context-Gap]。
        </action>
        <action>【interactive：分轮搜集】
            - 按 intake-form「通用 → 按类型加严」顺序提问；优先封闭式/选择题。
            - 每轮将已确认信息写入工作草稿（或 Issue Card 草案），直至必填集齐或用户明确表示暂无法提供（无法提供的必填项仍触发门禁）。
        </action>
        <action>【自动拉取（补充，两模式共用）】
            - 在已有 UserID/DeviceID 且 APM 可用时：补充崩溃日志、设备、版本等，与当前已知信息交叉校验。
        </action>
        <action>【AI 推断（补充，低权重）】
            - 仅对已有材料归纳；不得覆盖用户明确表述；标注 [AI-Inferred]。
        </action>
        <action>【研发与文档上下文（两模式共用）】
            - 收集仓库路径、分支、diff/patch、PRD、技术方案：来自文档解析或交互式问答。
            - 必填/选填以 intake-form 为准；非必填缺失可 [Context-Gap]。
        </action>
    </step>

    <step n="3" goal="问题分类">
        <action>根据信息将问题映射到标准分类树：
            | 一级分类 | 二级分类 |
            | 稳定性 | Crash / ANR / Freeze / OOM |
            | 性能 | 启动慢 / 卡顿 / 掉帧 / 耗电 / 发热 |
            | 功能 | 逻辑错误 / 数据异常 / 状态丢失 |
            | UI/UX | 布局异常 / 适配问题 / 动画异常 |
            | 网络 | 请求失败 / 超时 / 数据不一致 |
            | 兼容性 | 机型适配 / 系统版本 / 第三方 SDK |
            | 安全 | 数据泄露 / 权限滥用 / 注入风险 |
        </action>
        <action>确定主分类 + 次分类（复合问题时），评估分类置信度</action>
        <action>若用户在 intake 中已填写问题类型：将其作为主参考，与日志/堆栈/复现路径交叉校验；若结论不一致或置信度不足，触发封闭式确认后再固化分类，避免用户误分类直接进入下游。</action>
    </step>

    <step n="4" goal="问题边界判定与锚点盘点">
        <action>根据收集到的信息判定问题边界 (Issue_Boundary_Level)：
            - 存在明确 MR/PR 链接、需求单或提交哈希 -> EXACT_MR (Boundary_Confidence: High)
            - 存在可确认的版本起止点，但无具体 MR -> VERSION_RANGE (Boundary_Confidence 由区间宽度决定)
            - 仅有“一直有问题”描述或历史遗留、偶现问题 -> HISTORICAL_UNCLEAR (Boundary_Confidence 由动态锚点数量决定)
            *注意：当多信号冲突时（如用户说一直有Bug但日志显示某版本突增），取最窄有效边界作为主选，次窄作为备选 (Boundary_Alternative)。*
        </action>
        <action>盘点动态锚点 (Runtime_Anchor_Availability)：
            评估是否具备明确的 Crash 栈、ANR Trace、网络抓包、埋点日志等运行时硬锚点。标记为 Strong 或 Weak。
        </action>
    </step>

    <step n="5" goal="最小信息集门禁（含边界门禁）">
        <action>依据 {intake_form_template} 核对：**全局必填**（必须含「问题描述 + 预期效果」）+ **已判定问题类型下的「必填」**（含按类型矩阵中的「必填」单元格）。「建议必填」与选填**不阻塞**本步。</action>
        <check if="任一必填项仍缺失（含文档未写、交互未答、APM 未补全）">
            <action>更新 {workflow_status}：current_state = Info-Insufficient</action>
            <ask questions="仅针对仍缺的必填项：一次性列出缺失清单，用选择题/封闭式提问让用户补齐；禁止开放式泛问"/>
            <action>用户补齐后 goto step="2" 合并信息并重新跑本门禁</action>
        </check>
        <check if="Issue_Boundary_Level == 'HISTORICAL_UNCLEAR' 且 Runtime_Anchor_Availability == 'Weak'">
            <action>更新 {workflow_status}：current_state = Info-Insufficient</action>
            <ask questions="当前为历史模糊问题且缺乏动态运行锚点，直接分析极易受死代码或错误上下文干扰。请提供复现日志、Crash 栈、网络抓包、具体的错误码或发生异常的具体设备/时间点等明确锚点（最小补证清单）。"/>
            <action>用户补齐后 goto step="2" 合并信息并重新评估边界</action>
        </check>
        <check if="仅「建议必填」或选填缺失">
            <action>标注 [Context-Gap]，记入 Issue Card「缺失项」，继续进入下一阶段（不暂停）</action>
        </check>
    </step>

    <step n="6" goal="优先级评估">
        <action>按以下标准评估优先级：
            P0-Critical: 主流程阻断 / 大规模崩溃 / 数据丢失 / 安全漏洞
            P1-High: 核心功能受损 / 影响 >10% 用户
            P2-Medium: 功能可用但体验劣化 / 特定场景出现
            P3-Low: 轻微体验问题 / 极少数用户反馈
        </action>
    </step>

    <step n="7" goal="输出 Issue Card">
        <action>输出时须覆盖 issue-card 模板：「受理提交物」中注明系统判定场景（interactive / document）；「代码与文档上下文」完整；交互式可将多轮问答摘要写入「关键信息摘要」</action>
        <action>将 Issue_Boundary_Level, Boundary_Confidence, Boundary_Alternative, Runtime_Anchor_Availability 写入 Issue Card 的元数据区块</action>
        <template-output file="{output_file}" template="mobile-qa-workflow/templates/issue-card.md"/>
        <action>更新 {config_source}：output_issue_card = {output_file}，platform、priority 字段</action>
        <action>更新 {workflow_status}：Issue_Boundary_Level = {Issue_Boundary_Level}，Boundary_Confidence = {Boundary_Confidence}，Runtime_Anchor_Availability = {Runtime_Anchor_Availability}</action>
        <action>更新 {workflow_status}：current_state = Spec-Defining</action>
    </step>
</workflow>
```
