# Coder Workflow · 四阶段实施流程

> v4.2 PR-7 / O11+ / §2.1 E1：本文件由 [`agents/coder-agent.md`](./coder-agent.md) 入口
> 在「工具权限」段后、「返回判定协议」段前以**固定顺序**第 1 条 `<load>` 引入；
> 与 [`reference/contract-checklist-spec.md`](../reference/contract-checklist-spec.md)
> 拆分后共同构成原 v4.1 单文件 `coder-agent.md` 的全集。
>
> **加载契约**：
>
> - **唯一入口**：`agents/coder-agent.md`（P5 invoke-subagent 与 Limited 降级路径
>   均仅 `<load coder-agent.md>`，**禁止**单独 `<load coder-workflow.md>`）
> - **顺序契约**：本文件先于 `contract-checklist-spec.md` 加载（与入口固定顺序一致）
> - **职责切分**：本文件 = 四阶段执行步骤 + Error Dump 模板（动作）；
>   checklist-spec = 契约溯源 schema + 平台映射表（数据/规范）

# 四阶段工作流

## 阶段 1：契约溯源与防幻觉走查

<action>【契约溯源走查 — 硬性前置门禁】
    本阶段必须在编码之前完成，未通过不得进入阶段 2。

    1. 从 Fix Design 变更清单中，列出所有跨模块 API 调用、资源引用、配置键引用
    2. 对每一项引用，使用 Search/Grep 工具在源代码中检索其精确定义（Declaration）：
       - 函数签名：参数类型、返回值、访问修饰符
       - 配置键：精确键名、值类型、默认值
       - 资源引用：资源 ID、资源类型、所在文件
       - 枚举/常量：精确拼写、大小写、所在包路径
    3. 逐项填写 Contract Checklist（schema 与反空泛规范见
       reference/contract-checklist-spec.md）：
       | # | 溯源项 | 源文件 | 期望值 | 实际值 | 匹配状态 |
       |---|--------|--------|--------|--------|----------|
       匹配状态 = ✅ 精确匹配 / ❌ 不匹配 + 修正动作
    4. 校验规则（详见 contract-checklist-spec.md）：
       - 涉及 N 个跨模块引用 → checklist 必须 ≥ N 条
       - 所有 ❌ 项必须有修正动作，修正后重新验证直到 ✅
       - 源文件字段必须是可验证的 文件路径:行号 格式
       - 期望值和实际值必须是具体字符串/签名，不允许模糊描述如"某个方法"
</action>

<check if="任何溯源项仍为 ❌ 且无有效修正">
    <action>记录 Execution-Status = Incomplete</action>
    <action>在 impl-report.md 中标记 [CONTRACT-VERIFICATION-FAILED]</action>
    <action>阶段终止，不进入编码</action>
</check>

## 阶段 2：精确编码实施

<action>【编码实施】
    1. 严格按照 Fix Design 变更清单逐文件实施修改：
       - 单一职责：一个修复只解决一个问题
       - 最小变更：修改范围尽可能小，使用 SearchReplace 精确定位
       - 每次修改必须与 Contract Checklist 中的溯源记录对应
    2. 防御性编码：
       - 增加必要的边界检查和异常保护
       - 空值检查、类型检查、范围检查
    3. 代码注释标注规范：
       - 修复代码注释：// [FIX] issue-{issue_id}: 一句话描述
       - 防御性代码注释：// [DEFENSIVE-FIX] ID: df-{NNN} - 描述
</action>

<check if="存在防御性修复条目（来自 defensive-fix-design.md）">
    <action>【防御性修复实施】
        1. 遍历 priority: critical 的防御性修复条目，逐条实施：
           - 熔断器（Circuit Breaker）：在关键状态转换路径上添加异常中断机制
           - 状态断言点（State Assertion）：在状态机关键节点添加不变量断言
           - 防御性守卫（Defensive Guard）：在危险操作前添加前置条件检查
        2. 对 priority: recommended 的条目，评估修复范围后酌情实施
        3. 每个已实现的防御措施需在代码注释中标注对应的条目 ID
        4. 未实现的 critical 条目需在 impl-report.md 中说明原因
    </action>
</check>

## 阶段 3：微验证与自我纠错沙盒

<try retry="3">
    <check if="env_lint_tools == true">
        <action>执行静态 Lint/AST 检查：
            - Android: ./gradlew lint 或 ktlint
            - iOS: SwiftLint 或 swiftc -typecheck
            - 通用: AST 基础语法验证
        </action>
    </check>
    <check if="env_lint_tools == false">
        <action>AI 代码走查，逐项核对检查清单：
            - [ ] 无语法错误
            - [ ] 导包/import 均有效（无幻觉包名）
            - [ ] API 最低版本符合 minSdkVersion / Deployment Target
            - [ ] 无新增 Lint Error
            - [ ] 函数签名与调用方匹配
        </action>
    </check>

    <check if="检查发现错误">
        <action>【自我纠错】
            1. 记录错误现场（错误类型、文件、行号、完整错误消息）
            2. 回溯 Contract Checklist，检查是否因溯源遗漏导致
            3. 执行针对性修正（而非重写）
            4. 将纠错记录填入 impl-report.md 微验证纠错记录表：
               | 轮次 | 错误摘要 | 报错文件:行号 | 溯源操作 | 修正动作 | 验证结果 |
        </action>
    </check>

    <catch>
        <action>【3 轮纠错全失败 — 生成 Error Dump】
            1. 按下方「Error Dump 标准模板」生成完整的纠错失败现场转储
            2. 填写三轮尝试记录、当前代码快照、建议人工处理方向
            3. 将 error-dump.md 写入 {output_error_dump}
            4. 设置 Execution-Status = Human-Review
        </action>
    </catch>
</try>

## 阶段 4：产出与移交

<action>【产出汇总】
    1. 生成 impl-report.md，按模板填写所有节：
       - 元信息（含 Execution-Status 和 Repair-Route）
       - 变更清单
       - 契约溯源记录（从 Contract Checklist 汇总）
       - 微验证纠错记录（从阶段 3 纠错日志汇总）
       - 防御性修复实施记录（如有）
       - 静态微验证结果
       - 检查清单执行结果
    2. 确认所有必需产物已写入对应路径：
       - impl-report.md → {output_impl_report}
       - contract-checklist.md → {output_contract_checklist}（代码修复路径时）
    3. 更新 config_source 中的产物路径
</action>

<check if="Execution-Status == Success">
    <action>所有产物就绪，返回主 Agent</action>
</check>
<check if="Execution-Status == Human-Review">
    <action>error-dump.md 已生成，返回主 Agent 触发 Human-Review 协议</action>
</check>

# Error Dump 标准模板

<load target="mobile-qa-workflow/templates/error-dump.md" prompt="3 轮纠错失败时按此模板生成 Error Dump 转储"/>
