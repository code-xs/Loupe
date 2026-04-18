# B2C 移动端质量工作流 Batch A0 第一批可执行改动清单

> 日期：2026-04-18
> 范围：Batch A0 第一批可直接开工的改动
> 目标：先补齐运行时和状态机底座，再进入 Batch A / B 的正式结构改造

---

## 1. 执行原则

本清单只覆盖 Batch A0 的第一批可执行改动，特点是：

1. **改运行时底座，不改角色拓扑。**
2. **改状态与规则，不改最终业务策略。**
3. **先让系统支持未来改造，再让未来改造真正生效。**

本批次不做：

1. 不新增共享 `challenger` / `arbiter` 基座文件
2. 不切换专项复合角色
3. 不删除任何旧 Agent 文件
4. 不正式启用新的动态 fan-out 策略

---

## 2. 推荐任务序列

建议按以下顺序执行：

1. `A0-T1` 先加状态模板版本与路由字段
2. `A0-T2` 再补配置层的路由策略字段
3. `A0-T3` 再补 DSL 核心规则
4. `A0-T4` 再补主编排器的重路由逻辑
5. `A0-T5` 再补 P3 / P4 / P6 三个关键阶段
6. `A0-T6` 最后同步专项兼容层和入口文档

---

## 3. 第一批任务清单

## 3.1 A0-T1 主工作流状态模板升级

### 目标

让主工作流的 `workflow-status.yaml` 具备：

- 版本识别能力
- 动态 fan-out 承载能力
- 回流与重路由承载能力

### 涉及文件

- `mobile-qa-workflow/core/workflow-status-template.yaml`

### 具体修改内容

在保留现有字段结构的前提下，新增以下字段：

```yaml
workflow_version: "a0"
schema_version: 2
analysis_complexity: null
analysis_complexity_confidence: null
fanout_mode: null
reroute_reason: null
reroute_from_phase: null
reroute_target_phase: null
rca_retry_count: 0
fix_retry_count: 0
verification_failure_type: null
```

### 修改要求

1. 新字段放在现有基础状态字段之后、专项状态字段之前
2. 不改现有字段名和现有字段语义
3. 所有新增字段默认允许为 `null`
4. 注释中明确：
   - `workflow_version` 用于恢复兼容
   - `reroute_target_phase` 用于强制重入目标阶段

### 完成判据

- 新会话创建出的状态文件带版本字段
- 老字段不受影响
- 后续 `P3 / P4 / P6` 有状态落点可写

---

## 3.2 A0-T2 主工作流配置文件升级

### 目标

让配置层能记录当前路由策略版本和运行时追踪输出位。

### 涉及文件

- `mobile-qa-workflow/core/default-config.yaml`

### 具体修改内容

在现有产物路径与环境能力字段附近，新增：

```yaml
routing_policy_version: "a0"
active_fanout_policy: null
output_runtime_compat_report: null
output_reroute_trace: null
```

### 修改要求

1. 不改已有输出路径字段名
2. `routing_policy_version` 固定初始化为 `"a0"`
3. `output_reroute_trace` 仅做预留，不要求本批次立刻产出文件

### 完成判据

- 配置文件能表达当前路由策略版本
- 后续回流排查有配置落点

---

## 3.3 A0-T3 专项工作流状态与配置升级

### 目标

为专项工作流建立最小兼容层，确保后续角色收敛不会直接打断在途任务。

### 涉及文件

- `mobile-qa-workflow/functionality-deep-dive/core/workflow-status-template.yaml`
- `mobile-qa-workflow/functionality-deep-dive/core/default-config.yaml`

### 具体修改内容

#### 状态模板新增字段

```yaml
workflow_version: "v3-legacy"
schema_version: 2
legacy_flow_mode: true
compat_mapping_applied: false
```

#### 默认配置新增字段

```yaml
workflow_version: "v3-legacy"
routing_policy_version: "a0"
legacy_agent_set: true
compat_mode: true
```

### 修改要求

1. 当前阶段不改专项旧字段
2. 明确 `legacy_flow_mode: true` 表示当前默认仍按旧专项流运行
3. 不提前定义新专项角色文件名到 config 中

### 完成判据

- 专项流程首次具备版本与兼容状态
- 后续 Batch A 可以基于这些字段做新旧拓扑并存

---

## 3.4 A0-T4 DSL 核心规则补强

### 目标

在 DSL 基座里明确两件事：

1. 参数怎么注入
2. 状态升级与重路由怎么生效

### 涉及文件

- `mobile-qa-workflow/core/core-rules.xml`

### 具体修改内容

#### 在 `invoke-subagent` 规则中增加一条

语义要求：

- 允许通过 `subagent_prompt` 显式注入场景参数
- 参数传递依赖调用处字符串拼接与 `{var}` 占位替换
- 不依赖 `.md` Agent 文件内部模板渲染

建议加入的规则文本：

```xml
<rule>运行时参数注入：允许在 subagent_prompt 中通过显式文本和 {variable} 占位符注入场景、维度和模式参数；不得假设 agents/*.md 文件内部支持条件模板渲染。</rule>
```

#### 增加“状态重路由约束”说明

建议新增说明块，明确：

- 阶段文件可以决定升级
- 但必须通过 `workflow_status` 回写以下字段：
  - `fanout_mode`
  - `reroute_reason`
  - `reroute_target_phase`
- 主编排器只认状态字段，不认隐式文字描述

### 修改要求

1. 不破坏现有标签语义
2. 新规则应放在 `invoke-subagent` 规则段中，靠近“黑盒透传”描述
3. 若新增说明块，需保持现有 XML 结构风格

### 完成判据

- DSL 明确否定 `.md` 内部模板引擎假设
- 后续动态路由改造有统一规则依据

---

## 3.5 A0-T5 主编排器状态机补强

### 目标

让主编排器知道：

- 如何识别新版状态模板
- 如何响应 `P3 / P4 / P6` 发起的回流
- 如何避免无限循环

### 涉及文件

- `mobile-qa-workflow/core/workflow.xml`

### 具体修改内容

#### 修改点 1：恢复步骤增加版本识别

在“判断当前阶段并加载工作流”前后补充逻辑：

- 读取 `workflow_version`
- 若为空，则视为旧版状态文件
- 对旧版状态文件补充兼容默认值：
  - `fanout_mode = null`
  - `reroute_target_phase = null`
  - `rca_retry_count = 0`
  - `fix_retry_count = 0`

#### 修改点 2：判断当前阶段时优先处理重路由

在根据 `stepsCompleted` 判断当前阶段之前，增加优先级判断：

```text
if reroute_target_phase == qa-root-cause -> 当前阶段强制设为 qa-root-cause
if reroute_target_phase == qa-fix-design -> 当前阶段强制设为 qa-fix-design
```

#### 修改点 3：阶段完成后增加重试保护

增加逻辑：

- 若 `rca_retry_count > 2` 或 `fix_retry_count > 2`
- 则直接进入 `Human-Review`

### 修改要求

1. 不改变六阶段主序列
2. 重路由只作为“插队重入”，不永久改变工作流模型
3. 必须保留旧状态文件可恢复能力

### 完成判据

- 主编排器能识别重路由目标阶段
- 不会因为旧状态模板缺字段而失败
- 具备避免无限重入的保护

---

## 3.6 A0-T6 P3 先落状态，不落新策略

### 目标

先让 `P3` 会把复杂度、分析模式和升级原因写入状态文件，但暂不正式切换新的 fan-out 实现。

### 涉及文件

- `mobile-qa-workflow/phases/p3-root-cause.md`

### 具体修改内容

#### 修改点 1：复杂度评估后写回状态

在复杂度评估步骤后增加：

```text
更新 {workflow_status}：
- analysis_complexity = [simple|medium|complex]
- analysis_complexity_confidence = [High|Medium|Low]
```

#### 修改点 2：为后续升级预留状态写回

在以下场景写回：

- 反事实校验失败
- 最终置信度过低
- 多视角不收敛

写回内容：

```text
fanout_mode = escalate-required
reroute_reason = [具体原因]
reroute_target_phase = qa-root-cause
rca_retry_count += 1
```

### 修改要求

1. 本批次不改 investigator / challenger / arbiter 的真实调用拓扑
2. 只加状态写回和升级语义
3. 所有升级原因应尽量结构化，不只写自由文本

### 完成判据

- P3 具备“复杂度判定可被后续阶段推翻”的状态基础
- 后续 Batch B 可直接接入新路由矩阵

---

## 3.7 A0-T7 P4 先落状态，不落新 proposer 拓扑

### 目标

先让 `P4` 能记录当前修复模式与升级意图，为后续动态 proposer 模式铺路。

### 涉及文件

- `mobile-qa-workflow/phases/p4-fix-design.md`

### 具体修改内容

在“修复路径选择与方案生成”步骤附近增加状态写回：

```text
更新 {workflow_status}：
- fanout_mode = [single-fix | contested-fix | escalated-fix]
- reroute_reason = null 或 [高风险/不确定性原因]
```

建议同时增加注释性说明：

- 当前模式由置信度、风险和环境能力共同决定
- 本批次只记录模式，不正式改路由策略

### 完成判据

- P4 可以把当前设计模式显式写入状态文件
- P6 未来可根据该字段进行回流决策

---

## 3.8 A0-T8 P6 失败分类与回流分叉

### 目标

让验证阶段第一次具备“按失败类型重路由”的能力。

### 涉及文件

- `mobile-qa-workflow/phases/p6-verification.md`

### 具体修改内容

#### 在“验证判定”前增加失败分类

建议分类为：

```text
design_insufficient
root_cause_not_closed
implementation_mismatch
```

#### 修改失败路径

把当前统一回退：

```text
current_state = Fix-Designing
```

改成带分支的写回语义：

```text
若 verification_failure_type == design_insufficient:
  reroute_target_phase = qa-fix-design
  fix_retry_count += 1

若 verification_failure_type == root_cause_not_closed:
  reroute_target_phase = qa-root-cause
  rca_retry_count += 1
  fanout_mode = escalate-required
```

`implementation_mismatch` 可以先保留回流 `P4`，因为本批次还不处理更细的实施分叉。

### 修改要求

1. 本批次不改变 L1/L2/L3 的验证主框架
2. 只改变失败后的状态写回语义
3. 明确保留 `Human-Review` 兜底

### 完成判据

- P6 不再把所有失败统一当作“修复设计问题”
- 能为复杂度误判提供自动纠偏入口

---

## 3.9 A0-T9 专项编排器增加旧会话兼容识别

### 目标

让专项工作流先识别旧会话，再谈后续角色收敛。

### 涉及文件

- `mobile-qa-workflow/functionality-deep-dive/core/workflow.xml`

### 具体修改内容

在“初始化或恢复子工作区状态”步骤中补充：

1. 读取 `workflow_version`
2. 若缺失，则视为旧专项状态
3. 自动回填兼容默认值：
   - `legacy_flow_mode = true`
   - `compat_mapping_applied = false`

在“判断当前阶段”逻辑前增加注释性说明：

- 旧专项状态优先沿旧阶段继续执行
- Batch A0 不切换专项阶段序列

### 完成判据

- 旧专项任务不会因为新增字段而恢复失败
- 为后续 Batch A 的专项收敛留出安全空间

---

## 3.10 A0-T10 入口与平台文档同步

### 目标

确保 Full / Limited / 平台说明都明确同一件事：当前参数注入走调用 prompt，状态升级走状态文件。

### 涉及文件

- `mobile-qa-workflow/SKILL.md`
- `mobile-qa-workflow/system-prompt.md`
- `mobile-qa-workflow/PLATFORM-GUIDE.md`

### 具体修改内容

#### `SKILL.md`

补一段恢复逻辑说明：

- 恢复已有问题时先读取状态模板版本
- 动态路由状态由 `workflow-status.yaml` 驱动

#### `system-prompt.md`

补三类内容：

1. 参数化 prompt 不依赖 `.md` 模板渲染
2. `P3 / P4 / P6` 的回流语义
3. 状态机新增“验证失败回流 P3 / P4”的说明

#### `PLATFORM-GUIDE.md`

新增一节：

- “动态路由与状态恢复”

明确：

1. `{variable}` 占位是运行时变量注入
2. `.md` 文件本身不是模板引擎
3. Dify / Coze / LangGraph 等平台需要自己保证状态版本兼容

### 完成判据

- Full 与 Limited 文档口径一致
- 后续 Batch A / B 不会因为平台理解偏差而分叉

---

## 4. 建议按两次开发提交落地

### 提交 1：状态与规则底座

涉及任务：

- `A0-T1`
- `A0-T2`
- `A0-T3`
- `A0-T4`

涉及文件：

- `mobile-qa-workflow/core/workflow-status-template.yaml`
- `mobile-qa-workflow/core/default-config.yaml`
- `mobile-qa-workflow/functionality-deep-dive/core/workflow-status-template.yaml`
- `mobile-qa-workflow/functionality-deep-dive/core/default-config.yaml`
- `mobile-qa-workflow/core/core-rules.xml`

建议提交信息：

```bash
chore(workflow): add a0 routing state and runtime compatibility baseline
```

### 提交 2：主编排器与阶段回流语义

涉及任务：

- `A0-T5`
- `A0-T6`
- `A0-T7`
- `A0-T8`
- `A0-T9`
- `A0-T10`

涉及文件：

- `mobile-qa-workflow/core/workflow.xml`
- `mobile-qa-workflow/phases/p3-root-cause.md`
- `mobile-qa-workflow/phases/p4-fix-design.md`
- `mobile-qa-workflow/phases/p6-verification.md`
- `mobile-qa-workflow/functionality-deep-dive/core/workflow.xml`
- `mobile-qa-workflow/SKILL.md`
- `mobile-qa-workflow/system-prompt.md`
- `mobile-qa-workflow/PLATFORM-GUIDE.md`

建议提交信息：

```bash
chore(workflow): add reroute semantics for p3 p4 p6 and sync platform docs
```

---

## 5. 本批次完成定义

当以下条件全部满足时，这一批可执行改动才算完成：

1. 主工作流状态模板新增版本与路由字段
2. 专项状态模板新增兼容字段
3. `core-rules.xml` 明确参数注入约束
4. `core/workflow.xml` 能识别 `reroute_target_phase`
5. `p3/p4/p6` 已能写回升级或回流状态
6. `SKILL.md`、`system-prompt.md`、`PLATFORM-GUIDE.md` 已同步运行时口径

---

## 6. 完成后可直接进入的下一步

完成本批次后，就可以进入真正的结构改造：

1. 共享 `challenger` / `arbiter` 基座
2. 修正专项 `F4` 对通用 `investigator` 的借用
3. 正式上线 `P3 / P4` 动态 fan-out

因此，这一批虽然不“显眼”，但它决定后面所有架构改造是否能安全上线。
