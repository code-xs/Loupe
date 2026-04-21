# ADR Index — Mobile QA Workflow

> **目录用途**：本目录承载 Mobile QA Workflow 的 Architecture Decision Records (ADR)，每个 ADR 对应一项已拍板的关键设计决定（D1-D21）。
> **首批落地**：v4.2 PR-1（2026-04-21），按 V1.1 §3.1 O4+ Step 2 + 主控 §3 H4 强约束（ADR 必须先于代码 PR 落地）。
> **维护规则**：新增 ADR → 在本索引登记一行；状态切换（active → superseded）→ 同步本索引。

## ADR 列表

| 编号 | 标题 | 状态 | 关联决定 | 落地 PR |
|---|---|---|---|---|
| [ADR-001](./001-current-phase-result-runtime-only.md) | `current_phase_result` 设计为运行时变量（方案 A） | active | D1 | v4.1 PR-2（已合入） |
| [ADR-002](./002-step-pause-input-protocol.md) | `<step-pause>` 必备 `<input-protocol>` 子标签 | active | D2 | v4.1 PR-1（已合入） |
| [ADR-003](./003-tag-whitelist-boundary.md) | DSL 标签白名单边界（仅约束 `<flow>`/`<task>` 内部） | active | D3 | v4.1 PR-1（已合入） |
| [ADR-004](./004-audit-scope-double-layer.md) | 审计范围口径双层化 | active | D4 | v1.2.1 报告（已合入） |
| [ADR-005](./005-pr-tier-tagging.md) | PR 层级标签（🟢 / 🟡 / 🔴） | active | D5 | v4.1 PR-1（已合入） |
| [ADR-006](./006-deep-dive-keyname-deferral.md) | Deep-Dive 键名映射延后 | active | D6 | v4.1 不动，v4.3 评估 |
| [ADR-007](./007-fanout-mode-no-rename.md) | 保留 `fanout_mode` 不重命名 + 新增 `fix_fanout_mode` | active | D7 | v4.1 PR-1（已合入）+ v4.2 PR-2 修订 |
| [ADR-008](./008-step-pause-userinputs-namespace.md) | `step-pause` 写入 `user_inputs.*` 命名空间 + 顶层镜像双写 | active | D8 | v4.1 PR-2（已合入） |
| [ADR-009](./009-merge-order-constraint.md) | v4.1 PR 合入顺序 = PR-4 → PR-3 → PR-5 | active | D9 | v4.1 PR-1（已合入） |
| [ADR-010](./010-step-pause-registry-data-driven.md) | step-pause registry 数据驱动 | **draft** | D10 + V1.1 O10+ Stage-1 | **v4.2 PR-5（落地依赖）** |
| [ADR-011](./011-ci-entry-point.md) | CI 起点 = `.github/workflows/qa-workflow-schema-check.yml` | active | D11 | v4.1 PR-8（已合入） |
| [ADR-012](./012-install-trae-shim.md) | `install_trae.sh` 改为 shim 调用 | active | D12 | v4.1 PR-7（已合入） |
| [ADR-013](./013-migrate-script-path.md) | 迁移脚本路径锁定 `mobile-qa-workflow/scripts/migrate-workflow-status-v3-to-v4.py` | active | D13 | v4.1 PR-1（已合入） |
| [ADR-014](./014-step-pause-scope-restriction.md) | `<step-pause>` 调度作用域限定（仅编排器 step 4） | active | D14 | v4.1 PR-1 + PR-2（已合入） |
| [ADR-015](./015-userinputs-mirror-allowlist.md) | `user_inputs` 顶层镜像白名单受限双写 | active | D15 | v4.1 PR-1 + PR-2（已合入） |
| [ADR-016](./016-step-pause-required-params.md) | `<step-pause>` 必填参数表（`title` / `result_field` / `allowed_values`） | active | D16 | v4.1 PR-1（已合入） |
| [ADR-017](./017-non-bug-context-persistence.md) | `non_bug_context` 字段入 schema 持久化 | active | D17 | v4.1 PR-1（已合入） |
| [ADR-018](./018-parse-error-circuit-breaker.md) | `parse_error_count` 持久化 + 4 类生命周期动作 | active | D18 | v4.1 PR-1 + PR-2（已合入） |
| [ADR-019](./019-legacy-step-pause-allowlist.md) | legacy phase `<step-pause>` allowlist 实体化交付 | active | D19 | v4.1 PR-5 + PR-8（已合入） |
| [ADR-020](./020-v43-long-term-evolution.md) | v4.3 长期演进规划占位 | superseded-by-v4.3-plan | D20 | v4.3 立项启动 |
| [ADR-021](./021-phase-abort-macro-tags.md) | `<phase-abort>` / `<phase-complete>` 宏标签 | **draft** | V1.1 O21 | **v4.2 PR-3（落地依赖）** |

## 引用规范

- **代码内短引用**：`<!-- ADR-NNN -->`（XML 注释）/ `# ADR-NNN`（YAML 注释）单行引用
- **文档内长引用**：使用 markdown 链接 `[ADR-NNN](../doc/adr/NNN-slug.md)`，根据相对位置调整路径
- **状态变更**：active → superseded 时，必须在本索引同步 + 在 ADR 文件头部标注"被 ADR-XXX 取代"

## v1.1 修订摘要锚点

- 主控方案：[`doc/MOBILE_QA_WORKFLOW_STATE_SYNC_OPTIMIZATION_V1.1_2026-04-21.md`](../MOBILE_QA_WORKFLOW_STATE_SYNC_OPTIMIZATION_V1.1_2026-04-21.md)
- v4.2 README：[`mobile-qa-workflow/construction-plans/v4.2/README.md`](../../mobile-qa-workflow/construction-plans/v4.2/README.md)
- PR-1 施工单：[`mobile-qa-workflow/construction-plans/v4.2/pr-1-foundation-cleanup-and-ci-bootstrap-v1.1.md`](../../mobile-qa-workflow/construction-plans/v4.2/pr-1-foundation-cleanup-and-ci-bootstrap-v1.1.md)
