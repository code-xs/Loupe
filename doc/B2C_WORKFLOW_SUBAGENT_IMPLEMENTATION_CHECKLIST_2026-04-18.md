# B2C 移动端质量工作流 SubAgent 改造实施任务清单

> 日期：2026-04-18
> 依据：`doc/B2C_WORKFLOW_SUBAGENT_FINAL_ADOPTION_2026-04-18.md`
> 目标：将最终采纳版落到具体文件、改造步骤、执行顺序与验收标准

---

## 1. 实施原则

1. **先做低风险收敛，再做结构改造。**
2. **先保证主链路稳定，再收缩专项链路。**
3. **先完成路由切换，再清理旧文件。**
4. **所有角色裁剪都必须配合评测验证。**
5. **`system-prompt.md` 与平台入口文档必须同步，避免 Full / Limited 口径分裂。**
6. **任何涉及运行时能力假设的改造，必须先完成引擎兼容性确认。**

---

## 1.1 实施前确认门禁

以下 4 项在进入批次 A / B 前必须完成确认，否则不得直接推进结构改造。

### G-01 动态路由的引擎层支持边界

需要明确：

1. `P2` 输出的 `simple / medium / complex` 如何被后续阶段读取
2. fan-out 的决策点是在阶段文件内完成，还是需要主编排器显式参与
3. 运行时对阶段内多次 `invoke-subagent` 的调用稳定性如何
4. 是否允许通过状态字段驱动 P3 / P4 的重入和升级

当前判断：

- 现有主编排器 `core/workflow.xml` 负责“阶段路由”
- 现有 `p3-root-cause.md` / `p4-fix-design.md` 负责“阶段内 fan-out”
- 因此动态 fan-out 不仅要改 `p3/p4`，还必须补充主编排器对升级、回退和重入状态的支持

### G-02 参数化 Prompt 的运行时支持

需要明确：

1. 平台是否原生支持 `.md` 角色文件中的模板渲染
2. 是否支持类似 `{{ variable }}` 这类模板语法
3. 如果不支持，参数应通过何种方式注入

当前判断：

- 已确认 DSL 与工作流文本普遍使用 `{variable}` 形式传递运行时变量
- 已确认 `invoke-subagent` 的 `subagent_prompt` 必须作为黑盒透传
- **未发现任何证据表明当前运行时支持 Markdown 文件内部的条件模板渲染**

执行要求：

- 批次 A 不采用 `.md` 内部模板渲染作为前提
- 优先采用“共享基座文件 + 调用处显式注入场景参数”的方式
- 若后续确需模板渲染，必须先增加轻量预处理层并单独立项

### G-03 会话恢复与状态版本兼容

需要明确：

1. 工作流状态模板调整后，历史运行中任务如何恢复
2. 阶段名、角色名或状态字段变更后，旧会话如何兼容
3. 专项子工作流改造上线时，是否允许旧流程继续跑完

执行要求：

- 所有状态模板变更必须引入版本字段或兼容映射层
- 在途旧版专项流程必须允许继续完成，不得强制切换到新拓扑
- 旧状态到新状态的迁移规则必须文档化

### G-04 复杂度误判下的熔断与重路由

需要明确：

1. `P2` 的复杂度判定是否允许被 `P3` 或 `P6` 推翻
2. 低复杂度路径失败后，是否可自动升级到重模式
3. 验证失败时，是否能重路由回 `P3` 而不是只回退到 `P4`

执行要求：

- 动态 fan-out 必须配套熔断与重路由机制
- 不允许把复杂度判定设计成一次性、不可回滚决策
- 必须定义“升级触发条件、回写状态字段、重入阶段入口”

---

## 2. 总体实施顺序

### P0：先统一口径和消除重复

0. 完成运行时兼容性确认与门禁检查
1. 共享 `challenger` / `arbiter` 基座
2. 修正专项 F4 对通用 `investigator` 的借用
3. 明确业务角色与能力型 Agent 分类

### P1：再调整执行成本和专项编排

4. 为 P3 / P4 引入动态 fan-out
5. 收敛专项角色到 4~5 个复合角色
6. 调整专项产物策略为“强制独立 + 按需附录”

### P2：最后扩展产品谱系和评测闭环

7. 增补 UI/UX 深度分析（主流程内） 工作流
8. 建立改造前后评测基线与回归对比

---

## 3. 工作包总览

| 编号 | 工作包 | 优先级 | 目标 |
|------|--------|--------|------|
| WP-00 | 运行时兼容性确认 | P0 | 确认动态路由、参数注入、状态恢复的引擎支持边界 |
| WP-01 | 共享 `challenger` 基座 | P0 | 消除主流程与专项流程重复 prompt |
| WP-02 | 共享 `arbiter` 基座 | P0 | 统一仲裁口径与输出契约 |
| WP-03 | 修正专项 F4 角色闭合 | P0 | 取消对通用 `investigator` 的借用 |
| WP-04 | 统一 Agent 分类口径 | P0 | 区分业务角色与能力型 Agent |
| WP-05 | P3 动态 fan-out 改造 | P1 | 把深度 RCA 从默认重模式改为按复杂度升级 |
| WP-06 | P4 动态 fan-out 改造 | P1 | 把多方案设计从默认重模式改为按风险升级 |
| WP-07 | 专项角色收敛改造 | P1 | 将专项角色收敛为 4~5 个复合角色 |
| WP-08 | 专项阶段与编排收敛 | P1 | 让角色结构、阶段结构和子工作流契约一致 |
| WP-09 | 专项产物分级改造 | P1 | 降低文件风暴，保留核心审计产物 |
| WP-10 | 平台入口与文档同步 | P1 | 避免 `SKILL` / `system-prompt` / 平台文档口径漂移 |
| WP-11 | UI/UX 深度分析（主流程内） 预研与落地 | P2 | 补齐 B2C 产品谱系 |
| WP-12 | 评测闭环建设 | P2 | 用指标验证裁剪收益 |

---

## 4. 详细实施清单

## 4.0 WP-00 运行时兼容性确认

### 目标

在进入批次 A / B 前，确认当前工作流引擎是否支持本轮改造所依赖的运行时能力，避免实施方案建立在错误假设上。

### 涉及文件

#### 修改

- `mobile-qa-workflow/core/core-rules.xml`
- `mobile-qa-workflow/core/workflow.xml`
- `mobile-qa-workflow/core/workflow-status-template.yaml`
- `mobile-qa-workflow/functionality-deep-dive/core/workflow.xml`
- `mobile-qa-workflow/functionality-deep-dive/core/workflow-status-template.yaml`
- `mobile-qa-workflow/PLATFORM-GUIDE.md`
- `mobile-qa-workflow/SKILL.md`
- `mobile-qa-workflow/system-prompt.md`

#### 输出文档

- `doc/B2C_WORKFLOW_SUBAGENT_IMPLEMENTATION_CHECKLIST_2026-04-18.md`
- 建议补充一份运行时确认记录文档或附录

### 改造步骤

1. 确认动态 fan-out 的决策位置：
   - 主编排器负责阶段路由
   - 阶段文件负责阶段内 fan-out
2. 确认 `.md` Agent 文件不依赖模板渲染能力
3. 明确共享基座的参数注入方案：
   - 优先通过 `invoke-subagent` 的调用 prompt 注入场景参数
   - 不依赖 `.md` 文件内部条件模板
4. 明确状态模板升级方案：
   - 新增版本号
   - 保留旧字段兼容
   - 增加迁移映射说明
5. 明确动态 fan-out 的失败升级机制：
   - P3 低置信度升级
   - P6 验证失败重路由

### 验收标准

- 动态 fan-out、参数化 prompt、状态恢复三项边界有明确结论
- 批次 A / B 的方案不依赖未验证的运行时特性

---

## 4.1 WP-01 共享 `challenger` 基座

### 目标

将主工作流和专项工作流中的 `challenger` 共性逻辑抽出为共享基座，场景差异改为参数注入。

### 涉及文件

#### 新增

- `mobile-qa-workflow/agents/shared-challenger-base.md`

#### 修改

- `mobile-qa-workflow/agents/challenger.md`
- `mobile-qa-workflow/functionality-deep-dive/agents/challenger.md`
- `mobile-qa-workflow/phases/p3-root-cause.md`
- `mobile-qa-workflow/phases/p4-fix-design.md`
- `mobile-qa-workflow/functionality-deep-dive/phases/f4-isolation-debate.md`
- `mobile-qa-workflow/functionality-deep-dive/agents/README.md`
- `mobile-qa-workflow/system-prompt.md`

### 改造步骤

1. 抽取当前主流程与专项流程 `challenger` 的共性协议：
   - 输入契约
   - 质疑结果格式
   - 置信度影响方式
2. 在 `shared-challenger-base.md` 中定义统一基座：
   - 场景参数
   - 维度集参数
   - 输出格式参数
3. 参数注入方式采用“调用 prompt 显式注入”，不依赖 `.md` 内部模板渲染
3. 将 `agents/challenger.md` 改为主流程包装层：
   - `RCA` 场景使用五维质疑
   - `Fix` 场景使用四重攻击
4. 将 `functionality-deep-dive/agents/challenger.md` 改为专项包装层，或在完成专项收敛后删除并由 `deep-dive-arbiter` 吸收
5. 将 `p3-root-cause.md`、`p4-fix-design.md`、`f4-isolation-debate.md` 的调用 prompt 改为显式传入场景和维度参数
6. 更新专项 Agent 说明文档，避免继续描述“双份独立 challenger”

### 验收标准

- 主流程和专项流程对 `challenger` 的调用都能落到统一基座
- 五维 / 七维 / 四重攻击仍能区分
- 输出格式一致，且不影响现有仲裁流程

---

## 4.2 WP-02 共享 `arbiter` 基座

### 目标

统一主流程和专项流程的裁定协议、置信度校准方式和输出结构。

### 涉及文件

#### 新增

- `mobile-qa-workflow/agents/shared-arbiter-base.md`

#### 修改

- `mobile-qa-workflow/agents/arbiter.md`
- `mobile-qa-workflow/functionality-deep-dive/agents/arbiter.md`
- `mobile-qa-workflow/phases/p3-root-cause.md`
- `mobile-qa-workflow/phases/p4-fix-design.md`
- `mobile-qa-workflow/functionality-deep-dive/phases/f4-isolation-debate.md`
- `mobile-qa-workflow/system-prompt.md`

### 改造步骤

1. 抽取主流程与专项流程 `arbiter` 的共性：
   - 汇总结论
   - 质疑吸收
   - 最终裁定
   - 置信度校准
2. 在 `shared-arbiter-base.md` 中定义：
   - 输入结论集合格式
   - 评分或裁定维度参数
   - 输出模板参数
3. 将主流程 `arbiter.md` 调整为场景包装层：
   - 归因仲裁
   - 修复方案仲裁
4. 参数注入方式采用“调用 prompt 显式注入”，不依赖 `.md` 内部模板渲染
4. 将专项 `arbiter.md` 调整为专项包装层，或在专项角色收敛后并入 `deep-dive-arbiter`
5. 调整三个阶段文件中的调用 prompt，统一基座入口

### 验收标准

- 主流程与专项流程的仲裁逻辑口径一致
- `final_confidence` 的计算口径保持统一
- 不再需要长期维护两套高度同构的裁定 prompt

---

## 4.3 WP-03 修正专项 F4 角色闭合

### 目标

让专项工作流在根因收敛阶段具备自洽的专项角色，不再依赖通用 `investigator`。

### 涉及文件

#### 新增

- `mobile-qa-workflow/functionality-deep-dive/agents/deep-dive-race-and-isolation-analyst.md`

#### 修改

- `mobile-qa-workflow/functionality-deep-dive/phases/f4-isolation-debate.md`
- `mobile-qa-workflow/functionality-deep-dive/agents/README.md`
- `mobile-qa-workflow/functionality-deep-dive/core/workflow.xml`
- `mobile-qa-workflow/functionality-deep-dive/FUNCTIONALITY_DEEP_DIVE_WORKFLOW_V3.md`
- `mobile-qa-workflow/system-prompt.md`

### 改造步骤

1. 新建 `deep-dive-race-and-isolation-analyst.md`，吸收当前 F4 中：
   - 控制变量推演
   - 根因候选排序
   - 时序窗口解释
   - 状态异常闭环验证
2. 把 `f4-isolation-debate.md` 中 `subagent_type="investigator"` 的调用替换为新的专项复合分析角色
3. 去掉“加载 `state-analyst.md` 作为补充视角”的临时拼接方式
4. 更新专项流程说明文档，明确专项 F4 已形成闭合角色体系
5. 校验主工作流回注逻辑不受影响

### 验收标准

- 专项 F4 不再依赖通用 `investigator`
- 专项 RCA 仍能输出 `functionality-deep-dive-rca.md` 和 `deep-dive-summary.md`
- 主工作流 P3 回注专项结论的逻辑保持可用

---

## 4.4 WP-04 统一 Agent 分类口径

### 目标

明确哪些是业务角色，哪些是能力型 Agent，统一设计、评测和文档表达。

### 涉及文件

#### 修改

- `mobile-qa-workflow/PLATFORM-GUIDE.md`
- `mobile-qa-workflow/core/core-rules.xml`
- `mobile-qa-workflow/functionality-deep-dive/agents/README.md`
- `doc/B2C_WORKFLOW_SUBAGENT_FINAL_ADOPTION_2026-04-18.md`
- `mobile-qa-workflow/system-prompt.md`

### 改造步骤

1. 在平台和设计文档中增加两类定义：
   - 业务角色
   - 能力型 Agent
2. 明确 `search` 属于能力型 Agent，不纳入业务角色统计
3. 在 `core-rules.xml` 的人类可读说明区域增加分类说明
4. 将后续所有统计、评测和对外说明统一为同一口径

### 验收标准

- 文档中不再把 `search` 计入核心业务角色数量
- 角色统计口径前后一致

---

## 4.5 WP-05 P3 动态 fan-out 改造

### 目标

将 Phase 3 的深度 RCA 从“默认双 investigator + challenger + arbiter”改为“按复杂度升级”。

### 涉及文件

#### 修改

- `mobile-qa-workflow/core/workflow.xml`
- `mobile-qa-workflow/core/workflow-status-template.yaml`
- `mobile-qa-workflow/core/default-config.yaml`
- `mobile-qa-workflow/phases/p2-spec-definition.md`
- `mobile-qa-workflow/phases/p3-root-cause.md`
- `mobile-qa-workflow/templates/spec.md`
- `mobile-qa-workflow/reference/analysis-strategies.md`
- `mobile-qa-workflow/system-prompt.md`

### 改造步骤

1. 在 `spec.md` 中固化 RCA 复杂度字段：
   - `simple`
   - `medium`
   - `complex`
   - `complexity_confidence`
2. 在 `p2-spec-definition.md` 中补充复杂度判定规则与落盘逻辑
3. 在主编排器 `core/workflow.xml` 中补充 P3 的升级与重入状态处理：
   - 支持从轻模式升级到重模式
   - 支持根因置信度不足时重新进入 P3
   - 支持后续验证阶段触发回流到 P3
4. 在 `workflow-status-template.yaml` 和 `default-config.yaml` 中增加动态路由所需字段，例如：
   - `analysis_complexity`
   - `analysis_complexity_confidence`
   - `fanout_mode`
   - `reroute_reason`
   - `rca_retry_count`
5. 在 `p3-root-cause.md` 中引入新的路由矩阵：
   - `simple` -> 主 Agent 单视角 OVHSC
   - `medium` -> `investigator + challenger`
   - `complex` 或 `证据冲突` -> `2 investigators + challenger + arbiter`
6. 增加熔断升级逻辑：
   - `simple` 模式下若归因置信度低于阈值，自动升级为 `medium` 或 `complex`
   - 若 `challenger` 发现 Critical 级漏洞，强制升级到完整对抗模式
7. 调整 `analysis-strategies.md`，把策略数量与复杂度路由对齐
8. 保留单对话降级路径，避免低能力平台失效

### 验收标准

- `simple` 和部分 `medium` 问题不再默认进入四角色重模式
- `complex` 场景仍保留完整对抗与仲裁机制
- 复杂度误判时可自动升级，不会卡死在低配分析路径
- P3 输出结构不变

---

## 4.6 WP-06 P4 动态 fan-out 改造

### 目标

将 Phase 4 的修复设计从默认双 `fix-proposer` 改为按风险和置信度升级。

### 涉及文件

#### 修改

- `mobile-qa-workflow/core/workflow.xml`
- `mobile-qa-workflow/core/workflow-status-template.yaml`
- `mobile-qa-workflow/core/default-config.yaml`
- `mobile-qa-workflow/phases/p4-fix-design.md`
- `mobile-qa-workflow/phases/p6-verification.md`
- `mobile-qa-workflow/templates/fix-design.md`
- `mobile-qa-workflow/reference/fix-strategies.md`
- `mobile-qa-workflow/system-prompt.md`

### 改造步骤

1. 在主编排器 `core/workflow.xml` 中补充 P4 的回退与重入状态处理：
   - 支持从单方案升级到多方案模式
   - 支持验证失败时根据失败原因回流到 P3 或 P4
2. 在 `workflow-status-template.yaml` 和 `default-config.yaml` 中增加修复设计动态路由所需字段，例如：
   - `fix_strategy_mode`
   - `fix_risk_level`
   - `verification_failure_type`
   - `reroute_target_phase`
3. 在 `p4-fix-design.md` 中引入新的模式矩阵：
   - 高置信度 + 单点改动 -> 单 `fix-proposer`
   - 中置信度 -> `fix-proposer + challenger`
   - 多方案竞争或高风险修改 -> `2 proposers + challenger + arbiter`
4. 调整 `fix-design.md` 模板，兼容：
   - 单方案论证
   - 对抗仲裁方案
5. 调整 `fix-strategies.md`，为单方案和多方案模式分别给出策略提示
6. 在 `p6-verification.md` 中补充失败分类：
   - 设计问题 -> 回流 P4
   - 根因闭环失败 -> 回流 P3 并升级 fan-out
7. 校验进入 `p5-fix-impl.md` 的输入不受影响

### 验收标准

- 低风险问题不再默认触发双 proposer
- 高风险问题仍保留多方案竞争机制
- 验证失败时支持基于失败类型进行重路由，而不是固定回退到 P4
- `fix-design.md` 模板兼容新路由

---

## 4.7 WP-07 专项角色收敛改造

### 目标

将专项链路从当前 6 个细粒度角色收敛为 4~5 个复合角色。

### 涉及文件

#### 新增

- `mobile-qa-workflow/functionality-deep-dive/agents/deep-dive-context-analyst.md`
- `mobile-qa-workflow/functionality-deep-dive/agents/deep-dive-structure-analyst.md`
- `mobile-qa-workflow/functionality-deep-dive/agents/deep-dive-race-and-isolation-analyst.md`
- `mobile-qa-workflow/functionality-deep-dive/agents/deep-dive-arbiter.md`

#### 修改

- `mobile-qa-workflow/functionality-deep-dive/agents/README.md`
- `mobile-qa-workflow/functionality-deep-dive/phases/f1-context-reconstruction.md`
- `mobile-qa-workflow/functionality-deep-dive/phases/f2-state-topology.md`
- `mobile-qa-workflow/functionality-deep-dive/phases/f3-temporal-correlation.md`
- `mobile-qa-workflow/functionality-deep-dive/phases/f4-isolation-debate.md`
- `mobile-qa-workflow/functionality-deep-dive/phases/f5-defensive-fix-design.md`
- `mobile-qa-workflow/functionality-deep-dive/FUNCTIONALITY_DEEP_DIVE_WORKFLOW_V3.md`
- `mobile-qa-workflow/system-prompt.md`

#### 延后清理

- `mobile-qa-workflow/functionality-deep-dive/agents/context-reconstructor.md`
- `mobile-qa-workflow/functionality-deep-dive/agents/state-analyst.md`
- `mobile-qa-workflow/functionality-deep-dive/agents/temporal-analyst.md`
- `mobile-qa-workflow/functionality-deep-dive/agents/challenger.md`
- `mobile-qa-workflow/functionality-deep-dive/agents/arbiter.md`

### 改造步骤

1. 新建 4 个专项复合角色文件
2. 将旧角色能力映射到新角色：
   - `context-reconstructor` -> `deep-dive-context-analyst`
   - `state-analyst` -> `deep-dive-structure-analyst`
   - `temporal-analyst` + F4 隔离推演 -> `deep-dive-race-and-isolation-analyst`
   - `challenger` + `arbiter` -> `deep-dive-arbiter`
3. 先保留旧文件，不立即删除；等所有阶段路由切换完成后再清理
4. 更新专项说明文档与 Agent 列表

### 验收标准

- 专项运行角色收敛到目标结构
- 旧文件不再被实际编排调用
- `defensive-fix-architect` 仍保留按需触发能力

---

## 4.8 WP-08 专项阶段与编排收敛

### 目标

让专项子工作流的阶段结构、I/O 契约和角色结构保持一致。

### 涉及文件

#### 修改

- `mobile-qa-workflow/functionality-deep-dive/core/workflow.xml`
- `mobile-qa-workflow/functionality-deep-dive/core/workflow-model.yaml`
- `mobile-qa-workflow/functionality-deep-dive/core/default-config.yaml`
- `mobile-qa-workflow/functionality-deep-dive/core/workflow-status-template.yaml`
- `mobile-qa-workflow/core/workflow.xml`
- `mobile-qa-workflow/core/default-config.yaml`

### 改造步骤

1. 先完成角色切换，再调整专项 `workflow.xml` 的调用目标
2. 重新定义专项阶段序列：
   - 可以保持 5 阶段框架不变，但内部改为复合角色
   - 或在验证稳定后收敛到更少阶段
3. 为主工作流和专项工作流状态模板增加版本字段，例如：
   - `workflow_version`
   - `schema_version`
4. 增加旧状态兼容映射：
   - 旧阶段名到新阶段名
   - 旧角色产物到新产物依赖
5. 明确在途会话兼容策略：
   - 旧版专项会话允许按旧流程继续完成
   - 新会话使用新拓扑
6. 调整专项 `default-config.yaml`：
   - 让中间产物字段支持可选输出
7. 调整主工作流 `core/workflow.xml` 的专项 I/O 说明，确保主流程只依赖稳定产物
8. 确保状态恢复逻辑与阶段名称同步

### 验收标准

- 专项阶段定义与实际角色调用一致
- 主工作流对专项产物的读取不依赖已降级的中间文件
- 子工作流恢复能力正常
- 在途旧版专项任务不会因新状态模板上线而失效

---

## 4.9 WP-09 专项产物分级改造

### 目标

将专项产物分为“强制独立交付物”和“按需附录”，减少文件风暴。

### 涉及文件

#### 修改

- `mobile-qa-workflow/functionality-deep-dive/templates/environment-factor-report.md`
- `mobile-qa-workflow/functionality-deep-dive/templates/deep-dive-topology.md`
- `mobile-qa-workflow/functionality-deep-dive/templates/concurrency-analysis-report.md`
- `mobile-qa-workflow/functionality-deep-dive/templates/functionality-deep-dive-rca.md`
- `mobile-qa-workflow/functionality-deep-dive/templates/deep-dive-summary.md`
- `mobile-qa-workflow/functionality-deep-dive/core/default-config.yaml`
- `mobile-qa-workflow/core/default-config.yaml`
- `mobile-qa-workflow/core/workflow.xml`
- `mobile-qa-workflow/system-prompt.md`

### 改造步骤

1. 将以下产物改为按需输出：
   - `environment-factor-report.md`
   - `deep-dive-topology.md`
   - `concurrency-analysis-report.md`
2. 将这些内容优先沉入：
   - `functionality-deep-dive-rca.md` 附录
   - `deep-dive-summary.md` 摘要
3. 调整 `default-config.yaml`，将对应路径标记为可选
4. 调整 `core/workflow.xml` 的 I/O 契约描述，避免把可选产物写成固定依赖

### 验收标准

- 主流程只依赖稳定必要产物
- 专项仍能在需要时独立落盘分析报告
- 普通复杂 Case 的文件数量明显下降

---

## 4.10 WP-10 平台入口与文档同步

### 目标

确保 Full / Limited / 文档说明对新架构口径一致。

### 涉及文件

#### 修改

- `mobile-qa-workflow/SKILL.md`
- `mobile-qa-workflow/system-prompt.md`
- `mobile-qa-workflow/PLATFORM-GUIDE.md`
- `mobile-qa-workflow/FUNCTIONALITY_DEEP_DIVE_WORKFLOW_V3.md`
- `doc/B2C_WORKFLOW_SUBAGENT_FINAL_ADOPTION_2026-04-18.md`

### 改造步骤

1. 更新 `SKILL.md` 的工作流说明与角色说明
2. 更新 `system-prompt.md` 中内联的角色、阶段、产物和路由规则
3. 更新 `PLATFORM-GUIDE.md` 中的角色与平台说明
4. 更新专项说明文档，反映新的专项角色结构和产物策略

### 验收标准

- Full 平台和 Limited 平台行为说明一致
- 文档中不再出现旧专项角色拓扑的主叙述

---

## 4.11 WP-11 UI/UX 深度分析（主流程内） 预研与落地

### 目标

补齐当前只覆盖功能疑难、不覆盖 UI 疑难的问题。

### 涉及文件

#### 新增

- `mobile-qa-workflow/ui-ux-analysis/core/workflow.xml`
- `mobile-qa-workflow/ui-ux-analysis/core/workflow-model.yaml`
- `mobile-qa-workflow/ui-ux-analysis/core/default-config.yaml`
- `mobile-qa-workflow/ui-ux-analysis/phases/*`
- `mobile-qa-workflow/ui-ux-analysis/agents/*`
- `mobile-qa-workflow/ui-ux-analysis/templates/*`
- `mobile-qa-workflow/ui-ux-analysis/reference/*`

#### 修改

- `mobile-qa-workflow/phases/p3-root-cause.md`
- `mobile-qa-workflow/core/workflow.xml`
- `mobile-qa-workflow/system-prompt.md`

### 改造步骤

1. 定义 UI 疑难的触发条件
2. 设计 UI/UX 深度分析（主流程内） 的最小闭环角色与产物
3. 在 P3 中补充专项路由入口
4. 与 Functionality Deep-Dive 保持一致的编排和回注接口

### 验收标准

- UI 疑难场景具备独立专项分析链路
- 不影响现有功能疑难链路

---

## 4.12 WP-12 评测闭环建设

### 目标

用评测数据验证改造是否真的降低成本且不损伤质量。

### 涉及文件

#### 修改

- `eval-framework/coordinator.py`
- `eval-framework/comparator.py`
- `eval-framework/scoring_engine.py`
- `eval-framework/quality_gate.py`
- `eval-framework/report_generator.py`
- `eval-framework/configs/*.yaml`

#### 新增或补充

- `eval-cases/` 中覆盖：
  - 简单功能问题
  - 中等复杂功能问题
  - 高复杂度状态机问题
  - 生命周期竞态问题
  - 低收益 deep-dive 误触发问题

### 改造步骤

1. 增加改造前后链路对比维度：
   - `attribution_accuracy`
   - `fix_correctness`
   - `artifact_completeness`
   - `hallucination_interception`
   - 平均单 Case 调用 Agent 数
2. 增加 Deep-Dive 触发收益统计
3. 增加 P3 / P4 动态 fan-out 的收益评估
4. 为专项角色收敛建立 A/B 对比报告

### 验收标准

- 可以量化对比改造前后质量与成本
- 可以判断哪些裁剪有效，哪些需要回退

---

## 5. 推荐执行批次

## 批次 A：一周内可完成

- WP-00 运行时兼容性确认
- WP-01 共享 `challenger` 基座
- WP-02 共享 `arbiter` 基座
- WP-03 修正专项 F4 角色闭合
- WP-04 统一 Agent 分类口径

## 批次 B：主链路成本优化

- WP-05 P3 动态 fan-out 改造
- WP-06 P4 动态 fan-out 改造

## 批次 C：专项链路收敛

- WP-07 专项角色收敛改造
- WP-08 专项阶段与编排收敛
- WP-09 专项产物分级改造
- WP-10 平台入口与文档同步

## 批次 D：中长期增强

- WP-11 UI/UX 深度分析（主流程内） 预研与落地
- WP-12 评测闭环建设

---

## 6. 风险与注意事项

1. **不要在共享基座落地前直接删除旧专项 `challenger` / `arbiter` 文件。**
2. **不要在主流程 I/O 契约调整前就把专项中间产物彻底删掉。**
3. **不要在 `system-prompt.md` 未同步前只修改 Full 平台文件。**
4. **不要把专项角色一次性压成单一大 Agent。**
5. **角色裁剪完成后必须跑评测，再决定是否继续删除旧文件。**
6. **不要假设 `.md` Agent 文件原生支持条件模板渲染。**
7. **不要只改 `p3/p4` 而忽略主编排器对升级、重入和回退状态的支持。**
8. **不要在没有版本兼容层的情况下直接改写状态模板结构。**
9. **不要把复杂度判定设计成一次性不可回滚决策。**

---

## 7. 最终交付物

本轮改造完成后，至少应形成以下交付物：

1. 一套共享 `challenger` / `arbiter` 基座
2. 一套新的专项复合角色定义
3. 一版支持动态 fan-out 的 P3 / P4
4. 一版新的专项产物分级策略
5. 一套同步后的平台入口与架构说明文档
6. 一份评测对比报告，证明改造收益
