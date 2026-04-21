---
name: mobile-qa-workflow
description: >-
  Mobile B2C 质量问题工作流统一入口。当用户上报 Android/iOS 应用任何质量问题时使用。
  支持主链路动态 fan-out 与 Functionality Deep-Dive。
---

# Mobile QA B2C Workflow 统一入口

## 输入参数
- issue_description：【必填】问题描述
- intake_document_url：【选填】在线文档 URL
- issue_id：【选填】已有 Issue ID（恢复时使用）
- platform：【选填】Android / iOS / Both

## 运行时恢复约束
- 恢复已有问题时，先读取 `workflow-status.yaml` 中的 `workflow_version` / `schema_version`（v4.1 起 `schema_version = 4`），缺失则运行 `mobile-qa-workflow/scripts/migrate-workflow-status-v3-to-v4.py` 或按旧版状态补齐兼容默认值后再继续编排。
- `P3 / P4 / P6` 的动态路由状态统一写入 `workflow-status.yaml`，主编排器只读取结构化字段，不依赖阶段产物中的自由文本描述。
- 子 Agent 参数通过调用处 `subagent_prompt` 显式拼接传递，不假设 `agents/*.md` 文件内部支持模板渲染。
- `current_phase_result` 是 phase 执行期的**运行时变量**（不入 `workflow-status.yaml` 持久化字段表）；phase 早退前显式 `current_phase_result = ABORT`，编排器在同一执行轮次读取后接管 step-pause 调度。

## workflow_status 关键字段（v4.1 / `schema_version: 4`）

> 完整权威源见 [`core/workflow-status-template.yaml`](./core/workflow-status-template.yaml)。下表仅枚举 v4.1 主要新增/变更字段；老字段（`fanout_mode` / `analysis_complexity` / `reroute_target_phase` / `rca_retry_count` 等）保持不变。

| 字段 | 默认 | 用途 | 引入版本 |
|---|---|---|---|
| `schema_version` | `4` | v4.1 schema 升级；旧会话由迁移脚本补齐 | v4.1（v3 → v4） |
| `fix_fanout_mode` | `null` | P4 修复路由模式（C10 字段隔离，承接 `single-proposer` / `challenged-proposer` / `contested-arbitrated`），与 RCA 字段 `fanout_mode` 物理隔离 | v4.1 / v4.2 PR-2 收敛 `fix_strategy_mode` |
| `phase_history` | `[]` | 阶段执行历史，元素结构：`{phase, timestamp, fanout_mode, note?}`；P3 完成时 append（C10 兼容性方案 A 主路径） | v4.1 |
| `user_inputs` | `{}` | step-pause 用户回复命名空间容器；编排器 step 4 解析回复后**总是**写入 `user_inputs.<result_field>` | v4.1 |
| `non_bug_context` | `null` | 最近一次 P2 Non-Bug 判定上下文文本，供编排器 case Non-Bug 的 step-pause 标题占位 `{non_bug_context}` 使用；允许在后续会话中被覆盖，非长期业务字段 | v4.1（D17） |
| `parse_error_count` | `0` | step-pause 连续解析失败熔断计数器；**生命周期**：进入新 step-pause 前清零、解析成功清零、解析失败 +1、累计 ≥ 3 切到 `current_state = Human-Review` 并清零 | v4.1（D18） |
| `non_bug_user_choice` | `null` | step-pause 用户选择（`Accept` / `Reflow`）的**顶层镜像白名单字段**；编排器读取保持顶层 `{non_bug_user_choice}` 占位以兼容现有 switch | v4.1（顶层镜像，**v4.2 收敛到 `user_inputs.non_bug_user_choice`**） |

> ❌ **不持久化 `current_phase_result`**（D1：运行时变量）。
>
> ⚠️ **顶层镜像字段白名单（v4.1 D8 + D15）**：v4.1 起步白名单 = `{ non_bug_user_choice }`，新增需 PR Review 显式批准并同步更新 `core/workflow-status-template.yaml` 注释；v4.2 整体收敛后将删除所有顶层镜像字段，编排器统一改读 `user_inputs.<key>`。
>
> 🔁 **step-pause 输入协议（D2 + D16）**：所有 step-pause 标题最后一行必须形如 `请用 <key>=<value> 回复`；用户回复**首行**含 `<key>=<value>`，`<value>` ∈ `allowed_values` 白名单；解析失败编排器输出 `[parse-error: 期望 <key> ∈ <allowed_values>]` 并重新触发同一 step-pause；连续 3 次失败强制转 Human-Review。

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
