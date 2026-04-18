---
name: mobile-qa-workflow
description: >-
  Mobile B2C 质量问题工作流统一入口。当用户上报 Android/iOS 应用任何质量问题（Crash、性能、功能异常、
  UI 错乱、网络错误、兼容性问题）时使用。负责初始化工作区、恢复进度、调度六阶段工作流。
---

# Mobile QA B2C Workflow 统一入口

## 输入参数
- issue_description：【必填】问题描述。支持两种用法：**交互式**为多轮对话累计；**文档式**可写「见下文」并粘贴全文或配合 `intake_document_url`。
- intake_document_url：【选填】问题描述在线文档 URL（飞书/语雀等）；**document** 模式常用。
- issue_id：【选填】已有 Issue ID（恢复时使用）
- platform：【选填】Android / iOS / Both

**双模式汇合规则**：信息结构均以 `mobile-qa-workflow/templates/intake-form.md` 为准；**仅当必填项缺失时**再向用户封闭式确认，选填/建议必填缺失可标 `[Context-Gap]` 继续（见 `phases/p1-intake.md` 门禁）。

## 全局静态变量
- workspace_root: `{project_root}/qa-workspace`
- config_source: `{workspace_root}/{issue_id}/config_source.yaml`
- workflow_status: `{workspace_root}/{issue_id}/workflow-status.yaml`

<flow>
    <step n="1" goal="加载流程规范">
        <load target="mobile-qa-workflow/core/core-rules.xml" prompt="加载并执行，作为流程规范严格遵守"/>
    </step>

    <step n="2" goal="初始化或恢复工作区">
        <check if="用户指定了 {issue_id}（恢复已有问题）">
            <action>读取 {config_source} 和 {workflow_status}，恢复工作区上下文</action>
        </check>
        <check if="用户未指定 {issue_id}（新问题）">
            <action>生成 Issue ID，格式 YYYYMMDD-HHmmss（使用当前精确到秒的时间戳，如 20241201-153000，确保每次会话物理隔离）</action>
            <action>创建工作区目录 {workspace_root}/{issue_id}/</action>
            <load target="mobile-qa-workflow/core/default-config.yaml" prompt="保持所有内容原样写入到 {config_source}，仅将 {issue_id} 替换到文件中"/>
            <load target="mobile-qa-workflow/core/workflow-status-template.yaml" prompt="内容作为模版，创建 {workflow_status} 文件，将 {issue_id} 写入"/>
        </check>
    </step>

    <step n="3" goal="环境能力检测">
        <action>检测当前运行环境并更新 {config_source}：
            - 文件系统访问: [有/无]
            - Git 工具访问: [有/无]
            - 静态分析工具（Lint）: [有/无]
            - 子 Agent 能力: [有/无]
        </action>
    </step>

    <step n="4" goal="加载并执行工作流编排">
        <action>从 {config_source} 中读取 env_subagent、env_git 等环境配置变量</action>
        <load target="mobile-qa-workflow/core/workflow.xml" prompt="加载并执行，传递参数：
            - config_source: {config_source}
            - workflow_status: {workflow_status}
            - issue_description: {issue_description}
            - intake_document_url: {intake_document_url}
            - env_subagent: {env_subagent}
            - env_git: {env_git}"/>
    </step>
</flow>
