# Mobile B2C 工作流 — 状态/同步复杂度深度审视与务实优化方案

- 撰写日期：2026-04-21
- 范围：`mobile-qa-workflow/` 全量（主链路 + functionality-deep-dive 子链路 + 协议 + 模板 + 脚本）
- 不覆盖：`eval-framework/` 与 `eval-cases/`（详见姊妹文档 `LOUPE_B2C_WORKFLOW_ARCH_OPTIMIZATION_2026-04-21.md`）
- 核心原则：**先减漂移与同步点，再降表层复杂度**；任何建议默认遵守"产物契约不破坏 / 状态枚举向后兼容 / 评测口径不静默漂移"三条硬约束

---

## 0. TL;DR — 这套工作流为什么会越来越复杂？

通过逐文件审视 `core/`、`phases/`、`agents/`、`functionality-deep-dive/`、`templates/`、`scripts/` 全量 ~3000 行 DSL + Markdown，**复杂度的真实来源不是"业务规则多"，而是同一份语义被同步到了多个物理位置**。集中体现为：

| 复杂度类别 | 同一语义被复制到的物理位置数量 | 典型表现 |
|---|---|---|
| **`current_state` 枚举集** | 6+ 个文件（`workflow-status-template.yaml` / `core-rules.xml` / `workflow.xml` / `system-prompt.md` / `SKILL.md` / `PLATFORM-GUIDE.md` + 各 phase）| 每次新增/重命名状态需要同步改 6+ 处，遗漏即漂移（C5 收口正是为此）|
| **fan-out / 路由模式** | 4 处（`fanout_mode` + `fix_fanout_mode` + `rca_fanout_mode_snapshot` + `phase_history[].fanout_mode`）| 同一信息四份；C10"字段隔离"是补救，但留下了"快照 + 历史 + 当前"三层冗余 |
| **step-pause 用户输入** | 2 处（顶层镜像字段 + `user_inputs.<key>`）| D8 + D15 显式承认是 v4.1 → v4.2 过渡；目前白名单仅 1 个字段也强制双写 |
| **重试/熔断计数器** | 5 个独立字段（`rca_retry_count` / `fix_retry_count` / `non_bug_reflow_count` / `lint_retry_count` / `parse_error_count`）| 每个有独立的递增/重置时机；散落在 phases 与 orchestrator 多处 |
| **核心规则文本** | 至少 3 份（`core-rules.xml` 权威 + `system-prompt.md` 全量内联 + `SKILL.md` 摘要）| `system-prompt.md` 一行变更需同步审查 `core-rules.xml`；目前 `system-prompt.md` 已经与 `core/` 出现实质漂移（详见 §3）|
| **legacy phase 内联 step-pause** | 2 处显式（`p2-spec-definition.md:53` + `p4-fix-design.md:136`）+ 1 处对应允许清单（`legacy-phase-step-pause-allowlist.txt`）+ CI 检查 | D14 协议禁止内联，但保留了"违规清单"作为兼容层；本身就是同步点 |
| **invoke-subagent 头部 boilerplate** | ~10 次（每次调用都重复 `<load core-rules.xml/>` + `<load shared-base.md/>` + `<load wrapper.md/>`）| 任一文件移动都需要全量更新 |
| **deep-dive 配置键名** | 2 套（主端 `deep_dive_optional_artifacts.<key>` ↔ 子端 `emit_<key>`）| `config-schema.yaml` 的 `known_legacy_aliases` 块明示这是漂移；登记为 v4.2 遗留 #1 |

**核心判断**：当前复杂度有 70% 是"协议补丁 + 兼容层 + 过渡机制"叠加而成。它们每一项单独看都合理（v2.0/v2.1/v2.2 的 D1-D19 决定都有充分论证），但叠在一起就形成"理解一处必须理解全部"的耦合。**优化的根本路径不是"再加一个统一抽象"，而是物理删除冗余，让单一权威源真的只有一份。**

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
              └─ 唯一 step-pause 调度入口（D14 强协议）

phases/p3-root-cause.md (RCA)
  └─ 满足触发条件时 嵌套加载 functionality-deep-dive/core/workflow.xml (子编排)
                              └─ phases/f{1..5}-*.md
                                    └─ agents/deep-dive-*.md
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

---

## 2. 复杂度来源逐项审视（带文件引用，便于改造定位）

### 2.1 状态机层（最严重）

#### 2.1.1 `current_state` 权威源被复制到 6 处，且已发现实际漂移

权威源：`core/workflow-status-template.yaml:4-9` 注释列出 15 值。
但同样的枚举集合或其变体被另外维护在：

```49:55:mobile-qa-workflow/core/core-rules.xml
        <structural>
            <tag name="flow"><rule>定义工作流程的顶层容器</rule></tag>
            <tag name="task"><rule>在 phase 文件内定义可调度的子任务容器，与 flow 同级</rule></tag>
```

```104:108:mobile-qa-workflow/system-prompt.md
> **`current_state` 完整合法枚举集**（C5 单一权威源 / `core/workflow-status-template.yaml`）：
> `Intake` / `Spec-Defining` / `Spec-Uncertain` / `Context-Curating` / `Curation-Failed` /
> `Boundary-Refined` / `Non-Bug` / `Info-Insufficient` / `RCA-Designing` /
> `RCA-LowConfidence` / `Fix-Designing` / `Fix-Implementing` / `Verifying` /
> `Human-Review` / `Done`
```

`SKILL.md`、`PLATFORM-GUIDE.md`、各 phase 文件中也都有"current_state = X"的写入语句（`phases/p2-spec-definition.md:188` 仍写入了 `RCA-InProgress` —— 该值已不在权威枚举集！，详见 §2.1.2）。

**漂移成本**：v2.0/v2.1/v2.2 的 C5 决定就是为治理这一点，但治理动作是"加注释 + 加 PR Review 守门"，并未消除复制。每次新增/重命名状态需要 reviewer 手工核对 6 个文件。

#### 2.1.2 已经存在的状态值漂移（需要立即修复，零风险）

```186:188:mobile-qa-workflow/phases/p2-spec-definition.md
        <step n="9" goal="输出产物">
            ...
            <action>更新 {workflow_status}：current_state = RCA-InProgress</action>
```

`RCA-InProgress` 不在权威枚举集（应为 `RCA-Designing`）。`p6-verification.md` 已经 C5 收口替换了一处（`RCA-InProgress → RCA-Designing`），但 `p2-spec-definition.md` 末尾被遗漏。

**影响**：编排器 step 2 按 `RCA-InProgress` 走 default 分支（`goto step 2`），看似没炸，但路由语义不再可被静态推断；后续若 PR-8 CI 加严格 enum 校验会立即破。

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

### 2.2 step-pause 协议层（次严重）

#### 2.2.1 D14 + D15 + D16 + D18 = 同一交互点的 4 重协议补丁

`<step-pause>` 这一标签上挂载了至少 4 套协议：
1. **D14 调度作用域**：仅允许在 `core/workflow.xml` step 4，phase 禁止内联（`core-rules.xml:113-124`）
2. **D15 白名单受限双写**：`user_inputs.<key>` 总写 + 顶层 `<key>` 仅当在白名单内才写（白名单 v4.1 起步 = 1 个字段 `non_bug_user_choice`）
3. **D16 参数完整性**：`title` / `result_field` / `allowed_values` 必填 + `option` 0..*
4. **D18 parse-error 熔断**：连续 3 次解析失败 → Human-Review，`parse_error_count` 显式持久化跨回合

**问题**：D14 + 允许清单矛盾——明明禁止 phase 内联，又留了 `legacy-phase-step-pause-allowlist.txt` 允许 2 处遗留，并加 CI（`scripts/check-config-schema.sh` 的姊妹脚本）守门。这是把"一次性整改"变成了"长期容忍 + 文档强调 + CI 守门"。

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
- 这导致 Limited 平台与 Full 平台的行为存在隐式差异（部分版本号声明 v4.1，但内联实现可能停留在更早版本）。

#### 2.3.2 invoke-subagent 调用处的 boilerplate

每次调用 `challenger` / `arbiter` / `investigator` / `fix-proposer` / `coder-agent` 都要在 `subagent_prompt` 内显式写：
```xml
<load target='mobile-qa-workflow/core/core-rules.xml' prompt='加载流程规范'/>
<load target='mobile-qa-workflow/agents/shared-challenger-base.md' prompt='加载共享 challenger 基座'/>
<load target='mobile-qa-workflow/agents/challenger.md' prompt='加载主流程 challenger 包装层'/>
```
然后再注入 `scene` / `dimension_set` / `target_list` / `supporting_context` / `confidence_input` / `conditional_dimensions`（5-7 个参数）。

`p3-root-cause.md` 和 `p4-fix-design.md` 共有 ~10 次此类调用，每次平均 8-12 行 boilerplate。任何 agents 文件路径调整或基座文件重命名需要全量 grep 修改。

### 2.4 已废弃但仍保留的 5 个 deep-dive agent

`functionality-deep-dive/agents/` 下：`context-reconstructor.md` / `state-analyst.md` / `temporal-analyst.md` / `challenger.md` / `arbiter.md` 5 个文件全部标注"已废弃，仅供历史会话恢复"（`core-rules.xml:92-96`）。

新会话使用复合角色（`deep-dive-context-analyst` / `deep-dive-structure-analyst` / `deep-dive-race-and-isolation-analyst` / `deep-dive-arbiter` / `defensive-fix-architect`）。

**问题**：这 5 个文件占 ~250 行，其内容仍出现在 `core-rules.xml` 的 `<available-agents>` 列表中，是新会话的潜在干扰项（LLM 可能误调用），同时也是同步债（每次 deep-dive 重构需考虑兼容路径）。

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

### 2.6 文档版本爆炸与历史评审噪声

`mobile-qa-workflow/` 根目录有：
- `QUALITY-AUDIT-CONSTRUCTION-PLAN.md` / `-v1.md` / `-v1-REVIEW.md` / `-v2.md` / `-v2-REVIEW.md` / `-v2.1.md` / `-v2.1-REVIEW.md` / `-v2.2.md` / `-REVIEW-2026-04-20.md`
- `QUALITY-AUDIT-REPORT.md` / `-v1.1.md` / `-v1.1-REVIEW.md` / `-v1.2.md` / `-v1.2-REVIEW.md` / `-v1.2.1.md` / `-v1.2.1-REVIEW.md`
- `QUALITY-AUDIT-REVIEW.md`

合计 ~17 份历史方案/评审，约 50+ 万字。在仓库根目录与 `core/` 同级，对新接入者构成显著认知负担。其中 v2.2 是当前版本，前面所有版本均为历史决策（D1-D19）追溯材料。

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

#### O3. 删除 5 个废弃 deep-dive agent 文件 + `<available-agents>` 中 5 行声明

物理删除 `functionality-deep-dive/agents/{context-reconstructor,state-analyst,temporal-analyst,challenger,arbiter}.md`，并从 `core/core-rules.xml:92-96` 删除对应 5 行。

**为何不影响效果**：v4.1 新会话已切换到复合角色（`workflow_version = v4-composite` 默认值）；旧会话恢复时 `legacy_flow_mode = true`，按子工作流原状态字段恢复，**不需要 agents/*.md 文件实体存在**（agent 调用是按 `subagent_type` 字符串匹配，旧调用由旧 stepsCompleted 决定，新执行不再触发）。如担心兼容，可保留但加 README "v4.2 删除"标注，或迁移到 `archive/` 子目录。

#### O4. 把 17 份历史 QUALITY-AUDIT 文档移到 `mobile-qa-workflow/archive/v4.1-history/`

只在根目录保留：
- `QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md`（当前版）
- `QUALITY-AUDIT-REPORT-v1.2.1.md`（当前审计源）

其余统一移入归档目录，保留 git 历史。

**为何不影响效果**：纯文档归档，工作流执行不读取这些文件；Skill 入口、core/、phases/ 完全不引用它们。

#### O5. 在 `system-prompt.md` 顶部加显式同步声明 + 自动校验脚本

短期不能消除内联拷贝（Limited 平台必须有它），但可以：
1. 在 `system-prompt.md` 头部加 `<!-- AUTOGEN-FROM: core/{core-rules,workflow,workflow-status-template}.* @ schema_version=4 / sync-check=YYYY-MM-DD -->`
2. 在 `scripts/` 下加 `check-system-prompt-sync.sh`，对比 `current_state` 枚举集合等关键 token 是否一致。

**为何不影响效果**：仅加校验，不改运行时；让漂移在 PR Review 阶段就被发现，而不是上线后才暴露。

#### O6. 给 phase 文件加文件级"幂等性约束"（注释级别）

phase 内"更新 workflow_status: current_state = X"的写入动作，建议加注释强调"该字段写入是幂等的（同值重写不影响）"，并约定：
- 同一 step 内对 `current_state` 的写入只允许一次（如有 switch，每个 case 内一次）；
- 这样 reviewer 读 phase 文件可以一眼数清状态写入点。

### 3.2 P1 — 中等优化，需要回归验证（≈ 2-3 人日）

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

#### O9. 计数器统一为 `retries.{rca,fix,non_bug_reflow,lint,parse_error}` 命名空间

**改造**：
- `workflow-status-template.yaml` 把 5 个独立顶层字段合为 `retries: {rca: 0, fix: 0, non_bug_reflow: 0, lint: 0, parse_error: 0}`。
- 编排器与 phase 内对计数器的读写改为 `workflow_status.retries.X`。
- 迁移脚本兜底：v4→v4.1 把旧 5 个顶层字段值搬入 `retries`。

**为何不影响效果**：仅命名空间变化，业务规则与阈值不变；增加可读性（一眼看到所有计数器）。

#### O10. step-pause `user_inputs` 一次性消费机制下沉到编排器（去 case 内重复清空）

**现状**：6 个 case 各自手写 `清空 user_inputs.<key>`。

**改造**：在 `workflow.xml` step 4 解析 + 派发流程中加统一规则——派发完成后自动清空已消费的 `user_inputs.<key>`（一次性输入语义内置）。case 内只需关心"读 user_inputs 派发"，不写清空动作。

**为何不影响效果**：消费语义不变（"已读 → 清空"），只是把 8+ 处重复动作收敛到 1 处。

#### O11. 把 invoke-subagent 的 `<load>` boilerplate 抽到 agents/*.md 内部

**现状**：每次调用 challenger 都要在 `subagent_prompt` 显式 `<load core-rules.xml/>` + `<load shared-challenger-base.md/>` + `<load challenger.md/>` 三连击。

**改造**：约定子 Agent 启动时由 SubAgent 内部自行加载 `core-rules.xml` + 自身基座（在 `agents/challenger.md` 顶部加 `<setup>` 块声明依赖），调用方仅传业务参数（scene / dimension_set / target_list / ...）。

**为何不影响效果**：依赖加载时机一致（SubAgent 启动时加载 vs 调用方注入字符串再加载），只是减少调用方 prompt 长度与漂移面。需要确认 SubAgent 启动协议支持"自描述依赖加载"（Cursor/Trae 的 SubAgent 机制支持）。

#### O12. 删除"白名单受限双写"机制，全量改读 `user_inputs.<key>`

**事实**：D8/D15 的双写是"v4.1 → v4.2 过渡"，目标是 v4.2 删除。当前白名单只有 1 个字段 `non_bug_user_choice`。

**改造**：直接做 v4.2 收敛，不再走过渡：
- 编排器 case Non-Bug 把 `<switch condition="{non_bug_user_choice}">` 改为 `<switch condition="{user_inputs.non_bug_user_choice}">`。
- 删除 `workflow-status-template.yaml` 顶层 `non_bug_user_choice` 字段。
- 删除 `core/workflow.xml` step 4 头部双写中的"同步镜像写入"分支与白名单检查。
- 删除 `core-rules.xml` D15 协议中的"白名单受限"段落（保留 `user_inputs.<key>` 总写规则）。
- 删除 `system-prompt.md` 与 `PLATFORM-GUIDE.md` 中所有"顶层镜像白名单"说明段落。

**为何不影响效果**：
- 编排器读取路径只是从 `{non_bug_user_choice}` 改为 `{user_inputs.non_bug_user_choice}`，分支判定完全不变。
- 迁移脚本兜底：v4→v4.1 把旧 `non_bug_user_choice` 顶层值搬入 `user_inputs.non_bug_user_choice`。
- 这是 v4.2 既定方向，提前到 v4.1.1 执行可一次性消除"为 1 个字段维护一套协议 + CI + 白名单 + 文档"的全部成本。

#### O13. P2 内联 Spec-Uncertain step-pause 真正迁出（D14 完整收口）

**现状**：`p2-spec-definition.md:53` 有内联 step-pause 与编排器 step 4 case Spec-Uncertain 重复弹窗（已知 bug，登记为 v4.2 遗留 #6）。

**改造**：
- 删除 `p2-spec-definition.md:50-62` 的内联 step-pause；改为：
  ```xml
  <action>更新 {workflow_status}：current_state = Spec-Uncertain, spec_options = [<可能选项数组>]</action>
  <action>设置 current_phase_result = ABORT</action>
  ```
- 编排器 case Spec-Uncertain 的 step-pause 标题加 `{spec_options}` 占位，与 Non-Bug 同构。
- 同步删除 `legacy-phase-step-pause-allowlist.txt` 该条目。

**为何不影响效果**：交互体验完全等价（用户看到的还是同一个确认弹窗），但消除"重复弹窗"已知 bug + D14 协议合规 + 减少同步点。

#### O14. P4 内联 Fix Design 确认 step-pause 同样迁出

**现状**：`p4-fix-design.md:136-142` 有内联 Fix Design Confirm step-pause，违反 D14。

**改造**：
- `p4-fix-design.md` step 6 末尾改为：
  ```xml
  <action>更新 {workflow_status}：current_state = Fix-Confirming</action>
  <action>设置 current_phase_result = ABORT</action>
  ```
- 在 `workflow-status-template.yaml` 头部 enum 集中加 `Fix-Confirming`。
- 编排器 step 4 加 case `Fix-Confirming`，触发 step-pause（Continue / Revise）。
- 同步删除 allowlist 该条目，删除 `legacy-phase-step-pause-allowlist.txt` 整个文件（清空），并从 PR-8 CI 中删除该文件读取逻辑。

**为何不影响效果**：交互含义不变（用户依然看到 Continue/Revise 选项），只是触发位置统一到编排器，符合 D14 + 消除 D19 整套维护成本（allowlist 文件 + CI 逻辑 + 维护规约）。

#### O15. 合并 P3 三档 fan-out 中的"升级早退"路径为统一函数

**现状**：`p3-root-cause.md` 中三档 fan-out 各自有"升级条件 → 设字段 → ABORT"代码块，结构高度重复但分散：

- L57-67：simple-single 失败 → medium-challenge
- L96-106：medium-challenge 失败 → complex-arbitrated  
- L147-158：complex-arbitrated 不收敛 → Human-Review

**改造**：抽出统一的"P3 升级路由"段（位于 step 5 末尾），按 `escalation_target` 变量（由各 fan-out 块设置）执行单一升级动作集合。

**为何不影响效果**：升级语义不变，只是减少代码重复。

#### O16. deep-dive 主子配置键名收敛（v4.2 遗留 #1 提前）

**改造**：选择主端命名 `deep_dive_optional_artifacts.<key>` 作为权威，删除子端 `emit_*` 命名：
- `functionality-deep-dive/core/default-config.yaml` 把 `emit_environment_factor_report` 改为 `deep_dive_optional_artifacts.environment_factor_report`，与主端对齐。
- `config-schema.yaml` 删除 `known_legacy_aliases` 块。
- `f1-context-reconstruction.md` 等 phase 文件中所有 `emit_*` 引用改为 `deep_dive_optional_artifacts.*`。

**为何不影响效果**：键名统一不改变开关语义；接入方负担降低，CI 不再需要 alias 校验。

### 3.3 P2 — 长期演进（≈ 1 周以上，需更谨慎的回归）

#### O17. 把 `system-prompt.md` 改为"由 `core/` 自动构建"

**改造**：
- 在 `scripts/` 下新增 `build-system-prompt.py`，从 `core/{core-rules.xml, workflow.xml, workflow-status-template.yaml, default-config.yaml, workflow-model.yaml}` + 各 `phases/*.md` + `agents/*.md` 关键节摘要，按模板生成 `system-prompt.md`。
- 在 PR-8 CI 加门禁：`system-prompt.md` 必须由 `build-system-prompt.py` 生成（diff 校验）。

**为何不影响效果**：Limited 平台使用的内容完全等价（只是来源从手维护变为构建），但消除了所有内联拷贝的同步债。

#### O18. `current_phase_result = ABORT` 模式改为更显式的"phase 返回值约定"

**现状**：`current_phase_result` 是运行时变量（D1），phase 早退必须显式写 `<action>设置 current_phase_result = ABORT</action>`，否则编排器会错误追加 stepsCompleted（B1* 主链路根因）。

**问题**：每次新增早退点都需要记得显式赋值，遗漏即引入 B1* 类回归。

**改造**：把 ABORT 语义内置到状态字段：
- 增加权威约定："任何一次 phase 执行后，编排器读 `current_state`：若 ∈ {Non-Bug, Spec-Uncertain, RCA-LowConfidence, Curation-Failed, Human-Review, Info-Insufficient, Fix-Confirming, Boundary-Refined}（即所有 `stop_state`），自动视为 ABORT，不追加 stepsCompleted；若 ∈ {正常推进态}，视为完成。"
- 编排器 step 4 头部按此规则推断 ABORT，不再依赖 `current_phase_result` 运行时变量。
- 删除 phase 文件中所有 `<action>设置 current_phase_result = ABORT</action>` 行（仅保留 `current_state` 写入）。
- 删除 `core-rules.xml` 的 `<workflow-result-protocol>` 整段，删除 `system-prompt.md` 同步段。

**为何不影响效果**：原本 `ABORT` 与 `current_state ∈ stop_states` 是 1:1 对应的。让"ABORT 由 stop_state 隐式推导"消除了 6+ 处 phase 内显式赋值的同步债，并且让 phase 文件少 1 行/早退点（共 6+ 行）。需要在状态机文档中明确 stop_state 集合。

#### O19. agent 共享基座结构调整：减少 wrapper 层

**现状**：`agents/challenger.md`（包装层 25 行）+ `agents/shared-challenger-base.md`（基座 91 行）。包装层只做"scene 映射 + 输出值名词调整"。

**改造**：直接把场景映射作为 `shared-challenger-base.md` 内的 `<switch scene>` 分支（基座本来就有 scene 入参）；删除 wrapper 层文件。
- `agents/challenger.md` 删除（同 arbiter）。
- 调用方 `subagent_prompt` 仅 `<load shared-challenger-base.md/>` + 注入参数。

**为何不影响效果**：scene 切换逻辑不变，只是把"两个文件的层级耦合"压平为单文件。需要保证 `shared-challenger-base.md` 内的 scene 分支与原 wrapper 完全等价。

#### O20. functionality-deep-dive 子工作流的状态收编

**事实**：deep-dive 有自己的 `workflow-status-template.yaml`（含 `current_state` / `stepsCompleted` 等子集字段）+ 自己的 `workflow.xml` + 自己的 `workflow-model.yaml`。

**改造路径**：
- 中期：让 deep-dive 沿用主链路 `workflow-status.yaml`，仅扩展专属字段命名空间 `workflow_status.deep_dive.{...}`（替代独立 status 文件）。
- 编排器主链路在 P3 触发 deep-dive 时切换 `current_phase = deep-dive-f{1..5}`，复用现有 step 2 路由逻辑。

**为何不影响效果**：状态字段名空间隔离即可避免冲突；主链路状态恢复时无需感知 deep-dive 是否完成（已有 `specialized_workflow.status` 字段）。优势是消除 2 套 schema/迁移脚本/编排器协议。这是较大重构，建议放到 v4.2 整体规划。

---

## 4. 落地节奏与风险隔离

### 4.1 推荐合入顺序（每批后跑 eval-cases 全量回归）

| 批次 | 包含建议 | 工作量 | 风险 | 验收 |
|---|---|---|---|---|
| **B0**（即时）| O1 + O2 + O3 + O4 | 0.5d | 极低 | grep 验证 + 文档归档完成 |
| **B1**（同步债清理）| O5 + O6 + O11 | 1.0d | 低 | system-prompt sync 检查脚本通过；agents 调用 prompt 长度下降 ≥ 30% |
| **B2**（状态字段瘦身）| O7 + O8 + O9 | 1.0d | 中 | eval-cases 全量回归（chains A/B）通过；评分波动 ≤ 5% |
| **B3**（D8/D14 协议收口）| O12 + O13 + O14 | 1.5d | 中 | step-pause 不再重复弹窗；`legacy-phase-step-pause-allowlist.txt` 删除；CI 通过 |
| **B4**（agent + deep-dive 配置）| O15 + O16 + O19 | 1.5d | 中 | 子工作流回归通过；调用 boilerplate 行数下降 ≥ 50% |
| **B5**（长期演进）| O17 + O18 + O20 | 5d+ | 高 | 需要更全面的 eval 框架支持；建议作为 v4.2 主体 |

### 4.2 "不影响效果"的护栏（强制门禁）

每批改造合入前，必须满足：

1. **产物层**：`eval-framework/artifact_checker.py` 全量通过（产物存在性、关键段落、条件必需产物）。
2. **评分层**：`eval-cases/seed-10` 上 chains A/B 的 `mean_score` 不降（容许 ± 5% 抖动）；零分 case 数不增加。
3. **路由层**：随机抽 5 个 case 人工读 `workflow-status.yaml`，能解释当前状态、回流路径、计数器与权威 enum 一致。
4. **平台层**：Cursor + Trae 双侧手动跑 1 个 issue，行为对齐。Limited 平台（用 `system-prompt.md` 的）抽 1 个用例验证。

### 4.3 兼容性策略

所有 schema 变更（B2 / B3 / B4 涉及）：
- **写新读旧**：迁移脚本一次性升级（已有 `migrate-workflow-status-v3-to-v4.py` 模式）；新会话写新字段。
- **旧字段保留 1 个版本周期**：B2 中 `rca_fanout_mode_snapshot` / `fix_strategy_mode` 的删除建议先标记 deprecated（注释 "v4.2 删除"），v4.1 编排器仍可读，下个版本再物理删除。
- **强 CI 校验**：每批合入时 `check-config-schema.sh` + 新增的 `check-state-enum.sh`（O5 配套）+ `check-system-prompt-sync.sh`（O5 配套）必须全绿。

---

## 5. 优化前后对比（量化估计）

以"理解一个新 issue 需要读多少行 + 修改一个字段需要改多少处"为基准：

| 维度 | 现状（v4.1） | B0+B1+B2 后 | B0..B4 后 |
|---|---|---|---|
| `workflow-status.yaml` 顶层字段数 | 27 | 26（O8 -1）| 23（O9 合并 5→1，O7 -1，O8 -1，O12 -1）|
| `current_state` enum 维护文件数 | 6+ | 5（O5 加自动校验）| 5 + CI 守门 |
| step-pause 触发位置数 | 8（编排器 6 + phase 内联 2）| 8 | 6（O13/O14 收口）|
| invoke-subagent 调用平均 boilerplate 行数 | 8-12 | 3-5（O11）| 3-5 |
| fan-out 模式相关字段 | 4 | 3（O7 删除 snapshot）| 3 |
| 计数器顶层字段数 | 5 | 5 | 1（命名空间 retries.*，O9）|
| 协议补丁数（D14/D15/D16/D17/D18/D19）| 6 | 6 | 4（O12 删 D8+D15，O14 删 D19）|
| 已废弃/兼容文件数 | 5 个旧 deep-dive agent + 1 个 allowlist | 0 个旧 agent（O3）+ 1 个 allowlist | 0 + 0（O14 删 allowlist）|
| 历史评审文档（根目录干扰）| 17 | 2（O4 归档）| 2 |

**综合**：B0+B1+B2 后认知负担可下降 ~30%；B0..B4 后可下降 ~50%；B5 引入更大重构后可再降 ~20%（但风险也更高，建议分批）。

---

## 6. 我们必须保留的复杂度（不要为了简化而丢效果）

以下机制看似复杂，但**对效果有直接贡献，不应在本次优化中触动**：

1. **OVHSC 推理链 + Challenger 5 维度 + Arbiter 仲裁公式**：是归因质量的核心；reasoning-chain.md / shared-challenger-base.md / shared-arbiter-base.md 不动。
2. **三档动态 fan-out（P3 + P4）**：通过复杂度自适应保证简单问题快速、复杂问题深入。**但内部冗余字段可瘦身（见 O7/O8）**。
3. **契约溯源 (Contract Checklist) 强前置门禁**：是修复质量的核心防幻觉机制；coder-agent 的四阶段流程 + 文件哨兵法不动。
4. **Non-Bug 三字段职责正交**：`non_bug_reflow_count` / `non_bug_context` 各司其职；O12 仅是把 `non_bug_user_choice` 从顶层镜像收编到 `user_inputs.*`，业务字段保留。
5. **functionality-deep-dive 五阶段模型**：复杂功能问题的核心保障；F1-F5 保持不变（只是 O20 改造的是其状态文件归宿，不是阶段语义）。
6. **三层验证 (L1+L2+L3-Static + L3-Dynamic)**：闭环质量门禁的核心；P6 三类失败回流逻辑不动。
7. **P6 失败回流的强制升级**（`root_cause_not_closed → fanout_mode = complex-arbitrated`）：保证多轮回流时强制使用最严策略。
8. **Human-Review 7 类触发条件**：兜底机制，不调整。
9. **`current_state` 完整 15 值枚举集**：表达力刚刚好（继续合并会损失语义）；O9 合并的是计数器字段，不是 enum 值。
10. **每个 phase 的 `<load core-rules.xml>` step 1**：保证子调用上下文的协议一致性；O11 优化的是 invoke-subagent 内的拷贝，不是 phase 顶部的协议加载。

---

## 7. 风险清单（必读）

| 风险 | 影响 | 缓解 |
|---|---|---|
| O12（删顶层镜像）漏改某处编排器读取点 | step-pause 用户回复无法被路由识别 | grep `core/workflow.xml` 全量 `{non_bug_user_choice}`；改后跑 Non-Bug Accept/Reflow 双路径回归 |
| O13/O14（迁出 phase 内 step-pause）破坏老会话恢复 | 老 issue 重入时编排器 case 找不到 | 老会话恢复路径加兼容映射（旧 stepsCompleted 中含 P2/P4 即认为已通过 step-pause） |
| O17（system-prompt 自动构建）首次部署语义漂移 | Limited 平台行为变化 | 首次构建后人工 diff 与现版本，确认零业务语义差异 |
| O18（删除 current_phase_result 运行时变量）误判 ABORT | phase 被错误追加 stepsCompleted | `stop_state` 集合需明确并通过 enum 校验脚本兜底 |
| O20（deep-dive 状态收编）破坏子工作流恢复 | 老 deep-dive 会话无法恢复 | 迁移脚本提供双向兼容；建议作为 v4.2 整体规划 |

---

## 8. 附：本次审视涉及的关键文件索引

### 协议与编排（P0 优化关注）
- `mobile-qa-workflow/SKILL.md`（76 行）— Skill 入口
- `mobile-qa-workflow/core/workflow.xml`（357 行）— 主编排器
- `mobile-qa-workflow/core/core-rules.xml`（223 行）— DSL 协议权威源
- `mobile-qa-workflow/core/workflow-status-template.yaml`（95 行）— 状态机 schema 权威源
- `mobile-qa-workflow/core/workflow-model.yaml`（11 行）— 阶段序列
- `mobile-qa-workflow/core/default-config.yaml`（55 行）— 配置默认值
- `mobile-qa-workflow/core/config-schema.yaml`（83 行）— 配置键白名单

### 主链路 phases（P1 优化关注）
- `phases/p1-intake.md`（110 行）— 受理（含 step n=5 重号 bug）
- `phases/p2-spec-definition.md`（192 行）— Spec + 策展（含 RCA-InProgress 漂移、内联 step-pause）
- `phases/p3-root-cause.md`（230 行）— 三档 RCA fan-out + deep-dive 触发
- `phases/p4-fix-design.md`（145 行）— 三档 Fix proposer + 内联 step-pause
- `phases/p5-fix-impl.md`（164 行）— 调用 coder-agent + 文件哨兵
- `phases/p6-verification.md`（125 行）— 三层验证 + 失败回流

### 主链路 agents（P1/P2 优化关注）
- `agents/curator.md`（19 行）
- `agents/investigator.md`（57 行）
- `agents/challenger.md`（31 行）+ `agents/shared-challenger-base.md`（91 行）
- `agents/arbiter.md`（26 行）+ `agents/shared-arbiter-base.md`（83 行）
- `agents/fix-proposer.md`（72 行）
- `agents/coder-agent.md`（270 行，最重的 agent）

### Functionality Deep-Dive 子工作流
- `functionality-deep-dive/core/{workflow.xml, workflow-status-template.yaml, workflow-model.yaml, default-config.yaml}`
- `functionality-deep-dive/phases/f{1..5}-*.md`（共 277 行）
- `functionality-deep-dive/agents/{deep-dive-*,defensive-fix-architect}.md`（5 个新 agent）+ 5 个废弃旧 agent

### 模板与脚本
- `templates/*.md`（13 个模板，~1100 行）
- `scripts/migrate-workflow-status-v3-to-v4.py`（172 行）
- `scripts/legacy-phase-step-pause-allowlist.txt`（27 行，O14 后可删除）
- `scripts/check-config-schema.sh`（87 行）
- `install.sh` / `install_trae.sh`

### Limited 平台入口（O17 长期收编）
- `system-prompt.md`（~570 行，与 core/ 高度重叠的内联拷贝）
- `PLATFORM-GUIDE.md`（67 行）

### 历史方案（O4 归档候选）
- `QUALITY-AUDIT-CONSTRUCTION-PLAN-{v1, v2, v2.1, v2.2}.md` + 对应 REVIEW
- `QUALITY-AUDIT-REPORT-{v1.1, v1.2, v1.2.1}.md` + 对应 REVIEW

---

## 9. 跨平台与跨 LLM 兼容性评估（关键修订）

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

### 9.2 §3 建议的兼容性重分类

| ID | 跨平台等价性 | 对 Limited / 小 LLM 的额外风险 |
|---|---|---|
| **O1** RCA-InProgress 漂移修复 | ✅ 完全等价 | 无 |
| **O2** step n=5 重号修复 | ✅ 完全等价 | 无 |
| **O3** 删 5 个废弃 deep-dive agent | ✅ 完全等价 | 无 |
| **O4** 历史文档归档 | ✅ 完全等价 | 无 |
| **O5** system-prompt 同步校验脚本 | ✅ 完全等价 | **对 Limited 平台净正贡献**（防漂移）|
| **O6** 加幂等性注释 | ✅ 完全等价 | 无 |
| **O7** 删 `rca_fanout_mode_snapshot` | ✅ 完全等价（带迁移）| 无 |
| **O8** 合并 `fix_strategy_mode`/`fix_fanout_mode` | ✅ 完全等价（带迁移）| 无 |
| **O9** 计数器 `retries.*` 命名空间 | ⚠️ 需调整 | 小 LLM 读嵌套字段不如扁平稳；**建议保留扁平别名作为镜像** |
| **O10** step-pause 一次性消费下沉编排器 | ⚠️ 需明确范围 | 编排器侧统一 + case 内显式清空保留，**双重保险** |
| **O11** invoke-subagent boilerplate 抽到 agents 内部 | ❌ Cursor/Full 友好 | Limited 平台 `env_subagent=false` 走内联分支不受影响；但**部分 Full 平台（如 AutoGen）SubAgent 不支持自描述依赖加载**，需保留显式 `<load>` |
| **O12** 删顶层镜像、全量改读 `{user_inputs.X}` | ⚠️ 对小 LLM 风险中等 | 嵌套路径解析对小 LLM 不稳；**建议改为：保留顶层镜像字段，仅删除"白名单"机制（v4.1 起步只 1 个字段，固化双写即可）** |
| **O13** P2 内联 step-pause 迁出 | ✅ 完全等价 | 无 |
| **O14** P4 内联 step-pause 迁出 + 新增 Fix-Confirming | ✅ 完全等价 | 无；需同步到 `system-prompt.md`（最好通过 O17 自动构建）|
| **O15** P3 三档升级路径合并 | ✅ 完全等价 | 无 |
| **O16** deep-dive 主子配置键名收敛 | ✅ 完全等价 | 无 |
| **O17** `system-prompt.md` 由 `core/` 自动构建 | ✅ 完全等价 | **对 Limited 平台净正贡献**（消除 Full / Limited 行为漂移源）|
| **O18** 删 `current_phase_result`，按 `stop_state` 隐式推导 ABORT | ❌ Cursor/Full 友好 | 小 LLM 容易把"显式信号 ABORT"看丢；**强烈建议放弃此项**——显式信号是所有 LLM 的最小可靠契约 |
| **O19** wrapper（challenger/arbiter）压平 | ⚠️ 需调整 | wrapper 抽象在 `env_subagent=false` 时已退化；**建议改为：保留 wrapper 文件，仅整合内部重复（如 scene 映射）**，不物理删除 |
| **O20** deep-dive 状态收编主链路 | ⚠️ 大重构 | 跨平台都需重新验证；保持 v4.2 立项 |

### 9.3 调整后的"真正跨平台安全"建议清单

#### ✅ 完全跨平台安全（强烈建议做，对所有 Agent / LLM 都净正贡献）

- **O1 / O2 / O3 / O4 / O5 / O6**（B0 全集，纯整改）
- **O7 / O8**（state schema 瘦身，迁移脚本保兼容）
- **O13 / O14**（phase 内联 step-pause 迁出，D14 协议本身就是跨平台设计的）
- **O15 / O16**（结构性收敛，不动语义）
- **O17**（`system-prompt.md` 自动构建 —— **此项是跨平台兼容性的最大正贡献**，能从根本上消除 Full 与 Limited 平台的行为漂移）

#### ⚠️ 需要"跨平台调整"后才安全

- **O9 计数器命名空间**：改为"主写 `retries.*` + 同时保留 5 个扁平字段作为镜像"，或仅做注释级归类，物理上保持 5 个独立字段。
- **O10 一次性消费下沉**：保留实现但每个 case 内仍显式写一行清空，**编排器 + case 双重保险**。
- **O11 invoke-subagent boilerplate**：明确范围"仅适用于支持 SubAgent 自描述依赖加载的 Full 平台（Cursor/Claude Code 等）"；其他 Full 平台 + Limited 平台不动。
- **O12 删顶层镜像**：**改为只删除"白名单"协议机制**——既然白名单只有 1 个字段，把 D8/D15 整套"白名单受限双写 + PR Review 守门 + CI 校验 + 多文档说明"简化为"固定双写 `non_bug_user_choice`"。**保留顶层镜像字段本身**，让小 LLM 仍能用扁平引用 `{non_bug_user_choice}` 路由。
- **O19 wrapper 压平**：**改为只整合 wrapper 内重复内容**（scene 映射等），保留 challenger.md / arbiter.md 文件本身作为薄包装层。

#### ❌ 跨平台不建议执行（仅 Cursor/Full + 大 LLM 适用）

- **O18 删除 `current_phase_result` 运行时变量**：**放弃此项**。显式 ABORT 信号是所有 LLM 都能稳定执行的最小契约；改为"按 `stop_state` 集合隐式推导"在 Limited 平台 + 小 LLM 上风险高（容易把 stop_state 误判为正常推进态而追加 stepsCompleted，回到 B1* 主链路根因）。**显式信号永远比隐式推断对小 LLM 更友好。**

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
| invoke-subagent 内 `<load>` 三连击 | 不同 SubAgent 实现对"自加载依赖"支持度不一；显式注入是兜底 |
| `<step-pause>` 输出 `[result_field=X]` `[allowed_values=...]` 标签 | 让任意 LLM（含小模型）都能机械识别字段，不依赖语义理解 |

**本质矛盾**：**跨平台兼容性 ↔ 内部一致性是天然张力**。当目标是"绝大部分 Agent 和 LLM 都能跑"时，必须接受一定程度的"为最弱平台 / 最弱 LLM 设计"的冗余。这部分冗余不是"技术债"，而是**鲁棒性预算**。

### 9.5 最终修订后的合入节奏

> 替代 §4.1 表格中的批次划分。

| 批次 | 包含建议 | 工作量 | 跨平台风险 | 验收 |
|---|---|---|---|---|
| **B0**（即时）| O1+O2+O3+O4+O5+O6 | 0.5d | 极低 | grep 验证 + 文档归档完成 |
| **B1**（同步债清理，跨平台安全版）| O5（CI）+ O17（自动构建 system-prompt.md）| 1.0d | 极低 | sync 检查脚本通过；Limited 平台行为与 Full 平台完全对齐 |
| **B2**（state 字段瘦身）| O7 + O8 | 0.7d | 低 | 全量回归（chains A/B）；Limited 平台抽 1 个用例验证迁移脚本 |
| **B3**（D8/D15 协议简化 — 调整版）| O12 调整版（保留顶层镜像、删白名单机制）+ O13 + O14 | 1.0d | 低 | step-pause 不重复弹窗；删除 `legacy-phase-step-pause-allowlist.txt`；Limited 平台 step-pause 解析正常 |
| **B4**（结构收敛）| O15 + O16 | 0.5d | 低 | 子工作流回归通过 |
| **B5**（调整版的 boilerplate / wrapper）| O11 调整版（标范围）+ O19 调整版（保留文件、整合内部）| 0.7d | 中 | Cursor + Trae + 选 1 个 Limited 平台（如 Dify）三方手动验证 |
| **B6**（长期演进，单独立项）| O20 | 5d+ | 高 | 作为 v4.2 主体规划 |
| **❌ 放弃**（跨平台风险高）| **O18**（删 current_phase_result）| - | - | 不做 |
| **⚠️ 注释级**（不改 schema）| **O9**（计数器仅做注释归类）| 0.1d | 极低 | 不改字段，仅在 status-template 注释中按 retries 主题分组 |

**调整后总工作量**：~4.5d（vs 原方案 ~7d），**风险显著下降，跨平台收益显著提升**。

### 9.6 跨平台验收的硬门禁（强制）

每批合入前，除 §4.2 既有 4 层验收外，**必须新增**：

- **Cursor + Trae**（Full 平台）各跑同一 issue，行为一致
- **至少 1 个 Limited 平台**（推荐 Dify 或 OpenAI Assistants，因其 LLM 模型差异最大）跑同一 issue：
  - step-pause 输入解析正常（特别是 `parse_error_count` 熔断）
  - state enum 写入与读取一致（不出现 default 路由）
  - 产物文件存在且符合模板（如平台无文件系统则验证 markdown 内嵌产物）
- **小 LLM 抽样**：用 Qwen-Plus / GLM-4 / Doubao-Pro 至少跑 1 个 issue（即便平台层 OK，LLM 层差异也需独立验证）

只有跨 2 个 Full 平台 + 1 个 Limited 平台 + 1 个非 Claude/GPT 系 LLM 的 4 类回归全过，才能合入。

---

## 10. 结语

这套工作流的设计 **本身是良好的**：分阶段、双层路由（边界 + 复杂度）、共享对抗基座、强契约前置门禁、三层验证、Human-Review 兜底——这些都是经过审计与多轮 review 沉淀的成熟方案，是效果的根本保证，不应触动。

**当前的复杂度问题主要来自工程层面**：v4.1 是带着多个"过渡协议 + 兼容层"上线的小迭代，留下了 D8/D14/D15/D17/D18/D19 等一系列"过渡决定"。这些过渡决定本意是降低单次 PR 风险，但叠加后形成"为了维护过渡而维护过渡"的二阶复杂度。

**优化的真正机会是直接做 v4.2 收敛**：
- O12 把 D8/D15 双写过渡一次性收敛（v4.2 既定方向，提前执行）
- O13 + O14 把 D14 + D19 phase 内 step-pause 整改一次性完成（v4.2 遗留 #6）
- O7 + O8 + O9 状态字段瘦身（兼容性可控）
- O16 主子配置键名收敛（v4.2 遗留 #1 提前）

只要按 §4.1 的 B0-B4 节奏分批，每批跑全量回归，就可以在不损失效果的前提下，把"理解一处必须理解全部"的认知负担降低 50%，让后续迭代回到"小改动 → 小影响"的健康轨道。

**优先级建议**：先做 B0（0.5d，零风险纯整改）→ 跑回归 → 然后看资源决定是否做 B1-B4。B5 长期演进建议作为 v4.2 的主体规划单独立项。
