---
name: qa-fix-impl
description: Phase 5 — 修复实施，在独立分支执行代码修改并通过静态微验证闭环
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

    <step n="4" goal="代码或非代码修改实施">
        <check if="Fix Design 指向客户端代码缺陷">
            <action>严格按照 Fix Design Document 实施代码修改：
                - 单一职责：一个修复只解决一个问题，不搭便车
                - 最小变更：修改范围尽可能小
                - 防御性编程：增加必要的边界检查和异常保护
            </action>

            <check if="存在防御性修复条目（来自 step 2）">
                <action>【防御性修复实施】
                    1. 遍历 priority: critical 的防御性修复条目，逐条实施：
                       - 熔断器（Circuit Breaker）：在关键状态转换路径上添加异常中断机制
                       - 状态断言点（State Assertion）：在状态机关键节点添加不变量断言
                       - 防御性守卫（Defensive Guard）：在危险操作前添加前置条件检查
                    2. 对 priority: recommended 的条目，评估修复范围后酌情实施
                    3. 每个已实现的防御措施需在代码注释中标注对应的条目 ID：
                       // [DEFENSIVE-FIX] ID: df-001 - Circuit breaker for state transition
                    4. 未实现的 critical 条目需在 impl-report.md 中说明原因
                </action>
            </check>
        </check>
        <check if="Fix Design 指向远端漂移/跨端协调修复">
            <action>执行【非代码修复实施分支】：
                - 输出变更服务端配置、回滚 AB 实验或协调后端的具体指令和参数清单。
                - 如果必须在客户端做兼容兜底，则仅实现兜底逻辑，并标注 [Remote-Drift-Fallback]。
            </action>
        </check>
    </step>

    <step n="5" goal="静态微验证闭环">
        <check if="执行了纯非代码修复 (无客户端代码修改)">
            <action>跳过静态代码 Lint 检查，直接标记微验证通过。</action>
            <goto step="6"/>
        </check>
        
        <try retry="3">
            <check if="{env_lint_tools} == true">
                <action>执行静态 Lint/AST 检查：
                    - Android: ./gradlew lint
                    - iOS: SwiftLint
                    - 通用: AST 基础语法验证
                </action>
            </check>
            <check if="{env_lint_tools} == false">
                <action>AI 代码走查，逐项核对检查清单</action>
            </check>

            <action>验证必须通过的静态检查项：
                - [ ] 无语法错误
                - [ ] 导包/import 均有效（无幻觉包名）
                - [ ] API 最低版本符合 minSdkVersion / Deployment Target
                - [ ] 无新增 Lint Error
                - [ ] 函数签名与调用方匹配
            </action>

            <check if="静态检查失败">
                <action>AI 自动修正代码，更新 lint_retry_count</action>
            </check>

            <catch>
                <action>超过 3 轮仍失败，触发 Human-Review：附失败原因 + 当前代码快照</action>
                <action>更新 {workflow_status}：current_state = Human-Review, lint_retry_count = 3</action>
                <action>阶段结束，返回编排器</action>
            </catch>
        </try>
    </step>

    <step n="6" goal="代码修改检查清单">
        <action>逐项确认：
            - [ ] 修改符合 Fix Design Document 四重论证
            - [ ] 静态 Lint/AST 检查通过（或 AI 代码走查通过）
            - [ ] 没有引入新的 Lint Error（Warning 须列出）
            - [ ] 添加了必要的防御性代码
            - [ ] 异常路径有合理的降级策略
            - [ ] 线程安全性已确认
            - [ ] 内存管理正确
            - [ ] 跨平台行为一致（L1/L2/L3）
            - [ ] 添加/更新了相关单元测试
        </action>

        <check if="存在防御性修复条目（来自 step 2）">
            <action>【防御性修复验证清单】额外逐项确认：
                - [ ] 所有 priority: critical 条目已实施或已说明未实施原因
                - [ ] 每个防御性措施代码注释含对应条目 ID
                - [ ] 熔断器可正确触发和恢复
                - [ ] 状态断言点在异常状态时抛出明确错误信息
                - [ ] 防御性守卫不影响正常路径性能
            </action>
        </check>
    </step>

    <step n="7" goal="输出 Implementation Report">
        <template-output file="{output_file}" template="mobile-qa-workflow/templates/impl-report.md"/>
        <action>更新 {config_source}：output_impl_report = {output_file}</action>
        <action>更新 {workflow_status}：current_state = Verifying</action>
    </step>
</workflow>
```
