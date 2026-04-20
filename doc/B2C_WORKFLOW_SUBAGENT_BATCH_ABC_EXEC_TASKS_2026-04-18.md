# B2C 移动端质量工作流 Batch A/B/C 可执行清单

> 日期：2026-04-18
> 范围：`Batch A0` 之后的全部剩余改造场景
> 目标：把共享基座、动态 fan-out、专项角色收敛、产物分级、UI/UX 深度分析（主流程内） 和评测闭环拆成可直接执行的任务序列

---

## 1. 覆盖范围

本清单覆盖 `Batch A0` 之后的全部剩余需求，按三个批次收敛：

### Batch A

- 共享 `challenger` / `arbiter` 基座
- 修正专项 `F4` 对通用 `investigator` 的借用
- 统一业务角色 / 能力型 Agent 口径

### Batch B

- 正式启用 `P3` 动态 fan-out
- 正式启用 `P4` 动态 fan-out
- 让 `P6` 的失败分类和重路由真正生效

### Batch C

- 专项角色收敛到 `4~5` 个复合角色
- 专项阶段与编排收敛
- 专项产物分级
- 平台入口与文档同步
- `UI/UX 深度分析（主流程内）` 建设
- `eval-framework` 验证闭环

因此，这份文档已经覆盖了 A0 之后的全部剩余改造场景，不再遗漏主需求中的后续批次。

---

## 2. 执行总原则

1. **每个 Batch 都必须以上一批次的状态字段和运行时约束为前提。**
2. **路由切换先灰度，再删除旧文件。**
3. **任何角色裁剪都必须配套回归评测。**
4. **`system-prompt.md` 必须与 Full 平台实现同步。**
5. **涉及会话恢复的改动必须保留旧版兼容路径。**

---

## 3. Batch A 可执行清单

## 3.1 Batch A 的目标

Batch A 只解决“角色复用与边界问题”，不碰真正的 fan-out 动态启用。

完成后应达到：

1. `challenger` / `arbiter` 共性逻辑已抽成共享基座
2. 专项 `F4` 不再依赖通用 `investigator`
3. 文档和平台口径明确区分业务角色与能力型 Agent

---

## 3.2 Batch A 任务序列

### A-T1 新增共享 `challenger` 基座

#### 涉及文件

- 新增 `mobile-qa-workflow/agents/shared-challenger-base.md`
- 修改 `mobile-qa-workflow/agents/challenger.md`
- 修改 `mobile-qa-workflow/functionality-deep-dive/agents/challenger.md`

#### 具体修改内容

1. 在 `shared-challenger-base.md` 中沉淀共性内容：
   - 输入契约
   - 输出结构
   - 质疑结论格式
   - 置信度影响格式
2. 将主流程 `challenger.md` 改为包装层：
   - 归因模式
   - 修复模式
3. 将专项 `challenger.md` 改为专项包装层：
   - 七维专项质疑
4. 包装层内部只保留：
   - 场景说明
   - 维度集声明
   - 输出差异说明

#### 完成判据

- 主流程和专项流程不再维护两份完整同构的 challenger 逻辑
- 调用入口文件仍存在，避免直接打断现有路由

---

### A-T2 新增共享 `arbiter` 基座

#### 涉及文件

- 新增 `mobile-qa-workflow/agents/shared-arbiter-base.md`
- 修改 `mobile-qa-workflow/agents/arbiter.md`
- 修改 `mobile-qa-workflow/functionality-deep-dive/agents/arbiter.md`

#### 具体修改内容

1. 在 `shared-arbiter-base.md` 中沉淀共性裁定协议：
   - 汇总结论
   - 质疑吸收
   - 最终裁定
   - 置信度校准
2. 主流程 `arbiter.md` 只保留：
   - RCA 仲裁差异
   - Fix 仲裁差异
3. 专项 `arbiter.md` 只保留：
   - Deep-Dive 仲裁差异
   - 贡献因子定级差异

#### 完成判据

- 仲裁逻辑有统一基座
- `final_confidence` 的口径不再散落在两份大 prompt 中

---

### A-T3 改写主流程阶段文件的共享基座调用

#### 涉及文件

- `mobile-qa-workflow/phases/p3-root-cause.md`
- `mobile-qa-workflow/phases/p4-fix-design.md`

#### 具体修改内容

1. `p3-root-cause.md`
   - 继续调用 `challenger` / `arbiter`
   - 但调用 prompt 中显式传入：
     - `scene = RCA`
     - `dimension_set = rca-5d`
2. `p4-fix-design.md`
   - 继续调用 `challenger` / `arbiter`
   - 调用 prompt 中显式传入：
     - `scene = FIX`
     - `dimension_set = fix-4a`

#### 完成判据

- 主流程调用已经转为“共享基座 + 包装层”模式
- 不依赖 `.md` 模板渲染

---

### A-T4 改写专项 F4 的调用方式并切断通用 `investigator` 借用

#### 涉及文件

- 新增 `mobile-qa-workflow/functionality-deep-dive/agents/deep-dive-race-and-isolation-analyst.md`
- 修改 `mobile-qa-workflow/functionality-deep-dive/phases/f4-isolation-debate.md`
- 修改 `mobile-qa-workflow/functionality-deep-dive/agents/README.md`

#### 具体修改内容

1. 新建 `deep-dive-race-and-isolation-analyst.md`
   - 吸收当前 F4 中的：
     - 控制变量推演
     - 候选根因排序
     - 状态异常闭环验证
     - 时序窗口解释
2. 在 `f4-isolation-debate.md` 中：
   - 删除 `subagent_type="investigator"` 的使用
   - 改为调用 `deep-dive-race-and-isolation-analyst`
   - 删除“加载 `state-analyst.md` 作为补充视角”的拼接方式
3. 在专项 `agents/README.md` 中新增该角色说明

#### 完成判据

- 专项 F4 不再借用通用 `investigator`
- 专项分析链路边界更闭合

---

### A-T5 同步专项工作流说明文档

#### 涉及文件

- `mobile-qa-workflow/functionality-deep-dive/FUNCTIONALITY_DEEP_DIVE_WORKFLOW_V3.md`
- `mobile-qa-workflow/system-prompt.md`

#### 具体修改内容

1. 更新专项工作流说明：
   - F4 已改为专项收敛角色
   - 不再描述“借用主 investigator”
2. 更新 `system-prompt.md` 中相关专项段落：
   - 只同步边界修正
   - 不提前同步 Batch C 的最终角色收敛结构

#### 完成判据

- 文档与当前可运行拓扑一致

---

### A-T6 统一业务角色 / 能力型 Agent 口径

#### 涉及文件

- `mobile-qa-workflow/PLATFORM-GUIDE.md`
- `mobile-qa-workflow/core/core-rules.xml`
- `mobile-qa-workflow/functionality-deep-dive/agents/README.md`
- `doc/B2C_WORKFLOW_SUBAGENT_FINAL_ADOPTION_2026-04-18.md`
- `mobile-qa-workflow/system-prompt.md`

#### 具体修改内容

1. 增加“业务角色”与“能力型 Agent”定义
2. 明确 `search` 不计入业务角色统计
3. 在 `core-rules.xml` 的可读说明中补一段分类口径

#### 完成判据

- 对外和对内统计口径统一

---

## 3.3 Batch A 建议提交拆分

### Commit A1

- `shared-challenger-base.md`
- `challenger.md` 两处包装层
- `p3-root-cause.md`
- `p4-fix-design.md`

### Commit A2

- `shared-arbiter-base.md`
- `arbiter.md` 两处包装层

### Commit A3

- `deep-dive-race-and-isolation-analyst.md`
- `f4-isolation-debate.md`
- 专项说明文档

### Commit A4

- 分类口径同步文档

---

## 4. Batch B 可执行清单

## 4.1 Batch B 的目标

Batch B 让 `Batch A0` 里先落状态、未真正启用的动态路由正式生效。

完成后应达到：

1. `P3` 按复杂度和证据冲突启用不同 fan-out
2. `P4` 按风险和置信度启用不同 proposer 模式
3. `P6` 失败能真正回流 `P3` 或 `P4`

---

## 4.2 Batch B 任务序列

### B-T1 补 Spec 模板中的复杂度字段

#### 涉及文件

- `mobile-qa-workflow/templates/spec.md`

#### 具体修改内容

新增一个显式区块，例如：

- `Analysis Complexity`
- `Complexity Confidence`
- `Suggested Fan-out Mode`

建议支持值：

- `simple`
- `medium`
- `complex`

#### 完成判据

- `P2` 可以把复杂度结论稳定写入 `spec.md`

---

### B-T2 在 P2 中正式输出复杂度判定

#### 涉及文件

- `mobile-qa-workflow/phases/p2-spec-definition.md`

#### 具体修改内容

1. 增加复杂度判定步骤
2. 将复杂度结果写入：
   - `spec.md`
   - `workflow_status.analysis_complexity`
   - `workflow_status.analysis_complexity_confidence`

#### 完成判据

- `P3` 不再只能在自己内部猜复杂度

---

### B-T3 正式启用 P3 路由矩阵

#### 涉及文件

- `mobile-qa-workflow/phases/p3-root-cause.md`
- `mobile-qa-workflow/reference/analysis-strategies.md`
- `mobile-qa-workflow/system-prompt.md`

#### 具体修改内容

在 `p3-root-cause.md` 中把当前深度路径固定模式改为三档：

1. `simple`
   - 主 Agent 单视角 OVHSC
2. `medium`
   - `investigator + challenger`
3. `complex` 或 `证据冲突`
   - `2 investigators + challenger + arbiter`

同时补充升级逻辑：

- 轻模式置信度低 -> 升级
- `challenger` 出现 Critical -> 升级
- `P6` 回流 `P3` -> 强制进入升级模式

在 `analysis-strategies.md` 中：

- 为三档模式补策略建议
- 把策略数量和 fan-out 档位对齐

#### 完成判据

- `P3` 动态 fan-out 真正生效
- 复杂问题不丢上限，简单问题不再默认重编排

---

### B-T4 正式启用 P4 路由矩阵

#### 涉及文件

- `mobile-qa-workflow/phases/p4-fix-design.md`
- `mobile-qa-workflow/templates/fix-design.md`
- `mobile-qa-workflow/reference/fix-strategies.md`
- `mobile-qa-workflow/system-prompt.md`

#### 具体修改内容

在 `p4-fix-design.md` 中把当前多方案默认模式改为三档：

1. 高置信度 + 单点改动
   - 单 `fix-proposer`
2. 中置信度
   - `fix-proposer + challenger`
3. 多方案竞争或高风险修改
   - `2 proposers + challenger + arbiter`

在 `fix-design.md` 中：

- 兼容单方案输出
- 兼容对抗仲裁输出

在 `fix-strategies.md` 中：

- 区分单方案策略
- 区分高风险多方案策略

#### 完成判据

- `P4` 动态 proposer 模式真正生效

---

### B-T5 让主编排器真正识别 P3/P4 重入

#### 涉及文件

- `mobile-qa-workflow/core/workflow.xml`
- `mobile-qa-workflow/core/workflow-status-template.yaml`
- `mobile-qa-workflow/core/default-config.yaml`

#### 具体修改内容

1. 正式启用 `reroute_target_phase`
2. 正式启用：
   - `fanout_mode`
   - `analysis_complexity`
   - `fix_strategy_mode`
3. 增加重试上限保护：
   - `rca_retry_count`
   - `fix_retry_count`

#### 完成判据

- 主编排器不只是“能读字段”，而是真按字段路由

---

### B-T6 让 P6 失败分类真正生效

#### 涉及文件

- `mobile-qa-workflow/phases/p6-verification.md`

#### 具体修改内容

正式启用失败分类与回流：

1. `design_insufficient`
   - 回流 `P4`
2. `root_cause_not_closed`
   - 回流 `P3`
   - 强制升级 `fanout_mode`
3. `implementation_mismatch`
   - 先回流 `P4`
   - 必要时进入 `Human-Review`

#### 完成判据

- `P6` 成为纠偏入口，而不是只会统一回退

---

## 4.3 Batch B 建议提交拆分

### Commit B1

- `spec.md`
- `p2-spec-definition.md`

### Commit B2

- `p3-root-cause.md`
- `analysis-strategies.md`
- `system-prompt.md` 中 P3 部分

### Commit B3

- `p4-fix-design.md`
- `fix-design.md`
- `fix-strategies.md`
- `system-prompt.md` 中 P4 部分

### Commit B4

- `workflow.xml`
- `workflow-status-template.yaml`
- `default-config.yaml`
- `p6-verification.md`

---

## 5. Batch C 可执行清单

## 5.1 Batch C 的目标

Batch C 负责真正做“结构收敛、产物瘦身、产品谱系补齐、评测验证”。

完成后应达到：

1. 专项角色从 6 个细粒度角色收敛为 4~5 个复合角色
2. 专项阶段、产物和主编排依赖关系同步收敛
3. `UI/UX 深度分析（主流程内）` 有独立入口
4. 能用 `eval-framework` 比较改造前后收益

---

## 5.2 Batch C 任务序列

### C-T1 新建专项复合角色文件

#### 涉及文件

- 新增 `mobile-qa-workflow/functionality-deep-dive/agents/deep-dive-context-analyst.md`
- 新增 `mobile-qa-workflow/functionality-deep-dive/agents/deep-dive-structure-analyst.md`
- 新增 `mobile-qa-workflow/functionality-deep-dive/agents/deep-dive-race-and-isolation-analyst.md`
- 新增 `mobile-qa-workflow/functionality-deep-dive/agents/deep-dive-arbiter.md`

#### 具体修改内容

1. `deep-dive-context-analyst`
   - 吸收 `context-reconstructor`
   - 吸收部分状态输入预处理能力
2. `deep-dive-structure-analyst`
   - 吸收 `state-analyst`
   - 可做轻量时序预扫描
3. `deep-dive-race-and-isolation-analyst`
   - 吸收 `temporal-analyst`
   - 吸收 `F4` 隔离推演
4. `deep-dive-arbiter`
   - 吸收专项 `challenger + arbiter`

#### 完成判据

- 新专项复合角色文件齐备

---

### C-T2 改写专项阶段文件以切换到复合角色

#### 涉及文件

- `mobile-qa-workflow/functionality-deep-dive/phases/f1-context-reconstruction.md`
- `mobile-qa-workflow/functionality-deep-dive/phases/f2-state-topology.md`
- `mobile-qa-workflow/functionality-deep-dive/phases/f3-temporal-correlation.md`
- `mobile-qa-workflow/functionality-deep-dive/phases/f4-isolation-debate.md`
- `mobile-qa-workflow/functionality-deep-dive/phases/f5-defensive-fix-design.md`

#### 具体修改内容

1. `f1` 调整为调用 `deep-dive-context-analyst`
2. `f2` 调整为调用 `deep-dive-structure-analyst`
3. `f3` 调整为调用 `deep-dive-race-and-isolation-analyst`
4. `f4` 调整为调用 `deep-dive-arbiter`
5. `f5` 保留 `defensive-fix-architect`，但增加“按需触发”判定

#### 完成判据

- 专项阶段与新角色完全对齐

---

### C-T3 收敛专项编排和模型文件

#### 涉及文件

- `mobile-qa-workflow/functionality-deep-dive/core/workflow.xml`
- `mobile-qa-workflow/functionality-deep-dive/core/workflow-model.yaml`
- `mobile-qa-workflow/functionality-deep-dive/core/default-config.yaml`
- `mobile-qa-workflow/functionality-deep-dive/core/workflow-status-template.yaml`
- `mobile-qa-workflow/core/workflow.xml`

#### 具体修改内容

1. 调整专项 `workflow.xml` 的 Agent 调用目标
2. 视验证结果决定：
   - 保留 5 阶段框架但内部复合化
   - 或收敛阶段数量
3. 更新主工作流 `core/workflow.xml` 的专项 I/O 契约
4. 保留旧会话兼容分支，直到验证完成

#### 完成判据

- 主流程与专项流程 I/O 口径一致

---

### C-T4 产物分级改造

#### 涉及文件

- `mobile-qa-workflow/functionality-deep-dive/templates/environment-factor-report.md`
- `mobile-qa-workflow/functionality-deep-dive/templates/deep-dive-topology.md`
- `mobile-qa-workflow/functionality-deep-dive/templates/concurrency-analysis-report.md`
- `mobile-qa-workflow/functionality-deep-dive/templates/functionality-deep-dive-rca.md`
- `mobile-qa-workflow/functionality-deep-dive/templates/deep-dive-summary.md`
- `mobile-qa-workflow/functionality-deep-dive/core/default-config.yaml`
- `mobile-qa-workflow/core/default-config.yaml`
- `mobile-qa-workflow/core/workflow.xml`
- `mobile-qa-workflow/system-prompt.md`

#### 具体修改内容

1. 将以下文件降级为按需落盘：
   - `environment-factor-report.md`
   - `deep-dive-topology.md`
   - `concurrency-analysis-report.md`
2. 将其核心内容沉入：
   - `functionality-deep-dive-rca.md` 附录
   - `deep-dive-summary.md` 摘要
3. 将 config 和主流程 I/O 约束改为可选依赖

#### 完成判据

- 主流程只依赖 `deep-dive-summary.md` 和必要 RCA
- 文件风暴显著降低

---

### C-T5 清理旧专项角色文件引用

#### 涉及文件

- `mobile-qa-workflow/functionality-deep-dive/agents/README.md`
- 延后删除：
  - `context-reconstructor.md`
  - `state-analyst.md`
  - `temporal-analyst.md`
  - `challenger.md`
  - `arbiter.md`

#### 具体修改内容

1. 先用 Grep 确认旧文件不再被任何阶段引用
2. 再更新 README，声明旧文件已废弃
3. 最后再删除旧文件

#### 完成判据

- 旧文件不再被调用
- 删除动作发生在所有路由切换之后

---

### C-T6 全量同步入口与说明文档

#### 涉及文件

- `mobile-qa-workflow/SKILL.md`
- `mobile-qa-workflow/system-prompt.md`
- `mobile-qa-workflow/PLATFORM-GUIDE.md`
- `mobile-qa-workflow/functionality-deep-dive/FUNCTIONALITY_DEEP_DIVE_WORKFLOW_V3.md`
- `doc/B2C_WORKFLOW_SUBAGENT_FINAL_ADOPTION_2026-04-18.md`

#### 具体修改内容

1. 同步新的专项角色拓扑
2. 同步新的产物策略
3. 同步新的 P3/P4 路由矩阵

#### 完成判据

- 文档不再落后于真实实现

---

### C-T7 建设 UI/UX 深度分析（主流程内） 工作流

#### 涉及文件

- 新增 `mobile-qa-workflow/ui-ux-analysis/core/workflow.xml`
- 新增 `mobile-qa-workflow/ui-ux-analysis/core/workflow-model.yaml`
- 新增 `mobile-qa-workflow/ui-ux-analysis/core/default-config.yaml`
- 新增 `mobile-qa-workflow/ui-ux-analysis/phases/*`
- 新增 `mobile-qa-workflow/ui-ux-analysis/agents/*`
- 新增 `mobile-qa-workflow/ui-ux-analysis/templates/*`
- 新增 `mobile-qa-workflow/ui-ux-analysis/reference/*`
- 修改 `mobile-qa-workflow/phases/p3-root-cause.md`
- 修改 `mobile-qa-workflow/core/workflow.xml`
- 修改 `mobile-qa-workflow/system-prompt.md`

#### 具体修改内容

1. 根据现有历史设计资料落地最小可运行的 UI/UX 深度分析（主流程内）
2. 在 `P3` 中加入 UI 专项路由条件
3. 保持与 Functionality Deep-Dive 一致的回注接口

#### 完成判据

- UI 疑难问题有独立专项入口

---

### C-T8 建设评测闭环

#### 涉及文件

- `eval-framework/coordinator.py`
- `eval-framework/comparator.py`
- `eval-framework/scoring_engine.py`
- `eval-framework/quality_gate.py`
- `eval-framework/report_generator.py`
- `eval-framework/configs/*.yaml`
- `eval-cases/seed-10/*` 补充用例或标签

#### 具体修改内容

1. 增加对比维度：
   - `attribution_accuracy`
   - `fix_correctness`
   - `artifact_completeness`
   - `hallucination_interception`
   - 平均单 Case agent 数
2. 增加 P3 / P4 动态 fan-out 的收益统计
3. 增加 Deep-Dive 进入收益比统计
4. 输出 A/B/C 改造前后对比报告

#### 完成判据

- 可以量化判断改造是否真的有效

---

## 5. 推荐提交节奏

## Batch A

1. `A1` 共享 `challenger` 基座
2. `A2` 共享 `arbiter` 基座
3. `A3` 专项 F4 角色闭合
4. `A4` 分类口径文档同步

## Batch B

1. `B1` `P2 + spec.md`
2. `B2` `P3 + analysis-strategies`
3. `B3` `P4 + fix-design + fix-strategies`
4. `B4` `workflow.xml + p6-verification`

## Batch C

1. `C1` 新专项复合角色
2. `C2` 专项阶段切换
3. `C3` 专项编排与产物分级
4. `C4` 文档与入口同步
5. `C5` UI/UX 深度分析（主流程内）
6. `C6` eval 闭环

---

## 6. 完成定义

当以下条件全部满足时，才视为 A0 之后的全部需求完成：

1. 共享基座已上线
2. `P3 / P4 / P6` 动态路由已正式生效
3. 专项角色与阶段已收敛
4. 专项产物已分级
5. `UI/UX 深度分析（主流程内）` 已可运行
6. 评测框架可比较改造前后收益

---

## 7. 使用建议

推荐的实际推进顺序是：

1. 先完成 `Batch A`
2. 确认无恢复兼容问题后推进 `Batch B`
3. 等主链路稳定后再进入 `Batch C`

这样做的原因是：

- `Batch A` 改的是复用和边界，风险最低
- `Batch B` 改的是主链路策略，收益最大但风险高
- `Batch C` 改的是专项产品化和治理闭环，范围最广
