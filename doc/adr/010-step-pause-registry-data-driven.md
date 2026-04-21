# ADR-010: `step-pause-registry.yaml` 数据驱动方案

> **状态**：**active**（v4.2 PR-5 已落地 / 2026-04-21 / 详见文末「PR-5 落地纪要」）
> **关联决定**：D10（v2.0 附录 B 占位）+ V1.1 O10+ Stage-1 + Stage-2 + Registry 权威性约束
> **关联 PR**：**v4.2 PR-5（已交付）**

> **历史**：PR-1 落地为 `draft`（H4 前置依赖占位），PR-5 实际交付时同步切换为 `active`，并在文末追加「PR-5 落地纪要」（6 项 finalize 信息）。

## 1. 背景

v4.1 的 6 个 `<step-pause>` 在编排器 step 4 case 中以"硬编码 case 分支"形式存在，每个 case 重复 `title` / `result_field` / `allowed_values` / `option` 等 5 步配置。维护成本高 + 新增 step-pause 需要改编排器 XML。

## 2. 决定（草稿，PR-5 实施时 finalize）

引入 `core/step-pause-registry.yaml` 作为**数据驱动**的 step-pause 配置中心：
- 所有 step-pause 配置集中在 registry，按 `current_state` 索引
- 编排器 step 4 case 退化为通用模板：`<step-pause registry-key="${current_state}" />`，运行时按 key 查 registry 展开
- registry 单一权威源；CI `check-step-pause-registry.sh`（PR-5 启用 error）守门 registry 与编排器一致性

## 3. 替代方案

- **方案 X**（继续硬编码）：被拒绝。理由：① 维护成本随 step-pause 数量线性增加；② 新增配置需要 XML 编辑；③ 阻碍未来生成器化。

## 4. 影响

- **协议层**：`core/core-rules.xml` `<step-pause>` 标签定义新增 `registry-key` 属性
- **编排器**：`core/workflow.xml` step 4 case 由 6 处硬编码退化为 1 处通用模板
- **CI**：`check-step-pause-registry.sh`（PR-5 启用）守门 registry 完整性
- **跨平台**：Limited / Minimal 平台需要 registry 同步注入到 system-prompt（PR-6 build-system-prompt.py 处理）

## 5. 引用

- V1.1 §3.2.10+ Stage-1（O10+ 拆分）
- v2.2 主文档 §6 D10（占位）
- v4.2 README §6 PR-5（实际落地）
- ADR-016（`<step-pause>` 必填参数表 / registry 元素 schema 复用）

---

## 6. PR-5 落地纪要（2026-04-21 / v4.2 PR-5 v1.1 / draft → active）

本节为 PR-5 finalize 信息，6 项与施工单 §1 / §2 锚点对齐：

### 6.1 Registry 文件路径

- `mobile-qa-workflow/core/step-pause-registry.yaml`（C5 单一权威源）
- 顶部含 27 行 schema 注释块（含 `kind` / `step-pause` / `route` 形态描述 + 7 种 action_block 原子动作枚举）

### 6.2 Registry 7 项 state 字面（与编排器 step 4 case 1:1 等价）

| state | kind | result_field | allowed_values | mirror_to_top |
|---|---|---|---|---|
| `Info-Insufficient` | `step-pause` | `info_insufficient_action` | `[Submit]` | — |
| `Spec-Uncertain` | `step-pause` | `spec_uncertain_choice` | `["1", "2", "S"]` | — |
| `Non-Bug` | `step-pause` | `non_bug_user_choice` | `[Accept, Reflow]` | **true** |
| `RCA-LowConfidence` | `step-pause` | `rca_lowconf_action` | `[Retry, Human]` | — |
| `Curation-Failed` | `step-pause` | `curation_failed_action` | `[Retry, Human]` | — |
| `Human-Review` | `step-pause` | `human_review_continue` | `[Continue]` | — |
| `Boundary-Refined` | `route` | — | — | — |

### 6.3 编排器 4a / 4b / 4c 行号区间（`core/workflow.xml`）

- step 4a：L110~L143（step-pause 用户回复解析 + 受限双写 + 熔断）
- step 4b：L145~L156（阶段完成态判定 + 重试熔断）
- step 4c：L158~L200（状态路由 / 按 `kind` 派发：`step-pause` / `route` 两分支 + 流转态默认 `<goto step="2"/>`）
- 净瘦身：v4.1 单 step 4 的 ~270 行 → 4a/4b/4c 三段 ~90 行（数据 + 逻辑分离收益）

### 6.4 CI Check 16 严重度

- 脚本：`mobile-qa-workflow/scripts/check-step-pause-registry.sh`
- 严重度：**error 起步**（无 warning 过渡，主控 §4 / V1.1 §3.2.22 加严落实）
- 三类校验：① state 合法性（∈ workflow-status-template.yaml enum 集）/ ② **双向严格相等**（`EXPECTED ↔ REGISTRY`，分类报 missing / unexpected）/ ③ step 4a/4b/4c 区间内零硬编码 case（黑名单含 `Boundary-Refined` + `Fix-Confirming` 前向兼容）
- 集成位置：`.github/workflows/qa-workflow-schema-check.yml` 追加为 Check 16（CI-N1）

### 6.5 跨平台抽查结果摘要

- Cursor / Claude Code（Full）：6 个交互态弹窗 title / 选项字面与 PR-3' 后版本 100% 一致（registry 数据化 1:1 迁移）
- Dify（Limited）：本 PR 范围内 system-prompt 仍含 PR-3' 后字面（与 registry 同源，PR-6 sp 首次构建后自动一致）
- 单 prompt LLM（Minimal）：`<step-pause registry-key="${current_state}"/>` 配合 `core-rules.xml` `<forms>` 块协议层声明 + ADR-010 §0 展开规则双锚点，0 漏展开

### 6.6 与下游 PR 衔接事项（4 条）

1. **PR-6 / O13 + O14**（依赖本 PR）：删除 6 个 phase 文件内联 `<step-pause>`（受 `legacy-phase-step-pause-allowlist.txt` 兜底）+ 引入 `Fix-Confirming` 交互态 enum + 同步把 `Fix-Confirming` 加入本 registry（黑名单已前向兼容，仅需扩 `EXPECTED` + Check 16 ③ 类黑名单各 1 行） + 删除 `legacy-phase-step-pause-allowlist.txt`。
2. **PR-6 / O17+**（H1 触发）：build-system-prompt.py 把 registry 注入 system-prompt L1 分层；Limited 平台首次包含 registry 字面与 Cursor 完全等价。
3. **PR-6 / 遗留 #3**：`workflow-status-template.yaml` 顶层 `non_bug_user_choice` 字段删除；编排器 4c 改读 `user_inputs.<key>`；本 registry 中 `Non-Bug` 项的 `mirror_to_top: true` 标记一并下线（届时 `mirror_to_top` 字段从 schema 注释中删除，registry 内零 `mirror_to_top` 出现）。
4. **PR-7 / O15 + O11+**：P3 三档升级路径合并 / agents 模块化；不影响本 registry 结构，仅可能新增 1~2 项 step-pause 条目（届时按 §6.2 表追加，并同步 Check 16 ② 类 `EXPECTED` 集合）。
