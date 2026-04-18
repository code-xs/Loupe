# B2C 移动端质量工作流 SubAgent Batch A0 逐文件实施方案

> 日期：2026-04-18
> 目标：在进入 Batch A / B 真实结构改造前，先完成运行时边界确认、状态机补强、状态模板版本化与文档口径统一
> 依据：
> - `doc/B2C_WORKFLOW_SUBAGENT_FINAL_ADOPTION_2026-04-18.md`
> - `doc/B2C_WORKFLOW_SUBAGENT_IMPLEMENTATION_CHECKLIST_2026-04-18.md`

---

## 1. Batch A0 的定位

`Batch A0` 不是正式的角色重构批次，而是正式改造前的“运行时落地准备批次”。

本批次只解决 4 类问题：

1. 动态 fan-out 的引擎支持边界
2. 参数化 Prompt 的运行时注入方式
3. 会话恢复与状态模板版本兼容
4. 复杂度误判后的熔断与重路由机制

本批次**不做**以下事情：

1. 不新增共享 `challenger` / `arbiter` 基座文件
2. 不删除旧专项角色文件
3. 不正式切换到新的专项复合角色
4. 不在主流程中直接上线新的 fan-out 策略

一句话：

> Batch A0 的任务是把“未来要怎么改”变成“运行时能够安全支撑怎么改”。

---

## 2. 本批次的最终交付物

Batch A0 完成后，应形成以下交付物：

1. 一套明确的动态路由状态字段定义
2. 一套明确的 P3 / P4 / P6 重路由状态机设计
3. 一套带版本号的主工作流 / 专项工作流状态模板
4. 一套旧状态到新状态的兼容策略
5. 一份明确说明“参数通过调用 prompt 注入，而非 `.md` 内部模板渲染”的平台口径
6. 一份可供 Batch A / B 直接执行的运行时约束基线

---

## 3. 推荐实施顺序

### A0-1 先固化核心规则

- `core/core-rules.xml`
- `core/workflow-status-template.yaml`
- `core/default-config.yaml`

### A0-2 再补主编排器状态机

- `core/workflow.xml`
- `phases/p3-root-cause.md`
- `phases/p4-fix-design.md`
- `phases/p6-verification.md`

### A0-3 再补专项兼容层

- `functionality-deep-dive/core/workflow-status-template.yaml`
- `functionality-deep-dive/core/default-config.yaml`
- `functionality-deep-dive/core/workflow.xml`

### A0-4 最后同步入口与文档

- `SKILL.md`
- `system-prompt.md`
- `PLATFORM-GUIDE.md`
- `doc/B2C_WORKFLOW_SUBAGENT_IMPLEMENTATION_CHECKLIST_2026-04-18.md`

---

## 4. 逐文件实施方案

## 4.1 `mobile-qa-workflow/core/core-rules.xml`

### 本文件在 Batch A0 的角色

作为 DSL 规则基座，负责把后续动态路由、参数注入与兼容约束显式化，避免后续阶段文件“各写各的规则”。

### 需要补充的内容

1. 在 `invoke-subagent` 规则区补充参数注入约束：
   - 允许通过 `subagent_prompt` 传入场景参数
   - 参数传递采用调用 prompt 显式注入
   - 不依赖 `.md` 文件内部模板渲染
2. 增加动态 fan-out 的运行时约束说明：
   - 阶段文件可根据状态字段选择不同 subagent 拓扑
   - 但升级、回退、重入必须回写 `workflow_status`
3. 增加重路由规则说明：
   - `P3` 低置信度可升级分析模式
   - `P6` 验证失败允许回流 `P3` 或 `P4`
4. 增加状态模板版本兼容约束：
   - 读取状态文件时必须优先识别版本
   - 未识别版本时进入兼容映射逻辑

### 具体改造步骤

1. 在 `invoke-subagent` 的规则段落增加“运行时参数注入”条目
2. 在支持标签说明后增加“动态路由约束”说明块
3. 在 `human-review-protocol` 前增加“状态恢复兼容”说明块
4. 为示例调用增加一条“场景参数注入”示例

### 验收结果

- 后续所有动态路由改造都有统一 DSL 规则依据
- 不再默认假设 `.md` 原生支持模板引擎

---

## 4.2 `mobile-qa-workflow/core/workflow-status-template.yaml`

### 本文件在 Batch A0 的角色

作为主工作流状态单一事实源，承担未来动态 fan-out、重路由和恢复兼容的状态持久化职责。

### 需要补充的字段

建议新增：

- `workflow_version`
- `schema_version`
- `analysis_complexity`
- `analysis_complexity_confidence`
- `fanout_mode`
- `reroute_reason`
- `reroute_from_phase`
- `reroute_target_phase`
- `rca_retry_count`
- `fix_retry_count`
- `verification_failure_type`

### 字段用途说明

- `workflow_version` / `schema_version`
  - 用于状态模板版本识别与旧会话兼容
- `analysis_complexity`
  - 落盘 `simple / medium / complex`
- `analysis_complexity_confidence`
  - 标记复杂度判定本身的置信度
- `fanout_mode`
  - 标记当前是否处于 `single-view / investigator+challenger / full-debate`
- `reroute_reason`
  - 记录为什么升级或回退
- `reroute_from_phase` / `reroute_target_phase`
  - 记录回流链路
- `rca_retry_count` / `fix_retry_count`
  - 防止无限回流
- `verification_failure_type`
  - 区分“修复方案不足”还是“根因闭环失败”

### 具体改造步骤

1. 在保留现有字段不破坏的前提下新增上述字段
2. 保持 YAML 结构稳定，不改动现有关键字段语义
3. 在注释中补充旧会话兼容说明
4. 明确默认值均允许为 `null`

### 验收结果

- 后续 P3/P4/P6 的动态路由有状态落点
- 状态模板变更不再是无版本演进

---

## 4.3 `mobile-qa-workflow/core/default-config.yaml`

### 本文件在 Batch A0 的角色

作为工作区配置与产物路径登记表，负责为动态路由和回流逻辑提供补充配置字段。

### 需要补充的字段

建议新增：

- `routing_policy_version`
- `output_runtime_compat_report`
- `output_reroute_trace`
- `active_fanout_policy`

### 具体改造步骤

1. 保留现有产物路径定义
2. 新增与 Batch A0 对应的运行时配置字段
3. 为后续评测与回流排障预留 reroute trace 输出位

### 验收结果

- 主流程支持记录动态路由策略版本
- 未来回流或排障时可追踪路由决策

---

## 4.4 `mobile-qa-workflow/core/workflow.xml`

### 本文件在 Batch A0 的角色

作为主编排器，Batch A0 需要把它从“只会顺序流转阶段”升级为“理解升级、回退、重入”的状态机。

### 需要补的能力

1. 支持识别新状态模板字段
2. 支持 `P3` 的升级重入
3. 支持 `P4` 的升级重入
4. 支持 `P6` 基于失败类型回流到 `P3` 或 `P4`
5. 支持状态模板版本兼容

### 具体改造步骤

1. 在初始化/恢复状态步骤中增加：
   - 读取 `workflow_version`
   - 若缺失则标记为旧版状态
   - 进入兼容映射逻辑
2. 在“判断当前阶段”逻辑中补充以下判断：
   - 若 `reroute_target_phase == qa-root-cause`，优先重新进入 `P3`
   - 若 `reroute_target_phase == qa-fix-design`，优先重新进入 `P4`
3. 在“阶段完成后更新进度并路由”中补充：
   - `P3` 升级后不直接进入 `P4`
   - `P6` 失败时不再固定回退
4. 增加对 `rca_retry_count` / `fix_retry_count` 的保护
5. 增加“超过重路由阈值则进入 Human-Review”的保护逻辑

### 推荐新增状态或语义

- `RCA-Rerouting`
- `Fix-Rerouting`
- `Verification-Failed`

如果不希望新增太多状态，也至少要在现有 `current_state` 之外依赖 `reroute_target_phase` 明确路由意图。

### 验收结果

- 主编排器具备对后续动态 fan-out 的状态承载能力
- 不会因为阶段文件升级而导致主流程无法恢复

---

## 4.5 `mobile-qa-workflow/phases/p3-root-cause.md`

### 本文件在 Batch A0 的角色

此时不正式切换新 fan-out 策略，但要先把未来动态路由所需的状态写入、升级触发条件和重入入口定义清楚。

### Batch A0 只做的事情

1. 增加复杂度字段写回约定
2. 增加轻模式失败时的升级约定
3. 增加回流后重新执行的入口说明

### 具体改造步骤

1. 在复杂度评估后，显式写回：
   - `analysis_complexity`
   - `analysis_complexity_confidence`
2. 在快速路径或轻模式路径后增加升级触发条件：
   - 最终置信度低于阈值
   - `challenger` 出现 Critical 级质疑
   - 反事实校验失败
3. 升级时写回：
   - `fanout_mode`
   - `reroute_reason`
   - `reroute_target_phase = qa-root-cause`
4. 不在 Batch A0 里真正替换所有分支，只先定义新状态和入口

### 验收结果

- P3 已具备“复杂度判定可被推翻”的运行时约束
- 后续 Batch B 可以直接接管具体 fan-out 实现

---

## 4.6 `mobile-qa-workflow/phases/p4-fix-design.md`

### 本文件在 Batch A0 的角色

和 P3 一样，先补状态与升级语义，不在 Batch A0 里直接切换真实 proposer 拓扑。

### Batch A0 只做的事情

1. 增加修复模式状态写回
2. 增加修复方案不足时的升级语义
3. 增加给 `P6` 的失败分类协作字段

### 具体改造步骤

1. 在模式选择处增加写回：
   - `fix_strategy_mode`
   - `fanout_mode`
2. 增加升级条件定义：
   - 高风险修改
   - 副作用不确定
   - 多方案打分接近
3. 在输出阶段补充：
   - 记录当前 fix route 的判定依据
4. 为 `P6` 预留失败分类回流接口

### 验收结果

- P4 和 P6 能通过状态字段协同
- 后续 Batch B 可直接把多 proposer 动态化接上

---

## 4.7 `mobile-qa-workflow/phases/p6-verification.md`

### 本文件在 Batch A0 的角色

这是复杂度误判的最后一道兜底。Batch A0 的关键改动之一，就是让 `P6` 有能力区分“设计问题”与“根因问题”。

### 需要补的能力

1. 验证失败分类
2. 按失败分类重路由
3. 回写 `reroute_target_phase`

### 具体改造步骤

1. 在“验证判定”前增加失败分类逻辑：
   - `design_insufficient`
   - `root_cause_not_closed`
   - `implementation_mismatch`
2. 当失败类型为 `design_insufficient`：
   - 回流 `qa-fix-design`
3. 当失败类型为 `root_cause_not_closed`：
   - 回流 `qa-root-cause`
   - 同时要求升级 `fanout_mode`
4. 把失败原因写回 `workflow_status`
5. 设置重试上限，避免 `P3 -> P4 -> P6` 无限环

### 验收结果

- 验证阶段不再只是“统一退回 P4”
- 复杂度误判具备自动纠偏能力

---

## 4.8 `mobile-qa-workflow/functionality-deep-dive/core/workflow-status-template.yaml`

### 本文件在 Batch A0 的角色

为专项工作流的旧会话兼容和未来角色收敛做准备。

### 需要补充的字段

建议新增：

- `workflow_version`
- `schema_version`
- `legacy_flow_mode`
- `compat_mapping_applied`

### 具体改造步骤

1. 保留现有 `stepsCompleted / current_state / artifacts`
2. 新增版本与兼容字段
3. 明确：
   - 旧版专项会话允许继续沿旧阶段完成
   - 新版专项会话才使用新映射

### 验收结果

- 专项状态模板具备版本演进基础
- 后续 Batch A 不会因为状态结构变更伤到在途任务

---

## 4.9 `mobile-qa-workflow/functionality-deep-dive/core/default-config.yaml`

### 本文件在 Batch A0 的角色

为专项工作流兼容运行和旧/新拓扑共存提供配置占位。

### 需要补充的字段

建议新增：

- `workflow_version`
- `routing_policy_version`
- `legacy_agent_set`
- `compat_mode`

### 具体改造步骤

1. 新增版本字段
2. 新增兼容模式字段
3. 为后续专项角色收敛保留双拓扑切换空间

### 验收结果

- 专项 config 可以区分旧拓扑与新拓扑

---

## 4.10 `mobile-qa-workflow/functionality-deep-dive/core/workflow.xml`

### 本文件在 Batch A0 的角色

专项编排器在本批次不做结构收敛，但必须先具备“识别旧会话、允许继续沿旧路径执行”的兼容能力。

### 具体改造步骤

1. 在初始化或恢复子工作区状态时读取：
   - `workflow_version`
   - `compat_mode`
2. 若为旧版会话：
   - 使用旧阶段序列继续执行
3. 若为新版会话：
   - 按新版兼容策略执行
4. 增加兼容映射说明注释，避免后续误删旧分支

### 验收结果

- 新旧专项流程可以并存一段时间
- 不会因为上线新状态模板导致旧专项任务中断

---

## 4.11 `mobile-qa-workflow/SKILL.md`

### 本文件在 Batch A0 的角色

作为 Full 平台入口，要同步“运行时边界”而不是同步未来尚未上线的结构改造。

### 需要补充的说明

1. 当前运行时不依赖 `.md` 内部模板渲染
2. 动态路由状态由工作区状态文件驱动
3. 恢复已有问题时需优先识别状态模板版本

### 具体改造步骤

1. 在初始化或恢复工作区步骤中补充版本识别说明
2. 在加载主编排器步骤中补充“读取动态路由状态字段”的说明
3. 明确 Batch A0 之后恢复逻辑新增版本兼容

### 验收结果

- Full 平台入口和底层状态机口径一致

---

## 4.12 `mobile-qa-workflow/system-prompt.md`

### 本文件在 Batch A0 的角色

作为 Limited 平台完整内联版本，必须先同步运行时边界，否则 Full / Limited 会出现设计分叉。

### 需要补充的内容

1. 状态机增加重路由语义
2. 复杂度误判可升级
3. P6 可回流 P3 或 P4
4. 参数化 prompt 不依赖 `.md` 模板渲染

### 具体改造步骤

1. 在核心规则部分补充参数注入与状态版本兼容说明
2. 在状态机图中补充：
   - `Verification -> P3`
   - `Verification -> P4`
3. 在 P3、P4、P6 的内联阶段描述中增加对应状态字段说明
4. 仅同步运行时前置规则，不提前同步未来所有角色改名

### 验收结果

- Limited 平台行为边界与 Full 平台一致
- 不会因为 system prompt 落后导致两套实现口径分裂

---

## 4.13 `mobile-qa-workflow/PLATFORM-GUIDE.md`

### 本文件在 Batch A0 的角色

负责说明不同平台下哪些能力是原生支持、哪些能力需要通过状态文件和 prompt 约定实现。

### 需要补充的说明

1. 当前参数化 prompt 的实现方式
2. 当前状态恢复的版本兼容要求
3. 动态 fan-out 的运行边界

### 具体改造步骤

1. 新增一节“动态路由与状态恢复”
2. 新增一节“Prompt 参数注入约束”
3. 明确 `.md` 角色文件不依赖模板引擎

### 验收结果

- 平台说明文档可以作为 Batch A / B 的约束参考

---

## 4.14 `doc/B2C_WORKFLOW_SUBAGENT_IMPLEMENTATION_CHECKLIST_2026-04-18.md`

### 本文件在 Batch A0 的角色

作为总实施清单，要在 Batch A0 完成后被更新为“门禁已确认”的状态。

### 具体改造步骤

1. 把 `WP-00` 从“待确认”改成“已完成/有结论”
2. 将 A0 产出的运行时结论回写到总清单
3. 将后续 Batch A / B 的前置依赖标记为已解除

### 验收结果

- 总清单和 A0 方案不冲突
- 后续批次可以基于已确认边界继续推进

---

## 5. 推荐提交顺序

建议将 Batch A0 拆成 4 个小提交，而不是一次性全部堆进一个提交。

### Commit 1

- `core/core-rules.xml`
- `core/workflow-status-template.yaml`
- `core/default-config.yaml`

主题：

`chore(workflow): add runtime routing and schema version baseline`

### Commit 2

- `core/workflow.xml`
- `phases/p3-root-cause.md`
- `phases/p4-fix-design.md`
- `phases/p6-verification.md`

主题：

`chore(workflow): add reroute state model for p3 p4 p6`

### Commit 3

- `functionality-deep-dive/core/workflow-status-template.yaml`
- `functionality-deep-dive/core/default-config.yaml`
- `functionality-deep-dive/core/workflow.xml`

主题：

`chore(deep-dive): add legacy compatibility and schema version fields`

### Commit 4

- `SKILL.md`
- `system-prompt.md`
- `PLATFORM-GUIDE.md`
- `doc/B2C_WORKFLOW_SUBAGENT_IMPLEMENTATION_CHECKLIST_2026-04-18.md`
- 本文档

主题：

`docs(workflow): sync runtime constraints for batch a0`

---

## 6. Batch A0 完成判定

满足以下条件，才算 Batch A0 完成：

1. 主工作流和专项工作流状态模板都带版本字段
2. 主编排器可以识别重路由目标阶段
3. `P6` 失败已可区分回流 `P3` 或 `P4`
4. 文档已明确参数注入不依赖 `.md` 模板渲染
5. Full / Limited 平台说明已同步
6. 总实施清单已回写 A0 结论

---

## 7. Batch A0 完成后的下一步

当 Batch A0 完成后，后续批次的依赖关系如下：

1. `Batch A`
   - 共享 `challenger` / `arbiter` 基座
   - 修正专项 F4 角色闭合
2. `Batch B`
   - P3 / P4 动态 fan-out 正式上线
3. `Batch C`
   - 专项角色收敛与专项产物分级

因此，`Batch A0` 的价值不在于直接减少角色数，而在于让之后每一次角色和编排改造都有安全的运行时底座。
