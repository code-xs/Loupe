# Mobile B2C 工作流 — 状态/同步复杂度深度审视与务实优化方案 · V1.1

- 撰写日期：2026-04-21
- 版本：V1.1（基于 [V1](MOBILE_QA_WORKFLOW_STATE_SYNC_OPTIMIZATION_V1_2026-04-21.md) 吸收外部报告 [Loupe_B2C_Workflow_Deep_Optimization_Report](../../../Downloads/Loupe_B2C_Workflow_Deep_Optimization_Report.md) 的 10 项结构性优化）
- 范围：`mobile-qa-workflow/` 全量（主链路 + functionality-deep-dive 子链路 + 协议 + 模板 + 脚本）
- 不覆盖：`eval-framework/` 与 `eval-cases/`（详见姊妹文档 `LOUPE_B2C_WORKFLOW_ARCH_OPTIMIZATION_2026-04-21.md`）
- 核心原则：**先减漂移与同步点，再降表层复杂度**；任何建议默认遵守"产物契约不破坏 / 状态枚举向后兼容 / 评测口径不静默漂移 / **跨平台行为对齐**"四条硬约束

---

## V1.1 修订日志（vs V1 2026-04-21）

> V1.1 在保留 V1 全部判断（含 F1/F2/F3/F4 finding 与跨平台兼容性章）的基础上，吸收外部报告的 10 项结构性优化。**对外部报告的所有"零风险/Full 平台前提"建议，均按 V1 跨平台四类回归门禁重新分级。**

| ID | 类型 | 来源 | V1.1 处理 |
|---|---|---|---|
| **O4+** | 扩展 | 外部 §2.9.1 | 原 O4 仅归档历史文档；扩展为"归档 + ADR 化 + 注释外迁"（D1-D19 散布注释 ~165 行收敛到 `doc/adr/`）|
| **O10+** | 扩展 | 外部 §2.1 | 原 O10 仅把 user_inputs 清空下沉编排器；扩展为 step-pause-registry.yaml 数据驱动（6 case switch 注册表化）|
| **O11+** | 扩展 | 外部 §2.5.1 | 原 O11 仅整合 invoke-subagent boilerplate；扩展为 `coder-agent.md` 拆三件（角色 / 工作流 / Checklist 规范）|
| **O17+** | 扩展 | 外部 §2.3 | 原 O17 仅"自动构建消除漂移"；扩展为生成器输出 L0-L4 分层产物（按需注入）|
| **O19+** | 扩展 | 外部 §2.5.2 | 原 O19 仅整合 wrapper 内重复；扩展为提取 `shared-input-guard.md`（10 行通用入参校验）|
| **O21** | 新增 | 外部 §2.2 + §2.8 | `<phase-abort>` / `<phase-complete>` 声明式宏标签，结构性消除 B1* 类 bug |
| **O22** | 新增 | 外部 §2.10 | CI 安全网 4 件套补全（io-contract / subagent-params / phase-abort 结构 / deep-dive 键名）|
| **O23** | 新增 | 外部 §2.7.1 | `core-rules.xml` 拆 essential(70行) + dsl-reference(150行)，phase 只加载 essential |
| **O24** | 新增 | 外部 §2.7.2 | `reasoning-chain` 按 4 个分类拆分，P3 只加载命中分类 |
| **O25** | 新增 | 外部 §2.7.3 | SubAgent 专用 `core-rules-subagent.xml`（30 行，去除编排器协议）|

**外部报告中 V1.1 不吸收的项目**：
- 外部 §2.6.1（Deep-Dive step-pause 上提到主编排器）— 与 V1 §6 第 13 条"deep-dive 子编排独立调度域"判断冲突；折中方案是子工作流挂起时显式写入主 status 的 `specialized_workflow.status` 让主编排器**有感知能力**但**不参与调度**。
- 外部对 O18（删 current_phase_result 运行时变量）的隐含支持 — 在 V1 §9.3 已显式否决。

**V1.1 对 V1 章节的影响**：
- §3 新增 O21-O25 五条，扩展 O4/O10/O11/O17/O19 五条
- §4.1 批次表新增 B2.5（phase-abort 宏）与 B4.5（Token 优化），调整 B0/B3/B5
- §5 量化对比表新增 5 行（行数减少、token 节省、新增交互态成本、注释行数、CI 守门覆盖率）
- §9.2 兼容性重分类表新增 10 行
- §10 优先级建议增补 v4.2 收敛新成员

**V1.1 二次修订（2026-04-21 质检接纳）**：本文件在首次发布后接纳质检结论的 4 条采纳门槛，**直接合并到对应章节而非新开版本**：
- §3.2.10 末尾新增 **Registry 权威性约束**（H3）：O10+ 落地后编排器 step 4 内禁止任何硬编码 case，CI 强制兜底
- §3.2.21 末尾新增 **执行引擎适配性 + 命名冲突规避**：明确仓库为 LLM 自执行模型（无外部 parser），`<phase-abort>` 宏可行但需 ADR-021 头段显式区分与 PR-4 子命题名 "phase-abort-fanout-isolation" 的差异
- §3.2.22 `check-step-pause-registry.sh` 实现要点加严（含"硬编码 case 禁出"校验）
- §4.1 批次表前新增 §4.1.0 **跨批次硬依赖与 B2.5 降级路径**（B1 等待 B3 O13a；B2.5 失败时 B3 降级回 5 步咒语）

---

## 0. TL;DR — 这套工作流为什么会越来越复杂？

通过逐文件审视 `core/`、`phases/`、`agents/`、`functionality-deep-dive/`、`templates/`、`scripts/` 全量 ~3000 行 DSL + Markdown，**复杂度的真实来源不是"业务规则多"，而是同一份语义被同步到了多个物理位置 + 协议知识散布在代码各处的注释和重复描述中**。集中体现为：

| 复杂度类别 | 同一语义被复制到的物理位置 | 典型表现 |
|---|---|---|
| **`current_state` 枚举集**【F4 修订】| **全量镜像 2 处**（`workflow-status-template.yaml:4-9` 权威 + `system-prompt.md:104-110` Limited 平台镜像）；**协议级引用 1 处**（`core-rules.xml` 提及 `current_state` 字段不带枚举值）；**字段描述/单值写入 多处**（`SKILL.md`、`PLATFORM-GUIDE.md` 描述字段；各 phase 写入单值，可能漂移如 `RCA-InProgress`）| 全量镜像同步是真正的同步债（2 处），但 phase 内单值写入也会引入漂移（已发现 1 处） |
| **fan-out / 路由模式** | 4 处（`fanout_mode` + `fix_fanout_mode` + `rca_fanout_mode_snapshot` + `phase_history[].fanout_mode`）| 同一信息四份；C10"字段隔离"是补救，但留下了"快照 + 历史 + 当前"三层冗余 |
| **step-pause 调度位置**【F3 修订】| **5 处**：编排器 `core/workflow.xml` step 4（6 case，主调度入口）+ `phases/p2-spec-definition.md:235` 内联（D14 遗留）+ `phases/p4-fix-design.md:136` 内联（D14 遗留）+ deep-dive 编排器 2 case（DD-LowConfidence / DD-Human-Review）| 主链路集中度高但**未真正唯一**；遗留位置由 `legacy-phase-step-pause-allowlist.txt` 守门 |
| **step-pause 用户输入** | 2 处（顶层镜像字段 + `user_inputs.<key>`）| D8 + D15 显式承认是 v4.1 → v4.2 过渡；目前白名单仅 1 个字段也强制双写 |
| **step-pause case 路由逻辑**【V1.1 新增】| 6 case 共 ~150 行 switch + 各 case 内重复的"重置计数 / 输出 / 解析 / 双写 / 派发 / 清空"6 步 | 新增 1 个 stop_state ≈ 60 行 5 文件改动 |
| **重试/熔断计数器** | 5 个独立字段（`rca_retry_count` / `fix_retry_count` / `non_bug_reflow_count` / `lint_retry_count` / `parse_error_count`）| 每个有独立的递增/重置时机；散落在 phases 与 orchestrator 多处 |
| **核心规则文本** | 至少 3 份（`core-rules.xml` 权威 + `system-prompt.md` 全量内联 + `SKILL.md` 摘要）| `system-prompt.md` 一行变更需同步审查 `core-rules.xml`；目前 `system-prompt.md` 已经与 `core/` 出现实质漂移 |
| **设计决策注释**【V1.1 新增】| D1-D19 解释散布在 XML 注释 / YAML 注释 / phase 文件 / system-prompt 共 50+ 处约 165 行 | 同一 D14 解释被改写过 5 次，互相已经轻微漂移；占据大量行数但对 LLM 执行无帮助 |
| **Spec-Uncertain 回复契约**【F1 新增】| 2 个不同契约：Full 路径 `workflow.xml:194` 用 `allowed_values=Confirm`（单选），Limited 路径 `system-prompt.md:165` + `p2-spec-definition.md:235-239` 用 `1\|2\|S`（三选） | 不同平台用户看到不同选项；O13 直接迁移会让某一边行为静默变化（必须先做 O13a 统一）|
| **legacy phase 内联 step-pause** | 2 处显式（`p2-spec-definition.md:53` + `p4-fix-design.md:136`）+ 1 处对应允许清单（`legacy-phase-step-pause-allowlist.txt`）+ CI 检查 | D14 协议禁止内联，但保留了"违规清单"作为兼容层；本身就是同步点 |
| **invoke-subagent 头部 boilerplate** | ~10 次（每次调用都重复 `<load core-rules.xml/>` + `<load shared-base.md/>` + `<load wrapper.md/>`）| 任一文件移动都需要全量更新 |
| **SubAgent 加载的 core-rules 完整体**【V1.1 新增】| ~10 次 SubAgent 调用都加载 222 行完整 core-rules（含编排器协议、step-pause、workflow-result-protocol）| SubAgent 不需要编排器协议；P3 complex 路径浪费 ~15K token |
| **reasoning-chain 全量加载**【V1.1 新增】| 200 行内含通用 OVHSC + 4 个分类专项推理引导（功能/UI/网络/兼容），P3 每次执行不论分类全量加载 | 每次浪费 ~3 个未命中分类 ~90 行 / ~3K token |
| **`coder-agent.md` 单文件 269 行**【V1.1 新增】| 角色定义(30) + I/O 契约(40) + 变量命名规范(20) + 工具白黑名单(20) + 四阶段工作流(100) + Contract Checklist 规范(25) + Error Dump 模板(35) + 平台溯源映射表(15) 杂糅在一个文件 | P6 验证时引用 Contract Checklist 也要加载完整 269 行 |
| **deep-dive 配置键名** | 2 套（主端 `deep_dive_optional_artifacts.<key>` ↔ 子端 `emit_<key>`）| `config-schema.yaml` 的 `known_legacy_aliases` 块明示这是漂移；登记为 v4.2 遗留 #1 |
| **遗留 deep-dive agent 兼容入口**【F2 修订】| 5 个旧 agent 文件（`functionality-deep-dive/agents/{context-reconstructor,state-analyst,temporal-analyst,challenger,arbiter}.md`）+ `core-rules.xml:92-96` 5 行声明 + `agents/README.md:10-17` 文档说明 | 新会话不调用，但**老会话恢复仍依赖**；物理删除有破坏老会话恢复风险（F2 finding） |
| **Phase 早退"5 步咒语"**【V1.1 新增】| P2 Non-Bug 早退 5 个连续 action + 45 行注释；P3 ABORT 4 处同构三步曲；P6 1 处 | 漏写任一步即复现 B1* bug；已修历史 bug 多起 |
| **CI 守门缺口**【V1.1 新增】| 仅有 eval.yml + check-config-schema.sh；缺 io-contract / subagent-params / phase-abort 结构 / state-enum / deep-dive 键名校验 | 上述漂移多数靠人工 review 兜底 |

**核心判断**：当前复杂度有 70% 是"协议补丁 + 兼容层 + 过渡机制"叠加而成，**另有 20% 是"协议知识用注释和重复描述形式散布在代码各处而非结构化声明"**。它们每一项单独看都合理（v2.0/v2.1/v2.2 的 D1-D19 决定都有充分论证），但叠在一起就形成"理解一处必须理解全部"的耦合。**优化的根本路径有两条并行**：
1. **物理删除冗余**（V1 主线）：让单一权威源真的只有一份，但每次删除都必须先穷尽所有引用点（含老会话恢复路径）。
2. **结构化收敛知识**（V1.1 新增主线）：把"协议知识"从散布在代码各处的注释和重复描述中，收敛为结构化的声明（registry / macro / ADR / 分层产物），让 phase 文件专注于业务逻辑，让编排器专注于状态路由。

---

## 1. 架构与运行时数据流（事实陈述）

### 1.1 执行入口与编排层级

```
SKILL.md (Skill 入口)
  └─ core/workflow.xml (主编排器)
       ├─ step 1: load core/core-rules.xml (DSL 协议)
       ├─ step 2: read workflow-status.yaml → 决定 current_phase
       ├─ step 3: switch(current_phase) → load phases/p{1..6}-*.md
       │             └─ phases 内部可能 invoke-subagent
       │                   └─ agents/*.md (curator/investigator/...)
       │                         └─ 共享基座 shared-{challenger,arbiter}-base.md
       └─ step 4: switch(current_state) → 触发 step-pause 或 goto step 2
              ↑
              └─ 主链路 step-pause 【主调度入口】（D14 协议目标）
                  ⚠️ 实际仓库仍存在 phase 内联 step-pause 与 deep-dive 独立调度入口
                       —— 详见 §1.5 step-pause 调度位置全景

phases/p3-root-cause.md (RCA)
  └─ 满足触发条件时 嵌套加载 functionality-deep-dive/core/workflow.xml (子编排)
                              └─ phases/f{1..5}-*.md
                                    └─ agents/deep-dive-*.md
                                    └─ 子编排器自身的 step-pause case（DD-LowConfidence / DD-Human-Review）
```

无 Skill 平台路径：`system-prompt.md` 一份内联了上述全部内容（约 570 行），作为 Dify/Coze 等平台的兜底入口。

### 1.2 状态/产物的物理存储

每个 issue 一个工作区 `qa-workspace/{issue_id}/`，包含：

| 文件 | 来源模板 | 用途 |
|---|---|---|
| `workflow-status.yaml` | `core/workflow-status-template.yaml` | **状态机权威源**（25+ 字段）|
| `default-config.yaml`（重命名为 issue 配置）| `core/default-config.yaml` | 输出路径与环境能力开关 |
| `issue-card.md` | `templates/issue-card.md` | P1 产物 |
| `spec.md` / `context-bundle.md` / `context-curation-report.md` | `templates/spec.md` 等 | P2 产物 |
| `rca-report.md` | `templates/rca-report.md` | P3 产物 |
| `fix-design.md` | `templates/fix-design.md` | P4 产物 |
| `impl-report.md` / `contract-checklist.md` /（条件）`error-dump.md` | `templates/impl-report.md` 等 | P5 产物 |
| `verification-report.md` / `knowledge-card.md` | `templates/*.md` | P6 产物 |
| `deep-dive/*` | `functionality-deep-dive/templates/*.md` | 专项产物（子工作区）|

### 1.3 状态机字段全景（按职责分层）

| 类别 | 字段 | 写入方 | 读取方 |
|---|---|---|---|
| **核心进度** | `current_state` / `stepsCompleted` / `lastStep` / `last_updated` | phases + orchestrator step 4 | orchestrator step 2 |
| **路由（RCA）** | `analysis_complexity` / `analysis_complexity_confidence` / `fanout_mode` / `rca_fanout_mode_snapshot` / `phase_history[]` | P2、P3 | P3、orchestrator step 2 |
| **路由（Fix）** | `fix_fanout_mode` / `fix_strategy_mode` / `fix_risk_level` | P4 | P4、P6 |
| **回流** | `reroute_target_phase` / `reroute_reason` / `reroute_from_phase` / `verification_failure_type` | P3、P6、orchestrator step 4 | orchestrator step 2 |
| **熔断计数器** | `rca_retry_count` / `fix_retry_count` / `non_bug_reflow_count` / `lint_retry_count` / `parse_error_count` | P3、P5、P6、orchestrator step 4 | orchestrator step 4 |
| **step-pause 输入** | `user_inputs.{6 个 key}` + `non_bug_user_choice`（顶层镜像）| orchestrator step 4 | orchestrator step 4 case |
| **Non-Bug 上下文** | `non_bug_context` | P2 | orchestrator step 4 case Non-Bug |
| **元信息** | `issue_id` / `platform` / `priority` / `Issue_Boundary_Level` / `Boundary_Confidence` / `Runtime_Anchor_Availability` / `active_branch` | P1、P5 | P3、P4、P6 |
| **Schema 元** | `workflow_version` / `schema_version` | 模板 + 迁移脚本 | orchestrator step 2 |
| **专项** | `specialized_workflow.{mode,status,sub_workspace,trigger_reason,merge_strategy}` | P3、deep-dive | P5 |

合计 **27 个顶层字段 + 1 个嵌套块 + `user_inputs` 命名空间**。

### 1.4 主链路状态转移（不含子工作流）

```
Intake ──P1──> Spec-Defining ──P2──> {Context-Curating → RCA-Designing | Non-Bug | Curation-Failed | Spec-Uncertain | Boundary-Refined}
RCA-Designing ──P3──> {Fix-Designing | RCA-LowConfidence | Human-Review}
Fix-Designing ──P4──> Fix-Implementing ──P5──> Verifying ──P6──> {Done | Fix-Designing | RCA-Designing | Human-Review}

任意 phase 早退 → 设 current_phase_result = ABORT（运行时变量，不持久化）
                 → orchestrator step 4 不追加 stepsCompleted，按 current_state 路由 step-pause
任意状态 → Human-Review（计数器熔断 / 解析错误 / 多轮不收敛）
```

**enum 集合**（`core/workflow-status-template.yaml` 头部权威源，15 个值）：
`Intake | Spec-Defining | Spec-Uncertain | Context-Curating | Curation-Failed | Boundary-Refined | Non-Bug | Info-Insufficient | RCA-Designing | RCA-LowConfidence | Fix-Designing | Fix-Implementing | Verifying | Human-Review | Done`

### 1.5 step-pause 调度位置全景【F3 新增】

D14 协议的目标是"phase 禁止内联 step-pause，全部由 `core/workflow.xml` step 4 调度"，但**当前仓库实际状态**：

| # | 位置 | 类型 | 触发条件 / case 名 | 是否合规 |
|---|---|---|---|---|
| 1 | `core/workflow.xml:160-176` step 4 switch | **主链路主调度入口** | 6 case：`Info-Insufficient` / `Spec-Uncertain` / `Non-Bug` / `RCA-LowConfidence` / `Curation-Failed` / `Human-Review` | ✅ 合规（D14 唯一目标位置）|
| 2 | `phases/p2-spec-definition.md:235-239` | **phase 内联（遗留）** | Spec 模糊歧义弹窗（与编排器 case Spec-Uncertain 重复）| ⚠️ 不合规，登记于 `legacy-phase-step-pause-allowlist.txt` |
| 3 | `phases/p4-fix-design.md:132-142` | **phase 内联（遗留）** | Fix Design 确认弹窗 | ⚠️ 不合规，登记于 `legacy-phase-step-pause-allowlist.txt` |
| 4 | `functionality-deep-dive/core/workflow.xml:57-63` | **deep-dive 子编排独立 case** | DD-LowConfidence | ✅ 合规（子编排有独立调度域）|
| 5 | `functionality-deep-dive/core/workflow.xml:65-69` | **deep-dive 子编排独立 case** | DD-Human-Review | ✅ 合规（子编排有独立调度域）|

**结论**：D14 在主链路只达成了"主调度入口"目标，**未达成"唯一调度入口"目标**。子编排有自己的调度域（设计上可接受），但 phase 内联是真正的违规（O13/O14 收尾目标）。

---

## 2. 复杂度来源逐项审视（带文件引用，便于改造定位）

### 2.1 状态机层（最严重）

#### 2.1.1 `current_state` 枚举的真实复制点【F4 修订】

**全量 15 值枚举镜像（真正同步债，2 处）**：

```4:9:mobile-qa-workflow/core/workflow-status-template.yaml
# current_state 完整合法枚举集（C5 单一权威源）：
# Intake | Spec-Defining | Spec-Uncertain | Context-Curating | Curation-Failed |
# Boundary-Refined | Non-Bug | Info-Insufficient | RCA-Designing |
# RCA-LowConfidence | Fix-Designing | Fix-Implementing | Verifying |
# Human-Review | Done
```

```104:110:mobile-qa-workflow/system-prompt.md
> **`current_state` 完整合法枚举集**（C5 单一权威源 / `core/workflow-status-template.yaml`）：
> `Intake` / `Spec-Defining` / `Spec-Uncertain` / `Context-Curating` / `Curation-Failed` /
> `Boundary-Refined` / `Non-Bug` / `Info-Insufficient` / `RCA-Designing` /
> `RCA-LowConfidence` / `Fix-Designing` / `Fix-Implementing` / `Verifying` /
> `Human-Review` / `Done`
```

**协议级引用（不维护枚举值，1 处）**：
- `core/core-rules.xml:100-124`：仅说明 `current_state` 字段语义、D14/D15 协议规则，不列举枚举值。修改 enum 不需要改这里。

**字段描述（不维护枚举值，2 处）**：
- `SKILL.md`：描述 `current_state` 字段含义与恢复语义，不列举枚举集。
- `PLATFORM-GUIDE.md`：同上。

**单值写入点（可能漂移的源头，10+ 处但非 enum 镜像）**：
- 各 phase 文件的 `<action>更新 {workflow_status}：current_state = X</action>` 语句。
- 这些不是 enum 镜像，但**写入值必须在权威 enum 集中**。`p2-spec-definition.md:188` 的 `RCA-InProgress` 漂移就是单值写入与权威集失配的例子。

**修订后的精准判断**：
- 真同步债 = **2 处全量镜像**（`workflow-status-template.yaml` ↔ `system-prompt.md`），由 O5 + O17+ 收口
- 单值写入漂移 = **per-phase 单点 bug**（如 O1 修复的 `RCA-InProgress`），由 CI enum 校验脚本（O5 配套 + O22）一次性兜底
- 协议引用与字段描述**不构成同步债**，不必改造

修订前"6+ 处枚举权威"的措辞被纠正为"2 处全量镜像 + 多处需 enum 校验的单值写入"。这降低了 O5/O17 的紧迫性叙事，但**改造方向不变**——仍然要做 sync 检查脚本与自动构建。

#### 2.1.2 已经存在的状态值漂移（需要立即修复，零风险）

```186:188:mobile-qa-workflow/phases/p2-spec-definition.md
        <step n="9" goal="输出产物">
            ...
            <action>更新 {workflow_status}：current_state = RCA-InProgress</action>
```

`RCA-InProgress` 不在权威枚举集（应为 `RCA-Designing`）。`p6-verification.md` 已经 C5 收口替换了一处（`RCA-InProgress → RCA-Designing`），但 `p2-spec-definition.md` 末尾被遗漏。

**影响**：编排器目前对未知值走 default 分支（`goto step 2`），看似没炸，但路由语义不再可被静态推断；后续若 PR-8 CI 加严格 enum 校验会立即破。

#### 2.1.3 fan-out 模式四副本

| 字段 | 文件:行 | 语义 |
|---|---|---|
| `fanout_mode` | `workflow-status-template.yaml:33` | RCA 当前 fan-out 模式（运行时活字段）|
| `fix_fanout_mode` | `workflow-status-template.yaml:34` | Fix 当前 fan-out 模式（C10 字段隔离新增）|
| `rca_fanout_mode_snapshot` | `workflow-status-template.yaml:37` | P3 完成时 `fanout_mode` 的快照（C10 兼容性方案 B 兜底）|
| `phase_history[].fanout_mode` | `workflow-status-template.yaml:48-54` | 每次 phase 完成时 append 的历史值（方案 A 主路径）|

**问题**：snapshot（B）与 phase_history（A）是"双保险"——同一信息存了两份。`p3-root-cause.md:214-215` 显式同时写两份。这是为了让 P3 重入时还原 RCA 上下文，但 `phase_history[]` 本身已经是顺序历史，**任何重入只需取 `phase_history` 中最近一条 `phase=qa-root-cause` 的 `fanout_mode`**。snapshot 字段是冗余安全网，并非必要。

此外，P4 引入 `fix_fanout_mode`（C10）的本意是"避免 P4 写入污染 RCA 字段 `fanout_mode`"，但 `p4-fix-design.md:36` 仍然两个字段都写：
```33:38:mobile-qa-workflow/phases/p4-fix-design.md
            <action>更新 {workflow_status}：
                - fix_risk_level = {fix_risk_level}
                - fix_strategy_mode = {fix_strategy_mode}
                - fix_fanout_mode = {fix_strategy_mode}
                - reroute_reason = null
            </action>
```
注意 `fix_strategy_mode` 与 `fix_fanout_mode` 取值完全相同（前者赋给后者）——它们语义重合，是同一信息的两个名字。

#### 2.1.4 5 个计数器，5 套生命周期规则

`rca_retry_count` / `fix_retry_count` / `non_bug_reflow_count` / `lint_retry_count` / `parse_error_count` 各自独立。其中：
- 递增点散落在 `p2-spec-definition.md`（non_bug_reflow_count）/ `p3-root-cause.md`（rca_retry_count，3 处）/ `p5-fix-impl.md`（lint_retry_count，间接）/ `p6-verification.md`（rca_retry_count + fix_retry_count）/ `core/workflow.xml`（parse_error_count + non_bug_reflow_count）/ orchestrator step 4。
- 重置规则各异，`parse_error_count` 重置规则跨 4 处文档反复声明（`workflow-status-template.yaml:72-78` + `core-rules.xml:160-164` + `system-prompt.md:34` + `workflow.xml` 步骤注释）。
- 熔断阈值各异：`rca_retry_count > 2` / `fix_retry_count > 2`（编排器）/ `non_bug_reflow_count >= 2`（编排器 + system-prompt）/ `parse_error_count >= 3`（编排器）/ `lint_retry_count` 在 coder-agent `<try retry="3">` 内部隐式管理。

**问题**：每个计数器都需要在编排器或 phase 内显式 +1 / 重置；任何漏写一处都会让熔断失效或永远触发。这是"业务规则数 × 实现位置数"的乘积复杂度。

#### 2.1.5 Phase 早退"5 步咒语"的结构性脆弱【V1.1 新增 — 外部 R2 借鉴】

**事实**：当前每个 ABORT 点都需要写 3-5 行 action + 大量注释解释为何需要这些步骤。以 P2 Non-Bug 早退为例（`p2-spec-definition.md` step 4）：

```xml
<!-- 当前实现：5 个连续 action + 45 行注释（D1/D14/D17/B1* 各一段） -->
<check if="判定为 Non-Bug">
    <action>生成 Non-Bug Resolution Report 文本</action>
    <action>更新 {workflow_status}：non_bug_context = {report_text}</action>
    <action>更新 {workflow_status}：current_state = Non-Bug</action>
    <action>设置 current_phase_result = ABORT</action>
    <!-- 45 行注释解释 D1/D14/D17/B1* 历史背景 -->
</check>
```

P3 有 4 处同构的"ABORT 三步曲"（写 state → 写 route fields → 设 ABORT），P6 有 1 处。

**问题**：
- 新增任何 stop_state 都需要在 phase 中写这个"5 步咒语"，写错任何一步就复现 B1* bug
- 注释占了比实际逻辑更大的篇幅，信噪比极低
- LLM 执行时，5 个 action 中间任何一步被跳过都会导致编排器行为异常（已在历史 bug 中多次发生）

**与 V1 O6 的关系**：V1 的 O6 只是"加注释强调幂等性"，是**口头约束**；要结构性消除该类 bug，需要 O21 引入 `<phase-abort>` / `<phase-complete>` 宏标签（详见 §3.2.21）。

### 2.2 step-pause 协议层（次严重）

#### 2.2.1 D14 + D15 + D16 + D18 = 同一交互点的 4 重协议补丁【F3 修订措辞】

`<step-pause>` 这一标签上挂载了至少 4 套协议：
1. **D14 调度作用域**：**目标**为"仅允许在 `core/workflow.xml` step 4 调度"（`core-rules.xml:113-124`），**实际**主链路仍有 2 处 phase 内联遗留（详见 §1.5），且子编排另有独立调度域。
2. **D15 白名单受限双写**：`user_inputs.<key>` 总写 + 顶层 `<key>` 仅当在白名单内才写（白名单 v4.1 起步 = 1 个字段 `non_bug_user_choice`）
3. **D16 参数完整性**：`title` / `result_field` / `allowed_values` 必填 + `option` 0..*
4. **D18 parse-error 熔断**：连续 3 次解析失败 → Human-Review，`parse_error_count` 显式持久化跨回合

**问题**：D14 的"目标"与"实际"之间有差距——为了不一次性大改，留了 `legacy-phase-step-pause-allowlist.txt` 允许 2 处遗留，并加 CI 守门。这是把"一次性整改"变成了"长期容忍 + 文档强调 + CI 守门"的状态。O13/O14 是这个差距的整改路径。

D15 白名单 1 个字段就要建一套白名单受限双写机制，配套：
- `workflow-status-template.yaml:80-85` 注释强契约
- `core/workflow.xml:115-123` 双写实现 + 白名单条件分支
- `core-rules.xml:165-172` 协议规则
- `system-prompt.md:39-40` 协议规则
- `PLATFORM-GUIDE.md:28` 接入方约束
- `QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md` 多处 D8/D15 决定文本

而该机制的最终归宿是 v4.2 整体删除（"v4.2 遗留 #3"）。**这是为 1 个字段维护了一套未来要删的过渡协议**。

#### 2.2.2 6 个 step-pause case 各有自己的 `result_field` + `allowed_values` + 清空回写

`core/workflow.xml` step 4 的 6 个 case，每个都需要：
1. 进入前重置 `parse_error_count = 0`
2. 输出 `<step-pause>` 含 `[result_field=...]` + `[allowed_values=...]` 标签 + `请用 X=Y 回复` 后缀
3. 解析用户回复
4. 写 `user_inputs.<key>` （+ 可选写顶层）
5. 解释 user_inputs 派发到 next state
6. **手动清空** `user_inputs.<key>` 与（如有）顶层镜像（"消费一次性输入，避免下一轮误派发"）

第 6 步在 6 个 case 中各自重复了 8+ 次清空动作。Non-Bug case 因为 Reflow 与 Accept 都要清空，共写了 4 处清空动作。任何遗漏会导致下一次同状态进入时 step-pause 被错误跳过。

**外部 R1 借鉴**：6 个 case 共 ~150 行 switch 是新增交互态的高成本来源，**新增 1 个 stop_state ≈ 60 行 5 文件改动**（编排器 case + system-prompt 路由表 + workflow-status-template enum + 文档说明 + CI allowlist）。O10+ 把 case 数据化为注册表（详见 §3.2.10），新增成本降至"1 文件 8 行"。

#### 2.2.3 Spec-Uncertain 回复契约 Full ↔ Limited 漂移【F1 新增】

这是 review F1 finding 揭示的最严重漂移：

| 路径 | 文件:行 | `result_field` | `allowed_values` | 选项 |
|---|---|---|---|---|
| **Full（编排器）** | `core/workflow.xml:184-205` | `spec_uncertain_choice` | `Confirm`（单值）| `[C] Confirm：确认后继续` |
| **Limited（system-prompt 路由表）** | `system-prompt.md:165` | `spec_uncertain_choice` | `1\|2\|S` | （描述性，未列 option）|
| **Limited（phase 内联）** | `phases/p2-spec-definition.md:235-239` | （inline）| —— | `[1] {option_1}` / `[2] {option_2}` / `[S] Skip：先并行分析` |

**影响**：
- 同一个 issue 在 Cursor（走 workflow.xml）与 Dify（走 system-prompt.md 内联）下，用户看到的选项**完全不同**。
- 如果直接执行 O13（删除 phase 内联，全部交给编排器调度），Limited 平台用户失去 1/2/S 三选选项，行为静默变化。
- 如果再叠加 O17（自动构建 system-prompt.md），生成器会以 workflow.xml 为权威源固化 `Confirm` 单选，Limited 平台行为切换无声完成。

**结论**：必须在 O13 之前先做 **O13a：统一 Spec-Uncertain 回复契约**（详见 §3.2.0），否则 O13 + O17 的组合会引入跨平台不可见的行为漂移。

### 2.3 跨文件复制层

#### 2.3.1 `system-prompt.md` 是核心规则的全量内联拷贝（最大同步债）

`system-prompt.md` 共 ~570 行，把以下内容全部内联：
- `core-rules.xml` 全部规则（`<core-rules>` 块）
- 所有阶段的核心 step / check 逻辑（重写为 `<workflow>` xml 块）
- 所有模板的 schema 摘要
- OVHSC、Challenger、修复策略、平台检查要点等参考知识

**问题**：
- 任何 `core-rules.xml` 的协议变更都需要同步审查 `system-prompt.md` 是否漂移；目前已经存在事实漂移，例如 `system-prompt.md:191` 仍然写 Phase 1 step 5 重复编号（两个 `step n="5"`，应当为 `step n="6"`），与 `phases/p1-intake.md` 的 7 步骤结构不一致。
- 任何 phase 的逻辑修订都要在 `system-prompt.md` 中找到对应的 xml 块并同步。
- 这导致 Limited 平台与 Full 平台的行为存在隐式差异（如 §2.2.3 揭示的 Spec-Uncertain 选项漂移）。

**外部 R3 借鉴**：当前 system-prompt.md 是"什么都有但什么都不精"的拷贝版本，可改为分层产物：L0 核心身份 / L1 执行规则 / L2 当前阶段逻辑 / L3 推理工具箱 / L4 平台知识。详见 O17+（§3.3.17）。

#### 2.3.2 invoke-subagent 调用处的 boilerplate

每次调用 `challenger` / `arbiter` / `investigator` / `fix-proposer` / `coder-agent` 都要在 `subagent_prompt` 内显式写：
```xml
<load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
<load target='mobile-qa-workflow/agents/shared-challenger-base.md' prompt='加载共享 challenger 基座'/>
<load target='mobile-qa-workflow/agents/challenger.md' prompt='加载主流程 challenger 包装层'/>
```
然后再注入 `scene` / `dimension_set` / `target_list` / `supporting_context` / `confidence_input` / `conditional_dimensions`（5-7 个参数）。

`p3-root-cause.md` 和 `p4-fix-design.md` 共有 ~10 次此类调用，每次平均 8-12 行 boilerplate。任何 agents 文件路径调整或基座文件重命名需要全量 grep 修改。

**外部 R5 + R7 借鉴**：
- `shared-arbiter-base.md`(83 行) 与 `shared-challenger-base.md`(91 行) 各有 ~15 行同构入参校验，可提取为 `shared-input-guard.md`（O19+）
- SubAgent 实际不需要编排器协议（step-pause / workflow-result-protocol），可用 `core-rules-subagent.xml`（30 行）替代 222 行完整 core-rules（O25），P3 complex 路径节省 ~15K token

#### 2.3.3 `coder-agent.md` 单文件 269 行职责杂糅【V1.1 新增 — 外部 R5 借鉴】

`coder-agent.md` 同时包含 8 个职责块：
- 角色定义（30 行）
- I/O 契约（40 行）
- 变量命名规范（20 行）
- 工具白黑名单（20 行）
- 四阶段工作流（100 行）
- Contract Checklist 规范（25 行）
- Error Dump 模板（35 行）
- 平台溯源映射表（15 行）

**问题**：
- P6 验证阶段需要引用 Contract Checklist 规范时，必须加载完整 269 行（节省空间 ~190 行）
- 修改四阶段工作流的 PR 与修改 I/O 契约的 PR 共用一个文件，diff review 难以聚焦
- 角色定义被工作流细节淹没，LLM 理解角色身份时需要"过滤噪声"

详见 O11+（§3.2.11）拆三件方案。

#### 2.3.4 reasoning-chain 全量加载浪费【V1.1 新增 — 外部 R7 借鉴】

`reference/reasoning-chain.md`（~200 行）包含：
- 通用 OVHSC 五步推理（~100 行）
- 4 个分类专项推理引导：功能 / UI / 网络 / 兼容（各 ~30 行）

P3 step 5 每次执行**全量加载** 200 行，但 issue 只命中 1 个分类，3 个未命中分类的 ~90 行是浪费。

详见 O24（§3.3.24）按分类拆分方案。

### 2.4 已废弃但仍保留的 5 个 deep-dive agent【F2 修订】

`functionality-deep-dive/agents/` 下：`context-reconstructor.md` / `state-analyst.md` / `temporal-analyst.md` / `challenger.md` / `arbiter.md` 5 个文件全部标注"已废弃，仅供历史会话恢复"（`agents/README.md:10-17` 与 `core-rules.xml:92-96`）。

新会话使用复合角色（`deep-dive-context-analyst` / `deep-dive-structure-analyst` / `deep-dive-race-and-isolation-analyst` / `deep-dive-arbiter` / `defensive-fix-architect`）。

**问题**：这 5 个文件占 ~250 行，其内容仍出现在 `core-rules.xml` 的 `<available-agents>` 列表中，是新会话的潜在干扰项（LLM 可能误调用），同时也是同步债（每次 deep-dive 重构需考虑兼容路径）。

**F2 finding 修订**：原版判断"新会话不用 → 物理删除零风险"过于乐观。子编排器 `functionality-deep-dive/core/workflow.xml:21-30` 仍包含老会话恢复逻辑（按 `workflow_version=v3-legacy` 与 `legacy_flow_mode=true` 走老路径），而老 stepsCompleted 中仍可能引用旧 agent 名字。**物理删除会破坏 v3-legacy 会话的恢复**。改造路径应该是"归档 + 退役标注 + CI deprecated 警告"，而非直接删除（O3 已修订）。

### 2.5 deep-dive 与主链路的配置键名漂移

`config-schema.yaml:78-83` 显式登记：
```yaml
known_legacy_aliases:
  deep_dive_optional_artifacts.environment_factor_report: emit_environment_factor_report
  deep_dive_optional_artifacts.deep_dive_topology:        emit_topology_report
  deep_dive_optional_artifacts.concurrency_analysis_report: emit_concurrency_report
```

主端用 `output_*` / `deep_dive_optional_artifacts.<key>`；子端 `functionality-deep-dive/core/default-config.yaml` 用 `emit_<key>`。两套命名同时存在，登记为 v4.2 遗留 #1。这意味着：
- 主端开关与子端开关需要"双向感知"才能保证 F1/F2/F3 默认产物落盘开关生效。
- 任何接入方需要同时熟悉两套键名。

### 2.6 文档版本爆炸与历史评审噪声 + 设计决策注释散布【V1.1 扩展 — 外部 §2.9.1 借鉴】

`mobile-qa-workflow/` 根目录有：
- `QUALITY-AUDIT-CONSTRUCTION-PLAN.md` / `-v1.md` / `-v1-REVIEW.md` / `-v2.md` / `-v2-REVIEW.md` / `-v2.1.md` / `-v2.1-REVIEW.md` / `-v2.2.md` / `-REVIEW-2026-04-20.md`
- `QUALITY-AUDIT-REPORT.md` / `-v1.1.md` / `-v1.1-REVIEW.md` / `-v1.2.md` / `-v1.2-REVIEW.md` / `-v1.2.1.md` / `-v1.2.1-REVIEW.md`
- `QUALITY-AUDIT-REVIEW.md`

合计 ~17 份历史方案/评审，约 50+ 万字。在仓库根目录与 `core/` 同级，对新接入者构成显著认知负担。其中 v2.2 是当前版本，前面所有版本均为历史决策（D1-D19）追溯材料。

**V1.1 新增观察**：除了根目录文档，**D1-D19 的解释还散布在 XML 注释 / YAML 注释 / phase 文件 / system-prompt 中共 50+ 处约 165 行**：
- workflow.xml: ~60 行注释
- P2: ~45 行注释
- P3: ~20 行注释
- core-rules.xml: ~15 行注释
- workflow-status-template.yaml: ~25 行注释

同一个 D14 解释在 5 个不同位置被改写过，互相已经轻微漂移。这部分注释对 LLM 执行没有实质帮助，应统一外迁到 `doc/adr/`（O4+）。

### 2.7 CI 守门覆盖缺口【V1.1 新增 — 外部 §2.10 借鉴】

当前 CI 只有：
- `eval.yml`：跑 eval-cases
- `qa-workflow-schema-check.yml`：调用 `scripts/check-config-schema.sh` 校验 config key 白名单

**缺失的关键校验**：

| 校验项 | 防止的 bug 类型 | 实现复杂度 | V1 是否覆盖 |
|--------|---------------|-----------|------------|
| `current_state` enum 校验 | 单值写入漂移（如 `RCA-InProgress`）| 低（grep + diff） | ✅ O5 配套 |
| `system-prompt.md` 与 `core/` sync 校验 | Limited 平台漂移 | 低（关键 token 对比） | ✅ O5 配套 |
| phase-abort/phase-complete 的 state 参数枚举检查 | B1* 类 — 写入非法状态 | 低（grep + diff） | ❌ 需 O22 |
| step-pause-registry 与编排器 switch 一致性 | step-pause 漏处理 | 低（yaml parse + grep） | ❌ 需 O22 |
| io-contract 声明 vs phase 实际 template-output 一致性 | 产物遗漏/多余 | 中（XML parse） | ❌ 需 O22 |
| subagent invoke 中的 `confidence_input`/`base_score` 参数存在性 | C2 类 — Schema-Violation | 中（grep 调用处） | ❌ 需 O22 |
| deep-dive 子配置键名与主配置 config-schema 白名单交叉检查 | 键名漂移 | 低 | ❌ 需 O22 |

详见 O22（§3.2.22）4 件套补全方案。

---

## 3. 优化方案（按"零风险 → 中风险 → 长期演进"分层）

### 3.1 P0 — 立即可做、零业务影响（≤ 0.5 人日）

#### O1. 修复 `p2-spec-definition.md` 末尾的 `RCA-InProgress` 漂移（无需任何人评审）

```186:188:mobile-qa-workflow/phases/p2-spec-definition.md
        <step n="9" goal="输出产物">
            ...
            <action>更新 {workflow_status}：current_state = RCA-InProgress</action>
```
改为 `current_state = RCA-Designing`。

**为何不影响效果**：编排器目前对未知值走 default → goto step 2，行为上等价于"按 stepsCompleted 推断下一阶段"，与显式写 `RCA-Designing` 路由结果一致；只是消除 enum 漂移。

#### O2. 修复 `p1-intake.md` 重复的 `step n="5"`

```200:206:mobile-qa-workflow/phases/p1-intake.md
    <step n="5" goal="优先级评估">
        ...
    </step>
    <step n="5" goal="输出 Issue Card">
```

`system-prompt.md` 同处也有同名 bug。改为 `step n="6"` 并整体重新编号 6 → 7。

**为何不影响效果**：`step` 编号仅作 LLM 顺序提示，不参与运行时分支判断；修正后避免"第 5 步执行两次"的潜在歧义。

#### O3.【V1 修订】**归档 5 个废弃 deep-dive agent**（不再"物理删除"）

> **F2 修订**：原版方案为"物理删除 + 删 `core-rules.xml` 5 行声明"，但子编排 `functionality-deep-dive/core/workflow.xml:21-30` + `agents/README.md:10-17` 表明老会话恢复仍依赖这些文件。改为"归档 + 退役标注"路径。

**改造**：
1. 把 `functionality-deep-dive/agents/{context-reconstructor,state-analyst,temporal-analyst,challenger,arbiter}.md` 5 个文件移入 `functionality-deep-dive/agents/archive/v3-legacy/` 子目录。
2. `core-rules.xml:92-96` 的 5 行 `<agent>` 声明保留，但每行加 `deprecated="true" recovery_only="true"` 属性，并在 LLM 提示中加 "仅供 v3-legacy 会话恢复，新会话禁用" 注释。
3. `functionality-deep-dive/agents/README.md:10-17` 把 "已废弃但保留兼容" 段落升级为 "**已退役（仅 v3-legacy 会话恢复）** —— 文件位于 `archive/v3-legacy/`"，并加退役计划（v4.3 物理删除前提：当前所有会话 schema_version ≥ 4 + 90 天无 v3-legacy 流量）。
4. CI 加 grep 守门：新会话的 stepsCompleted 中不应出现这 5 个 agent 名（出现即报错）。

**为何不影响效果**：
- 老会话恢复时按 `workflow_version=v3-legacy` 路径走，路径中的 `<load target="archive/v3-legacy/...">` 调整后仍能加载，行为等价。
- 新会话（默认 `workflow_version=v4-composite`）从未引用这 5 个 agent。
- 物理删除推迟到 v4.3（90 天观察期 + 流量统计后），消除"删除 = 破坏老会话"风险。

**风险等级**：从原版"零风险" 调整为 **"低风险（兼容性敏感）"**——必须先做 grep 全量验证 + 老会话回放测试 1 例。

#### O4+【V1.1 扩展 — 外部 §2.9.1 借鉴】**历史文档归档 + 设计决策 ADR 化 + 散布注释外迁**

**事实**：V1 原 O4 仅归档 17 份 QUALITY-AUDIT 历史文档；外部报告进一步指出，**D1-D19 的解释散布在 XML 注释 / YAML 注释 / phase 文件 / system-prompt 共 50+ 处约 165 行**，是更隐蔽的同步债。

**改造（三步走）**：

**Step 1（V1 原方案）：历史文档归档**
- 把 17 份历史 QUALITY-AUDIT 文档移到 `mobile-qa-workflow/archive/v4.1-history/`
- 根目录只保留：`QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md`（当前版）+ `QUALITY-AUDIT-REPORT-v1.2.1.md`（当前审计源）

**Step 2（V1.1 新增）：ADR 目录建立**
- 新建 `doc/adr/`，每条决定一个文件，命名 `<NNN>-<slug>.md`：
  ```
  doc/adr/
  ├── 001-current-phase-result-runtime-only.md      (D1)
  ├── 008-step-pause-userinputs-namespace.md         (D8)
  ├── 014-step-pause-scope-restriction.md            (D14)
  ├── 015-userinputs-mirror-allowlist.md             (D15)
  ├── 016-step-pause-required-params.md              (D16)
  ├── 017-non-bug-context-persistence.md             (D17)
  ├── 018-parse-error-circuit-breaker.md             (D18)
  ├── 019-legacy-step-pause-allowlist.md             (D19)
  └── ...
  ```
- 每个 ADR 文件结构：背景 / 决定 / 替代方案 / 影响 / 状态（active/superseded）

**Step 3（V1.1 新增）：散布注释外迁**
- 全仓库扫描 `<!-- D\d+: ... -->` 与 `# D\d+: ...` 形式的解释性注释
- 替换为 `<!-- ADR-014 -->` 单行引用（保留 ID 锚点，删除冗余解释）
- 长注释块（如 P2 step 4 的 45 行 Non-Bug 解释）整体删除，由 `<phase-abort reason="ADR-014">` 替代（依赖 O21）
- 预期净减行数：
  - workflow.xml: -60 行
  - P2: -45 行
  - P3: -20 行
  - core-rules.xml: -15 行
  - workflow-status-template.yaml: -25 行
  - **合计：~165 行注释外迁**

**为何不影响效果**：
- 纯文档归档与注释整理，工作流执行不读取这些注释；Skill 入口、core/、phases/ 业务逻辑完全不变。
- ADR 文件在 LLM 推理时**不被加载**（除非显式 `<load>`），不增加 token 预算。
- LLM 看到 `ADR-014` 引用后，若需要追溯历史可主动读 `doc/adr/014-*.md`，但默认执行不需要。

**与 O21 的依赖**：Step 3 的"长注释整体删除"依赖 O21 的 `<phase-abort reason="ADR-XXX">` 已落地；若 O21 未先做，Step 3 只能做"短注释引用化"，长注释保留。

#### O5. 在 `system-prompt.md` 顶部加显式同步声明 + 自动校验脚本

短期不能消除内联拷贝（Limited 平台必须有它），但可以：
1. 在 `system-prompt.md` 头部加 `<!-- AUTOGEN-FROM: core/{core-rules,workflow,workflow-status-template}.* @ schema_version=4 / sync-check=YYYY-MM-DD -->`
2. 在 `scripts/` 下加 `check-system-prompt-sync.sh`，对比 `current_state` 枚举集合等关键 token 是否一致。

**为何不影响效果**：仅加校验，不改运行时；让漂移在 PR Review 阶段就被发现，而不是上线后才暴露。

#### O6. 给 phase 文件加文件级"幂等性约束"（注释级别）

phase 内"更新 workflow_status: current_state = X"的写入动作，建议加注释强调"该字段写入是幂等的（同值重写不影响）"，并约定：
- 同一 step 内对 `current_state` 的写入只允许一次（如有 switch，每个 case 内一次）；
- 这样 reviewer 读 phase 文件可以一眼数清状态写入点。

**与 O21 的关系**：O21 的 `<phase-abort>` / `<phase-complete>` 宏标签从结构上保证"每个 phase 出口只有一个声明"，O6 退化为"过渡期约束"——O21 落地后 O6 自动失效，可在 V1.2 移除。

### 3.2 P1 — 中等优化，需要回归验证（≈ 2-3 人日）

#### O13a.【V1 新增 — F1 finding】**统一 Spec-Uncertain 回复契约**（O13 的强前置）

> **F1 修订**：O13 直接迁移会让 Full 与 Limited 平台用户看到的选项不一致。必须先统一回复契约。

**事实再述**：
- Full 路径：`core/workflow.xml:184-205` 用 `result_field=spec_uncertain_choice, allowed_values=Confirm`（单值确认）
- Limited 路径：`system-prompt.md:165` + `phases/p2-spec-definition.md:235-239` 用 `1|2|S` 三选

**改造**：
1. 选定**统一契约 = `1|2|S` 三选**（理由：保留更多用户决策能力，与 P2 内联设计的"列出多种可能 spec → 用户选具体方向"语义对齐；Confirm 单选丢失了"选 spec 1/spec 2/并行分析"的语义）。
2. 把 `core/workflow.xml:184-205` 的 step-pause 改写为：
   ```xml
   <step-pause title="Spec 存在歧义，请确认 Expected Behavior：
   {spec_options}
   
   [result_field=spec_uncertain_choice]
   [allowed_values=1|2|S]
   请用 spec_uncertain_choice=1（或 2 / S）回复"
               result_field="spec_uncertain_choice"
               allowed_values="1|2|S">
       <option title="[1] {option_1}" action="spec_uncertain_choice=1"/>
       <option title="[2] {option_2}" action="spec_uncertain_choice=2"/>
       <option title="[S] Skip：先并行分析所有可能" action="spec_uncertain_choice=S"/>
   </step-pause>
   ```
3. 编排器 step 4 case Spec-Uncertain 的下游 switch 增加 1/2/S 三个 case 分支：
   - `1` / `2` → `current_state = Spec-Defining` + 回写选定 spec 到 `workflow_status.selected_spec_index`
   - `S` → `current_state = Spec-Defining` + 标记并行分析模式
4. 同步把 `system-prompt.md:165` 路由表描述对齐为 `1|2|S` 三选 + 同样的 switch 分支。
5. P2 phase 文件需要在写 `Spec-Uncertain` 状态前同时写入 `spec_options = [{option_1}, {option_2}]` 数据，供编排器渲染 step-pause 标题。

**为何不影响效果**：
- 这本身就是"将原本 Limited 平台已经在用的契约，正式化为跨平台权威"——对 Limited 平台是行为不变，对 Full 平台是恢复语义（`Confirm` 单选实际上已经丢失了该决策点的设计意图）。
- 所有 Spec-Uncertain 的下游处理（按选择 spec 走 P2 step 4-9）保持不变。

**为何必须做**：是 O13 + O17 的强前置——若不先统一契约，O13 把 phase 内联砍掉后 Limited 平台用户失去三选选项，O17 再把 system-prompt.md 自动构建后该差异被永久固化为"Limited 平台只能 Confirm"。F1 finding 的核心修复点。

**验收**：Cursor + Dify 各跑 1 个 issue，Spec-Uncertain 弹窗看到的选项**完全一致**（`1|2|S` 三选）。

#### O7. 状态机字段瘦身：删除 `rca_fanout_mode_snapshot`，统一用 `phase_history` 反查

**改造**：
- `phase_history[]` 中已经有"qa-root-cause"条目附带 `fanout_mode`；P3 重入需要还原时，按"最近一条 `phase=qa-root-cause`"反查即可。
- 删除 `workflow-status-template.yaml:37` 的 `rca_fanout_mode_snapshot` 字段。
- `p3-root-cause.md:214` 删除快照写入。
- 迁移脚本：v3→v4 已有，再加 v4→v4.1 的 `rca_fanout_mode_snapshot` 移除步骤（保留旧字段为可选兼容）。

**为何不影响效果**：方案 A（`phase_history`）是主路径，方案 B（snapshot）是兜底，但当 phase_history 写入正确时 B 是冗余。可在迁移脚本中加"兜底防御：若 phase_history 为空但 snapshot 存在，按 snapshot 还原"以保留兼容性。

#### O8. 合并 `fix_strategy_mode` 与 `fix_fanout_mode`（同义字段）

**事实**：`p4-fix-design.md:33-37` 实际写入 `fix_fanout_mode = {fix_strategy_mode}`（同值赋两次）。

**改造**：保留 `fix_fanout_mode`（与 `fanout_mode` 命名对称，更清晰），废弃 `fix_strategy_mode`。
- `core/workflow-status-template.yaml` 删除 `fix_strategy_mode`。
- `p4-fix-design.md` 把所有 `fix_strategy_mode` 引用改为 `fix_fanout_mode`。
- 迁移脚本兜底：v4→v4.1 把现存 `fix_strategy_mode` 值同步到 `fix_fanout_mode`。

**为何不影响效果**：两字段同义，删除其一不改变路由。

#### O9. 计数器命名归类（注释级，不动 schema）

> **跨平台调整版（来自 §9）**：原版"统一为 `retries.{...}` 命名空间"在小 LLM 下读嵌套字段不如读扁平稳。改为注释级归类。

**改造**：
- `workflow-status-template.yaml` 在 5 个独立顶层字段附近加 `# group: retries` 注释块，说明它们是同一类语义。
- 不改字段名、不动 schema、不需迁移脚本。

**为何不影响效果**：完全无运行时变化，仅文档归类。需要嵌套命名空间的可在 v4.2 配合 O20 一并评估。

#### O10+【V1.1 扩展 — 外部 §2.1 借鉴】**step-pause-registry.yaml 数据驱动**（替代/扩展原 O10）

> **V1 原 O10 仅把 user_inputs 清空下沉编排器；V1.1 借鉴外部 R1，把整个 step 4 switch 数据化。**

**现状回顾**：`core/workflow.xml` step 4 的 6 个 case，每个都重复"重置计数 / 输出 step-pause / 解析回复 / 双写 / 派发 / 清空"6 步，共 ~150 行 switch + 各 case 内重复逻辑。新增 1 个 stop_state ≈ 60 行 5 文件改动。

**改造（两阶段）**：

**Stage 1：抽出注册表**

新建 `core/step-pause-registry.yaml`：
```yaml
# step-pause 注册表（C5 单一权威源）
# 编排器 step 4 按 current_state 命中后，按本表渲染 step-pause + 路由
registry:
  - state: Info-Insufficient
    title_template: "信息不足，需要用户补充以下缺失项：\n{missing_items}"
    result_field: info_insufficient_action
    allowed_values: [Submit]
    on_success:
      Submit: { set_state: Intake, goto: step_2 }

  - state: Spec-Uncertain   # O13a 已统一契约
    title_template: "Spec 存在歧义，请确认 Expected Behavior：\n{spec_options}"
    result_field: spec_uncertain_choice
    allowed_values: ["1", "2", "S"]
    on_success:
      "1": { set_state: Spec-Defining, write: { selected_spec_index: 1 }, goto: step_2 }
      "2": { set_state: Spec-Defining, write: { selected_spec_index: 2 }, goto: step_2 }
      "S": { set_state: Spec-Defining, write: { selected_spec_index: parallel }, goto: step_2 }

  - state: Non-Bug
    title_template: "Non-Bug 判定结果，请确认处理方向：\n{non_bug_context}"
    result_field: non_bug_user_choice
    allowed_values: [Accept, Reflow]
    mirror_to_top: true   # D15 双写标记数据化（O12 简化后仅 1 个字段，固定双写）
    on_success:
      Accept: { set_state: Done, terminal: true }
      Reflow:
        check: non_bug_reflow_count < 2
        true:  { set_state: Spec-Defining, increment: non_bug_reflow_count, goto: step_2 }
        false: { set_state: Human-Review }

  - state: RCA-LowConfidence
    title_template: "根因分析置信度不足（< 0.5），建议处理方向：{suggestion}"
    result_field: rca_lowconf_action
    allowed_values: [Retry, Human]
    on_success:
      Retry: { set_state: Spec-Defining, goto: step_2 }
      Human: { set_state: Human-Review }

  - state: Curation-Failed
    title_template: "上下文策展失败（置信度 < 0.4），请补充信息或转人工"
    result_field: curation_failed_action
    allowed_values: [Retry, Human]
    on_success:
      Retry: { set_state: Spec-Defining, goto: step_2 }
      Human: { set_state: Human-Review }

  - state: Human-Review
    title_template: "⚠️ 需要人工介入，请处理后告知继续方向"
    result_field: human_review_continue
    allowed_values: [Continue]
    on_success:
      Continue: { interpret_freetext: true, goto: step_2 }
```

**Stage 2：编排器 step 4 拆为 4a/4b/4c**（外部 §2.1 进一步借鉴）

```xml
<!-- Step 4a: 用户回复解析（仅在 step-pause 恢复时执行） -->
<step n="4a" goal="解析用户回复">
    <load target="mobile-qa-workflow/core/step-pause-registry.yaml"/>
    <action>按上一轮 result_field 在 registry 中查到 allowed_values，校验用户回复</action>
    <action>校验通过 → 写 user_inputs.<key>；mirror_to_top=true 时同时写顶层镜像</action>
    <action>校验失败 → parse_error_count += 1；≥3 → set_state=Human-Review；否则重触发 step-pause</action>
</step>

<!-- Step 4b: 阶段完成态判定 -->
<step n="4b" goal="处理 current_phase_result">
    <check if="current_phase_result == COMPLETE">
        <action>append stepsCompleted；更新 lastStep；reset parse_error_count</action>
    </check>
    <check if="current_phase_result == ABORT">
        <action>不追加 stepsCompleted；按 current_state 进入 4c</action>
    </check>
</step>

<!-- Step 4c: 状态路由（查表） -->
<step n="4c" goal="状态路由">
    <load target="mobile-qa-workflow/core/step-pause-registry.yaml"/>
    <check if="current_state 命中注册表">
        <action>按 registry 项的 on_success 派发：执行 set_state / write / increment / check</action>
        <action>派发完成自动清空 user_inputs.<key> 与 mirror_to_top（如有）</action>
        <action>若 terminal=true → 工作流完成；否则按 goto 跳转</action>
    </check>
    <check if="current_state == Done">
        <action>工作流完成，输出最终摘要</action>
    </check>
    <check if="current_state 未命中注册表且非 Done（流转态）">
        <goto step="2"/>
    </check>
</step>
```

**保留**：原 V1 O10 的"case 内显式清空 1 行作为兜底"思路保留——4c 的"自动清空"是编排器主路径，但允许 phase 文件在调试场景显式清空（**双重保险**）。

**为何不影响效果**：
- 注册表只是数据化表达，不改变状态转换语义。
- Stage 2 的 4a/4b/4c 拆分让 step 4 从 ~200 行混合关注点降到 ~60 行清晰三段。
- 新增交互态成本从"5 文件 60 行"降到"1 文件 8 行"。

**跨平台**：
- Limited 平台（Dify 等）：YAML 注册表对小 LLM 比 200 行嵌套 XML switch 更易读，**反向收益**。
- 注册表加载到 system-prompt.md（O17+ 自动构建后纳入分层 L1）。

**前置依赖**：必须先合入 O13a（避免把漂移契约固化到注册表）。

**Registry 权威性约束（V1.1 二次修订 / 质检 H3 接纳）**：

O10+ 落地后，编排器 `core/workflow.xml` step 4 内**严格禁止**任何"绕过 registry 的硬编码 case 分支"——所有 `current_state` 命中后的 step-pause 输出 + 派发 + 清空必须 **100% 走 registry 查表路径**。否则同步债只是从 XML switch 迁移到 YAML registry，没有真正消除。

**强制 CI 兜底**：`scripts/check-step-pause-registry.sh`（O22）必须包含三类校验：
1. **Registry 状态名合法性**：registry 中每个 `state` 必须在 `workflow-status-template.yaml` enum 集内（防注册表写错状态名）
2. **Registry 全覆盖**：编排器 step 4 实际触发 step-pause 的所有路径上的 `current_state`，必须全部在 registry 中有对应条目（防漏注册）
3. **硬编码 case 禁出**：`grep -E '<switch\b.*current_state|<check\b.*current_state\s*==\s*"(Info-Insufficient\|Spec-Uncertain\|Non-Bug\|RCA-LowConfidence\|Curation-Failed\|Human-Review\|Fix-Confirming)"'` 在编排器 step 4 范围内**必须返回零匹配**——所有交互态路由强制查 registry，发现硬编码立即报错

CI 校验通过后才允许合入。这是 H3 finding 的强约束闭环。

#### O11+【V1.1 扩展 — 外部 §2.5.1 + §2.5.2 借鉴】**invoke-subagent boilerplate 抽取 + `coder-agent.md` 拆三件 + `shared-input-guard.md` 提取**

> **V1 原 O11 仅整合 invoke-subagent boilerplate；V1.1 扩展为 agents 目录整体模块化。**

**Part A（V1 原方案）：invoke-subagent boilerplate 抽到 agents 内部（仅支持自描述加载的 Full 平台）**

约定子 Agent 启动时由 SubAgent 内部自行加载 `core-rules.xml` + 自身基座（在 `agents/challenger.md` 顶部加 `<setup>` 块声明依赖），调用方仅传业务参数。但同时保留旧调用方式作为 Limited 平台与 SubAgent 不支持自加载的 Full 平台的兼容路径。

**Part B（V1.1 新增）：`coder-agent.md` 拆三件**

当前 269 行单文件 → 拆为 3 个职责清晰的文件：

| 文件 | 内容 | 行数 | 加载时机 |
|------|------|------|---------|
| `agents/coder-agent.md` | 角色定义 + I/O 契约 + 工具白黑名单 + 变量命名规范 | ~70 行 | P5 invoke 时必加载 |
| `agents/coder-workflow.md` | 四阶段工作流（溯源→编码→验证→产出） | ~120 行 | P5 invoke 时必加载 |
| `reference/contract-checklist-spec.md` | Contract Checklist 规范 + Error Dump 模板 + 平台溯源映射表 | ~80 行 | P5 invoke 时加载；P6 验证时也可独立加载 |

**收益**：
- P6 验证阶段引用 Contract Checklist 规范时，不必加载完整 269 行（节省 ~190 行）
- 修改四阶段工作流不会影响 I/O 契约定义；diff review 更聚焦
- 角色定义保持精简，LLM 理解角色身份更快

**Part C（V1.1 新增）：`shared-input-guard.md` 提取**

`shared-arbiter-base.md`(83 行) 与 `shared-challenger-base.md`(91 行) 各有 ~15 行同构入参校验。提取为 `agents/shared-input-guard.md`（~10 行）：

```markdown
# Shared Input Guard Protocol

执行任何业务逻辑之前，按以下顺序校验必填入参：

1. 若 `{required_field}` 缺失/null/空字符串：
   - 输出 `[Schema-Violation: missing {required_field}]`
   - 立即停止，不产出任何业务输出
2. 若 `{required_field}` 存在但类型不匹配（如非数值）：
   - 输出 `[Schema-Violation: invalid {required_field} type]`
   - 立即停止

> 校验失败是调用方契约错误，不转为 Human-Review。
```

Arbiter/Challenger base 各改为：
```markdown
## 入参校验
<load target="agents/shared-input-guard.md"/>
- required_field = base_score（Arbiter）/ confidence_input（Challenger）
```

**为何不影响效果**：
- Part A：依赖加载时机一致（SubAgent 启动时加载 vs 调用方注入字符串再加载），只是减少调用方 prompt 长度与漂移面
- Part B：拆分后总加载行数与单文件等价，但按需加载场景节省 token
- Part C：校验语义不变，消除两个 base 的同构维护负担

**跨平台**：Part A 仅适用于 Cursor/Claude Code/Trae 等支持 SubAgent 自加载的 Full 平台；Limited 平台保留显式 `<load>` 三连击。Part B/C 跨平台等价。

#### O12. 简化"白名单受限双写"协议（保留双写实现，删除白名单机制）

> **跨平台调整版（来自 §9）**：原版"删除顶层镜像、全量改读 `{user_inputs.X}`" 对小 LLM 嵌套引用风险高。改为"保留顶层镜像字段，仅删除白名单复杂度"。

**事实**：D8/D15 的"白名单受限双写"是为 1 个字段 `non_bug_user_choice` 维护了一套白名单 + PR Review + CI + 多文档的复杂协议。

**改造**：
- **保留** `workflow-status-template.yaml` 顶层 `non_bug_user_choice` 字段（让小 LLM 能用扁平 `{non_bug_user_choice}` 引用）。
- **保留** `core/workflow.xml` step 4 的双写实现（user_inputs.X + 顶层 X 均写）。
- **删除** "白名单"协议机制：把 D15 协议从"白名单受限双写"改为"固定双写 1 个字段 `non_bug_user_choice`"；不再维护白名单文件 / PR Review 守门 / CI 校验 / 跨文档说明。
- 删除 `core-rules.xml` 中"白名单受限"段落（保留"双写规则"段落）。
- 删除 `system-prompt.md` 与 `PLATFORM-GUIDE.md` 中"顶层镜像白名单"说明段落。

**与 O10+ 的关系**：O10+ 的 registry 中 `mirror_to_top: true` 标记完成了 D15 协议的数据化——只在 Non-Bug 这一行标 true，其他行不标。O12 删的是"白名单元协议"复杂度（白名单文件 + 跨文档说明），保留的双写实现已被 registry 表达。

**为何不影响效果**：
- 编排器读取与写入路径**完全不变**（仍然双写 + 仍然两边都能读）。
- 只删除了"白名单"的元协议复杂度——为 1 个字段建一套白名单是显著过度工程。
- v4.2 整体收敛改为 v4.3 评估（届时 LLM 普遍能力提升后再考虑全量改读 `user_inputs.X`）。

#### O13. P2 内联 Spec-Uncertain step-pause 真正迁出（D14 完整收口）— **依赖 O13a + O21 完成**

**前置**：O13a 必须先合入并通过 Cursor + Dify 双平台回归；O21 提供 `<phase-abort>` 宏标签让 P2 改写更简洁。

**改造**：
- 删除 `phases/p2-spec-definition.md:230-240` 的内联 step-pause。
- P2 phase 文件改为（使用 O21 宏标签）：
  ```xml
  <phase-abort state="Spec-Uncertain"
               fields='{"spec_options": "<可能选项数组>"}'
               reason="ADR-014"/>
  ```
- 编排器 step 4 case Spec-Uncertain 已经在 O13a 中改造为 `1|2|S` 三选 + O10+ 中转为注册表项，此处仅需删除 phase 内联即可。
- 同步删除 `legacy-phase-step-pause-allowlist.txt` 中 `p2-spec-uncertain` 条目。

**为何不影响效果**：因为 O13a 已经统一了契约，P2 phase 内联与编排器 case 已是完全等价的两份实现，删除任一份对用户体验都没有变化。

#### O14. P4 内联 Fix Design 确认 step-pause 同样迁出

**现状**：`p4-fix-design.md:136-142` 有内联 Fix Design Confirm step-pause，违反 D14。

**改造**：
- `p4-fix-design.md` step 6 末尾改为（使用 O21 宏标签）：
  ```xml
  <phase-abort state="Fix-Confirming" reason="ADR-014"/>
  ```
- 在 `workflow-status-template.yaml` 头部 enum 集中加 `Fix-Confirming`（**enum 集变更需同步 `system-prompt.md` 镜像**——若已合入 O17+ 自动构建则自动同步）。
- 在 `core/step-pause-registry.yaml`（O10+）中加新条目：
  ```yaml
  - state: Fix-Confirming
    title_template: "Fix Design 已生成，请确认是否继续：\n{fix_design_summary}"
    result_field: fix_confirming_choice
    allowed_values: [Continue, Revise]
    on_success:
      Continue: { set_state: Fix-Implementing, goto: step_2 }
      Revise:   { set_state: Fix-Designing,    goto: step_2, increment: fix_retry_count }
  ```
- 同步删除 allowlist 该条目，并删除 `legacy-phase-step-pause-allowlist.txt` 整个文件（清空）+ 从 PR-8 CI 中删除该文件读取逻辑。

**为何不影响效果**：交互含义不变（用户依然看到 Continue/Revise 选项），只是触发位置统一到编排器，符合 D14 + 消除 D19 整套维护成本（allowlist 文件 + CI 逻辑 + 维护规约）。

**前置依赖**：因为引入了新 enum 值 `Fix-Confirming`，**必须配套 O5 sync 校验或 O17+ 自动构建**，否则手维护的 `system-prompt.md` 与 `workflow-status-template.yaml` 立即出现枚举漂移。

#### O15. 合并 P3 三档 fan-out 中的"升级早退"路径为统一函数

**现状**：`p3-root-cause.md` 中三档 fan-out 各自有"升级条件 → 设字段 → ABORT"代码块，结构高度重复但分散：

- L57-67：simple-single 失败 → medium-challenge
- L96-106：medium-challenge 失败 → complex-arbitrated  
- L147-158：complex-arbitrated 不收敛 → Human-Review

**改造**：抽出统一的"P3 升级路由"段（位于 step 5 末尾），按 `escalation_target` 变量（由各 fan-out 块设置）执行单一升级动作集合。

**与 O21 的协同**：升级早退的 ABORT 写法用 `<phase-abort>` 宏一行表达，进一步缩短：
```xml
<phase-abort state="RCA-Designing"
             fields='{"fanout_mode": "{escalation_target}",
                      "reroute_reason": "simple_path_not_closed",
                      "reroute_from_phase": "qa-root-cause",
                      "reroute_target_phase": "qa-root-cause",
                      "rca_retry_count": "+1"}'
             reason="ADR-015"/>
```

**为何不影响效果**：升级语义不变，只是减少代码重复。

#### O16. deep-dive 主子配置键名收敛（v4.2 遗留 #1 提前）

**改造**：选择主端命名 `deep_dive_optional_artifacts.<key>` 作为权威，删除子端 `emit_*` 命名：
- `functionality-deep-dive/core/default-config.yaml` 把 `emit_environment_factor_report` 改为 `deep_dive_optional_artifacts.environment_factor_report`，与主端对齐。
- `config-schema.yaml` 删除 `known_legacy_aliases` 块。
- `f1-context-reconstruction.md` 等 phase 文件中所有 `emit_*` 引用改为 `deep_dive_optional_artifacts.*`。

**为何不影响效果**：键名统一不改变开关语义；接入方负担降低，CI 不再需要 alias 校验。

#### O21【V1.1 新增 — 外部 §2.2 + §2.8 借鉴】**`<phase-abort>` / `<phase-complete>` 声明式宏标签**

**现状回顾**（§2.1.5）：每个 ABORT 点需要写 3-5 行 action + 大量注释，漏写任一步即复现 B1* bug。当前 phase 文件中该模式重复 ~10 处。

**改造**：定义两个标准宏标签，把"5 步咒语"封装为一行声明。

**Step 1：在 `core-rules.xml` 的 `<supported-tags>` 中新增**

```xml
<tag name="phase-abort">
    <rules>
        <rule>Phase 早退的声明式宏标签（语法糖），等价于以下动作序列：
            1. 更新 {workflow_status}：current_state = {state}
            2. 更新 {workflow_status}：{fields} 中的全部 key-value
            3. 设置 current_phase_result = ABORT
            4. 退出当前 phase（不执行后续 step）
        </rule>
        <rule>禁止在 phase-abort 之后继续执行任何 step</rule>
    </rules>
    <params>
        <param name="state" required="true">目标 current_state（必须在权威枚举集内）</param>
        <param name="fields" required="false">附加写回字段，JSON 格式（支持 "+1" 表示自增）</param>
        <param name="reason" required="false">触发原因引用，建议使用 ADR-XXX</param>
    </params>
</tag>

<tag name="phase-complete">
    <rules>
        <rule>Phase 正常完成的声明式宏标签，等价于：
            1. 更新 {workflow_status}：current_state = {state}
            2. 更新 {workflow_status}：{fields} 中的全部 key-value
            3. append phase_history 一条新记录（含 fanout_mode 等元数据）
            4. update config_source 注册产物路径
            5. 设置 current_phase_result = COMPLETE
            6. 退出当前 phase
        </rule>
    </rules>
    <params>
        <param name="state" required="true">目标 current_state</param>
        <param name="fields" required="false">附加写回字段，JSON 格式</param>
        <param name="append_history" required="false">phase_history 追加项</param>
        <param name="update_config" required="false">config_source 批量注册项</param>
    </params>
</tag>
```

**Step 2：phase 文件改写示例**

P2 step 4 Non-Bug 早退从 5 步 + 45 行注释 → 1 行：
```xml
<check if="判定为 Non-Bug">
    <action>生成 Non-Bug Resolution Report 文本</action>
    <phase-abort state="Non-Bug"
                 fields='{"non_bug_context": "{report_text}"}'
                 reason="ADR-014"/>
</check>
```

P3 step 5 升级早退从 12 行 → 5 行：
```xml
<check if="反事实校验失败 或 最终置信度 < 0.70">
    <phase-abort state="RCA-Designing"
                 fields='{"fanout_mode": "medium-challenge",
                          "reroute_reason": "simple_path_not_closed",
                          "reroute_from_phase": "qa-root-cause",
                          "reroute_target_phase": "qa-root-cause",
                          "rca_retry_count": "+1"}'
                 reason="ADR-015"/>
</check>
```

P3 step 10 正常完成从 6 行 → 3 行：
```xml
<phase-complete state="Fix-Designing"
                fields='{"reroute_reason": null, "reroute_target_phase": null}'
                append_history='{"phase": "qa-root-cause", "fanout_mode": "{fanout_mode}"}'
                update_config='{"output_rca_report": "{output_file}"}'/>
```

**Step 3：CI 静态校验（依赖 O22）**
- 每个 phase 的最后一个 `<step>` 必须包含 `<phase-complete>` 或 `<phase-abort>`
- `state` 参数必须在权威 enum 集内
- `fields` 中的 key 必须在 `workflow-status-template.yaml` 中存在

**效果**：
- Phase 文件中所有 ABORT 点从"5 步 + 注释"变为"1 行声明"
- **结构性消除 B1* 类 bug**（漏写任何一步的风险归零）
- 注释外迁后 phase 文件专注于业务逻辑，信噪比大幅提升
- 配合 O4+ Step 3 删除 ~165 行散布注释

**为何不影响效果**：
- 宏标签只是语法糖，展开后语义与当前完全相同
- LLM 解释该标签时按 `core-rules.xml` 中的 `<rule>` 展开
- 跨平台等价：所有 LLM 都能读 `<rule>` 块的展开规则
- 与 V1 §6 第 11 条"`current_phase_result = ABORT` 显式赋值"**不冲突**——宏标签展开后内部仍然是显式赋值，只是写在 `<rule>` 中而非每个 phase 重写

**前置依赖**：无（独立可做）；但**O13/O14/O15 改写时强烈推荐使用本标签**，否则 v4.2 后还是 5 步咒语堆积。

**跨平台**：
- Full 平台 + 大 LLM：完全等价
- Limited 平台 + 小 LLM：宏标签首次解释时 LLM 需要"内联展开 4 步"，可能略增推理负担；缓解方式是在 `system-prompt.md`（O17+ 分层后的 L1）中把展开规则放在显眼位置

**风险等级**：中（首次合入后人工抽查 LLM 执行记录确认正确展开）

**执行引擎适配性确认（V1.1 二次修订 / 质检确认题接纳）**：

仓库实际执行模型已核查，确认 O21 在当前架构下**可行**：

1. **执行模型本质 = LLM 自执行 + CI 模式扫描**：`core-rules.xml` 顶部 `<llm critical="true">` 块全部是写给 LLM 看的 mandate，不存在外部"标签解释器"或"DSL 编译器"组件。
2. **CI 不做"标签白名单守门"**：`core-rules.xml:25-33` 显式声明"PR-8 CI 不做元素白名单校验"，新增 `<phase-abort>` / `<phase-complete>` 不会被现有 CI 拒绝。
3. **已有"协议级标签由 LLM 按 `<rule>` 自解释"的成熟先例**：`core-rules.xml:100-106` 的 `<workflow-status-routing>` 标签整段就是"文档+协议描述"，LLM 读 `<rule>` 自动遵守，**无需任何 parser 支持**——这正是 O21 宏标签的同款模式。

**3 条护栏（采纳门槛）**：
- **H1：在 `core-rules.xml` `<supported-tags>` 内显式定义两个新 `<tag>` 块**，含完整 `<rule>` 展开规则（4 步动作）+ `<params>` 必填校验。与 `<workflow-status-routing>` 同款先例，让 LLM 在加载 core-rules 时一次性看到展开协议，不依赖"内化记忆"。
- **H2：在 `system-prompt.md`（O17+ 分层后的 L1 层）置顶位置同样写入完整展开规则**（不只是引用，要写完整 4 步）。Limited 平台单 prompt 模式 LLM 不会去翻 `core-rules.xml`，必须就地能看到展开规则；防小 LLM 漏展开。
- **H3：B2.5 落地后**，**前 5 个使用宏标签的 PR 强制人工抽查 LLM 执行记录 ≥ 10 例**，确认 4 步动作（state / fields / ABORT / 退出）全部正确执行。LLM 解释一致性是经验性的，CI 静态校验只能查"宏是否被书写"不能查"宏是否被正确展开"，必须运行时兜底。

**命名冲突规避（V1.1 二次修订）**：

仓库内 `mobile-qa-workflow/construction-plans/v2.2/pr4-phase-abort-fanout-isolation.md` 已经把 "phase-abort" 用作 PR-4 子命题名（语义是 "ABORT 字段写回隔离协议 / C10"，**不是 XML 宏标签**）。O21 引入 `<phase-abort>` XML 标签时，**强制要求**在 ADR-021（O4+ 新增 `doc/adr/021-phase-abort-macro.md`）首段显式区分：

> **本 ADR 中的 `<phase-abort>` 是 v4.2 引入的宏标签（macro tag），与 PR-4 文档名 "phase-abort-fanout-isolation" 中的 "phase-abort" 是不同概念**：前者是 DSL 语法糖，后者指 ABORT 字段写回隔离协议（C10）。两者的关系是：本宏标签**实现了** PR-4 的 ABORT 写回隔离协议，是其语义的封装。

避免后续 reviewer 把 PR-4 的 "phase-abort" 与 V1.1 的 `<phase-abort>` 混读。

#### O22【V1.1 新增 — 外部 §2.10 借鉴】**CI 安全网 4 件套补全**

**现状回顾**（§2.7）：当前 CI 仅校验 config-schema 白名单与 eval-cases 跑分，缺 5+ 项关键守门。

**改造**：新增 4 个 CI 脚本（与 V1 已有的 O5 配套 sync 校验合计 6 项）：

| 脚本 | 防护 | 实现要点 | 依赖 |
|------|------|---------|------|
| `scripts/check-state-enum.sh`（V1 O5 配套）| 非法状态写入 | grep `current_state = X` → 与 `workflow-status-template.yaml` 头部 enum 集 diff | - |
| `scripts/check-system-prompt-sync.sh`（V1 O5 配套）| 内联拷贝漂移 | 比对 system-prompt.md 与 core/ 关键 token | - |
| `scripts/check-phase-abort-structure.sh`【V1.1 新增】 | B1* 类 / phase 出口规范性 | XML parse 各 phase 文件，验证最后 step 含 `<phase-abort>` 或 `<phase-complete>`；`state` 在 enum 内；`fields` key 在 template 内 | O21 |
| `scripts/check-step-pause-registry.sh`【V1.1 新增 / V1.1 二次修订加严】 | step-pause 漏处理 + Registry 权威性 | 三类校验：(1) registry 状态名必须在 enum 内；(2) 编排器实际触发 step-pause 的所有路径上的 `current_state` 必须在 registry 中有对应条目（防漏注册）；(3) **硬编码 case 禁出**——编排器 step 4 范围内 `grep` 任何 `<switch case="<交互态>">` 形式必须返回零匹配，强制所有路由查 registry（详见 §3.2.10 末尾约束）| O10+ |
| `scripts/check-io-contract.sh`【V1.1 新增】 | 产物声明一致性 | 解析 workflow.xml `<io-contract>` + 各 phase `<template-output>` 的 `file` 属性，对照 → 声明但未输出报错 | - |
| `scripts/check-subagent-params.sh`【V1.1 新增】 | C2 类 Schema-Violation | grep invoke-subagent 调用 → 验证 `confidence_input` / `base_score` 等必填参数存在 | - |

**Step 1：分批合入**
- B0：V1 O5 已含的 2 个脚本（state-enum + sync）+ V1.1 新增的 `check-io-contract.sh` + `check-subagent-params.sh`（独立无依赖）
- B2.5：`check-phase-abort-structure.sh`（与 O21 同批）
- B3：`check-step-pause-registry.sh`（与 O10+ 同批）

**Step 2：CI workflow 集成**
- 在 `.github/workflows/qa-workflow-schema-check.yml` 中追加 6 个脚本调用
- 任一脚本失败 → CI 红，PR 不可合入

**效果**：
- 5 类历史 bug（B1* / 枚举漂移 / 产物遗漏 / Schema-Violation / step-pause 漏处理）从"靠 PR Review 兜底"变为"CI 自动拦截"
- PR Review 焦点从"找漂移"转移到"评估业务变更"

**为何不影响效果**：纯 CI 守门，不改运行时；让历史 bug 在 PR 阶段就被发现而非线上才暴露。

**跨平台**：CI 守门作用于代码层，与平台无关；对所有平台一致受益。

**风险等级**：低（脚本失败可降级为 warning，待人工确认后再升级为 error）

### 3.3 P2 — 长期演进（≈ 1 周以上，需更谨慎的回归）

#### O17+【V1.1 扩展 — 外部 §2.3 借鉴】**把 `system-prompt.md` 改为"由 `core/` 自动构建"+ 输出 L0-L4 分层产物**

> **V1 原 O17 仅"自动构建消除漂移"；V1.1 借鉴外部 R3，把生成器目标从"单一全量文件"升级为"L0-L4 分层产物"。**

**现状回顾**（§2.3.1）：569 行的 system-prompt.md 是"什么都有但什么都不精"的拷贝版本，完整保留 step-pause 协议 + workflow-result-protocol + v4.1 字段表 + phase 简化骨架，但简化不统一（有些保留 v4.1 注释，有些不保留）。

**改造（两阶段）**：

**Stage 1（V1 原方案）：自动构建消漂移**

- 新增 `scripts/build-system-prompt.py`，从 `core/{core-rules.xml, workflow.xml, workflow-status-template.yaml, default-config.yaml, workflow-model.yaml, step-pause-registry.yaml}` + 各 `phases/*.md` + `agents/*.md` 关键节摘要按模板生成
- PR-8 CI 加门禁：`system-prompt.md` 必须由 `build-system-prompt.py` 生成（diff 校验）

**Stage 2（V1.1 新增）：分层产物 L0-L4**

生成器输出 5 个分层片段，按需注入：

| 层级 | 内容 | 行数估计 | 加载时机 | 设计原则 |
|------|------|---------|---------|---------|
| **L0: 核心身份** | 角色定义、6 阶段序列、状态机转换图 | ~30 行 | 每轮都需要 | 跨 phase 不变 |
| **L1: 执行规则** | 步骤顺序、ABORT 协议（含 `<phase-abort>` 展开）、step-pause 输入规范、step-pause-registry 路由表 | ~50 行 | 每轮都需要 | 跨 phase 不变 |
| **L2: 当前阶段逻辑** | 按 current_state 动态展开（仅当前阶段 + 前后 1 阶段的决策树）| ~80 行 | 按 current_phase 注入 | 决策树式，删除步骤式叙述 |
| **L3: 推理工具箱** | OVHSC 五步 + 置信度公式 + 证据权重表 + Challenger 7 维 + Arbiter 公式 | ~60 行 | P3/P4 时注入 | 完整保留（V1 §6 第 1 条要求）|
| **L4: 平台知识** | 分类策略引导（按 issue_card 主分类只注入命中分类）| ~40 行 | 按分类注入 | 与 O24 reasoning-chain 拆分对齐 |

**生成器对 Limited 平台的输出策略**：
- **Dify / Coze 单 prompt 模式**：合并 L0+L1+L2(全量)+L3+L4(全量) ≈ 350 行（仍比当前 569 行少 38%）
- **支持多轮注入的 Limited 平台**（如 OpenAI Assistants）：L0+L1 常驻，L2 按 phase 动态注入，L3 按 phase 注入，L4 按分类注入；单轮峰值 ~180 行

**关键变化**（外部 §2.3 借鉴）：
1. 删除所有设计决策注释（D1/D14/D15/D17/D18 解释）— 改为 ADR-XXX 引用（与 O4+ 协同）
2. 删除 v4.1 字段表的完整重复 — 改为只保留"最少持久化字段清单"（一行枚举）
3. phase 逻辑从"压缩全文"改为"决策树"

精简后 P3 决策树示例：
```markdown
## Phase 3: 根因分析
1. 证据阈值：纯 C 级 → ABORT(Spec-Defining)
2. Fan-out 路由：读取 analysis_complexity/fanout_mode → 选择 simple/medium/complex
3. 执行 OVHSC（详见 L3）
4. 升级条件：反事实失败|置信度<0.70 → 升级 fanout
5. 专项路由：功能复杂 + 状态/并发 → Deep-Dive
6. 边界判定：功能/网络类 → 抓包确认归属
7. 输出：rca-report.md；置信度≥0.5 → Fix-Designing；<0.5 → ABORT(RCA-LowConfidence)
```

**为何不影响效果**：
- L3 推理工具箱完整保留 OVHSC 五步 + 置信度公式 + 证据权重表（V1 §6 第 1 条不可触动）
- L1 执行规则完整保留 ABORT 协议和 step-pause 格式
- 在 Dify/Coze 环境下用 eval-cases 做对照实验验证无降级

**跨平台**：
- **对 Limited 平台净正贡献**：消除 Full / Limited 行为漂移源（含 §2.2.3 揭示的 Spec-Uncertain 漂移类问题）
- **Token 预算可控**：单 prompt 模式 350 行；多轮注入模式峰值 180 行
- 首次构建后人工 diff 与现版本，确认零业务语义差异

**前置依赖**：必须在 O13a 完成后再做（避免把已漂移的契约固化到自动构建产物中）

#### O18.【V1 ❌ 放弃】~~`current_phase_result = ABORT` 模式改为更显式的"phase 返回值约定"~~

> **跨平台风险否决**：原版改造方案在 Limited 平台 + 小 LLM 上风险高。详见 §9.3。**保留 `current_phase_result` 显式赋值机制不动**。

**与 O21 的对比**：O21 的 `<phase-abort>` 宏标签**展开后内部仍然是 `current_phase_result = ABORT` 的显式赋值**，只是把"5 步咒语"封装为一行声明。这是与 O18 的本质区别——O18 试图删除显式赋值，O21 只是隐藏书写形式但保留语义。

#### O19+【V1.1 扩展 — 外部 §2.5.2 借鉴】**agent 共享基座结构调整**

> **V1 原 O19 仅整合 wrapper 内重复；V1.1 借鉴外部 R5，配合 O11+ Part C 提取 `shared-input-guard.md`。**

**改造（两部分）**：

**Part A（V1 原方案）：保留 wrapper 文件，整合 wrapper 内重复内容**
- `agents/challenger.md` 保留为薄包装层文件（不删除）
- 把 challenger.md / arbiter.md 中重复的 scene 映射逻辑整合到 `shared-challenger-base.md` / `shared-arbiter-base.md` 内的 `<switch scene>` 分支
- wrapper 层只保留"加载基座 + 必要参数透传"

**Part B（V1.1 新增 — 与 O11+ Part C 联动）：提取 `shared-input-guard.md`**
- 见 O11+ Part C 详述
- 整合后 `shared-arbiter-base.md` 与 `shared-challenger-base.md` 各减少 ~12 行同构入参校验
- 入参校验语义统一在一处维护

**为何不影响效果**：scene 切换逻辑不变；入参校验语义不变；只是减少重复维护负担。

#### O20. functionality-deep-dive 子工作流的状态收编

**事实**：deep-dive 有自己的 `workflow-status-template.yaml`（含 `current_state` / `stepsCompleted` 等子集字段）+ 自己的 `workflow.xml` + 自己的 `workflow-model.yaml`。

**改造路径**：
- 中期：让 deep-dive 沿用主链路 `workflow-status.yaml`，仅扩展专属字段命名空间 `workflow_status.deep_dive.{...}`（替代独立 status 文件）。
- 编排器主链路在 P3 触发 deep-dive 时切换 `current_phase = deep-dive-f{1..5}`，复用现有 step 2 路由逻辑。

**与外部 §2.6.1 的差异**【V1.1 重申】：外部主张"DD-LowConfidence/DD-Human-Review 上提到主编排器"，**V1 维持否决**——子编排独立调度域是合理设计；折中方案是子工作流挂起时显式写入主 status 的 `specialized_workflow.status = DD-LowConfidence`，让主编排器在 P3 step 6 检测后做合理处理（**有感知能力但不参与调度**）。

**为何不影响效果**：状态字段名空间隔离即可避免冲突；主链路状态恢复时无需感知 deep-dive 是否完成（已有 `specialized_workflow.status` 字段）。优势是消除 2 套 schema/迁移脚本/编排器协议。这是较大重构，建议放到 v4.2 整体规划。

#### O23【V1.1 新增 — 外部 §2.7.1 借鉴】**`core-rules.xml` 拆 essential + dsl-reference**

**事实**：`core-rules.xml` 222 行中：
- `<supported-tags>` 占 ~100 行（O21 后还会增加 `<phase-abort>` / `<phase-complete>` 两个）
- `<available-agents>` 占 ~40 行
- `<llm>` mandates + `<WORKFLOW-RULES>` + `<workflow-result-protocol>` + `<human-review-protocol>` 占 ~70 行

phase 执行时**只需要后者 70 行**；DSL 标签白名单与 agent 列表大部分不需要。

**改造**：

**Step 1：拆分**
| 文件 | 内容 | 行数 | 加载场景 |
|------|------|------|---------|
| `core/core-rules-essential.xml` | `<llm>` mandates + `<WORKFLOW-RULES>` + `<workflow-result-protocol>` + `<human-review-protocol>` | ~70 行 | 每个 phase 首步必加载 |
| `core/core-rules-dsl-reference.xml` | `<supported-tags>` 完整白名单 + `<agent-taxonomy>` + `<available-agents>` | ~150 行 | 仅在需要解析新标签或 invoke subagent 时加载 |

**Step 2：phase 文件改动**
- 所有 phase `<load target="core-rules.xml">` 改为 `<load target="core-rules-essential.xml">`
- invoke-subagent 调用前若需要 dsl-reference 则显式 `<load target="core-rules-dsl-reference.xml">`

**Step 3：兼容性**
- `core/core-rules.xml` 保留为聚合入口（include essential + dsl-reference），向后兼容旧调用方

**效果**：
- 每个 phase 执行节省 ~150 行（约 3K-4K tokens）
- 6 个 phase 总节省 ~20K tokens
- Limited 平台单 prompt 模式不受影响（system-prompt.md 由 O17+ 自动构建按需聚合）

**跨平台**：
- Full 平台：直接受益
- Limited 平台：通过 O17+ 间接受益（生成器在分层注入时只在需要 dsl-reference 的 L 层引入）

**风险等级**：低（仅文件拆分 + 引用路径调整）

#### O24【V1.1 新增 — 外部 §2.7.2 借鉴】**`reasoning-chain` 按分类拆分**

**事实**：`reference/reasoning-chain.md`（~200 行）当前包含通用 OVHSC + 4 个分类专项推理引导（功能/UI/网络/兼容），P3 每次执行不论分类全量加载，3 个未命中分类的 ~90 行是浪费。

**改造**：

**Step 1：拆分**
| 文件 | 内容 | 行数 |
|------|------|------|
| `reference/reasoning-chain-core.md` | 通用 OVHSC 五步 + 置信度公式 + 证据权重表 | ~100 行 |
| `reference/reasoning-guide-functional.md` | 功能类专项推理引导 | ~30 行 |
| `reference/reasoning-guide-ui.md` | UI 类专项推理引导 | ~30 行 |
| `reference/reasoning-guide-network.md` | 网络类专项推理引导 | ~30 行 |
| `reference/reasoning-guide-compat.md` | 兼容类专项推理引导 | ~30 行 |

**Step 2：P3 改造**
- P3 step 5 必加载 `reasoning-chain-core.md`
- 根据 `issue_card.主分类` 加载对应 `reasoning-guide-{category}.md`
- 多分类场景（罕见）按权重最高分类加载，必要时人工 fallback 到全量

**Step 3：与 O17+ L4 对齐**
- O17+ Stage 2 的 L4 平台知识层按命中分类注入（生成器读 issue_card 后选择对应 guide）

**效果**：每次 P3 执行节省 ~90 行（约 2K-3K tokens）

**跨平台**：
- Full 平台：P3 phase 文件改 `<load>` 路径即可
- Limited 平台：通过 O17+ L4 按需注入

**风险等级**：低（仅文件拆分 + 加载路径分支判断）

#### O25【V1.1 新增 — 外部 §2.7.3 借鉴】**SubAgent 专用轻量 core-rules**

**事实**：P3 complex-arbitrated 模式中，4 个 invoke-subagent 各自 `<load target='core-rules.xml'>`。由于 SubAgent 是独立对话，重复加载不可避免——但 SubAgent **不需要**编排器协议（step-pause / workflow-result-protocol），目前都加载了完整 222 行。

**改造**：

**Step 1：新建 `core/core-rules-subagent.xml`（~30 行）**

只包含 SubAgent 需要遵守的规则：
- 步骤顺序约束（按 invoke 输入参数执行）
- 产物格式约束（按 `<output-contract>` 输出）
- 共享标签子集（`<load>` / `<action>` / `<check>` / `<output>`）
- 不包含：编排器协议 / step-pause / workflow-result-protocol / available-agents / 顶层 mandates

**Step 2：SubAgent 调用方改造**

```xml
<!-- 改造前 -->
<invoke-subagent name="challenger">
    <subagent_prompt>
        <load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
        ...
    </subagent_prompt>
</invoke-subagent>

<!-- 改造后 -->
<invoke-subagent name="challenger">
    <subagent_prompt>
        <load target='mobile-qa-workflow/core/core-rules-subagent.xml' prompt='加载 subagent 规范'/>
        ...
    </subagent_prompt>
</invoke-subagent>
```

**效果**：每个 SubAgent prompt 减少 ~190 行 core-rules 负载。
- P3 complex 路径有 4 个 SubAgent → 节省 ~760 行（~15K tokens）
- P4 complex 路径类似 → 节省 ~10K tokens

**跨平台**：
- Full 平台支持 SubAgent：直接受益
- Limited 平台 `env_subagent=false` 内联模式：本优化不适用（内联模式直接读主 prompt，core-rules 已经在 system-prompt.md 中按 O17+ 分层注入）

**风险等级**：低（新文件 + 调用方路径替换）

**前置依赖**：建议在 O11+ Part A（SubAgent 自描述加载）落地后做，可一并把"加载 core-rules-subagent.xml"放到 SubAgent 的 `<setup>` 块。

---

## 4. 落地节奏与风险隔离

### 4.1.0 跨批次硬依赖与降级路径（V1.1 二次修订 / 质检 H1+H2 接纳）

> 本节是 §4.1 批次表的**前置约束**。批次内的依赖在 §4.1 表后说明，**跨批次**的硬依赖与失败降级路径在此统一声明。

**Hard Dependency 1：B1 中 O17+ 的"首次构建"必须等待 B3 中 O13a 合入**

- **背景**：O17+ 自动构建 system-prompt.md 时，会以 `core/workflow.xml` 为权威源生成 step-pause 协议片段；若此时 O13a（统一 Spec-Uncertain 回复契约为 `1|2|S` 三选）尚未合入，生成器会把 `Confirm` 单选契约**永久固化**到自动构建产物中，Limited 平台行为静默漂移。
- **约束**：
  - B1 内的 sync 校验脚本（O5 配套：`check-state-enum.sh` + `check-system-prompt-sync.sh`）可以**先做**（独立于 O13a）
  - B1 内的 O17+ **生成器实现**可以先写
  - 但 **O17+ 的"首次构建并替换 system-prompt.md"** 必须**严格等待** B3 中 O13a 合入并通过 Cursor + Dify 双平台回归后才能执行
- **CI 门禁**：在 `.github/workflows/qa-workflow-schema-check.yml` 中加 `check-build-system-prompt-precondition.sh`，验证 system-prompt.md 中 Spec-Uncertain 段落的 `allowed_values` 必须为 `1|2|S` 而非 `Confirm`（防 O13a 未合入就执行首次构建）

**Hard Dependency 2：B2.5 必须先于 B3 合入（保留）+ B2.5 失败时 B3 的降级路径**

- **正向依赖**（V1.1 已声明）：B2.5 引入 `<phase-abort>` / `<phase-complete>` 宏标签后，B3 中的 O13/O14 改写时强烈推荐使用宏，否则又是 5 步咒语堆积。
- **降级路径（V1.1 二次修订 / 质检 H2 接纳）**：如果 B2.5 因质量问题（如人工抽查 LLM 执行记录发现展开不一致超过阈值、CI `check-phase-abort-structure.sh` 持续误报阻塞 PR、Limited 平台小 LLM 漏展开率 > 5%）**未通过验收**：
  - B3 中的 O13/O14 必须**降级回原"5 步咒语"写法**（不阻塞 D14 收口）
  - O21 推迟到 v4.3 评估
  - 此时 V1.1 §5 量化对比表中"Phase 早退 ABORT 点平均行数"与"B1* 类 bug 再现概率"两行的收益**降级为 0**，但 D14 收口（B3）不受影响
  - **不允许**反向阻塞：B2.5 验收失败不得阻止 B3 进入实施

**Hard Dependency 3：B3 内严格串行（V1.1 已声明）**

- 顺序：`O13a → O10+ → O13 → O14`
- **禁止**在同一 PR 中并行；每步合入后必须单独跑 eval-cases 全量回归 + 跨平台 4 类验收
- 详细原因见 §4.1 批次表后"B3 严格串行说明"

**Hard Dependency 4：O21 / O10+ 的 ADR 必须先于代码改动**

- **背景**：O21 引入 `<phase-abort>` / `<phase-complete>` 宏标签时，与 PR-4 文档名 `pr4-phase-abort-fanout-isolation.md` 存在命名冲突（详见 §3.2.21 末尾"命名冲突规避"）。
- **约束**：
  - 在 B2.5 任何代码 PR 之前，**先**合入 ADR 文件 `doc/adr/021-phase-abort-macro.md`（O4+ 范围）
  - ADR 首段必须显式区分宏标签与 PR-4 子命题名
  - 同理 `doc/adr/010-step-pause-registry.md` 必须先于 B3 代码 PR 合入

**总结跨批次依赖关系图**：

```
B0 (基础整改 + ADR 化)
  └─ ADR-010 / ADR-021 文件 ──┐
                              │
B0.5 (O3 归档)                 │
                              ▼
B1 (同步债清理)                B2.5 (O21 宏标签)
  ├─ O5 sync 脚本（独立）       │
  └─ O17+ 生成器实现（独立）    │
       │                       │
       │                       ▼
       │                   B3 (D14 收口 — 严格串行)
       │                     O13a → O10+ → O13 → O14
       │                       │
       │                       ▼
       └────[ 等待 O13a ]── O17+ 首次构建并替换 system-prompt.md
                              │
                              ▼
                         B4 / B4.5 / B5 / B6
```

### 4.1 推荐合入顺序（每批后跑 eval-cases 全量回归）— **V1.1 修订版**

| 批次 | 包含建议 | 工作量 | 跨平台风险 | 验收 |
|---|---|---|---|---|
| **B0**（即时纯整改）| O1 + O2 + O4+（含 ADR 化）+ O5 + O6 + O22(部分: state-enum + sync + io-contract + subagent-params) | 0.6d | 极低 | grep 验证 + 文档归档完成 + ADR 目录建立 + 4 个 CI 脚本绿 |
| **B0.5**（O3 单独，兼容性敏感）| O3（归档版）| 0.3d | 低 | 老会话 v3-legacy 回放 1 例 + grep 守门 + CI deprecated 警告生效 |
| **B1**（同步债清理）| O5 配套校验脚本 + O17+（自动构建 + 分层产物，可分批）| 1.5d | 极低 | sync 检查脚本通过；Limited 平台行为与 Full 平台完全对齐；首次自动构建产物人工 diff 通过 |
| **B2**（state 字段瘦身）| O7 + O8 + O9（注释级）| 0.7d | 低 | 全量回归通过；Limited 平台抽 1 个用例验证迁移脚本 |
| **B2.5**【V1.1 新增】（phase 出口宏标签）| O21（`<phase-abort>` / `<phase-complete>`）+ O22(phase-abort 结构检查) | 1.0d | 中 | 首批 PR 期间人工抽查 LLM 执行记录确认正确展开；CI 结构校验绿 |
| **B3**（D8/D15/D14 协议收口 — 严格串行）| **O13a → O13 → O14** + O12（白名单删除）+ O10+（registry 数据化）+ O22(step-pause-registry 检查) | 2.0d | 中 | step-pause 不重复弹窗；Cursor + Dify 双侧 Spec-Uncertain 弹窗选项一致；删除 `legacy-phase-step-pause-allowlist.txt`；新增 stop_state 改动量验证（在 B3 末尾加 1 个 demo case）|
| **B4**（结构收敛）| O15 + O16 | 0.5d | 低 | 子工作流回归通过；O15 配合 O21 改写后人工 diff 检查 |
| **B4.5**【V1.1 新增】（Token 精准优化）| O23 + O24 + O25 | 1.0d | 低 | P3 complex 路径 token 实测下降 ≥ 25%；3 类 LLM 抽样验证（Claude / Qwen / Doubao） |
| **B5**（boilerplate / wrapper / agents 模块化）| O11+（含 coder-agent 拆三件 + shared-input-guard）+ O19+（保留文件、整合内部）| 1.0d | 中 | Cursor + Trae + 选 1 个 Limited 平台三方手动验证；P5/P6 调用 coder-agent 与 contract-checklist-spec 路径正确 |
| **B6**（长期演进，单独立项）| O20 | 5d+ | 高 | 作为 v4.2 主体规划 |
| **❌ 放弃**（跨平台风险高）| O18（删 current_phase_result）| - | - | 不做 |

**B3 严格串行说明**【F1 修订】：B3 内多项必须按 `O13a → O10+ → O13 → O14` 顺序合入并各自单独回归，**禁止在同一 PR 中并行**。原因：
- O13a 改的是契约语义（Cursor 平台用户立刻看到选项变化）
- O10+ 是把 case switch 转为 registry，依赖 O13a 已经统一契约才能数据化
- O13 是删 phase 内联（依赖 O13a 已经统一 + O10+ 注册表已就绪）
- O14 引入新 enum `Fix-Confirming` + 删 allowlist 文件（依赖 O17+ 或 O5 已守门 + O10+ 注册表已就绪）

**B2.5 与 B3 的依赖**：B2.5 必须先于 B3 合入，因为 B3 中 O13/O14 改写时强烈推荐用 O21 的 `<phase-abort>` 宏标签，否则又是 5 步咒语堆积。

**调整后总工作量**：约 8.6d（相比 V1 的 ~5.1d 增加 ~3.5d，主要来自 O17+ 分层产物 / O21 宏标签 / O22 CI 4 件套 / O23-O25 Token 优化 / O11+ coder-agent 拆三件 / O4+ ADR 化）；**跨平台风险无显著上升**，反向收益是新增交互态成本与 token 预算双重下降。

### 4.2 "不影响效果"的护栏（强制门禁）

每批改造合入前，必须满足：

1. **产物层**：`eval-framework/artifact_checker.py` 全量通过（产物存在性、关键段落、条件必需产物）。
2. **评分层**：`eval-cases/seed-10` 上 chains A/B 的 `mean_score` 不降（容许 ± 5% 抖动）；零分 case 数不增加。
3. **路由层**：随机抽 5 个 case 人工读 `workflow-status.yaml`，能解释当前状态、回流路径、计数器与权威 enum 一致。
4. **平台层**【V1 加严】：
   - **Cursor + Trae** 双侧手动跑 1 个 issue，行为对齐
   - **至少 1 个 Limited 平台**（Dify / OpenAI Assistants）手动跑 1 个 issue
   - **小 LLM 抽样**：用 Qwen-Plus / GLM-4 / Doubao-Pro 至少跑 1 个 issue
5. **B0.5 专属（O3 归档）**：v3-legacy 老会话回放 1 例，确认归档后路径仍可加载。
6. **B2.5 专属（O21 宏标签）**【V1.1 新增】：首批使用宏标签的 PR 抽查 LLM 执行记录，确认 `<phase-abort>` 展开后 4 步动作（state / fields / ABORT / 退出）全部正确执行；CI `check-phase-abort-structure.sh` 必须绿。
7. **B3 专属（Spec-Uncertain 契约 + registry）**：
   - Cursor + Dify 各跑 1 个 Spec-Uncertain 触发的 issue，弹窗选项**完全一致**且用户响应能被正确路由
   - registry 化后增加 1 个 demo case：在本地分支临时新增 1 个 stop_state（如 `Demo-State`）实际跑通，验证"1 文件 8 行"成本
8. **B4.5 专属（Token 优化）**【V1.1 新增】：
   - P3 complex 路径 token 实测下降 ≥ 25%（基线对比）
   - 3 类 LLM 抽样：Claude（Full）+ Qwen-Plus（Limited）+ Doubao-Pro（Limited）各跑 1 case，OVHSC 推理质量不降级
9. **B5 专属（agents 模块化）**【V1.1 新增】：
   - P5 invoke coder-agent 时正确加载三件套（coder-agent + coder-workflow + contract-checklist-spec）
   - P6 单独引用 contract-checklist-spec 时不加载 coder-workflow（验证按需加载生效）

### 4.3 兼容性策略

所有 schema 变更（B2 / B3 / B4 涉及）：
- **写新读旧**：迁移脚本一次性升级（已有 `migrate-workflow-status-v3-to-v4.py` 模式）；新会话写新字段。
- **旧字段保留 1 个版本周期**：B2 中 `rca_fanout_mode_snapshot` / `fix_strategy_mode` 的删除建议先标记 deprecated（注释 "v4.2 删除"），v4.1 编排器仍可读，下个版本再物理删除。
- **强 CI 校验**：每批合入时 `check-config-schema.sh` + 新增的 6 个 CI 脚本（O5 + O22 配套）必须全绿。
- **遗留 agent 退役**【V1 新增】：B0.5 的 O3 归档采用"3 步退役 = 标 deprecated → 移到 archive/ → 90 天后物理删除"模式，与本工作流其他 deprecation 路径一致。
- **宏标签兼容**【V1.1 新增】：B2.5 引入的 `<phase-abort>` / `<phase-complete>` 在 `core-rules.xml` 中显式声明展开规则；旧版 phase 文件（手写 5 步）继续兼容运行，新版 phase 文件混合使用。v4.3 评估强制使用宏标签。
- **文件拆分兼容**【V1.1 新增】：B4.5 的 `core-rules.xml` 拆分保留聚合入口（include essential + dsl-reference），向后兼容；B5 的 `coder-agent.md` 拆三件保留原 `coder-agent.md` 为 stub（include 三件，标 deprecated），v4.3 删除。

---

## 5. 优化前后对比（量化估计）— **V1.1 修订版**

以"理解一个新 issue 需要读多少行 + 修改一个字段需要改多少处 + 单次执行 token 预算"为基准：

| 维度 | 现状（v4.1） | B0+B1+B2 后 | B0..B4 后 | B0..B5 后【V1.1 新增】|
|---|---|---|---|---|
| `workflow-status.yaml` 顶层字段数 | 27 | 26（O8 -1）| 25（O7 -1，O8 -1）| 25 |
| **`current_state` 全量枚举镜像数**【F4 修订】 | 2（template + system-prompt）| 2 + 强 CI 校验（O5 + O22）| 1（O17+ 自动构建后 system-prompt 不再独立维护，仅由 template 派生）| 1 |
| step-pause 触发位置数【F3 修订】 | 5（编排器 6 case + 主链路 phase 内联 2 + 子编排 2 case）| 5 | 3（O13/O14 收口 phase 内联，子编排 2 case 保留为合规设计）| 3 |
| **step-pause case switch 行数**【V1.1 新增】| ~150（编排器 step 4 内联）| ~150 | ~30（O10+ registry 数据化后 step 4 仅查表）| ~30 |
| **新增 1 个 stop_state 改动量**【V1.1 新增】| 5 文件 ~60 行 | 5 文件 ~60 行 | **1 文件 8 行**（O10+ registry 加 1 行 + 编排器 0 改动）| 1 文件 8 行 |
| **Phase 早退 ABORT 点平均行数**【V1.1 新增】| ~5 行 + ~10 行注释 | ~5 行 + ~10 行注释 | ~1 行（O21 宏标签 + O4+ 注释外迁）| ~1 行 |
| **B1* 类 bug 再现概率**【V1.1 新增】| 存在（漏写任一 ABORT 步骤）| 存在 | **结构性消除**（O21 宏封装 + O22 CI 校验）| 结构性消除 |
| invoke-subagent 调用平均 boilerplate 行数 | 8-12 | 8-12 | 5-8（O11+ 仅 Full 平台支持自描述加载场景）| 5-8 |
| fan-out 模式相关字段 | 4 | 3（O7 删除 snapshot）| 3 | 3 |
| 计数器顶层字段数 | 5 | 5（O9 仅注释归类）| 5 | 5 |
| 协议补丁数（D14/D15/D16/D17/D18/D19）| 6 | 6 | 4（O12 简化 D15，O14 删 D19）| 4 |
| 已废弃/兼容文件数【F2 修订】 | 5 个旧 deep-dive agent + 1 个 allowlist | 5 个归档 + deprecated 标注 + 1 个 allowlist | 5 个归档（v4.3 物理删）+ 0 个 allowlist（O14 删）| 5 个归档 + 0 个 allowlist |
| **散布注释行数**【V1.1 新增】| ~165（D1-D19 解释散布在 50+ 处）| ~165 | ~40（O4+ ADR 化 + 注释外迁，保留 ADR-XXX 引用）| ~40 |
| 历史评审文档（根目录干扰）| 17 | 2（O4 归档）| 2 | 2 |
| **system-prompt.md 行数**【V1.1 新增】| 569（手维护，与 core/ 漂移）| 569（O5 加 sync 校验） | **~250**（O17+ 自动构建 + 分层产物聚合 L0+L1+L2+L3+L4） | ~250 |
| **P3 complex 路径 token**【V1.1 新增】| ~85K | ~85K | ~70K（O17+ 分层注入节省）| **~55K**（再叠加 O23 core-rules 拆分 + O24 reasoning-chain 拆分 + O25 SubAgent 轻量 core-rules）|
| **`coder-agent.md` 单文件行数**【V1.1 新增】| 269 | 269 | 269 | **70 + 120 + 80**（O11+ 拆三件，按需加载）|
| **CI 守门覆盖项数**【V1.1 新增】| 1（config-schema）| 3（+ state-enum + sync）| 5（+ io-contract + subagent-params）| 6（+ phase-abort 结构 + step-pause-registry，B2.5/B3 落地）|
| **跨平台契约一致性**【F1 新增】| 已知漂移 1 处（Spec-Uncertain）| 漂移修复 1 处（O13a）| 全平台契约对齐 + 自动构建守门（O17+）| 全平台契约对齐 |
| **同步维护文件数**【V1.1 新增】| 5 处（重复协议描述：core-rules + workflow.xml + SKILL + system-prompt + PLATFORM-GUIDE）| 5 处 | 1 权威源 + 引用（O17+ 自动构建后 system-prompt 不再独立维护）| 1 权威源 + 引用 |

**综合**：
- **B0+B1+B2 后**：认知负担可下降 ~25%
- **B0..B4 后**：认知负担可下降 ~50%（V1.1 比 V1 多 5pp，主要来自 O21 宏 + O17+ 分层）
- **B0..B5 后**：认知负担可下降 ~60%；**P3 complex 路径 token 下降 ~35%**（B4.5 专项贡献）
- **B6 长期演进后**：可再降 ~15%（但风险也更高，建议分批）

> 相比 V1 的"30%/50%/20%"，V1.1 略上调收益估计——主要是因为 B2.5（O21）+ B4.5（Token 优化）的结构性贡献被定量化。但优化方向不变，跨平台收益仍然显著。

---

## 6. 我们必须保留的复杂度（不要为了简化而丢效果）

以下机制看似复杂，但**对效果有直接贡献，不应在本次优化中触动**：

1. **OVHSC 推理链 + Challenger 5 维度 + Arbiter 仲裁公式**：是归因质量的核心；reasoning-chain.md（O24 拆分后是 reasoning-chain-core.md）/ shared-challenger-base.md / shared-arbiter-base.md 不动业务语义，只做职责拆分。
2. **三档动态 fan-out（P3 + P4）**：通过复杂度自适应保证简单问题快速、复杂问题深入。**但内部冗余字段可瘦身（见 O7/O8）**。
3. **契约溯源 (Contract Checklist) 强前置门禁**：是修复质量的核心防幻觉机制；coder-agent 的四阶段流程 + 文件哨兵法不动（O11+ 拆三件只是按职责拆文件，业务语义零变化）。
4. **Non-Bug 三字段职责正交**：`non_bug_reflow_count` / `non_bug_context` 各司其职；O12 简化的是 `non_bug_user_choice` 的"白名单元协议"，业务字段保留。
5. **functionality-deep-dive 五阶段模型**：复杂功能问题的核心保障；F1-F5 保持不变（只是 O20 改造的是其状态文件归宿，不是阶段语义）。
6. **三层验证 (L1+L2+L3-Static + L3-Dynamic)**：闭环质量门禁的核心；P6 三类失败回流逻辑不动。
7. **P6 失败回流的强制升级**（`root_cause_not_closed → fanout_mode = complex-arbitrated`）：保证多轮回流时强制使用最严策略。
8. **Human-Review 7 类触发条件**：兜底机制，不调整。
9. **`current_state` 完整 15 值枚举集**：表达力刚刚好（继续合并会损失语义）；O14 仅在尾部加 `Fix-Confirming`，不动既有语义。
10. **每个 phase 的 `<load core-rules.xml>` step 1**：保证子调用上下文的协议一致性；O11+ 优化的是 invoke-subagent 内的拷贝，不是 phase 顶部的协议加载。O23 把 core-rules 拆 essential + dsl-reference，phase 顶部加载 essential 即可。
11. **`current_phase_result = ABORT` 显式赋值**【V1 新增】：是所有 LLM（含小模型）都能稳定执行的最小契约；O18 已放弃。**O21 的宏标签展开后内部仍然是显式赋值，与本条不冲突**。
12. **`<step-pause>` 强结构标签**（`[result_field=X][allowed_values=...]` + `请用 X=Y 回复`）：跨 LLM 输入解析最低公约数，不动。**O10+ 把 6 case 数据化为 registry，但 step-pause 输出的强结构格式不变**。
13. **deep-dive 子编排独立调度域**【V1 新增 / F3】：`functionality-deep-dive/core/workflow.xml` 自己的 step-pause case 是合理的（子编排有独立生命周期），不应强行合并到主编排器（外部 §2.6.1 的"上提"建议不吸收）。
14. **OVHSC 推理工具箱完整保留**【V1.1 重申】：O17+ Stage 2 的 L3 层 + O24 拆分后的 reasoning-chain-core.md 完整保留 OVHSC 五步 + 置信度公式 + 证据权重表，**不允许任何精简**。

---

## 7. 风险清单（必读）— **V1.1 修订版**

| 风险 | 影响 | 缓解 |
|---|---|---|
| **O3（归档遗留 agent）破坏 v3-legacy 老会话恢复**【F2 新增】 | 老 issue 重入时找不到 agent 文件，恢复失败 | B0.5 单独成批；归档前先 grep 验证当前所有会话 schema_version ≥ 4；归档后老路径仍能加载（仅路径变化）；CI 加 v3-legacy 流量统计，90 天无流量再考虑 v4.3 物理删除 |
| **O4+（ADR 化 + 注释外迁）破坏现有 PR Review 习惯**【V1.1 新增】 | reviewer 习惯于看 inline 注释了解决策，外迁后需要主动查 ADR | 外迁时保留 `<!-- ADR-014 -->` 引用作为锚点；首次外迁后内部宣讲 1 次；高频引用的 ADR 在 PR 模板中加链接 |
| **O13a（Spec-Uncertain 契约统一）改变 Cursor 用户体验**【F1 新增】 | Cursor 用户从单选 `Confirm` 变为 `1\|2\|S` 三选 | 改造方向是"恢复语义而非削减"——Confirm 单选本身已经丢失了原始设计的"选 spec 1/2 或并行"意图，统一后是质量提升；Cursor 用户教育成本可忽略（仍是单次确认动作）|
| O13/O14（迁出 phase 内 step-pause）破坏老会话恢复 | 老 issue 重入时编排器 case 找不到 | 老会话恢复路径加兼容映射（旧 stepsCompleted 中含 P2/P4 即认为已通过 step-pause）；B3 严格串行 |
| O14 引入新 enum `Fix-Confirming` 但 system-prompt.md 未同步 | Limited 平台路由 default → goto step 2，行为静默漂移 | 必须在 O14 之前合入 O5 sync 校验脚本或 O17+ 自动构建之一；O22 的 `check-state-enum.sh` 强制兜底 |
| O12（删白名单元协议）误改 v4.2 路径 | 未来 v4.2 全量收敛时需要重新设计 | 双写实现保留，仅删元协议；v4.2 收敛改为 v4.3 评估 |
| O17+（system-prompt 自动构建 + 分层产物）首次部署语义漂移 | Limited 平台行为变化 | 首次构建后人工 diff 与现版本，确认零业务语义差异；必须在 O13a 之后做（避免固化漂移）；分层产物先在内部 Dify 实例 A/B 验证 1 周 |
| **O21（`<phase-abort>` 宏标签）LLM 理解偏差**【V1.1 新增】 | 宏标签未被正确展开（漏执行某一步）→ 复现 B1* bug | core-rules.xml 中明确写展开 `<rule>`；首批 PR 期间人工抽查 LLM 执行记录 ≥10 例；CI `check-phase-abort-structure.sh` 静态校验 state/fields；运行时通过 eval-cases 全量回归兜底 |
| **O22（CI 4 件套）误报阻塞 PR**【V1.1 新增】 | 脚本逻辑 bug 导致正常 PR 被拦 | 首次部署降级为 warning（仅打印不阻塞），观察 1 周后再升级为 error；脚本本身放在 scripts/ 下，由 PR 单独 review |
| **O23/O24/O25（Token 拆分）拆错文件路径**【V1.1 新增】 | phase / SubAgent 加载失败 | CI 加 `<load>` 路径有效性校验；首次拆分后跑 eval-cases 全量回归 |
| **O11+（coder-agent 拆三件）破坏 P5 invoke 路径**【V1.1 新增】 | P5 invoke 后 SubAgent 缺少必要上下文 | 保留原 `coder-agent.md` 为 stub（include 三件）作为 v4.3 前的兼容；P5 调用方一次性更新到三件加载；B5 验收必须包含 P5/P6 全路径回归 |
| ~~O18（删除 current_phase_result 运行时变量）~~ | ~~小 LLM 漏掉 ABORT 信号~~ | **V1 已放弃此项；O21 是其安全替代** |
| O20（deep-dive 状态收编）破坏子工作流恢复 | 老 deep-dive 会话无法恢复 | 迁移脚本提供双向兼容；建议作为 v4.2 整体规划 |

---

## 8. 附：本次审视涉及的关键文件索引

### 协议与编排（P0 优化关注）
- `mobile-qa-workflow/SKILL.md`（76 行）— Skill 入口
- `mobile-qa-workflow/core/workflow.xml`（357 行）— 主编排器
- `mobile-qa-workflow/core/core-rules.xml`（223 行）— DSL 协议权威源（O23 拆 essential + dsl-reference）
- `mobile-qa-workflow/core/workflow-status-template.yaml`（95 行）— 状态机 schema 权威源
- `mobile-qa-workflow/core/workflow-model.yaml`（11 行）— 阶段序列
- `mobile-qa-workflow/core/default-config.yaml`（55 行）— 配置默认值
- `mobile-qa-workflow/core/config-schema.yaml`（83 行）— 配置键白名单
- `mobile-qa-workflow/core/step-pause-registry.yaml`【V1.1 O10+ 新增】— step-pause 注册表
- `mobile-qa-workflow/core/core-rules-essential.xml`【V1.1 O23 新增】— phase 必加载
- `mobile-qa-workflow/core/core-rules-dsl-reference.xml`【V1.1 O23 新增】— 按需加载
- `mobile-qa-workflow/core/core-rules-subagent.xml`【V1.1 O25 新增】— SubAgent 专用

### 主链路 phases（P1 优化关注）
- `phases/p1-intake.md`（110 行）— 受理（含 step n=5 重号 bug）
- `phases/p2-spec-definition.md`（192 行）— Spec + 策展（含 RCA-InProgress 漂移、内联 step-pause、Spec-Uncertain 契约源）
- `phases/p3-root-cause.md`（230 行）— 三档 RCA fan-out + deep-dive 触发
- `phases/p4-fix-design.md`（145 行）— 三档 Fix proposer + 内联 step-pause
- `phases/p5-fix-impl.md`（164 行）— 调用 coder-agent + 文件哨兵
- `phases/p6-verification.md`（125 行）— 三层验证 + 失败回流

### 主链路 agents（P1/P2 优化关注）
- `agents/curator.md`（19 行）
- `agents/investigator.md`（57 行）
- `agents/challenger.md`（31 行）+ `agents/shared-challenger-base.md`（91 行）
- `agents/arbiter.md`（26 行）+ `agents/shared-arbiter-base.md`（83 行）
- `agents/shared-input-guard.md`【V1.1 O11+/O19+ 新增】— 共享入参校验
- `agents/fix-proposer.md`（72 行）
- `agents/coder-agent.md`（270 行，最重的 agent）→ V1.1 O11+ 拆为：
  - `agents/coder-agent.md`（70 行 — 角色 + I/O 契约）
  - `agents/coder-workflow.md`（120 行 — 四阶段工作流）
  - `reference/contract-checklist-spec.md`（80 行 — Checklist + Error Dump + 平台溯源）

### Reference（P2 优化关注）
- `reference/reasoning-chain.md`（200 行）→ V1.1 O24 拆为：
  - `reference/reasoning-chain-core.md`（100 行 — 通用 OVHSC + 置信度公式）
  - `reference/reasoning-guide-functional.md`（30 行）
  - `reference/reasoning-guide-ui.md`（30 行）
  - `reference/reasoning-guide-network.md`（30 行）
  - `reference/reasoning-guide-compat.md`（30 行）

### Functionality Deep-Dive 子工作流
- `functionality-deep-dive/core/{workflow.xml, workflow-status-template.yaml, workflow-model.yaml, default-config.yaml}`
- `functionality-deep-dive/phases/f{1..5}-*.md`（共 277 行）
- `functionality-deep-dive/agents/{deep-dive-*,defensive-fix-architect}.md`（5 个新 agent）+ 5 个废弃旧 agent（O3 归档目标）
- `functionality-deep-dive/agents/README.md`（17 行，O3 退役标注更新目标）

### 模板与脚本
- `templates/*.md`（13 个模板，~1100 行）
- `scripts/migrate-workflow-status-v3-to-v4.py`（172 行）
- `scripts/legacy-phase-step-pause-allowlist.txt`（27 行，O14 后可删除）
- `scripts/check-config-schema.sh`（87 行）
- `scripts/check-state-enum.sh`【V1 O5 新增】
- `scripts/check-system-prompt-sync.sh`【V1 O5 新增】
- `scripts/check-phase-abort-structure.sh`【V1.1 O22 新增】
- `scripts/check-step-pause-registry.sh`【V1.1 O22 新增】
- `scripts/check-io-contract.sh`【V1.1 O22 新增】
- `scripts/check-subagent-params.sh`【V1.1 O22 新增】
- `scripts/build-system-prompt.py`【V1 O17 / V1.1 O17+ 新增】
- `install.sh` / `install_trae.sh`

### Limited 平台入口（O17+ 长期收编）
- `system-prompt.md`（~570 行手维护 → ~250 行自动构建）
- `PLATFORM-GUIDE.md`（67 行）

### 文档归档与 ADR【V1.1 新增】
- `mobile-qa-workflow/archive/v4.1-history/`（17 份 QUALITY-AUDIT 历史文档）
- `doc/adr/`（D1-D19 决策文档化）

### 历史方案（O4+ 归档候选）
- `QUALITY-AUDIT-CONSTRUCTION-PLAN-{v1, v2, v2.1, v2.2}.md` + 对应 REVIEW
- `QUALITY-AUDIT-REPORT-{v1.1, v1.2, v1.2.1}.md` + 对应 REVIEW

---

## 9. 跨平台与跨 LLM 兼容性评估

> 本节是 §3 优化建议的**兼容性补丁**。原始 §3 的部分建议在 Cursor/Claude Code 这类 Full 平台 + 大 LLM 上是净收益，但在 Dify/Coze/OpenAI Assistants/LangGraph/纯 Chat 等 Limited 平台或国内中等 LLM（Qwen/Doubao/GLM 等）上可能引入额外风险。**本工作流的核心目标是"绝大部分 Agent 和 LLM 都能跑"，必须以跨平台最低公约数为优化前提**。

### 9.1 当前平台/LLM 兼容矩阵

| 档次 | 代表平台 | SubAgent | 文件系统 | 典型 LLM | 入口 |
|---|---|---|---|---|---|
| **Full** | Cursor / Trae / CapCode / Windsurf / AutoGen / CrewAI / Claude Code | 真隔离 | ✅ | Claude/GPT 大模型 | `SKILL.md` + `core/workflow.xml` |
| **Limited** | Dify / Coze / OpenAI Assistants / LangGraph / 纯 Chat | 无（`env_subagent=false`）| 部分有 | 国内中等模型常见 | `system-prompt.md` 内联 |
| **Minimal** | 单次 LLM 调用、无外部编排 | 无 | 无 | 任意 | `system-prompt.md` 单 prompt |

跨平台敏感的 5 个维度：
1. **SubAgent 真假**：Limited 平台 `<invoke-subagent>` 全部走 `env_subagent=false` 内联分支
2. **状态存储介质**：Limited 平台的 `workflow-status.yaml` 可能只是对话上下文中的 YAML 文本块
3. **DSL 解析保真度**：DSL 由 LLM 解释（非真 parser），小模型对嵌套 XML / 复杂条件的可靠度更低
4. **变量引用深度**：`{user_inputs.non_bug_user_choice}` 对小 LLM 比扁平 `{non_bug_user_choice}` 难
5. **运行时变量跨调用**：`current_phase_result` 在同一执行轮次保持的可靠性，依赖编排器实际是否消费

### 9.2 §3 建议的兼容性重分类（V1.1 修订）

| ID | 跨平台等价性 | 对 Limited / 小 LLM 的额外风险 |
|---|---|---|
| **O1** RCA-InProgress 漂移修复 | ✅ 完全等价 | 无 |
| **O2** step n=5 重号修复 | ✅ 完全等价 | 无 |
| **O3** 归档 5 个废弃 deep-dive agent【V1 修订】 | ⚠️ 兼容性敏感 | 物理删除会破坏 v3-legacy 老会话恢复；改为归档 + 退役标注 + 90 天观察 + v4.3 物理删除 |
| **O4+** 历史文档归档 + ADR 化 + 注释外迁【V1.1 扩展】 | ✅ 完全等价 | 无（注释外迁不影响运行时；ADR 引用对所有 LLM 等价）|
| **O5** system-prompt 同步校验脚本 | ✅ 完全等价 | **对 Limited 平台净正贡献**（防漂移）|
| **O6** 加幂等性注释 | ✅ 完全等价 | 无（O21 落地后可在 V1.2 移除）|
| **O7** 删 `rca_fanout_mode_snapshot` | ✅ 完全等价（带迁移）| 无 |
| **O8** 合并 `fix_strategy_mode`/`fix_fanout_mode` | ✅ 完全等价（带迁移）| 无 |
| **O9** 计数器命名归类（注释级，不动 schema）| ✅ 完全等价 | 无（已调整为注释级）|
| **O10+** step-pause-registry 数据化 + step 4 拆 4a/4b/4c【V1.1 扩展】 | ✅ 完全等价 | **对 Limited 平台净正贡献**——YAML 注册表对小 LLM 比 200 行嵌套 XML switch 更易读 |
| **O11+** invoke-subagent boilerplate 抽取 + coder-agent 拆三件 + shared-input-guard 提取【V1.1 扩展】 | ⚠️ 范围限定 | Part A 仅 Full 平台 SubAgent 自加载场景；Part B/C 跨平台等价 |
| **O12** 简化白名单元协议（保留双写实现）| ✅ 完全等价 | 保留顶层镜像字段让小 LLM 仍能扁平引用；只删元协议复杂度 |
| **O13a** 统一 Spec-Uncertain 回复契约【V1 新增 / F1】 | ✅ 完全等价（统一后）| **必须先做**；统一前 Full / Limited 选项不一致 |
| **O13** P2 内联 step-pause 迁出（依赖 O13a）【V1 修订 / F1】 | ✅ 安全（前提：O13a 已合入）| 无（前提满足后）|
| **O14** P4 内联 step-pause 迁出 + 新增 Fix-Confirming | ✅ 完全等价（前提：O5 或 O17+ 已守门）| 新 enum 必须同步 system-prompt.md，否则漂移 |
| **O15** P3 三档升级路径合并 | ✅ 完全等价 | 无；与 O21 协同后写法更简 |
| **O16** deep-dive 主子配置键名收敛 | ✅ 完全等价 | 无 |
| **O17+** `system-prompt.md` 由 `core/` 自动构建 + 分层产物 L0-L4【V1.1 扩展】 | ✅ 完全等价 | **对 Limited 平台最大正贡献**——消除漂移源 + token 预算下降 |
| **O18** 删 `current_phase_result`，按 `stop_state` 隐式推导 ABORT【V1 ❌ 放弃】 | ❌ 不安全 | 小 LLM 容易把"显式信号 ABORT"看丢；保留显式赋值是所有 LLM 的最小可靠契约 |
| **O19+** wrapper 保留 + shared-input-guard 提取【V1.1 扩展】 | ✅ 完全等价 | wrapper 文件保留，仅整合内部重复 |
| **O20** deep-dive 状态收编主链路 | ⚠️ 大重构 | 跨平台都需重新验证；保持 v4.2 立项 |
| **O21** `<phase-abort>` / `<phase-complete>` 宏标签【V1.1 新增】 | ⚠️ 中风险 | 宏首次解释时 LLM 需内联展开 4 步，可能略增推理负担；缓解：在 system-prompt.md L1 显眼位置放展开规则 + CI 静态校验兜底 |
| **O22** CI 4 件套补全【V1.1 新增】 | ✅ 完全等价 | 纯 CI 守门，与平台无关；对所有平台一致受益 |
| **O23** core-rules 拆 essential + dsl-reference【V1.1 新增】 | ✅ 完全等价 | Full 直接受益；Limited 通过 O17+ 间接受益 |
| **O24** reasoning-chain 按分类拆分【V1.1 新增】 | ✅ 完全等价 | Full 直接受益；Limited 通过 O17+ L4 按需注入间接受益 |
| **O25** SubAgent 专用轻量 core-rules【V1.1 新增】 | ⚠️ 范围限定 | 仅适用于支持 SubAgent 的 Full 平台；Limited 平台 `env_subagent=false` 内联模式不适用 |

### 9.3 调整后的"真正跨平台安全"建议清单（V1.1 修订）

#### ✅ 完全跨平台安全（强烈建议做，对所有 Agent / LLM 都净正贡献）

- **O1 / O2 / O4+ / O5 / O6**（B0 整改集，O3 已拆出 B0.5）
- **O7 / O8 / O9（注释级）**（state schema 瘦身，迁移脚本保兼容）
- **O10+**（registry 数据化 + step 4 拆 4a/4b/4c）
- **O12**（保留双写实现版）
- **O13a + O13 + O14**（D14 收口三连，需严格串行）
- **O15 / O16**（结构性收敛，不动语义）
- **O17+**（`system-prompt.md` 自动构建 + 分层产物 — **跨平台兼容性最大正贡献**）
- **O19+**（保留 wrapper 文件 + shared-input-guard 提取）
- **O22**（CI 4 件套）
- **O23 / O24**（Token 优化，不限平台）

#### ⚠️ 兼容性敏感（需要单独批次或前置）

- **O3 归档版**：单独 B0.5 批次；改为归档而非删除；90 天观察期。
- **O11+ Part A**：仅适用于支持 SubAgent 自描述加载的 Full 平台；Limited 平台与不支持的 Full 平台保留旧调用方式。
- **O21**：宏标签首次解释成本可控但需要 CI 兜底 + 人工抽查。
- **O25**：仅 Full 平台 SubAgent 场景适用。

#### ❌ 跨平台不建议执行（仅 Cursor/Full + 大 LLM 适用）

- **O18 删除 `current_phase_result` 运行时变量**：**放弃此项**。显式 ABORT 信号是所有 LLM 都能稳定执行的最小契约；改为"按 `stop_state` 集合隐式推导"在 Limited 平台 + 小 LLM 上风险高（容易把 stop_state 误判为正常推进态而追加 stepsCompleted，回到 B1* 主链路根因）。
- **外部 §2.6.1 Deep-Dive step-pause 上提主编排器**：与 V1 §6 第 13 条冲突；折中方案是子工作流挂起时显式写入主 status 的 `specialized_workflow.status`，让主编排器**有感知能力但不参与调度**。

### 9.4 跨平台兼容性的"反向洞察"——哪些"冗余"必须保留

经过本节兼容性回顾，可以识别出工作流中**"看似冗余实则是跨平台保护"的设计**，不应当作技术债削减：

| 看似冗余 | 实际是跨平台兼容性的保护 |
|---|---|
| `system-prompt.md` 全量内联 | Limited 平台必须有自包含 prompt；不能依赖外部文件 |
| `current_phase_result` 显式赋值 | 小 LLM 需要显式信号，隐式推断不可靠 |
| 顶层镜像字段（即便只 1 个）| 扁平变量引用比嵌套路径对所有 LLM 都更稳 |
| `env_subagent=true/false` 双路径 | Limited 平台没有真 SubAgent，必须有内联降级 |
| `<input-protocol>` 强制 `请用 X=Y 回复` | 不同 LLM 对自由格式回复解析能力差异大；强结构是最低公约数 |
| 每个 phase 顶部 `<load core-rules.xml>` | SubAgent 启动时的协议加载机制各平台不一；显式重新加载是兜底 |
| invoke-subagent 内 `<load>` 三连击（部分平台）| 不同 SubAgent 实现对"自加载依赖"支持度不一；显式注入是兜底 |
| `<step-pause>` 输出 `[result_field=X]` `[allowed_values=...]` 标签 | 让任意 LLM（含小模型）都能机械识别字段，不依赖语义理解 |
| **deep-dive 独立调度域（含独立 step-pause case）**【V1 新增】| 子编排有独立生命周期，强行合并到主编排器会增加主编排器复杂度且降低可移植性 |
| **`<phase-abort>` / `<phase-complete>` 宏标签的展开规则在 core-rules 显式声明**【V1.1 新增】| 不依赖 LLM "内化"宏定义，每次首加载即可看到展开规则；防止小 LLM 漏展开 |
| **`current_phase_result` 在 O21 宏标签展开后仍是显式赋值**【V1.1 新增】| 宏只是隐藏书写形式，运行时语义仍是显式 ABORT 信号；与 §6 第 11 条不冲突 |

**本质矛盾**：**跨平台兼容性 ↔ 内部一致性是天然张力**。当目标是"绝大部分 Agent 和 LLM 都能跑"时，必须接受一定程度的"为最弱平台 / 最弱 LLM 设计"的冗余。这部分冗余不是"技术债"，而是**鲁棒性预算**。

### 9.5 最终修订后的合入节奏

> 已在 §4.1 直接修订，本节不重复。重点强调 B3 严格串行（O13a → O10+ → O13 → O14）+ B2.5 必须先于 B3。

### 9.6 跨平台验收的硬门禁（强制）

每批合入前，除 §4.2 既有 4 层验收外，**必须新增**：

- **Cursor + Trae**（Full 平台）各跑同一 issue，行为一致
- **至少 1 个 Limited 平台**（推荐 Dify 或 OpenAI Assistants，因其 LLM 模型差异最大）跑同一 issue：
  - step-pause 输入解析正常（特别是 `parse_error_count` 熔断）
  - state enum 写入与读取一致（不出现 default 路由）
  - 产物文件存在且符合模板（如平台无文件系统则验证 markdown 内嵌产物）
- **小 LLM 抽样**：用 Qwen-Plus / GLM-4 / Doubao-Pro 至少跑 1 个 issue（即便平台层 OK，LLM 层差异也需独立验证）
- **B0.5 专属（O3）**：v3-legacy 老会话回放 1 例
- **B2.5 专属（O21 宏）**【V1.1 新增】：人工抽查 LLM 执行记录 ≥10 例，确认宏标签 4 步动作全部正确执行
- **B3 专属（O13a/O10+/O13/O14）**：Cursor + Dify 各跑 1 个 Spec-Uncertain 触发 + 1 个 Fix-Confirming 触发的 issue，**弹窗选项完全一致**；新增 1 个 demo stop_state 验证 1 文件 8 行成本
- **B4.5 专属（Token 优化）**【V1.1 新增】：P3 complex 路径 token 实测下降 ≥ 25%；3 类 LLM 抽样 OVHSC 推理质量不降级
- **B5 专属（agents 模块化）**【V1.1 新增】：P5/P6 全路径回归通过；按需加载验证（P6 单独引用 contract-checklist-spec 时不加载 coder-workflow）

只有跨 2 个 Full 平台 + 1 个 Limited 平台 + 1 个非 Claude/GPT 系 LLM 的 4 类回归全过，才能合入。

---

## 10. 结语

这套工作流的设计 **本身是良好的**：分阶段、双层路由（边界 + 复杂度）、共享对抗基座、强契约前置门禁、三层验证、Human-Review 兜底——这些都是经过审计与多轮 review 沉淀的成熟方案，是效果的根本保证，不应触动。

**当前的复杂度问题主要来自工程层面**：v4.1 是带着多个"过渡协议 + 兼容层"上线的小迭代，留下了 D8/D14/D15/D17/D18/D19 等一系列"过渡决定"。这些过渡决定本意是降低单次 PR 风险，但叠加后形成"为了维护过渡而维护过渡"的二阶复杂度。**V1.1 进一步识别出"协议知识用注释和重复描述形式散布在代码各处而非结构化声明"是另一类同步债**——这部分由 O4+ ADR 化 + O21 宏标签 + O17+ 分层产物 + O22 CI 4 件套联合解决。

**优化的真正机会是直接做 v4.2 收敛**（V1.1 修订版）：

**收敛动作（B0/B0.5/B1）**：
- O4+ 历史文档归档 + ADR 化 + 注释外迁（**V1.1 扩展**）
- O3 归档版（兼容性敏感，单独 B0.5）
- O17+ 自动构建 + 分层产物 L0-L4（**V1.1 扩展**）
- O22 CI 4 件套（**V1.1 新增**）

**核心收敛（B2/B2.5/B3）**：
- O7 + O8 状态字段瘦身（兼容性可控）
- O21 `<phase-abort>` / `<phase-complete>` 宏标签（**V1.1 新增**，B2.5）
- O13a 先统一跨平台 Spec-Uncertain 契约（**F1 finding 修复，必做前置**）
- O10+ step-pause-registry 数据化 + step 4 拆 4a/4b/4c（**V1.1 扩展**）
- O13 + O14 把 D14 + D19 phase 内 step-pause 整改一次性完成（v4.2 遗留 #6，依赖 O13a + O10+ + O21）
- O12 把 D8/D15 元协议简化（保留双写实现）

**结构收敛（B4/B4.5/B5）**：
- O15 + O16 主子配置键名收敛（v4.2 遗留 #1 提前）
- O23 + O24 + O25 Token 精准优化（**V1.1 新增**，B4.5）
- O11+ + O19+ agents 模块化（**V1.1 扩展**，含 coder-agent 拆三件 + shared-input-guard）

**长期演进（B6）**：
- O20 deep-dive 状态收编（v4.2 立项）

**V1.1 关键否决项**（继承 V1）：
- O18（删 `current_phase_result`）放弃 — 跨平台风险高
- O3 物理删除路径放弃 — 改为归档 + 退役标注
- 外部 §2.6.1（Deep-Dive step-pause 上提主编排器）不吸收 — 与 §6 第 13 条冲突，子编排独立调度域是合理设计

只要按 §4.1 的 B0 → B0.5 → B1-B6 节奏分批，每批跑全量回归 + 跨平台 4 类验收，就可以在不损失效果的前提下，把"理解一处必须理解全部"的认知负担降低 **~60%**（V1.1 比 V1 多 ~10pp）+ **P3 complex 路径 token 下降 ~35%**（B4.5 专项贡献）+ **B1* 类 bug 结构性消除**（O21 宏 + O22 CI），让后续迭代回到"小改动 → 小影响"的健康轨道。

**优先级建议**：先做 B0（0.6d，零风险纯整改 + ADR 化）+ B0.5（O3 归档，0.3d）→ 跑回归 → 然后看资源决定是否做 B1-B5。B6 长期演进建议作为 v4.2 的主体规划单独立项。

**V1.1 推荐路径核心思路**（一句话）：**把"协议知识"从散布在代码各处的注释和重复描述中，收敛为结构化的声明（registry / macro / ADR / 分层产物），让 phase 文件专注于业务逻辑，让编排器专注于状态路由，让 SubAgent 只加载它需要的协议，让 CI 守住所有静态可校验的不变量。**

---

> **V1.1 文档与 V1 之间的对齐审查**：本 V1.1 已逐项接纳外部报告的 10 项结构性优化（O4+ / O10+ / O11+ / O17+ / O19+ / O21 / O22 / O23 / O24 / O25），保留 V1 全部判断（含 F1/F2/F3/F4 finding 与跨平台兼容性章），同时显式拒绝外部的 1 项主张（§2.6.1 Deep-Dive step-pause 上提）+ 1 项隐含支持（O18 等价方案）。如需进一步审视，可对本 V1.1 执行 second-pass review。
