# PR-2 · 编排器 step-pause 白名单受限双写 + step 4 case 规范化 + step 3 传参（v2.2 详细施工单）

> **主文档**：[`../../QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md`](../../QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md) §4（索引行）
> **子文档骨架**：[README.md §2](./README.md)
> **协议依赖**：附录 C **D1 / D2 / D8 / D14 / D15 / D16 / D17 / D18**（全部定义见主文档附录 C）
> **强前置 PR**：PR-1（协议层）已合入；本 PR 只对 `core/workflow.xml` 一个文件做改动
> **状态**：✅ 已展开（v2.2，2026-04-20）
> **唯一职责**：把 PR-1 在 `core/core-rules.xml` 中定义的 `<step-pause>` 协议（D2/D14/D15/D16/D18）落地到编排器 `core/workflow.xml`：
> 1. step 4 头部新增"用户回复解析 + 白名单受限双写 + parse_error_count 生命周期"；
> 2. step 4 内全部 6 个 step-pause case（含**新增**的 case Non-Bug step-pause）按 D16 补齐 `result_field` / `allowed_values` / `<input-protocol>` 标签；
> 3. step 3 各 case 的 `<load>` prompt 显式补传 `{issue_id}` / `{workflow_status}`（顺手修 m9）。

---

## 1. PR 元信息

| 项 | 值 |
|---|---|
| 分支命名 | `feat/qa-workflow-v4.1-pr2-orchestrator-step-pause` |
| Base | PR-1 合入后的 `main`（必须 rebase 到 PR-1 之后；PR-1 未合入禁止开 PR-2） |
| 层级 | 🔴 编排器层（紧随 PR-1，先于 PR-3/PR-4/PR-5） |
| 目标合入顺序 | **PR-1 → PR-2 → PR-4 → PR-3 → PR-5 → PR-6 → PR-7 → PR-8**（D9） |
| Reviewer | 1 名编排器 owner（必看 step 4 头部双写原子性 + 6 个 case 参数表） + 1 名协议 owner（必看 D14/D15/D16/D18 与 PR-1 `<input-protocol>` 5 条规则的逐条对齐） |
| 关联 issue | v4.1 主修复条目：**C11**（编排器侧 step-pause 白名单双写实现 + 现有 step-pause 参数表补齐）；附带 **m9**（step 3 `<load>` prompt 显式传参） |
| 工作量 | 0.40d（v2.0 0.3d + v2.1 case Non-Bug step-pause 规范化 +0.05d + v2.2 D18 生命周期补齐 +0.05d） |
| 涉及文件 | **1 个**：`core/workflow.xml`（修改） |
| 不在本 PR 范围 | ① 任何 `phases/**` 改动（D14：phase 内 step-pause 治理一律延后或归 PR-3/PR-5）② `core/core-rules.xml` 进一步修订（属 PR-1 范围）③ `core/workflow-status-template.yaml` 字段增删（属 PR-1 范围；本 PR 仅消费已注册的 `user_inputs` / `parse_error_count` / `non_bug_context` / 顶层镜像白名单）④ `legacy-phase-step-pause-allowlist.txt` 实体生成（属 PR-5 范围）⑤ CI 守门脚本（属 PR-8 范围）⑥ 文档同步（属 PR-7 范围） |

---

## 2. 文件级 diff 列表

> 本 PR 只动 `core/workflow.xml` 一个文件，下设 8 个变更点：W1（step 3 传参）+ W2（step 4 头部解析双写）+ W3-W8（step 4 内 6 个 step-pause case 规范化）。
> 所有变更点均**只新增或替换**，不删除既有 `<switch>` / `<case>` 结构骨架（保证 D1 方案 A 与现有顶层读取兼容）。

### 2.1 文件 A · `core/workflow.xml`（修改）

> **修复条目锚点**：C11（D2/D14/D15/D16/D18 编排器实现）/ m9（step 3 prompt 显式传参）

#### 2.1.1 变更点 W1 · step 3 各 case 的 `<load>` prompt 显式补传 `{issue_id}` / `{workflow_status}`（m9 part）

**原文（行号锚点 L43-87）**：

```43:87:mobile-qa-workflow/core/workflow.xml
            <step n="3" goal="执行当前阶段">
                <action>更新 {workflow_status}：current_state 设为对应状态，last_updated 设为当前时间</action>
                <action>初始化 {current_phase_result} = CONTINUE</action>

                <switch condition="{current_phase}">
                    <case if="qa-intake">
                        <load target="mobile-qa-workflow/phases/p1-intake.md" prompt="加载并执行，传递参数：
                            - config_source: {config_source}
                            - workspace_folder: {workspace_root}/{issue_id}
                            - issue_description: {issue_description}
                            - intake_document_url: {intake_document_url}"/>
                    </case>
                    <case if="qa-spec-definition">
                        <load target="mobile-qa-workflow/phases/p2-spec-definition.md" prompt="加载并执行，传递参数：
                            - config_source: {config_source}
                            - workspace_folder: {workspace_root}/{issue_id}
                            - issue_card: {workspace_root}/{issue_id}/issue-card.md"/>
                    </case>
                    <case if="qa-root-cause">
                        <load target="mobile-qa-workflow/phases/p3-root-cause.md" prompt="加载并执行，传递参数：
                            - config_source: {config_source}
                            - workspace_folder: {workspace_root}/{issue_id}
                            - env_subagent: {env_subagent}"/>
                    </case>
                    <case if="qa-fix-design">
                        <load target="mobile-qa-workflow/phases/p4-fix-design.md" prompt="加载并执行，传递参数：
                            - config_source: {config_source}
                            - workspace_folder: {workspace_root}/{issue_id}
                            - env_subagent: {env_subagent}"/>
                    </case>
                    <case if="qa-fix-impl">
                        <load target="mobile-qa-workflow/phases/p5-fix-impl.md" prompt="加载并执行，传递参数：
                            - config_source: {config_source}
                            - workspace_folder: {workspace_root}/{issue_id}
                            - env_subagent: {env_subagent}
                            - env_git: {env_git}"/>
                    </case>
                    <case if="qa-verification">
                        <load target="mobile-qa-workflow/phases/p6-verification.md" prompt="加载并执行，传递参数：
                            - config_source: {config_source}
                            - workspace_folder: {workspace_root}/{issue_id}
                            - env_subagent: {env_subagent}"/>
                    </case>
                </switch>
            </step>
```

**新文**（每个 case 的 `<load>` prompt 内**统一首两行追加**`issue_id` / `workflow_status`，其余参数原样保留；为可读性下文仅展示首两个 case，其余 4 个 case 同结构补齐）：

```xml
            <step n="3" goal="执行当前阶段">
                <action>更新 {workflow_status}：current_state 设为对应状态，last_updated 设为当前时间</action>
                <action>初始化 {current_phase_result} = CONTINUE</action>

                <switch condition="{current_phase}">
                    <case if="qa-intake">
                        <load target="mobile-qa-workflow/phases/p1-intake.md" prompt="加载并执行，传递参数：
                            - issue_id: {issue_id}
                            - workflow_status: {workflow_status}
                            - config_source: {config_source}
                            - workspace_folder: {workspace_root}/{issue_id}
                            - issue_description: {issue_description}
                            - intake_document_url: {intake_document_url}"/>
                    </case>
                    <case if="qa-spec-definition">
                        <load target="mobile-qa-workflow/phases/p2-spec-definition.md" prompt="加载并执行，传递参数：
                            - issue_id: {issue_id}
                            - workflow_status: {workflow_status}
                            - config_source: {config_source}
                            - workspace_folder: {workspace_root}/{issue_id}
                            - issue_card: {workspace_root}/{issue_id}/issue-card.md"/>
                    </case>
                    <!-- qa-root-cause / qa-fix-design / qa-fix-impl / qa-verification 同结构：
                         在 prompt 第二/三行依次追加：
                           - issue_id: {issue_id}
                           - workflow_status: {workflow_status}
                         其余原参数保持不变 -->
                </switch>
            </step>
```

**修订理由**：
- m9（v1.2.1 §三 m9 / 主文档 §3 PR-2 "顺手修 m9 中的 step 3 部分"）：现有 6 个 phase 调用都隐式依赖 phase 内能从全局上下文读到 `{issue_id}` 与 `{workflow_status}`，但 phase 文件实际经常出现"找不到 workflow-status.yaml 路径""无法回写 user_inputs"等问题。显式传参根除歧义，且与 PR-3 P2 写入 `non_bug_context` / `current_state = Non-Bug` 的接口契约对齐。
- D17 联动：PR-3 在 P2 内写 `non_bug_context` 时必须知道 `{workflow_status}` 的物理路径，本变更点是该写入的隐式前置。

**兼容性影响**：
- 旧 phase 文件不读 `issue_id` / `workflow_status` 也无害（多余参数 LLM 自动忽略）；新 phase 文件可显式消费。
- 与 PR-1 `core/workflow-status-template.yaml` 头部 `issue_id: null` 字段语义一致。

---

#### 2.1.2 变更点 W2 · step 4 头部新增"step-pause 用户回复解析 + 白名单受限双写 + parse_error_count 生命周期"块（D2 / D15 / D18）

**插入位置**：在原 step 4 第一行（`<check if="{current_phase_result} != ABORT">`，行号锚点 L90）**之前**，作为 step 4 的**第一个**子节点。

**原文（行号锚点 L89-100）**：

```89:100:mobile-qa-workflow/core/workflow.xml
            <step n="4" goal="阶段完成后更新进度并路由">
                <check if="{current_phase_result} != ABORT">
                    <action>将 {current_phase} 加入 {workflow_status} 的 stepsCompleted 数组</action>
                </check>
                <check if="{current_phase_result} == ABORT">
                    <action>保留 {workflow_status} 的 stepsCompleted 不变，等待当前阶段人工处理或补充信息后再重试</action>
                </check>
                <action>更新 {workflow_status} 的 lastStep 为 {current_phase}</action>
                <check if="rca_retry_count > 2 或 fix_retry_count > 2">
                    <action>触发重试熔断保护：更新 {workflow_status}：current_state = Human-Review</action>
                </check>
```

**新文**（在 `<step n="4" ...>` 开标签后、`<check if="{current_phase_result} != ABORT">` 之前**插入**整段新块，原有 4 段逻辑保持不变）：

```xml
            <step n="4" goal="阶段完成后更新进度并路由">
                <!-- ──────────────────────────────────────────────────────────────────
                     v4.1 / C11 / D2 / D15 / D18：step-pause 用户回复解析 + 白名单受限双写
                     ──────────────────────────────────────────────────────────────────
                     触发条件：本轮请求是上一轮 step-pause 的用户回复（按 PR-1 core-rules.xml
                     `<input-protocol> rule n=1/2` 识别 — 上一条 LLM 输出含
                     `[result_field=<key>]` 与 `[allowed_values=...]` 标签，本轮用户输入首行
                     形如 `<key>=<value>`）。识别失败时本块跳过，不影响下方既有路由逻辑。
                     ────────────────────────────────────────────────────────────────── -->
                <check if="本轮请求是上一轮 step-pause 的用户回复（按 input-protocol rule n=2 识别）">
                    <action>从用户回复首行解析 {key}={value}；{key} 必须等于上一轮 step-pause 的
                            result_field（不一致直接判定解析失败）；{value} 必须落在上一轮 step-pause
                            的 allowed_values 白名单内（不在直接判定解析失败）</action>

                    <check if="解析成功">
                        <!-- D15 白名单受限双写：user_inputs.<key> 总写；顶层 <key> 仅在白名单内才写 -->
                        <action>更新 {workflow_status}：user_inputs.{key} = {value}（D15 总写；
                                user_inputs 命名空间见 core/workflow-status-template.yaml）</action>
                        <check if="{key} ∈ workflow-status-template.yaml 顶层镜像白名单
                                   （v4.1 起步 = {non_bug_user_choice}）">
                            <action>同步镜像写入 workflow_status.{key} = {value}（D8 v4.1 双写过渡，
                                    v4.2 收敛后删除该动作 — 见 v4.2 遗留 #3）</action>
                        </check>
                        <action>更新 {workflow_status}：parse_error_count = 0（D18 解析成功立即清零）</action>
                    </check>

                    <check if="解析失败">
                        <action>更新 {workflow_status}：parse_error_count += 1（D18 +1）</action>
                        <check if="parse_error_count >= 3">
                            <action>更新 {workflow_status}：current_state = Human-Review</action>
                            <action>输出 [parse-exceed: 连续 3 次解析失败，转人工]
                                    （触发 core-rules.xml `<human-review-protocol>` trigger n=4/5 类）</action>
                            <action>更新 {workflow_status}：parse_error_count = 0（D18 熔断后清零）</action>
                            <!-- 不 goto，落入下方 switch；current_state = Human-Review 会进入 case Human-Review
                                 重新发起 Human-Review 通知 step-pause -->
                        </check>
                        <check if="parse_error_count &lt; 3">
                            <action>输出 [parse-error: 期望 {key} ∈ {allowed_values}]</action>
                            <action>重新触发同一 step-pause（current_state 不变；不修改 stepsCompleted；
                                    user_inputs 不写）</action>
                            <action>结束本回合（return；下方 ABORT/lastStep/switch 全部跳过）</action>
                        </check>
                    </check>
                </check>

                <!-- 既有逻辑（L90-99）保持不变 -->
                <check if="{current_phase_result} != ABORT">
                    <action>将 {current_phase} 加入 {workflow_status} 的 stepsCompleted 数组</action>
                </check>
                <check if="{current_phase_result} == ABORT">
                    <action>保留 {workflow_status} 的 stepsCompleted 不变，等待当前阶段人工处理或补充信息后再重试</action>
                </check>
                <action>更新 {workflow_status} 的 lastStep 为 {current_phase}</action>
                <check if="rca_retry_count > 2 或 fix_retry_count > 2">
                    <action>触发重试熔断保护：更新 {workflow_status}：current_state = Human-Review</action>
                </check>
```

**修订理由**：
- D2（v1.0 + v2.0 强化）：把 PR-1 `<input-protocol>` 5 条规则中**与编排器执行强相关**的 4 条（rule n=2/3/4/5）落地为可单步执行的 `<action>` / `<check>` 序列，让 LLM 在执行 step 4 时无需"猜测"协议含义。
- D15（v2.1）：双写代码**严格走"白名单 in"才写顶层**，严禁泛化"无条件双写"实现（与 PR-2 主文档评审重点第一条一致）。注释中显式列出 v4.1 起步白名单 `{non_bug_user_choice}`，与 `core/workflow-status-template.yaml` 顶层镜像白名单字段集"强契约"对齐（PR-8 CI 据此守门）。
- D18（v2.2）：`parse_error_count` 4 类生命周期动作（**进入新 step-pause 前清零** / 解析成功清零 / 解析失败 +1 / 熔断后清零）必须在编排器内完整出现 — 本变更点覆盖**后 3 类**，第 1 类（"进入新 step-pause 前清零"）在变更点 W3-W8 的 6 个 case 内分别落地。
- "结束本回合"动作语义：parse-error 重提路径**不能 fall-through 到下方 ABORT/switch**，否则会把 step-pause 用户回复误计入 stepsCompleted 或触发重复路由；显式中断本回合是"复发性 bug"防御。

**兼容性影响**：
- 本块由 `<check if="本轮请求是上一轮 step-pause 的用户回复">` 守门 — 任何**非 step-pause 回复**触发的 step 4（如 phase 正常完成回流）都跳过本块，保持与 v3 既有行为一致。
- 已合入 PR-1 是必要前提：`<input-protocol>` 标签语义、`user_inputs` / `parse_error_count` / 顶层镜像白名单字段集，全部依赖 PR-1。PR-1 未合入时 grep `core/workflow-status-template.yaml` 找不到上述字段，本块在解析期就会失败 — 这是 D9 PR 合入顺序约束的物理基础。
- 顶层 `non_bug_user_choice` 的双写让现有 `<switch condition="{non_bug_user_choice}">`（变更点 W5 后位于 case Non-Bug step-pause 之后）继续可用，**不破坏 v3 顶层读取契约**（D8 双写过渡核心红利）。

---

#### 2.1.3 变更点 W3 · step 4 case Info-Insufficient 升级（D16 参数表 + D18 reset）

**原文（行号锚点 L102-109）**：

```102:109:mobile-qa-workflow/core/workflow.xml
                    <case if="Info-Insufficient">
                        <step-pause title="信息不足，需要用户补充以下缺失项：
{missing_items}
">
                            <option title="[S] Submit：补充信息后继续
" action="收到补充信息后，goto step 2 重新执行 qa-intake"/>
                        </step-pause>
                    </case>
```

**新文**：

```xml
                    <case if="Info-Insufficient">
                        <!-- D18：进入新 step-pause 前重置 parse_error_count -->
                        <action>更新 {workflow_status}：parse_error_count = 0</action>

                        <step-pause title="信息不足，需要用户补充以下缺失项：
{missing_items}

[result_field=info_insufficient_action]
[allowed_values=Submit]
请用 info_insufficient_action=Submit 回复"
                                    result_field="info_insufficient_action"
                                    allowed_values="Submit">
                            <option title="[S] Submit：补充信息后继续，回流 qa-intake"
                                    action="info_insufficient_action=Submit"/>
                        </step-pause>

                        <!-- step-pause 用户回复解析 + 双写已在 step 4 头部完成（变更点 W2）；
                             此处依据 user_inputs 派发到下一步 -->
                        <switch condition="{user_inputs.info_insufficient_action}">
                            <case if="Submit">
                                <action>更新 {workflow_status}：current_state = Intake</action>
                                <action>清空 {workflow_status}.user_inputs.info_insufficient_action（消费一次性输入，避免下一轮 step 4 误派发）</action>
                                <goto step="2"/>
                            </case>
                        </switch>
                    </case>
```

**修订理由**：
- D16：`<step-pause>` 三必填参数（`title` / `result_field` / `allowed_values`）一次性补齐，与 PR-1 `<step-pause>` 参数表完全对齐；`<option>` 的 `action` 属性按 D16 协议形式 `<result_field>=<value>`。
- 标题尾部三行（`[result_field=...]` / `[allowed_values=...]` / `请用 ... 回复`）= PR-1 `<input-protocol>` rule n=1 的三件事一次出齐，让 LLM 在打印 step-pause 时**无需猜测**。
- D18 第 1 类生命周期动作"进入新 step-pause 前重置 parse_error_count"在 case 内显式落地。
- 派发 switch + "清空 user_inputs.<key>" 动作：保证**下一轮 step 4 不会误把上一次回复当成新输入**派发（防御性自闭环）。

**兼容性影响**：
- `info_insufficient_action` **不在**顶层镜像白名单（v4.1 白名单 = `{non_bug_user_choice}`），所以变更点 W2 双写时仅写 `user_inputs.info_insufficient_action`，**不污染顶层 schema**（D15 守门，PR-8 CI 强制）。
- 派发 case Submit 内的 `goto step="2"` 与原 v3 option 自然语言 `"goto step 2 重新执行 qa-intake"` 等价；额外 `current_state = Intake` 显式写入是为兼容编排器 step 2 在 `reroute_target_phase` 为空时根据 `current_state` 推导 `current_phase`。

---

#### 2.1.4 变更点 W4 · step 4 case Spec-Uncertain 升级（D16 参数表 + D18 reset + Reviewer 注）

**原文（行号锚点 L110-117）**：

```110:117:mobile-qa-workflow/core/workflow.xml
                    <case if="Spec-Uncertain">
                        <step-pause title="Spec 存在歧义，需要确认 Expected Behavior：
{spec_options}
">
                            <option title="[C] Confirm：确认后继续
" action="收到确认后，goto step 2 继续 qa-spec-definition"/>
                        </step-pause>
                    </case>
```

**新文**（保守对齐：`allowed_values="Confirm"`，与现有单选项 `[C] Confirm` 严格一致；主文档 PR-2 描述中提到的"`1|2|S`"是 v4.2 目标态，需 P2 同步外发多个 spec 选项才能落地，PR-2 不做该改造，**Reviewer 显式选择是否升级**）：

```xml
                    <case if="Spec-Uncertain">
                        <action>更新 {workflow_status}：parse_error_count = 0</action>

                        <step-pause title="Spec 存在歧义，需要确认 Expected Behavior：
{spec_options}

[result_field=spec_uncertain_choice]
[allowed_values=Confirm]
请用 spec_uncertain_choice=Confirm 回复"
                                    result_field="spec_uncertain_choice"
                                    allowed_values="Confirm">
                            <option title="[C] Confirm：确认后继续，回流 qa-spec-definition"
                                    action="spec_uncertain_choice=Confirm"/>
                        </step-pause>

                        <switch condition="{user_inputs.spec_uncertain_choice}">
                            <case if="Confirm">
                                <action>更新 {workflow_status}：current_state = Spec-Defining</action>
                                <action>清空 {workflow_status}.user_inputs.spec_uncertain_choice</action>
                                <goto step="2"/>
                            </case>
                        </switch>
                    </case>
```

**修订理由**：
- D16 / D18：与 W3 同理，参数表与 reset 动作齐备。
- **Reviewer 注（v2.2 主文档 §3 PR-2 description 第 4 项遗留）**：主文档原文 "建议 `spec_uncertain_choice` allowed_values = `1|2|S`"，但当前 P2 在 `{spec_options}` 中并未显式生成 `[1] / [2]` 多选项；强行升级会导致用户回复 `1` 或 `2` 时无法对应到具体 Spec 解读。本 PR 采取**保守口径**：与现有 `[C] Confirm` 选项严格对齐，allowed_values 收敛到单值 `Confirm`；待 v4.2 与 P2 内联 step-pause 一并整改时（v4.2 遗留 #6）再扩展为多值集合。如 Reviewer 选择本 PR 直接升级，需同步在 PR description 注明对 P2 `{spec_options}` 输出格式的契约要求（PR-3 不在 PR-2 范围内动 P2）。
- 与 PR-3 关系：PR-3 不动 case Spec-Uncertain（D14 收窄声明），P2 内现存 Spec-Uncertain 内联 step-pause 仍存在（与本 case **重复弹窗 bug**），属 v4.2 遗留 #6 治理目标，本 PR 不消除该 bug，仅保证编排器侧合规。

**兼容性影响**：同 W3。

---

#### 2.1.5 变更点 W5 · step 4 case Non-Bug 升级（D14 / D15 / D17 / D18 — 本 PR 改动最大的 case）

**原文（行号锚点 L118-140）**：

```118:140:mobile-qa-workflow/core/workflow.xml
                    <case if="Non-Bug">
                        <action>读取 p2 阶段 step-pause 用户选择结果</action>
                        <switch condition="{non_bug_user_choice}">
                            <case if="Accept">
                                <action>更新 {workflow_status}：current_state = Closed</action>
                                <action>工作流结束</action>
                            </case>
                            <case if="Reflow">
                                <action>读取 {workflow_status} 中的 non_bug_reflow_count</action>
                                <check if="non_bug_reflow_count >= 2">
                                    <action>同一问题已回流 2 次，触发 Human-Review 协议</action>
                                    <action>更新 {workflow_status}：current_state = Human-Review</action>
                                    <goto step="4"/>
                                </check>
                                <check if="non_bug_reflow_count &lt; 2">
                                    <action>在 Issue Card 中标注 [Re-Evaluated #{non_bug_reflow_count + 1}]</action>
                                    <action>将用户新证据追加到 issue-card.md</action>
                                    <action>更新 {workflow_status}：non_bug_reflow_count += 1, current_state = Spec-Defining</action>
                                    <goto step="2"/>
                                </check>
                            </case>
                        </switch>
                    </case>
```

**新文**（**关键改动**：① 删除"读取 p2 阶段 step-pause 用户选择结果"动作 — D14 后 P2 不再有 step-pause；② **首次进入** case 时由编排器**自身**发起 step-pause，标题用 `{non_bug_context}` 占位，由 PR-3 在 P2 写入；③ 用户回复后由变更点 W2 双写到顶层 `non_bug_user_choice` 与 `user_inputs.non_bug_user_choice`，下方既有 `<switch condition="{non_bug_user_choice}">` 直接命中；④ 用 `<check if="user_inputs.non_bug_user_choice 为空">` 控制 step-pause 仅在首次进入时发起，避免重入时重复弹窗）：

```xml
                    <case if="Non-Bug">
                        <!-- 阶段 1：若用户尚未回复，发起 Non-Bug 判定确认 step-pause（D14 编排器统一调度） -->
                        <check if="{workflow_status}.user_inputs.non_bug_user_choice 为空（即首次进入或上一轮已消费）">
                            <action>更新 {workflow_status}：parse_error_count = 0（D18 进入新 step-pause 前重置）</action>

                            <step-pause title="Non-Bug 判定结果，请确认处理方向：

{non_bug_context}

[result_field=non_bug_user_choice]
[allowed_values=Accept|Reflow]
请用 non_bug_user_choice=&lt;value&gt; 回复"
                                        result_field="non_bug_user_choice"
                                        allowed_values="Accept|Reflow">
                                <option title="[A] Accept：接受 Non-Bug 判定，关闭 issue"
                                        action="non_bug_user_choice=Accept"/>
                                <option title="[R] Reflow：补充证据后重新进入 Spec-Defining 重审"
                                        action="non_bug_user_choice=Reflow"/>
                            </step-pause>
                        </check>

                        <!-- 阶段 2：用户已回复 → 变更点 W2 已完成解析与双写（user_inputs.non_bug_user_choice
                             与顶层 non_bug_user_choice 同步存在）；下方既有 switch 直接命中，无需任何改动。 -->
                        <switch condition="{non_bug_user_choice}">
                            <case if="Accept">
                                <action>更新 {workflow_status}：current_state = Closed</action>
                                <action>清空 {workflow_status}.user_inputs.non_bug_user_choice 与顶层 non_bug_user_choice
                                        （消费一次性输入；下一次同 issue 进入 Non-Bug 才能再次发起 step-pause）</action>
                                <action>工作流结束</action>
                            </case>
                            <case if="Reflow">
                                <action>读取 {workflow_status} 中的 non_bug_reflow_count</action>
                                <check if="non_bug_reflow_count >= 2">
                                    <action>同一问题已回流 2 次，触发 Human-Review 协议
                                            （core-rules.xml `<human-review-protocol>` trigger n=6）</action>
                                    <action>更新 {workflow_status}：current_state = Human-Review</action>
                                    <action>清空 {workflow_status}.user_inputs.non_bug_user_choice 与顶层 non_bug_user_choice</action>
                                    <goto step="4"/>
                                </check>
                                <check if="non_bug_reflow_count &lt; 2">
                                    <action>在 Issue Card 中标注 [Re-Evaluated #{non_bug_reflow_count + 1}]</action>
                                    <action>将用户新证据追加到 issue-card.md</action>
                                    <action>更新 {workflow_status}：non_bug_reflow_count += 1, current_state = Spec-Defining</action>
                                    <action>清空 {workflow_status}.user_inputs.non_bug_user_choice 与顶层 non_bug_user_choice</action>
                                    <goto step="2"/>
                                </check>
                            </case>
                        </switch>
                    </case>
```

**修订理由**：
- D14（v2.1）：v3 的 case Non-Bug 不发起 step-pause，依赖 P2 内联 step-pause；v4.1 把 P2 内联 step-pause 移除（PR-3），**Non-Bug 用户确认 step-pause 必须改由编排器统一调度**。本变更点是 D14 在编排器侧的**唯一**实施落地（PR-1 是协议层声明，PR-3 是 P2 phase 侧"早退而非弹窗"，PR-2 是编排器侧"接管弹窗"）。
- D15（v2.1）：`non_bug_user_choice` ∈ v4.1 起步顶层镜像白名单，所以变更点 W2 会**双写**`user_inputs.non_bug_user_choice` + 顶层 `non_bug_user_choice`；既有 `<switch condition="{non_bug_user_choice}">` 读取顶层值仍可用 — 这是 D8 双写过渡的**关键红利**，**整段 switch 内部 4 个分支与 v3 完全等价**，无破坏性变更。
- D17（v2.2）：step-pause 标题中的 `{non_bug_context}` 占位由 PR-3 在 P2 内显式写入 `workflow_status.non_bug_context`（"Working-As-Designed"等判定文本）。占位失败（即 PR-3 未合入或 P2 漏写）时降级输出空串，不会让 step-pause 不可用 — Reviewer 可在 PR-3 同周期联调验证。
- D18（v2.2）：在 case 内显式增加 `parse_error_count = 0` 重置动作，覆盖第 1 类生命周期。
- "首次进入"守门 (`<check if="user_inputs.non_bug_user_choice 为空">`)：避免用户已回复一次后，工作流在某个其他路径重新进入 case Non-Bug 时**重复发起**同一 step-pause 把用户已经做出的选择"回滚"掉。
- "消费一次性输入"清空动作（出现在所有分支末尾）：保证下一次同 issue 真正进入 Non-Bug 时（如二次 Spec-Defining 后再被判定为 Non-Bug）能正确**重新发起**确认 step-pause。

**兼容性影响**：
- **关键兼容性红利**：删除"读取 p2 阶段 step-pause 用户选择结果"是**唯一一处与 v3 行为不等价的语义变更**，但仅当 PR-3 同周期合入移除 P2 内联 step-pause 时才生效；PR-2 单独合入时该动作变为"读取一个 P2 不再产出的字段"，效果等价于 noop（顶层 `non_bug_user_choice` 仍由变更点 W2 写，原 switch 仍可用）。**因此 PR-2 与 PR-3 的合入时间窗口可以解耦**（与 D9 PR-4 → PR-3 顺序兼容，PR-3 后置不破坏 PR-2）。
- 已合入 PR-1 是必要前提：`non_bug_context` 字段、`non_bug_user_choice` 顶层镜像白名单、`user_inputs` 命名空间均依赖 PR-1。

---

#### 2.1.6 变更点 W6 · step 4 case RCA-LowConfidence 升级（D16 参数表 + D18 reset）

**原文（行号锚点 L141-149）**：

```141:149:mobile-qa-workflow/core/workflow.xml
                    <case if="RCA-LowConfidence">
                        <step-pause title="根因分析置信度不足（&lt; 0.5），建议处理方向：{suggestion}
">
                            <option title="[R] Retry：补充上下文后重新分析
" action="goto step 2 回到 qa-spec-definition 补充证据"/>
                            <option title="[H] Human：转人工处理
" action="触发 Human-Review 协议"/>
                        </step-pause>
                    </case>
```

**新文**：

```xml
                    <case if="RCA-LowConfidence">
                        <action>更新 {workflow_status}：parse_error_count = 0</action>

                        <step-pause title="根因分析置信度不足（&lt; 0.5），建议处理方向：{suggestion}

[result_field=rca_lowconf_action]
[allowed_values=Retry|Human]
请用 rca_lowconf_action=&lt;value&gt; 回复"
                                    result_field="rca_lowconf_action"
                                    allowed_values="Retry|Human">
                            <option title="[R] Retry：补充上下文后重新分析（回流 qa-spec-definition）"
                                    action="rca_lowconf_action=Retry"/>
                            <option title="[H] Human：转人工处理"
                                    action="rca_lowconf_action=Human"/>
                        </step-pause>

                        <switch condition="{user_inputs.rca_lowconf_action}">
                            <case if="Retry">
                                <action>更新 {workflow_status}：current_state = Spec-Defining</action>
                                <action>清空 {workflow_status}.user_inputs.rca_lowconf_action</action>
                                <goto step="2"/>
                            </case>
                            <case if="Human">
                                <action>更新 {workflow_status}：current_state = Human-Review</action>
                                <action>清空 {workflow_status}.user_inputs.rca_lowconf_action</action>
                                <goto step="4"/>
                            </case>
                        </switch>
                    </case>
```

**修订理由**：与 W3/W4 同理。`rca_lowconf_action` **不在**顶层白名单，仅写 `user_inputs.rca_lowconf_action`，下方派发 switch 显式从 `user_inputs.*` 读取。

**兼容性影响**：
- 原 v3 option 注释 "建议处理方向（< 0.5）"中的"0.5"与 PR-1 `<input-protocol>` 中 RCA 置信度阈值一致，**未变更阈值语义**。
- 原 [H] Human 选项的 v3 自然语言 "触发 Human-Review 协议" 现以 `current_state = Human-Review` + `goto step="4"` 显式落地，行为完全等价（goto 4 后落入 case Human-Review 触发 Human-Review 通知）。

---

#### 2.1.7 变更点 W7 · step 4 case Human-Review 升级（D16 参数表 + D18 reset）

**原文（行号锚点 L150-157）**：

```150:157:mobile-qa-workflow/core/workflow.xml
                    <case if="Human-Review">
                        <action>输出 Human-Review 通知（按 core-rules.xml 中的 human-review-protocol 格式）</action>
                        <step-pause title="⚠️ 需要人工介入，请处理后告知继续方向
">
                            <option title="[C] Continue：人工处理完成，继续工作流
" action="根据人工指令更新状态，goto step 2"/>
                        </step-pause>
                    </case>
```

**新文**：

```xml
                    <case if="Human-Review">
                        <action>输出 Human-Review 通知（按 core-rules.xml 中的 human-review-protocol 格式）</action>
                        <action>更新 {workflow_status}：parse_error_count = 0</action>

                        <step-pause title="⚠️ 需要人工介入，请处理后告知继续方向

[result_field=human_review_continue]
[allowed_values=Continue]
请用 human_review_continue=Continue 回复"
                                    result_field="human_review_continue"
                                    allowed_values="Continue">
                            <option title="[C] Continue：人工处理完成，继续工作流"
                                    action="human_review_continue=Continue"/>
                        </step-pause>

                        <switch condition="{user_inputs.human_review_continue}">
                            <case if="Continue">
                                <action>根据人工指令更新 {workflow_status} 中的 current_state / 各计数器字段
                                        （由人工在回复正文中以 YAML 片段形式追加；编排器读取并合并到 workflow_status）</action>
                                <action>清空 {workflow_status}.user_inputs.human_review_continue</action>
                                <goto step="2"/>
                            </case>
                        </switch>
                    </case>
```

**修订理由**：与 W3 同理。注意 v3 原文 "根据人工指令更新状态" 是高度依赖 LLM 自行解释的自然语言；新文里改为"在 case 内显式描述 — 人工在回复正文里追加 YAML，编排器合并"，**保持 v3 行为语义**但描述更精确。

**兼容性影响**：人工指令的格式（YAML 片段）属事实标准，本 PR 不引入新约束；如未来 Reviewer 希望进一步规范，可在 v4.2 补 `<input-protocol>` 子规则。

---

#### 2.1.8 变更点 W8 · step 4 case Curation-Failed 升级（D16 参数表 + D18 reset）

**原文（行号锚点 L163-171）**：

```163:171:mobile-qa-workflow/core/workflow.xml
                    <case if="Curation-Failed">
                        <step-pause title="上下文策展失败（置信度 &lt; 0.4），请补充信息或转人工：
">
                            <option title="[R] Retry：补充信息后重新策展
" action="goto step 2 回到 qa-spec-definition 补充证据"/>
                            <option title="[H] Human：转人工处理
" action="触发 Human-Review 协议"/>
                        </step-pause>
                    </case>
```

**新文**：

```xml
                    <case if="Curation-Failed">
                        <action>更新 {workflow_status}：parse_error_count = 0</action>

                        <step-pause title="上下文策展失败（置信度 &lt; 0.4），请补充信息或转人工：

[result_field=curation_failed_action]
[allowed_values=Retry|Human]
请用 curation_failed_action=&lt;value&gt; 回复"
                                    result_field="curation_failed_action"
                                    allowed_values="Retry|Human">
                            <option title="[R] Retry：补充信息后重新策展（回流 qa-spec-definition）"
                                    action="curation_failed_action=Retry"/>
                            <option title="[H] Human：转人工处理"
                                    action="curation_failed_action=Human"/>
                        </step-pause>

                        <switch condition="{user_inputs.curation_failed_action}">
                            <case if="Retry">
                                <action>更新 {workflow_status}：current_state = Spec-Defining</action>
                                <action>清空 {workflow_status}.user_inputs.curation_failed_action</action>
                                <goto step="2"/>
                            </case>
                            <case if="Human">
                                <action>更新 {workflow_status}：current_state = Human-Review</action>
                                <action>清空 {workflow_status}.user_inputs.curation_failed_action</action>
                                <goto step="4"/>
                            </case>
                        </switch>
                    </case>
```

**修订理由**：与 W6 完全同构（同样的 `Retry|Human` 二选一），仅业务语义差异。

**兼容性影响**：原 v3 行为完全保留，只是把"goto step 2 回到 qa-spec-definition"等自然语言落到结构化 `current_state = Spec-Defining + goto step="2"`。

---

### 2.2 顶层镜像白名单合规性矩阵（PR-2 自检）

> 本表是变更点 W2 的"白名单 in"判定的**唯一权威依据**，与 PR-1 `core/workflow-status-template.yaml` 顶层镜像白名单严格对齐；PR-8 CI 据此守门。

| step-pause case | result_field | allowed_values | 是否在顶层白名单 | 双写动作（变更点 W2 实施） |
|---|---|---|---|---|
| Info-Insufficient | `info_insufficient_action` | `Submit` | ❌ 不在 | 仅写 `user_inputs.info_insufficient_action` |
| Spec-Uncertain | `spec_uncertain_choice` | `Confirm` | ❌ 不在 | 仅写 `user_inputs.spec_uncertain_choice` |
| Non-Bug | `non_bug_user_choice` | `Accept`\|`Reflow` | ✅ **在白名单**（v4.1 起步唯一项） | 双写：`user_inputs.non_bug_user_choice` + 顶层 `non_bug_user_choice` |
| RCA-LowConfidence | `rca_lowconf_action` | `Retry`\|`Human` | ❌ 不在 | 仅写 `user_inputs.rca_lowconf_action` |
| Human-Review | `human_review_continue` | `Continue` | ❌ 不在 | 仅写 `user_inputs.human_review_continue` |
| Curation-Failed | `curation_failed_action` | `Retry`\|`Human` | ❌ 不在 | 仅写 `user_inputs.curation_failed_action` |

> **强契约说明**：
> - 任何后续 PR 试图把上表"❌ 不在"的 result_field 写入顶层 schema → 必须先在 `core/workflow-status-template.yaml` 顶层镜像白名单注释段落显式注册 + 同步 PR-1 文档同步动作 + PR-8 CI 复测；不得仅在 `core/workflow.xml` 单边添加。
> - 仅有 `non_bug_user_choice` 写顶层是**有意为之**：与编排器现有 `<switch condition="{non_bug_user_choice}">` 顶层读取契约兼容（D8 双写过渡），其余 5 个 case 内部派发 switch **统一从 `user_inputs.*` 读取**，避免污染顶层 schema。

---

## 3. PR-level DoD 子集（链接到主文档 §5）

> 完整清单见主文档 [§5.1 静态契约校验](../../QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md#51-静态契约校验每个-pr-必跑) 与 [§5.2 动态用例](../../QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md#52-动态用例关键回归路径)。本节仅列 PR-2 必须满足的子集。

### 3.1 §5.1 静态契约校验（PR-2 必跑子集）

- [ ] **step-pause 参数表完整**（§5.1 第 10 项 / D16）：grep `core/workflow.xml` 中所有 `<step-pause` 标签，**6 处**全部同时声明 `title` + `result_field` + `allowed_values`（缺一项 fail）。
- [ ] **step-pause 输入协议完整**（§5.1 第 12 项 / D2）：6 处 step-pause 标题尾部均含 3 行机器可读标签：`[result_field=<key>]` / `[allowed_values=<v1>|<v2>|...]` / `请用 <key>=<value> 回复`；每个 `<option>` 的 `action` 属性形式严格为 `<result_field>=<value>` 且 `<value>` 命中 allowed_values。
- [ ] **顶层镜像白名单受限**（§5.1 第 13 项 / D15）：grep `core/workflow.xml` 头部双写动作（变更点 W2），**必须**包含 `<check if="{key} ∈ workflow-status-template.yaml 顶层镜像白名单">`；除 case Non-Bug（`non_bug_user_choice`）外的 5 个 case 派发 switch **必须**从 `{user_inputs.*}` 读取，**不得**直接读取顶层 `{xxx_user_choice}` / `{xxx_action}` / `{xxx_choice}` / `{xxx_continue}` 形式（grep 反向校验：`{(info_insufficient_action|spec_uncertain_choice|rca_lowconf_action|human_review_continue|curation_failed_action)}` 不带 `user_inputs.` 前缀的命中应为 0）。
- [ ] **parse-error 生命周期闭合**（§5.1 第 14 项 / D18）：grep `core/workflow.xml`，必须同时包含 4 类 parse_error_count 动作：
  - `parse_error_count += 1`（解析失败）= 变更点 W2 内出现 1 次
  - `parse_error_count = 0`（解析成功后清零）= 变更点 W2 内出现 1 次
  - `parse_error_count = 0`（进入新 step-pause 前重置）= 变更点 W3-W8 各出现 1 次（共 6 次）
  - `parse_error_count = 0`（熔断后清零）= 变更点 W2 内出现 1 次
  - 合计至少 9 处 `parse_error_count` 写入动作。
- [ ] **D14 调度作用域守门间接达成**（§5.1 第 11 项）：本 PR 仅在 `core/workflow.xml` 编排器 step 4 内放置 `<step-pause>`，**不修改任何 phase 文件**（grep PR diff 验证：`phases/` / `functionality-deep-dive/phases/` 路径下命中数 = 0）。
- [ ] **case Non-Bug 自闭环正确性**（变更点 W5 私有 DoD）：
  1. step-pause 由 `<check if="user_inputs.non_bug_user_choice 为空">` 守门（"首次进入"语义）；
  2. 删除原 v3 "读取 p2 阶段 step-pause 用户选择结果" 动作；
  3. step-pause 标题包含 `{non_bug_context}` 占位（与 PR-3 写入端对齐 D17）；
  4. 现有 `<switch condition="{non_bug_user_choice}">` **保持原有 4 个分支**（Accept / Reflow + non_bug_reflow_count 子分支），仅在每个分支末尾追加"清空 user_inputs.non_bug_user_choice 与顶层 non_bug_user_choice"动作。
- [ ] **step 3 显式传参**（m9）：grep step 3 的 6 个 case `<load>` prompt，**全部**首段 2 行追加 `issue_id: {issue_id}` / `workflow_status: {workflow_status}`。

### 3.2 §5.2 动态用例（PR-2 必跑子集）

- [ ] **§5.2.4 用例 D · C11 step-pause 编排器侧规范化（D14/D15/D16）** 全部 5 项断言通过 — 这是 PR-2 的**核心验收用例**，必须在 PR description 附 LLM 重放 trace。
- [ ] **§5.2.2 用例 B · B2 P2 Non-Bug 反流** 第 2-5 项断言（"编排器 step 4 触发 step-pause" → "白名单受限双写" → "switch 命中 Reflow" → "non_bug_reflow_count = 1"）通过；本 PR 不验收第 1 项（"P2 phase 内写 non_bug_context → 写 current_state = Non-Bug → 设 ABORT → 退出 phase"），该项由 PR-3 验收。
- [ ] **回归用例**：模拟 6 个 case 各 3 次连续解析失败，断言每次第 3 次失败时 `current_state` 切换到 Human-Review、`parse_error_count` 在熔断后清零、Human-Review case 重新发起 step-pause。

> **PR-2 不验收的 §5.x 项**（由后续 PR 联动）：
> - §5.1 第 1/2/3/4/5/6/7/8/9/15/16/17 项 → PR-1 / PR-3 / PR-4 / PR-5 / PR-7 / PR-8 承接
> - §5.2.1 用例 A（B1\* P3 RCA 低置信回流） → PR-4 验收（PR-2 仅保证编排器 case 不破坏 ABORT 标记的 stepsCompleted 行为）
> - §5.2.3 用例 C（C10 字段污染） → PR-4 验收
> - §5.2.5 用例 E（B3 Deep-Dive 落盘） → PR-5 验收
> - §5.2.6 用例 F（C9 P6 失败分支产物） → PR-4 + PR-6 联合验收

---

## 4. PR-level 回滚动作（链接到主文档 §7）

完整回滚预案见主文档 [§7.2 PR-2 回滚](../../QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md#72-pr-2-回滚v20-调整双写丢失影响显著)，关键点摘录：

- **回滚命令**：`git revert <PR-2-merge-commit>`。
- **回滚后状态**：
  - `core/workflow.xml` step 4 头部 step-pause 解析与白名单受限双写块**消失** → 用户回复**不再被双写**到 `user_inputs.*` 与顶层 `non_bug_user_choice`；
  - 6 个 step-pause case 的 `result_field` / `allowed_values` 标签**消失** → step-pause 输出格式回退到 v3 隐式语义；
  - case Non-Bug 重新依赖"P2 阶段 step-pause 用户选择结果"，但若 PR-3 已合入（D14 移除 P2 内联 step-pause），将出现 `non_bug_user_choice` 永远为空 → **case Non-Bug 完全卡住**（switch 落入空分支，工作流停滞）；
  - `parse_error_count` 不再自增/清零 → 用户随意回复均被 LLM 隐式接受，**3 次熔断保护失效**；
  - step 3 显式传参（m9 part）回退 → phase 文件需自行从全局上下文猜测 `issue_id` / `workflow_status` 路径，回归 m9 老问题。
- **下游影响**：
  - PR-3 / PR-4 / PR-5 中的 `<action>设置 current_phase_result = ABORT</action>` 标记**仍然生效**（运行时变量行为不依赖 PR-2，方案 A 红利）；但 step-pause 用户回复链路完全断。
  - PR-3 已合入时，**case Non-Bug 卡死**风险特别高 → 必须在 PR-2 回滚同时**临时回退 PR-3 P2 早退分支**（手工 hotfix：在 PR-3 移除的位置临时恢复 P2 内联 step-pause），或同步 revert PR-3。
- **风险等级**：🟡 **中**（v1.0 同等级）— 单独 revert PR-2 **会立即破坏 B2 闭环 + 6 个 case step-pause 输入协议**，需谨慎；建议先评估"新 commit 修补"路线。
- **存量 v3 会话兼容**：PR-1 引入的迁移脚本不依赖 PR-2，回滚后存量已迁移到 v4 的会话**仍然为 v4 schema**，但 v4.1 顶层镜像字段 `non_bug_user_choice` 永远不会被双写更新 → 这些会话需通过手工编辑或 v4.2 收敛动作清理。

---

## 5. §5.1 静态契约校验自检（PR-2 视角）

> 按主文档 §5.1 17 项清单逐项核查 PR-2 是否落地或留待后续 PR 联动。✅ = 本 PR 满足；⏸ = 不在本 PR 范围（标注承接方）；➖ = 本 PR 不引入但需间接守住。

| § 5.1 校验项 | PR-2 状态 | 落地证据 / 承接方 |
|---|---|---|
| 1. Schema 自洽（current_state 取值有定义） | ➖ | 本 PR 引入的新 `current_state` 写入（如 `Spec-Defining` / `Human-Review` 等）均已在 PR-1 头部注释枚举集内 |
| 2. Schema 版本升级显式（schema_version=4） | ⏸ | PR-1 承接 |
| 3. Non-Bug 上下文字段已注册（D17） | ➖ | 本 PR 在变更点 W5 step-pause 标题消费 `{non_bug_context}` 占位；字段注册由 PR-1 完成；写入端由 PR-3 完成 |
| 4. parse-error 计数器已注册（D18） | ➖ | 字段由 PR-1 注册；生命周期由本 PR 变更点 W2 + W3-W8 的 9 处动作完整闭合 |
| 5. 配置键名注册（config-schema） | ⏸ | PR-1 承接 |
| 6. 标签白名单（含 `<task>` + 边界声明） | ⏸ | PR-1 承接；本 PR 不引入新标签 |
| 7. 字段隔离（fanout_mode 不重命名 / fix_fanout_mode 新增） | ➖ | 本 PR 不动 fanout 字段族 |
| 8. ❌ 不存在 `rca_fanout_mode` 裸字段（D7 反向校验） | ➖ | grep `core/workflow.xml` 命中 0 处 |
| 9. ABORT 标记完整（phases 5+ 处） | ⏸ | PR-3 / PR-4 承接 |
| 10. step-pause 参数表完整（D16） | ✅ | 变更点 W3-W8 / 6 处 step-pause `<params>` |
| 11. step-pause 调度作用域守门（D14） | ➖ | 本 PR 仅在编排器内增/改 step-pause；不修改 phase 文件（diff 守门） |
| 12. step-pause 输入协议完整（标题后缀 + parse-error） | ✅ | 变更点 W2（parse-error 全链路）+ W3-W8 标题尾部 3 行标签 |
| 13. 顶层镜像白名单受限（D15） | ✅ | 变更点 W2 含"白名单 in"判断；§2.2 合规矩阵 6 行逐项核对 |
| 14. parse-error 生命周期闭合（编排器侧 4 类动作） | ✅ | 变更点 W2（+1 / 解析成功清零 / 熔断后清零）+ W3-W8（进入新 step-pause 前清零，6 处）合计 ≥ 9 处 |
| 15. 持久化字段表纯净性（无 `current_phase_result`） | ➖ | 本 PR 仅消费 `{current_phase_result}` 运行时变量（既有 step 3 L45 与 step 4 L90/L93），不写入 schema |
| 16. 顶层镜像字段过渡标注（"v4.2 收敛"） | ➖ | 标注由 PR-1 完成；本 PR 仅消费白名单语义 |
| 17. allowlist 交付完整（D19） | ⏸ | PR-5 生成首版 + PR-8 CI 消费 |

**自检结论**：PR-2 落地主文档 §5.1 中编排器层可独立验收的 4/17 项（第 10/12/13/14 项）；其余 13 项中 9 项属于 ➖（不引入但间接守住，本 PR diff 不破坏）、4 项 ⏸（明确承接方）。**PR-2 是 §5.1 第 13/14 两项的唯一落地点**，PR Review 必须重点核查这两项的 grep 证据。

---

## Changelog

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-04-20 | 自主文档 v2.2 §3 PR-2 描述完整展开为子文档；引入 8 个变更点（W1-W8）+ 顶层镜像白名单合规性矩阵 + PR-level DoD 子集 + 回滚动作 + §5.1 自检表；保守对齐 Spec-Uncertain `allowed_values="Confirm"`（与现状选项一致；主文档建议的 `1|2|S` 升级因依赖 P2 多选项输出，登记为 PR Review 议题） |
