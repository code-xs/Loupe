# Functionality Deep-Dive Reference Knowledge Base

本目录包含功能疑难专项子工作流的参考知识文件，供各阶段 Agent 加载使用。

## 文件清单

| 文件 | 用途 | 使用阶段 |
|------|------|---------|
| `environment-factor-thresholds.md` | 环境因子异常阈值基准（内存/温控/网络/磁盘/生命周期） | F1 - Context Reconstruction |
| `state-machine-patterns.md` | 状态机常见缺陷模式（孤岛状态/非法跳转/守卫缺失/竞态更新/脏写等） | F2 - State Topology |
| `race-condition-patterns.md` | 竞态条件常见模式（CTA/RMW/回调交错/生命周期竞态/事件丢失等） | F3 - Temporal Correlation |
| `isolation-patterns.md` | 隔离诊断方法论（Mock/断网/缓存/状态/逻辑/时序隔离） | F4 - Isolation & Debate |

## 使用方式

各阶段 Phase 文件通过 `<load>` 标签加载对应参考文件：

```xml
<load target="mobile-qa-workflow/functionality-deep-dive/reference/environment-factor-thresholds.md" prompt="加载环境因子阈值参考"/>
```

Agent 在分析过程中应对照参考文件中的模式/阈值进行排查，并在结论中引用具体模式编号。
