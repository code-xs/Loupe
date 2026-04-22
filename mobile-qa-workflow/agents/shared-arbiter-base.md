# Shared Arbiter Base

本文件定义主工作流与专项工作流共用的 `arbiter` 裁定协议。

## 输入契约
- `scene`: `RCA` / `FIX` / `DEEP_DIVE`
- `candidate_set`: Investigator、Fix-Proposer、专项分析角色的候选结论集合
- `challenge_reports`: Challenger 或专项挑战结果
- `comparison_focus`: 本次裁定的关键对比维度
- `base_score`: 候选结论基础评分或原始置信度

## 入参完整性校验（v4.2 PR-7 / O19+ / shared-input-guard）

> v4.2 PR-7 / O19+ / §3.6：本段从原 v4.1 / C2 wrapper 文本抽取至
> [`agents/shared-input-guard.md`](./shared-input-guard.md)，与
> `shared-challenger-base.md` 通过单一参数 `required_field` 同源复用，避免双写漂移。
>
> **本 wrapper 写死 `required_field = base_score`**（候选结论基础评分或原始置信度）。
> 除 `base_score` 外的其它入参缺失（`scene` / `candidate_set` / `challenge_reports` /
> `comparison_focus`）按 v4.1 范围口径 D5 暂**不**视为 Schema-Violation。

<load target="mobile-qa-workflow/agents/shared-input-guard.md" prompt="加载 wrapper 入参完整性校验通用契约（required_field=base_score）"/>

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
