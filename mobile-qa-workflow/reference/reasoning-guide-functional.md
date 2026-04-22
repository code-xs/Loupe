# Reasoning Guide · 功能类问题

> v4.2 PR-7 / O24 / R24-1：本文件由 P3 step 5 按 issue_card 主分类「功能/功能*」命中加载，
> 与 [`reasoning-chain-core.md`](./reasoning-chain-core.md) 配套使用。
>
> **聚合契约（D-AGG-2）**：`<!-- AGG-INJECT-START -->` ~ `<!-- AGG-INJECT-END -->` 之间
> 的内容会被 `scripts/sync-reasoning-chain-aggregate.py` 注入到聚合产物
> `reference/reasoning-chain.md` 的「## 分类专项推理引导」章节内（注入顺序：
> functional → ui → network → compat）。区块外的内容仅供本文件作为独立加载入口阅读。

## 加载入口

主路径：`phases/p3-root-cause.md` step 5 起点 / invoke-subagent 内部
触发条件：`issue_card.主分类` 一级主题包含「功能」或「功能*」

<!-- AGG-INJECT-START -->
### 功能类问题

**OBSERVE 阶段重点**:
- 将"功能不正常"分解为具体的数据/状态偏差点
- 对照 Spec 中的 I/O Mapping，逐条标注哪些输出不符
- 对照状态转换图，定位状态偏离发生在哪个转换上
- 在数据流关键节点逐点检查，定位数据首次偏离的位置

**HYPOTHESIZE 阶段重点**:
- 优先考虑: 条件分支遗漏/边界值处理缺失/状态机跳转丢失/异步回调时序
- 必须检查: 服务端数据是否符合预期（排除前端接了脏数据的可能）
- 必须检查: Feature Flag / AB 实验配置是否影响了行为

**VERIFY 阶段重点**:
- 关键验证手段: 在数据流每个节点打桩检查数据是否符合预期
- 反事实: 如果假设成立，相同操作路径下不同输入是否也会异常？
- 边界: 改变输入为边界值，行为是否符合假设预测？
<!-- AGG-INJECT-END -->
