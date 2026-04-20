# B2C 工作流全面分析、PE 复核与优化方案

> 日期：2026-04-18
> 范围：当前仓库内 `mobile-qa-workflow/`、相关 `doc/` 文档，以及与 B2C 工作流直接关联的治理支撑层
> 目标：深入分析当前 B2C 工作流的每个核心模块与文件，重点 review 当前 Markdown 上下文中的 PE 设计、模块间逻辑冲突、语义描述问题，并给出可执行优化方案

---

## 1. 结论摘要

当前 B2C 工作流已经不是“若干 Prompt 的堆叠”，而是一套具备以下四层能力的工程化体系：

1. **入口适配层**：`SKILL.md`、`system-prompt.md`、`PLATFORM-GUIDE.md`
2. **主编排层**：`core/workflow.xml` + `phases/p1~p6`
3. **专项子工作流层**：`functionality-deep-dive/` 与 `ui-ux-analysis/`
4. **评测治理层**：`eval-framework/` + `eval-cases/`

整体判断：

- **架构方向正确**：主链路闭环完整，状态驱动意识较强，子 Agent 分工清晰。
- **Prompt Engineering 基础扎实**：大量关键规则已从自然语言习惯升级为显式契约、模板、状态字段与 I/O 约束。
- **当前主要问题不在“有没有设计”，而在“单一事实源不够彻底、部分字段语义被复用污染、入口文档存在双轨演进、专项元数据承载能力不足”。**

一句话结论：

> 当前 B2C 工作流已具备生产级骨架，但仍存在“状态 schema 设计不够纯净、Full/Limited 双入口口径易漂移、专项元数据只能表示单路上下文、若干 phase 依赖隐式变量”的系统性问题；下一步应从“单一事实源、显式契约、状态结构去歧义、文档治理分层”四个方向收敛。

---

## 2. 审核方法

本次 review 采用静态全量阅读与交叉比对方式完成，重点检查：

1. `mobile-qa-workflow/` 下入口、主编排、阶段、Agent、模板、专项子工作流文件
2. `doc/` 下与 B2C 工作流当前设计、实施、验收直接相关的文档
3. 核心字段在以下载体中的一致性：
   - `workflow-status-template.yaml`
   - `default-config.yaml`
   - `workflow.xml`
   - `phases/*.md`
   - `templates/*.md`
   - `SKILL.md`
   - `system-prompt.md`
4. 模块间 I/O 契约、状态回写、专项回注、平台降级与恢复兼容路径

---

## 3. 当前工作流全景

## 3.1 入口层

| 文件 | 角色 | 当前判断 |
|------|------|---------|
| `mobile-qa-workflow/SKILL.md` | Full 平台统一入口 | 当前最接近真实运行入口 |
| `mobile-qa-workflow/system-prompt.md` | Limited 平台整包入口 | 信息较全，但与分拆文件存在长期漂移风险 |
| `mobile-qa-workflow/PLATFORM-GUIDE.md` | 平台接入说明 | 口径相对新，但更多是说明层而非执行层 |
| `mobile-qa-workflow/install.sh` | Skill 安装脚本 | 非运行逻辑，属于分发辅助 |
| `mobile-qa-workflow/install_trae.sh` | Trae 安装脚本 | 非运行逻辑，属于分发辅助 |

### 判断

- `SKILL.md` 已承担初始化工作区、环境探测、调用主编排器的职责。
- `system-prompt.md` 试图把核心规则、阶段逻辑、模板摘要全部内联，适配无文件引用平台。
- 这两份文件都在描述“整个工作流”，因此天然存在**双份规范**风险。

---

## 3.2 主编排层 `core/`

| 文件 | 角色 | 当前判断 |
|------|------|---------|
| `core/core-rules.xml` | DSL 规则底座、子 Agent 协议、人审协议 | 是最关键的“规则单一事实源”候选 |
| `core/workflow.xml` | 主工作流编排器 | 是当前主流程最可信的执行级定义 |
| `core/workflow-model.yaml` | 六阶段顺序 | 简洁稳定 |
| `core/workflow-status-template.yaml` | 状态模板 | 字段较完善，但部分字段语义混用 |
| `core/default-config.yaml` | 工作区配置与输出路径登记表 | 基础完整，但字段登记仍有遗漏 |

### 判断

- `workflow.xml` 已覆盖：阶段 I/O 契约、状态恢复、重路由、人工停顿、熔断保护。
- `workflow-status-template.yaml` 已引入版本字段、复杂度字段、重试计数、专项工作流字段，方向正确。
- `default-config.yaml` 作为“输出路径注册表”的定位成立，但尚未完全覆盖当前 phase 实际写入的所有键。

---

## 3.3 六阶段 `phases/`

| 文件 | 角色 | 当前判断 |
|------|------|---------|
| `phases/p1-intake.md` | Intake / 分类 / 边界 / 信息门禁 | 成熟，B2C 特征明显 |
| `phases/p2-spec-definition.md` | Spec / Non-Bug / 上下文策展 / 复杂度输出 | 质量高，但存在隐式变量与配置登记缺口 |
| `phases/p3-root-cause.md` | RCA / 动态 fan-out / 专项路由 / 回注 | 主链路最复杂也最关键 |
| `phases/p4-fix-design.md` | 修复策略 / 四重论证 / proposer 路由 | 路由逻辑强，但字段命名污染最明显 |
| `phases/p5-fix-impl.md` | coder-agent 调用 / 文件哨兵 / 实施收口 | 已进入黑盒实施模式，但若干变量仍偏隐式 |
| `phases/p6-verification.md` | 验证 / 失败分类 / 回流 / PR 生成 | 已具备纠偏入口，但与入口文档仍需完全对齐 |

### 判断

- `p1`、`p2`、`p3`、`p4` 的思路完整，明显经过多轮架构打磨。
- `p5` 已完成从“主 Agent 直改代码”到 “coder-agent 黑盒实施”的升级。
- `p6` 已不是简单验收，而是状态回流的控制闸门。

---

## 3.4 主工作流 Agent

| 文件 | 角色 | 当前判断 |
|------|------|---------|
| `agents/curator.md` | 上下文净化与策展 | 职责清晰，边界正确 |
| `agents/investigator.md` | OVHSC 调查员 | 输出结构清晰 |
| `agents/challenger.md` | 主流程 challenger 包装层 | 已改为共享基座包装层 |
| `agents/shared-challenger-base.md` | challenger 共享基座 | 收敛效果好 |
| `agents/arbiter.md` | 主流程 arbiter 包装层 | 已改为共享基座包装层 |
| `agents/shared-arbiter-base.md` | arbiter 共享基座 | 统一了 `final_confidence` 口径 |
| `agents/fix-proposer.md` | 修复方案设计 | 约束清晰 |
| `agents/coder-agent.md` | 实施专员 | P5 能力隔离的关键 |

### 判断

- 主链路 6 个核心业务角色目前仍然合理，不建议粗暴合并。
- 共享基座 + 包装层设计已经落地，是当前 Prompt 设计中最健康的一部分。

---

## 3.5 主工作流知识与模板层

### `reference/`

| 文件 | 角色 |
|------|------|
| `reference/analysis-strategies.md` | RCA 动态策略知识 |
| `reference/fix-strategies.md` | 修复策略知识 |
| `reference/platform-checklist.md` | Android/iOS 平台约束与检查点 |
| `reference/reasoning-chain.md` | OVHSC 推理链定义 |

### `templates/`

| 文件 | 角色 |
|------|------|
| `templates/issue-card.md` | Intake 产物模板 |
| `templates/intake-form.md` | Intake 信息采集模板 |
| `templates/intake-form-blank.md` | 空白采集表 |
| `templates/spec.md` | Spec 模板，含复杂度路由区块 |
| `templates/context-curation-report.md` | 策展报告模板 |
| `templates/context-bundle.md` | RCA 证据包模板 |
| `templates/rca-report.md` | RCA 报告模板 |
| `templates/fix-design.md` | 修复设计模板 |
| `templates/contract-checklist.md` | 契约溯源模板 |
| `templates/impl-report.md` | 实施报告模板 |
| `templates/error-dump.md` | 失败现场模板 |
| `templates/verification-report.md` | 验证报告模板 |
| `templates/knowledge-card.md` | 抽象知识沉淀模板 |

### 判断

- 模板体系很完整，是当前工作流“可审计”的核心基础。
- 模板层整体质量高，但与 phase/config/入口文档之间仍有少量登记不一致。

---

## 3.6 Functionality Deep-Dive 子工作流

### 说明与编排

| 文件 | 角色 |
|------|------|
| `functionality-deep-dive/FUNCTIONALITY_DEEP_DIVE_WORKFLOW_V3.md` | 功能疑难专项说明 |
| `functionality-deep-dive/core/workflow.xml` | 专项编排器 |
| `functionality-deep-dive/core/workflow-model.yaml` | F1-F5 阶段定义 |
| `functionality-deep-dive/core/default-config.yaml` | 子工作流默认配置 |
| `functionality-deep-dive/core/workflow-status-template.yaml` | 子工作流状态模板 |

### 阶段

| 文件 | 角色 |
|------|------|
| `functionality-deep-dive/phases/f1-context-reconstruction.md` | 环境与上下文重建 |
| `functionality-deep-dive/phases/f2-state-topology.md` | 状态拓扑 |
| `functionality-deep-dive/phases/f3-temporal-correlation.md` | 时序与并发 |
| `functionality-deep-dive/phases/f4-isolation-debate.md` | 专项隔离与收敛 |
| `functionality-deep-dive/phases/f5-defensive-fix-design.md` | 防御性修复附录 |

### Agent

| 文件 | 角色 | 状态 |
|------|------|------|
| `agents/deep-dive-context-analyst.md` | 复合环境分析角色 | 现行 |
| `agents/deep-dive-structure-analyst.md` | 复合结构分析角色 | 现行 |
| `agents/deep-dive-race-and-isolation-analyst.md` | 复合时序/隔离角色 | 现行 |
| `agents/deep-dive-arbiter.md` | 专项七维质疑 + 仲裁 | 现行 |
| `agents/defensive-fix-architect.md` | 防御性修复设计 | 现行 |
| `agents/context-reconstructor.md` | 旧角色 | 兼容保留 |
| `agents/state-analyst.md` | 旧角色 | 兼容保留 |
| `agents/temporal-analyst.md` | 旧角色 | 兼容保留 |
| `agents/challenger.md` | 旧专项 challenger | 兼容保留 |
| `agents/arbiter.md` | 旧专项 arbiter | 兼容保留 |
| `agents/README.md` | 角色说明 | 当前与现状一致 |

### 模板与参考

| 文件 | 角色 |
|------|------|
| `templates/functionality-deep-dive-rca.md` | 专项 RCA 模板 |
| `templates/deep-dive-summary.md` | 回注摘要模板 |
| `templates/defensive-fix-design.md` | 防御性修复模板 |
| `templates/environment-factor-report.md` | 可选环境因子报告 |
| `templates/deep-dive-topology.md` | 可选拓扑报告 |
| `templates/concurrency-analysis-report.md` | 可选并发报告 |
| `reference/environment-factor-thresholds.md` | 环境阈值知识 |
| `reference/state-machine-patterns.md` | 状态机模式 |
| `reference/race-condition-patterns.md` | 竞态模式 |
| `reference/isolation-patterns.md` | 隔离模式 |
| `reference/README.md` | 参考说明 |

### 判断

- Functionality Deep-Dive 已从“细粒度旧角色拓扑”收敛到“复合角色拓扑”。
- 当前主流程与专项流程的关系基本闭合。
- 仍需注意与主流程 `specialized_workflow` 元数据结构的匹配问题。

---

## 3.7 UI/UX 深度分析（主流程内） 子工作流

### 编排与配置

| 文件 | 角色 | 当前判断 |
|------|------|---------|
| `ui-ux-analysis/core/workflow.xml` | UI 专项编排器 | 最小可运行，但成熟度明显低于主流程与功能专项 |
| `ui-ux-analysis/core/workflow-model.yaml` | U1-U4 阶段序列 | 存在，但当前编排器未真正使用 |
| `ui-ux-analysis/core/default-config.yaml` | UI 默认配置 | 极简 |
| `ui-ux-analysis/core/workflow-status-template.yaml` | UI 状态模板 | 过于轻量，恢复/追踪信息不足 |

### 阶段与 Agent

| 文件 | 角色 |
|------|------|
| `ui-ux-analysis/phases/u1-context-and-visual-baseline.md` | UI 环境与视觉基线 |
| `ui-ux-analysis/phases/u2-layout-topology.md` | 布局拓扑 |
| `ui-ux-analysis/phases/u3-render-timing-and-interaction.md` | 渲染与交互时序 |
| `ui-ux-analysis/phases/u4-ui-ruling.md` | UI 专项裁定 |
| `ui-ux-analysis/agents/ui-context-analyst.md` | UI 现场分析 |
| `ui-ux-analysis/agents/ui-structure-analyst.md` | UI 结构分析 |
| `ui-ux-analysis/agents/ui-render-and-interaction-analyst.md` | UI 渲染与交互分析 |
| `ui-ux-analysis/agents/ui-ux-analysis-arbiter.md` | UI 裁定 |
| `ui-ux-analysis/templates/ui-ux-analysis-rca.md` | UI RCA 模板 |
| `ui-ux-analysis/templates/ui-ux-analysis-summary.md` | UI 摘要模板 |
| `ui-ux-analysis/reference/ui-patterns.md` | UI 模式库 |

### 判断

- UI/UX 深度分析（主流程内） 已具备最小链路，但当前更接近“第一版专项样板”，未达到主流程等成熟度。
- 当前 UI 专项最明显问题是：**恢复能力、状态粒度、显式参数契约和降级分支都不够完整**。

---

## 3.8 评测治理层

### `eval-framework/`

当前重要文件包括：

- `coordinator.py`
- `baseline_runner.py`
- `artifact_checker.py`
- `judge.py`
- `scoring_engine.py`
- `quality_gate.py`
- `report_generator.py`
- `comparator.py`
- `optimizer.py`
- `iteration_loop.py`
- `session_manager.py`
- `weakness_detector.py`
- `artifact-checklist.yaml`
- `case-schema.yaml`
- `scoring-rubric-base.yaml`
- `auto-reply-rules.yaml`
- `configs/*.yaml`
- `tests/test_judge_parse.py`

### `eval-cases/`

`eval-cases/seed-10/` 下各 case 结构统一，包含：

- `metadata.yaml`
- `input/issue-description.md`
- `input/logs/README.md`
- `input/code-snapshot/README.md`
- `ground-truth/expected-root-cause.md`
- `ground-truth/expected-contributing.md`
- `ground-truth/expected-fix-direction.md`
- `ground-truth/scoring-rubric.yaml`

### 判断

- 评测层不是运行路径，但它决定了“结构优化是否真的有效”。
- 当前设计文档多次强调“以评测数据而非体感裁剪 Agent”，这条原则是正确的。

---

## 3.9 `doc/` 文档层

当前与 B2C 工作流直接相关的核心文档可分四类：

### A. 当前设计/实施参考

- `doc/B2C_WORKFLOW_SUBAGENT_FINAL_ADOPTION_2026-04-18.md`
- `doc/B2C_WORKFLOW_SUBAGENT_IMPLEMENTATION_CHECKLIST_2026-04-18.md`
- `doc/B2C_WORKFLOW_SUBAGENT_BATCH_ABC_EXEC_TASKS_2026-04-18.md`
- `doc/B2C_WORKFLOW_BATCH_ABC_PR_DESCRIPTION_2026-04-18.md`
- `doc/B2C_WORKFLOW_SUBAGENT_SPLIT_REVIEW_2026-04-18.md`

### B. 运行前置与兼容规划

- `doc/B2C_WORKFLOW_SUBAGENT_BATCH_A0_FILE_PLAN_2026-04-18.md`
- `doc/B2C_WORKFLOW_SUBAGENT_BATCH_A0_EXEC_TASKS_2026-04-18.md`

### C. 历史专项评审

- `doc/B2C_WORKFLOW_CODER_SUBAGENT_QA_REPORT_2026-04-17.md`
- `doc/CODER_SUBAGENT_V2_1_MUST_FIX_CHECKLIST_2026-04-17.md`
- `doc/CODER_SUBAGENT_V3_QA_REPORT_2026-04-17.md`
- `doc/CODER_SUBAGENT_V3_1_IMPLEMENTATION_AND_CONSTRUCTION_QA_REPORT_2026-04-17.md`
- `doc/CODER_SUBAGENT_CONSTRUCTION_PLAN_V1_1_REVIEW_2026-04-17.md`
- `doc/CODER_SUBAGENT_FIX_COMPARISON_REPORT_2026-04-18.md`

### D. 其他历史架构材料

- `doc/DEEP_DIVE_WORKFLOW_V3_ARCHITECTURE_PROPOSAL.md`
- `doc/DEEP_DIVE_WORKFLOW_V3_BREAKDOWN.md`
- `doc/FUNCTIONALITY_DEEP_DIVE_V3_FILE_CHECKLIST.md`
- `doc/coder-workflow-design.md`
- `doc/LOUPE_*`
- `doc/Loupe_V1.2_Code_Review_Report.md`

### 判断

- `doc/` 当前最大问题不是“内容少”，而是**现行规范、施工计划、历史评审、验收复盘混放**。
- 如果缺少明确标签，使用者很容易把“历史计划文档”误读为“当前执行规范”。

---

## 4. 当前 PE 设计的优点

这里的 PE 指 Prompt Engineering 与上下文编排设计，而不仅是单个角色 Prompt 文案。

## 4.1 强项

1. **规则已结构化**
   - 核心规则从自然语言升级为 `core-rules.xml` 可执行约束。

2. **阶段职责分离明确**
   - P1/P2/P3/P4/P5/P6 基本对应真实工程闭环。

3. **动态路由思想成立**
   - P3 复杂度 fan-out、P4 风险 fan-out、P6 失败回流形成基本闭环。

4. **上下文污染控制意识强**
   - `curator`、Context Bundle、证据等级与存活性机制设计成熟。

5. **实施质量隔离意识成立**
   - `coder-agent` 使实施噪音从主推理上下文剥离。

6. **专项工作流的回注接口已定义**
   - 主流程能够消费专项摘要，而不是专项分析与主链路割裂。

7. **评测导向正确**
   - 文档层已经明确“不能为了减 Agent 而减 Agent”。

---

## 5. 关键问题与冲突清单

以下问题按影响范围排序。

## 5.1 P0 级问题

### P0-1 `fanout_mode` 发生语义污染，P3 与 P4 共用同一字段承载不同概念

相关位置：

- `mobile-qa-workflow/core/workflow-status-template.yaml`
- `mobile-qa-workflow/phases/p3-root-cause.md`
- `mobile-qa-workflow/phases/p4-fix-design.md`

现状：

- P3 中 `fanout_mode` 表示 RCA 路由模式，例如 `simple-single / medium-challenge / complex-arbitrated`
- 但 P4 中又把 `fix_strategy_mode` 同时写入 `fanout_mode`

问题本质：

- 一个字段承载了两个阶段、两类不同语义的模式值。
- 这会破坏状态字段“单字段单语义”的可审计性。

风险：

1. 后续主编排器或评测系统读取 `fanout_mode` 时无法判断其属于 RCA 还是 Fix。
2. 文档中“动态 fan-out”的统计口径会被污染。
3. Debug 和回放时会出现“状态值合法但语义错位”的隐蔽问题。

结论：

- 这是当前状态 schema 中最明显的设计缺陷之一。

### P0-2 `specialized_workflow` 结构只能描述一路专项，无法稳定承载 Functionality 与 UI 双专项并存

相关位置：

- `mobile-qa-workflow/core/workflow-status-template.yaml`
- `mobile-qa-workflow/phases/p3-root-cause.md`

现状：

- `workflow-status-template.yaml` 中 `specialized_workflow` 只有一组 `mode/status/sub_workspace/trigger_reason/merge_strategy`
- P3 既可触发 `functionality-deep-dive`，也可触发 `ui-ux-analysis`
- 每次触发都会覆写同一组 `specialized_workflow.*` 字段

问题本质：

- 状态结构只支持“当前有一个专项”，但流程逻辑已经允许“同一 Case 触发多个专项”。

风险：

1. 第二个专项会覆盖第一个专项的元数据。
2. 最终状态文件无法回答“这个 Case 实际触发了哪些专项”。
3. 评测层如果依赖 `specialized_workflow.mode` 统计收益，会出现统计失真。

结论：

- 这是典型的“流程能力已经升级，状态结构还停留在旧模型”的冲突。

### P0-3 Full / Limited 双入口未形成真正的单一事实源

相关位置：

- `mobile-qa-workflow/SKILL.md`
- `mobile-qa-workflow/core/workflow.xml`
- `mobile-qa-workflow/system-prompt.md`

现状：

- `SKILL.md + core/workflow.xml + phases/*.md` 是拆分式真实执行定义
- `system-prompt.md` 是一份内联大 Prompt
- 两者都在描述完整工作流

具体表现：

1. `system-prompt.md` 顶层状态机较简化，未完整镜像主编排器中的所有状态分支与收口逻辑
2. `system-prompt.md` 更像“手工同步版规范”，而不是从拆分源自动生成的产物

风险：

1. Full 平台与 Limited 平台长期行为漂移
2. 文档口径与真实执行口径产生双轨
3. 未来修复时容易“只改分拆文件”或“只改内联 Prompt”

结论：

- 当前仓库已经多次在文档中提醒这个风险，说明它不是理论问题，而是现实维护压力。

---

## 5.2 P1 级问题

### P1-1 多个 phase 依赖隐式变量，参数契约没有在文件头显式声明完整

相关位置：

- `phases/p2-spec-definition.md`
- `phases/p3-root-cause.md`
- `phases/p4-fix-design.md`
- `phases/p5-fix-impl.md`
- `phases/p6-verification.md`
- `ui-ux-analysis/phases/u1~u4`

现状：

- 文件头参数区只声明了部分变量
- 但正文中直接使用了 `{env_subagent}`、`{env_git}`、`{output_impl_report}` 等变量

问题本质：

- 运行时能传，不代表契约是清晰的。
- 这会让 phase 文件从“显式 DSL”退化成“部分依赖上下文默契”。

风险：

1. Limited 平台或后续引擎接入者无法确定必需输入。
2. 新维护者难以判断变量来源。
3. 更容易出现“阶段文件能跑，但头部参数说明不真实”的语义偏差。

结论：

- 这是典型的 PE 文档性问题，会削弱 Prompt 可维护性。

### P1-2 配置登记表与 phase 实际输出不完全一致

相关位置：

- `mobile-qa-workflow/phases/p2-spec-definition.md`
- `mobile-qa-workflow/core/default-config.yaml`
- `mobile-qa-workflow/core/workflow.xml`

现状：

- P2 最终会写入 `output_curation_report`
- 但 `default-config.yaml` 没有该字段
- 主编排器的 I/O 契约也没有把 `context-curation-report.md` 作为 Phase 2 产物显式列出

问题本质：

- 配置登记、阶段输出、编排 I/O 三个层面未完全一致。

风险：

1. 产物存在但不在统一登记表中。
2. 下游或评测层如果依赖配置登记读取文件，会遗漏该产物。
3. 新人容易误判 `context-curation-report.md` 是“非标准输出”。

结论：

- 这属于“工程化最后一公里未收口”的问题。

### P1-3 UI/UX 深度分析（主流程内） 的编排与状态成熟度明显低于主流程和功能专项

相关位置：

- `ui-ux-analysis/core/workflow.xml`
- `ui-ux-analysis/core/workflow-model.yaml`
- `ui-ux-analysis/core/workflow-status-template.yaml`
- `ui-ux-analysis/phases/u1-context-and-visual-baseline.md`
- `ui-ux-analysis/phases/u4-ui-ruling.md`

现状：

- `workflow-model.yaml` 已存在，但 `workflow.xml` 没有像主流程/功能专项一样按 `stepsCompleted` 判定当前阶段
- 状态模板过于轻量，缺少 `last_updated`、`current_stage`、兼容字段等
- U1/U2/U3/U4 使用 `{env_subagent}`，但 phase 头部未声明
- U1 若 `{env_subagent} == false` 没有明确降级分支

问题本质：

- UI/UX 深度分析（主流程内） 已接入主流程，但自身仍是“最小可运行实现”，尚未达到同等级工程约束。

风险：

1. UI 专项中断恢复能力差
2. 降级平台行为不稳定
3. 与主流程关于“状态驱动恢复”的设计哲学不一致

结论：

- UI/UX 深度分析（主流程内） 当前应被视为“已接入、未完全产品化”。

### P1-4 `specialized_workflow.status` 的值域定义不闭合

相关位置：

- `mobile-qa-workflow/phases/p5-fix-impl.md`
- `mobile-qa-workflow/phases/p3-root-cause.md`
- `mobile-qa-workflow/functionality-deep-dive/core/workflow.xml`

现状：

- P5 判断条件写的是 `specialized_workflow.status ∈ {DD-Completed, Merged}`
- 但功能专项编排器本身设置的是 `DD-Completed`
- 主流程回注时更新的是 `merge_strategy = merged-into-main-rca`，不是 `status = Merged`

问题本质：

- 设计中出现了“想表达已合并”与“实际状态值”不一致的问题。

风险：

1. 代码阅读者会误以为存在 `Merged` 状态
2. 后续如果有人真按 `Merged` 扩展，会形成另一套并行语义

结论：

- 这是明显的语义描述问题，应统一状态值与合并标记职责。

---

## 5.3 P2 级问题

### P2-1 `doc/` 层“唯一执行口径”与“历史计划文档混放”存在治理冲突

相关位置：

- `doc/B2C_WORKFLOW_SUBAGENT_FINAL_ADOPTION_2026-04-18.md`
- `doc/B2C_WORKFLOW_SUBAGENT_IMPLEMENTATION_CHECKLIST_2026-04-18.md`
- `doc/B2C_WORKFLOW_SUBAGENT_BATCH_ABC_EXEC_TASKS_2026-04-18.md`
- `doc/B2C_WORKFLOW_BATCH_ABC_PR_DESCRIPTION_2026-04-18.md`
- `doc/B2C_WORKFLOW_CODER_SUBAGENT_QA_REPORT_2026-04-17.md`

现状：

- `FINAL_ADOPTION` 声称自己是“唯一执行口径”
- 但 `IMPLEMENTATION_CHECKLIST`、`BATCH_ABC_EXEC_TASKS` 属于施工分解文档
- `PR_DESCRIPTION` 描述的是“已落地现状”
- `QA_REPORT` 又在描述“尚未落地”的历史状态

问题本质：

- 文档的“时态”和“规范等级”没有显式标记。

风险：

1. 阅读者容易把历史文档当现行规范
2. 会出现“明明已经上线，但文档仍写未落地”的语义冲突

结论：

- 当前 `doc/` 更像知识仓库，不像有治理规则的规范目录。

### P2-2 UI 与 Functionality 专项在“产品化成熟度”上不对称

现状：

- Functionality Deep-Dive 已有版本兼容、复合角色、可选产物策略
- UI/UX 深度分析（主流程内） 只有最小可运行拓扑

影响：

- 主流程对两个专项的接入方式已统一，但两个专项的可维护性和恢复能力并不对等。

### P2-3 局部描述仍存在“计划态文案残留”

现状：

- 若干 `doc/` 文件仍用“待改造”“不要提前同步”“后续批次”等工程计划语气
- 与当前代码库已落地状态同时存在

影响：

- 对当前审阅者不友好
- 会放大 PE 上下文歧义

---

## 6. 模块间逻辑冲突总结

综合来看，当前最核心的模块间冲突有 6 类：

1. **状态字段冲突**
   - `fanout_mode` 被 P3 与 P4 复用

2. **专项元数据冲突**
   - `specialized_workflow` 无法表达多专项并存

3. **入口规范冲突**
   - `system-prompt.md` 与拆分式主流程并非自动同步

4. **契约显式性冲突**
   - phase 头部参数区与正文真实依赖不完全一致

5. **配置登记冲突**
   - `default-config.yaml` 未完全覆盖真实输出

6. **文档时态冲突**
   - 现行规范、施工计划、历史评审混放

---

## 7. 优化方案

以下方案按优先级给出。

## 7.1 P0：状态 schema 去歧义

### 方案 A：拆分 RCA 与 Fix 路由字段

建议把当前：

- `fanout_mode`
- `fix_strategy_mode`

调整为更清晰的状态结构，例如：

```yaml
routing:
  rca_mode: null
  fix_mode: null
  rca_complexity: null
  rca_complexity_confidence: null
  fix_risk_level: null
```

最低限度也应改为：

- `rca_fanout_mode`
- `fix_strategy_mode`

不要再让 `fanout_mode` 同时承载两种语义。

### 方案 B：重构专项状态结构

建议把：

```yaml
specialized_workflow:
  mode: null
  status: null
  sub_workspace: null
  trigger_reason: null
  merge_strategy: null
```

升级为可表示多专项的结构，例如：

```yaml
specialized_workflows:
  functionality:
    triggered: false
    status: null
    sub_workspace: null
    trigger_reason: null
    merge_strategy: null
  ui:
    triggered: false
    status: null
    sub_workspace: null
    trigger_reason: null
    merge_strategy: null
```

收益：

1. 同一 Case 可同时保留功能专项与 UI 专项痕迹
2. 评测与回放更稳定
3. 不再发生元数据覆写

---

## 7.2 P0：建立真正的单一事实源

建议明确三层权威性：

1. **执行级权威源**
   - `core/workflow.xml`
   - `phases/*.md`
   - `agents/*.md`
   - `templates/*.md`
   - `core/*.yaml`

2. **平台适配产物**
   - `SKILL.md`
   - `system-prompt.md`
   - 它们不应再被视为并行设计源，而应视为“入口包装”

3. **说明文档**
   - `doc/` 下文档只做解释与治理，不再承担执行规范定义职责

最好做法：

- 建立一个“由拆分源生成 `system-prompt.md`”的流程
- 或至少建立一致性检查脚本，校验关键字段、状态枚举、角色列表是否一致

---

## 7.3 P1：把 phase 头部参数声明补齐为真实契约

建议新增一条规范：

> 任何在 phase 正文中使用的 `{variable}`，必须在文件头参数区或静态变量区显式声明来源。

可执行动作：

1. 补齐 `env_subagent`、`env_git`、`issue_id`、`output_*` 等变量声明
2. 对 `ui-ux-analysis/phases/*.md` 做同样治理
3. 为 phase 文件增加轻量契约检查脚本，扫描“正文变量引用”与“头部声明”差异

收益：

- Prompt/DSL 的可维护性显著提升
- 有利于后续平台迁移

---

## 7.4 P1：统一 I/O 契约、配置登记与模板输出

建议建立“三表一致”原则：

1. `workflow.xml` 的 `<io-contract>`
2. `default-config.yaml` 的输出键
3. phase 最终 `<template-output>` 与配置回写动作

针对当前问题，至少应：

1. 为 `context-curation-report.md` 补齐标准输出登记
2. 明确它是否属于 Phase 2 正式产物
3. 如果是正式产物，就同时更新：
   - `workflow.xml`
   - `default-config.yaml`
   - 相关平台入口说明

---

## 7.5 P1：把 UI/UX 深度分析（主流程内） 提升到与 Functionality 同等级的编排成熟度

建议分两步：

### 第一步：补齐状态与恢复能力

补齐：

- `current_stage`
- `last_updated`
- `schema_version`
- `stepsCompleted`
- 兼容字段或恢复策略

### 第二步：补齐编排器一致性

让 `ui-ux-analysis/core/workflow.xml`：

1. 读取 `workflow-model.yaml`
2. 基于 `stepsCompleted` 判断当前阶段
3. 更新 `lastStep`
4. 明确 `env_subagent == false` 的降级路径

收益：

- UI 专项不再只是“挂接进去能跑”
- 而是真正与主流程保持同一工程哲学

---

## 7.6 P1：修正文档治理模型

建议为 `doc/` 增加分层与标签：

### 目录分层建议

- `doc/current/`
  - 当前现行架构与规范
- `doc/implementation-history/`
  - 批次计划、施工记录、PR 说明
- `doc/reviews/`
  - QA 报告、评审结论
- `doc/archive/`
  - 已过时材料

### 文档头部强制标签

每份文档增加：

- `Document-Type`: spec / plan / review / history
- `Status`: current / historical / archived
- `Source-of-Truth`: yes / no

收益：

1. 降低“历史计划文档误当现行规范”的风险
2. 改善后续 PE 上下文质量
3. 提升团队认知一致性

---

## 7.7 P2：增加一致性校验与文档编译流程

建议新增轻量治理工具，至少覆盖：

1. **状态字段一致性校验**
   - 检查 `workflow-status-template.yaml` 中字段是否被入口、phase、评测同时识别

2. **变量声明校验**
   - 检查 phase 中引用的变量是否显式声明

3. **入口文档一致性校验**
   - 检查 `SKILL.md`、`system-prompt.md`、`PLATFORM-GUIDE.md` 中关键枚举是否一致

4. **文档时态校验**
   - 阻止“历史审计文档”被误标为当前规范

---

## 8. 推荐整改顺序

### 第一批：先改状态与入口单一事实源

1. 拆分 `fanout_mode` 语义
2. 重构 `specialized_workflow` 结构
3. 明确 `core/ + phases/ + templates/` 为执行级唯一事实源

### 第二批：再改 phase 契约显式性

1. 补齐各 phase 参数头
2. 补齐 `default-config.yaml` 输出登记
3. 对 `context-curation-report.md` 等边缘产物完成三表一致收口

### 第三批：专项产品化收尾

1. 提升 UI/UX 深度分析（主流程内） 的恢复与降级能力
2. 统一两个专项的状态与元数据表达方式

### 第四批：治理自动化

1. 增加一致性校验脚本
2. 建立 `system-prompt.md` 自动生成或自动对账流程
3. 重构 `doc/` 分层

---

## 9. 最终判断

### 9.1 对当前 B2C 工作流的判断

- **主架构成熟度**：高
- **主链路模块边界**：整体清晰
- **PE 结构化程度**：高
- **当前最大问题**：不是能力缺失，而是“语义治理还不够纯”

### 9.2 对当前 Markdown 上下文 PE 的判断

当前 Markdown 体系的优点在于：

- 信息完整
- 角色、阶段、模板、状态字段都较明确
- 可审计性强

当前 Markdown 体系的主要问题在于：

- 多份文件共同定义同一概念
- 部分隐式变量削弱契约透明度
- 历史文档与现行规范混放，降低上下文纯度

### 9.3 一句话建议

> 当前最该做的不是继续加新角色，而是把已有规则体系再“净化一层”：让每个字段只有一个语义、每个入口只有一个权威源、每份文档都有明确时态、每个阶段只依赖显式声明的上下文。

---

## 10. 本次 review 建议作为后续整改输入的优先项

1. **拆分 `fanout_mode` 与 `fix_strategy_mode` 的状态职责**
2. **把 `specialized_workflow` 升级为可表达多专项并存的结构**
3. **明确拆分式流程文件为唯一执行事实源，限制 `system-prompt.md` 成为同步产物**
4. **补齐各 phase 的显式参数契约**
5. **收口 `default-config.yaml`、I/O 契约与真实输出的差异**
6. **把 UI/UX 深度分析（主流程内） 从“最小可运行”升级到“可恢复、可降级、可审计”**
7. **重构 `doc/` 目录，显式区分 current / plan / review / archive**

