# Loupe Mobile B2C Workflow 架构梳理与务实优化建议（不影响效果）
生成日期：2026-04-21

## 0. 目标与约束（必须不影响效果）
本工程的核心价值是：在“输入信息有限且噪声大”的真实移动端问题场景下，通过一套**标准化、流程化**工作流，稳定地产出可归因、可修复、可验证的闭环产物，并能在自检评测中保持分数表现。

为保证“优化不降效”，本文所有建议默认遵循以下硬约束：
- 产物契约不破坏：`mobile-qa-workflow/core/workflow.xml` 中 `<io-contract>` 定义的阶段 I/O 契约必须保持兼容（可扩展，不可删改导致下游缺输入）。
- 状态机不破坏：`mobile-qa-workflow/core/workflow-status-template.yaml` 的字段结构与枚举集保持向后兼容（可新增字段、可兼容旧值，不可让旧会话无法恢复）。
- 评测口径不破坏：`eval-framework` 产物检查 + LLM Judge 的聚合口径不发生“静默漂移”（任何 schema 变更必须通过兼容层/版本号显式化，并有回归验证）。
- 优化优先“消除漂移与不一致”，再谈“重构与抽象”：先把隐性复杂度（状态/同步/命名漂移）收敛到单一权威源，再做结构性简化。

## 1. 工程整体结构（当前仓库的真实职责边界）
从仓库内容来看，本工程不是一个移动 App，而是“移动 QA 工作流 + 自检评测框架”的组合：
- `mobile-qa-workflow/`：面向移动端 B2C 质量问题的工作流定义（编排 DSL、phase 文档、agent 角色模板、产物模板、状态机 schema 等）。
- `eval-framework/`：用于批量运行工作流（链路 A/B/C/D）、校验产物、LLM-as-Judge 打分、生成报表、质量门禁、以及（计划中的）闭环优化器。
- `eval-cases/`：评测用 case seed（输入/ground-truth）。
- `doc/`：大量历史评审与方案文档（对齐与遗留项说明密集）。

后续的“状态管理与同步复杂度”主要来自：**工作流（文档/DSL）层** 与 **评测/执行（Python）层** 两套系统在 schema、命名、版本控制上的漂移。

## 2. 运行时架构与数据流（主链路）
### 2.1 工作流执行（mobile-qa-workflow）
工作流执行的“权威编排入口”是：
- `mobile-qa-workflow/SKILL.md`：技能入口，负责初始化/恢复工作区，并加载主编排器 `core/workflow.xml`。
- `mobile-qa-workflow/core/workflow.xml`：主编排器，按 `workflow-status.yaml` 中 `stepsCompleted` 与 `current_state` 调度 phase，并在 step 4 统一做 step-pause 路由。
- `mobile-qa-workflow/core/core-rules.xml`：流程 DSL 标签白名单、step-pause 输入协议、ABORT 早退协议、Human-Review 协议等“硬规则”。

执行过程中存在两类“状态/配置”文件：
- `config_source`（通常落地为 `mobile-qa-workflow/core/default-config.yaml` 的拷贝）：环境能力与输出路径等配置键（由 `core/config-schema.yaml` 约束键名白名单）。
- `workflow_status`（通常落地为 `mobile-qa-workflow/core/workflow-status-template.yaml` 的实例）：**阶段状态机**与路由字段（`current_state`、`stepsCompleted`、`reroute_target_phase`、`fanout_mode`、`fix_strategy_mode`、计数器等）。

phase 以 Markdown + DSL 的方式实现（`mobile-qa-workflow/phases/p1~p6-*.md`），由主编排器 step 3 `load` 执行。phase 输出产物（模板落盘），并通过更新 `workflow_status` 驱动下一阶段路由。

### 2.2 评测执行（eval-framework）
评测框架的主入口是：
- `eval-framework/coordinator.py`：构建任务队列（case × chain），启动 IDE Session（或 baseline）、校验产物、保存状态与摘要。
- `eval-framework/session_manager.py`：IDE 适配层（Trae/Cursor/Extension/DirectLLM 的抽象），负责进程生命周期。
- `eval-framework/artifact_checker.py`：产物完整性校验（存在性/最小字数/关键段落/条件必需产物）。
- `eval-framework/judge.py`：LLM-as-Judge，读取产物 + ground truth，按 rubric 输出结构化分数并加权。
- `eval-framework/scoring_engine.py`：对 judge-results 聚合统计、效率指标等。
- `eval-framework/quality_gate.py`：CI 门禁（均分、回归、零分 case、产物通过率、平均 agent 数等）。

链路概念：
- Chain A/B：通过 IDE Session 跑 `mobile-qa-workflow`（区别一般是 expert/standard 或策略差异）。
- Chain C：手工输入。
- Chain D：baseline runner 裸跑（`eval-framework/baseline_runner.py`）。

## 3. 模块与关键文件逐一说明（“复杂度从哪里来”）
### 3.1 mobile-qa-workflow/core（编排与契约）
- `core/workflow.xml`
  - 职责：主编排器；读取 `config_source`/`workflow_status`；决定当前 phase；执行 phase；在 step 4 统一解析 step-pause 用户回复并路由。
  - 复杂度来源：路由 case 多、兼容逻辑多（reroute、计数器熔断、step-pause 双写白名单等）。
- `core/workflow-model.yaml`
  - 职责：阶段序列（stepsCompleted -> next phase）。
  - 复杂度来源：如果 phase/文档/状态机枚举不一致，会造成“看似能跑但语义漂移”。
- `core/workflow-status-template.yaml`
  - 职责：状态机 schema 权威源（字段结构 + `current_state` 合法枚举 + 白名单镜像策略）。
  - 复杂度来源：新旧状态值/字段兼容、以及“顶层字段与 user_inputs 双写”过渡策略。
- `core/default-config.yaml` + `core/config-schema.yaml`
  - 职责：config_source 默认值与允许键名白名单。
  - 复杂度来源：存在已明确记录的键名漂移（deep-dive 子配置 emit_* vs 主配置 output_* / optional_artifacts 子键）。
- `core/core-rules.xml`
  - 职责：DSL 规则与协议（尤其 D1/D2/D14/D15/D18 的 stop/ABORT/step-pause 协议）。
  - 复杂度来源：规则一旦在 phase/system-prompt/脚本之间多处复制，就容易漂移。

### 3.2 mobile-qa-workflow/phases（主链路阶段实现）
- `phases/p1-intake.md`：信息受理、分类、最小信息集门禁、输出 issue-card，并设置 `current_state = Spec-Defining`。
- `phases/p2-spec-definition.md`：Spec 三要素 + 扩展模块 + Non-Bug 早退 + 上下文策展 + 输出 spec/context bundle。
  - 已知复杂点：文件内仍存在 legacy 内联 `<step-pause>`（Spec-Uncertain），与“编排器 step 4 统一 step-pause”目标冲突（已在文档注释中登记为 v4.2 遗留）。
  - 已知风险点：末尾 `current_state = RCA-InProgress`（该值不在 schema 权威枚举里；见后续“漂移问题”）。
- `phases/p3-root-cause.md`：动态 fan-out（simple/medium/complex）+ 可进入专项 deep-dive + 置信度低/多轮不收敛时 ABORT 并回流/转人工。
- `phases/p4-fix-design.md`：按风险/置信度动态选择 proposer/challenger/arbiter；并存在 legacy 内联 `<step-pause>`（确认进入修复实施），同样与 D14 目标冲突。
- `phases/p5-fix-impl.md`：调用 coder-agent；通过产物“文件哨兵”判定成功/失败（impl-report / contract-checklist / error-dump）并设置状态。
- `phases/p6-verification.md`：三层验证 + 失败分类回流（design_insufficient/root_cause_not_closed/implementation_mismatch），失败时 ABORT，成功时 `current_state = Done`。

### 3.3 eval-framework（评测与闭环）
- `coordinator.py`
  - 职责：任务队列、执行、重试、产物校验、保存状态与摘要、并行执行。
  - 复杂度来源：运行结果 schema（TaskResult）与下游 QualityGate/IterationLoop 的字段读取存在不一致（详见第 4 节）。
- `session_manager.py`
  - 职责：启动 headless IDE、超时与终止、收集 artifacts。
  - 复杂度来源：适配器抽象不错，但 AutoReplyEngine 目前未真正接入会话交互（属于“半成品复杂度”）。
- `artifact_checker.py`
  - 职责：产物存在性/大小/关键段落/条件必需产物；并已引入“impl-report 元信息解析”做条件校验。
  - 复杂度来源：条件表达式能力不足导致一些规则只能硬编码（代码中已标 TODO）。
- `judge.py` / `scoring_engine.py` / `quality_gate.py`
  - 职责：打分、聚合、门禁。
  - 复杂度来源：字段路径与数据来源不一致会造成门禁“看似跑通但指标失真”。
- `iteration_loop.py` / `optimizer.py`
  - 职责：理论上实现 Eval→薄弱→改进→回归 的闭环。
  - 复杂度来源：当前实现与注释目标不一致（没有真正“评分”和“选子集回归”），属于“逻辑漂移风险”。

## 4. 当前主要复杂度与“漂移/同步”问题清单（高优先级）
本节只列“会放大复杂度、并可能影响稳定性/可维护性/可信度”的问题；很多属于“看似能跑，但语义与口径在漂移”。

### 4.1 Run ID 生成与结果目录分裂（评测框架严重一致性问题）
`eval-framework/coordinator.py` 中：
- `run()` 自己生成 `run_id`，用于 `_save_state(run_id, ...)` 与 `_save_summary(run_id, ...)`。
- 但 `build_queue()` 又**内部生成另一个 run_id**，并用它构造每个 task 的 `output_dir`。

结果：
- 一次评测会产生两个 run 目录：一个放 task 输出，一个放 state/summary（或混杂），导致“状态/产物/报告”难以对齐，增加排查与自动化处理复杂度。

### 4.2 workflow_status 枚举与 phase 写入值存在不一致（状态机漂移）
`core/workflow-status-template.yaml` 明确 `current_state` 权威枚举集合包含 `RCA-Designing`，但 `phases/p2-spec-definition.md` 末尾写入 `current_state = RCA-InProgress`（不在权威枚举内）。

风险：
- 路由语义不清：编排器 step 4 目前对未知 state 走 default（goto step 2），短期可能“看起来没炸”，但对人/对工具都增加理解成本。
- 后续若引入严格校验（CI/schema check），会被迫处理历史数据。

### 4.3 step-pause 的“单一调度入口”原则被破坏（交互点重复与同步负担）
`core/core-rules.xml` 已明确 D14：`<step-pause>` 仅允许在编排器 `core/workflow.xml` step 4 内。
但当前仍存在：
- `phases/p2-spec-definition.md` 内联 Spec-Uncertain step-pause（已登记为 v4.2 遗留）。
- `phases/p4-fix-design.md` 内联 Fix Design 确认 step-pause（同样登记为遗留）。

风险：
- 同一状态可能被弹两次（文档里也承认“重复弹窗已知 bug”）。
- step-pause 协议（result_field/allowed_values/双写白名单）只能在一个地方维护，否则必然漂移。

### 4.4 “结果 schema”在多个 Python 模块之间不一致（门禁/闭环指标可能失真）
典型例子：
- `coordinator.py` 生成的 `EvalRunSummary.results` 是序列化后的 TaskResult（字段如 `runtime_metrics`、`check_result` 等）。
- `quality_gate.py` 读取 `agent_count` 时用 `r.get("metadata", {}).get("runtime_metrics", {})`，但 TaskResult 里的 runtime_metrics 是顶层字段而非 metadata 子字段，导致平均 agent 数经常为 0（指标失真）。
- `iteration_loop.py` 注释称“收集并评分”，但 `_collect_and_score()` 实际只是把 `eval_summary.results` 原样返回，并不调用 `LLMJudge`，`weighted_score` 多为 0（闭环逻辑失真）。

风险：
- 你以为门禁/闭环在工作，但关键指标读错路径会让“复杂度控制/效率优化”完全失真，进而引发错误优化方向。

### 4.5 重复实现与常量散落（同步成本高）
例如 agent_count 的估算逻辑在：
- `eval-framework/coordinator.py::_estimate_agent_count`
- `eval-framework/judge.py::LLMJudge._estimate_agent_count`

风险：
- 一处改、另一处忘改，造成效率指标口径不一致。

## 5. 优化总体策略：先“减漂移/减同步点”，再“降复杂度”
把优化拆为 3 层，每层都给出“如何保证不影响效果”的落地方式。

### 5.1 P0（必须先做）：一致性与兼容层（不改变业务行为）
目标：不改变工作流效果，只让状态/结果“可被稳定理解与验证”。

建议清单：
1) 统一评测 run_id 的单一来源
- 做法：`Coordinator.run()` 生成 run_id 后传入 `build_queue(run_id=...)`，禁止 build_queue 内部生成新 run_id。
- 不影响效果的原因：只改变输出目录对齐方式，不改变任何执行逻辑/判分逻辑。
- 验收：一次 run 只产生一个 `eval-results/eval-.../` 目录，目录下同时包含 `eval-state.json`、`eval-summary.json` 与各 case 输出。

2) 引入 “Result Schema Adapter”（读写兼容，不改产物内容）
- 做法：在 `eval-framework` 增加一个小模块（例如 `result_schema.py`）提供：
  - `normalize_task_result(dict) -> dict`：把历史字段路径统一映射（例如把顶层 `runtime_metrics` 也镜像到 `metadata.runtime_metrics` 或反之），供 QualityGate/Report 使用。
  - `normalize_eval_summary(dict) -> dict`：兼容 `judge-results.json` 与 `eval-summary.json` 两套入口。
- 不影响效果的原因：只是把“读取口径”统一，避免指标失真；不改变产物生成、也不改变评分。
- 验收：QualityGate 的 `avg_agent_count`、artifact pass rate、score/regression 读数与实际一致。

3) workflow_status 值漂移的兼容映射（写新读旧）
- 做法：
  - 编排器 step 2 读取状态后，增加“兼容映射层”：若读到 `RCA-InProgress` 等历史值，映射为 `RCA-Designing`（或映射到最接近的合法枚举）。
  - phase 写入时优先写入权威枚举；但读取时仍兼容旧值，避免历史工作区无法恢复。
- 不影响效果的原因：路由语义不变（本来 default 也会 goto step 2），只是让状态值更可控。
- 验收：老工作区继续可恢复；新工作区不会再出现非法枚举值。

4) 把“单一权威源”机制工程化（从文档约定升级为工具约束）
- 做法：
  - 对 `current_state` 枚举、step-pause result_field 白名单、config-schema allowed_keys 等，建立自动校验（CI 已有部分，继续收敛）。
  - 输出一份“自动生成的权威表”（例如从 `workflow-status-template.yaml` 抽取枚举），让 phase 文档不要手写重复枚举。
- 不影响效果的原因：只减少漂移概率，不改执行逻辑。

### 5.2 P1（强烈建议）：交互与状态路由收敛（减少同步复杂度）
目标：减少“一个语义多处实现”的同步点，避免后续迭代引入指数级复杂度。

建议清单：
1) step-pause 完全收敛到 `core/workflow.xml` step 4（清理 legacy 内联）
- 做法：
  - 为 Spec-Uncertain / Fix-Confirm 等引入明确的 `current_state`（例如 `Spec-Uncertain` 已有；Fix 可新增 `Fix-Confirming` 或用既有状态承载），并在编排器 step 4 统一 step-pause。
  - phase 只负责设置 `current_state` + `current_phase_result = ABORT`，不负责弹窗。
  - 对 legacy 期做双轨兼容：编排器识别到“phase 内联 step-pause 已执行”的情况，避免重复弹窗（可通过 `user_inputs` 是否已有 key 来判定）。
- 不影响效果的原因：交互含义不变，只是把触发点集中管理，减少重复与漂移。
- 验收：同一问题不会出现重复弹窗；step-pause 协议（解析、熔断、双写）只维护一处。

2) 将“路由策略”从散落的自然语言迁移为显式策略对象（但保留现有字段）
- 背景：当前存在 `active_fanout_policy` / `active_fix_strategy_policy` 等策略字段，但真正策略分支散落在 phase 文档中。
- 做法：
  - 定义一份结构化的 `policy contract`（例如 YAML），把“输入 -> 输出状态字段”的决策表显式化。
  - phase 中引用策略名，并把关键决策结果写回 `workflow_status`（已有要求），但决策逻辑可读性显著提升。
- 不影响效果的原因：策略输出字段不变，只是把分支条件显式化，减少人肉同步。

3) 统一“计数器熔断”与“回流”规则的责任边界
- 做法：
  - 规定：计数器（`rca_retry_count` / `fix_retry_count` / `parse_error_count`）的递增点只允许在一个位置（建议：编排器负责 step-pause 解析与 parse_error；phase 负责业务回流计数）。
  - 所有熔断转 Human-Review 的条件在编排器集中处理（目前已做一部分）。
- 不影响效果的原因：规则不变，只减少重复写入与边界不清。

### 5.3 P2（长期演进）：降低状态管理与同步成本（架构级减复杂度）
目标：让“新增一个状态/产物/策略”变成可控的、低风险的改动。

建议清单：
1) 把 `workflow_status` 视作“事件溯源 + 当前快照”
- 做法：
  - 保留现有字段作为快照（兼容）。
  - 增加 `transition_log`（append-only）记录每次 state change 的：from/to、timestamp、reason、writer（phase/orchestrator）、关键字段 diff。
- 好处：调试“状态不同步”会从猜测变成可追溯；并能在评测中统计真实复杂度来源。
- 不影响效果的原因：仅新增日志字段，不改现有路由。

2) 将“模板产物”与“校验规则”绑定为可版本化契约
- 背景：ArtifactChecker 目前做存在性/段落检查，但规则演进容易和模板漂移。
- 做法：
  - 在模板头部加入 `template_version`（或在 checklist 中声明版本）。
  - ArtifactChecker 依据版本加载不同 required_sections，避免模板演进影响历史 case。
- 不影响效果的原因：对旧产物继续按旧规则校验；新产物显式使用新规则。

3) “深专项（functionality-deep-dive）”与主链路的配置键名漂移收敛
- 背景：`core/default-config.yaml` 与 deep-dive 子配置存在 emit_* / output_* 命名漂移，已记录为 v4.2 遗留。
- 做法：
  - 引入显式 alias 映射表，并在读取时同时识别两套键；写入统一写新键。
  - 在迁移脚本中提供一次性修复（可选）。
- 不影响效果的原因：旧键仍可被识别；减少后续扩展时的“忘记同步”风险。

## 6. “不影响效果”的落地与验收方法（强烈建议作为发布护栏）
为了保证优化不降效，建议把“效果”具象化为可回归的指标与工件：
- 工件级：产物文件集合完整，模板段落齐全（ArtifactChecker）。
- 评分级：Judge 加权分均值不降、低分 case 不退化（QualityGate）。
- 效率级：平均 agent 数口径正确且可追踪（先修 schema 读取问题）。

推荐的落地节奏：
1) 先做 P0：run_id 对齐 + result schema adapter + state 值兼容映射
2) 在 `eval-cases/seed-10` 上跑一次全量回归（至少 chains A/B；如成本允许加 baseline D 对比）
3) 通过 QualityGate 门禁后，再做 P1 的 step-pause 收敛（一次只迁一个 legacy 点，避免大爆炸）

验收标准建议（示例）：
- `mean_score` 不降（或允许极小波动，但 regression < 5%）。
- `artifact_pass_rate >= 90%`（现有门禁）。
- `avg_agent_count` 指标不为 0 且分布合理（修复读数后才有意义）。
- 随机抽样 3 个 case，人读 `workflow-status.yaml` 能清晰解释当前状态与回流原因（transition_log 会显著改善）。

## 7. 附：本次分析涉及的关键文件索引
- 工作流入口：`mobile-qa-workflow/SKILL.md`
- 主编排器：`mobile-qa-workflow/core/workflow.xml`
- 核心规则：`mobile-qa-workflow/core/core-rules.xml`
- 状态机 schema：`mobile-qa-workflow/core/workflow-status-template.yaml`
- 阶段序列：`mobile-qa-workflow/core/workflow-model.yaml`
- 配置 schema：`mobile-qa-workflow/core/config-schema.yaml`、`mobile-qa-workflow/core/default-config.yaml`
- Phase：`mobile-qa-workflow/phases/p1-intake.md` ~ `p6-verification.md`
- 评测执行：`eval-framework/coordinator.py`、`eval-framework/session_manager.py`
- 产物校验：`eval-framework/artifact_checker.py`
- 评分与门禁：`eval-framework/judge.py`、`eval-framework/scoring_engine.py`、`eval-framework/quality_gate.py`
- 迁移脚本：`mobile-qa-workflow/scripts/migrate-workflow-status-v3-to-v4.py`

