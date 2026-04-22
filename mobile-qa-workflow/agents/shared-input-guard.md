# Shared Input Guard

> v4.2 PR-7 / O19+ / §3.6：本文件抽取自 `shared-challenger-base.md` 与
> `shared-arbiter-base.md` 中**字面同构**的「入参完整性校验」段（v4.1 / C2 wrapper），
> 通过 `{required_field}` 单一参数复用。两份 wrapper 改为 `<load shared-input-guard.md/>`
> + 一行「本 wrapper required_field = X」preamble，再执行各自统一执行/裁定协议。
>
> **写死 required_field 取值清单（由 wrapper 各自声明，禁止扩展）**：
>
> | wrapper | required_field | 数值语义 |
> |---|---|---|
> | `agents/shared-challenger-base.md` | `confidence_input` | 被质疑对象原始置信度（OVHSC SCORE 步产物）|
> | `agents/shared-arbiter-base.md` | `base_score` | 候选结论基础评分或原始置信度 |
>
> CI（既存 `check-subagent-params.sh` 已对调用方做注入校验；本文件对被调方 wrapper 端做防御）。

## 校验前置条件

执行任何「统一执行协议」/「统一裁定协议」步骤之前，wrapper 必须按以下顺序自检入参 `{required_field}`：

1. 若 `{required_field}` **缺失**（未提供 / 为 null / 为空字符串）：
   - 输出固定文本：`[Schema-Violation: missing {required_field}]`
   - **立即停止推理**；不产出任何下游报告字段（`## Challenge Report` / `## Arbiter Ruling` 等）
2. 若 `{required_field}` 存在但**非数值**（无法被解析为浮点数）：
   - 输出固定文本：`[Schema-Violation: invalid {required_field} type]`
   - **立即停止推理**
3. 其它入参（`scene` / `dimension_set` / `target_list` / `supporting_context` / `candidate_set` /
   `challenge_reports` / `comparison_focus` 等）缺失暂**不**视为 Schema-Violation
   （v4.1 范围口径 D5：仅 C2 必修核心数值字段；其它入参治理后续 PR 再迭代）

## 失败语义

> `[Schema-Violation: missing {required_field}]` 是**调用方契约错误**，**不是**业务不确定：
>
> - **不应**转为 `[No Issue Found]`（challenger）或 `[Arbiter-Uncertain]`（arbiter）
> - **不应**转为 Human-Review（不触发 `human-review-protocol`）
> - 调用方（PR-4 P3/P4 已落地的 invoke-subagent / 内联 Limited 段）必须修复入参后**重试**
> - 便于后续 CI / trace 定位调用方缺陷

## 与上游既存检查的关系

- **调用方端**：`scripts/check-subagent-params.sh`（既存）扫描所有 invoke-subagent 内 prompt
  是否包含必填字段注入；本文件不重复该层。
- **被调方端**：本文件即 wrapper 端校验的唯一规范；两份 wrapper 在 invoke 实际进入推理前
  优先执行本节，校验通过后才进入各自的统一执行/裁定协议。
- **生效范围**：仅 Full 平台（`env_subagent=true`）的 invoke-subagent 子对话；Limited 平台
  内联段由 `build-system-prompt.py` 在拼装 system-prompt.md 时复用同一文本（GEN-PR7 §4 第 3 条）。
