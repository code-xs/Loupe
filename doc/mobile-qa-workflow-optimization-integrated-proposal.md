# Mobile QA 工作流复杂问题归因优化整合方案

## 1. 文档目标

本文将原始优化分析与审查意见整合为一份统一方案，目标不是单纯优化检索体验，而是**大幅提升复杂移动端问题的归因准确性**，尤其聚焦以下高风险场景：

- 大型工程中的海量相似代码、平行实现和历史遗留分支。
- 只能定位到版本区间、无法直接定位到具体 MR 的回归问题。
- 历史遗留、偶现、跨端、跨配置、跨依赖链的问题。
- 动态运行证据与静态代码结构强耦合，但传统 AI 容易被错误上下文牵引的场景。

本方案的设计原则是：**先收缩搜索空间，再启动高阶推理；先确认真实执行路径，再讨论相似代码；先建立问题边界，再选择检索方式。**

## 2. 背景与核心挑战

当前 Mobile QA 工作流基于 OVHSC（Observe -> Hypothesize -> Verify -> Score -> Chain）推理链和多 Agent 对抗机制，在逻辑推演层面已经具备较强约束能力。但在大型移动端工程中，导致误判的主因通常不在推理链本身，而在于**进入推理链的上下文已经被污染**。

### 2.1 挑战一：海量相似代码导致“幻觉锚定”

复杂移动端工程中常见以下情况：

- A/B 实验遗留，仓库中同时存在 `FeatureV1`、`FeatureV2` 甚至更多演化分支。
- Android/iOS 双端或多业务线平行复制了相似组件、基类、适配层。
- 旧容器、旧路由、旧状态机在迁移阶段长期共存。
- 历史废弃代码没有及时清理，但名称、结构、业务语义与现行代码高度相似。

这会导致 AI 在纯静态搜索、语义召回或关键字匹配时，极易拿到“看起来很像、实际上不跑”的上下文，并围绕错误对象完成高度自洽的归因分析。这类问题不是“不会分析”，而是“对错误代码分析得太好”，因此必须被定义为一类独立的系统性失效模式。

### 2.2 挑战二：问题引入边界不确定，导致搜索半径失控

不同问题具备不同的边界清晰度，而边界清晰度直接决定应该如何开始分析：

- `EXACT_MR`：知道由某个 MR、需求或重构引入。
- `VERSION_RANGE`：只能定位到某个版本区间，期间包含大量 commit。
- `HISTORICAL_UNCLEAR`：问题存在已久，边界极宽，甚至跨越多代架构。

若工作流对这三类问题使用同一套检索策略，结果通常是：

- 边界清晰场景没有充分利用 diff 优势。
- 版本区间场景陷入代码海中无效漫游。
- 历史问题场景被死代码和未激活分支严重误导。

### 2.3 挑战三：动态证据与真实执行路径缺乏硬绑定

移动端问题的真实执行路径受到以下因素共同影响：

- Feature Flag / A/B 实验命中。
- 远端配置、灰度策略、资源包和模板。
- 服务端响应 schema 或数据契约。
- 设备、系统版本、ROM、SDK 行为差异。
- 生命周期、线程、缓存与时序条件。

因此，静态代码分析若不能与 Crash 栈、ANR Trace、抓包、Method Trace、Layout Inspector、埋点等动态痕迹建立映射，归因准确性就很难稳定。

## 3. 方案总纲

本方案将现有工作流从“统一检索 + 统一分析”升级为“边界感知路由 + 上下文策展 + 动态锚定 + 分层推理”。

### 3.1 三条顶层原则

1. **问题边界优先于搜索行为。**
2. **上下文净化优先于根因推理。**
3. **动态执行路径优先于静态相似性。**

### 3.2 三个关键升级点

1. 引入 `Issue_Boundary_Level` 作为工作流一级路由条件。
2. 引入 `Context Curator` 机制，对候选上下文做存活性、相关性和运行时映射审查。
3. 强化动态运行数据为硬锚点，要求静态证据必须解释其与动态痕迹的关系。

## 4. 目标架构

### 4.1 角色分层

现有多 Agent 架构建议升级为以下职责分层：

- `Context Curator`
  - 负责上下文候选搜集、去噪、去重、存活性校验、配置掩码、运行时映射。
- `Investigator`
  - 负责基于净化后的上下文执行 OVHSC 推理。
- `Challenger`
  - 负责质疑根因的因果充分性、必要性、证据可靠性、平台盲区及时间漂移。
- `Arbiter`
  - 负责汇总结论、吸收挑战、校准置信度并输出最终裁定。

该分层的核心收益是把“找什么能被分析”和“如何分析”拆开，降低高阶推理被脏上下文污染的概率。

### 4.2 路由分层

现有 `p3-root-cause.md` 中的 `analysis_path = fast | deep` 不应再作为唯一主路由，而应降为第二层路由。建议采用双层决策：

- 第一层：按 `Issue_Boundary_Level` 决定“从哪里开始找”。
- 第二层：按复杂度、优先级、证据强度决定“分析做多深”。

路由结构如下：

| 第一层边界路由 | 含义 | 第二层分析路由 |
|---|---|---|
| `EXACT_MR` | 从 diff、相关提交和作者时序切入 | `fast` / `deep` |
| `VERSION_RANGE` | 从版本变更降噪和 commit 排序切入 | `fast` / `deep` |
| `HISTORICAL_UNCLEAR` | 从动态锚点、自底向上回溯切入 | `fast` / `deep` |

## 5. 边界感知协议

### 5.1 为什么要增加判定协议

仅定义 `EXACT_MR` / `VERSION_RANGE` / `HISTORICAL_UNCLEAR` 还不够，必须同时定义边界是如何判定的，否则该字段本身会成为新的不稳定变量。

### 5.2 建议输入特征

Intake 阶段对以下信号做结构化判断：

- 是否存在明确 MR/PR 链接、需求单或提交哈希。
- 是否存在可确认的版本起止点。
- 是否存在“首次异常出现时间”与“最后正常时间”。
- 是否具备可直接锚定的动态证据。
- 用户是否明确描述“最近改了什么”或“历史一直如此”。
- 是否存在跨端、跨模块、跨配置的额外复杂性。

### 5.3 建议输出结构

建议在 `issue-card.md` 和 `workflow-status.yaml` 中输出以下字段：

| 字段 | 含义 |
|---|---|
| `Issue_Boundary_Level` | `EXACT_MR` / `VERSION_RANGE` / `HISTORICAL_UNCLEAR` |
| `Boundary_Confidence` | 边界判定置信度 |
| `Boundary_Evidence` | 支撑边界判定的证据 |
| `Boundary_Alternative` | 次优边界解释 |
| `Runtime_Anchor_Availability` | 动态锚点是否充足 |

### 5.4 门禁规则

- 当 `Boundary_Confidence` 高时，进入单一路由。
- 当 `Boundary_Confidence` 低时，不直接信任单一路径，应采用“双轨低成本验证”。
- 当 `HISTORICAL_UNCLEAR` 且 `Runtime_Anchor_Availability` 弱时，不进入深度 RCA，而先输出最小补证清单。

## 6. 上下文策展机制

### 6.1 为什么必须增加 Context Curator

当前工作流中，`context-bundle.md` 默认被视为可信输入，但复杂问题中最大风险恰恰是 Context Bundle 已被相似代码、死分支或旧配置污染。因此必须在 Investigator 之前增加策展层。

### 6.2 Curator 的职责

`Context Curator` 不做最终 RCA，只做“让谁进入 RCA”。其职责应包括：

1. 相似代码候选聚合与去重。
2. 基于调用关系、引用关系、运行日志做真实性校验。
3. 基于配置快照、Feature Flag、AB 命中结果做入口掩码。
4. 基于 `git blame`、变更时间、文件活跃度做陈旧性识别。
5. 对无法确认是否相关的候选项进行“保留但降级”处理，而不是简单删除。

### 6.3 Curator 输出契约

建议新增独立的 `context-curation-report.md` 或将以下结构合并进 `context-bundle.md`：

| 字段 | 说明 |
|---|---|
| `candidate_contexts` | 原始候选上下文集合 |
| `pruned_contexts` | 被剔除的上下文 |
| `keep_reasons` | 保留理由，必须可审计 |
| `prune_reasons` | 剔除原因，如 `dead-code` / `flag-off` / `no-runtime-link` |
| `runtime_links` | 与栈、日志、抓包、调用链的映射 |
| `unresolved_noise` | 仍未判明真伪的噪声候选 |
| `curation_confidence` | 策展后上下文整体可信度 |

### 6.4 证据分级升级

建议将原有证据等级从单一 A/B/C 升级为二维模型：

- `Reliability`：A / B / C
- `Liveness`：`Live` / `Suspect` / `Dead`

这样能更准确地区分“证据可靠但可能不在真实路径上”和“证据本身就不可靠”。

## 7. 动态锚定与执行路径恢复

### 7.1 动态锚定的核心地位

对复杂问题而言，动态痕迹应是最高优先级证据。优先级顺序建议如下：

1. Crash 栈、ANR Trace、抓包、Layout Inspector、稳定复现日志。
2. Method Trace、性能 Profile、服务端日志、Git blame。
3. 用户截图、录屏、用户口述、AI 推断。

### 7.2 对 `HISTORICAL_UNCLEAR` 场景的调整

原始方案提出“禁止全局搜索”，方向对，但过硬时会造成低证据场景停摆。因此建议升级为**受控搜索模式**：

- 允许搜索，但必须从现场锚点出发，例如错误码、埋点名、页面文案、路由名、请求字段。
- 搜索结果仅可作为补证引导，不可直接进入根因主链。
- 未映射到动态痕迹的静态结果，最高只能视为 C 级线索。

### 7.3 Bottom-Up Tracing 的工程化要求

自底向上回溯不是一句原则，而应当成为工作流中的显式步骤：

- 从栈顶方法、异常请求组装点、Layout 异常节点开始。
- 通过 Find Usages、Call Hierarchy、调用图索引向上恢复真实路径。
- 将路径结果沉淀为单独的 `runtime-call-path` 区块。
- 任何根因假设都必须说明其与 `runtime-call-path` 的关系。

### 7.4 配置快照掩码的严谨化

Feature Flag 和 AB 掩码不能只看“当前值”，必须绑定时间和作用域。建议记录：

| 字段 | 含义 |
|---|---|
| `Config_Snapshot_Timestamp` | 报障时刻的配置时间点 |
| `Flag_Scope` | 用户/设备/版本/地区等作用域 |
| `Flag_Source` | 服务端、缓存、本地兜底等来源 |
| `Flag_Staleness` | 配置是否可能过期 |
| `Mask_Decision_Reason` | 本次剔除/保留的决策理由 |

否则容易误删案发时真实激活的路径。

## 8. 三类场景的具体分析策略

## 8.1 场景一：`EXACT_MR`

### 目标

在已知问题与某个 MR/需求强相关时，尽可能将分析范围收敛到改动闭包内。

### 建议动作

1. 在 `p2` 强制拉取 MR Diff。
2. 将 Diff 覆盖代码标记为 A 级高优先级证据。
3. 结合 `git blame`、作者、时间窗口交叉校验相似代码。
4. 若结论不直接指向 Diff，也必须解释 Diff 与异常暴露之间的关系。

### 关键修正

“未涉及 Diff 即惩罚”不应机械执行，更准确的规则应是：

- 若假设与 Diff 无关，但能解释 Diff 为触发器而非根因，可保持中高置信度。
- 若假设既不涉及 Diff，也无法解释为何在该 MR 后暴露，则显著降权。

这样可以避免对“新入口激活旧问题”类场景过拟合。

## 8.2 场景二：`VERSION_RANGE`

### 目标

在无法直接定位 MR 的情况下，先把海量提交空间降维，再进入代码分析。

### 建议动作

1. 增加“版本变更筛查”步骤。
2. 从版本区间提取 `git log`、变更文件、模块路径、作者和上线时间。
3. 构建多信号 commit 排序，而不是简单关键字过滤。
4. 若环境允许，提供 `git bisect` 或正常/异常版本对比提示。

### Commit 排序模型

建议排序信号包括：

- 文本信号：commit message、文件名、模块关键词、错误关键字。
- 结构信号：是否触达报错模块、基础设施层、网络层、状态管理层。
- 时序信号：首次异常时间、灰度时间、版本发布时间。
- 责任信号：是否由相关 owner 提交。
- 动态信号：是否能与日志、埋点、栈映射。

最终输出不应是“一个 commit 列表”，而应是“带分数和命中理由的候选排名”。

## 8.3 场景三：`HISTORICAL_UNCLEAR`

### 目标

在边界极宽、死代码极多、配置干扰极强的场景下，优先围绕真实运行现场逆向收缩范围。

### 建议动作

1. 若缺乏强动态锚点，优先补证，不直接做深度归因。
2. 启用受控搜索模式，不允许无锚点的全仓漫游。
3. 从现场证据自底向上做调用路径恢复。
4. 使用配置快照掩码过滤显然不可能激活的路径。
5. 保留未证伪候选，但明确标记为 `Suspect`，避免误杀。

### 特别注意

历史问题常见真正根因并非“老代码逻辑错了”，而是以下对象发生漂移：

- 服务端 schema 或默认值变化。
- Feature Flag 命中策略变化。
- 远端模板、资源、H5、CDN 资源变化。
- 第三方 SDK 升级或行为变化。
- ROM、权限策略、系统行为变化。

因此 `HISTORICAL_UNCLEAR` 必须内建“远端/外部依赖漂移”分析轴。

## 9. 对 Challenger 的增强要求

现有五维质疑协议已具备良好基础，但为提高复杂问题归因准确性，建议增加两类固定质疑：

1. `Temporal Drift Challenge`
   - 如果客户端代码没有明显变化，是否是服务端契约、灰度配置、实验策略、第三方依赖或系统环境发生变化。
2. `Activation Challenge`
   - 假设中的代码路径在案发时间、案发用户、案发设备和案发配置下是否真的被激活。

这两类质疑将显著提高对“老代码突然坏了”和“相似代码误命中”的识别能力。

## 10. 对现有工作流文件的改造建议

## 10.1 `p1-intake.md`

新增“问题边界判定与锚点盘点”步骤，输出：

- `Issue_Boundary_Level`
- `Boundary_Confidence`
- `Boundary_Evidence`
- `Runtime_Anchor_Availability`
- `最小补证清单`

对于 `HISTORICAL_UNCLEAR + 弱动态锚点` 场景，应优先触发补证，而不是直接推入 RCA。

## 10.2 `p2-spec-definition.md`

在“证据收集与可信度分级”之前插入 `Context Curation` 子步骤，建议：

- 输出 `context-curation-report.md`
- 将净化后的上下文写入 `context-bundle.md`
- 记录 `Context_Noise_Risk` 与 `Context_Curation_Summary`
- 允许 Curator 失败时回退 `Info-Insufficient` 或进入 `Human-Review`

## 10.3 `p3-root-cause.md`

在复杂度评估前增加“边界驱动路由”步骤：

- `EXACT_MR` -> `Diff Focus Mode`
- `VERSION_RANGE` -> `Commit Denoising Mode`
- `HISTORICAL_UNCLEAR` -> `Dynamic Anchoring + Bottom-Up Mode`

然后再根据复杂度和优先级决定 `fast` / `deep`。

## 10.4 `workflow.xml`

建议在状态机中显式体现策展阶段，方式有两种：

- 方案 A：增加准阶段 `qa-context-curation`
- 方案 B：保留六阶段结构，但在 `qa-spec-definition` 中增加中间状态：
  - `current_state = Context-Curating`
  - 保存 `context-curation-report.md`
  - 允许回退或人工升级

若不让 Curator 进入状态机，整个机制会缺乏观测性和可调试性。

## 11. 元数据扩展建议

建议在 `workflow-status.yaml`、`issue-card.md`、`context-bundle.md` 中新增以下字段：

| 字段 | 建议位置 | 作用 |
|---|---|---|
| `Issue_Boundary_Level` | issue-card / workflow-status | 决定主路由 |
| `Boundary_Confidence` | issue-card | 控制是否允许单一路由 |
| `Boundary_Evidence` | issue-card | 边界判定可审计 |
| `Runtime_Anchor_Availability` | issue-card | 控制补证与 RCA 入口 |
| `Context_Noise_Risk` | context-bundle | 标记上下文污染程度 |
| `Context_Curation_Summary` | context-bundle | 记录净化前后变化 |
| `Config_Snapshot_Metadata` | context-bundle | 记录 flag 时间和作用域 |
| `Remote_Drift_Suspected` | spec / rca | 标记远端或外部依赖漂移风险 |
| `Analysis_Budget` | workflow-status | 控制成本、时延和 Agent 深度 |

## 12. 成本、SLA 与使用边界

为保证方案可落地，必须控制复杂度叠加后的时延与成本。建议按场景定义预算：

| 场景 | 目标时延 | 允许额外工具调用 | 多 Agent 深度模式 |
|---|---:|---:|---|
| `EXACT_MR` | 2-5 分钟 | 低到中 | 仅高优先级问题启用 |
| `VERSION_RANGE` | 5-10 分钟 | 中 | 需先完成降噪 |
| `HISTORICAL_UNCLEAR` | 10-20 分钟 | 高 | 默认单 Agent + Curator，必要时升级 |

该预算的意义在于避免流程无限膨胀，确保优化后的系统既更准，也仍然能被团队常态化使用。

## 13. 度量体系

若要证明方案真正提升了归因准确性，必须建立指标，而不是只依赖专家直觉。建议跟踪以下指标：

| 指标 | 定义 | 目标方向 |
|---|---|---|
| `False Context Rate` | RCA 中引用但事后证伪为无关代码的比例 | 持续下降 |
| `Boundary Routing Accuracy` | 边界判定与人工复盘一致率 | 持续上升 |
| `First Useful Anchor Time` | 从 intake 到拿到首个有效动态锚点的时间 | 持续下降 |
| `RCA Rework Rate` | 根因报告被回流重做或推翻的比例 | 持续下降 |
| `Human Escalation Quality` | 进入人工复核时是否已明显收缩范围 | 持续上升 |
| `Curator Precision` | 被剔除上下文中事后确认为噪声的比例 | 持续上升 |

## 14. 落地优先级

### 14.1 P0：优先落地

1. 增加边界判定元数据和 Intake 门禁。
2. 增加 Context Curator 子步骤与结构化输出。
3. 将边界路由提升为 `p3` 的第一层决策。
4. 在 `workflow.xml` 中显式记录策展状态。

### 14.2 P1：高价值增强

1. 为 `VERSION_RANGE` 增加多信号 commit 排序。
2. 为 `HISTORICAL_UNCLEAR` 增加受控搜索模式。
3. 为 Challenger 增加 `Temporal Drift` 和 `Activation` 质疑。
4. 完善配置快照掩码的时间、作用域和缓存维度。

### 14.3 P2：系统化升级

1. 建立 `runtime-call-path` 自动摘要能力。
2. 建立真实 case 回放与离线评估集。
3. 对 Curator 精度/召回单独评估。
4. 按场景持续优化预算与 SLA。

## 15. 最终结论

本方案的核心不是“让 AI 搜得更多”，而是“让 AI 在更小、更真、更可审计的上下文上进行推理”。只有这样，复杂问题的归因准确性才会真正提升。

整合后的设计可以概括为三句话：

1. **先判断问题边界，再决定检索方式。**
2. **先净化上下文，再启动根因推理。**
3. **先确认真实执行路径，再分析相似代码。**

若按本文方案推进，Mobile QA Workflow 将从“擅长逻辑推理的 QA Agent”升级为“具备工程级收缩能力和更高归因准确性的 RCA 系统”。
