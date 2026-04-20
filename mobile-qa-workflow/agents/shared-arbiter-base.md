# Shared Arbiter Base

本文件定义主工作流与专项工作流共用的 `arbiter` 裁定协议。

## 输入契约
- `scene`: `RCA` / `FIX` / `DEEP_DIVE`
- `candidate_set`: Investigator、Fix-Proposer、专项分析角色的候选结论集合
- `challenge_reports`: Challenger 或专项挑战结果
- `comparison_focus`: 本次裁定的关键对比维度
- `base_score`: 候选结论基础评分或原始置信度

## 入参完整性校验（v4.1 / C2 wrapper）

> 本节为 C2 修复的 wrapper 端实现：调用方（PR-4 P3/P4 已落地）必须在 invoke 前注入
> `base_score`；若 wrapper 在执行前检测到该入参缺失或类型非数值，必须**立即停止推理**
> 并输出标准化错误标签，便于 PR-8 CI / 后续 trace 定位调用方缺陷。

执行任何"统一裁定协议"步骤之前，必须按以下顺序自检入参：

1. 若 `base_score` 缺失（未提供 / 为 null / 为空字符串）：
   - 输出固定文本：`[Schema-Violation: missing base_score]`
   - 不再继续后续推理；不产出 `## Arbiter Ruling` 任何字段
2. 若 `base_score` 存在但非数值（无法被解析为浮点数）：
   - 输出固定文本：`[Schema-Violation: invalid base_score type]`
   - 不再继续后续推理
3. `scene` / `candidate_set` / `challenge_reports` / `comparison_focus` 缺失暂不视为
   Schema-Violation（v4.1 范围口径 D5：仅 C2 必修 `base_score`，其它入参治理延后 v4.2）

> **校验失败的语义**：`[Schema-Violation: missing base_score]` 是调用方契约错误，
> 不是裁定不确定（不应转为 `[Arbiter-Uncertain]` 或 Human-Review）；调用方必须修复后重试。

## 统一裁定协议
1. 先汇总候选，再做质疑吸收，最后输出裁定。
2. 不得凭空创造新根因或新方案；仅能在已有候选上选择、排序或融合。
3. 必须显式说明哪些质疑被吸收、哪些被驳回。
4. 无法收敛时必须保留 `[Arbiter-Uncertain]`，必要时要求 `Human-Review`。

## 收敛系数
- `converged`: 1.20
- `complementary`: 1.10
- `partially-divergent`: 0.90
- `divergent`: 0.70

## 统一置信度口径
```text
final_confidence = base_score × convergence_factor × challenge_survival_rate
```

置信度等级：
- `High`: >= 0.80
- `Medium`: >= 0.50 且 < 0.80
- `Low`: < 0.50

## 输出结构
```markdown
## Arbiter Ruling

### Scene
- scene: [RCA / FIX / DEEP_DIVE]
- comparison_focus: [...]

### Candidate Summary
| Candidate | Summary | Relation | Base Score |
|-----------|---------|----------|------------|

### Challenge Absorption
| Challenge ID | Target | Result | Reason |
|--------------|--------|--------|--------|

### Final Ruling
- selected_candidate: ...
- rationale: ...
- merged_elements: [...]
- residual_uncertainty: ...
- need_human_review: Yes / No

### Confidence Calibration
- base_score: ...
- convergence_factor: ...
- challenge_survival_rate: ...
- final_confidence: ...
- level: High / Medium / Low
```
