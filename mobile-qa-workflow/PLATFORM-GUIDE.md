# Mobile QA Workflow — 平台集成指南

## 概述

本工作流采用 XML 标签化 DSL 进行编排，可在 Full 与 Limited 两类平台运行。

## 角色口径

- **业务角色**：直接承担质量闭环职责的 Agent，例如 `curator`、`investigator`、`challenger`、`arbiter`、`fix-proposer`、`coder-agent`、各类 deep-dive analyst / arbiter / architect。
- **能力型 Agent**：提供检索或基础能力，但不计入业务角色统计，例如 `search`。

## 入口文件

| 文件 | 用途 |
|------|------|
| `SKILL.md` | 支持 Skill 机制的平台入口 |
| `system-prompt.md` | 无文件系统访问的平台入口 |
| `core/workflow.xml` | 主编排逻辑 |
| `phases/p1~p6-*.md` | 各阶段详细逻辑 |
| `functionality-deep-dive/` | 功能疑难专项工作流 |

## 动态路由与状态恢复

- `{variable}` 用于运行时变量注入；场景参数、维度参数、模式参数由调用处显式写入 `subagent_prompt`，不依赖 `agents/*.md` 内部模板渲染。
- `workflow-status.yaml` 是动态路由唯一可信状态源；`analysis_complexity`、`fanout_mode`、`fix_fanout_mode`、`reroute_target_phase`、重试计数、`phase_history`、`user_inputs`、`non_bug_context`、`parse_error_count` 等字段由阶段文件写回，由主编排器读取并执行。
- 恢复已有会话时必须优先识别 `workflow_version` / `schema_version`（v4.1 起 `schema_version = 4`）；旧状态缺字段时，需要先补兼容默认值（迁移脚本：`mobile-qa-workflow/scripts/migrate-workflow-status-v3-to-v4.py`），再恢复阶段执行。
- `current_phase_result` 是 phase 执行期的**运行时变量**（D1：仅在 phase 当次执行轮次内有效，**不会持久化**到 `workflow-status.yaml`）；phase 早退前显式 `current_phase_result = ABORT`，编排器在同一执行轮次读取后接管 step-pause 调度。
- step-pause 用户回复统一写入 `workflow_status.user_inputs.<result_field>` 命名空间（v4.2 PR-6 起，详见 ADR-015 v4.2 修订段）；编排器 / phase / system-prompt 引用用户回复值时统一使用 `{user_inputs.<key>}` 形式。

## 主链路策略

- `P3` 采用三档 fan-out：`simple-single` / `medium-challenge` / `complex-arbitrated`
- `P4` 采用三档 proposer 模式：`single-proposer` / `challenged-proposer` / `contested-arbitrated`
- `P6` 失败分类后可回流 `P3` 或 `P4`；`root_cause_not_closed` 默认强制升级到 `complex-arbitrated`

## 专项工作流

### Functionality Deep-Dive
- 复合角色：`deep-dive-context-analyst`、`deep-dive-structure-analyst`、`deep-dive-race-and-isolation-analyst`、`deep-dive-arbiter`、`defensive-fix-architect`
- 核心强制产物：`deep-dive-summary.md`、`functionality-deep-dive-rca.md`
- 按需独立落盘：`environment-factor-report.md`、`deep-dive-topology.md`、`concurrency-analysis-report.md`

## Full 能力平台

`mobile-qa-workflow/` 目录是唯一权威源；Skill 镜像目录只应作为软链接入口，避免版本漂移。

- Cursor / Trae / CapCode / Windsurf：使用 `SKILL.md`
- AutoGen / CrewAI：用 `core/workflow.xml` 作为编排器，`phases/*.md` 作为阶段节点，`agents/*.md` 作为子角色定义

## Limited 能力平台

- Dify / Coze / OpenAI Assistants / LangGraph：使用 `system-prompt.md`
- 至少持久化字段（v4.1 / `schema_version: 4`）：
  - **版本与基础**：`schema_version`(=4)、`workflow_version`、`current_state`、`stepsCompleted`
  - **路由与计数**：`analysis_complexity`、`analysis_complexity_confidence`、`fanout_mode`、`fix_fanout_mode`、`fix_risk_level`、`reroute_target_phase`、`reroute_reason`、`rca_retry_count`、`fix_retry_count`、`non_bug_reflow_count`、`lint_retry_count`
  - **历史**：`phase_history`（结构：`{phase, timestamp, fanout_mode, note?}`，P3 写入端在每次 phase 完成时 append；P3 重入时反查最近一条 `qa-root-cause` 元素的 `fanout_mode` 还原）
  - **step-pause 协议字段**：`user_inputs`（命名空间，编排器 step 4 解析用户回复后总是写入 `user_inputs.<result_field>`）、`parse_error_count`（连续解析失败计数器，进入新 step-pause / 解析成功 / 熔断转 Human-Review 时清零，>= 3 时强制转人工）
  - **Non-Bug 字段（职责正交，v4.2 PR-6 修订）**：`non_bug_reflow_count`（跨轮回流次数）、`non_bug_context`（最近一次 Non-Bug 判定上下文文本，供编排器 case Non-Bug 的 step-pause 标题占位 `{non_bug_context}` 使用）；用户选择走 `user_inputs.non_bug_user_choice` 不进顶层 schema
- ❌ **不持久化 `current_phase_result`**（D1：phase 执行期运行时变量，不入 schema）

## Coder Agent 适配

- Full 平台：通过 `<invoke-subagent subagent_type="coder-agent">` 独立运行
- Limited 平台：将契约溯源内联到 Phase 5，由验证阶段审计
- Minimal 平台：外部编排层自行实现 pre-coding contract tracing
