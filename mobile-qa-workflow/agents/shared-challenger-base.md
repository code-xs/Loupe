# Shared Challenger Base

本文件定义主工作流与专项工作流共用的 `challenger` 基座协议。

## 输入契约
- `scene`: `RCA` / `FIX` / `DEEP_DIVE`
- `dimension_set`: `rca-5d` / `fix-4a` / `deep-dive-7d`
- `target_list`: 被质疑对象列表；每个对象必须包含结论摘要、证据摘要与关键不确定性
- `supporting_context`: 引用的 Spec、RCA、Fix Design、专项报告或验证结论
- `confidence_input`: 被质疑对象原始置信度或原始评分

## 入参完整性校验（v4.2 PR-7 / O19+ / shared-input-guard）

> v4.2 PR-7 / O19+ / §3.6：本段从原 v4.1 / C2 wrapper 文本抽取至
> [`agents/shared-input-guard.md`](./shared-input-guard.md)，与
> `shared-arbiter-base.md` 通过单一参数 `required_field` 同源复用，避免双写漂移。
>
> **本 wrapper 写死 `required_field = confidence_input`**（被质疑对象原始置信度，
> OVHSC SCORE 步产物）。除 `confidence_input` 外的其它入参缺失（`scene` /
> `dimension_set` / `target_list` / `supporting_context`）按 v4.1 范围口径 D5
> 暂**不**视为 Schema-Violation。

<load target="mobile-qa-workflow/agents/shared-input-guard.md" prompt="加载 wrapper 入参完整性校验通用契约（required_field=confidence_input）"/>

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
