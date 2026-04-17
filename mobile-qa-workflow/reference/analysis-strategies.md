# 分析策略池与对抗协议

## 分析策略池

编排器根据问题边界分类和问题表现分类，选择 2-3 个策略分配给不同 Investigator。

### 边界驱动专项策略（第一层路由）

当启动 RCA 分析时，必须根据 `Issue_Boundary_Level` 采用对应的边界策略：

- **Strategy-DiffFocus** (适用 `EXACT_MR`):
  从明确的 MR Diff / PR / 提交哈希切入。将 Diff 覆盖代码标记为高优证据，结合 git blame 与时间窗口验证相似代码。若推导出的根因与 Diff 无关，必须合理解释 Diff 为何作为触发器暴露了该历史问题。
- **Strategy-CommitDenoise** (适用 `VERSION_RANGE`):
  版本区间降噪模式。从区间提取变更并构建多信号 Commit 排序（结构信号 30% > 动态信号 25% > 时序信号 20% > 文本信号 15% > 责任信号 10%）。形成“带分数和命中理由的候选排名”后再进行代码分析。
- **Strategy-DynamicBottomUp** (适用 `HISTORICAL_UNCLEAR`):
  受控搜索与自底向上回溯模式。禁止全局无锚点漫游，必须从 Error/Log/UI/埋点 中提炼原子锚点。每锚点限制搜集最多 5 个候选，过滤时必须要求候选能与调用栈映射或在当前 Flag 下激活。从现场证据自底向上恢复调用链，沉淀为 `runtime-call-path`。

### 通用策略（适用全部分类）

- **Strategy-Regression**: 从 git log/blame 出发，定位可疑变更，关注引入时间点
- **Strategy-Pattern**: 从知识库相似案例出发，模式匹配，关注已知问题模式

### 稳定性/性能专项策略

- **Strategy-StackTrace**: 从崩溃堆栈/异常点出发，逐帧溯源，关注直接代码缺陷
- **Strategy-Platform**: 从平台机制特性出发，检查生命周期/内存/线程模型违规

### 功能专项策略

- **Strategy-DataFlow**: 从数据流转路径出发，逐节点追踪数据变化
- **Strategy-StateMachine**: 从状态机模型出发，检查状态转换的完整性和正确性
- **Strategy-BizRule**: 从业务规则出发，逐条验证代码实现是否覆盖

### UI/UX 专项策略

- **Strategy-LayoutTree**: 从 View Hierarchy 出发，分析约束/布局参数的计算结果
- **Strategy-ResourceChain**: 从资源加载链出发，检查多密度/多尺寸/多主题资源是否正确
- **Strategy-RenderTiming**: 从渲染时序出发，检查异步数据加载后的布局刷新时机

### 网络专项策略

- **Strategy-RequestChain**: 从请求构造到响应处理的完整链路逐层排查
- **Strategy-ContractDiff**: 对比 API 契约定义与实际请求响应的差异
- **Strategy-EnvironmentDiff**: 对比正常/异常网络环境下的行为差异

### 兼容性专项策略

- **Strategy-DeviceDiff**: 从问题设备与正常设备的参数差异出发，定位敏感点
- **Strategy-APISurface**: 从使用的系统 API 出发，检查版本兼容性和厂商修改
- **Strategy-SDKInteraction**: 从第三方 SDK 版本和交互出发，检查兼容性声明

### 编排器分配规则

- 必须包含 1 个通用策略 + 1-2 个分类专项策略
- 确保至少有 2 个策略从不同维度切入（避免"换个说法得出同样结论"的假收敛）

---

## Challenger 质疑协议

Challenger Agent 接收所有 Investigator 的 Reasoning Chain Output，对每个结论执行系统化质疑：

```markdown
## Challenge Protocol（挑战协议）

对每个 Investigator 的结论执行以下质疑:

### 1. 因果充分性质疑
"假设根因X被修复，问题是否一定消失？是否存在X被修复但问题依旧的场景？"

### 2. 因果必要性质疑
"是否存在其他原因Y，同样能解释所有观察到的现象？Y的可能性是否被充分排除？"

### 3. 证据可靠性质疑
"所引用的证据是否存在多义性？同一证据是否可以支持不同结论？"

### 4. 遗漏检查
"是否存在未被解释的现象？因果链中是否有未验证的跳跃？"

### 5. 平台盲区检查
"分析是否充分考虑了平台特异性？Android/iOS在此场景下的行为差异是否被纳入？"
```

**质疑输出**：对每个结论标注为：
- **存活（Survived）**: 所有质疑均能合理回应
- **削弱（Weakened）**: 部分质疑暴露弱点，附具体弱点描述
- **否决（Refuted）**: 发现致命反驳证据，附反驳证据

---

## Arbiter 仲裁协议

Arbiter Agent 接收所有 Investigator 的结论 + Challenger 的质疑结果，执行最终裁定：

```markdown
## Arbitration Protocol（仲裁协议）

### Step 1: 汇总对比
将所有存活/削弱的假设列表，按维度对比:
- 证据覆盖度: 能解释多少个原子现象
- 反事实通过率: 预测验证的通过比例
- 抗质疑强度: 经过 Challenger 后的剩余置信度
- 因果链完整度: 从触发到现象的链条是否有断裂

### Step 2: 一致性分析
- 多个 Investigator 是否指向同一根因？（收敛 → 高置信）
- 指向不同根因？（发散 → 可能多因素或分析不足）
- 部分重叠？（可能存在根因链，一个是另一个的上游）

### Step 3: 最终裁定
- 收敛情况: 直接采信，最终置信度 = avg(各Agent置信度) × 收敛加权
- 发散情况:
  - 判断是否为多根因问题（分别列出）
  - 或标记为"需补充信息"，列出需要额外收集的上下文
  - 或降级置信度，附带完整的不确定性说明

### Step 4: 置信度校准
最终置信度 = base_score × convergence_factor × challenge_survival_rate
- base_score: 最佳假设的原始得分
- convergence_factor: 1.2(全部收敛), 1.0(部分收敛), 0.7(完全发散)
- challenge_survival_rate: 通过质疑的比例
```

---

## 多 Agent 对抗轮次控制

```
对抗轮次控制规则:
- Investigator 分析: 1 轮（并行），不可重试
- Challenger 质疑: 1 轮（基于 Investigator 结论执行一次性质疑）
- Arbiter 裁定: 1 轮，但允许向 Investigator 发起最多 1 次"定向补问"
  （仅当某一关键假设存在信息空缺，补问内容必须是明确的封闭式问题）
- 最大对抗总轮次: 3 轮（Investigator + Challenger + Arbiter，含 1 次补问）
- 超过上限仍未收敛 → 强制 Arbiter 执行降级裁定（见下）
```

### Arbiter 强制降级裁定规则

触发条件：达到轮次上限 **或** 所有 Investigator 结论完全发散无重叠

降级裁定输出：
1. 列出所有存活假设（不做选择）
2. 为每个假设标注: 支持证据数量 + 最强证据等级
3. 给出"当前最可能假设"（仅基于证据覆盖度机械排序，不做推断）
4. 置信度强制降为 Low（< 0.5）
5. 工作流状态转为 Human-Review，附带降级裁定报告

---

## Sub-Issue 拆分协议

### 触发条件（满足任一即可）
1. Issue Card 中 Platform = Both
2. Root Cause 假设指向平台特异性代码（非共享业务逻辑层）
3. Fix Design 需要在 Android 和 iOS 分别修改代码

### 拆分流程

**Step 1**: 编排器从当前 Issue 生成两个子工单:
- Sub-Issue-Android: {父Issue-ID}-android
  - 继承父 Issue 的 Spec Document（共享行为规约）
  - 独立的 Context Bundle（仅包含 Android 端相关证据和代码）
- Sub-Issue-iOS: {父Issue-ID}-ios
  - 继承父 Issue 的 Spec Document（共享行为规约）
  - 独立的 Context Bundle（仅包含 iOS 端相关证据和代码）

**Step 2**: 两个 Sub-Issue 各自独立经历 Phase 3/4/5
- 各自产出独立的 Root Cause Report 和 Fix Design Document
- 各自在独立分支上实施修复（fix/ai-issue-{父ID}-android 和 fix/ai-issue-{父ID}-ios）

**Step 3**: 跨端一致性对比（由父 Issue Arbiter Agent 执行）
- 输入: Sub-Issue-Android 的 Fix Design Document + Sub-Issue-iOS 的 Fix Design Document
- 执行对比:
  - L2 行为一致性: 两端修复后是否产生相同的业务结果？
  - L3 容错一致性: 两端的异常处理和降级策略是否对齐？
  - 差异识别: 是平台合理差异还是需要对齐的不一致？
- 输出: 跨端一致性报告（附带允许差异的理由说明）

**Step 4**: 父 Issue 状态
- 仅在两个 Sub-Issue 均验证通过后，父 Issue 才能关闭
- Knowledge Card 在父 Issue 级别生成，包含双端分析的综合经验

### 无多 Agent 能力时的降级处理

在纯对话平台中，无法并行派发子 Agent，应采用以下降级策略：

- 在同一对话中顺序执行两端分析，明确标注 `[Android 分析]` / `[iOS 分析]`
- 最后执行跨端一致性对比
- 同样需要明确标注 `[Investigator-A: Strategy-XXX]` / `[Challenger 质疑]` / `[Arbiter 裁定]` 的角色
