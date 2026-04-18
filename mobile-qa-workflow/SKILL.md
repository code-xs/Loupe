---
name: mobile-qa-workflow
description: >-
  Mobile B2C 质量问题工作流统一入口。当用户上报 Android/iOS 应用任何质量问题时使用。
  支持主链路动态 fan-out、Functionality Deep-Dive 与 UI Deep-Dive。
---

# Mobile QA B2C Workflow 统一入口

## 输入参数
- issue_description：【必填】问题描述
- intake_document_url：【选填】在线文档 URL
- issue_id：【选填】已有 Issue ID（恢复时使用）
- platform：【选填】Android / iOS / Both

## 运行时恢复约束
- 恢复已有问题时，先读取 `workflow-status.yaml` 中的 `workflow_version` / `schema_version`，缺失则按旧版状态补齐兼容默认值后再继续编排。
- `P3 / P4 / P6` 的动态路由状态统一写入 `workflow-status.yaml`，主编排器只读取结构化字段，不依赖阶段产物中的自由文本描述。
- 子 Agent 参数通过调用处 `subagent_prompt` 显式拼接传递，不假设 `agents/*.md` 文件内部支持模板渲染。

## 角色口径
- 业务角色：`curator`、`investigator`、`challenger`、`arbiter`、`fix-proposer`、`coder-agent` 与专项复合角色
- 能力型 Agent：`search`

<flow>
    <step n="1" goal="加载流程规范">
        <load target="mobile-qa-workflow/core/core-rules.xml" prompt="加载并执行，作为流程规范严格遵守"/>
    </step>

    <step n="2" goal="初始化或恢复工作区">
        <check if="用户指定了 {issue_id}">
            <action>读取 {config_source} 和 {workflow_status}，恢复工作区上下文，并优先识别状态模板版本、复杂度字段和重路由字段</action>
        </check>
        <check if="用户未指定 {issue_id}">
            <action>生成 Issue ID，格式 YYYYMMDD-HHmmss</action>
            <action>创建工作区目录 {workspace_root}/{issue_id}/</action>
            <load target="mobile-qa-workflow/core/default-config.yaml" prompt="保持所有内容原样写入到 {config_source}，仅将 {issue_id} 替换到文件中"/>
            <load target="mobile-qa-workflow/core/workflow-status-template.yaml" prompt="内容作为模版，创建 {workflow_status} 文件，将 {issue_id} 写入"/>
        </check>
    </step>

    <step n="3" goal="环境能力检测">
        <action>检测当前运行环境并更新 {config_source}：文件系统 / Git / Lint / 子 Agent 能力</action>
    </step>

    <step n="4" goal="加载并执行主编排">
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
