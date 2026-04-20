# Mobile B2C 质量工作流 — 施工大纲 Review 报告（2026-04-20）

> 审阅对象：
> - `mobile-qa-workflow/QUALITY-AUDIT-REPORT-v1.2.1.md`
> - `mobile-qa-workflow/QUALITY-AUDIT-CONSTRUCTION-PLAN.md`（施工大纲，非详细施工清单）
>
> 审阅基线：以仓库当前源码为准（`mobile-qa-workflow/`）。
>
> 结论摘要：代码现状与审计报告的核心结论高度一致；施工大纲结构清晰但存在若干会导致落地偏航的关键冲突点，需要先拍板协议与范围口径。

---

## 结论概览

- 工程代码现状与 `QUALITY-AUDIT-REPORT-v1.2.1.md` 核心结论高度一致：B1*/B2/C10/C11/M16/B3 等“系统性协议缺失/字段污染/跨阶段 IPC 断链”在源码中都能直接复现与定位。
- `QUALITY-AUDIT-CONSTRUCTION-PLAN.md` 作为“施工大纲”结构是清晰的（PR 拆分、依赖拓扑、DoD/迁移/回滚骨架齐全），但目前存在数个会导致落地偏航的关键问题：
  - 范围与 Out-of-scope 自相矛盾
  - 把运行时变量当成状态 schema 字段（协议未定，容易两套语义并存）
  - step-pause 写回缺少可执行协议（仅有方向，缺落地机制）
  - tag 白名单治理边界未澄清（只修 `<task>` 可能不足）
  - Deep-Dive 产物落盘与主配置键名体系未对齐

---

## 工程代码现状（关键事实核验）

### B1* Phase 早退未结构化为 ABORT：属实且是主链路根因

- 编排器在执行阶段前初始化 `current_phase_result = CONTINUE`：
  - [workflow.xml](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/workflow.xml#L43-L46)
- 编排器仅在 `current_phase_result == ABORT` 时才“不会把 phase 追加到 stepsCompleted”：
  - [workflow.xml](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/workflow.xml#L89-L95)
- 但 P3 多处“阶段结束，返回编排器”没有设置 `current_phase_result = ABORT`：
  - [p3-root-cause.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/phases/p3-root-cause.md#L24-L31)
  - [p3-root-cause.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/phases/p3-root-cause.md#L53-L66)
- P6 失败回流同样“阶段结束，返回编排器”但不置 ABORT：
  - [p6-verification.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/phases/p6-verification.md#L63-L85)

### B2 P2 Non-Bug 闭环缺失：属实

- 编排器对 `Non-Bug` 分支期待 `non_bug_user_choice` 结果并驱动 Accept/Reflow：
  - [workflow.xml](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/workflow.xml#L118-L140)
- 但 P2 实际只做“非 Bug 类型枚举检查”，没有写 `current_state = Non-Bug`、没有 step-pause、也没有写回 `non_bug_user_choice`：
  - [p2-spec-definition.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/phases/p2-spec-definition.md#L46-L63)
- system-prompt 里反而有完整 Non-Bug step-pause 闭环，形成“入口能力回退”：
  - [system-prompt.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/system-prompt.md#L147-L190)

### C10 fanout_mode 跨阶段字段污染：属实且可直接定位

- P4 把 `fanout_mode` 写成 `fix_strategy_mode`：
  - [p4-fix-design.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/phases/p4-fix-design.md#L26-L38)
- P6 回流到 P3 时会强制覆盖 `fanout_mode = complex-arbitrated`（RCA 语义）：
  - [p6-verification.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/phases/p6-verification.md#L69-L75)
- 状态模板里 `fanout_mode` 与 `fix_strategy_mode` 并存，但缺少明确字段隔离策略：
  - [workflow-status-template.yaml](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/workflow-status-template.yaml#L20-L29)

### C11 step-pause 无写回协议：属实且存在“规范 vs 用法”不一致

- `core-rules.xml` 中 `<step-pause>` 只声明 `title/option` 参数，没有任何“结果写回字段/键”的协议：
  - [core-rules.xml](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/core-rules.xml#L97-L103)
- 但实际工作流大量使用 `<option ... action="...">`，并假设“下一轮可以读到用户选择结果”：
  - [workflow.xml](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/workflow.xml#L101-L170)

### M16 config_source 键漂移（output_curation_report）：属实

- P2 写入 `output_curation_report`：
  - [p2-spec-definition.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/phases/p2-spec-definition.md#L115-L121)
- 默认配置里没有该键：
  - [default-config.yaml](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/default-config.yaml#L9-L26)

### B3 Deep-Dive 默认不落盘导致 F4 可读输入缺失：属实

- Deep-Dive 默认 config 把 `emit_*_report` 全部设为 false：
  - [dd-default-config.yaml](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/functionality-deep-dive/core/default-config.yaml#L16-L18)
- F2 在 `emit_topology_report != true` 时明确“不强制独立落盘”：
  - [f2-state-topology.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/functionality-deep-dive/phases/f2-state-topology.md#L37-L46)
- F4 的输入是可选文件路径，默认情况下很容易为空：
  - [f4-isolation-debate.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/functionality-deep-dive/phases/f4-isolation-debate.md#L6-L24)

---

## 对 QUALITY-AUDIT-REPORT-v1.2.1.md 的 Review（报告质量）

### 强项

- “缺陷台账五字段 + 复现链路 + 兼容性方案”写法可直接转成工程任务，并且关键点能落到源码证据（上面核验项已覆盖主风险）。
- 对 C3 降级为 M17 的处理是正确的：Deep-Dive F4 调用链确实绕过主 wrapper，直接加载 shared base：
  - [f4-isolation-debate.md](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/functionality-deep-dive/phases/f4-isolation-debate.md#L40-L55)

### 建议补强（避免落地时产生误解）

- “tag 白名单”问题不止 `<task>`：当前 DSL 实际出现的顶层标签远多于此（`<io-contract>`、`<phase>`、`<llm>`、`<mandate>` 等）。建议在报告里明确：
  - 校验范围是否仅覆盖 `<flow>`/`<workflow>` 内部 DSL；
  - 或者要做全量严格校验（需要更大改动面）。
- 多处 Fix Sketch 假设存在“schema/CI 守门员”，但仓库当前主要是工作流 DSL 文档而非可执行编译系统；建议把“谁来校验、在哪个入口校验、失败如何 fail-fast”明确成统一前置假设。

---

## 对 QUALITY-AUDIT-CONSTRUCTION-PLAN.md 的 Review（大纲层面问题与改进）

### P0：范围与 Out-of-scope 存在硬冲突，需要先纠偏

- §1.2 写 M16 out-of-scope，但 PR-1/PR-8 又把 config-schema/CI（典型 M16 治理）纳入；这会导致评审时无法用“范围守门”裁决。
- §1.2 声称“本次仅做 9 条”，但 §1.1 表格又加了 PR-6/7/8（模板治理/入口对齐/install+CI），已经超出“9 条 Blocker/Critical”的直觉定义，需要先统一口径：
  - “9 条”是“缺陷条目数”（B1*/B2/B3/C1/C2/C5/C9/C10/C11）；
  - 还是“施工工作包数/PR 数”。

### P0：把运行时变量当成 workflow-status schema 字段，存在设计偏差

- 代码里 `current_phase_result` 是编排器在当次执行初始化的运行时变量：
  - [workflow.xml](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/workflow.xml#L43-L46)
- 施工大纲 PR-1 计划把 `current_phase_result` 写进 `workflow-status-template.yaml`，但如果不同时修改编排器从状态文件读取/写入它，这个字段只会增加歧义而不改变行为。
- 更稳的两条路线（建议二选一，避免“两套语义”并存）：
  - 方案 A：保持 `current_phase_result` 为运行时变量。所有 phase 早退点在退出前显式 `设置 current_phase_result = ABORT`，状态文件不引入该字段。
  - 方案 B：改为状态字段协议。编排器 step 4 判断改为读 `workflow_status.current_phase_result`，并定义清晰的写回时机（进入 phase 前置 CONTINUE，早退置 ABORT，成功保持 CONTINUE）。

### P0：step-pause 写回（C11）在大纲里缺少“可执行协议”

- 方向正确（引入 `result_field`），但缺少关键定义：用户下一次输入如何结构化为可解析值；否则“由编排器统一写回”仍只能靠 LLM 猜测。
- 建议在大纲层面定死一种输入协议（示例）：
  - 用户回复必须包含 `result_field=<OptionKey>`（如 `non_bug_user_choice=Accept`）；
  - 编排器只接受白名单值并写回到状态文件（可审计、可回放）。

### P1：C1 tag 白名单修复建议过窄，需明确治理边界

- 大纲 PR-1 只写“supported-tags 增 `<task>`”，但当前 DSL 实际出现的顶层标签更多。如果目标是严格校验，需要一次性明确校验范围；如果目标是最小修复消除已知报错，也应写清楚只校验 `<flow>` 内部。

### P1：Deep-Dive 落盘（B3）需要“键名体系对齐”，不只是翻默认值

- 主 `default-config.yaml` 使用 `deep_dive_optional_artifacts.*`：
  - [default-config.yaml](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/core/default-config.yaml#L37-L41)
- Deep-Dive 子工作流使用 `emit_*` 布尔开关：
  - [dd-default-config.yaml](file:///Users/bytedance/Code/loupe/mobile-qa-workflow/functionality-deep-dive/core/default-config.yaml#L16-L18)
- 仅翻 deep-dive 默认值为 true 能缓解，但仍缺主配置驱动子配置的映射（否则两套开关长期漂移）。

### P1：PR 拆分与依赖拓扑总体合理，但 DoD/迁移/回滚的落点需要再收敛

- 大纲里 DoD、迁移脚本接口、回滚策略骨架是高价值部分。
- 建议在每个 PR 段落明确“哪些改动属于协议层（core-rules/workflow.xml）必须先合并、哪些属于文档同步可以后置”，避免 PR-7 文档对齐反复 rebase 消耗评审。

---

## 建议的下一步最小决策（让大纲可进入逐 PR 施工）

- 明确 v4.1 的范围口径：是“只做九条缺陷”，还是“九条缺陷 + 为防回归所必需的最小 CI/install/文档同步”。
- 在大纲里拍板两个协议：
  - `phase_result`：运行时变量 vs 状态字段
  - `step-pause`：用户回复的结构化格式与写回规则
- 明确 tag 校验边界：只校验 `<flow>` 内 DSL，还是全量标签都要进白名单；按此决定 C1 的实际改动面与风险。

