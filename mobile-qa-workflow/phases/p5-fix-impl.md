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
- output_file: '{workspace_folder}/impl-report.md'
- workflow_status: '{workspace_folder}/workflow-status.yaml'

```xml
<workflow>
    <step n="1" goal="加载流程规范和上游产物">
        <load target="mobile-qa-workflow/core/core-rules.xml" prompt="重新加载作为流程规范"/>
        <action>读取 {fix_design} 和 {spec_file}</action>
        <load target="mobile-qa-workflow/reference/platform-checklist.md" prompt="加载平台检查清单和 API 版本合规检查"/>
    </step>

    <step n="2" goal="工作区初始化">
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

    <step n="3" goal="代码或非代码修改实施">
        <check if="Fix Design 指向客户端代码缺陷">
            <action>严格按照 Fix Design Document 实施代码修改：
                - 单一职责：一个修复只解决一个问题，不搭便车
                - 最小变更：修改范围尽可能小
                - 防御性编程：增加必要的边界检查和异常保护
            </action>
        </check>
        <check if="Fix Design 指向远端漂移/跨端协调修复">
            <action>执行【非代码修复实施分支】：
                - 输出变更服务端配置、回滚 AB 实验或协调后端的具体指令和参数清单。
                - 如果必须在客户端做兼容兜底，则仅实现兜底逻辑，并标注 [Remote-Drift-Fallback]。
            </action>
        </check>
    </step>

    <step n="4" goal="静态微验证闭环">
        <check if="执行了纯非代码修复 (无客户端代码修改)">
            <action>跳过静态代码 Lint 检查，直接标记微验证通过。</action>
            <goto step="5"/>
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

    <step n="5" goal="代码修改检查清单">
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
    </step>

    <step n="6" goal="输出 Implementation Report">
        <template-output file="{output_file}" template="mobile-qa-workflow/templates/impl-report.md"/>
        <action>更新 {config_source}：output_impl_report = {output_file}</action>
        <action>更新 {workflow_status}：current_state = Verifying</action>
    </step>
</workflow>
```
