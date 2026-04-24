# Mobile QA Workflow — 平台集成指南

## 概述

本工作流采用 XML 标签化 DSL 进行编排，可在 Full 与 Limited 两类平台运行。

## 角色口径

> 详见 [`SKILL.md`](./SKILL.md)「角色口径」节。

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
- `workflow-status.yaml` 是动态路由唯一可信状态源；字段定义与语义以 [`core/workflow-status-template.yaml`](./core/workflow-status-template.yaml) 为权威。
- 运行时恢复与 step-pause 写入协议以 [`SKILL.md`](./SKILL.md)「运行时恢复约束 / workflow_status 关键字段」为准。

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
- 至少持久化字段：完整字段定义见 [`core/workflow-status-template.yaml`](./core/workflow-status-template.yaml)，最小使用说明见 [`SKILL.md`](./SKILL.md)「workflow_status 关键字段」节
- ❌ **不持久化 `current_phase_result`**（D1：运行时变量）

## Coder Agent 适配

- Full 平台：通过 `<invoke-subagent subagent_type="coder-agent">` 独立运行
- Limited 平台：将契约溯源内联到 Phase 5，由验证阶段审计
- Minimal 平台：外部编排层自行实现 pre-coding contract tracing
