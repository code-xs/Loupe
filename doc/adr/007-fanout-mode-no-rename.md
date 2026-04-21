# ADR-007: 保留 `fanout_mode` 不重命名 + 新增 `fix_fanout_mode`

> **状态**：active
> **关联决定**：D7（v1.0 review 第 P0-1 项）
> **关联 PR**：v4.1 PR-1（已合入）

## 1. 背景

`rca_fanout_mode` 命名体系前后不一致：PR-1 schema 未定义、DoD/迁移脚本却引用。若按"统一改名为 `rca_fanout_mode`"会涉及 `core/workflow.xml` step 2 / 多个 phase / 迁移脚本同步调整。

## 2. 决定

**保留** 现有 `fanout_mode` 作为 RCA 字段（**不重命名**），仅做最小化扩展：
- `fanout_mode`：继续表示 RCA 阶段的 fanout 模式（语义不变）
- `fix_fanout_mode`：v4.1 新增（C10 + D7），承接 P4 的 `fix_strategy_mode/contested-arbitrated` 等取值（Fix 阶段隔离）
- `rca_fanout_mode_snapshot`：保留命名（语义清晰），P3 完成时 `fanout_mode` 的快照，用于 P3 重入时还原 RCA 上下文

## 3. 替代方案

- **方案 X**（统一改名 `rca_fanout_mode`）：被拒绝。理由：① 改动面大（core/workflow.xml step 2 / 多 phase / 迁移脚本）；② 老会话兼容代价高；③ 无新功能收益，纯命名洁癖。

## 4. 影响

- **协议层**：`core/workflow-status-template.yaml` 头部新增 `fix_fanout_mode: null` 字段 + 注释
- **编排器**：`core/workflow.xml` step 2 无任何修改（红利）
- **PR-1/PR-2 减少改动面**

## 5. 引用

- v2.2 主文档 §6 D7 拍板纪要（v1.0 review P0-1）
- `core/workflow-status-template.yaml` L33-37 字段定义 + 注释
