# 分析策略池与动态 Fan-out 协议

## 路由矩阵

| Complexity / Trigger | Fan-out Mode | 角色组合 | 目标 |
|----------------------|-------------|---------|------|
| `simple` 且证据单峰 | `simple-single` | 主 Agent 单视角 OVHSC | 低成本快速闭环 |
| `medium` 或轻度冲突 | `medium-challenge` | `investigator + challenger` | 保留反驳能力，避免默认重编排 |
| `complex` / 证据冲突 / P6 回流 / Critical challenge | `complex-arbitrated` | `2 investigators + challenger + arbiter` | 最大化质量上限 |

## 升级规则
- `simple-single` 下出现反事实失败、最终置信度过低或新证据冲突 -> 升级到 `medium-challenge`
- `medium-challenge` 下 `challenger` 出现 `Critical` 或仍无法收敛 -> 升级到 `complex-arbitrated`
- `P6` 因 `root_cause_not_closed` 回流 `P3` -> 直接强制 `complex-arbitrated`

## 边界策略（第一层路由）
- `Strategy-DiffFocus`：适用 `EXACT_MR`，聚焦 MR / PR / Diff 与 blame
- `Strategy-CommitDenoise`：适用 `VERSION_RANGE`，先做区间变更降噪再分析
- `Strategy-DynamicBottomUp`：适用 `HISTORICAL_UNCLEAR`，从锚点自底向上回溯

## `simple-single` 建议打法
- 只保留一条主假设链，必须做反事实校验
- 优先消费 A 级证据与 Spec 中已确定的行为约束
- 不得因为“可能还存在别的解释”而直接进入多 Agent；必须给出升级触发证据

## `medium-challenge` 建议打法
- Investigator 选择 1 个主策略 + 1 个边界策略
- Challenger 仅执行 `rca-5d` 维度集；必要时加条件维度
- 若 Challenger 只给出 Minor / Major，允许在当前层级闭环

## `complex-arbitrated` 建议打法
- Investigator-A：采用 1 个边界策略 + 1 个分类策略
- Investigator-B：必须与 A 形成独立切入角度，避免假收敛
- Challenger：覆盖所有候选结论
- Arbiter：执行共享裁定协议并统一 `final_confidence`

## 分类策略建议

### 功能类
- `Strategy-DataFlow`
- `Strategy-StateMachine`
- `Strategy-BizRule`

### 稳定性 / 性能类
- `Strategy-StackTrace`
- `Strategy-Platform`
- `Strategy-Regression`

### UI / UX 类
- `Strategy-LayoutTree`
- `Strategy-ResourceChain`
- `Strategy-RenderTiming`
- 布局/渲染/交互时序问题在主 RCA 内完成分析，不再切换到独立 UI 专项子工作流

### 网络类
- `Strategy-RequestChain`
- `Strategy-ContractDiff`
- `Strategy-EnvironmentDiff`

### 兼容性类
- `Strategy-DeviceDiff`
- `Strategy-APISurface`
- `Strategy-SDKInteraction`
