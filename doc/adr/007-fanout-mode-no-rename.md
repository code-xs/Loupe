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

---

## v4.2 PR-2 修订（2026-04-21）

**修订背景**：V1.1 §3.2.7 / §3.2.8 识别出 `rca_fanout_mode_snapshot` 与 `fix_strategy_mode` 是冗余字段：
- `rca_fanout_mode_snapshot`：方案 A（`phase_history` 反查）已是主路径，snapshot 字段是 C10 兼容性方案 B 兜底；PR-1 / PR-4 P3 写入端落地后 `phase_history` 永远非空，snapshot 是纯冗余。
- `fix_strategy_mode`：与 `fix_fanout_mode` 同义（P4 step 2 内 `fix_fanout_mode = {fix_strategy_mode}` 同值赋两次）。

**修订决定**：
- **删除** `rca_fanout_mode_snapshot` schema 字段；P3 重入还原仅依赖 `phase_history` 反查。
- **合并** `fix_strategy_mode` → `fix_fanout_mode`（保留 `fix_fanout_mode` 命名，与 `fanout_mode` 命名对称）。
- **保留** D7 原决定不变：`fanout_mode` 字段名继续作 RCA 字段，**不重命名**为 `rca_fanout_mode`；DoD 反向校验"裸 `rca_fanout_mode` 必须打回"继续生效。
- **同步落地 P3 重入读端**（v1.1 review Blocking 1 修订 / O7 方案 B / v1.2 落点修订）：在 `phases/p3-root-cause.md` step 4 第一个边界策略动作之前追加"若 `fanout_mode` 缺失/null 则反查 `phase_history` 末项 `qa-root-cause` 元素的 `fanout_mode` 还原"逻辑，并在 `core/workflow.xml` **step 2** 读字段列表追加 `phase_history`（编排器层显式声明，方便 Limited 平台 prompt 注入器同步注入）；snapshot 字段删除后由本读端独立支撑 P3 重入兼容（旧 C10 兼容性方案 B 不再需要）。

**存量兼容**：v4.2 PR-2 同步交付 `migrate-workflow-status-v3-to-v4.py --cleanup-v4-deprecated` 子命令，幂等地拷值 + 删除两个废弃字段；同时迁移脚本文件头 docstring 删除"不实施 fanout_mode 反查还原逻辑"一句（该断言被 v4.2 PR-2 的 P3 step 4 反查读端取代）。

**关联 PR**：v4.2 PR-2（落地）；后续 PR-3/4/5/6/7 不再涉及这两个字段。
