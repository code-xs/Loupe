# Functionality Deep-Dive Agents

## 当前复合角色
- `deep-dive-context-analyst.md`: 环境与上下文重构，吸收部分输入预处理能力
- `deep-dive-structure-analyst.md`: 状态机与数据流拓扑分析，含轻量时序预扫描
- `deep-dive-race-and-isolation-analyst.md`: 竞态、时序窗口、控制变量推演与候选根因排序
- `deep-dive-arbiter.md`: 吸收专项 challenger + arbiter，负责七维质疑与最终裁定
- `defensive-fix-architect.md`: 防御性修复附录，按需触发

## 已废弃但保留兼容
- `context-reconstructor.md`
- `state-analyst.md`
- `temporal-analyst.md`
- `challenger.md`
- `arbiter.md`

这些旧文件仅供历史会话恢复，新的阶段编排不再直接调用。
