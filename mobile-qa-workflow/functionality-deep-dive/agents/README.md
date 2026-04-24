# Functionality Deep-Dive Agents

## 当前复合角色
- `deep-dive-context-analyst.md`: 环境与上下文重构，吸收部分输入预处理能力
- `deep-dive-structure-analyst.md`: 状态机与数据流拓扑分析，含轻量时序预扫描
- `deep-dive-race-and-isolation-analyst.md`: 竞态、时序窗口、控制变量推演与候选根因排序
- `deep-dive-arbiter.md`: 吸收专项 challenger + arbiter，负责七维质疑与最终裁定
- `defensive-fix-architect.md`: 防御性修复附录，按需触发

## 已退役（仅用于 v3-legacy 会话恢复）

以下 5 个 agent **新会话不再使用**，仅在恢复旧会话时可能被加载；物理文件已归档至 `archive/v3-legacy/`：

- `context-reconstructor.md`
- `state-analyst.md`
- `temporal-analyst.md`
- `challenger.md`（deep-dive 子目录下的 legacy wrapper，**不影响**主流程 `mobile-qa-workflow/agents/challenger.md`）
- `arbiter.md`（deep-dive 子目录下的 legacy wrapper，**不影响**主流程 `mobile-qa-workflow/agents/arbiter.md`）

**退役原因**：deep-dive 子工作流已收敛为上方“当前复合角色”的 5 个 agent；旧 agent 仅保留用于历史会话恢复。

**物理删除前提**（用于后续清理 legacy 文件时判定是否安全）：
1. 所有持久化会话的 `schema_version ≥ 4`（建议由 CI 守门）
2. 连续 90 天无 v3-legacy 恢复流量（统计应同时覆盖：
   - deep-dive：`workflow_version=v3-legacy` 且 `legacy_flow_mode=true`
   - 主流程：`workflow_version=legacy` 的兼容路径）
3. 主流程与 deep-dive 子流程均无 `<load target="archive/v3-legacy/...">` 残留引用（grep 验证）

**现状**：
- 物理文件位置：`functionality-deep-dive/agents/archive/v3-legacy/` 下 5 个 `.md`
- DSL 声明位置：主流程 `core/core-rules.xml` 中标注为“兼容旧会话”的对应 agent
