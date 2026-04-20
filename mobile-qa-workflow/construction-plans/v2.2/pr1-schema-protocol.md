# PR-1 · schema 协议层（v2.2 详细施工单）

> **主文档**：[`../../QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md`](../../QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md) §4.1（索引行）
> **子文档骨架**：[README.md §2](./README.md)
> **协议依赖**：附录 C **D1 / D2 / D3 / D7 / D8 / D14 / D15 / D16 / D17 / D18**（全部定义见主文档附录 C）
> **状态**：✅ 已展开（v2.2，2026-04-20）
> **唯一职责**：把所有"新字段、新枚举、新参数、step-pause 写回协议、step-pause 调度作用域约束、schema 版本升级、配置键名权威源"一次落地，作为 PR-2~PR-8 的协议契约基石。

## 1. PR 元信息

| 项 | 值 |
|---|---|
| 分支命名 | `feat/qa-workflow-v4.1-pr1-schema-protocol` |
| Base | `main` |
| 层级 | 🔴 协议层（最优先合入，无任何上游 PR 依赖） |
| 目标合入顺序 | **PR-1 → PR-2 → PR-4 → PR-3 → PR-5 → PR-6 → PR-7 → PR-8**（D9） |
| Reviewer | 1 名协议层 owner（必看 D14/D15/D16/D17/D18 落地）+ 1 名 schema/CI owner（必看 schema_version 升级与字段命名隔离） |
| 关联 issue | v4.1 主修复条目：B1\*（协议层规则定义）/ C1（`<task>` + 边界声明）/ C5（状态枚举源）/ C10（`fix_fanout_mode` + snapshot 字段定义）/ C11（`<step-pause>` + `<input-protocol>` + 顶层镜像白名单）/ M16（config-schema 引入）+ 配套：schema_version 3 → 4 |
| 工作量 | 1.3d（v2.0 0.8d + v2.1 D14 +0.03d + D16 +0.02d + v2.2 D17/D18 +0.08d + v2.2 review #10 迁移脚本 +0.37d） |
| 涉及文件 | 5 个：`core/core-rules.xml`（修改）/ `core/workflow-status-template.yaml`（修改）/ `core/config-schema.yaml`（**新增**）/ `core/default-config.yaml`（修改）/ `scripts/migrate-workflow-status-v3-to-v4.py`（**新增**，v2.2 review #10 方案 ① 拉入） |
| 不在本 PR 范围 | ① v4.2 遗留 #6（phase 内现存 step-pause 全面治理）② PR-2 编排器双写实现 ③ PR-5 `legacy-phase-step-pause-allowlist.txt` 实体生成 ④ 任何 phase 文件改动 |

## 2. 文件级 diff 列表

### 2.1 文件 A · `core/core-rules.xml`（修改）

> **修复条目锚点**：C1（`<task>` + 边界声明）/ C11（`<step-pause>` 协议）/ B1\*（`<workflow-result-protocol>` 协议层规则）/ D14（调度作用域约束）/ D16（参数表完整定义）/ D2（`<input-protocol>` + 标题强制后缀 + 3 次熔断）

#### 2.1.1 变更点 A1 · `<supported-tags>.<structural>` 增 `<task>` 标签 + 边界声明注释（C1 / D3）

**原文（行号锚点 L24-40）**：

```24:40:mobile-qa-workflow/core/core-rules.xml
    <supported-tags desc="Mobile QA Workflow 支持的标签">
        <structural>
            <tag name="flow"><rule>定义工作流程的顶层容器</rule></tag>
            <tag name="step">
                <rules>
                    <rule>定义步骤编号和目标</rule>
                    <rule>严禁跳过或合并步骤，必须按 n 属性指定的严格递增顺序执行</rule>
                </rules>
                <params>
                    <param name="n">步骤编号</param>
                    <param name="goal">步骤目标</param>
                </params>
            </tag>
            <tag name="check"><rule>条件判断块，包含条件表达式和对应操作</rule><params><param name="if">条件表达式</param></params></tag>
            <tag name="switch"><rule>基于变量值的多分支条件判断</rule><params><param name="condition">分支判断变量</param></params></tag>
            <tag name="for-each"><rule>遍历集合中的元素</rule><params><param name="collection">需要遍历的集合</param></params></tag>
        </structural>
```

**新文**：

```xml
    <supported-tags desc="Mobile QA Workflow 支持的标签">
        <!--
          标签白名单边界声明（v4.1 / D3）：
          本白名单仅约束 <flow>/<task> 内部 DSL 标签；元数据标签（<llm>/<mandate>/
          <agent-taxonomy>/<human-review-protocol>/<trigger>/<output-format> 等）不在
          LLM 解析校验范围内，PR-8 CI 也不对元数据标签做白名单守门。
        -->
        <structural>
            <tag name="flow"><rule>定义工作流程的顶层容器</rule></tag>
            <tag name="task"><rule>在 phase 文件内定义可调度的子任务容器，与 flow 同级</rule></tag>
            <tag name="step">
                <rules>
                    <rule>定义步骤编号和目标</rule>
                    <rule>严禁跳过或合并步骤，必须按 n 属性指定的严格递增顺序执行</rule>
                </rules>
                <params>
                    <param name="n">步骤编号</param>
                    <param name="goal">步骤目标</param>
                </params>
            </tag>
            <tag name="check"><rule>条件判断块，包含条件表达式和对应操作</rule><params><param name="if">条件表达式</param></params></tag>
            <tag name="switch"><rule>基于变量值的多分支条件判断</rule><params><param name="condition">分支判断变量</param></params></tag>
            <tag name="for-each"><rule>遍历集合中的元素</rule><params><param name="collection">需要遍历的集合</param></params></tag>
        </structural>
```

**修订理由**：
- C1（v1.2.1 §三 C1）：phase 文件实际使用 `<task>` 但白名单未注册，导致 LLM 解析期可能误判为非法标签。
- D3 边界声明：审计阶段反复确认元数据标签不应进入 DSL 校验，新增整段注释固化 reviewer 共识。

**兼容性影响**：纯加项，旧 phase 文件已使用的 `<task>` 立即合规；元数据标签注释明确不受白名单管控，PR-8 CI 不会因此误报。

---

#### 2.1.2 变更点 A2 · `<step-pause>` 标签彻底重写（C11 / D2 / D14 / D16）

**原文（行号锚点 L98，单行高密度定义）**：

```98:98:mobile-qa-workflow/core/core-rules.xml
            <tag name="step-pause"><rules><rule>强制触发硬停顿，等待用户确认后才能继续</rule><rule>将 title 和 option 输出在纯文本回复中</rule><rule>输出后立即结束当前回复，未收到用户指令前禁止执行后续步骤</rule></rules><params><param name="title">停顿标题</param><param name="option">停顿选项</param></params></tag>
```

**新文**（按 D16 完整参数表 + D14 调度作用域约束 + D2 `<input-protocol>` 子规则）：

```xml
            <tag name="step-pause">
                <rules>
                    <rule>强制触发硬停顿，等待用户确认后才能继续</rule>
                    <rule>将 title 和 option 输出在纯文本回复中</rule>
                    <rule>输出后立即结束当前回复，未收到用户指令前禁止执行后续步骤</rule>
                    <rule critical="true" id="step-pause-scope">
                        调度作用域约束（v4.1 / D14）：
                        &lt;step-pause&gt; 仅允许出现在 core/workflow.xml 编排器 step 4 内
                        （按 current_state 路由触发）；phase 文件
                        （phases/**、functionality-deep-dive/phases/**）禁止内联
                        &lt;step-pause&gt;。phase 早退应通过
                          &lt;action&gt;更新 {workflow_status}：current_state = &lt;stop_state&gt;&lt;/action&gt;
                          &lt;action&gt;设置 current_phase_result = ABORT&lt;/action&gt;
                        让编排器接管，由编排器 step 4 对应 case 统一触发 step-pause。
                        例外清单见 mobile-qa-workflow/scripts/legacy-phase-step-pause-allowlist.txt
                        （v4.2 遗留 #6 治理目标，PR-5 维护、PR-8 CI 消费）。
                    </rule>
                </rules>
                <params>
                    <param name="title" required="true">
                        停顿标题（必填）。最后一行必须追加 "请用 &lt;key&gt;=&lt;value&gt; 回复"，
                        其中 &lt;key&gt; 必须与 result_field 同名，&lt;value&gt; 必须落在 allowed_values 内。
                    </param>
                    <param name="result_field" required="true">
                        本停顿点用户回复写入的字段名（必填）。在 core/workflow-status-template.yaml
                        的顶层镜像白名单内时由编排器双写到 workflow_status.&lt;result_field&gt;；
                        总是写入 workflow_status.user_inputs.&lt;result_field&gt;。
                    </param>
                    <param name="allowed_values" required="true">
                        合法回复值白名单（必填，使用 "|" 分隔）。例如 "Accept|Reflow"。
                        编排器解析失败时回显该白名单。
                    </param>
                    <param name="option" required="false" cardinality="0..*">
                        停顿选项（可选，0..*）。每个 &lt;option&gt; 标注一行可选回复语义，
                        其 action 属性形式必须为 "&lt;result_field&gt;=&lt;value&gt;"
                        且 &lt;value&gt; 必须命中 allowed_values 白名单。
                    </param>
                </params>
                <input-protocol critical="true">
                    <rule n="1">
                        step-pause 输出时必须包含两行机器可读标签：
                          [result_field=&lt;key&gt;]
                          [allowed_values=&lt;v1&gt;|&lt;v2&gt;|...]
                        并保证标题最后一行为 "请用 &lt;key&gt;=&lt;value&gt; 回复"。
                    </rule>
                    <rule n="2">
                        用户回复必须以 &lt;key&gt;=&lt;value&gt; 作为首行；&lt;value&gt; 必须在 allowed_values 白名单内。
                    </rule>
                    <rule n="3">
                        解析失败时编排器输出 "[parse-error: 期望 &lt;key&gt; ∈ &lt;allowed_values&gt;]"
                        并重新触发同一 step-pause；将 workflow_status.parse_error_count += 1。
                    </rule>
                    <rule n="4">
                        进入新的 step-pause 之前，编排器必须将 workflow_status.parse_error_count 重置为 0；
                        解析成功也立即清零；连续 3 次解析失败后转 Human-Review，并清零计数器
                        （字段语义见 core/workflow-status-template.yaml 中 parse_error_count，决定 D18）。
                    </rule>
                    <rule n="5">
                        编排器恢复后采用"白名单受限双写"（D15）：
                          workflow_status.user_inputs.&lt;key&gt; = &lt;value&gt;       （总写）
                          workflow_status.&lt;key&gt; = &lt;value&gt;                  （仅当 &lt;key&gt; 在
                                                                                core/workflow-status-template.yaml
                                                                                顶层镜像白名单内才写）
                        v4.1 起步顶层镜像白名单 = { non_bug_user_choice }。
                    </rule>
                </input-protocol>
            </tag>
```

**修订理由**：
- C11（v1.2.1 §三 C11）：step-pause 当前仅有 title/option，无 result_field/allowed_values，导致 LLM 解析用户回复时全靠"猜",B2 闭环、Spec-Uncertain 等链路均依赖此协议。
- D16：一次性把参数表定义齐 `title (必填) / result_field (必填) / allowed_values (必填) / option (可选, 0..*)`，与 PR-2/PR-3 引用一致。
- D14：把"phase 文件禁止内联 step-pause"作为标签级 `<rule critical="true">` 显式可见，reviewer 一行 grep 即可确认；并埋好对 `legacy-phase-step-pause-allowlist.txt` 的引用，配合 PR-5/PR-8。
- D2 + D18：`<input-protocol>` 把"标题强制后缀 + parse-error 回显白名单 + 3 次熔断 + parse_error_count 生命周期 + 双写白名单受限"五件事完整闭合，PR-2 直接照单实现即可。

**兼容性影响**：
- 现有 step-pause（如 `core/workflow.xml` step 4 内 6 处）合入本 PR 后立即"参数缺失",但 PR-2 同周期补齐 `result_field`/`allowed_values`，并由 PR-8 CI 守门防止漏改。
- phase 内 `<step-pause>` 现状盘点入 PR-5 allowlist，本 PR 不影响。

---

#### 2.1.3 变更点 A3 · 新增 `<workflow-result-protocol>` 章节（B1\* 协议层 / D1）

**插入位置**：在 `<supported-tags>` 闭合后、`<human-review-protocol>` 之前（即原 L104 与 L106 之间）。

**原文（行号锚点 L104-106）**：

```104:106:mobile-qa-workflow/core/core-rules.xml
    </supported-tags>

    <human-review-protocol critical="true">
```

**新文**：

```xml
    </supported-tags>

    <workflow-result-protocol critical="true">
        <rule>
            current_phase_result 是 phase 执行期的运行时变量（不入 workflow-status.yaml schema，
            决定 D1）。phase 早退（含 ABORT、RCA-LowConfidence、Curation-Failed、Non-Bug 等）
            必须在返回编排器之前显式写入：
              &lt;action&gt;设置 current_phase_result = ABORT&lt;/action&gt;
            编排器读取规则：在同一执行轮次内读取 current_phase_result；若未显式赋值则视作正常完成
            （current_phase_result = OK），将本 phase 追加到 workflow_status.stepsCompleted。
        </rule>
        <rule>
            phase 早退点位（v4.1 主链路）：
              · phases/p2-spec-definition.md：Non-Bug 早退（PR-3） / Context-Curating / Curation-Failed
              · phases/p3-root-cause.md：4 处早退点（PR-4，含 RCA-LowConfidence 等）
              · phases/p6-verification.md：1 处失败回流早退点（PR-4）
            上述 5+ 处必须在 PR-3/PR-4 内补齐 &lt;action&gt;设置 current_phase_result = ABORT&lt;/action&gt; 标记。
        </rule>
        <rule>
            禁止把 current_phase_result 写入 core/workflow-status-template.yaml；
            禁止在 phase 文件外（如 agents/templates）引用该变量；
            禁止在 SKILL.md / system-prompt.md / PLATFORM-GUIDE.md 的"最少持久化字段"列表中收录该字段。
        </rule>
    </workflow-result-protocol>

    <human-review-protocol critical="true">
```

**修订理由**：B1\*（v1.2.1 §三 B1\*）+ D1：v4.1 取方案 A —— `current_phase_result` 作为运行时变量。本章节是协议层"权威定义",PR-3/PR-4 在 phase 内的 ABORT 标记、PR-7 文档同步、§5.1 静态校验"持久化字段表纯净性"均回链此处。

**兼容性影响**：
- 旧 phase 文件无 ABORT 标记，本 PR 合入后协议要求生效；PR-3/PR-4 在同 milestone 内补齐 5+ 处。
- 编排器 `core/workflow.xml` step 4 ABORT 分支**无需修改**（D1 方案 A 红利）。

---

### 2.2 文件 B · `core/workflow-status-template.yaml`（修改）

> **修复条目锚点**：C5（状态枚举源）/ C10（`fix_fanout_mode` + `rca_fanout_mode_snapshot`）/ C11（`user_inputs` + 顶层镜像白名单）/ D7（不重命名 `fanout_mode`） / D8 + D15（顶层镜像白名单）/ D17（`non_bug_context`）/ D18（`parse_error_count`）/ schema_version 3 → 4

#### 2.2.1 变更点 B1 · 头部注释扩容 + `current_state` 合法枚举集注释（C5）

**原文（行号锚点 L1-7）**：

```1:7:mobile-qa-workflow/core/workflow-status-template.yaml
# Mobile QA Workflow 状态模板文件，禁止修改此文件格式
# ⚠️ CRITICAL: 此文件必须保持严格 YAML 格式，LLM 禁止修改结构

# [PRESERVE_FORMAT]
issue_id: null
current_state: Intake
platform: null
```

**新文**：

```yaml
# Mobile QA Workflow 状态模板文件，禁止修改此文件格式
# ⚠️ CRITICAL: 此文件必须保持严格 YAML 格式，LLM 禁止修改结构
#
# current_state 合法枚举集（C5 单一权威源，v4.1 完整集合）：
#   Intake / Spec-Defining / Spec-Uncertain / Context-Curating / Curation-Failed
#   / Boundary-Refined / Non-Bug / Info-Insufficient / RCA-Designing
#   / RCA-LowConfidence / Fix-Designing / Fix-Implementing / Verifying
#   / Human-Review / Done
# 任何 phase / 编排器 / 文档新增的 current_state 取值，必须先在此处注册并同步
# SKILL.md / system-prompt.md / PLATFORM-GUIDE.md（PR-7 联动）。

# [PRESERVE_FORMAT]
issue_id: null
current_state: Intake
platform: null
```

**修订理由**：C5（v1.2.1 §三 C5）目前 5 个新枚举（`Context-Curating` / `Curation-Failed` / `Boundary-Refined` / `Fix-Implementing` / `Verifying`）散落在 `system-prompt.md` 与 phase 文件，缺单一权威源；PR-8 CI 的"Schema 自洽"项需要本注释作为校验锚点。

**兼容性影响**：注释项，0 行为破坏；PR-7 同周期把同列表搬到三处入口文档。

---

#### 2.2.2 变更点 B2 · `schema_version` 升级 + 新增字段集中注入（C10 / C11 / D7 / D17 / D18）

**原文（行号锚点 L19-30）**：

```19:30:mobile-qa-workflow/core/workflow-status-template.yaml
schema_version: 3
analysis_complexity: null
analysis_complexity_confidence: null
fanout_mode: null
fix_strategy_mode: null
fix_risk_level: null
reroute_reason: null
reroute_from_phase: null
reroute_target_phase: null
rca_retry_count: 0
fix_retry_count: 0
verification_failure_type: null
```

**新文**（在保留所有现有字段的基础上集中追加；为减小 diff，调整 `schema_version` 为 4，并紧随其后插入新字段块）：

```yaml
schema_version: 4    # v4.1：3 → 4（v2.0 P0-3）；迁移脚本路径见 mobile-qa-workflow/scripts/migrate-workflow-status-v3-to-v4.py
analysis_complexity: null
analysis_complexity_confidence: null

# fanout_mode 命名约束（D7）：保留为 RCA 字段，不重命名为 rca_fanout_mode；
# Fix 阶段一律改写 fix_fanout_mode（C10 字段隔离）。
fanout_mode: null
fix_fanout_mode: null    # C10 + D7：v4.1 新增，承接 P4 的 fix_strategy_mode/contested-arbitrated 等取值
# C10 兼容性方案 B 兜底：P3 完成时 fanout_mode 的快照，用于 P3 重入时还原 RCA 上下文；
# 与 phase_history 中元素的 fanout_mode 字段双保险（迁移脚本 §6.3 利用该值还原 fanout_mode）。
rca_fanout_mode_snapshot: null

fix_strategy_mode: null
fix_risk_level: null
reroute_reason: null
reroute_from_phase: null
reroute_target_phase: null
rca_retry_count: 0
fix_retry_count: 0
verification_failure_type: null

# phase_history（v4.1 / v2.0 P1-2）：阶段执行历史，元素结构固定为：
#   { phase: <str, e.g. "qa-root-cause">,
#     timestamp: <ISO8601>,
#     fanout_mode: <str|null, 该阶段完成时 fanout_mode 的取值>,
#     note: <str, 可选备注> }
# PR-4 P3 完成时按此结构 append；迁移脚本 §6.3 据此反查 fanout_mode 还原值。
phase_history: []

# user_inputs（v4.1 / C11 D2）：step-pause 用户回复的命名空间容器。
# 编排器 step 4 解析 step-pause 用户回复后总是写入 user_inputs.<result_field>；
# 仅当 <result_field> 在下方"顶层镜像字段白名单"内时，才同步写入顶层（D15 双写白名单受限）。
# v4.2 收敛后编排器改读 user_inputs.<key>，届时删除下方所有顶层镜像字段。
user_inputs: {}

# Non-Bug 上下文（v4.1 / v2.2 D17）：供编排器 step 4 case Non-Bug 的 step-pause
# 标题占位 "{non_bug_context}" 使用，承载最近一次 Non-Bug 判定说明
# （Working-As-Designed / 复现路径不充分等）。允许在后续会话中被覆盖，非长期业务字段。
# 写入端：phases/p2-spec-definition.md step 4 判定 Non-Bug 时（PR-3）。
non_bug_context: null

# parse-error 计数器（v4.1 / v2.2 D18）：step-pause 连续解析失败熔断计数器。
# 生命周期（编排器 core/workflow.xml step 4 维护，PR-2 实现）：
#   · 进入新的 step-pause 之前 → 重置 0
#   · 解析成功 → 重置 0
#   · 解析失败 → += 1
#   · 累计 >= 3 → 切到 current_state = Human-Review，并重置 0
parse_error_count: 0

# ⚠️ 顶层镜像字段白名单（v4.1 双写过渡，v4.2 收敛 / D8 + D15）
# 协议（强契约）：编排器双写时仅当 step-pause 的 result_field 出现在以下字段集中，
#   才会同步写入顶层；不在白名单内的 result_field 仅写 user_inputs.<key>，不污染顶层 schema。
# 起步白名单 = { non_bug_user_choice }；新增需 PR Review 显式批准并同步本块注释。
# v4.2 收敛动作：编排器改读 user_inputs.<key>，并删除以下字段（v4.2 遗留 #3）。
non_bug_user_choice: null    # 镜像 user_inputs.non_bug_user_choice（v4.1 起步白名单）
```

> **diff 落地说明**：上述新文中 `verification_failure_type` 已存在于原 L30，**不重复声明**；实际 PR 中仅在原 L30 之后顺序插入新字段块（`fix_fanout_mode` / `rca_fanout_mode_snapshot` / `phase_history` / `user_inputs` / `non_bug_context` / `parse_error_count` / 顶层镜像白名单注释 + `non_bug_user_choice`）。`fanout_mode` 紧接其前的注释为新增。

**修订理由**：
- C10：P4 复用 `fanout_mode` 导致 P3→P4→P6→P3 升级判断 switch 落入 default 分支（v1.2.1 §三 C10）；新增 `fix_fanout_mode` + `rca_fanout_mode_snapshot` 实现强字段隔离。
- D7：保留 `fanout_mode` 为 RCA 字段，仅外迁 Fix 语义，PR-4 不动 P3/P6 的 `fanout_mode` 写入。
- C11 + D2 + D8 + D15：`user_inputs` 命名空间承载所有 step-pause 回复；顶层镜像字段白名单 v4.1 起步集 = `{non_bug_user_choice}`，与编排器现有 `{non_bug_user_choice}` 顶层读取兼容。
- D17 / D18：`non_bug_context` / `parse_error_count` 既然已被 PR-2/PR-3 实际使用（v2.1 review 揭示的协议缺口），必须显式入 schema。
- v2.0 P0-3：schema_version 3 → 4 显式动作，保证迁移脚本与 PR-8 CI 有版本号锚点。

**兼容性影响**：
- 存量 v3 会话：迁移脚本（§2.5）注入新字段全为默认值（null / [] / {} / 0），不破坏已有读路径。
- `fanout_mode` **保持不变**（D7），任何试图重命名 `rca_fanout_mode` 的 PR 必须打回（§5.1 反向校验项）。
- `current_phase_result` **绝不出现**在本文件（D1，§5.1 持久化字段表纯净性校验）。

---

### 2.3 文件 C · `core/config-schema.yaml`（**新增**）

> **修复条目锚点**：M16（最小子集）。`config_source` 单一权威源 schema，声明所有合法 `output_*` 键名，作为 PR-8 CI 键漂移检测的权威输入。

**修改类型**：新增文件。

**原文**：N/A（不存在）。

**新文**（最小子集，仅声明键名集合 + 引用关系）：

```yaml
# Mobile QA Workflow — config_source 键名 schema（M16 最小子集 / v4.1 引入）
# ────────────────────────────────────────────────────────────────────────────
# 唯一职责：枚举 phases 中所有 "更新 config_source.<key>" 动作允许使用的合法键名。
# 消费方：
#   · core/default-config.yaml          —— 实际默认值落地，本表是其字段子集的权威白名单
#   · functionality-deep-dive/core/default-config.yaml —— deep-dive 子配置（emit_* 与本表
#                                                       存在键名漂移，统一映射延后 v4.2 遗留 #1）
#   · phases/**/*.md                    —— 所有 "更新 config_source.<key>" 动作必须命中本表
#   · .github/workflows/qa-workflow-schema-check.yml （PR-8 / D11）
#   · mobile-qa-workflow/scripts/check-config-schema.sh （PR-8 / D13）
# ────────────────────────────────────────────────────────────────────────────
# 命名约定：
#   · output_*  : 阶段产物文件路径（落盘到 qa-workspace/{issue_id}/）
#   · env_*     : 运行环境能力开关（read-only，由 install 期决定）
#   · active_*  : 路由策略选择（运行期可由 phase 写）
#   · routing_* : 路由元数据
# ────────────────────────────────────────────────────────────────────────────

schema_version: 1   # config-schema 自身版本号，与 workflow-status-template 的 schema_version 解耦

allowed_keys:
  # ── 标识 / 元信息 ──────────────────────────────────────────────────────────
  - issue_id
  - workspace_name
  - platform
  - priority

  # ── 主流程产物（output_*）────────────────────────────────────────────────
  - output_issue_card
  - output_spec
  - output_context_bundle
  - output_curation_report   # v4.1 新增（PR-1 同步补齐 default-config.yaml，C5 关联）
  - output_rca_report
  - output_fix_design
  - output_impl_report
  - output_contract_checklist
  - output_error_dump
  - output_verification_report
  - output_knowledge_card

  # ── Deep-Dive 产物（B3 联动 / 与 deep-dive 子配置 emit_* 存在键名漂移） ──
  - output_environment_factor_report
  - output_topology_report
  - output_concurrency_report
  - output_deep_dive_rca
  - output_deep_dive_summary
  - output_defensive_fix_design

  # ── 环境能力 / 路由策略 / 运行期产物 ─────────────────────────────────────
  - env_file_system
  - env_git
  - env_lint_tools
  - env_subagent
  - routing_policy_version
  - active_fanout_policy
  - active_fix_strategy_policy
  - output_runtime_compat_report
  - output_reroute_trace

  # ── Deep-Dive 默认产物开关聚合块 ────────────────────────────────────────
  - deep_dive_optional_artifacts

  # ── 修复 / 仓库元信息 ───────────────────────────────────────────────────
  - fix_branch
  - repo_path
  - repo_branch
  - code_patch
  - prd_link
  - tech_design_link

# 子键白名单（仅当顶层 key 是聚合块时声明）
nested_allowed_keys:
  deep_dive_optional_artifacts:
    - environment_factor_report
    - deep_dive_topology
    - concurrency_analysis_report

# 已知遗留映射（仅记录，不参与校验，统一治理延后 v4.2 遗留 #1）
known_legacy_aliases:
  # 主端 deep_dive_optional_artifacts.<key> ↔ 子端 emit_<key>
  deep_dive_optional_artifacts.environment_factor_report: emit_environment_factor_report
  deep_dive_optional_artifacts.deep_dive_topology:        emit_topology_report
  deep_dive_optional_artifacts.concurrency_analysis_report: emit_concurrency_report
```

**修订理由**：
- M16 最小子集（v1.2.1 §三 M16）：v4.1 不做全量 schema CI（§十 #20 延后），但必须解决 `config_source` 键漂移这一最小诉求，否则 PR-8 CI 无法启动。
- 同时把 v4.2 遗留 #1（主→子键名映射）登记在 `known_legacy_aliases`，避免后续维护时丢失上下文。

**兼容性影响**：
- 新增文件 0 破坏；PR-8 CI 在本文件存在前不启动 M16 校验。
- `output_curation_report` 同步补到 `default-config.yaml`（变更点 D1）。

---

### 2.4 文件 D · `core/default-config.yaml`（修改）

> **修复条目锚点**：M16（最小子集 default 端落地）/ C5 关联（Context-Curating 状态需要的产物路径）。

#### 2.4.1 变更点 D1 · 补齐 `output_curation_report`（M16）

**原文（行号锚点 L9-18）**：

```9:18:mobile-qa-workflow/core/default-config.yaml
output_issue_card: null
output_spec: null
output_context_bundle: null
output_rca_report: null
output_fix_design: null
output_impl_report: null
output_contract_checklist: null
output_error_dump: null
output_verification_report: null
output_knowledge_card: null
```

**新文**：

```yaml
output_issue_card: null
output_spec: null
output_context_bundle: null
output_curation_report: null   # v4.1 新增 / C5 联动：Context-Curating 阶段产物路径
output_rca_report: null
output_fix_design: null
output_impl_report: null
output_contract_checklist: null
output_error_dump: null
output_verification_report: null
output_knowledge_card: null
```

**修订理由**：
- v2.2 §3 PR-1 锁定的"补齐 `output_curation_report` 等缺失键"，与 `core/config-schema.yaml` `allowed_keys` 中新增条目一一对应。
- C5 联动：`Context-Curating` 状态在 PR-3 中需要落盘 curation-report，路径键必须先在 default-config 注册。

**兼容性影响**：纯加项，旧 issue 工作区在迁移到 v4.1 后字段值默认 `null`，不影响既有 phase 不写该字段的旧路径。

---

### 2.5 文件 E · `scripts/migrate-workflow-status-v3-to-v4.py`（**新增**）

> **修复条目锚点**：v2.2 review #10 方案 ①（迁移脚本归 PR-1 同 PR 落地）/ schema_version 3 → 4 配套 / D17（`non_bug_context`）/ D18（`parse_error_count`）/ C10（`fix_fanout_mode` + `rca_fanout_mode_snapshot`）/ C11 + D2（`user_inputs` 命名空间）/ D8 + D15（顶层镜像 `non_bug_user_choice`）/ v2.0 P1-2（`phase_history`）。

#### 2.5.1 变更点 E1 · 新增迁移脚本（v3 → v4 字段注入 + 反幂等 + dry-run）

**修改类型**：新增（文件不存在）。

**新文（脚本骨架，可直接执行）**：

```python
#!/usr/bin/env python3
"""migrate-workflow-status-v3-to-v4.py

将 mobile-qa-workflow/<workspace>/workflow-status.yaml 从 schema_version=3 迁移到 4。

迁移动作（与 core/workflow-status-template.yaml v4.1 schema 一一对应）:
  · schema_version: 3 -> 4
  · 注入 7 个新顶层字段（缺失即注入默认值，存在即保留原值，幂等）:
      - fix_fanout_mode: None
      - rca_fanout_mode_snapshot: None
      - phase_history: []
      - user_inputs: {}
      - non_bug_context: None
      - parse_error_count: 0
      - non_bug_user_choice: None        # 顶层镜像白名单（v4.1 起步集，v4.2 收敛删除）

不做的事:
  · 不重命名任何 v3 已有字段（D7：fanout_mode 保持不变）
  · 不修改 specialized_workflow 嵌套块（PRESERVE_FORMAT 区域）
  · 不写入 current_phase_result（D1：运行时变量，不入 schema）
  · 不实施 fanout_mode 反查还原逻辑（主文档 §6.3 描述的 phase_history 反查由 PR-4 写入完成后增强）
  · 不支持 v4 → v3 反向迁移

用法:
  python migrate-workflow-status-v3-to-v4.py <path-to-workflow-status.yaml> [--dry-run] [--no-strict]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from ruamel.yaml import YAML
except ImportError:
    sys.stderr.write("error: requires ruamel.yaml (pip install ruamel.yaml)\n")
    sys.exit(2)

NEW_FIELDS_DEFAULTS: dict[str, object] = {
    "fix_fanout_mode": None,
    "rca_fanout_mode_snapshot": None,
    "phase_history": [],
    "user_inputs": {},
    "non_bug_context": None,
    "parse_error_count": 0,
    "non_bug_user_choice": None,
}


def migrate(doc: dict, *, strict: bool = True) -> tuple[bool, list[str]]:
    """对单个 workflow-status doc 执行迁移；返回 (是否变更, 动作日志)。"""
    log: list[str] = []
    current = doc.get("schema_version")

    if current == 4:
        log.append("noop: schema_version already 4 (idempotent)")
        return False, log

    if current != 3:
        if strict:
            raise ValueError(f"unexpected schema_version: {current!r} (expect 3)")
        log.append(f"warn: unexpected schema_version {current!r}, force migrate")

    doc["schema_version"] = 4
    log.append("set schema_version: 3 -> 4")

    for key, default in NEW_FIELDS_DEFAULTS.items():
        if key in doc:
            log.append(f"keep existing: {key} = {doc[key]!r}")
            continue
        doc[key] = default
        log.append(f"inject: {key} = {default!r}")

    return True, log


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate workflow-status.yaml v3 -> v4")
    parser.add_argument("path", type=Path, help="path to workflow-status.yaml")
    parser.add_argument("--dry-run", action="store_true", help="print planned changes without writing")
    parser.add_argument("--no-strict", action="store_true", help="allow unknown schema_version (force migrate)")
    args = parser.parse_args()

    if not args.path.is_file():
        sys.stderr.write(f"error: not a file: {args.path}\n")
        return 2

    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)

    with args.path.open("r", encoding="utf-8") as f:
        doc = yaml.load(f)

    try:
        changed, log = migrate(doc, strict=not args.no_strict)
    except ValueError as e:
        sys.stderr.write(f"error: {e}\n")
        return 1

    for line in log:
        print(f"[migrate] {line}")

    if not changed:
        return 0

    if args.dry_run:
        print("[migrate] --dry-run: no file written")
        return 0

    with args.path.open("w", encoding="utf-8") as f:
        yaml.dump(doc, f)
    print(f"[migrate] wrote: {args.path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**修订理由**：
- v2.2 review #10：协议层 schema_version 升级与迁移脚本是强耦合的 — schema 不升、脚本无意义；脚本不到位、schema 升级不可逆（存量 v3 会话立即读不出新字段），故同 PR 落地。
- 7 个新字段默认值与 §2.2.2（B2）新文逐项对齐，保证迁移后的 `workflow-status.yaml` 与 v4.1 模板语义同构。
- **反幂等设计**：检测到 `schema_version == 4` 直接 noop，避免误把 user 数据覆盖为默认值；strict 模式禁止从未知版本（≠3）迁移，防止跨版本误调用。
- **dry-run 模式**：reviewer 可在合入前对 v3 测试夹具预览迁移动作，输出与实际写入逻辑共享 `migrate()` 路径，保证两者一致。
- **PRESERVE_FORMAT 区域不动**：使用 `ruamel.yaml`（非 PyYAML）保留注释与缩进风格；不接触 `specialized_workflow` 嵌套块，符合主契约"严格 YAML 格式 + LLM 禁止修改结构"。
- **fanout_mode 反查还原（主文档 §6.3）暂不在本骨架内**：该逻辑依赖 `phase_history` 已被 PR-4 写入完成，PR-1 时 `phase_history` 始终为空，反查无意义；后续可在 PR-4 合入后追加 `--restore-fanout-mode` 子命令增强。

**兼容性影响**：
- 仅在 `schema_version=3` 时执行字段注入；已为 v4 直接 noop（幂等），可重复执行。
- 不支持 v4 → v3 反向迁移；与 §4 回滚动作"存量已迁移到 v4 的会话需要手工或备份恢复"措辞一致。
- 依赖 `ruamel.yaml`，需要在 PR-1 提交时同步在工程 README / 实施文档登记最低 Python 依赖（建议 `ruamel.yaml >= 0.17`）。
- CLI 退出码：0 = 成功（含 noop）；1 = 迁移逻辑异常（如 schema_version 不合法且未启用 `--no-strict`）；2 = 用法错误（文件不存在 / 缺依赖）。

## 3. PR-level DoD 子集（链接到主文档 §5）

> 完整清单见主文档 [§5.1 静态契约校验](../../QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md#51-静态契约校验每个-pr-必跑)。本节仅列 PR-1 必须满足的子集。

PR-1 必须满足主文档 §5.1 中的以下子集（其余 §5.1 项由后续 PR 联动满足）：

- [ ] **Schema 自洽**（§5.1 第 1 项）：`workflow-status-template.yaml` 头部注释列出的 `current_state` 合法枚举集与 `core/core-rules.xml` `<workflow-result-protocol>` 引用的 stop_state 一致；与 PR-7 `system-prompt.md` 状态机图一致（PR-7 验收时复检）。
- [ ] **Schema 版本升级显式**（§5.1 第 2 项）：`workflow-status-template.yaml` `schema_version: 4` 字面量已落入 diff。
- [ ] **Non-Bug 上下文字段已注册**（§5.1 第 3 项 / D17）：`workflow-status-template.yaml` 中存在 `non_bug_context: null` 且注释完整。
- [ ] **parse-error 计数器已注册**（§5.1 第 4 项 / D18）：`workflow-status-template.yaml` 中存在 `parse_error_count: 0` 且注释含完整生命周期描述。
- [ ] **配置键名注册**（§5.1 第 5 项 / M16）：`core/config-schema.yaml` 文件存在；`allowed_keys` 与 `core/default-config.yaml` 中已声明键名互为子集（PR-1 自身保证 default-config 中所有 `output_*` 键均在 `allowed_keys` 内）。
- [ ] **标签白名单**（§5.1 第 6 项 / C1 / D3）：`<task>` 在 `<supported-tags>.<structural>` 中；元数据标签边界注释已加。
- [ ] **字段隔离**（§5.1 第 7 项 / C10 / D7）：`fix_fanout_mode` / `rca_fanout_mode_snapshot` 已新增；`fanout_mode` 字段名**保持不变**（grep `rca_fanout_mode\b` 仅命中 `rca_fanout_mode_snapshot`）。
- [ ] **不存在 `rca_fanout_mode` 裸字段**（§5.1 第 8 项 / D7 反向校验）。
- [ ] **step-pause 参数表完整**（§5.1 第 10 项 / D16）：`<step-pause>` 标签 `<params>` 内 `title` / `result_field` / `allowed_values` 三个 `required="true"` 标记齐备；`option` 标记 `required="false" cardinality="0..*"`。
- [ ] **step-pause 调度作用域显式**（§5.1 第 11 项 / D14）：`<step-pause>` 内含 `id="step-pause-scope"` 的 `<rule critical="true">`；规则文字含"phase 文件禁止内联 `<step-pause>`"等关键词；提及 `legacy-phase-step-pause-allowlist.txt`。
- [ ] **step-pause 输入协议完整**（§5.1 第 12 项 / D2 强化 + v2.1 收紧）：`<input-protocol>` 5 条 `<rule>` 全部到位（机器可读标签 / 标题强制后缀 / parse-error 重提 / parse_error_count 生命周期 / 白名单受限双写）。
- [ ] **顶层镜像白名单受限**（§5.1 第 13 项 / D15）：`workflow-status-template.yaml` 中"顶层镜像字段白名单"注释含"强契约"声明 + "白名单 = `{non_bug_user_choice}`"；`non_bug_user_choice: null` 已显式声明且与注释相邻可被 grep 关联。
- [ ] **持久化字段表纯净性**（§5.1 第 15 项 / D1 协议层占位）：`workflow-status-template.yaml` 内 grep `current_phase_result` 命中 0 处；`<workflow-result-protocol>` 内已明确禁止收录到任何持久化字段表（PR-7 联动验收）。
- [ ] **顶层镜像字段过渡标注**（§5.1 第 16 项 / D8）：白名单注释段含"v4.2 收敛"字样。
- [ ] **迁移脚本可执行 + 反幂等 + dry-run 一致**（v2.2 review #10 / 同 PR 落地）：`scripts/migrate-workflow-status-v3-to-v4.py` 对 v3 测试夹具执行后 `schema_version=4` 且 7 个新字段全部注入；对已为 v4 的文件再次执行返回 noop（幂等）；`--dry-run` 输出与不带该参数的实际写入完全一致（共享 `migrate()` 路径）；`ruamel.yaml` 写出未损坏 `[PRESERVE_FORMAT]` 区域内 `specialized_workflow` 嵌套块的注释与缩进。

> **PR-1 不验收的 §5.1 项**（由后续 PR 联动）：第 9 项（ABORT 标记完整 → PR-3/PR-4）/ 第 14 项（`parse_error_count` 编排器生命周期闭合 → PR-2）/ 第 17 项（allowlist 交付完整 → PR-5）。

## 4. PR-level 回滚动作（链接到主文档 §7）

完整回滚预案见主文档 [§7.1 PR-1 回滚](../../QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md#71-pr-1-回滚)，关键点摘录：

- **回滚命令**：`git revert <PR-1-merge-commit>`。
- **回滚后状态**：`core-rules.xml` 失去 `<task>` 白名单 / `<step-pause>` 完整参数表 / `<input-protocol>` / `<workflow-result-protocol>` / D14 调度作用域约束；`workflow-status-template.yaml` 缺所有新字段且 `schema_version` 退回 3；`config-schema.yaml` 文件被删除；`default-config.yaml` 失去 `output_curation_report`。
- **下游影响**：已合入的 PR-2/PR-3/PR-4/PR-5 全部失去协议契约 → 必须连同上述 PR 一起 revert（建议序列：`git revert <PR-5> <PR-4> <PR-3> <PR-2> <PR-1>`，参见主文档 §7.1 回滚 SQL）。
- **风险等级**：🔴 高，**禁止单独 revert PR-1**；如 PR-1 出现严重缺陷优先走"新 commit 修补"路线。
- **存量 v3 会话兼容**：迁移脚本 `mobile-qa-workflow/scripts/migrate-workflow-status-v3-to-v4.py`（与 PR-1 同 PR 落地，骨架见 §2.5）回滚时一并被还原；存量已迁移到 v4 的会话需要手工或备份恢复（迁移脚本不支持 v4 → v3 反向迁移）。

## 5. §5.1 静态契约校验自检（PR-1 视角）

> 按主文档 §5.1 17 项清单逐项核查 PR-1 是否落地或留待后续 PR 联动。✅ = 本 PR 满足；⏸ = 不在本 PR 范围（标注承接方）。

| § 5.1 校验项 | PR-1 状态 | 落地证据 / 承接方 |
|---|---|---|
| 1. Schema 自洽（current_state 取值有定义） | ✅ | 变更点 B1 头部注释列出 v4.1 完整枚举集 |
| 2. Schema 版本升级显式（schema_version=4） | ✅ | 变更点 B2 首行 `schema_version: 4` |
| 3. Non-Bug 上下文字段已注册（D17） | ✅ | 变更点 B2 `non_bug_context: null` + 注释 |
| 4. parse-error 计数器已注册（D18） | ✅ | 变更点 B2 `parse_error_count: 0` + 完整生命周期注释 |
| 5. 配置键名注册（config-schema） | ✅ | 文件 C 新增 + 文件 D 补 `output_curation_report` |
| 6. 标签白名单（含 `<task>` + 边界声明） | ✅ | 变更点 A1 |
| 7. 字段隔离（fanout_mode 不重命名 / fix_fanout_mode 新增） | ✅ | 变更点 B2（`fanout_mode` 注释 + `fix_fanout_mode: null` + `rca_fanout_mode_snapshot: null`） |
| 8. ❌ 不存在 `rca_fanout_mode` 裸字段（D7 反向校验） | ✅ | grep `rca_fanout_mode` 仅命中 `rca_fanout_mode_snapshot` |
| 9. ABORT 标记完整（phases 5+ 处） | ⏸ | 协议在变更点 A3 已固化；标记落地由 PR-3 / PR-4 承接 |
| 10. step-pause 参数表完整（D16） | ✅ | 变更点 A2 `<params>` 块 |
| 11. step-pause 调度作用域守门（D14） | ✅ | 变更点 A2 含 `id="step-pause-scope"` 的 `<rule critical="true">`；CI 实施由 PR-8 承接 |
| 12. step-pause 输入协议完整（标题后缀 + parse-error） | ✅ | 变更点 A2 `<input-protocol>` 5 条规则 |
| 13. 顶层镜像白名单受限（D15） | ✅ | 变更点 B2 白名单注释（"强契约" + 起步白名单）+ 单条镜像字段；编排器实现由 PR-2 承接 |
| 14. parse-error 生命周期闭合（编排器侧 +1 / 清零 4 类动作） | ⏸ | 协议在变更点 A2 `<input-protocol>` 与变更点 B2 字段注释已固化；编排器实现由 PR-2 承接 |
| 15. 持久化字段表纯净性（无 `current_phase_result`） | ✅ | 变更点 A3 `<workflow-result-protocol>` + 变更点 B2 不含该字段；文档落地由 PR-7 承接 |
| 16. 顶层镜像字段过渡标注（"v4.2 收敛"） | ✅ | 变更点 B2 白名单注释段含"v4.2 收敛 / v4.2 遗留 #3" |
| 17. allowlist 交付完整（D19） | ⏸ | PR-5 生成首版 + PR-8 CI 消费；PR-1 仅在变更点 A2 引用文件路径 |

**自检结论**：PR-1 涵盖主文档 §5.1 中协议层可落地的 14/17 项；剩余 3 项（第 9/14/17 项）属于编排器/phase/CI 实现层面，已分别在主文档 §3 PR-2 / PR-3 / PR-4 / PR-5 / PR-8 评审重点中显式承接，不构成 PR-1 验收阻塞。

---

## Changelog

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-04-20 | 自主文档 v2.2 §4.1 完整迁出，结构调整为子文档自包含形态；内容与主文档 v2.2 §4.1 等价 |
| v2.0 | 2026-04-20 | v1.2 review P0 收口：① Finding #1 修正 A3 行号锚点 L103-105 → L104-106（fenced ref + 正文叙述同步）；② Finding #10 方案 ① 落地 — 迁移脚本拉入 PR-1（涉及文件 4 → 5、工作量 0.93d → 1.3d、§2 新增 §2.5 完整脚本骨架含 ruamel.yaml 实现 + 反幂等 + dry-run、§3 DoD 追加迁移脚本可执行项、§2.2.2 兼容性引用 "§6.1" → "§2.5"、§4 回滚动作 cross-link 由"主文档 §6"改为"§2.5"）。Finding #2/#3/#4/#5/#6/#7/#8/#9/#11 共 9 项 P1/P2/P3 暂留，建议在代码施工完成后或跨 PR 阶段统一处理。 |
