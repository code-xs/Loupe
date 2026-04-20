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
- `workflow-status.yaml` 是动态路由唯一可信状态源；`analysis_complexity`、`fanout_mode`、`fix_fanout_mode`、`fix_strategy_mode`、`reroute_target_phase`、重试计数、`phase_history`、`user_inputs`、`non_bug_context`、`parse_error_count`、`rca_fanout_mode_snapshot` 等字段由阶段文件写回，由主编排器读取并执行。
- 恢复已有会话时必须优先识别 `workflow_version` / `schema_version`（v4.1 起 `schema_version = 4`）；旧状态缺字段时，需要先补兼容默认值（迁移脚本：`mobile-qa-workflow/scripts/migrate-workflow-status-v3-to-v4.py`），再恢复阶段执行。
- `current_phase_result` 是 phase 执行期的**运行时变量**（不入持久化字段表），phase 早退前显式 `current_phase_result = ABORT` 让编排器接管 step-pause；编排器侧不读不写持久化镜像。

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
  - **路由与计数**：`analysis_complexity`、`analysis_complexity_confidence`、`fanout_mode`、`fix_fanout_mode`、`fix_strategy_mode`、`fix_risk_level`、`reroute_target_phase`、`reroute_reason`、`rca_retry_count`、`fix_retry_count`、`non_bug_reflow_count`、`lint_retry_count`
  - **历史与快照**：`phase_history`（结构：`{phase, timestamp, fanout_mode, note?}`）、`rca_fanout_mode_snapshot`（P3 完成时 `fanout_mode` 快照，C10 兼容性方案 B 兜底）
  - **step-pause 协议字段**：`user_inputs`（命名空间，编排器 step 4 解析用户回复后总是写入 `user_inputs.<result_field>`）、`parse_error_count`（连续解析失败计数器，进入新 step-pause / 解析成功 / 熔断转 Human-Review 时清零，>= 3 时强制转人工）
  - **Non-Bug 三字段（职责正交）**：`non_bug_reflow_count`（跨轮回流次数）、`non_bug_context`（最近一次 Non-Bug 判定上下文文本，供编排器 case Non-Bug 的 step-pause 标题占位 `{non_bug_context}` 使用）、`non_bug_user_choice`（顶层镜像白名单字段，**v4.1 过渡，v4.2 收敛到 `user_inputs.non_bug_user_choice`**）
- ❌ **不持久化 `current_phase_result`**（D1：phase 执行期运行时变量，不入 schema）
- ⚠️ **顶层镜像字段白名单（v4.1 D8 + D15）**：v4.1 起步白名单 = `{ non_bug_user_choice }`；新增需 PR Review 显式批准并同步 `core/workflow-status-template.yaml` 注释；v4.2 整体收敛后将删除所有顶层镜像字段，编排器统一改读 `user_inputs.<key>`

## Coder Agent 适配

- Full 平台：通过 `<invoke-subagent subagent_type="coder-agent">` 独立运行
- Limited 平台：将契约溯源内联到 Phase 5，由验证阶段审计
- Minimal 平台：外部编排层自行实现 pre-coding contract tracing
