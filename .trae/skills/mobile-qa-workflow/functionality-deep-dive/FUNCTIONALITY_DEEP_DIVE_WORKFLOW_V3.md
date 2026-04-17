# Functionality Deep-Dive Workflow V3

> 适用场景：复杂、偶发、难复现的业务逻辑异常，如状态机紊乱、并发竞态、缓存一致性问题、生命周期耦合问题。
> 设计原则：效果优先，独立专项分析，结果回注主工作流。

## 1. 目标

本子工作流用于处理主工作流难以通过标准 RCA 路径快速收敛的复杂功能异常问题。它聚焦于：

- 状态机拓扑还原
- 数据流与不可变性审查
- 时序对齐与竞态剖析
- 多 Agent 对抗式归因
- 防御性修复与架构演进建议

## 2. 触发条件

由主工作流 `p3-root-cause.md` 分诊触发，建议满足以下任一条件时进入本子工作流：

1. 主分类为 `功能`，且 `complexity_level in {medium, complex}`
2. 问题具有偶发性，且涉及状态机、并发、缓存一致性、生命周期耦合中的任一维度
3. 标准快速路径反事实校验失败，且异常不属于纯 UI 结构问题

## 3. 输入

- `issue-card.md`
- `spec.md`
- `context-bundle.md`
- 主工作流路由结果与复杂度评估
- 可用日志 / APM / 抓包 / 代码库访问能力

## 4. 五阶段模型

1. `F1` 环境与上下文重构
2. `F2` 状态机与数据流拓扑
3. `F3` 时序对齐与竞态剖析
4. `F4` 隔离诊断与多 Agent 对抗
5. `F5` 防御性修复与架构演进建议

## 5. 核心产物

- `environment-factor-report.md`
- `deep-dive-topology.md`
- `concurrency-analysis-report.md`
- `functionality-deep-dive-rca.md`
- `defensive-fix-design.md`（条件输出）
- `deep-dive-summary.md`

## 6. 回注主工作流

本子工作流最终通过 `deep-dive-summary.md` 向主工作流回注结论。主工作流应至少消费以下信息：

- `Primary Root Cause`
- `Contributing Factors`
- `Top Evidence`
- `Confidence`
- `Need Defensive Fix`
- `Need Human Review`
- `Recommended Attachments`

`functionality-deep-dive-rca.md` 作为专项完整 RCA 产物保留，用于审计和后续 Fix Design 深化。

## 7. 与主工作流边界

- 主工作流负责分诊、调用、回注和后续闭环。
- 本子工作流负责专项分析本体，不直接替代主工作流的 `fix-design`、`fix-impl`、`verification`。
- 若本子工作流未收敛，优先返回 `Need Human Review = true`，由主工作流决定转人工或回退处理。
