# Functionality Deep-Dive Workflow V4

> 适用场景：复杂、偶发、难复现的业务逻辑异常，如状态机紊乱、并发竞态、缓存一致性问题、生命周期耦合问题。
> 设计原则：保留专项分析能力，但收敛为复合角色并降低默认文件风暴。

## 目标角色结构
1. `deep-dive-context-analyst`
2. `deep-dive-structure-analyst`
3. `deep-dive-race-and-isolation-analyst`
4. `deep-dive-arbiter`
5. `defensive-fix-architect`（按需触发）

## 五阶段模型
1. `F1` 环境与上下文重构
2. `F2` 状态机与数据流拓扑
3. `F3` 时序对齐与竞态剖析
4. `F4` 隔离诊断与专项收敛
5. `F5` 防御性修复附录（按需）

## 产物策略
- 强制独立：`deep-dive-summary.md`、`functionality-deep-dive-rca.md`
- 按需独立：`environment-factor-report.md`、`deep-dive-topology.md`、`concurrency-analysis-report.md`
- 条件独立：`defensive-fix-design.md`

## 边界修正
- `F4` 不再借用主链路通用 `investigator`
- 专项链路通过 `deep-dive-race-and-isolation-analyst + deep-dive-arbiter` 形成自洽闭环
- 旧细粒度角色仅保留给历史会话恢复

## 回注主工作流
- 主流程至少消费 `Primary Root Cause`、`Contributing Factors`、`Top Evidence`、`Confidence Level`
- 若 `Need Defensive Fix = Yes`，则在 `fix-design.md` 中消费 `defensive-fix-design.md`
