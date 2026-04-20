# Mobile B2C 质量工作流 — 深度质检报告

> **审计范围**：`/Users/bytedance/Code/loupe/mobile-qa-workflow/` 全部 70 余个文件
> **审计视角**：AI Skills 工程化 + 移动端质量闭环 + LLM 编排可靠性
> **输出维度**：模块评分 → 缺陷台账 → 优化建议 → 优先级矩阵
> **审计日期**：2026-04-20
> **报告版本**：v1.0

---

## 一、整体评估

| 维度 | 评分（10 分制） | 简评 |
|---|---|---|
| 架构分层 | 8 | 主链路 + Deep-Dive 双层、共享基座 + 包装层思路清晰 |
| 角色契约一致性 | 5.5 | 共享基座/包装层/调用方三层之间字段对不齐 |
| 状态机可靠性 | 5 | `reroute_target_phase` 与 `stepsCompleted` 存在系统性路由漏洞 |
| 模板与产物治理 | 6 | 模板字段冗余/重复，与流程实际产出错位 |
| 标签 DSL 规范 | 6 | `core-rules.xml` 未声明 `<task>`，但所有 `workflow.xml` 都用了 |
| 跨工作流（主/Deep-Dive）一致性 | 4.5 | 默认值冲突、状态枚举漂移、产物落盘策略矛盾 |
| 文档/入口一致性 | 6.5 | `SKILL.md`、`system-prompt.md`、`PLATFORM-GUIDE.md` 内容未对齐 |
| 安装/分发 | 7 | 健壮但 `install.sh` 与 `install_trae.sh` 严重重复 |

**综合得分：6.0/10** — 设计意图与抽象到位，但**契约层（schema、字段、枚举、I/O 协议）的对齐度严重不足**，在真实多 Agent 编排环境中会出现路由错乱、状态丢失、产物缺失等问题。

---

## 二、模块级雷达图（缺陷数 / 严重等级）

| 模块 | Blocker | Critical | Major | Minor |
|---|---|---|---|---|
| 顶层入口（SKILL/system-prompt/PLATFORM-GUIDE） | 0 | 2 | 4 | 3 |
| `core/`（workflow.xml + 4 个 yaml + core-rules） | 1 | 4 | 6 | 4 |
| `agents/`（8 个） | 0 | 3 | 5 | 4 |
| `phases/`（P1–P6） | 2 | 5 | 7 | 5 |
| `templates/`（14 个） | 0 | 1 | 6 | 6 |
| `reference/`（4 个） | 0 | 0 | 3 | 2 |
| `functionality-deep-dive/`（25+） | 1 | 4 | 7 | 4 |

---

## 三、缺陷台账（按严重等级降序）

### 🔴 BLOCKER（阻塞工作流正确执行）

#### B1. P3 重路由与 `stepsCompleted` 互锁，重入根因分析时阶段会被跳过
- **位置**：`core/workflow.xml` step 4 + `phases/p3-root-cause.md` step 5 + `phases/p6-verification.md` step 6
- **现象**：P3 内部升级 fan-out 时把 `reroute_target_phase = qa-root-cause` 并"阶段结束返回编排器"。但回到 `workflow.xml` step 4 时，由于 `current_phase_result != ABORT`，**`qa-root-cause` 已被加入 `stepsCompleted`**。下一次循环 step 2 优先识别 reroute 字段后清空，再轮到 P6 回流到 P3 时同样问题。状态字段虽对齐，但已完成阶段集合无法表示"重入"。
- **影响**：升级到 `medium-challenge` / `complex-arbitrated` 的二次 RCA 实际不会被执行；P6 回流的 `root_cause_not_closed` 也会失效。
- **修复建议**：升级路径必须将 `current_phase_result = ABORT`（与失败回流统一），或者在 step 4 中"识别到非空 reroute_target_phase 时回退一次 stepsCompleted"。建议增设 `stepsCompleted` 只追加唯一项的语义改造为 `phase_history`（可重复）+ `latest_completed_phase`（最近一次）。

#### B2. P2 `qa-spec-definition` 完全缺失 Non-Bug 处理路径
- **位置**：`phases/p2-spec-definition.md` step 4
- **现象**：仅写了"逐项检查 Working-As-Designed / User-Misoperation / …"，**未触发 step-pause、未写回 `current_state = Non-Bug`、未读写 `non_bug_user_choice` / `non_bug_reflow_count`**。
- 而 `core/workflow.xml` step 4 的 `Non-Bug` case 完全依赖这些字段。
- **影响**：Non-Bug 反流闭环（含 ≤2 次 Reflow / >2 次 Human-Review）实际**永远不会触发**。`system-prompt.md` 的 P2 step 4 反而是完整版，主工作流 vs system-prompt 实现不一致。
- **修复建议**：把 `system-prompt.md` 的 P2 step 4 完整结构（输出 Non-Bug Resolution Report → step-pause → Accept/Reflow + 计数器）补回 `phases/p2-spec-definition.md`，并新增字段 `non_bug_user_choice` 到 `workflow-status-template.yaml`。

#### B3. Deep-Dive F2/F3 中间产物默认不落盘 → F4 读不到
- **位置**：`functionality-deep-dive/core/default-config.yaml` (`emit_topology_report: false`、`emit_concurrency_report: false`、`emit_environment_factor_report: false`) + `phases/f1`/`f2`/`f3` 末尾的"保留供 F4 回注，不强制独立落盘"
- **现象**：F4 phase 入参 `topology_report` / `concurrency_report` 是文件路径变量，不落盘则**没有任何介质供 F4 / F5 读取**（沉入"附录"在 LLM 多 SubAgent 隔离场景下无对话上下文回传）。
- 此外主工作流 `core/default-config.yaml` 的 `deep_dive_optional_artifacts.environment_factor_report: true` **与 deep-dive 的 false 直接打架**。
- **修复建议**：要么默认 `emit_*_report: true` 与主配置一致；要么在 deep-dive workflow.xml 设计内存式 handoff（不可取，多 SubAgent 隔离不允许内存共享）。强烈建议**强制 F1/F2/F3 必须落盘**，并在主入口侧只控制是否回注到 RCA 附录，与"产物可独立审计"原则一致。

---

### 🟠 CRITICAL（功能/契约严重错位）

#### C1. `<task>` 标签未在 `core-rules.xml` 的 supported-tags 中声明
- **位置**：`core/workflow.xml` 第 1 行 `<task id="…">`、`functionality-deep-dive/core/workflow.xml` 同样
- `core-rules.xml` `<supported-tags>` 仅列了 `flow / step / check / switch / for-each / action / load / invoke-subagent / workflow-status-routing / goto / step-pause / ask / try / template-output`。
- **影响**：严格遵守 core-rules 的 Agent 会拒识 `<task>` 容器。
- **修复**：要么把 `<task>` 加入 supported-tags，要么把两个 workflow.xml 的根容器统一改成 `<flow>` 包装（与 SKILL.md 风格一致）。

#### C2. 共享基座的输入契约与调用方传参严重缺位
- `agents/shared-arbiter-base.md` 输入契约要求 `base_score`，但 `phases/p3-root-cause.md`、`p4-fix-design.md` 调用 `arbiter` 时**全部未传 `base_score`**。
- `agents/shared-challenger-base.md` 输入契约要求 `confidence_input`，调用方同样**全部未传**。
- **影响**：`final_confidence = base_score × convergence_factor × challenge_survival_rate` 缺乏输入，arbiter 只能猜或临时构造，置信度计算不可重复。
- **修复**：phases 文件统一在 subagent_prompt 中显式拼接 `base_score = {上游 investigator final_score 列表}` 与 `confidence_input`，并在 arbiter wrapper 中校验。

#### C3. `challenger` 包装层的 dimension_set 枚举与基座不一致
- `agents/challenger.md` 仅枚举 `rca-5d / fix-4a`；`agents/shared-challenger-base.md` 多了 `deep-dive-7d`。
- Deep-Dive `f4-isolation-debate.md` 注入 `dimension_set = deep-dive-7d` 时，按 wrapper 校验"`scene` 与 `dimension_set` 一致性"会**判定为非法**。
- **修复**：要么把 `deep-dive-7d` 加入主 wrapper（更合理：让主 wrapper 也能透传 DEEP_DIVE 场景），要么由 `deep-dive-arbiter.md` 不再依赖主 wrapper。

#### C4. `coder-agent` 的输入 `defensive-fix-design.md` 触发条件枚举漂移
- `phases/p5-fix-impl.md` step 2 条件：`specialized_workflow.status ∈ {DD-Completed, Merged}`。
- 主 workflow-status-template / deep-dive workflow-status-template **均无 `Merged` 枚举**。Deep-Dive 子工作流仅产出 `DD-Completed / DD-LowConfidence / DD-Human-Review / DD-InProgress / DD-Intake`。
- `phases/p3-root-cause.md` step 7 写 `specialized_workflow.merge_strategy = merged-into-main-rca`、`specialized_workflow.status = DD-Completed`，**没有任何地方写 status = Merged**。
- **修复**：去掉 `Merged` 分支或在 P3 收尾处显式写入 `Merged`，并在两个状态模板里追加该枚举。

#### C5. `current_state = Context-Curating` 未在状态模板与编排器中建模
- `phases/p2-spec-definition.md` step 7 设置 `Context-Curating`，但 `workflow-status-template.yaml` 没有该枚举，`workflow.xml` step 4 也没有 case 匹配，会落入 default 分支造成阶段误转。
- `Curation-Failed` 同样没有在状态模板中预置。
- **修复**：在 `workflow-status-template.yaml` 增补合法枚举集合，并在 README/system-prompt.md 状态机图中补完。

#### C6. P3 升级 fan-out 后没有重置 stepsCompleted/重试无界保护缺失
- 与 B1 同源，但还存在二次问题：`p3-root-cause.md` `complex-arbitrated` 分支的"对抗轮次超过 3 轮仍未收敛"**没有计数器字段**（无 `arbitrate_round_count`），LLM 无法可靠判断。
- `core/workflow.xml` step 4 已有 `rca_retry_count > 2` 强制 Human-Review，但 `rca_retry_count` 只在升级时 +1，对"P3 内部 LLM 自身的对抗轮"无感知。
- **修复**：在 `workflow-status-template.yaml` 增加 `arbitrate_round_count`，由 P3 内显式回写。

#### C7. P5 中 `non-code-fix` 路径产物缺失
- `phases/p5-fix-impl.md` step 4 `non-code-fix` 分支只写"输出变更服务端配置或协调指令"为说明性 action，goto step 7 后才生成 `impl-report.md`，**真正的远端变更指令清单没有专属落盘文件**。
- 主 workflow.xml io-contract 仅声明 `impl-report.md` 必需，但与 PLATFORM-GUIDE.md "Coder Agent 适配 — Limited 平台：将契约溯源内联到 Phase 5" 不一致：`non-code-fix` 路径下契约溯源被设为 `SKIPPED`，但远端漂移本身应当有"远端配置变更证据/审计单"。
- **修复**：新增 `templates/remote-change-instruction.md`，作为 non-code-fix 的 mandatory 产物。

#### C8. 主工作流 vs system-prompt.md vs SKILL.md 三处状态机/字段定义不一致
- `system-prompt.md` 的 Phase 1 出现两个 `step n="5"`（"优先级评估"和"输出 Issue Card"重复编号）。
- 状态机图缺：`Context-Curating` / `Curation-Failed` / `Boundary-Refined` / `Fix-Implementing`（实际由 P5 写入）/ `Verifying`。
- PLATFORM-GUIDE.md "至少持久化字段"只列了 7 个，缺 `schema_version` / `non_bug_reflow_count` / `verification_failure_type` / `Issue_Boundary_Level` 等。
- **修复**：以 `core/workflow-status-template.yaml` 为权威源生成另两份文档的字段清单，CI 中加 schema 一致性测试。

#### C9. P6 验证失败回流时 `verification-report.md` 不生成 → 上游决策失锚
- `phases/p6-verification.md` step 6 失败分支直接 "阶段结束，返回编排器"，**未走 step 7 模板输出**。
- 但 `workflow.xml` `io-contract` 声明 `qa-verification` 必输出 `verification-report.md, knowledge-card.md`。
- **影响**：回到 P3/P4 后，下游无法引用本次失败的逐条证据；`fix_retry_count` 增加但用户/审计追溯困难。
- **修复**：失败分支也必须先 `template-output` 生成"中间态" verification-report（含失败分类与证据），再回流。

---

### 🟡 MAJOR（语义冲突 / 设计漏洞）

#### M1. `default-config.yaml` 与 SKILL.md 命名不一致
- SKILL.md 用 `{workspace_root}/{issue_id}/`，但 `default-config.yaml` 没有 `workspace_root` 键，只有 `workspace_name`、`workspace_folder`（在 deep-dive 里）。
- **修复**：统一命名为 `workspace_root`，并在 `default-config.yaml` 中显式列出该键（含示例 `qa-workspace`）。

#### M2. `workflow-status-template.yaml` 包含未使用字段
- `lint_retry_count`：实际工作流仅用 `fix_retry_count`，`core-rules.xml` 也只提到 `fix_retry_count`。
- `default-config.yaml` 中 `output_runtime_compat_report`、`output_reroute_trace` 全流程未引用。
- **修复**：删除冗余字段，或补完使用流程。

#### M3. `arbiter.md` / `challenger.md` 包装层缺 DEEP_DIVE 场景路由
- 主 wrapper 只覆盖 `RCA / FIX`，但 deep-dive arbiter 显式说"caller should load shared-arbiter-base"——意味着可以走 DEEP_DIVE，但主 wrapper 不感知 DEEP_DIVE 时如何映射 `selected` 命名（`final_root_cause` 还是 `recommended_fix_option`？）。
- **修复**：补 DEEP_DIVE → `selected = primary_root_cause`。

#### M4. `core-rules.xml` 中 `available-agents` 与 `agents/README.md` 列表口径冲突
- core-rules.xml 列表把 `context-reconstructor / state-analyst / temporal-analyst / 旧 challenger / 旧 arbiter` 都作为 deep-dive 可用 agent（虽标"已废弃"），但 `functionality-deep-dive/agents/README.md` 同样列废弃文件。这造成主编排器一旦从 core-rules.xml 派发任务到旧名字 SubAgent，会落到只有"Legacy Wrapper"内容的薄文件，**无法产出任何产物**（旧 arbiter.md/challenger.md 只是重定向说明）。
- **修复**：**移除主可用清单**中的旧名字（仅在 deep-dive/README 内部保留），并明确"旧名字仅作为 status 字段恢复参考，不可作为 invoke-subagent 目标"。

#### M5. `error-dump.md` 模板与 `coder-agent.md` 内嵌的同名模板**双份且不一致**
- `templates/error-dump.md` 缺少 coder-agent 内嵌模板中的 ✅/❌ 区分、"已应用变更/未回滚状态"细节。
- **修复**：删除一份；以 templates 目录为权威，coder-agent 仅引用文件路径。

#### M6. `defensive-fix-architect.md` 输出标题与 `templates/defensive-fix-design.md` 模板标题不一致
- agent 输出 `## Defensive Fix Addendum`，模板顶层 `## Defensive Fix Design — {Issue-ID}`。
- 字段集合也不完全对齐（agent 多 `Proportionality Review`，模板独立"竞态收敛措施"块在 agent 输出中无对应）。
- **修复**：以模板为准，agent 输出格式逐字段对齐。

#### M7. P3 调用 investigator 时 `{strategy_a}` `{strategy_b}` 占位无赋值机制
- `phases/p3-root-cause.md` `medium-challenge` / `complex-arbitrated` 分支的 prompt 含 `使用策略 {strategy_a}`，但 P3 上游或自身**没有从 `reference/analysis-strategies.md` 中选取并赋值的 action**。
- **修复**：P3 内补一个"策略选择 step"，依据 `主分类 + Issue_Boundary_Level + analysis_complexity` 从知识库选 1-2 个策略并写入 `workflow-status` 临时字段（如 `selected_strategy_pair`）。

#### M8. `investigator.md` 单视角时无 `challenge_survival_rate`，`final_confidence` 公式无法套用
- `agents/investigator.md` 输出 `SCORE` 表，但单 investigator 无 challenger，按 `shared-arbiter-base.md` 公式 `final_confidence = base_score × convergence × challenge_survival_rate` 在 simple-single 模式下没有定义。
- **修复**：在 `reasoning-chain.md` 与 shared-arbiter-base.md 都补一个**单视角降级公式**：`single_view_confidence = base_score × falsification_pass_ratio`（已通过反事实预测占比）。

#### M9. Deep-Dive 主→子工作流参数与状态隔离机制缺失
- `phases/p3-root-cause.md` step 6 `<load target="…/functionality-deep-dive/core/workflow.xml">` 调用——但这是同步阻塞调用还是异步？没有约定。
- `parent_issue_id` 在 deep-dive workflow-status-template.yaml 中定义，但**主 P3 调用时未在传参里赋值**，永远是 null，跨工作流追溯丢失。
- 子工作流 step-pause（DD-LowConfidence / DD-Human-Review）触发时主工作流如何感知？仅靠"`deep-dive-summary.md` 是否存在"判断 → 误判为"未触发深潜"。
- **修复**：明确同步语义；P3 step 6 显式注入 `parent_issue_id = {issue_id}`；增加"子工作流回信号"约定（例如 `specialized_workflow.handoff_status` 字段）。

#### M10. `templates/spec.md` 与 `templates/issue-card.md` 与 `workflow-status` 状态枚举漂移
- spec.md 模板 "Spec 状态: 确认 / Spec-Uncertain"，issue-card 模板"工作流状态: Spec-Defining / Info-Insufficient"——而 workflow-status 实际枚举更广，"确认"在状态机图中不存在。
- **修复**：模板字段值域改为引用 `workflow-status-template.yaml` 权威枚举，避免局部小词典。

#### M11. `templates/verification-report.md` 失败分类与 `phases/p6-verification.md` 不一致
- 模板写"未通过 → 回退到 Phase 4"；P6 实际有三类失败 → P3/P4。
- **修复**：模板补三类回流分类，与状态字段对齐。

#### M12. `intake-form.md` 与 `intake-form-blank.md` 用途未定义
- 两份采集表共存，p1-intake.md 仅引用 `intake-form.md`，blank 版从未被引用。
- **修复**：明确"blank 是给真人快速贴的极简版，full 是 Agent 内部清单"，并在 SKILL.md / system-prompt.md 入口处指明何时给用户哪一份。

#### M13. `templates/impl-report.md` "测试执行结果"表与实际能力不符
- 模板含"通过/失败/跳过"列，但 P5/coder-agent 仅做静态走查与 Lint，不真正执行测试。
- **修复**：把该表改为"测试用例覆盖度核对（不执行）"，避免误导。

#### M14. `templates/knowledge-card.md` 与 `verification-report.md` 双写 L3-Dynamic
- 两个产物都有 L3-Dynamic 字段，但 P6 完成时 verification-report 已写 [Pending-CI]，knowledge-card 又重复一次"待回填"——CI 回填到底回到哪个文件没明确。
- **修复**：knowledge-card 仅引用 verification-report 的 L3-Dynamic 区，不重复 schema。

#### M15. Reference 与流程的引用断层
- `reference/platform-checklist.md` "通用规则：跨层契约与资源引用溯源约束" 与 `agents/coder-agent.md` 阶段 1 内容**严重重复**（两处分别可被独立修改，已经存在版本漂移：coder-agent 多了 4 类校验细则）。
- **修复**：以 platform-checklist.md 为权威；coder-agent 仅 `<load>` 引用。

---

### 🟢 MINOR（可读性、维护性、冗余）

- **m1**：`install.sh` 与 `install_trae.sh` 95% 同源，仅 .cursor/.trae 不同。建议合并为 `install.sh --target=cursor|trae|both`。
- **m2**：`curator.md` 没有 YAML frontmatter，与同目录其他 agents 风格不统一。
- **m3**：`core-rules.xml` 列了 `<for-each>` 但全工作流从未使用，应当删掉或补使用示例。
- **m4**：`workflow_version` 字段值漂移：`abc-1` / `legacy` / `v3-legacy` / `v4-composite`，缺统一 SemVer 规范。
- **m5**：`functionality-deep-dive/FUNCTIONALITY_DEEP_DIVE_WORKFLOW_V3.md` 文件名是 V3，正文标题"V4 Workflow"——文件名/标题语义错位。
- **m6**：`functionality-deep-dive/agents/temporal-analyst.md` / `state-analyst.md` 等旧 agent 完整保留（200+ 行有效定义），但不再被任何 phase 调用，"旧会话恢复"机制本身没有 phase 入口可挂载，是空声明。
- **m7**：`core-rules.xml` `<supported-tags>` 中 `<template-output>` 仅列 `template`，未列 `file`，但所有 phases 都用了 `file` 参数。
- **m8**：`workflow.xml` step 4 的 `Non-Bug` case 内 `goto step="4"`（自循环）；改 Human-Review 后再 goto 自身只会再走一次 switch，应改为 `goto step="3"` 或终止。
- **m9**：`core/workflow.xml` step 3 调用 phases 时未将 `{issue_id}` / `{workflow_status}` 路径作为参数显式传递；phases 内部依赖 `{workspace_folder}/workflow-status.yaml` 的隐式约定，**没有在调用契约中固化**。
- **m10**：`agents/coder-agent.md` "工具权限/白名单" 列了 `Search/Grep`、`SearchReplace`，但 core-rules.xml 没有定义工具调用规范（与 Cursor 工具集无映射），跨平台移植时 LLM 不知如何对应。
- **m11**：rca-report.md "完整专项报告引用"块预设 4 个文件路径，若 `emit_*_report = false` 默认下文件不存在，会写出无效链接。
- **m12**：`phases/p2-spec-definition.md` 文件首部缩进 4 空格（包括 frontmatter），与其他 phases 顶格风格不一致，会让某些 YAML 解析器报错。
- **m13**：`templates/contract-checklist.md` 增加了"校验结论"块，但 `coder-agent.md` 中模板内嵌版本无此块，两份模板字段集不一致。
- **m14**：`PLATFORM-GUIDE.md` 提到"AutoGen / CrewAI" 集成，但仓库未提供 sample 桥接代码或 schema export，易过度承诺。

---

## 四、优化建议（按优先级排序）

### 立刻修复（本周）— Blocker / Critical

1. **路由模型重构**：把 `stepsCompleted` 改名为 `phase_history`（允许重复），新增 `latest_completed_phase`，并在 `core/workflow.xml` step 4 中明确"识别 reroute 时不追加 stepsCompleted"。同步更新 SKILL.md / system-prompt.md / PLATFORM-GUIDE.md。
2. **补全 P2 Non-Bug 完整闭环**：把 `system-prompt.md` 已写好的逻辑搬回 `phases/p2-spec-definition.md`；`workflow-status-template.yaml` 补 `non_bug_user_choice`。
3. **强制 Deep-Dive F1/F2/F3 落盘**：`functionality-deep-dive/core/default-config.yaml` 默认值翻为 true，与主配置 `deep_dive_optional_artifacts` 对齐；或者保留按需，但要求 F4 入参支持"内联报告内容"而非文件路径。
4. **声明 `<task>` 标签**：`core/core-rules.xml` `<supported-tags>` 增加 `<task>`，或两个 workflow.xml 改用 `<flow>`。
5. **共享基座契约 + 调用方传参对齐**：把 `base_score`、`confidence_input` 在所有 phases subagent_prompt 中显式拼接；并加一道 wrapper 校验"缺参时输出 `[Schema-Violation]`"。
6. **状态枚举单一权威源**：以 `workflow-status-template.yaml` 为权威，扩展 `Context-Curating / Curation-Failed / Boundary-Refined / Fix-Implementing / Verifying / Merged`，并删除/合并 `lint_retry_count` 等死字段。
7. **P6 失败分支也产出 verification-report.md**：作为"中间态"产物，包含失败分类与 reroute 元信息。

### 本月内（Major）— 契约和模板治理

8. 统一 `arbiter / challenger` wrapper 与共享基座的 scene/dimension_set 枚举（含 DEEP_DIVE / deep-dive-7d）。
9. P3 增设"策略选择 step"，把 `analysis-strategies.md` 中的策略池显式选取并写入 `selected_strategy_pair`。
10. 引入"子工作流回信号"字段：`specialized_workflow.handoff_status`（DD-Completed / DD-LowConfidence / DD-Human-Review / DD-Aborted），主工作流读取该字段而非"summary 文件是否存在"。
11. `defensive-fix-architect.md` 输出格式与 `templates/defensive-fix-design.md` 字段一对一对齐。
12. 删除 `agents/curator.md` 之外所有 agent 文件的格式异类（统一 frontmatter）。
13. `error-dump.md`、`contract-checklist.md` 等"双份模板"统一到 templates/ 目录，agent 文件只引用路径。
14. `intake-form.md` / `intake-form-blank.md` 标注用途与触发时机。
15. `verification-report.md` 模板补完三类回流分类。
16. `knowledge-card.md` 取消 L3-Dynamic 重复字段，仅引用。

### 中期演进（Minor + 工程化）

17. **schema 一致性 CI**：用 Python/Node 脚本扫描 `workflow-status-template.yaml` / `default-config.yaml` / phases / templates，检测字段命名漂移、枚举漂移，落地到 GitHub Action。
18. **install 脚本合并**：`install.sh --target` 参数化，DRY 原则。
19. **版本号统一为 SemVer**：`workflow_version: 4.0.0`、`schema_version: 3.1.0`，废弃 `abc-1` 等魔法值。
20. **Skills 镜像源同步**：`PLATFORM-GUIDE.md` 提到"`mobile-qa-workflow/` 是唯一权威源；Skill 镜像目录只应作为软链接入口"。建议在 install.sh 末尾加 `--check-drift` 选项，比对 `~/.cursor/skills/mobile-qa-workflow` 与项目源是否同源。
21. 移除 `core-rules.xml` 中已废弃 deep-dive 角色枚举，仅保留新角色；旧角色文件移入 `legacy/` 子目录；同时删除"旧会话恢复但无 phase 入口"的承诺。

---

## 五、优先级矩阵（影响 × 紧急度）

```
                影响：高                                     影响：低
紧急度：高    │ B1 路由互锁    B2 Non-Bug缺失   B3 落盘     │ M3 占位变量未赋值
              │ C1 task 标签   C2 共享基座契约  C5 枚举漂移  │ M5 模板双份
              │ C7 non-code-fix C9 验证失败缺产物            │ M11 模板回流分类
              │                                              │
紧急度：中    │ C3 dimension_set C4 Merged 枚举 C8 文档漂移  │ M9 子工作流隔离
              │ C6 计数器缺失                                │ M14 平台适配过度承诺
              │                                              │
紧急度：低    │ M1/M2 命名/字段  M4 wrapper 场景             │ m1-m14 所有 minor
              │ M15 reference 双源                           │
```

---

## 六、关键洞察

1. **设计意图 vs 实施落差最大的环节是"动态路由"**。`reroute_target_phase` + `fanout_mode` + `fix_strategy_mode` 三件套思路先进，但 `stepsCompleted` 单调追加的语义把整个动态路由的可重入性切断。
2. **共享基座 + 包装层**是优秀模式，但**没有任何静态校验**保证 wrapper 与 base 的 scene/dimension/枚举对齐——典型的 LLM Agent 工程"跨文件契约失守"。
3. **主工作流和 Deep-Dive 子工作流之间的 IPC 抽象不足**：以"文件存在与否"作为信号传递机制，对置信度低、暂停、人工介入这种**非二元状态**完全失声。
4. **system-prompt.md 实际比 SKILL.md + phases 组合更"完整"**（例如 P2 Non-Bug 处理）——意味着维护过程中**两套实现已经发生版本回归**，需要立即建立单一权威源 + 自动派生机制。
5. **Templates 字段在多处冗余**（L3-Dynamic、契约溯源、error-dump、defensive-fix-design），而工作流又依赖这些字段做下游决策——**字段漂移直接转化为 LLM 决策错乱**。

---

## 七、推荐落地动作清单

| # | 动作 | 工作量 | 立即收益 |
|---|---|---|---|
| 1 | 修补 B1 路由互锁（改造 stepsCompleted） | 0.5d | 解决 P3/P6 升级与回流失效的最大隐患 |
| 2 | 补全 P2 Non-Bug 路径 | 0.3d | 关闭 Non-Bug 闭环死循环风险 |
| 3 | Deep-Dive 默认产物落盘 | 0.2d | 修复 F4 输入丢失 |
| 4 | 状态枚举一表通（schema 单源） | 0.5d | 消除 4 处枚举漂移 |
| 5 | wrapper/base 契约校验 + base_score 注入 | 0.5d | final_confidence 可重复 |
| 6 | P6 失败分支必输出报告 | 0.2d | 闭环可审计 |
| 7 | 模板字段对齐 + 删除冗余 | 1d | 提高 LLM 输出质量 |
| 8 | install 脚本合并 + Schema CI | 0.5d | 防止后续漂移 |

**预计总工作量 3.7 人日**，建议作为本工作流的 **"v4.1 修订版"** 小迭代上线。

---

## 附录：审计方法与覆盖文件清单

### 审计方法
1. **结构遍历**：自顶向下对 `mobile-qa-workflow/` 全部目录逐层 `ls`，绘制依赖图。
2. **逐文件深读**：每份文件读取 → 提炼意图、I/O 契约、依赖项、状态变更副作用。
3. **横向交叉验证**：在 phases ↔ agents ↔ templates ↔ workflow-status 四象限中两两比对字段、枚举、回流路径。
4. **主工作流 vs 子工作流对比**：识别命名冲突、契约冲突、覆盖盲区。
5. **平台兼容性核查**：Full-capability vs Limited-capability 平台两条入口（SKILL.md / system-prompt.md）的实现对齐度。

### 覆盖文件清单
- 顶层：`SKILL.md`、`PLATFORM-GUIDE.md`、`system-prompt.md`、`install.sh`、`install_trae.sh`
- 核心：`core/core-rules.xml`、`core/workflow.xml`、`core/workflow-model.yaml`、`core/workflow-status-template.yaml`、`core/default-config.yaml`
- Agents：`agents/{curator,investigator,fix-proposer,coder-agent,arbiter,challenger,shared-arbiter-base,shared-challenger-base}.md`
- Phases：`phases/p1-intake.md` ~ `phases/p6-verification.md`
- Templates：`templates/` 下全部 14 份模板
- References：`reference/{analysis-strategies,fix-strategies,reasoning-chain,platform-checklist}.md`
- Deep-Dive：`functionality-deep-dive/` 全部 25+ 文件（含 core / agents / phases / templates / reference）

---

**报告完成** · 如需直接落地这些修复，可按"推荐落地动作清单"逐项创建 PR。
