# B2C 工作流严谨分析报告

> 日期：2026-04-18
> 范围：`mobile-qa-workflow/`、`eval-framework/`、`eval-cases/seed-10/`、`doc/` 中与 B2C 工作流直接相关的设计、编排、评测与治理材料
> 目标：在不跳过关键组成部分的前提下，对当前 B2C 工作流做文件级审视，并对 `B2C_WORKFLOW_ARCHITECTURE_REVIEW_2026-04-18.md` 与 `B2C_WORKFLOW_COMPREHENSIVE_REVIEW_2026-04-18.md` 做交叉验证、补充与收敛

---

## 1. 审核方法与覆盖范围

本次审查采用四层交叉法：

1. **入口与编排层静态阅读**
   - 覆盖 `SKILL.md`、`PLATFORM-GUIDE.md`、`system-prompt.md`
   - 覆盖 `core/*.xml|yaml`
   - 覆盖主工作流 `phases/p1~p6`
2. **角色、模板、知识层静态阅读**
   - 覆盖主工作流 `agents/`、`templates/`、`reference/`
   - 覆盖 `functionality-deep-dive/` 与 `ui-ux-analysis/` 的核心编排、阶段、角色、模板、参考材料
3. **评测治理层静态阅读**
   - 覆盖 `eval-framework/` 核心 Python、YAML、测试
   - 重点核对状态字段、产物契约、评测指标与工作流状态是否一致
4. **Case 数据层抽样与结构校验**
   - 覆盖 `eval-cases/seed-10/` 全部 case 的元数据
   - 重点阅读代表性 `case-001-state-machine-race`
   - 验证 case schema、ground truth 与动态路由口径是否一致

覆盖统计：

- `mobile-qa-workflow/`: 88 个文件
- `eval-framework/`: 22 个文件
- `eval-cases/seed-10/`: 80 个文件
- `doc/`: 25 个 Markdown 文档

结论可信度说明：

- **高可信**：来自当前仓库执行级文件的直接证据
- **中高可信**：来自设计文档与执行文件交叉一致的判断
- **中可信**：来自文档意图与代码现状存在偏差时的推断性治理建议

---

## 2. 总体判断

当前 B2C 工作流已经具备明显的工程化骨架，不再是“若干 Prompt 堆叠”，而是由以下四层构成：

1. **入口适配层**
   - `SKILL.md`
   - `system-prompt.md`
   - `PLATFORM-GUIDE.md`
2. **主编排层**
   - `core/workflow.xml`
   - `core/workflow-status-template.yaml`
   - `phases/p1~p6`
3. **专项子工作流层**
   - `functionality-deep-dive/`
   - `ui-ux-analysis/`
4. **评测治理层**
   - `eval-framework/`
   - `eval-cases/`

整体成熟度判断：

- **架构方向正确**：主链路已形成 Intake -> Spec -> RCA -> Fix -> Impl -> Verification 的完整闭环。
- **Prompt Engineering 结构化程度高**：大量规则已落成 DSL、模板、状态字段、I/O 契约，而不是停留在自然语言约定。
- **当前主要问题不是能力缺失，而是语义治理不够纯净**：状态字段复用、入口双事实源、评测口径与模板口径错位、专项状态结构不足，是现阶段的核心矛盾。

一句话结论：

> 当前 B2C 工作流已具备生产级主骨架，但尚未完成“单一事实源、单字段单语义、模板与评测对齐、专项状态结构可扩展、入口口径自动同步”这五个治理闭环。

---

## 3. 分层分析

## 3.1 入口适配层

### `mobile-qa-workflow/SKILL.md`

定位：

- 是 Full 能力平台的主入口。
- 负责初始化工作区、恢复旧会话、探测环境能力、加载主编排器。

优点：

- 已明确恢复兼容规则。
- 已明确 `P3 / P4 / P6` 的动态路由必须写入 `workflow-status.yaml`。
- 已明确子 Agent 参数通过调用处显式注入，避免假设 `agents/*.md` 内部可模板渲染。

问题：

- 它与 `system-prompt.md` 同时描述“完整工作流”，形成双份规范。

### `mobile-qa-workflow/system-prompt.md`

定位：

- 是 Limited 平台的整包内联版。
- 同时内联核心规则、阶段逻辑、模板摘要、参考知识。

优点：

- 对无外部文件引用的平台极具可移植性。
- 信息完整，便于快速理解全貌。

问题：

- 它不是由拆分式执行源自动生成，而是手工维护版，存在长期漂移风险。
- 仍保留明显的 SubAgent 编排口径，对“纯 Chat 单体模型”并不完全自然。
- 与当前 `ui-ux-analysis` 已落地状态相比，部分摘要仍带有“future/最小化描述”痕迹。

### `mobile-qa-workflow/PLATFORM-GUIDE.md`

定位：

- 是平台接入说明层，不是执行源。

优点：

- 已明确区分业务角色与能力型 Agent。
- 已明确 Full / Limited 平台的接入方式。

问题：

- 仍沿用 `fanout_mode` 作为统一动态路由字段口径，未揭示它在 P3/P4 被复用污染的现实问题。

结论：

- 入口层最大的风险是**双入口并行维护**，而不是内容贫弱。

---

## 3.2 主编排层 `core/`

### `core/core-rules.xml`

定位：

- 是工作流 DSL 规则底座。

优点：

- 清晰定义支持标签、子 Agent 启动协议、人审协议、结构化路由协议。
- `invoke-subagent` 的黑盒透传原则写得很明确。

问题：

- 仍保留大量“旧专项角色仅兼容恢复”的知识，增加上下文负担。
- `workflow-status-routing` 仍把 `fanout_mode` 作为动态路由主字段之一，没有从 schema 层拆分 RCA/Fix 语义。

### `core/workflow.xml`

定位：

- 主工作流最可信的执行级定义。

优点：

- I/O 契约清晰。
- 恢复逻辑、重路由逻辑、熔断逻辑已经成型。
- 能正确识别 `reroute_target_phase` 并支持 `qa-root-cause` / `qa-fix-design` 重入。

问题：

- 与 `p1` / `p2` 中的交互控制流存在重复接管。
- 过于依赖结构化状态字段的语义正确性，一旦字段被污染，整个路由与评测都会偏移。

### `core/workflow-status-template.yaml`

定位：

- 当前工作流状态的唯一结构化快照模板。

优点：

- 已有版本字段、复杂度字段、重试计数、专项状态槽位。

问题：

- `fanout_mode` 与 `fix_strategy_mode` 同时存在，但 P4 仍把 `fix_strategy_mode` 写进 `fanout_mode`，破坏单字段单语义。
- `specialized_workflow` 只有单槽位，只适合“一次只有一个专项”的旧模型。

### `core/default-config.yaml`

定位：

- 工作区配置与产物路径登记表。

优点：

- 主产物与专项产物路径基本齐全。

问题：

- `output_curation_report` 未登记，但 P2 实际会写。

结论：

- `core/` 已具备编排基础，但状态 schema 仍是当前最需要治理的源头。

---

## 3.3 六阶段 `phases/`

### P1 `p1-intake.md`

优点：

- 双场景 intake 设计成熟。
- 分类树、边界等级、锚点强弱、最小信息集门禁都体现了 B2C 问题受理经验。

问题：

- `ask + goto` 已在 Phase 内部接管暂停与恢复，而主编排器也接管 `Info-Insufficient`，形成双控制流。

### P2 `p2-spec-definition.md`

优点：

- 把 Spec、Non-Bug、复杂度判定、Context Curation 融合在同一阶段，逻辑上合理。
- `Analysis Complexity / Suggested Fan-out Mode` 已落到模板与状态。

问题：

- `env_subagent` 等变量在正文中使用，但文件头未显式声明。
- `context-curation-report.md` 会被输出，但 config 与主 I/O 清单未完全同步。
- `step-pause` 与主编排器 `Spec-Uncertain / Non-Bug` 路由存在重复接管。

### P3 `p3-root-cause.md`

优点：

- 三档 fan-out 设计合理。
- 专项路由、跨平台分析、边界策略、OVHSC 推理链都较完整。

问题：

- `specialized_workflow` 只支持单一路专项元数据。
- UI 与 Functionality 同时触发时会发生覆写。
- `fanout_mode` 是 RCA 关键字段，但后续被 P4 覆写。

### P4 `p4-fix-design.md`

优点：

- `single-proposer / challenged-proposer / contested-arbitrated` 三档设计合理。
- 四重论证、竞争方案、回归测试、专项附录整合都很完整。

问题：

- 直接把 `fix_strategy_mode` 写入 `fanout_mode`，是当前最显著的状态污染点。
- `challenger` 升级后在 Phase 内部 `goto step="3"`，与主编排恢复模型存在潜在重复控制风险。

### P5 `p5-fix-impl.md`

优点：

- 已完成从“主 Agent 直接改代码”到“独立 coder-agent 黑盒实施”的设计升级。
- `contract-checklist.md`、`impl-report.md`、`error-dump.md` 三哨兵模型清晰。

问题：

- `specialized_workflow.status ∈ {DD-Completed, Merged}` 中的 `Merged` 实际从未由主流程写入。
- 如果上一轮失败留下 `error-dump.md`，重入时没有清理动作，存在卡死风险。
- 多个变量如 `output_impl_report`、`output_contract_checklist`、`issue_id`、`env_git`、`env_subagent` 依赖隐式上下文。

### P6 `p6-verification.md`

优点：

- 已不只是验收，而是失败分类和回流路由控制闸门。

问题：

- `root_cause_not_closed` 时继续写回 `fanout_mode = complex-arbitrated`，进一步固化了对污染字段的依赖。

结论：

- 六阶段链路设计合理，但 **P1/P2 控制流归属、P4 状态污染、P5 重入残留、P6 回流字段设计** 是四个关键风险点。

---

## 3.4 主工作流角色层 `agents/`

主链路角色结构：

- `curator.md`
- `investigator.md`
- `challenger.md`
- `shared-challenger-base.md`
- `arbiter.md`
- `shared-arbiter-base.md`
- `fix-proposer.md`
- `coder-agent.md`

判断：

- 角色拆分整体合理，不建议粗暴压缩主链路角色。
- 共享基座是当前最健康的 Prompt 结构化成果之一。

关键问题：

1. `shared-challenger-base.md` 的输出推荐值固定为 `Accept / Revise / Reject`，但 `challenger.md` 在 FIX 场景要求 `Adopt / Revise / Reject`，存在枚举不一致。
2. `coder-agent.md` 的设计非常细，但它与主流程之间是黑盒关系，因此“前置门禁”在主流程视角本质上是“后置哨兵校验”，语义需要统一。

---

## 3.5 模板层 `templates/`

主模板整体质量高，是当前工作流“可审计”的基础。

主要优点：

- `issue-card.md` 把 intake、边界与代码文档上下文合并到统一卡片。
- `spec.md` 正式承载复杂度路由字段。
- `fix-design.md`、`impl-report.md`、`verification-report.md` 的工程可审计性很强。

关键问题：

1. `context-bundle.md` 的 `Specialized Workflow Inputs` 仍只写 `functionality-deep-dive / none`，缺少 `ui-ux-analysis`。
2. `rca-report.md` 仍写 `（不再包含 UI 专项）`，与当前已接入 UI/UX 深度分析（主流程内） 的现状不一致。
3. `artifact-checklist.yaml` 与模板标题存在错位：
   - `issue-card.md` 模板使用 `基本信息 / 复现信息`
   - 但 `artifact-checklist.yaml` 要求 `Issue Summary / Reproduction Steps`
   - 这会导致评测侧关键段落校验存在假阴性风险

结论：

- 模板层强，但**模板与评测检查表未完全同源**。

---

## 3.6 参考知识层 `reference/`

主工作流参考文件：

- `analysis-strategies.md`
- `fix-strategies.md`
- `platform-checklist.md`
- `reasoning-chain.md`

作用判断：

- 它们是“知识型支撑层”，不是状态机的一部分。
- 其价值在于把抽象策略从 Phase 逻辑中解耦出来。

风险：

- 当前主要风险不是内容本身，而是缺少自动一致性检查，无法保证 `system-prompt.md` 摘要与这些源文件长期一致。

---

## 3.7 Functionality Deep-Dive 子工作流

组成完整，覆盖：

- 编排：`core/workflow.xml`、`workflow-model.yaml`、`default-config.yaml`、`workflow-status-template.yaml`
- 阶段：`f1` 到 `f5`
- 角色：现行复合角色 + 兼容旧角色
- 模板：RCA / Summary / Topology / Concurrency / Environment / Defensive Fix
- 参考：环境因子、状态机、竞态、隔离模式

优点：

- 已完成从细粒度旧角色到复合角色的收敛。
- 子工作流自身具备恢复能力与版本兼容意识。
- 可选中间产物策略较成熟。

问题：

- 文件名仍叫 `FUNCTIONALITY_DEEP_DIVE_WORKFLOW_V3.md`，正文标题却是 `V4`，命名不一致。
- 主流程只提供单槽 `specialized_workflow`，无法完整承载其与 UI 专项并存的情况。

结论：

- Functionality Deep-Dive 是当前专项层中成熟度最高的部分。

---

## 3.8 UI/UX 深度分析（主流程内） 子工作流

组成完整但显著更轻：

- 编排：`core/workflow.xml`、`workflow-model.yaml`、`default-config.yaml`、`workflow-status-template.yaml`
- 阶段：`u1` 到 `u4`
- 角色：4 个最小角色
- 模板：`ui-ux-analysis-rca.md`、`ui-ux-analysis-summary.md`
- 参考：`ui-patterns.md`

优点：

- 已具备最小可运行链路。
- 已接入主流程 P3。

问题：

1. `workflow.xml` 不读取 `workflow-model.yaml`，也不基于 `stepsCompleted` 决定当前阶段。
2. `workflow-status-template.yaml` 字段过少，缺少 `last_updated`、`current_stage`、`schema_version` 等。
3. `u1-u4` 多处直接使用 `{env_subagent}`，但参数头未声明。
4. 没有明确的降级分支。
5. 更严重的是，评测层仍默认把 `DD-Completed` 理解为功能专项完成，并要求 `deep-dive/*` 产物；UI 专项一旦触发，当前 artifact checker 存在误判风险。

结论：

- UI/UX 深度分析（主流程内） 已接入，但仍处于“最小样板版”，还没有达到主流程与 Functionality 专项的产品化成熟度。

---

## 3.9 分发辅助层

文件：

- `install.sh`
- `install_trae.sh`

判断：

- 这是安装分发辅助文件，不属于运行时核心逻辑。
- 对架构质量影响较低。

---

## 3.10 评测治理层 `eval-framework/`

### 结构评价

`eval-framework/` 不是工作流执行源，但它决定了“优化是否真实有效”的裁判口径。

关键模块作用：

- `coordinator.py`: 调度 A/B/C/D 四链
- `session_manager.py`: IDE 会话管理
- `artifact_checker.py`: 产物完整性校验
- `judge.py`: LLM-as-Judge
- `scoring_engine.py`: 统计与聚合
- `comparator.py`: 横向对比与效率指标
- `quality_gate.py`: CI 门禁
- `weakness_detector.py`: 薄弱点定位
- `optimizer.py`: 自动改进提案
- `iteration_loop.py`: Eval -> Optimize -> Verify 闭环
- `report_generator.py`: 报告生成
- `baseline_runner.py`: Chain D 裸跑

### 优点

- 已明确将工作流优化绑定到评测结果，而不是主观感觉。
- 动态路由、Deep-Dive 命中率、平均 agent 数等 ROI 指标已经进入比较口径。

### 关键问题

1. **状态字段污染会直接污染评测**
   - `coordinator.py` 与 `judge.py` 都从 `workflow-status.yaml` 读取 `fanout_mode`、`fix_strategy_mode` 和 `specialized_workflow`。
   - 一旦 P4 把 `fanout_mode` 覆写成 fix 模式，评测层会把 RCA 与 Fix 的 agent 成本和路由命中一起算错。

2. **`artifact-checklist.yaml` 与当前模板不完全对齐**
   - 会导致“产物存在且合理，但被轻量检查误判缺段落”的问题。

3. **专家模式产物检查仍偏向功能专项**
   - `artifact_checker.py` 只要看到 `specialized_workflow.status in (DD-Completed, Merged)`，就强制要求 `deep-dive/*` 路径。
   - UI 专项触发时，同样可能被判定应存在功能专项产物。

4. **`Merged` 状态是假设态，不是现网事实态**
   - `artifact-checklist.yaml`、`artifact_checker.py`、`p5-fix-impl.md` 都把 `Merged` 当成可能状态。
   - 但主流程实际上用的是 `merge_strategy = merged-into-main-rca`，不是 `status = Merged`。

5. **`iteration_loop.py` 当前不闭环**
   - 文件声明要执行完整 Eval/Judge/Weakness/Optimize 流程。
   - 但 `_collect_and_score()` 实际只返回 `eval_summary.results`，并未真正调用 `judge.py` 生成标准评分结果。
   - 这意味着迭代优化链路目前更像脚手架，而非真正可用闭环。

结论：

- 评测层方向正确，但**对执行状态与模板的依赖比代码层更脆弱**，是当前第二大治理重点。

---

## 3.11 Case 数据层 `eval-cases/seed-10/`

当前包含 10 个种子 Case：

1. `case-001-state-machine-race`
2. `case-002-cache-drift`
3. `case-003-lifecycle-coupling`
4. `case-004-coroutine-race`
5. `case-005-multi-module-chain`
6. `case-006-simple-npe`
7. `case-007-network-timeout`
8. `case-008-memory-leak`
9. `case-009-deadlock`
10. `case-010-event-bus-misorder`

每个 Case 结构统一：

- `metadata.yaml`
- `input/issue-description.md`
- `input/logs/README.md`
- `input/code-snapshot/README.md`
- `ground-truth/expected-root-cause.md`
- `ground-truth/expected-contributing.md`
- `ground-truth/expected-fix-direction.md`
- `ground-truth/scoring-rubric.yaml`

优点：

- Case schema 已显式引入 `expected_route / expected_fanout_mode / expected_fix_mode`。
- Case 不只评根因，还评动态路由是否命中预期。

问题：

- 当前 seed-10 尚未看到明确的 UI 专项 case；这会导致 UI/UX 深度分析（主流程内） 的评测覆盖不足。

结论：

- Case 数据层已开始约束动态路由设计，但对 UI 专项成熟度的拉动仍然不足。

---

## 3.12 文档治理层 `doc/`

`doc/` 当前同时存在四类材料：

1. 现行设计/采纳类
2. 施工任务/批次说明类
3. 历史 QA/评审类
4. 其他架构材料

优点：

- 信息非常丰富，几乎完整保留了从设计、施工到复盘的全过程。

问题：

- 缺少明确的 `current / plan / review / archive` 分层。
- 容易把历史计划态文档误读为当前执行规范。

结论：

- `doc/` 更像知识仓库，不像严格治理后的规范目录。

---

## 4. 对两份重点评审文档的深度分析

## 4.1 `B2C_WORKFLOW_ARCHITECTURE_REVIEW_2026-04-18.md`

这份文档的特点：

- 聚焦“明确冲突点”
- 风格偏架构缺陷审计
- 更接近 P0/P1 问题单

### 这份文档判断准确的部分

1. `fanout_mode` 语义污染
2. P5 Human-Review 重入死循环
3. P1/P2 子流程与主编排器重复接管控制流
4. `system-prompt.md` 与真实 SubAgent 架构存在割裂

### 这份文档遗漏但应补充的关键点

1. **评测层也被 `fanout_mode` 污染**
   - 不只是 RCA 回流失真，`coordinator.py` / `judge.py` / `comparator.py` 的效率与 ROI 指标也会被污染。
2. **`specialized_workflow` 单槽位问题**
   - 这不是文档中最突出的点，但它已经成为主流程与专项层的结构性瓶颈。
3. **UI 专项与评测校验不兼容**
   - 这份文档没有展开，但当前是现实风险。
4. **Artifact checklist 与模板标题错位**
   - 属于“评测侧假失败”问题，文档中未覆盖。

### 对该文档的评价

- **问题识别能力强**
- **对代码现状的直击度高**
- **但更偏主工作流内部逻辑，未充分覆盖评测与模板联动问题**

结论：

> 该文档适合作为“架构缺陷优先级清单”的基础，但不足以单独作为全局治理报告。

---

## 4.2 `B2C_WORKFLOW_COMPREHENSIVE_REVIEW_2026-04-18.md`

这份文档的特点：

- 覆盖范围更广
- 更强调“全景 + 模块分层 + 治理建议”
- 是更适合作为汇报底稿的版本

### 这份文档判断准确的部分

1. 已正确识别四层结构：入口、主编排、专项、评测治理
2. 已正确指出 `specialized_workflow` 不能表达多专项并存
3. 已正确指出 Full / Limited 双入口不是单一事实源
4. 已正确指出 phase 参数契约不够显式
5. 已正确指出 UI/UX 深度分析（主流程内） 成熟度低于主流程与功能专项
6. 已正确指出 `doc/` 混放问题

### 这份文档仍可加强的部分

1. **需要把评测层问题写得更硬**
   - 当前不只是“评测依赖状态字段”，而是已经存在显式错位：
   - heading 不匹配
   - UI 专项会被按功能专项校验
   - `fanout_mode` 污染会影响 `avg_agent_count`
2. **需要把迭代闭环脚手架未完成点单独指出**
   - `iteration_loop.py` 当前并未真正完成 Judge 驱动的优化闭环
3. **需要补充模板层陈旧点**
   - `rca-report.md` 仍有 `（不再包含 UI 专项）` 描述
   - `context-bundle.md` 仍只写 functionality 模式

### 对该文档的评价

- **全景性强**
- **问题排序合理**
- **已接近正式治理报告**

结论：

> 该文档已经是高质量全局 review，但若要成为真正的“严谨报告”，还需把评测侧和模板侧的事实错位写得更具体、更执行化。

---

## 5. 新增关键发现

以下发现是本次在交叉阅读代码与文档后，应作为新增结论补入的重点：

### P0-1 `fanout_mode` 不仅语义污染，还会直接污染 ROI 统计

事实链：

- `p3-root-cause.md` 把 `fanout_mode` 作为 RCA 路由模式
- `p4-fix-design.md` 又把 `fix_strategy_mode` 写入 `fanout_mode`
- `coordinator.py` / `judge.py` / `comparator.py` 用最终状态文件估算 agent 数与路由命中

结果：

- `avg_agent_count`
- `score_per_agent`
- `expected_fanout_hit_rate`

都可能失真。

### P0-2 `artifact-checklist.yaml` 与现行模板口径不一致

事实链：

- `issue-card.md` 模板没有 `Issue Summary` / `Reproduction Steps` 标题
- 校验清单却硬性要求这些段落

结果：

- 评测会出现“工作流正常产出，但轻量校验误报缺段落”的假失败。

### P0-3 UI/UX 深度分析（主流程内） 已接入主流程，但专家模式校验仍按 Functionality Deep-Dive 处理

事实链：

- `artifact_checker.py` 只看 `specialized_workflow.status`
- 一旦状态是 `DD-Completed`，就检查 `deep-dive/*`
- UI 专项产物真实路径是 `ui-ux-analysis/*`

结果：

- UI 专项 case 会被错误判定缺失功能专项产物。

### P0-4 `specialized_workflow` 单槽位会让“双专项并存”彻底不可审计

结果：

- 主流程无法回答一个 case 是否同时触发过功能专项和 UI 专项。
- 评测无法统计双专项协同收益。

### P1-1 模板层仍残留旧时态描述

表现：

- `rca-report.md` 仍写 `（不再包含 UI 专项）`
- `context-bundle.md` 只写 functionality 专项输入

### P1-2 自动优化闭环当前还不是可运行真闭环

表现：

- `iteration_loop.py` 中 `_collect_and_score()` 没有调用 judge，只回传原始 summary。

### P1-3 多个 Python 模块使用顶级绝对导入

表现：

- 如 `coordinator.py` 中使用 `from session_manager import ...`
- 在包方式导入与脚本方式执行之间存在环境敏感性

这属于工程稳定性债务，不是当前 B2C Prompt 设计的核心问题，但值得记录。

---

## 6. 优先级结论

## P0：必须优先整改

1. 拆分 `fanout_mode` 与 `fix_strategy_mode` 的状态职责
2. 重构 `specialized_workflow` 为可表达多专项并存的结构
3. 修复评测层对 UI 专项的错误校验逻辑
4. 对齐 `artifact-checklist.yaml` 与当前模板标题/段落

## P1：强烈建议近期整改

1. 统一子流程与主编排器的暂停/恢复控制权
2. 修复 P5 重入残留失败产物问题
3. 补齐各 phase 的显式参数契约
4. 提升 UI/UX 深度分析（主流程内） 的状态恢复、降级与编排一致性
5. 修复模板中的旧时态残留

## P2：治理与产品化收尾

1. 建立拆分源到 `system-prompt.md` 的自动生成或一致性校验
2. 重构 `doc/` 目录分层
3. 补齐 UI 专项 case 与评测样本
4. 让 `iteration_loop.py` 真正连上 Judge 和评分引擎

---

## 7. 建议整改路线

### 第一阶段：状态与评测去歧义

- 改状态 schema
- 改 artifact checker
- 改 checklist 与模板对齐

### 第二阶段：控制流与专项结构收口

- 收回 P1/P2 内部暂停逻辑
- 修 P5 重入
- 升级 UI/UX 深度分析（主流程内） 状态机

### 第三阶段：入口与文档治理

- 明确 `core + phases + templates` 为唯一执行事实源
- `SKILL.md` 与 `system-prompt.md` 退为入口包装
- `doc/` 增加时态与权威标签

### 第四阶段：评测闭环完善

- 增加 UI 专项 case
- 修复 iteration loop
- 用指标验证状态 schema 重构后的真实收益

---

## 8. 最终结论

### 对当前代码库的最终判断

- **主工作流架构**：成熟度高
- **Functionality Deep-Dive**：成熟度中高
- **UI/UX 深度分析（主流程内）**：成熟度中低
- **评测治理层**：方向正确，但与执行层存在关键错位
- **文档治理层**：信息充足，但时态与权威性未分层

### 对两份重点评审文档的最终判断

- `B2C_WORKFLOW_ARCHITECTURE_REVIEW_2026-04-18.md`
  - 更擅长识别硬冲突
  - 适合作为缺陷清单
- `B2C_WORKFLOW_COMPREHENSIVE_REVIEW_2026-04-18.md`
  - 更适合作为汇报底稿
  - 已接近正式治理报告

### 一句话总结

> 当前 B2C 工作流最需要的不是继续增加角色，而是把“状态字段、专项元数据、评测校验、模板口径、入口文档”这五个层面的事实源彻底收束，让执行、评测、文档三者真正说同一种语言。

---

## 9. 文件级覆盖附录

### 9.1 `mobile-qa-workflow/`

入口与规则：

- `PLATFORM-GUIDE.md`
- `SKILL.md`
- `system-prompt.md`
- `install.sh`
- `install_trae.sh`

主流程 Agent：

- `agents/arbiter.md`
- `agents/challenger.md`
- `agents/coder-agent.md`
- `agents/curator.md`
- `agents/fix-proposer.md`
- `agents/investigator.md`
- `agents/shared-arbiter-base.md`
- `agents/shared-challenger-base.md`

主流程 Core：

- `core/core-rules.xml`
- `core/default-config.yaml`
- `core/workflow-model.yaml`
- `core/workflow-status-template.yaml`
- `core/workflow.xml`

主流程 Phase：

- `phases/p1-intake.md`
- `phases/p2-spec-definition.md`
- `phases/p3-root-cause.md`
- `phases/p4-fix-design.md`
- `phases/p5-fix-impl.md`
- `phases/p6-verification.md`

主流程 Reference：

- `reference/analysis-strategies.md`
- `reference/fix-strategies.md`
- `reference/platform-checklist.md`
- `reference/reasoning-chain.md`

主流程 Template：

- `templates/context-bundle.md`
- `templates/context-curation-report.md`
- `templates/contract-checklist.md`
- `templates/error-dump.md`
- `templates/fix-design.md`
- `templates/impl-report.md`
- `templates/intake-form-blank.md`
- `templates/intake-form.md`
- `templates/issue-card.md`
- `templates/knowledge-card.md`
- `templates/rca-report.md`
- `templates/spec.md`
- `templates/verification-report.md`

Functionality Deep-Dive：

- `functionality-deep-dive/FUNCTIONALITY_DEEP_DIVE_WORKFLOW_V3.md`
- `functionality-deep-dive/agents/README.md`
- `functionality-deep-dive/agents/arbiter.md`
- `functionality-deep-dive/agents/challenger.md`
- `functionality-deep-dive/agents/context-reconstructor.md`
- `functionality-deep-dive/agents/deep-dive-arbiter.md`
- `functionality-deep-dive/agents/deep-dive-context-analyst.md`
- `functionality-deep-dive/agents/deep-dive-race-and-isolation-analyst.md`
- `functionality-deep-dive/agents/deep-dive-structure-analyst.md`
- `functionality-deep-dive/agents/defensive-fix-architect.md`
- `functionality-deep-dive/agents/state-analyst.md`
- `functionality-deep-dive/agents/temporal-analyst.md`
- `functionality-deep-dive/core/default-config.yaml`
- `functionality-deep-dive/core/workflow-model.yaml`
- `functionality-deep-dive/core/workflow-status-template.yaml`
- `functionality-deep-dive/core/workflow.xml`
- `functionality-deep-dive/phases/f1-context-reconstruction.md`
- `functionality-deep-dive/phases/f2-state-topology.md`
- `functionality-deep-dive/phases/f3-temporal-correlation.md`
- `functionality-deep-dive/phases/f4-isolation-debate.md`
- `functionality-deep-dive/phases/f5-defensive-fix-design.md`
- `functionality-deep-dive/reference/README.md`
- `functionality-deep-dive/reference/environment-factor-thresholds.md`
- `functionality-deep-dive/reference/isolation-patterns.md`
- `functionality-deep-dive/reference/race-condition-patterns.md`
- `functionality-deep-dive/reference/state-machine-patterns.md`
- `functionality-deep-dive/templates/concurrency-analysis-report.md`
- `functionality-deep-dive/templates/deep-dive-summary.md`
- `functionality-deep-dive/templates/deep-dive-topology.md`
- `functionality-deep-dive/templates/defensive-fix-design.md`
- `functionality-deep-dive/templates/environment-factor-report.md`
- `functionality-deep-dive/templates/functionality-deep-dive-rca.md`

UI/UX 深度分析（主流程内）：

- `ui-ux-analysis/agents/ui-context-analyst.md`
- `ui-ux-analysis/agents/ui-ux-analysis-arbiter.md`
- `ui-ux-analysis/agents/ui-render-and-interaction-analyst.md`
- `ui-ux-analysis/agents/ui-structure-analyst.md`
- `ui-ux-analysis/core/default-config.yaml`
- `ui-ux-analysis/core/workflow-model.yaml`
- `ui-ux-analysis/core/workflow-status-template.yaml`
- `ui-ux-analysis/core/workflow.xml`
- `ui-ux-analysis/phases/u1-context-and-visual-baseline.md`
- `ui-ux-analysis/phases/u2-layout-topology.md`
- `ui-ux-analysis/phases/u3-render-timing-and-interaction.md`
- `ui-ux-analysis/phases/u4-ui-ruling.md`
- `ui-ux-analysis/reference/ui-patterns.md`
- `ui-ux-analysis/templates/ui-ux-analysis-rca.md`
- `ui-ux-analysis/templates/ui-ux-analysis-summary.md`

### 9.2 `eval-framework/`

- `__init__.py`
- `artifact-checklist.yaml`
- `artifact_checker.py`
- `auto-reply-rules.yaml`
- `baseline_runner.py`
- `case-schema.yaml`
- `comparator.py`
- `configs/eval-config.yaml`
- `configs/monthly-compare.yaml`
- `configs/nightly-full.yaml`
- `configs/pr-quick.yaml`
- `coordinator.py`
- `iteration_loop.py`
- `judge.py`
- `optimizer.py`
- `quality_gate.py`
- `report_generator.py`
- `scoring-rubric-base.yaml`
- `scoring_engine.py`
- `session_manager.py`
- `tests/test_judge_parse.py`
- `weakness_detector.py`

### 9.3 `eval-cases/seed-10/`

Case 列表：

- `case-001-state-machine-race`
- `case-002-cache-drift`
- `case-003-lifecycle-coupling`
- `case-004-coroutine-race`
- `case-005-multi-module-chain`
- `case-006-simple-npe`
- `case-007-network-timeout`
- `case-008-memory-leak`
- `case-009-deadlock`
- `case-010-event-bus-misorder`

每个 Case 均包含：

- `metadata.yaml`
- `input/issue-description.md`
- `input/logs/README.md`
- `input/code-snapshot/README.md`
- `ground-truth/expected-root-cause.md`
- `ground-truth/expected-contributing.md`
- `ground-truth/expected-fix-direction.md`
- `ground-truth/scoring-rubric.yaml`

### 9.4 本次重点交叉核对文档

- `doc/B2C_WORKFLOW_ARCHITECTURE_REVIEW_2026-04-18.md`
- `doc/B2C_WORKFLOW_COMPREHENSIVE_REVIEW_2026-04-18.md`
- `doc/B2C_WORKFLOW_SUBAGENT_FINAL_ADOPTION_2026-04-18.md`
- `doc/B2C_WORKFLOW_BATCH_ABC_PR_DESCRIPTION_2026-04-18.md`
- `doc/B2C_WORKFLOW_SUBAGENT_IMPLEMENTATION_CHECKLIST_2026-04-18.md`
