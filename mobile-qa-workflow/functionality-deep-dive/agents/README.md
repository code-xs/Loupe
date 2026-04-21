# Functionality Deep-Dive Agents

## 当前复合角色
- `deep-dive-context-analyst.md`: 环境与上下文重构，吸收部分输入预处理能力
- `deep-dive-structure-analyst.md`: 状态机与数据流拓扑分析，含轻量时序预扫描
- `deep-dive-race-and-isolation-analyst.md`: 竞态、时序窗口、控制变量推演与候选根因排序
- `deep-dive-arbiter.md`: 吸收专项 challenger + arbiter，负责七维质疑与最终裁定
- `defensive-fix-architect.md`: 防御性修复附录，按需触发

## 已退役（仅 v3-legacy 会话恢复 / v4.2 PR-1 落地）

以下 5 个 agent 在 v4 之后**新会话不再使用**，物理文件已归档至 `archive/v3-legacy/`：

- `context-reconstructor.md`
- `state-analyst.md`
- `temporal-analyst.md`
- `challenger.md`（**v1.1 新增到清单** — deep-dive 子目录下，**不影响**主流程 `mobile-qa-workflow/agents/challenger.md`；当前为 Legacy Wrapper 薄文件）
- `arbiter.md`（**v1.1 新增到清单** — deep-dive 子目录下，**不影响**主流程 `mobile-qa-workflow/agents/arbiter.md`；当前为 Legacy Wrapper 薄文件）

**退役原因**：deep-dive 子工作流 v4 已收敛为本目录其余 5 个新 agent（详见 README 上半段 + `core/workflow.xml`）。

**v4.3 物理删除前提**（来自 V1.1 §3.1 O3）：
1. 所有持久化会话的 `schema_version ≥ 4`（CI 守门：`check-state-enum.sh` 兜底）
2. 90 天内零 v3-legacy 流量（按 `workflow_version=v3-legacy` 与 `legacy_flow_mode=true` 标记的会话计数为 0；**注意**：主流程 `core/workflow.xml` 的 v3 兼容默认值是 `workflow_version = legacy`，与 deep-dive 的 `v3-legacy` 是不同字符串值，统计时需双侧累加；详见本 PR §6 议题 H2）
3. 主流程与 deep-dive 子流程均无 `<load target="archive/v3-legacy/...">` 残留引用（grep 验证）

**当前状态**（v4.2 PR-1 落地）：
- 物理文件位置：`functionality-deep-dive/agents/archive/v3-legacy/` 下 5 个 .md
- DSL 声明位置：主流程 `core/core-rules.xml` L92-96，5 个 `<agent name=... scenario="兼容旧会话">` 元素，文本内容已升级为"已退役（v3-legacy 会话恢复专用 / 详见 ADR-019）；新会话禁用"
- 物理删除推迟到 v4.3 立项
