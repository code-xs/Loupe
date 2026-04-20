# UI/UX 深度分析（主流程内） 模块移除施工文档

## 1. 文档目的

本文档用于指导在当前工程中完整移除 `ui-ux-analysis` 模块及其相关逻辑，确保：

- 删除 `mobile-qa-workflow/ui-ux-analysis/` 模块本体；
- 删除主工作流、配置、模板、规则、评测框架中对该模块的显式引用；
- 保持 `functionality-deep-dive` 及主链路正常运行；
- 避免出现悬挂引用、错误产物路径、错误统计口径和误导性文档描述；
- 为后续代码修改提供明确的批次划分、验证方法和回滚策略。

本文档仅定义施工方案，不直接修改代码逻辑。

## 2. 目标与边界

### 2.1 施工目标

本次施工目标是将 `ui-ux-analysis` 从“正式能力”降为“不存在能力”，使系统在运行、配置、文档和评测层面均不再依赖它。

### 2.2 必须达到的结果

- 仓库内不再存在 `mobile-qa-workflow/ui-ux-analysis/` 目录；
- 主 RCA 不再触发 UI 专项子工作流；
- Fix Design 不再尝试读取 `ui-ux-analysis-summary.md`；
- 默认配置中不再暴露 UI 专项输出字段；
- 规则层不再声明 UI/UX 深度分析（主流程内） 子 Agent；
- 评测框架不再将 `ui-ux-analysis` 作为合法 route 或产物来源；
- Chain B 的对外语义收敛为“Functionality Deep-Dive 专家模式”；
- 代码修改后，全仓检索不应再出现运行链路中的 `ui-ux-analysis` 残留引用。

### 2.3 本次不处理范围

- 不删除 `functionality-deep-dive` 模块；
- 不改动 `eval-cases/` 现有 case 内容，除非后续发现 schema 校验需要样例补齐；
- 默认不改写 `doc/` 下历史评审与归档文档，以保留历史事实；
- 不重构 `specialized_workflow` 通用状态结构，因为功能专项仍在使用；
- 不引入新的 UI 子工作流替代方案，本次是“直接移除”，不是“能力迁移”。

## 3. 总体设计原则

### 3.1 原则一：删能力，不删通用机制

要删除的是 `ui-ux-analysis` 这条专项能力，不是所有专项机制。`specialized_workflow` 状态字段、Deep-Dive 统计口径、功能专项分流能力继续保留。

### 3.2 原则二：先断引用，再删实体

施工顺序必须先识别并解除主链路、模板、评测侧的引用，再删除目录本体并做全局复查。否则容易出现读取不存在文件、产物路径错误、状态统计异常。

### 3.3 原则三：运行面优先于文档面

必须优先保证执行链路正确，其次才是说明文档收敛。也就是说：

- 第一优先级：工作流、配置、模板、评测逻辑；
- 第二优先级：Skill 入口、System Prompt、平台说明；
- 第三优先级：历史归档文档。

### 3.4 原则四：保持功能类专项能力完整

删除 UI 专项后，复杂 UI 问题仍然应通过主 RCA 的 UI/UX 分析策略留在主流程内处理，而不是造成该类问题无路可走。

## 4. 工程影响面总览

本次施工涉及四个层面：

### 4.1 运行时工作流层

位于 `mobile-qa-workflow/`，影响最大，包括：

- 主编排 I/O 契约；
- P3 根因分析的专项路由；
- P4 修复设计的上游输入；
- 默认配置输出项；
- 核心规则中的 Agent 声明；
- Skill 入口与 System Prompt；
- 模板和策略参考文档。

### 4.2 模块实体层

位于 `mobile-qa-workflow/ui-ux-analysis/`，包括：

- `agents/`
- `core/`
- `phases/`
- `reference/`
- `templates/`

这一整棵目录需要删除。

### 4.3 评测与统计层

位于 `eval-framework/`，影响中等，包括：

- 产物采集顺序；
- 运行时统计中的 `specialized_workflow_mode` 口径；
- agent 数估算；
- route 枚举定义；
- Chain B 命名和对外描述。

### 4.4 文档与平台说明层

位于：

- `mobile-qa-workflow/SKILL.md`
- `mobile-qa-workflow/system-prompt.md`
- `mobile-qa-workflow/PLATFORM-GUIDE.md`
- `mobile-qa-workflow/reference/*.md`
- `mobile-qa-workflow/templates/*.md`

这一层主要用于消除误导性描述与入口暴露。

## 5. 文件级施工清单

以下按“必须修改 / 建议修改 / 删除”三类列出。

### 5.1 删除文件与目录

#### A. 整体删除目录

- `mobile-qa-workflow/ui-ux-analysis/`

#### B. 目录内全部子文件一并删除

- `mobile-qa-workflow/ui-ux-analysis/agents/ui-context-analyst.md`
- `mobile-qa-workflow/ui-ux-analysis/agents/ui-ux-analysis-arbiter.md`
- `mobile-qa-workflow/ui-ux-analysis/agents/ui-render-and-interaction-analyst.md`
- `mobile-qa-workflow/ui-ux-analysis/agents/ui-structure-analyst.md`
- `mobile-qa-workflow/ui-ux-analysis/core/default-config.yaml`
- `mobile-qa-workflow/ui-ux-analysis/core/workflow-model.yaml`
- `mobile-qa-workflow/ui-ux-analysis/core/workflow-status-template.yaml`
- `mobile-qa-workflow/ui-ux-analysis/core/workflow.xml`
- `mobile-qa-workflow/ui-ux-analysis/phases/u1-context-and-visual-baseline.md`
- `mobile-qa-workflow/ui-ux-analysis/phases/u2-layout-topology.md`
- `mobile-qa-workflow/ui-ux-analysis/phases/u3-render-timing-and-interaction.md`
- `mobile-qa-workflow/ui-ux-analysis/phases/u4-ui-ruling.md`
- `mobile-qa-workflow/ui-ux-analysis/reference/ui-patterns.md`
- `mobile-qa-workflow/ui-ux-analysis/templates/ui-ux-analysis-rca.md`
- `mobile-qa-workflow/ui-ux-analysis/templates/ui-ux-analysis-summary.md`

### 5.2 必须修改文件

#### 主工作流层

- `mobile-qa-workflow/core/workflow.xml`
- `mobile-qa-workflow/core/default-config.yaml`
- `mobile-qa-workflow/core/core-rules.xml`
- `mobile-qa-workflow/phases/p3-root-cause.md`
- `mobile-qa-workflow/phases/p4-fix-design.md`
- `mobile-qa-workflow/SKILL.md`
- `mobile-qa-workflow/system-prompt.md`
- `mobile-qa-workflow/PLATFORM-GUIDE.md`

#### 模板与参考层

- `mobile-qa-workflow/reference/analysis-strategies.md`
- `mobile-qa-workflow/reference/fix-strategies.md`
- `mobile-qa-workflow/templates/fix-design.md`
- `mobile-qa-workflow/templates/rca-report.md`

#### 评测框架层

- `eval-framework/judge.py`
- `eval-framework/coordinator.py`
- `eval-framework/case-schema.yaml`
- `eval-framework/configs/eval-config.yaml`

### 5.3 建议修改文件

以下文件不改也未必阻塞运行，但建议同步收敛，以避免口径漂移：

- `eval-framework/comparator.py`
- `eval-framework/report_generator.py`
- `eval-framework/scoring_engine.py`

说明：

- 这几个文件主要使用通用 `specialized_workflow_mode` 概念，本身不一定写死 `ui-ux-analysis`；
- 但 Chain B、Deep-Dive 进入率、route 命中率等展示文案建议同步调整，以保证报表语义准确。

### 5.4 默认不修改文件

- `mobile-qa-workflow/core/workflow-status-template.yaml`
- `mobile-qa-workflow/phases/p5-fix-impl.md`
- `eval-framework/artifact-checklist.yaml`
- `eval-cases/seed-10/**/metadata.yaml`
- `doc/*.md` 历史归档文档

说明：

- `workflow-status-template.yaml` 的 `specialized_workflow` 结构仍被功能专项使用；
- `p5-fix-impl.md` 只显式处理 `functionality-deep-dive`，不会错误引用 UI 专项；
- `artifact-checklist.yaml` 当前只强制检查功能专项产物；
- `eval-cases` 现有样例未使用 `ui-ux-analysis` 路由；
- `doc/` 历史文档默认保留。

## 6. 逐文件修改要求

### 6.1 `mobile-qa-workflow/core/workflow.xml`

#### 修改目标

移除主编排 I/O 契约中与 UI 专项产物相关的可选输入输出声明。

#### 具体动作

- 删除 `qa-root-cause` 输出中的：
  - `ui-ux-analysis-summary.md`
  - `ui-ux-analysis-rca.md`
- 删除 `qa-fix-design` 输入中的：
  - `ui-ux-analysis-summary.md`

#### 预期结果

主编排契约只保留：

- 主 RCA 产物；
- 功能专项可选产物；
- UI 问题仍走主 RCA，但不再产生独立 UI 专项附件。

### 6.2 `mobile-qa-workflow/core/default-config.yaml`

#### 修改目标

移除 UI 专项输出配置字段，避免下游认为该能力仍然存在。

#### 具体动作

- 删除：
  - `output_ui_ux_analysis_rca`
  - `output_ui_ux_analysis_summary`

#### 预期结果

默认配置只保留主链路和功能专项相关输出项。

### 6.3 `mobile-qa-workflow/core/core-rules.xml`

#### 修改目标

移除 UI/UX 深度分析（主流程内） agent group 声明，防止框架在规则层继续暴露该角色集。

#### 具体动作

- 删除整个 `agent-group name="ui-ux-analysis"` 区块；
- 保留 `main-workflow` 与 `functionality-deep-dive` 两个 agent-group。

#### 预期结果

规则层只承认：

- 主流程 Agent；
- 功能疑难专项 Agent；
- 不再存在 UI 专项角色。

### 6.4 `mobile-qa-workflow/phases/p3-root-cause.md`

#### 修改目标

去除 UI 专项子工作流路由与回注逻辑，保留功能专项逻辑。

#### 具体动作

- 在“专项子工作流路由决策”中删除 UI 触发条件说明；
- 删除 `满足 ui-ux-analysis 触发条件` 的整段分支；
- 删除创建 `{workspace_folder}/ui-ux-analysis/` 子工作区的动作；
- 删除加载 `mobile-qa-workflow/ui-ux-analysis/core/workflow.xml` 的动作；
- 删除 UI 专项摘要回注逻辑；
- 保留功能专项分流与回注逻辑。

#### 同步文案调整

将“复杂 UI / 布局 / 渲染 / 交互问题可进入 UI/UX 深度分析（主流程内）”改为类似表述：

- 复杂 UI / 布局 / 渲染 / 交互问题仍在主 RCA 中使用 UI/UX 专项分析策略处理；
- 不再启动独立 UI 子工作流。

#### 预期结果

P3 只保留：

- 主 RCA 动态 fan-out；
- 功能专项子工作流；
- UI 问题在主 RCA 内分析，不再分流。

### 6.5 `mobile-qa-workflow/phases/p4-fix-design.md`

#### 修改目标

去除对 UI 专项摘要的读取和依赖。

#### 具体动作

- 删除全局静态变量 `ui_ux_analysis_summary`；
- 将“若存在则读取 {deep_dive_summary} 与 {ui_ux_analysis_summary}”改为只读取 `{deep_dive_summary}`；
- 保留功能专项摘要输入逻辑。

#### 预期结果

Fix Design 只依赖：

- `issue-card.md`
- `spec.md`
- `rca-report.md`
- 功能专项摘要（若存在）

### 6.6 `mobile-qa-workflow/SKILL.md`

#### 修改目标

收敛对外能力说明，移除 UI/UX 深度分析（主流程内） 暴露。

#### 具体动作

- 将描述中的 “支持主链路动态 fan-out、Functionality Deep-Dive 与 UI/UX 深度分析（主流程内）”
  改为 “支持主链路动态 fan-out 与 Functionality Deep-Dive”；
- 检查其他段落是否有 UI 专项残留并删除。

#### 预期结果

Skill 入口文案与真实能力一致。

### 6.7 `mobile-qa-workflow/system-prompt.md`

#### 修改目标

去除系统级描述、主流程描述、Fix Design 描述中的 UI 专项能力。

#### 具体动作

- 从角色口径中删除 “UI/UX 深度分析（主流程内） 复合角色”；
- 从 Phase 3 描述中删除“复杂 UI 问题可进入 UI/UX 深度分析（主流程内）”；
- 从 Phase 4 描述中删除 `ui-ux-analysis-summary.md` 输入；
- 检查模板摘要、阶段定义、说明段落是否还有 UI 专项残留；
- 将 UI 问题保留为主流程分析类别，而非专项工作流。

#### 预期结果

`system-prompt.md` 与落地工作流保持一致，不再暗示独立 UI 专项存在。

### 6.8 `mobile-qa-workflow/PLATFORM-GUIDE.md`

#### 修改目标

去除平台集成说明中的 UI 子工作流目录与能力说明。

#### 具体动作

- 从入口文件列表中删除 `ui-ux-analysis/`；
- 删除 `### UI/UX 深度分析（主流程内）` 整节；
- 保留 `Functionality Deep-Dive` 说明；
- 若有“各类 deep-dive”泛化表述，保留但需避免误导为存在多个独立专项。

#### 预期结果

平台集成文档只描述当前真实存在的主流程与功能专项。

### 6.9 `mobile-qa-workflow/reference/analysis-strategies.md`

#### 修改目标

调整 UI/UX 分类策略，使复杂 UI 问题留在主 RCA 中分析。

#### 具体动作

- 删除“优先切换到 `ui-ux-analysis`”表述；
- 改写为：
  - 使用 `Strategy-LayoutTree`
  - 使用 `Strategy-ResourceChain`
  - 使用 `Strategy-RenderTiming`
  - 在主 RCA 内完成布局、渲染、交互时序分析

#### 预期结果

分析策略仍覆盖 UI/UX 问题，但不再依赖已删除模块。

### 6.10 `mobile-qa-workflow/reference/fix-strategies.md`

#### 修改目标

移除 Fix 阶段对 UI 专项摘要的消费假设。

#### 具体动作

- 删除“复杂 UI 问题：优先消费 `ui-ux-analysis-summary.md`”；
- 改为“复杂 UI 问题：优先回看主 RCA 中的 UI/UX 证据链与布局/渲染分析”。

### 6.11 `mobile-qa-workflow/templates/fix-design.md`

#### 修改目标

移除模板中的 UI 专项附录引用。

#### 具体动作

- 在“专项附录”中删除：
  - `UI/UX 深度分析（主流程内）`
- 保留：
  - `Functionality Deep-Dive`

#### 预期结果

模板字段与实际上游输入一致。

### 6.12 `mobile-qa-workflow/templates/rca-report.md`

#### 修改目标

去掉对 UI 专项的占位式描述，避免模板暗示未来或已存在 UI 专项。

#### 具体动作

- 将 “专项子工作流: [未触发 / 已触发-功能疑难专项 / 已触发-（不再包含 UI 专项）]”
  改为只保留主流程和功能专项相关表述。

### 6.13 `eval-framework/judge.py`

#### 修改目标

移除评测产物采集与 agent 估算中的 UI 专项逻辑。

#### 具体动作

- 在 `priority_files` 中删除：
  - `ui-ux-analysis/ui-ux-analysis-summary.md`
  - `ui-ux-analysis/ui-ux-analysis-rca.md`
- 在 `_estimate_agent_count()` 中删除：
  - `elif specialized_mode == "ui-ux-analysis": total += 3`

#### 预期结果

评测器不再读取不存在的 UI 专项产物，也不会为已删除模块计入 agent 数。

### 6.14 `eval-framework/coordinator.py`

#### 修改目标

同步修正运行时统计中的 UI 专项 agent 估算。

#### 具体动作

- 删除 `_estimate_agent_count()` 中 `ui-ux-analysis` 分支。

#### 预期结果

运行态统计与真实能力一致。

### 6.15 `eval-framework/case-schema.yaml`

#### 修改目标

移除 `expected_route` 枚举中的 `ui-ux-analysis`。

#### 具体动作

- 将：
  - `[standard-rca, functionality-deep-dive, ui-ux-analysis]`
  改为：
  - `[standard-rca, functionality-deep-dive]`

#### 预期结果

Schema 与系统支持能力一致。

### 6.16 `eval-framework/configs/eval-config.yaml`

#### 修改目标

收敛 Chain B 的命名和定位。

#### 具体动作

- 将：
  - `专家模式（Functionality/UI/UX 深度分析（主流程内））`
  改为：
  - `专家模式（Functionality Deep-Dive）`

#### 预期结果

对外配置和报表语义不再宣称 UI 专项能力。

## 7. 分批施工方案

建议按四个批次实施，避免一次性大改难以定位问题。

### 批次一：解除主工作流引用

目标：

- 不再有任何运行时路径尝试加载 UI 专项子工作流；
- 不再有任何上游/下游契约声明 UI 专项产物。

修改文件：

- `mobile-qa-workflow/core/workflow.xml`
- `mobile-qa-workflow/core/default-config.yaml`
- `mobile-qa-workflow/core/core-rules.xml`
- `mobile-qa-workflow/phases/p3-root-cause.md`
- `mobile-qa-workflow/phases/p4-fix-design.md`

完成判定：

- 检索 `ui-ux-analysis` 不再出现在主工作流关键文件中；
- 删除目录前，运行逻辑已不再引用它。

### 批次二：收敛模板与入口文档

目标：

- 入口与模板不再误导使用者；
- UI 问题的处理方式被重新描述为主 RCA 内分析。

修改文件：

- `mobile-qa-workflow/SKILL.md`
- `mobile-qa-workflow/system-prompt.md`
- `mobile-qa-workflow/PLATFORM-GUIDE.md`
- `mobile-qa-workflow/reference/analysis-strategies.md`
- `mobile-qa-workflow/reference/fix-strategies.md`
- `mobile-qa-workflow/templates/fix-design.md`
- `mobile-qa-workflow/templates/rca-report.md`

完成判定：

- 对外文档中不再出现 UI/UX 深度分析（主流程内） 作为正式能力。

### 批次三：删除模块实体

目标：

- 彻底删除 `mobile-qa-workflow/ui-ux-analysis/`。

修改范围：

- 删除整个目录。

完成判定：

- 目录不存在；
- 全仓检索没有运行面引用残留。

### 批次四：修正评测框架

目标：

- 评测框架不再读取 UI 专项产物；
- route schema、agent 统计、Chain B 描述收敛。

修改文件：

- `eval-framework/judge.py`
- `eval-framework/coordinator.py`
- `eval-framework/case-schema.yaml`
- `eval-framework/configs/eval-config.yaml`
- 视情况补充：
  - `eval-framework/comparator.py`
  - `eval-framework/report_generator.py`
  - `eval-framework/scoring_engine.py`

完成判定：

- `ui-ux-analysis` 不再是合法 route；
- 统计不会再为其计数；
- 报表语义与运行能力一致。

## 8. 验证方案

### 8.1 静态检索验证

施工完成后执行全仓检索，重点检查以下关键词：

- `ui-ux-analysis`
- `UI/UX 深度分析（主流程内）`
- `output_ui_ux_analysis`
- `ui_ux_analysis_summary`
- `ui_ux_analysis_rca`

通过标准：

- 运行逻辑、配置、模板、评测框架中不再出现上述关键字；
- 若 `doc/` 历史归档保留，则允许仅在历史文档中存在残留。

### 8.2 文件存在性验证

检查：

- `mobile-qa-workflow/ui-ux-analysis/` 不存在；
- 被修改文件均存在且语义完整；
- 不存在引用已删除文件的路径。

### 8.3 语义一致性验证

重点检查：

- P3 是否仅保留功能专项；
- P4 是否只读取 `deep-dive-summary.md`；
- Chain B 是否只描述功能专项；
- `expected_route` 是否只允许 `standard-rca` 和 `functionality-deep-dive`。

### 8.4 诊断验证

对修改文件运行诊断检查：

- YAML 结构有效；
- Python 语法有效；
- Markdown 无需严格语法验证，但应避免明显格式断裂。

### 8.5 回归关注点

重点关注下列潜在回归：

- 主 RCA 对 UI/UX 类问题是否仍可分析；
- Fix Design 是否因缺失 UI 摘要而报错；
- 评测链路是否仍能正确统计功能专项；
- Chain B 报表与配置描述是否一致。

## 9. 风险清单与规避措施

### 风险一：主流程仍残留悬挂引用

表现：

- 运行时尝试读取已删除的 `ui-ux-analysis` 文件；
- 或模板中仍要求 UI 专项产物。

规避措施：

- 必须先完成批次一，再删除目录；
- 删除后立即做全仓检索复查。

### 风险二：评测统计口径失真

表现：

- agent_count 偏高；
- route schema 与真实能力不一致；
- Chain B 描述仍包含 UI 专项。

规避措施：

- 必须同步修改 `judge.py`、`coordinator.py`、`case-schema.yaml`、`eval-config.yaml`。

### 风险三：文档口径与运行逻辑不一致

表现：

- 使用者仍会尝试寻找 UI 专项子目录；
- 系统说明仍宣称支持 UI/UX 深度分析（主流程内）。

规避措施：

- 同步收敛 `SKILL.md`、`system-prompt.md`、`PLATFORM-GUIDE.md`。

### 风险四：误删历史文档造成语义混乱

表现：

- 历史评审文档被修改后无法反映当时真实上下文。

规避措施：

- 默认不改 `doc/` 历史归档；
- 如需全文清理，应单独确认并作为第二阶段文档治理任务处理。

## 10. 回滚策略

### 10.1 轻量回滚

适用于发现某处引用遗漏但整体设计方向正确的情况。

做法：

- 保留已删除 `ui-ux-analysis` 目录的变更历史；
- 仅恢复个别误删字段或说明文案；
- 不恢复 UI 专项整体能力。

### 10.2 完整回滚

适用于确认本次移除策略不可接受的情况。

做法：

- 整体回滚本次提交；
- 恢复 `mobile-qa-workflow/ui-ux-analysis/` 目录；
- 恢复主 RCA、P4、规则层、评测层相关改动。

### 10.3 回滚判定标准

以下任一情况建议回滚：

- 主流程无法完成 RCA；
- Fix Design 因输入缺失无法运行；
- 评测框架核心链路失效；
- UI/UX 类问题出现明显分析能力断层，且无法在主 RCA 中吸收。

## 11. 施工后验收标准

满足以下条件视为验收通过：

- `mobile-qa-workflow/ui-ux-analysis/` 已彻底删除；
- 主流程、模板、规则、配置中无 UI 专项运行时引用；
- 评测框架不再采集或统计 UI 专项；
- Chain B 对外描述已收敛；
- 功能专项能力不受影响；
- 全仓检索残留仅限历史归档文档或明确允许保留的说明材料。

## 12. 推荐执行顺序

推荐严格按以下顺序落地：

1. 修改 `mobile-qa-workflow/core/*` 与 `phases/p3-root-cause.md`
2. 修改 `phases/p4-fix-design.md`
3. 修改模板、策略参考、入口文档
4. 删除 `mobile-qa-workflow/ui-ux-analysis/`
5. 修改 `eval-framework/*`
6. 全仓检索复查
7. 运行诊断与最小验证

## 13. 施工确认结论

本次施工本质上是一次“能力下线”而不是“代码目录删除”。

其关键成功点在于：

- 先从主工作流切断所有入口；
- 再删除模块实体；
- 最后统一修正评测与说明层口径。

只要严格按本文档分批执行，可以在不破坏主链路和功能专项的前提下，完整移除 `ui-ux-analysis`。
