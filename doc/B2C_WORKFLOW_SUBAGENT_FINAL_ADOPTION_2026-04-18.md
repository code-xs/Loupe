# B2C 移动端质量工作流 SubAgent 拆分最终采纳版

> 日期：2026-04-18
> 目标：形成面向 B2C 场景的最终采纳方案，作为后续架构调整与实施的唯一执行口径

---

## 1. 最终结论

当前工作流的优化方向不是简单减少 SubAgent 数量，而是在不损伤归因质量、修复质量和工程可审计性的前提下，压缩真正偏重的专项链路，并降低默认执行成本。

最终采纳结论如下：

1. **主工作流保留 6 个核心业务 Agent，不做粗暴合并。**
2. **专项深挖链路从当前重型拆分收敛为 4~5 个复合角色。**
3. **`challenger` / `arbiter` 采用共享基座 + 场景参数化。**
4. **P3 / P4 从默认重 fan-out 调整为按复杂度动态升级。**
5. **专项中间产物改为“核心产物强制独立、分析草稿按需附录”。**
6. **后续是否继续裁剪，以评测指标而非主观感觉为准。**

一句话版本：

> 保留主链路质量上限，收缩专项链路编排重量，把当前体系从“研究型重工作流”收敛为“生产型高质量工作流”。

---

## 2. 采纳后的目标架构

## 2.1 主工作流

主工作流继续保留以下 6 个核心业务 Agent：

- `curator`
- `investigator`
- `challenger`
- `arbiter`
- `fix-proposer`
- `coder-agent`

这 6 个角色分别承担：

1. 上下文净化
2. 根因调查
3. 结论质疑
4. 最终裁定
5. 修复设计
6. 修复实施

该拆分与 B2C 质量问题闭环的核心认知任务一一对应，继续合并会明显损伤质量上限，不采纳进一步压缩主链路角色的方案。

## 2.2 专项深挖工作流

`functionality-deep-dive` 采纳“收一层、不压平”的优化方向。

目标角色结构如下：

1. `deep-dive-context-analyst`
   - 负责环境因子重建
   - 吸收部分状态输入预处理能力

2. `deep-dive-structure-analyst`
   - 负责状态机与数据流拓扑分析
   - 在需要时执行轻量时序预扫描

3. `deep-dive-race-and-isolation-analyst`
   - 负责竞态、时序窗口、隔离推演
   - 吸收当前 F4 中对通用 `investigator` 的借用职责

4. `deep-dive-arbiter`
   - 负责“先质疑、后裁定”的收敛协议
   - 吸收专项 `challenger + arbiter` 的双阶段能力

5. `defensive-fix-architect`
   - 保留为按需触发角色
   - 仅在需要生成防御性修复附录时启动

采纳后的原则是：

- 不再保留当前“一阶段对应一个细粒度 Agent”的重型串行结构
- 也不将专项链路一次性压缩为单一大 Agent
- 目标是让专项链路既保留专门分析能力，又具备可运营性和可维护性

---

## 3. 共享能力设计

## 3.1 `challenger` / `arbiter` 共享基座

采纳共享基座方案。

建议抽象为：

- `agents/shared-challenger-base.md`
- `agents/shared-arbiter-base.md`

主流程与专项流程通过参数注入差异：

- 场景：`RCA` / `Fix` / `Deep-Dive`
- 维度集：5 维 / 7 维 / 4 重攻击
- 输出模板差异
- 评分口径差异

预期收益：

1. 减少重复维护
2. 降低 prompt 漂移
3. 统一仲裁与质疑口径
4. 降低主流程与专项流程之间的规则不一致风险

## 3.2 Agent 分类口径

采纳“业务角色”与“能力型 Agent”区分方案。

### 业务角色

- `curator`
- `investigator`
- `challenger`
- `arbiter`
- `fix-proposer`
- `coder-agent`
- 各类 deep-dive analyst / architect

### 能力型 Agent

- `search`

这样做的目标是避免误判实际业务角色复杂度，并提升后续设计文档、评测口径与沟通口径的一致性。

---

## 4. 编排优化方案

## 4.1 P3 Root Cause

采纳按复杂度动态升级的 fan-out 策略：

- `simple`
  - 主 Agent 单视角 OVHSC

- `medium`
  - `investigator + challenger`

- `complex` 或 `证据冲突`
  - `2 investigators + challenger + arbiter`

目标是把默认重模式从“常态”改为“升级态”。

## 4.2 P4 Fix Design

采纳按风险与置信度动态升级的方案生成策略：

- `根因高置信度 + 变更范围单点`
  - 单 `fix-proposer`

- `根因中置信度`
  - `fix-proposer + challenger`

- `多方案竞争` 或 `高风险修改`
  - `2 proposers + challenger + arbiter`

## 4.3 专项 F4 收敛修正

采纳修正专项 F4 角色边界的方案。

目标状态：

- 专项工作流不再借用主链路通用 `investigator` 作为关键收敛角色
- 专项根因收敛能力内聚到专项复合分析角色中
- 专项工作流形成自洽、闭合的角色体系

---

## 5. 产物策略

采纳“强制独立文件”和“按需附录”两级制。

## 5.1 强制独立文件

以下产物继续保留为一级独立交付物：

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

## 5.2 按需附录或内部章节

以下专项分析产物降级为按需输出：

- `environment-factor-report.md`
- `deep-dive-topology.md`
- `concurrency-analysis-report.md`

执行原则：

- 当专项分析对审计、复盘或跨团队协作有显著价值时，仍可单独落盘
- 对一般 Case，优先沉入专项 RCA 附录或内部章节，减少文件风暴

---

## 6. 改造优先级

## 6.1 P0

1. 统一 `challenger` / `arbiter` 基座
2. 修正专项 F4 对通用 `investigator` 的借用式设计
3. 在设计文档中明确区分业务角色与能力型 Agent

## 6.2 P1

1. 将专项 F2 / F3 / F4 收敛为更少的复合分析角色
2. 将部分专项中间产物降级为附录
3. 为 P3 / P4 增加按复杂度触发的动态 fan-out 规则

## 6.3 P2

1. 建设 `UI Deep-Dive Workflow`
2. 用 `eval-framework` 验证不同拆分策略的真实收益

---

## 7. 验收指标

后续所有 SubAgent 裁剪、合并和编排调整，都以以下指标作为验收基线：

1. `attribution_accuracy`
2. `fix_correctness`
3. `artifact_completeness`
4. `contract_first_pass_accuracy`
5. `hallucination_interception`
6. `self_healing_rate`
7. 平均单 Case 调用 Agent 数
8. 深度路径触发率
9. Deep-Dive 进入率与实际收益比

验收原则：

- 若角色减少但归因质量下降，不视为成功
- 若调用成本下降且关键质量指标持平或提升，才视为有效优化
- 若专项进入率高但收益低，应继续压缩专项链路重量

---

## 8. 执行口径

从本文件起，后续关于 B2C SubAgent 拆分的改造，以以下口径统一执行：

1. **主链路不压缩核心认知角色。**
2. **专项链路收敛为复合角色，而不是单一大角色。**
3. **重复角色通过共享基座消除，而不是继续双份维护。**
4. **重型多 Agent 编排必须由复杂度或冲突证据触发。**
5. **所有改造最终服从评测数据。**
