# B2C 移动端质量工作流模块全景与 SubAgent 拆分评审

> 日期：2026-04-18
> 范围：当前仓库运行时主工程、专项子工作流、评测框架与历史设计资料
> 目标：深入理解工程模块与文件职责，判断当前 subagent 拆分是否过多，并给出面向 B2C 场景的优化建议

---

## 1. 结论先行

### 1.1 总体判断

当前工程不是一个“Prompt 堆”，而是一套已经具备以下四层能力的质量问题处理系统：

1. **运行入口层**：`SKILL.md` / `system-prompt.md` 负责适配 Full 与 Limited 平台。
2. **主工作流编排层**：`core/workflow.xml` + `phases/p1~p6` 负责六阶段问题闭环。
3. **专项深挖层**：`functionality-deep-dive/` 负责复杂功能类问题的独立深度分析。
4. **评测与优化层**：`eval-framework/` + `eval-cases/` 负责效果校验、弱点识别与自优化。

从“是否要优于市场大多数同类方案”的目标看，这种分层方向是对的，因为它兼顾了：

- 过程审计性
- 复杂问题的专门分析能力
- 平台能力降级路径
- 评测闭环与持续迭代能力

### 1.2 对 subagent 拆分是否过多的结论

**结论不是“整体过多”，而是“主链路基本合理，专项链路偏重，部分角色重复与粒度过细”。**

更具体地说：

1. **主工作流的 subagent 数量不算过多**。
   - `curator`
   - `investigator`
   - `challenger`
   - `arbiter`
   - `fix-proposer`
   - `coder-agent`
   这 6 个角色分别对应证据净化、根因分析、反驳、裁定、方案设计、代码实施，职责边界清楚，符合高质量移动端问题闭环的真实分工。

2. **真正显得偏重的是 `functionality-deep-dive/` 的专项拆分**。
   - `context-reconstructor`
   - `state-analyst`
   - `temporal-analyst`
   - `challenger`
   - `arbiter`
   - `defensive-fix-architect`
   这套拆分方法论上是成立的，但在当前实现中存在串行依赖强、角色复用度高、产物中间层偏多的问题，已经接近“为分析而分析”。

3. **重复定义的 `challenger` / `arbiter` 是最明显的可收敛点**。
   主工作流和专项工作流分别维护两套同名角色文件，语义高度相似，只是质疑维度和仲裁对象不同，适合改为“共享基座 + 场景参数化”。

4. **`search` 不应被当成核心业务 subagent 计数**。
   它更像“检索能力插件”而不是领域专家。若把它算入 subagent 数，会夸大实际的角色复杂度。

### 1.3 我的最终建议

若目标是 **B2C 场景下显著提升归因与修复能力，同时控制工程复杂度**，建议采取：

1. **保留主链路 6 个核心 agent，不建议粗暴合并。**
2. **收缩专项深挖链路，把 6 个专项 agent 收敛到 4 个左右的“复合型专项角色”。**
3. **把重复的质疑/仲裁 prompt 抽象为共享基座，而不是两套近似文件。**
4. **把多 agent fan-out 改成“按复杂度动态升级”，而不是默认重型编排。**

---

## 2. 工程全景理解

## 2.1 目录层级总览

当前仓库的核心结构可以按“运行主链路”和“治理支撑链路”理解：

### 运行主链路

- `mobile-qa-workflow/`
  - 主工作流入口、编排规则、阶段实现、模板、参考知识、agent 定义
- `mobile-qa-workflow/functionality-deep-dive/`
  - 主工作流可路由触发的复杂功能问题专项深挖子工作流

### 治理支撑链路

- `eval-framework/`
  - 评测运行器、评分引擎、弱点检测器、优化器
- `eval-cases/`
  - 评测样本与标准答案
- `doc/`
  - 历史设计、评审、QA 报告、架构提案

---

## 3. 模块与文件职责梳理

以下内容聚焦“当前运行体系中真正重要的文件”。对于 `eval-cases/seed-10/*` 这类重复结构样本，只总结模板结构，不逐个展开。

## 3.1 `mobile-qa-workflow/` 根目录

| 文件 | 作用 |
|------|------|
| `SKILL.md` | Full 能力平台统一入口，负责初始化工作区、环境探测、加载主编排器 |
| `system-prompt.md` | Limited 平台整包入口，把规则、阶段、模板、知识内联到单文件 |
| `PLATFORM-GUIDE.md` | 平台接入与 Full/Limited/Minimal 差异说明 |
| `install.sh` | Cursor/通用 Skill 安装脚本 |
| `install_trae.sh` | Trae Skill 安装脚本 |

### 评价

- `SKILL.md` 是真实运行入口，结构清晰。
- `system-prompt.md` 负责能力降级，是平台适配的关键资产。
- `PLATFORM-GUIDE.md` 很重要，因为它说明该工程从一开始就不是只为单一平台设计。

## 3.2 `mobile-qa-workflow/core/`

| 文件 | 作用 |
|------|------|
| `core-rules.xml` | 全局 DSL 语义、执行规则、`invoke-subagent` 契约、人审协议 |
| `workflow.xml` | 主编排器，负责阶段调度、状态路由、阶段 I/O 契约 |
| `workflow-model.yaml` | 六阶段顺序定义 |
| `workflow-status-template.yaml` | 问题工作区状态模板 |
| `default-config.yaml` | 工作区默认配置与产物路径登记表 |

### 评价

- `core-rules.xml` 是整个系统最关键的底座文件。
- `workflow.xml` 的状态机、I/O 契约和恢复能力较成熟。
- `default-config.yaml` 把产物路径与环境能力显式化，是工程化而非纯 prompt 化的重要标志。

## 3.3 `mobile-qa-workflow/phases/`

| 文件 | 作用 |
|------|------|
| `p1-intake.md` | 受理、分类、边界判断、最小信息集门禁 |
| `p2-spec-definition.md` | Spec 三要素、非 Bug 判定、候选证据搜集、Context Curation |
| `p3-root-cause.md` | 证据阈值、边界路由、复杂度评估、OVHSC、多 agent RCA、专项路由 |
| `p4-fix-design.md` | 修复策略生成、四重论证、方案仲裁、回归设计 |
| `p5-fix-impl.md` | 修复路由、Coder Agent 调用、实施产物验收 |
| `p6-verification.md` | L1/L2/L3 静态验证、知识卡生成、闭环与 PR 生成 |

### 评价

- 六阶段分层很稳，符合移动端质量问题从“事实收集 -> 规约 -> 归因 -> 设计 -> 实施 -> 验证”的自然流程。
- P3/P4/P5 是工程价值最高的三个阶段，也是复杂度最高的三个阶段。

## 3.4 `mobile-qa-workflow/agents/`

| 文件 | 作用 |
|------|------|
| `curator.md` | 上下文策展，防止脏上下文/死代码进入 RCA |
| `investigator.md` | 执行 OVHSC 的独立根因调查员 |
| `challenger.md` | 归因/修复方案的反驳者 |
| `arbiter.md` | 汇总多个结论并进行最终裁定 |
| `fix-proposer.md` | 设计修复方案并完成四重论证 |
| `coder-agent.md` | 契约溯源、精确编码、微验证、自愈与移交 |

### 评价

- 这 6 个角色是当前主链路真正的业务核心角色。
- 这套拆分并不冗余，反而是当前系统优于通用型方案的关键原因之一。

## 3.5 `mobile-qa-workflow/reference/`

| 文件 | 作用 |
|------|------|
| `analysis-strategies.md` | P3 深度 RCA 的策略池与多视角协议 |
| `reasoning-chain.md` | OVHSC 推理链定义 |
| `platform-checklist.md` | Android/iOS 平台检查要点与约束 |
| `fix-strategies.md` | 修复方案设计时的策略知识库 |

### 评价

- `reference/` 让工作流不只是“角色扮演”，而是有知识支撑。
- 这类文件不应该被再拆成独立 agent，它们更适合作为共享知识库。

## 3.6 `mobile-qa-workflow/templates/`

| 文件 | 作用 |
|------|------|
| `issue-card.md` | 问题受理后的标准卡片 |
| `spec.md` | Spec 与分类扩展字段模板 |
| `context-curation-report.md` | 策展留痕模板 |
| `context-bundle.md` | 进入 RCA 的证据包模板 |
| `rca-report.md` | 根因分析报告模板 |
| `fix-design.md` | 修复方案设计模板 |
| `contract-checklist.md` | 契约溯源清单模板 |
| `impl-report.md` | 实施报告模板 |
| `error-dump.md` | 失败现场转储模板 |
| `verification-report.md` | 验证报告模板 |
| `knowledge-card.md` | 抽象化知识沉淀模板 |
| `intake-form.md` / `intake-form-blank.md` | 受理采集表 |

### 评价

- 模板体系很完整。
- 模板数量虽多，但这不是坏事，因为它直接提升可审计性与评测友好度。
- 真正需要控制的是“哪些模板必须成为独立文件”，而不是简单减少模板个数。

## 3.7 `mobile-qa-workflow/functionality-deep-dive/`

### 核心说明文件

| 文件 | 作用 |
|------|------|
| `FUNCTIONALITY_DEEP_DIVE_WORKFLOW_V3.md` | 专项子工作流总体说明与边界 |
| `agents/README.md` | 专项角色清单说明 |

### `core/`

| 文件 | 作用 |
|------|------|
| `core/workflow.xml` | 专项子工作流编排器 |
| `core/workflow-model.yaml` | F1-F5 阶段定义 |
| `core/workflow-status-template.yaml` | 子工作区状态模板 |
| `core/default-config.yaml` | 子工作流默认配置 |

### `phases/`

| 文件 | 作用 |
|------|------|
| `f1-context-reconstruction.md` | 环境因子重建 |
| `f2-state-topology.md` | 状态机与数据流拓扑还原 |
| `f3-temporal-correlation.md` | 时间轴与竞态窗口分析 |
| `f4-isolation-debate.md` | 隔离诊断、多 agent 对抗与专项 RCA 汇总 |
| `f5-defensive-fix-design.md` | 防御性修复附录生成 |

### `agents/`

| 文件 | 作用 |
|------|------|
| `context-reconstructor.md` | 隐蔽环境因子与系统干预重建 |
| `state-analyst.md` | 状态机/数据流分析 |
| `temporal-analyst.md` | 时序/竞态分析 |
| `challenger.md` | 专项七维质疑 |
| `arbiter.md` | 专项仲裁 |
| `defensive-fix-architect.md` | 防御性修复设计 |

### `reference/`

| 文件 | 作用 |
|------|------|
| `environment-factor-thresholds.md` | 环境阈值知识 |
| `state-machine-patterns.md` | 状态机异常模式 |
| `race-condition-patterns.md` | 竞态模式 |
| `isolation-patterns.md` | 隔离诊断模式 |
| `README.md` | 参考资料说明 |

### `templates/`

| 文件 | 作用 |
|------|------|
| `environment-factor-report.md` | F1 产物模板 |
| `deep-dive-topology.md` | F2 产物模板 |
| `concurrency-analysis-report.md` | F3 产物模板 |
| `functionality-deep-dive-rca.md` | F4 主专项 RCA 模板 |
| `deep-dive-summary.md` | 主工作流回注摘要 |
| `defensive-fix-design.md` | F5 附录修复模板 |

### 评价

- 这是当前工程最“重型”的部分。
- 从效果导向看，它很专业。
- 从工程运营看，它开始接近“一个独立产品线”，这也是 subagent 过重感的主要来源。

## 3.8 `eval-framework/`

| 文件 | 作用 |
|------|------|
| `coordinator.py` | 评测协调器，驱动 Case × Chain 执行 |
| `session_manager.py` | IDE 会话管理 |
| `baseline_runner.py` | 基线模型执行 |
| `artifact_checker.py` | 产物完整性校验 |
| `judge.py` | 评判器 |
| `scoring_engine.py` | 多维度评分统计 |
| `weakness_detector.py` | 低分环节识别与归因 |
| `optimizer.py` | 自动生成改进方案并应用/回滚 |
| `quality_gate.py` | 质量门禁 |
| `report_generator.py` | 生成评测报告 |
| `comparator.py` | 链路或方案对比 |
| `iteration_loop.py` | 迭代运行逻辑 |
| `case-schema.yaml` | Case 结构定义 |
| `artifact-checklist.yaml` | 产物校验基准 |
| `scoring-rubric-base.yaml` | 评分基线 |
| `auto-reply-rules.yaml` | IDE 自动回复规则 |
| `configs/*.yaml` | 不同评测 profile 配置 |
| `tests/test_judge_parse.py` | 评测层测试 |

### 评价

- 评测层是这个仓库的“护城河”之一。
- 它使 subagent 拆分不只是拍脑袋，而可以与分数、弱点维度和迭代策略挂钩。

## 3.9 `eval-cases/`

结构模式统一：

- `metadata.yaml`
- `input/issue-description.md`
- `input/logs/README.md`
- `input/code-snapshot/README.md`
- `ground-truth/expected-root-cause.md`
- `ground-truth/expected-contributing.md`
- `ground-truth/expected-fix-direction.md`
- `ground-truth/scoring-rubric.yaml`

### 评价

- 这部分不是运行逻辑，但决定了优化是否有客观锚点。
- 也是判断“subagent 增减是否真的提升效果”的最终依据。

## 3.10 `doc/`

`doc/` 中保留了大量历史报告、架构提案和 QA 结论。它们不属于运行路径，但有三类重要价值：

1. 记录设计演进过程
2. 解释为何引入某些重型结构
3. 为后续裁剪或合并提供历史上下文

---

## 4. 当前 SubAgent 实际拓扑

## 4.1 主工作流的调用图

### Phase 2

- `search`：搜集候选证据
- `curator`：策展与净化

### Phase 3

- `investigator` x 2：多视角 RCA
- `challenger`：五维/七维质疑
- `arbiter`：最终裁定
- 可选：跨平台时 `investigator` x 2

### Phase 4

- `fix-proposer` x 2：多方案设计
- `challenger`
- `arbiter`

### Phase 5

- `coder-agent`

## 4.2 专项深挖工作流的调用图

### F1

- `context-reconstructor`

### F2

- `state-analyst`

### F3

- `temporal-analyst`

### F4

- `investigator`
- `challenger`
- `arbiter`

### F5

- `defensive-fix-architect`

## 4.3 数量判断

如果按“角色文件数”看，当前工程看起来很多；但若按“真正进入一次典型 Case 的 agent 数”看，需要分场景：

1. **普通 Case**
   - 可能只有 `search + curator + investigator/challenger/arbiter + fix-proposer/challenger/arbiter + coder-agent`
2. **简单 Case**
   - P3/P4 甚至会走单对话降级模式，不一定触发完整 fan-out
3. **复杂功能疑难 Case**
   - 才会叠加 F1-F5 的专项链路

因此，“agent 总量偏多”主要发生在 **复杂功能疑难场景**，而不是所有问题默认都这么重。

---

## 5. 对“是否过拆”的具体评判

## 5.1 不算过拆的部分

### 1. `curator` 不应与 `investigator` 合并

原因：

- 前者负责“证据净化”
- 后者负责“根因推理”

若合并，容易出现“边找边信、边信边推”的锚定污染。

### 2. `challenger` / `arbiter` 在主工作流中仍有价值

原因：

- B2C 场景的复杂问题经常存在偶发、跨端、跨模块、证据冲突
- 单 Investigator 结论容易“看起来合理但不够稳”
- 质疑与仲裁机制是优于通用方案的重要来源

### 3. `fix-proposer` 与 `coder-agent` 必须分离

原因：

- 方案设计与代码实施是两种完全不同的认知负载
- `coder-agent` 的价值恰恰在于隔离实现噪音和实施幻觉

**结论**：主工作流 6 个核心 agent 不建议做大合并。

## 5.2 明显偏重的部分

### 1. `functionality-deep-dive` 阶段与 agent 基本一一对应，串行感过强

当前 F1/F2/F3/F5 基本是：

- 一个阶段
- 一个专项 agent
- 一个独立产物

这使得：

- 编排层复杂
- 中间产物增多
- 每个阶段都要读写文件
- 真正并行收益有限，因为 F2 依赖 F1，F3 依赖 F2，F4 又依赖前三者

这更像“学术式分解”，而不是“生产式高效执行”。

### 2. 专项 `challenger` / `arbiter` 与主链路版本重复度高

差异主要在：

- 质疑维度数量不同
- 关注对象从一般根因变成状态机/生命周期/缓存/并发

但角色骨架非常相似，维护两套文件会带来：

- prompt 漂移
- 改动同步成本
- 规则不一致风险

### 3. F4 的角色体系存在不完全自洽

在 `f4-isolation-debate.md` 中，专项工作流没有使用专门的“deep-dive investigator”，而是调用了通用 `investigator`，再额外加载 `state-analyst.md` 作为补充视角。

这反映出一个问题：

- 角色边界并没有完全闭合
- 专项工作流在汇总阶段仍借用了主链路通用角色
- 说明当前专项角色体系还没有收敛到最自然的形态

### 4. 主链路 P3/P4 的默认 fan-out 仍然偏重

当前深度路径 RCA 和多方案 Fix Design 默认就是：

- 双 Investigator / 双 Proposer
- Challenger
- Arbiter

这种设计在 P0/P1 或强冲突证据场景下合理，但对一部分中等复杂度问题来说，成本偏高。

### 5. 部分中间产物更像“内部推理草稿”，没必要都强制独立文件化

尤其在专项工作流中：

- `environment-factor-report.md`
- `deep-dive-topology.md`
- `concurrency-analysis-report.md`

它们当然有价值，但不一定都需要始终作为一级产物存在。对不少 Case 来说，把它们沉为附录或内部 section 即可。

---

## 6. 当前实现中已观察到的结构性问题

## 6.1 角色定义重复

重复最明显的是：

- `mobile-qa-workflow/agents/challenger.md`
- `mobile-qa-workflow/functionality-deep-dive/agents/challenger.md`
- `mobile-qa-workflow/agents/arbiter.md`
- `mobile-qa-workflow/functionality-deep-dive/agents/arbiter.md`

问题不是“不能重复”，而是：

- 两套文件高度同构
- 长期会出现一边增强、一边滞后的漂移

## 6.2 专项路由只覆盖功能疑难，整体产品谱系未闭合

历史架构提案里已经提出 `UI Deep-Dive Workflow`，但当前仓库只真正落地了 `Functionality Deep-Dive Workflow`。

这会导致：

- 功能疑难有重型专线
- UI 疑难仍主要靠主链路

从 B2C 全场景效果看，产品谱系并不完全平衡。

这不是“subagent 太多”的问题，但会影响“拆分是否值得”的投入产出比。

## 6.3 `search` 的地位不稳定

P2 使用的是 `subagent_type="search"`，但它不是主工程 `agents/` 目录中的业务角色定义。

这说明当前系统实际上混用了两类能力：

1. 业务 subagent
2. 平台工具型 subagent

如果不在设计文档里明确区分，团队很容易高估“业务角色数量”。

---

## 7. 优化建议

## 7.1 原则

优化目标不应是“为了减少数量而减少数量”，而应是：

1. 保住真正带来质量收益的隔离
2. 消除重复角色与低并行价值的过细拆分
3. 让复杂模式只在必要时触发

## 7.2 建议一：主工作流保留 6 个核心 agent，不做粗暴合并

### 建议保留

- `curator`
- `investigator`
- `challenger`
- `arbiter`
- `fix-proposer`
- `coder-agent`

### 原因

- 这 6 个角色正好对应质量问题闭环中的 6 类核心认知任务
- 继续合并会明显损伤质量上限
- 相比市场大多数“一个 agent 干到底”的方案，这正是当前工程的优势所在

## 7.3 建议二：把专项深挖从 6 角色综合为 4 个复合角色

### 推荐目标结构

1. `deep-dive-context-analyst`
   - 合并当前 `context-reconstructor`
   - 吸收一部分状态输入预处理能力

2. `deep-dive-structure-analyst`
   - 合并 `state-analyst`
   - 在需要时内嵌时序预扫描

3. `deep-dive-race-and-isolation-analyst`
   - 合并 `temporal-analyst`
   - 吸收 F4 中 Investigator 的隔离推演能力

4. `deep-dive-arbiter`
   - 吸收专项 `challenger + arbiter`
   - 以“先质疑后裁定”的单角色双阶段协议运行

5. `defensive-fix-architect`
   - 保留，但只在需要生成防御性附录时触发

### 预期收益

- 专项运行角色从 6 降到 4~5
- F4 的通用 `investigator` 借用问题会自然消失
- 中间产物数量可同步减少

## 7.4 建议三：把 `challenger` / `arbiter` 抽成共享基座

### 做法

保留一个主文件基座，例如：

- `agents/shared-challenger-base.md`
- `agents/shared-arbiter-base.md`

然后由主流程与专项流程通过参数化注入：

- 场景：RCA / Fix / Deep-Dive
- 维度集：5 维 / 7 维 / 4 重攻击
- 输出模板差异

### 预期收益

- 减少重复维护
- 降低 prompt 漂移
- 更容易统一评测口径

## 7.5 建议四：把多 agent fan-out 改为动态升级矩阵

### 当前问题

P3/P4 对中等复杂度问题也容易进入双 investigator / 双 proposer + challenger + arbiter 的重模式。

### 建议策略

#### P3

- `simple`：主 Agent 单视角 OVHSC
- `medium`：`investigator + challenger`
- `complex` 或 `证据冲突`：`2 investigators + challenger + arbiter`

#### P4

- `根因高置信度 + 变更范围单点`：单 `fix-proposer`
- `根因中置信度`：`fix-proposer + challenger`
- `多方案竞争` 或 `高风险修改`：`2 proposers + challenger + arbiter`

### 预期收益

- 降低平均成本
- 把重模式留给真正需要的 Case
- 不牺牲疑难场景上限

## 7.6 建议五：重新定义哪些产物必须独立文件化

### 推荐保留为强制独立文件

- `issue-card.md`
- `spec.md`
- `context-bundle.md`
- `rca-report.md`
- `fix-design.md`
- `contract-checklist.md`
- `impl-report.md`
- `verification-report.md`
- `knowledge-card.md`
- `deep-dive-summary.md`

### 推荐降级为“按需附录/内部章节”

- `environment-factor-report.md`
- `deep-dive-topology.md`
- `concurrency-analysis-report.md`

### 原因

- 这些文件对审计有价值，但不一定都要始终作为一级交付物
- 可降低专项工作流的文件风暴

## 7.7 建议六：在设计文档中区分“业务角色”与“能力型 agent”

### 建议分类

#### 业务角色

- `curator`
- `investigator`
- `challenger`
- `arbiter`
- `fix-proposer`
- `coder-agent`
- 各类专项 analyst / architect

#### 能力型 agent

- `search`

### 原因

- 便于正确理解实际 subagent 复杂度
- 避免把检索能力误当成业务角色膨胀

---

## 8. 推荐的目标拆分方案

## 8.1 短期可落地版

### 保留

- 主工作流 6 个核心角色不动
- 专项 F5 的 `defensive-fix-architect` 保留

### 调整

1. 合并专项 `challenger` + `arbiter`
2. F4 不再调用通用 `investigator`
3. 将 F2/F3 视情况合并为一个复合专项分析阶段

### 结果

- 主工作流：6 个核心角色
- 专项工作流：6 降到约 4 个角色

## 8.2 中期优化版

1. 共享 `challenger` / `arbiter` 基座
2. 以复杂度驱动 P3/P4 fan-out
3. 缩减专项中间产物
4. 把专项阶段从 F1-F5 收敛到 F1-F4

## 8.3 长期产品版

1. 保留主工作流 6 核心角色
2. `Functionality Deep-Dive` 收敛为 4 角色
3. 独立建设 `UI Deep-Dive`
4. 用统一评测框架比较不同拆分策略的收益

---

## 9. 我的最终判断

### 9.1 回答“当前 subagent 拆分是否过多”

**回答：局部过多，但不是全局过多。**

### 9.2 更精确的判断

1. **主工作流没有过拆**
   - 它的角色数和职责边界是匹配的
   - 如果希望效果显著优于市场方案，主链路不宜再压缩

2. **专项深挖有过拆倾向**
   - 主要体现在阶段串行化、角色重复、文件产物过密
   - 当前更像“研究型工作流”，可以向“生产型专项工作流”收一层

3. **最优路线不是减少主链路 agent，而是压缩专项链路的重度编排**
   - 保住质量上限
   - 降低维护和执行成本

### 9.3 一句话建议

> 保留主工作流 6 个核心业务 agent，把专项深挖从“6 角色 + 5 中间产物”的重模式，收敛成“4 角色 + 动态产物”的轻重分层模式，是当前最适合 B2C 场景的优化方向。

---

## 10. 建议的改造优先级

### P0

1. 统一 `challenger` / `arbiter` 基座
2. 修正专项 F4 对通用 `investigator` 的借用式设计
3. 在设计文档中明确区分业务角色与能力型 agent

### P1

1. 将专项 F2/F3/F4 收敛为更少的复合分析角色
2. 将部分专项中间产物降级为附录
3. 给 P3/P4 增加按复杂度触发的动态 fan-out 规则

### P2

1. 独立建设 `UI Deep-Dive Workflow`
2. 用 `eval-framework` 验证不同 agent 拆分方案的真实收益，而不是凭直觉裁剪

---

## 11. 适合作为后续改造验收的指标

若后续真的调整 subagent 拆分，建议至少观测以下指标：

1. `attribution_accuracy`
2. `fix_correctness`
3. `artifact_completeness`
4. `contract_first_pass_accuracy`
5. `hallucination_interception`
6. `self_healing_rate`
7. 平均单 Case 调用 agent 数
8. 深度路径触发率
9. Deep-Dive 进入率与实际收益比

只有在这些指标证明“更少的角色仍能保持或提升结果”时，裁剪才是正确的。

