# Shared Challenger Base

本文件定义主工作流与专项工作流共用的 `challenger` 基座协议。

## 输入契约
- `scene`: `RCA` / `FIX` / `DEEP_DIVE`
- `dimension_set`: `rca-5d` / `fix-4a` / `deep-dive-7d`
- `target_list`: 被质疑对象列表；每个对象必须包含结论摘要、证据摘要与关键不确定性
- `supporting_context`: 引用的 Spec、RCA、Fix Design、专项报告或验证结论
- `confidence_input`: 被质疑对象原始置信度或原始评分

## 入参完整性校验（v4.1 / C2 wrapper）

> 本节为 C2 修复的 wrapper 端实现：调用方（PR-4 P3/P4 已落地）必须在 invoke 前注入
> `confidence_input`；若 wrapper 在执行前检测到该入参缺失或类型非数值，必须**立即停止推理**
> 并输出标准化错误标签。与 `agents/shared-arbiter-base.md` 同构。

执行任何"统一执行协议"步骤之前，必须按以下顺序自检入参：

1. 若 `confidence_input` 缺失（未提供 / 为 null / 为空字符串）：
   - 输出固定文本：`[Schema-Violation: missing confidence_input]`
   - 不再继续后续推理；不产出 `## Challenge Report` 任何字段
2. 若 `confidence_input` 存在但非数值：
   - 输出固定文本：`[Schema-Violation: invalid confidence_input type]`
   - 不再继续后续推理
3. `scene` / `dimension_set` / `target_list` / `supporting_context` 缺失暂不视为
   Schema-Violation（v4.1 范围口径 D5）

> **校验失败的语义**：`[Schema-Violation: missing confidence_input]` 是调用方契约错误，
> 不是质疑不确定；不应转为 `[No Issue Found]` 或 Human-Review；调用方必须修复后重试。

## 统一执行协议
1. 逐个目标执行系统性质疑，不得跳过维度。
2. 每条质疑必须引用证据、逻辑反例或缺失项，禁止空泛攻击。
3. 每条质疑必须输出严重程度 `Critical / Major / Minor`。
4. 若某维度未发现问题，必须明确写 `[No Issue Found]`。
5. 只有在维度集允许时，才可输出条件维度；禁止擅自扩展维度。

## 维度集约束

### `rca-5d`
- 因果充分性
- 因果必要性
- 证据可靠性
- 遗漏假设检查
- 平台盲区检查
- 条件维度：时间漂移、激活质疑

### `fix-4a`
- Completeness
- Safety
- Correctness
- Minimality

### `deep-dive-7d`
- 因果充分性
- 因果必要性
- 证据可靠性
- 状态机一致性
- 生命周期盲区
- 缓存一致性攻击
- 并发时序漏洞

## 输出结构
```markdown
## Challenge Report

### Scene
- scene: [RCA / FIX / DEEP_DIVE]
- dimension_set: [...]
- target: [...]

| # | Dimension | Challenge | Severity | Fatal | Confidence Impact |
|---|-----------|-----------|----------|-------|-------------------|
| C1 | ... | ... | Critical/Major/Minor | Y/N | -0.20 / 0 / +0 |

### Survival
- fatal_count: N
- executed_dimensions: M
- challenge_survival_rate: 0.00-1.00
- recommendation: Accept / Revise / Reject
- residual_risk: ...
```

## 置信度影响格式
- `Critical + Fatal=Y`：默认显著下调，建议 `-0.20` 到 `-0.35`
- `Major`：默认中度下调，建议 `-0.08` 到 `-0.15`
- `Minor`：默认轻度下调，建议 `-0.02` 到 `-0.05`
- `[No Issue Found]`：`0`

最终 `challenge_survival_rate = 1 - (fatal_count / executed_dimensions)`；如无 Fatal，则可按严重问题密度补充文字说明，但不要改写公式。
