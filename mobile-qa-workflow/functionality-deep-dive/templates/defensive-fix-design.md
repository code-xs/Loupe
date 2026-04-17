# 防御性修复设计模板

```markdown
## Defensive Fix Design — {Issue-ID}

### 关联信息
- **专项 RCA 报告**: [functionality-deep-dive-rca.md]
- **专项置信度**: [0.XX] ([High/Medium/Low])
- **主 RCA 置信度**: [0.XX]

### 修复策略概述
- **主要防御目标**: [状态机加固 / 竞态收敛 / 生命周期感知 / 缓存一致性]
- **修复范围级别**: [stop-gap (止血) / hardening (加固) / architectural (架构演进)]

### 拓扑变更（前后对比）

#### Before
- 状态转移: [A -> B -> C，缺少 guard 在 B -> C]
- 已知缺陷: [Pattern-X: ...]

#### After
- 状态转移: [A -> B -[guard]-> C]
- 新增守卫: [guard 条件描述]

### 守卫 / 断言 / 降级策略

| 位置 | 类型 | 条件 | 失败时策略 |
|------|------|------|----------|
| [Class.method] | Guard | [前置条件] | [拒绝转移 + 日志] |
| [Class.method] | Assertion | [不变量] | [Debug 崩溃 / Release 降级] |
| [Class.method] | Fallback | [异常状态] | [回退到安全状态] |

### 生命周期感知处理
- **订阅管理**: [订阅/取消的对称性修复]
- **任务取消**: [CoroutineScope / DisposeBag 绑定]
- **恢复处理**: [savedInstanceState / 状态恢复路径修复]

### 竞态收敛措施
- **锁/同步策略**: [具体保护措施]
- **原子操作**: [AtomicXxx / volatile 使用]
- **熔断器**: [超时 / 重试上限 / 降级条件]

### 适度性评审
- **为什么不能更小**: [...]
- **过度设计风险**: [评估]
- **与主修复方案的关系**: [补充 / 替代 / 独立]

### 渐进式落地路径
- **Phase 1 (止血)**: [与主修复一同上线的最小防御措施]
- **Phase 2 (加固)**: [下一版本跟进的加固措施]
- **Phase 3 (演进)**: [中长期的架构级防御优化]
```
