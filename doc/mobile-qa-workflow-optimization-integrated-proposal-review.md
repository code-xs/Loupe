# Mobile QA 工作流优化整合方案 — 深度审查报告

## 一、总体评价

本方案是当前移动端 AI QA 领域中少见的、从"推理质量"层面深入到"上下文质量"层面的系统性设计。方案的核心洞察——**归因失真的主因不是推理链不够强，而是进入推理链的上下文已被污染**——精准命中了大型移动端工程中 AI 辅助排障的核心瓶颈。

三条顶层原则（边界优先于搜索、净化优先于推理、动态路径优先于静态相似性）方向正确、逻辑自洽。与现有工程的兼容性良好，可以嵌入 `p1/p2/p3` 而不需要推翻现有架构。

**但方案在从"设计蓝图"到"可稳定运行的系统"之间，仍存在若干结构性缺陷和落地盲区。** 以下逐一分析。

---

## 二、方案与现有工程架构的精确映射与兼容性分析

### 2.1 现有架构关键约束

当前工程的核心架构特征：

| 维度 | 现状 | 方案影响 |
|---|---|---|
| 阶段数 | 6 阶段（intake → spec → rca → fix-design → fix-impl → verification） | 方案建议增加准阶段或中间状态，需评估对状态机的影响 |
| Agent 数 | 4 个（investigator / challenger / arbiter / fix-proposer） | 方案新增 Curator，需定义 Agent 文件和调用协议 |
| 路由机制 | `p3` 单层路由：`complexity_level → fast/deep` | 方案改为双层路由：`boundary → fast/deep`，需重构 `p3` step 4 |
| 证据模型 | 一维：A/B/C | 方案改为二维：Reliability(A/B/C) × Liveness(Live/Suspect/Dead) |
| 状态机 | 7 个状态（Intake/Spec-Defining/RCA-InProgress/Fix-Designing/Fix-Implementing/Verifying/Closed + 异常状态） | 方案增加 Context-Curating 等中间状态 |
| 降级模式 | `env_subagent == false` 时单对话顺序模拟 | 方案未覆盖此降级场景 |

### 2.2 兼容性结论

方案与现有架构**不冲突但需要补充**。关键补充点：

1. `workflow.xml` 的 `io-contract` 需要扩展（新增 `context-curation-report.md`）
2. `core-rules.xml` 的 `available-agents` 需要增加 `curator`
3. `workflow-status-template.yaml` 需要新增边界相关字段
4. `system-prompt.md` 需要同步更新（这是一份完整内联版本，工作量不小）

---

## 三、结构性缺陷与盲区

### 缺陷 1：Context Curator 缺少 Agent 定义文件和调用协议

**现状**：当前 `agents/` 目录下有 4 个 Agent 定义文件（investigator.md、challenger.md、arbiter.md、fix-proposer.md），每个都有明确的 Role/Capabilities/Constraints/Output Format。

**问题**：方案定义了 Curator 的职责（§6.2）和输出契约（§6.3），但没有提供：
- `agents/curator.md` 的完整定义
- Curator 在 `core-rules.xml` 的 `available-agents` 中的注册
- Curator 的 `invoke-subagent` 调用方式
- Curator 与 Investigator 的数据传递协议

**风险**：没有 Agent 定义文件，Curator 在实际执行时会被主 Agent "内联执行"而非作为独立 Agent 运行，导致策展逻辑与推理逻辑混在一起，违背了方案"把找什么能被分析和如何分析拆开"的初衷。

**建议**：补充完整的 `agents/curator.md`，至少包含：
- Role 定义（与现有 Agent 格式对齐）
- Capabilities：5 项策展职责的执行协议
- Constraints：禁止做 RCA、必须输出结构化报告、误杀保护规则
- Output Format：与 §6.3 契约对齐的 Markdown 模板
- 在 `core-rules.xml` 的 `available-agents` 中注册 `<agent name="curator" scenario="策展">上下文净化、存活性校验、配置掩码</agent>`

---

### 缺陷 2：边界判定协议缺少决策算法和冲突处理

**现状**：方案 §5 定义了边界判定的输入特征和输出结构，但缺少关键的决策逻辑。

**问题 1：判定算法未定义**。当输入特征存在矛盾时如何判定？例如：
- 用户提供了版本区间（倾向 `VERSION_RANGE`），但同时提到了"可能是某个 MR 引入的"（倾向 `EXACT_MR`）
- 用户说"一直有这个问题"（倾向 `HISTORICAL_UNCLEAR`），但日志显示首次出现在 v2.1（倾向 `VERSION_RANGE`）

方案提到 `Boundary_Confidence` 和 `Boundary_Alternative`，但没有定义：
- 置信度的计算方式（是离散的 High/Medium/Low，还是连续的 0-1 分数？）
- 主选与备选之间的切换阈值
- 多信号冲突时的优先级规则

**问题 2：边界等级的动态迁移未处理**。在分析过程中，新证据可能改变边界判定。例如：
- `VERSION_RANGE` 场景下，commit 排序后锁定到某个 MR → 应升级为 `EXACT_MR`
- `HISTORICAL_UNCLEAR` 场景下，补证后获得版本区间 → 应升级为 `VERSION_RANGE`

当前 `p3-root-cause.md` 的步骤是线性的，没有"回溯更新边界"的机制。

**建议**：
1. 定义边界判定的决策树或评分模型，至少明确以下规则：
   - 存在明确 MR/PR 链接 → `EXACT_MR`，置信度 High
   - 存在版本起止点但无 MR → `VERSION_RANGE`，置信度由版本区间宽度决定
   - 仅有"一直有问题"描述 → `HISTORICAL_UNCLEAR`，置信度由动态锚点数量修正
   - 多信号冲突时，取**最窄有效边界**作为主选，次窄作为备选
2. 在 `p3` 中增加"边界回溯"步骤：当分析过程中发现更精确的边界证据时，允许更新 `Issue_Boundary_Level` 并重新路由

---

### 缺陷 3：单对话降级模式完全未覆盖

**现状**：`p3-root-cause.md` step 5 对 `env_subagent == false` 有完整的降级方案——顺序模拟 Investigator-A/B → Challenger → Arbiter。`analysis-strategies.md` §末尾也有"无多 Agent 能力时的降级处理"。

**问题**：方案新增的 Curator、增强的 Challenger（7 维质疑）、边界驱动路由、commit 排序等机制，全部没有单对话降级方案。这意味着：
- 在不支持子 Agent 的平台（Dify、Coze、纯 Chat 对话）上，这些增强全部失效
- `system-prompt.md` 作为独立部署版本，需要同步更新但方案未提及

**建议**：
1. 为 Curator 设计单对话降级模式：在 `p2` 的证据收集步骤中，由主 Agent 顺序执行策展 checklist（而非独立 Agent），输出仍为 `context-curation-report.md`
2. 为 Challenger 的 2 个新质疑维度（Temporal Drift / Activation）补充到单对话降级模板中
3. 明确 `system-prompt.md` 的同步更新计划

---

### 缺陷 4：Curator 的执行时机与 p2 证据收集存在时序冲突

**现状**：`p2-spec-definition.md` 的步骤序列是：
1. 加载上游产物
2. 填写 Spec 三要素
3. 加载分类扩展模块
4. Spec 校准
5. 非 Bug 判定
6. **证据收集与可信度分级**
7. 输出 Spec + Context Bundle

**方案建议**（§10.2）：在"证据收集与可信度分级"之前插入 Context Curation。

**问题**：Curator 需要对候选上下文做存活性校验、配置掩码、运行时映射，但这些操作的前提是**上下文已经被收集**。如果 Curator 在证据收集之前运行，它没有输入；如果在之后运行，证据已经按旧的 A/B/C 分级了，Curator 的二维分级（Reliability × Liveness）需要回溯修正。

**建议**：将 p2 的证据处理拆分为三个子步骤：
1. **证据收集**（原 step 6 前半）：搜集所有候选证据和代码定位
2. **Context Curation**（新增）：对收集到的候选做策展，输出 `context-curation-report.md`
3. **证据分级与 Context Bundle 生成**（原 step 6 后半 + step 7）：基于策展结果，使用二维分级模型生成最终的 `context-bundle.md`

这样 Curator 有了输入，且分级在策展之后，逻辑通顺。

---

### 缺陷 5：二维证据模型（Reliability × Liveness）与现有置信度计算公式不兼容

**现状**：`reasoning-chain.md` 的置信度计算公式为：

```
正向得分 = SUM(证据权重: A=1.0/B=0.7/C=0.4)
```

**方案建议**（§6.4）：证据等级从一维升级为二维——Reliability(A/B/C) × Liveness(Live/Suspect/Dead)。

**问题**：这会产生 9 种组合（A-Live, A-Suspect, A-Dead, B-Live, ...），但现有公式只处理 3 种。方案没有定义：
- 每种组合的权重系数是什么？
- `Dead` 证据是否应该完全排除（权重=0）还是降权？
- `Suspect` 证据在什么条件下可以升级为 `Live`？
- 这对 `final_confidence = base_score × convergence_factor × challenge_survival_rate` 公式有何影响？

**建议**：定义完整的权重矩阵：

| Reliability \ Liveness | Live | Suspect | Dead |
|---|---|---|---|
| A | 1.0 | 0.7 | 0.2（仅作排除性参考） |
| B | 0.7 | 0.5 | 0.1 |
| C | 0.4 | 0.2 | 0.0（不进入推理链） |

并明确规则：
- `Dead` 证据不参与正向得分计算，但可在 CHAIN 步骤中作为"已排除路径"的标注
- `Suspect` 证据需要附带升级条件说明
- 仅由 `Suspect` 及以下证据支撑的假设，置信度上限为 0.5

---

### 缺陷 6：`HISTORICAL_UNCLEAR` 的受控搜索模式缺少具体搜索协议

**现状**：方案 §7.2 提出了"受控搜索模式"的概念——允许搜索但必须从现场锚点出发，搜索结果仅作补证引导。方向正确，但缺少可执行的搜索协议。

**问题**：
- "现场锚点"具体指什么？错误码、埋点名、页面文案、路由名、请求字段——这些的搜索方式完全不同
- 搜索结果的"补证引导"角色如何在工作流中体现？是写入 `context-bundle.md` 的独立区块，还是标记为特殊证据等级？
- 搜索深度如何控制？一次搜索允许返回多少候选？允许递归搜索几层？

**建议**：定义受控搜索的三层协议：

```
第一层：锚点提取
  从动态证据中提取可搜索的原子锚点：
  - 错误码/错误信息 → Grep 全局搜索
  - 埋点事件名 → Grep + 调用图搜索
  - 页面路由名 → 路由表反查 + Grep
  - 请求 URL/字段名 → 网络层代码搜索
  - UI 文案 → strings.xml / Localizable.strings 搜索

第二层：候选收集
  每个锚点最多返回 5 个候选代码位置
  候选必须标注与锚点的映射关系

第三层：候选过滤
  候选代码必须满足至少一项：
  - 被 Crash 栈/日志直接引用
  - 在调用链上可达栈顶方法
  - 在 Feature Flag 当前配置下可激活
  不满足任何一项的候选 → 标记为 Suspect，不进入主推理链
```

---

### 缺陷 7：Config Snapshot Metadata 的工程可行性被高估

**现状**：方案 §7.4 定义了 5 个配置快照字段（Config_Snapshot_Timestamp / Flag_Scope / Flag_Source / Flag_Staleness / Mask_Decision_Reason）。

**问题**：在真实的移动端工程中，获取"报障时刻的配置快照"面临以下困难：
- 大多数 APM/Feature Flag 平台不提供历史配置查询 API
- 客户端本地配置可能已被覆盖，无法回溯
- 服务端配置的生效时间与客户端拉取时间存在延迟
- 灰度配置的命中逻辑可能涉及多层嵌套（用户标签 × 地区 × 版本 × 实验组）

如果把这些字段设为"必填"，大量实际问题会因为无法获取而卡在 Curator 阶段。

**建议**：
1. 将 Config Snapshot Metadata 分为两级：
   - **必需级**：`Mask_Decision_Reason`（每次掩码操作必须记录理由）
   - **最佳努力级**：其余 4 个字段，能获取则填，不能获取则标 `[Config-Snapshot-Unavailable]`
2. 当配置快照不可用时，Curator 应采用**保守掩码策略**：不因"当前 Flag 为 false"而剔除代码，而是将其标记为 `Suspect` 而非 `Dead`
3. 在 Challenger 的 Activation 质疑中，当配置快照缺失时，应将"路径是否被激活"标记为 `[Uncertain]` 而非直接否定

---

### 缺陷 8：方案未考虑对 p4/p5/p6 阶段的连锁影响

**现状**：方案的改造建议（§10）只覆盖了 p1/p2/p3 和 workflow.xml，但边界感知路由和上下文策展对下游阶段有连锁影响。

**具体影响**：

1. **p4-fix-design**：如果 RCA 报告中包含了 `Remote_Drift_Suspected` 标记，修复方案可能不是改客户端代码，而是协调服务端变更或配置调整。当前 `p4-fix-design.md` 的修复策略池（精准修复/输入校验/状态隔离/降级兜底/配置修复/架构调整）没有覆盖"跨端协调修复"策略。

2. **p5-fix-impl**：如果根因指向远端漂移而非客户端代码缺陷，当前 `p5-fix-impl.md` 的"代码修改"步骤可能不适用，需要增加"非代码修复"分支（如配置变更、服务端协调）。

3. **p6-verification**：如果修复方案涉及远端变更，当前 `p6-verification.md` 的 L1/L2/L3 验证体系需要扩展——静态代码走查无法验证远端变更的效果。

**建议**：在方案中增加 §10.5-10.7，明确 p4/p5/p6 需要的适配改造，至少包括：
- p4 增加"远端协调修复"策略类型
- p5 增加"非代码修复"实施路径
- p6 增加"远端变更验证"标注

---

### 缺陷 9：度量体系缺少基线测量和 A/B 测试设计

**现状**：方案 §13 定义了 6 个度量指标，方向正确，但缺少：
- 当前系统的基线数据（没有基线就无法证明改进效果）
- A/B 测试设计（如何对比优化前后的效果）
- 指标的采集方式（从哪里取数、由谁计算）

**建议**：
1. 在实施 P0 改造之前，先对现有工作流跑一轮基线测量，至少收集：
   - 当前 `False Context Rate` 的估算（可通过人工复盘最近 20 个 RCA 报告）
   - 当前 `RCA Rework Rate`（统计被回流重做的报告比例）
   - 当前 `Human Escalation Quality`（人工复核时 AI 是否已收缩范围）
2. 设计 A/B 对照：同一批问题分别用旧流程和新流程分析，对比归因准确性
3. 指标采集应尽量自动化——在 `rca-report.md` 模板中增加"引用上下文清单"区块，便于事后审计

---

### 缺陷 10："双轨低成本验证"未定义具体协议

**现状**：方案 §5.4 提到"当 Boundary_Confidence 低时，不直接信任单一路径，应采用双轨低成本验证"。

**问题**：
- "双轨"指什么？同时按两种边界等级执行分析？
- "低成本"如何保证？同时跑两条路径的 token 消耗可能翻倍
- 两条路径的结果如何合并？由谁裁定？
- 什么条件下退出双轨模式？

**建议**：定义双轨验证协议：

```
触发条件：Boundary_Confidence == Low（或主选与备选边界等级不同）

执行方式：
  轨道 A：按主选边界等级执行快速路径分析（仅 OVHSC，不启动多 Agent 对抗）
  轨道 B：按备选边界等级执行快速路径分析

合并规则：
  若两轨结论一致 → 采信结论，Boundary_Confidence 升级为 Medium
  若两轨结论不一致 → 不做选择，输出双轨对比报告，进入 Human-Review

成本控制：
  双轨模式仅使用快速路径（单视角 OVHSC），不启动深度路径
  总 token 消耗约为单轨深度路径的 60%
```

---

## 四、方案中设计优秀但需强化的部分

### 4.1 边界驱动路由 — 最有价值的设计点，但需要"边界回溯"机制

方案将 `Issue_Boundary_Level` 作为 p3 的第一层路由，这是整个方案最核心的贡献。但当前设计是**静态的**——边界在 p1 判定后不再变化。

实际上，在 `VERSION_RANGE` 场景下，commit 排序可能锁定到具体 MR；在 `HISTORICAL_UNCLEAR` 场景下，受控搜索可能发现版本线索。**边界等级应该允许在分析过程中被精化**。

建议在 p3 的 OVHSC 推理链中增加一个隐式步骤：如果 VERIFY 阶段发现了更精确的边界证据，允许回溯更新 `Issue_Boundary_Level` 并调整分析策略。

### 4.2 Challenger 增强 — 方向正确，但需要与现有五维协议整合

方案建议增加 `Temporal Drift Challenge` 和 `Activation Challenge`，这两个维度确实命中了移动端高频误判场景。但直接从 5 维扩展到 7 维需要考虑：

- 现有 `challenger.md` 的 Constraints 要求"逐条执行所有维度的质疑，不得遗漏"。7 维意味着每条质疑的工作量增加 40%。
- 在单对话降级模式下，7 维质疑的 token 消耗可能超出预算。

建议：
- 将 7 维分为**核心 5 维**（始终执行）和**条件 2 维**（仅在特定场景触发）
- 触发条件：`Temporal Drift` 仅在 `HISTORICAL_UNCLEAR` 或代码无近期变更时触发；`Activation` 仅在存在 Feature Flag / AB 实验相关代码时触发
- 这样既保证了关键场景的覆盖，又控制了常规场景的成本

### 4.3 Commit 排序模型 — 设计合理，但需要与现有策略池整合

方案 §8.2 的多信号 commit 排序模型（文本/结构/时序/责任/动态）设计合理，但当前 `analysis-strategies.md` 的 `Strategy-Regression` 策略只描述了"从 git log/blame 出发"，没有 commit 排序的具体协议。

建议将 commit 排序模型作为 `Strategy-Regression` 的增强版定义，明确：
- 5 类信号的权重分配（建议：结构信号 30% > 动态信号 25% > 时序信号 20% > 文本信号 15% > 责任信号 10%）
- 排序输出的格式（带分数和命中理由的候选排名）
- 与 `VERSION_RANGE` 路由的绑定关系

---

## 五、落地可行性与工程风险评估

### 5.1 P0 改造范围过大

方案 §14.1 将 4 项改造列为 P0，但每项的实际工作量都不小：

| P0 项 | 涉及文件 | 预估影响 |
|---|---|---|
| 边界判定元数据 + Intake 门禁 | p1-intake.md, issue-card.md, workflow-status-template.yaml, intake-form.md, system-prompt.md | 新增步骤 + 模板扩展 |
| Curator 子步骤 + 结构化输出 | **新增** agents/curator.md, context-curation-report.md 模板; 修改 p2-spec-definition.md, core-rules.xml, context-bundle.md | 新增 Agent + 阶段重构 |
| 边界路由提升为 p3 第一层决策 | p3-root-cause.md 步骤重构 | 路由逻辑重写 |
| workflow.xml 显式记录策展状态 | workflow.xml, workflow-status-template.yaml | 状态机扩展 |

**风险**：一次性改造 4 项，任何一项出问题都会影响整体稳定性。

**建议**：将 P0 进一步拆分为 P0-A 和 P0-B：

- **P0-A（最小可行增量）**：仅增加边界判定元数据和 Intake 门禁，不改 p3 路由逻辑。边界等级作为"信息标注"存在，供人工参考。
- **P0-B（路由生效）**：在 P0-A 稳定后，将边界等级接入 p3 路由，并增加 Curator。

这样即使 P0-B 出问题，P0-A 的边界标注仍然有价值。

### 5.2 Curator 可能成为新的误判源

Curator 的核心风险是**误杀活代码**。如果 Curator 因为配置快照不可用而错误地将某段代码标记为 `Dead`，后续推理将完全错过真实根因。这比"上下文有噪声"更危险——噪声可以被 Challenger 质疑，但缺失的上下文无法被质疑。

**建议**：为 Curator 增加**误杀保护规则**：
1. 任何被剔除的上下文必须保留在 `pruned_contexts` 中，不可物理删除
2. 如果 Investigator 的所有假设都无法解释观察到的现象，自动触发"策展回溯"——从 `pruned_contexts` 中恢复被剔除的候选项
3. Curator 的剔除操作必须有明确的 `prune_reason`，且每个 reason 必须可被人工审计

### 5.3 system-prompt.md 的同步更新成本

`system-prompt.md` 是一份 400+ 行的完整内联版本，将所有工作流逻辑、模板、参考知识全部写在一个文件中。方案的任何改造都需要同步更新这个文件，且由于它是自包含的，更新时容易与模块化版本不一致。

**建议**：
1. 在方案中明确 `system-prompt.md` 的更新责任和验证机制
2. 考虑增加自动化校验：对比 `system-prompt.md` 与模块化文件的差异，确保一致性

---

## 六、补充优化建议

### 建议 1：增加"边界等级迁移"的状态机路径

当前状态机没有"边界精化"的路径。建议在 `workflow.xml` 中增加：

```
RCA-InProgress → Boundary-Refined → RCA-InProgress
  （条件：分析过程中发现更精确的边界证据）
```

这允许 p3 在不回退到 p1 的情况下更新边界等级。

### 建议 2：为 Curator 增加"策展置信度"门禁

Curator 输出的 `curation_confidence` 应该有门禁：
- `curation_confidence >= 0.7`：策展结果可信，进入 RCA
- `0.4 <= curation_confidence < 0.7`：策展结果部分可信，标记 `[Curation-Partial]`，进入 RCA 但 Challenger 需额外质疑策展质量
- `curation_confidence < 0.4`：策展失败，回退 `Info-Insufficient` 或进入 `Human-Review`

### 建议 3：在 knowledge-card 中增加边界路由模式沉淀

当前 `knowledge-card.md` 模板没有边界路由相关字段。建议增加：
- `boundary_level`：该案例的边界等级
- `curation_patterns`：策展过程中发现的典型噪声模式（如"XX 模块存在 3 个平行实现"）
- `routing_effectiveness`：边界路由是否有效收缩了搜索空间

这将为未来的边界判定提供历史参考，逐步提升 `Boundary_Confidence` 的准确性。

### 建议 4：为 `VERSION_RANGE` 场景增加"版本对比清单"模板

方案提到"提供正常/异常版本对比提示"，但没有定义模板。建议在 `context-bundle.md` 中增加：

```markdown
### 版本对比清单（VERSION_RANGE 专项）
| 维度 | 正常版本 | 异常版本 | 差异摘要 |
|---|---|---|---|
| 版本号 | v1.2 | v1.3 | - |
| 代码变更量 | - | N files, M commits | - |
| 依赖变更 | - | SDK X 升级到 Y | - |
| 配置变更 | - | Flag Z 从 true 变为 false | - |
| 服务端变更 | - | API W 新增字段 | - |
```

### 建议 5：增加"远端漂移分析"作为 p3 的显式步骤

方案 §8.3 提到 `HISTORICAL_UNCLEAR` 必须"内建远端/外部依赖漂移分析轴"，但这只是文字描述，没有成为 p3 的显式步骤。

建议在 p3 的 step 6（客户端-服务端边界判定）中扩展：

```
原：仅功能类/网络类触发
改：功能类/网络类 + HISTORICAL_UNCLEAR + Remote_Drift_Suspected=true 均触发

原：三步法（抓包 → 判定归属 → Handoff）
改：四步法（抓包 → 判定归属 → 漂移检查 → Handoff/继续分析）

新增"漂移检查"：
  - 服务端 schema 是否近期变更？
  - 灰度配置是否近期调整？
  - 第三方 SDK 是否近期升级？
  - 系统行为是否近期变化（如 Android 版本更新）？
```

---

## 七、综合评分

| 维度 | 评分 | 评价 |
|---|---:|---|
| 核心洞察准确性 | 9.5/10 | "上下文污染是归因失真的主因"这一判断极为精准 |
| 方法论先进性 | 9/10 | 边界感知路由 + 上下文策展 + 动态锚定，体系完整 |
| 与现有架构兼容性 | 7.5/10 | 可嵌入但需补充 Agent 定义、降级模式、IO 契约 |
| 工程可实施性 | 6/10 | P0 范围过大、Curator 缺 Agent 定义、降级模式缺失 |
| 风险控制完整性 | 6.5/10 | 误杀保护不足、配置快照可行性被高估、下游阶段未覆盖 |
| 度量与验证体系 | 6/10 | 指标定义好但缺基线和 A/B 设计 |

---

## 八、最终建议

方案的核心方向完全正确，三条顶层原则应作为下一版 Mobile QA Workflow 的设计基石。但在落地路径上，我建议：

1. **先做 P0-A**（边界标注 + Intake 门禁），验证边界判定协议的准确性
2. **再做 P0-B**（Curator + 路由生效），补齐 Agent 定义和降级模式
3. **同步建立基线**，用真实 case 回放验证改进效果
4. **P1 增强时优先做 Challenger 扩展和受控搜索**，这两项对归因准确性的提升最直接

**一句话总结**：方案把"让 AI 在更小、更真、更可审计的上下文上推理"这个核心命题讲透了，但还需要把"如何确保上下文确实更小更真"的工程协议补全——特别是 Curator 的完整定义、边界判定的决策算法、单对话降级模式、以及误杀保护机制。
