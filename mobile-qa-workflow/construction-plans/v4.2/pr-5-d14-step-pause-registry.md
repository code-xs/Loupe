# PR-5 · D14 收口 #2：step-pause registry 数据化（O10+ + O22）（v4.2 详细施工单 / **v1.1 当前生效版**）

> **主控文档**：[`./README.md`](./README.md)（§6 PR-5 / §3 H3+H4 / §4 CI 守门表 / §5 跨平台矩阵）
> **方案文档**：[`../../../doc/MOBILE_QA_WORKFLOW_STATE_SYNC_OPTIMIZATION_V1.1_2026-04-21.md`](../../../doc/MOBILE_QA_WORKFLOW_STATE_SYNC_OPTIMIZATION_V1.1_2026-04-21.md) §3.2.10+（Stage-1 + Stage-2 + Registry 权威性约束） / §3.2.22（`check-step-pause-registry.sh` 三类校验加严） / §4.1 B3 严格串行
> **关联 ADR**：[`doc/adr/010-step-pause-registry-data-driven.md`](../../../doc/adr/010-step-pause-registry-data-driven.md)（PR-1 已落地草稿，本 PR finalize 为 `active`）+ [`doc/adr/016-step-pause-required-params.md`](../../../doc/adr/016-step-pause-required-params.md)（**v1.1 修订**：本 PR 追加 v4.2 修订段，声明 `<step-pause>` 两种互斥形态）+ [`doc/adr/008-step-pause-userinputs-namespace.md`](../../../doc/adr/008-step-pause-userinputs-namespace.md)（user_inputs 命名空间）+ [`doc/adr/015-userinputs-mirror-allowlist.md`](../../../doc/adr/015-userinputs-mirror-allowlist.md)（双写白名单 → registry `mirror_to_top` 数据化）+ [`doc/adr/018-parse-error-circuit-breaker.md`](../../../doc/adr/018-parse-error-circuit-breaker.md)（parse_error_count 熔断协议）+ [`doc/adr/019-legacy-step-pause-allowlist.md`](../../../doc/adr/019-legacy-step-pause-allowlist.md)（PR-6 删 phase 内联依赖本 PR registry 就绪）
> **关联 V1.1 项**：**O10+**（Stage-1 抽出注册表 + Stage-2 编排器 step 4 拆 4a/4b/4c）+ **O22**（`check-step-pause-registry.sh`，三类校验 / **error 起步**）+ Registry 权威性强约束（H3）
> **历史版本**：[`./pr-5-d14-step-pause-registry-REVIEW-2026-04-21.md`](./pr-5-d14-step-pause-registry-REVIEW-2026-04-21.md)（v1.0 review 报告 / 2 High + 2 Medium）。本文 v1.0 主体在原文件内已被本次 v1.1 修订**就地覆盖**（无独立 v1.0 快照文件）；v1.0 → v1.1 量化对比详见 §0。
> **状态**：📐 已展开（v1.1，2026-04-21；review 整体修订后）
>
> **唯一职责（单段施工 / 不可拆 commit）**：
> - **核心数据化**：新建 `core/step-pause-registry.yaml`（REG-N1），把 v4.1 编排器 step 4 内 6 个交互态 case（`Info-Insufficient` / `Spec-Uncertain` / `Non-Bug` / `RCA-LowConfidence` / `Curation-Failed` / `Human-Review`）的 `step-pause` 配置 + `on_success` 路由表 100% 数据化；**v1.1 修订**：同时把 `Boundary-Refined` 作为 `kind: route` 纯路由项纳入 registry（review Finding 1 收口 / Patch A）
> - **编排器重构**：`core/workflow.xml` step 4 拆为 **4a（解析）/ 4b（阶段完成态）/ 4c（路由查表）** 三段；所有路由态 case 全部退化为通用模板，硬编码 `<switch>` / `<case>` 全部移除（H3 强约束）
> - **协议层声明**：`core/core-rules.xml` `<step-pause>` 标签 schema 重构为 `<forms>` 互斥两形态（**v1.1 修订**：v1.0 仅"追加 registry-key 必填"会与 ADR-016 旧三必填冲突 / Patch B）；同步 ADR-016 追加 v4.2 修订段；同步 `check-io-contract.sh` 加互斥校验
> - **CI 守门**：新建 `mobile-qa-workflow/scripts/check-step-pause-registry.sh`（SCRIPT-N1），三类校验 + **error 起步**；**v1.1 修订**：第 ② 类「全覆盖」升级为「双向严格相等」，分类报错 missing / unexpected（review Finding 3 收口 / Patch C）
> - **ADR finalize**：`doc/adr/010-step-pause-registry-data-driven.md` 状态 `draft → active`（ADR-D1）+ 追加「PR-5 落地纪要」+ ADR 索引同步（ADR-IDX1）
> - **CI 集成**：`.github/workflows/qa-workflow-schema-check.yml` 追加 Check（CI-N1）
>
> **不在本 PR 范围**（H3 边界）：
> ① **O13 / O14**：phase 文件内联 `<step-pause>` 删除 + `Fix-Confirming` enum 引入 + `legacy-phase-step-pause-allowlist.txt` 删除 → **PR-6**（依赖本 PR registry 就绪 + PR-3' 宏可用）
> ② **O17+ system-prompt 首次构建**：把 registry 注入分层 L1 → **PR-6**（H1 触发首次构建）
> ③ **O15** P3 三档升级路径合并 / **O11+** agents 模块化 → PR-7
> ④ **`mirror_to_top` 字段最终瘦身**：`workflow-status-template.yaml` 顶层 `non_bug_user_choice` 字段删除 → **v4.2 收尾遗留 #3**（待 PR-6 编排器 4c 改读 `user_inputs.<key>` 后才能删，本 PR 仅在 registry 中数据化标记 `mirror_to_top: true` 维持双写）
> ⑤ **新增 stop_state 真实业务态**：本 PR 仅给出 demo 验证步骤（**v1.1 修订** DEMO-V1：本地验证脚本 / 不入 commit / 含完整临时步骤与回退动作 / review Finding 4 收口 / Patch D），不引入新的业务交互态

---

## 0. v1.0 → v1.1 修订摘要（按 review 4 项 Patch 块组织）

> 本节是 v1.1 相对 v1.0 的**结构性变化总览**，便于 reviewer 快速定位增量；具体改动文本见对应章节。**v1.0 主体骨架完全保留**，本次仅做"协议自洽 + 路由完整性 + CI 严格性 + 验收可执行性"四类改动，**未引入新的 V1.1 项**。

| Patch 块 | 触发 review 项 | 改动章节 | 改动性质 |
|---|---|---|---|
| **A — 路由完整性修订** | Finding 1（High） | §2.1 REG-N1（registry schema 加 `kind` 字段 + `Boundary-Refined` 纯路由项 / **REG-N1.7**）/ §2.3 XML-D1（4c 按 `kind` 派发：`route` 走 `on_route`，`step-pause` 走既有流程）/ §3.1 D1（"严格相等"6 项 → **7 项**含 Boundary-Refined）/ §A 附录字面对照表新增 1 行 | 状态机回归修复：v1.0 把 `Boundary-Refined` 误归默认流转，会导致 P3 自循环（`current_state` 不再被改写为 `RCA-Designing`）；v1.1 把它纳入 registry 作为「纯路由态」，与 6 个交互态共用同一权威源 |
| **B — `<step-pause>` 互斥形态契约** | Finding 2（High） | §1 顶部「关联 ADR」+「涉及文件」/ §2.2 TAG-D1（重写为 `<forms>` 互斥块）/ 新增 §2.5.bis ADR-016 v4.2 修订段（**ADR-D2**）/ 新增 §2.6.bis `check-io-contract.sh` 互斥校验补丁（**CI-D1**） | 协议层自洽：v1.0 仅"追加 `registry-key` required"会与 ADR-016 已有三必填（`title` / `result_field` / `allowed_values`）天然冲突，且与"旧写法继续兼容"语句矛盾；v1.1 明确两种互斥形态（inline / registry），同步 ADR-016 + check-io-contract.sh |
| **C — Check 16 第 ② 类双向严格相等** | Finding 3（Medium） | §2.4 SCRIPT-N1（第 ② 类骨架重写为双向 diff，分类报 `missing` / `unexpected`）/ §3.1 D1（保持"严格相等"文案，与脚本对齐） | DoD 假绿封堵：v1.0 第 ② 类仅 `EXPECTED ⊆ REG_STATES`，registry 多出未消费项时仍绿；v1.1 用 `comm -23 / -13` 双向 diff 兜底「权威性强约束」（H3）|
| **D — DEMO-V1 重定义** | Finding 4（Medium） | §3.2 B6 行（重写为「本地验证脚本 / 不入 commit / 7 步完整流程含 enum 临时扩展 + phase 临时改写 + 强制回退」）/ §6.1 reviewer 关注点同步 | 验收可执行性：v1.0 demo 与 enum 守门 + 文件冻结边界三方矛盾；v1.1 通过「dev/demo-v1-local 临时分支 + 演示后 hard reset」让 demo 在不破坏边界约束的前提下可复现 |

**v1.0 → v1.1 量化对比**：
- 总章节结构不变（§1 ~ §7 + 附录 §A）
- 变更点编号约定不变（REG/TAG/XML/SCRIPT/ADR/CI/IDX 前缀）
- 总变更点数：12 → **14**（registry 多 1 项 `Boundary-Refined` 计入 REG-N1.7 / `core-rules.xml` 重写不变 / 新增 ADR-016 v4.2 修订段 = `ADR-D2` / 新增 `check-io-contract.sh` 互斥校验补丁 = `CI-D1`；其余 10 个变更点编号不变）
- 工作量：0.6d → **0.7d**（+0.1d 吸收在原"跨平台抽查 0.1d"buffer 内可消化，关键路径 7.2d 不变）
- 涉及文件：6 → **8**（新增 `doc/adr/016-step-pause-required-params.md` 修改 + `mobile-qa-workflow/scripts/check-io-contract.sh` 修改）

---

## 1. PR 元信息

| 项 | 值 |
|---|---|
| 分支命名 | `feat/qa-workflow-v4.2-pr5-step-pause-registry` |
| Base | PR-3'（PR-3 + PR-4 合并版）合入后的 `main` |
| 层级 | 🟡 **协议级 + 编排器结构性重构**：① 引入新协议 `<step-pause registry-key="...">`（中风险，依赖 LLM 按 ADR-010 §0 展开规则查表）② 编排器 step 4 从 ~270 行 6 case switch 收敛到 ~70 行通用模板 ③ **零用户可见行为变化**——所有弹窗 `title` / `allowed_values` / `option` 文本与 PR-3' 完全一致（registry 把硬编码字面 1:1 数据化） |
| 目标合入顺序 | PR-1 → PR-2 → PR-3' → **PR-5** → PR-6 → PR-7（**严守 H3**：禁止与 PR-3' 或 PR-6 合并） |
| Reviewer | **方案 owner**（必看：① registry 6 个交互态项 + **1 个路由态项 Boundary-Refined**（v1.1 修订）与 PR-3' 后 `core/workflow.xml` step 4 case 字面 1:1 等价 ② step 4a/4b/4c 三段覆盖 v4.1 step 4 全部行为，含 4c 按 `kind` 派发 `route` / `step-pause` 两种形态 ③ `mirror_to_top` 仅 Non-Bug 为 true ④ Non-Bug `Reflow check` 与 P2 写入端一致 ⑤ **`<step-pause>` 互斥两形态契约（inline / registry）在 `core-rules.xml` 与 ADR-016 v4.2 修订段表述一致**（v1.1 修订）+ **平台 owner**（必看：① CI Check 16 主干零 error，含第 ② 类双向 diff 验证 ② Cursor + Dify 双侧 4 个交互态弹窗截图一致 ③ Limited 平台 LLM `registry-key` 查表 ≥ 5 例 0 漏展开 ④ **DEMO-V1 在 `dev/demo-v1-local` 临时分支验证后 hard reset，最终 PR diff 干净**（v1.1 修订）⑤ **`check-io-contract.sh` 互斥校验补丁在干净主干输出零 error**（v1.1 修订）） |
| 关联 V1.1 项 | O10+ Stage-1+2（含 Registry 权威性约束） + O22(`check-step-pause-registry.sh`，**error 起步**) + ADR-010 finalize + **ADR-016 v4.2 修订段**（v1.1 修订） |
| **工作量** | **0.7d**（v1.1 修订；v1.0 = 0.6d，+0.1d 吸收在原"跨平台抽查"buffer 内可消化；拆分：REG-N1 字面迁移 + Boundary-Refined 路由态 ≈ 0.15d / XML-D1 step 4 重构（含 4c kind 派发） ≈ 0.2d / SCRIPT-N1 三类校验（含双向 diff） ≈ 0.15d / TAG-D1 重写 + ADR-016 v4.2 修订段 + check-io-contract.sh 互斥校验补丁 ≈ 0.1d / ADR-010 finalize + CI 集成 + 跨平台抽查 + DEMO-V1 ≈ 0.1d） |
| 涉及文件 | **新增**：`core/step-pause-registry.yaml`（REG-N1）+ `scripts/check-step-pause-registry.sh`（SCRIPT-N1）。**修改**：`core/workflow.xml`（XML-D1，step 4 全段重写）+ `core/core-rules.xml`（TAG-D1，**v1.1 修订**：重构为 `<forms>` 互斥两形态）+ `doc/adr/010-step-pause-registry-data-driven.md`（ADR-D1，`draft → active` + 落地纪要）+ **`doc/adr/016-step-pause-required-params.md`**（ADR-D2，**v1.1 修订**：追加 v4.2 修订段，声明两形态互斥契约）+ `doc/adr/000-index.md`（ADR-IDX1）+ **`mobile-qa-workflow/scripts/check-io-contract.sh`**（CI-D1，**v1.1 修订**：追加 `<step-pause>` 互斥校验段）+ `.github/workflows/qa-workflow-schema-check.yml`（CI-N1）。**禁止修改**：`core/workflow-status-template.yaml`（遗留 #3 留 PR-6 后清理）/ 6 phase 文件 / `system-prompt.md`（H1 留 PR-6）/ `legacy-phase-step-pause-allowlist.txt`（O14 留 PR-6）。 |

---

## 2. 文件级 diff 列表

> 本 PR 共 **6 类变更点 14 个**（v1.1 修订：原 12 → 14；新增 REG-N1.7 / ADR-D2 / CI-D1，TAG-D1 重写口径），按"先数据化（registry）→ 协议层（schema）→ 编排器重写 → CI 守门 → ADR finalize → CI 集成"顺序：
>
> | 编号前缀 | 含义 | 数量（v1.1） | 完整字面位置 |
> |---|---|---|---|
> | **REG-N1** | 新建 `core/step-pause-registry.yaml`（6 个交互态 + **1 个路由态 Boundary-Refined**（v1.1 / Patch A）+ 顶部权威性约束注释块）| 1（含 7 项条目） | §2.1（完整字面，~95 行 yaml） |
> | **TAG-D1** | `core-rules.xml` `<step-pause>` 标签 schema **重构为 `<forms>` 互斥两形态**（v1.1 修订 / Patch B；v1.0 仅"追加 registry-key 必填"已废弃）| 1 | §2.2 |
> | **XML-D1** | `core/workflow.xml` step 4 整段重写为 4a/4b/4c 三段；4c 按 `kind` 派发（v1.1 修订）（删 ~270 行 / 增 ~80 行 / 净瘦身 ~190 行）| 1 | §2.3（完整字面，~80 行 xml） |
> | **SCRIPT-N1** | 新建 `scripts/check-step-pause-registry.sh`（三类校验 + python 提取 + error 起步；**v1.1 修订**：第 ② 类双向 diff / Patch C）| 1 | §2.4 |
> | **ADR-D1 + ADR-D2 + ADR-IDX1** | ADR-010 `draft → active` + 落地纪要（ADR-D1）+ **ADR-016 追加 v4.2 修订段**（ADR-D2 / v1.1 / Patch B）+ index 同步（ADR-IDX1）| 3 | §2.5（ADR-D1）+ §2.5.bis（ADR-D2）|
> | **CI-N1 + CI-D1** | workflow yml 追加 Check 16（CI-N1）+ **`check-io-contract.sh` 追加 `<step-pause>` 互斥校验段**（CI-D1 / v1.1 / Patch B）| 2 | §2.6（CI-N1）+ §2.6.bis（CI-D1） |
>
> **变更点编号约定**：N\* = 新建 / D\* = diff 改写 / IDX\* = ADR 索引同步。所有变更同 commit 提交（O10+ Stage-1 + Stage-2 物理上不可分——CI Check 16 第 ③ 类「硬编码 case 禁出」校验在 Stage-1 单独 push 时必红）。

---

### 2.1 文件 A · `mobile-qa-workflow/core/step-pause-registry.yaml`（REG-N1，新建）

**操作**：新建文件。文件结构 = **顶部权威性约束注释块（C5 单一权威源 / H3 引用）** + `registry:` 顶层数组（**v1.1 修订**：7 项 = 6 个交互态 `kind: step-pause` + 1 个路由态 `kind: route` `Boundary-Refined`，按 v4.1 编排器 step 4 case 出现顺序排列；REG-N1.7 = `Boundary-Refined` 路由项 / Patch A）。

**新文（完整字面）**：

```yaml
# Mobile QA Workflow · step-pause 注册表（C5 单一权威源 / v4.2 PR-5 / O10+）
# ⚠️ CRITICAL: 编排器 core/workflow.xml step 4a / 4c 查表的唯一数据源；
# 编排器内严格禁止硬编码 <switch case="<交互态>">（CI check-step-pause-registry.sh
# 第 ③ 类 error 兜底；详见 ADR-010 §2 + V1.1 §3.2.10+ 末尾）。
#
# Schema（v4.2 PR-5 v1.1 / Patch A）：
#   state(必填，∈enum) / kind("step-pause"|"route"，默认 "step-pause")
# kind == "step-pause"（6 个交互态）：
#   title_template / result_field / allowed_values / options[{title, action}]
#   / on_success(map[str → action_block]) / mirror_to_top(可选 bool，D15 双写标记，
#     v4.2 PR-5 起仅 Non-Bug；遗留 #3 删除后下线)。
# kind == "route"（1 个纯路由态 Boundary-Refined）：
#   on_route(action_block) — 编排器 4c 命中时直接执行，不发起 step-pause、不等用户回复。
# action_block 原子动作（详见 ADR-010 §0 展开规则）：
#   set_state(str，∈enum) / write(map，key ∈顶层字段) / increment(str，同上)
#   / goto("step_2"|"step_4") / terminal(true) / interpret_freetext(true，仅 Human-Review)
#   / check(str，"field <op> literal" + true/false 子块)

registry:
  - state: Info-Insufficient
    title_template: |
      信息不足，需要用户补充以下缺失项：
      {missing_items}
    result_field: info_insufficient_action
    allowed_values: [Submit]
    options:
      - title: "[S] Submit：补充信息后继续，回流 qa-intake"
        action: "info_insufficient_action=Submit"
    on_success:
      Submit:
        set_state: Intake
        goto: step_2

  - state: Spec-Uncertain   # PR-3' / O13a 已统一契约为 1|2|S 三选
    title_template: |
      Spec 存在歧义，请确认 Expected Behavior：
      {spec_options}
    result_field: spec_uncertain_choice
    allowed_values: ["1", "2", "S"]
    options:
      - title: "[1] {option_1}（采纳第 1 种 Expected Behavior 继续）"
        action: "spec_uncertain_choice=1"
      - title: "[2] {option_2}（采纳第 2 种 Expected Behavior 继续）"
        action: "spec_uncertain_choice=2"
      - title: "[S] Skip：先并行分析所有可能，后续确认"
        action: "spec_uncertain_choice=S"
    on_success:
      "1":
        set_state: Spec-Defining
        write: { selected_spec_index: 1 }
        goto: step_2
      "2":
        set_state: Spec-Defining
        write: { selected_spec_index: 2 }
        goto: step_2
      "S":
        set_state: Spec-Defining
        write: { selected_spec_index: parallel }
        goto: step_2

  - state: Non-Bug
    title_template: |
      Non-Bug 判定结果，请确认处理方向：

      {non_bug_context}
    result_field: non_bug_user_choice
    allowed_values: [Accept, Reflow]
    mirror_to_top: true   # D15 双写数据化（v4.2 PR-5 起步白名单：仅本项；遗留 #3 删除后本标记一并下线）
    options:
      - title: "[A] Accept：接受 Non-Bug 判定，关闭 issue"
        action: "non_bug_user_choice=Accept"
      - title: "[R] Reflow：补充证据后重新进入 Spec-Defining 重审"
        action: "non_bug_user_choice=Reflow"
    on_success:
      Accept:
        set_state: Done
        terminal: true
      Reflow:
        check: "non_bug_reflow_count < 2"
        true:
          set_state: Spec-Defining
          increment: non_bug_reflow_count
          goto: step_2
        false:
          set_state: Human-Review

  - state: RCA-LowConfidence
    title_template: |
      根因分析置信度不足（< 0.5），建议处理方向：{suggestion}
    result_field: rca_lowconf_action
    allowed_values: [Retry, Human]
    options:
      - title: "[R] Retry：补充上下文后重新分析（回流 qa-spec-definition）"
        action: "rca_lowconf_action=Retry"
      - title: "[H] Human：转人工处理"
        action: "rca_lowconf_action=Human"
    on_success:
      Retry:
        set_state: Spec-Defining
        goto: step_2
      Human:
        set_state: Human-Review

  - state: Curation-Failed
    title_template: |
      上下文策展失败（置信度 < 0.4），请补充信息或转人工
    result_field: curation_failed_action
    allowed_values: [Retry, Human]
    options:
      - title: "[R] Retry：补充信息后重新策展（回流 qa-spec-definition）"
        action: "curation_failed_action=Retry"
      - title: "[H] Human：转人工处理"
        action: "curation_failed_action=Human"
    on_success:
      Retry:
        set_state: Spec-Defining
        goto: step_2
      Human:
        set_state: Human-Review

  - state: Human-Review
    title_template: |
      ⚠️ 需要人工介入，请处理后告知继续方向
    result_field: human_review_continue
    allowed_values: [Continue]
    options:
      - title: "[C] Continue：人工处理完成，继续工作流"
        action: "human_review_continue=Continue"
    on_success:
      Continue:
        interpret_freetext: true   # 编排器 4c 由 LLM 解释回复正文，更新 current_state / 计数器
        goto: step_2

  # ── REG-N1.7（v1.1 / Patch A / review Finding 1 收口）─────────────────────────
  # Boundary-Refined 是 P3 写入的"纯路由态"（phases/p3-root-cause.md L62），
  # v4.1 编排器在 step 4 内显式 set_state = RCA-Designing 后回 step 2。
  # v1.0 误归默认流转会让 current_state 留在 Boundary-Refined 导致 P3 自循环；
  # v1.1 把它纳入 registry 作为 kind: route 项，与 6 个交互态共用同一权威源。
  - state: Boundary-Refined
    kind: route
    on_route:
      set_state: RCA-Designing
      goto: step_2
```

**字面等价性保证**：① 6 个 `kind: step-pause` 项的 `title_template` / `result_field` / `allowed_values` / `options[].title` / `options[].action` 与 PR-3' 合入后 `core/workflow.xml` step 4 内对应 case 完全 1:1；② **REG-N1.7（v1.1 / Patch A）**：`Boundary-Refined` 路由项的 `set_state = RCA-Designing` + `goto step_2` 与 v4.1 `core/workflow.xml:333-336` 逐行等价。CI Check 16 第 ① + ② 类自动兜底；任何字面差异 = registry 与编排器不一致 = CI 红。

**修订理由（V1.1 §3.2.10+ Stage-1 / ADR-010 §2 / v1.1 Patch A）**：① 把 6 case ~150 行硬编码 `switch` + 1 个 case `Boundary-Refined` 路由分支收敛到本注册表；② `mirror_to_top` 数据化承接 D15 双写白名单（O12 简化效果），未来删除时只删本字段一行 + 编排器 4a 一段；③ schema 内 `on_success` / `on_route` 原子动作集 = 「set_state / write / increment / goto / terminal / interpret_freetext / check」7 种，覆盖 v4.1 step 4 内全部行为（含 Boundary-Refined 的 set_state + goto 路由副作用，v1.1 修订纳入）；④ **`kind` 字段（v1.1）**：默认 `step-pause` 保证 6 个交互态 yaml 体例不变，仅在 `Boundary-Refined` 显式标 `route`；编排器 4c 按 `kind` 派发，禁止跨形态混用 `on_success` 与 `on_route`。

**兼容性影响**：① 本文件**新建**，老会话（v3 / v4 schema）继续兼容（编排器 4a/4c 按 registry 查表，老会话 `current_state` 命中后行为 1:1 等价，含 `Boundary-Refined → RCA-Designing` 改态）；② Limited 平台 system-prompt 中暂未注入 registry，本 PR 范围内 Limited 平台仍按 PR-3' 后 sp 既有 step-pause 字面执行（**反向收益**——sp 内字面与 registry 字面同源，PR-6 首次构建后自动一致）。

---

### 2.2 文件 B · `mobile-qa-workflow/core/core-rules.xml`（TAG-D1，**v1.1 重写 / Patch B / review Finding 2 收口**）

**v1.0 → v1.1 变化**：v1.0 仅"在 `<params>` 追加 `<param name="registry-key" required="true">`"，与 ADR-016 已有的 `title` / `result_field` / `allowed_values` 三必填**天然冲突**——`<step-pause registry-key="${current_state}"/>` 同时缺三个旧必填且多一个新必填，CI `check-io-contract.sh` 必报错；同时与原文档"旧写法继续兼容"语句逻辑互斥。v1.1 把 `<step-pause>` 重构为 `<forms>` **互斥两形态契约**。

**操作**：在 `core/core-rules.xml` 现有 `<tag name="step-pause">` 块（L108 起）内做以下结构化改写——`<rules>` 段保留前 4 个 `<rule>`（含 `step-pause-scope` critical rule 不动）；`<params>` 段整段替换为 `<forms>` 块；`<input-protocol>` 段保留不动（5 条 rule 与两种形态均正交）。

**新文（关键字面，新 `<forms>` 块替换原 `<params>` 段）**：

```xml
<tag name="step-pause">
    <rules>
        <!-- 前 4 个 rule 保留不动（含 step-pause-scope critical rule）-->
        ...
        <rule>v4.2 PR-5 起 &lt;step-pause&gt; 必须命中且仅命中以下两种互斥形态之一
              （由 scripts/check-io-contract.sh 互斥校验段强制 / 详见 ADR-016 v4.2 修订段）。</rule>
    </rules>
    <forms>
        <!-- Inline 形态（v4.1 老写法 / PR-6 删除 phase 内联前过渡保留 / 仅 phase 文件残留例外） -->
        <form name="inline">
            <required>title, result_field, allowed_values</required>
            <optional cardinality="0..*">option</optional>
            <forbidden>registry-key</forbidden>
            <expand>LLM 按 input-protocol rule n=1 输出强结构 [result_field=...][allowed_values=...]
                    并附"请用 &lt;key&gt;=&lt;value&gt; 回复"末尾行；编排器 4a 按 result_field 解析。</expand>
        </form>
        <!-- Registry 形态（v4.2 PR-5 起 / 编排器 4c 唯一形态） -->
        <form name="registry">
            <required>registry-key</required>
            <forbidden>title, result_field, allowed_values, option</forbidden>
            <expand>LLM 按 ADR-010 §0 展开规则查 core/step-pause-registry.yaml，
                    把 registry-key 命中项的 title_template / result_field / allowed_values / options
                    渲染为等价 inline 形态再按 input-protocol rule n=1 输出。</expand>
        </form>
        <mutex critical="true">两 form 必须命中且仅命中其中之一；同时含 registry-key 与 title
                              / 同时缺两组关键字段，均判定为协议违规（check-io-contract.sh 互斥校验段 error）。</mutex>
    </forms>
    <params>
        <!-- 旧 4 个 param 描述按原字面保留（title / result_field / allowed_values / option），
             仅在每个 param 顶部追加一行 "属于 form=inline" 标记；
             新增 1 个 param 描述 registry-key（属于 form=registry）。 -->
        <param name="title" required="form:inline">...（保留原 v1.0 字面）</param>
        <param name="result_field" required="form:inline">...（保留原 v1.0 字面）</param>
        <param name="allowed_values" required="form:inline">...（保留原 v1.0 字面）</param>
        <param name="option" required="false" cardinality="0..*">...（保留原 v1.0 字面）</param>
        <param name="registry-key" required="form:registry">
            v4.2 PR-5 起新增。值通常为 "${current_state}"，由编排器 4c 在 LLM 展开前注入；
            LLM 按 ADR-010 §0 展开规则查 core/step-pause-registry.yaml 渲染等价 inline 形态。
            禁止与 title / result_field / allowed_values / option 共存（mutex critical）。
        </param>
    </params>
    <input-protocol critical="true">
        <!-- 5 条 rule 完全保留（与两形态均正交）-->
        ...
    </input-protocol>
</tag>
```

**修订理由（v1.1 / Patch B / review Finding 2 收口）**：① `<forms>` + `<mutex>` 在协议层显式表达"两形态互斥"，比 v1.0 的"required + 兼容声明"更可机器校验；② `required="form:inline"` / `required="form:registry"` 把"按形态条件必填"编码进 schema 属性，与 ADR-016 已有"必填参数表"叙述同步可演化（ADR-016 v4.2 修订段 / ADR-D2 同步落地）；③ LLM 只需读 `<forms>` 即可决定走哪一套展开规则，无需依赖外部"内化记忆"（与 PR-3' TAG-N1/N2 同款先例）。

**兼容性影响**：① **inline 形态**：phase 文件中 PR-6 之前残留的内联 `<step-pause title="..." result_field="..." allowed_values="..."/>`（受 `legacy-phase-step-pause-allowlist.txt` 兜底）继续命中 `form=inline`，行为完全等价；② **registry 形态**：本 PR 内编排器 4c 唯一新写法，6 个交互态弹窗字面经 registry 渲染后与 v4.1 完全等价；③ **mutex 强约束**：由 `check-io-contract.sh` 互斥校验段（CI-D1 / §2.6.bis）兜底，任何混用立即 CI 红。

---

### 2.3 文件 C · `mobile-qa-workflow/core/workflow.xml`（XML-D1，step 4 整段重写）

**操作**：定位当前 `core/workflow.xml` 的 `<step n="4" goal="阶段完成后更新进度并路由">` 块（v1.0 当前主干 100~373 行）；**整段删除**（含其内所有 `<switch>` / `<case>` 嵌套）；按下方新文**整段写入** 3 个新 step（4a / 4b / 4c）。

**新文（完整字面）**：

```xml
            <!-- ──────────────────────────────────────────────────────────────────
                 Step 4a / 4b / 4c（v4.2 PR-5 / O10+ Stage-2）：
                 把 v4.1 单 step 4 内 ~270 行 6-case switch 拆为三段职责正交：
                   · 4a：仅在 step-pause 恢复时执行 — 解析用户回复 + 双写 + 熔断
                   · 4b：阶段完成态判定 — 维护 stepsCompleted / lastStep / 重试熔断
                   · 4c：状态路由查表 — 按 registry on_success 派发或落入流转态
                 数据源：core/step-pause-registry.yaml（C5 单一权威源 / 禁止内联 case）
                 详见 ADR-010 §0 展开规则 + V1.1 §3.2.10+ + check-step-pause-registry.sh ──────── -->

            <step n="4a" goal="step-pause 用户回复解析 + 受限双写 + 熔断">
                <load target="mobile-qa-workflow/core/step-pause-registry.yaml"/>
                <check if="本轮请求是上一轮 step-pause 的用户回复（按 core-rules.xml input-protocol rule n=2 识别）">
                    <action>从用户回复首行解析 {key}={value}</action>
                    <action>按上一轮 step-pause 的 result_field 在 registry 中查到 allowed_values；
                            {key} 必须 == result_field（不一致判定解析失败）；
                            {value} 必须 ∈ allowed_values（不在判定解析失败）</action>

                    <check if="解析成功">
                        <action>更新 {workflow_status}：user_inputs.{key} = {value}（D15 总写）</action>
                        <check if="该 registry 项 mirror_to_top == true">
                            <action>同步镜像写入 workflow_status.{key} = {value}
                                    （v4.2 PR-5 起仅 Non-Bug 一项；v4.2 遗留 #3 删除后本块一并下线）</action>
                        </check>
                        <action>更新 {workflow_status}：parse_error_count = 0（D18 解析成功立即清零）</action>
                    </check>

                    <check if="解析失败">
                        <action>更新 {workflow_status}：parse_error_count += 1（D18 +1）</action>
                        <check if="parse_error_count >= 3">
                            <action>更新 {workflow_status}：current_state = Human-Review</action>
                            <action>输出 [parse-exceed: 连续 3 次解析失败，转人工]
                                    （触发 core-rules.xml human-review-protocol trigger n=4/5 类）</action>
                            <action>更新 {workflow_status}：parse_error_count = 0（熔断后清零）</action>
                            <!-- 不 return，落入 4b/4c 由 registry 重新发起 Human-Review step-pause -->
                        </check>
                        <check if="parse_error_count &lt; 3">
                            <action>输出 [parse-error: 期望 {key} ∈ {allowed_values}]</action>
                            <action>重新触发同一 step-pause（current_state 不变；不修改 stepsCompleted；user_inputs 不写）</action>
                            <action>结束本回合（return；下方 4b / 4c 跳过）</action>
                        </check>
                    </check>
                </check>
            </step>

            <step n="4b" goal="阶段完成态判定 + 重试熔断">
                <check if="{current_phase_result} != ABORT">
                    <action>将 {current_phase} 加入 {workflow_status} 的 stepsCompleted 数组</action>
                </check>
                <check if="{current_phase_result} == ABORT">
                    <action>保留 stepsCompleted 不变，等待当前阶段人工处理或补充信息后再重试</action>
                </check>
                <action>更新 {workflow_status} 的 lastStep 为 {current_phase}</action>
                <check if="rca_retry_count > 2 或 fix_retry_count > 2">
                    <action>触发重试熔断保护：更新 {workflow_status}：current_state = Human-Review</action>
                </check>
            </step>

            <step n="4c" goal="状态路由（registry 查表 / v1.1 修订：按 kind 派发）">
                <load target="mobile-qa-workflow/core/step-pause-registry.yaml"/>

                <check if="{current_state} == Done">
                    <action>工作流完成，输出最终摘要</action>
                </check>

                <check if="{current_state} 命中 registry">
                    <!-- v1.1 修订 / Patch A：先按 kind 派发；默认 step-pause，仅 Boundary-Refined 为 route。 -->

                    <!-- 分支 A：kind == "step-pause"（6 个交互态） -->
                    <check if="registry 项 kind == &quot;step-pause&quot;（默认）">
                        <!-- 首次进入交互态：发起 step-pause，等待用户回复（下一轮由 4a 解析） -->
                        <check if="本轮非 step-pause 用户回复（即 user_inputs.{result_field} 为空）">
                            <action>更新 {workflow_status}：parse_error_count = 0（D18 进入新 step-pause 前重置）</action>
                            <step-pause registry-key="${current_state}"/>
                            <!-- LLM 按 ADR-010 §0 展开规则 + core-rules.xml form=registry 查 registry 渲染 title / allowed_values / options -->
                        </check>

                        <!-- step-pause 用户回复已被 4a 写入 user_inputs.{result_field}：派发 on_success -->
                        <check if="本轮 user_inputs.{result_field} 非空">
                            <action>按 registry 项 on_success.{user_inputs.&lt;result_field&gt;} 执行原子动作序列：
                                    set_state / write / increment / check（true/false 子块）/ goto / terminal / interpret_freetext
                                    （详见 ADR-010 §0 与 step-pause-registry.yaml schema 注释）</action>
                            <action>派发完成后清空 user_inputs.{result_field}（消费一次性输入）；
                                    若 mirror_to_top == true，同步清空 workflow_status.{result_field}</action>
                            <action>按 on_success 中的 goto 跳转（terminal:true 时直接结束）</action>
                        </check>
                    </check>

                    <!-- 分支 B（v1.1 / Patch A）：kind == "route"（纯路由态，仅 Boundary-Refined） -->
                    <check if="registry 项 kind == &quot;route&quot;">
                        <action>不发起 step-pause、不等用户回复；直接按 registry 项 on_route 执行原子动作序列
                                （set_state / write / increment / goto / terminal）；与 v4.1 编排器
                                step 4 case Boundary-Refined 的"显式改态 + goto"行为 1:1 等价。</action>
                    </check>
                </check>

                <check if="{current_state} 未命中 registry 且非 Done（即纯流转态：Spec-Defining / Context-Curating / RCA-Designing / Fix-Designing / Fix-Implementing / Verifying / Intake）">
                    <!-- v1.1 修订：Boundary-Refined 已上移到 registry kind: route 项，本默认分支不再覆盖它。 -->
                    <goto step="2"/>
                </check>
            </step>
```

**修订理由（V1.1 §3.2.10+ Stage-2 + Registry 权威性约束 / v1.1 Patch A）**：① 4a / 4b / 4c 三段职责正交，编排器从 ~270 行混合关注点降到 ~80 行清晰三段（净瘦身 ~190 行）；② **零硬编码 case**——所有交互态 100% 走 `<step-pause registry-key="${current_state}" />` + `on_success` 查表，所有路由态 100% 走 `kind: route` + `on_route` 查表（含 Boundary-Refined）；③ 4b 的 stepsCompleted / lastStep / 重试熔断保留为通用动作（不特化 case），与 v4.1 完全等价；④ **v1.1 修订**：4c 默认分支已剥离 `Boundary-Refined`（v1.0 误归默认会导致 P3 自循环），改由 registry `kind: route` 显式改态 `current_state = RCA-Designing` 后跳转。

**兼容性影响（行为等价性 / DEMO-V1 验收）**：① 6 个交互态弹窗 title / 选项字面 100% 不变；② Spec-Uncertain 的 `selected_spec_index` 写入语义 100% 保留；③ Non-Bug 的 reflow 熔断逻辑（`< 2 → 重审 + +1 / >= 2 → Human-Review`）100% 保留；④ Human-Review 的自由文本解释 100% 保留；⑤ **v1.1 修订**：Boundary-Refined 的 `set_state = RCA-Designing + goto step 2` 行为 100% 保留，由 registry `kind: route` 项接管。

---

### 2.4 文件 D · `mobile-qa-workflow/scripts/check-step-pause-registry.sh`（SCRIPT-N1，新建）

**操作**：新建可执行 bash 脚本（`chmod +x`），实现 V1.1 §3.2.22 加严的三类校验，**默认 error 起步**（无 warning 过渡阶段，与主控 §4 严重度表一致）。

**三类校验（V1.1 §3.2.22 / ADR-010 §4 CI 约束）**：

| # | 校验目标 | 算法（python 提取 + bash grep / 与 `check-phase-abort-structure.sh` ENUM 抽取算法 DRY） |
|---|---|---|
| ① | Registry 状态名合法性 | 抽 `workflow-status-template.yaml` 头部「v4.1 完整集合」注释块得 `ENUM_SET`（同 `check-state-enum.sh`）；遍历 registry 每个 `state` ∈ `ENUM_SET`，违例 error |
| ② | Registry **双向严格相等**（v1.1 修订 / Patch C / review Finding 3 收口）| 在 `core/workflow.xml` 内严格匹配 4a/4b/4c 三段拆分（缺失即 error）；`EXPECTED_REGISTRY = {6 个交互态 + Boundary-Refined（v1.1 / Patch A）}` 与 registry 的 `state` 集**双向 diff**：`MISSING = EXPECTED − REGISTRY`（漏注册）/ `UNEXPECTED = REGISTRY − EXPECTED`（误增条目，含未审批的 demo 残留）。两类各自 error，分类报错。v1.0 仅子集校验（`EXPECTED ⊆ REGISTRY`）的方案已废弃 |
| ③ | 硬编码 case 禁出（H3） | 仅在 step 4a/4b/4c 区间内 grep：`<switch\b[^>]*current_state[^>]*>` 或 `<case\s+if="<交互态>"\s*>` 或 `<check\s+if="[^"]*current_state\s*==\s*"?<交互态>"?[^"]*"`；交互态白名单含 `Fix-Confirming`（PR-6 前向兼容）+ `Boundary-Refined`（v1.1：路由态硬编码也禁，强制走 registry kind: route）|

**骨架**（关键提取段；完整脚本随 PR 提交）：

```bash
#!/usr/bin/env bash
# check-step-pause-registry.sh (v4.2 PR-5 / O10+ / O22 / SCRIPT-N1)
set -euo pipefail
cd "$(dirname "$0")/.."
REG="core/step-pause-registry.yaml"; XML="core/workflow.xml"; TPL="core/workflow-status-template.yaml"
fail=0; emit_error() { echo "::error::$*"; fail=1; }

ENUM_SET=$(python3 - "$TPL" <<'PY'
import re, sys
src = open(sys.argv[1], encoding='utf-8').read().splitlines()
collect, block = False, []
for ln in src:
    if not collect and 'v4.1 完整集合' in ln: collect = True; continue
    if collect:
        if not ln.lstrip().startswith('#'): break
        block.append(ln)
        if 'Done' in ln: break
print(' '.join(sorted(set(re.findall(r'\b[A-Z][A-Za-z-]+\b', '\n'.join(block))))))
PY
)
REG_STATES=$(python3 -c "import re; print(' '.join(re.findall(r'^\s*-\s*state:\s*([A-Za-z][A-Za-z0-9-]*)', open('$REG').read(), flags=re.M)))")

# ① state 合法性
for st in $REG_STATES; do
  echo " $ENUM_SET " | grep -q " $st " || emit_error "registry state='$st' 不在 enum 集内"
done

# ② 拆分 + 双向严格相等（v1.1 修订 / Patch C）
python3 -c "import re,sys; sys.exit(0 if re.search(r'<step\s+n=\"4a\".*?</step>\s*<step\s+n=\"4b\".*?</step>\s*<step\s+n=\"4c\".*?</step>', open('$XML').read(), re.S) else 1)" \
  || emit_error "$XML 内未发现 step 4a/4b/4c 三段拆分（O10+ Stage-2 未落地）"
# v1.1：6 个交互态 + 1 个路由态 Boundary-Refined（Patch A）
EXPECTED="Info-Insufficient Spec-Uncertain Non-Bug RCA-LowConfidence Curation-Failed Human-Review Boundary-Refined"
EXP_SORTED=$(echo "$EXPECTED" | tr ' ' '\n' | sort -u)
REG_SORTED=$(echo "$REG_STATES" | tr ' ' '\n' | sort -u)
MISSING=$(comm -23 <(echo "$EXP_SORTED") <(echo "$REG_SORTED"))
UNEXPECTED=$(comm -13 <(echo "$EXP_SORTED") <(echo "$REG_SORTED"))
[ -n "$MISSING" ]    && for s in $MISSING;    do emit_error "registry 缺失条目（漏注册）: $s"; done
[ -n "$UNEXPECTED" ] && for s in $UNEXPECTED; do emit_error "registry 多余条目（H3 权威性 / 未审批的 demo 残留？）: $s"; done

# ③ 硬编码 case 禁出（仅在 step 4a/4b/4c 区间内 / v1.1 黑名单含 Boundary-Refined）
HITS=$(python3 - "$XML" <<'PY'
import re, sys
src = open(sys.argv[1], encoding='utf-8').read()
m = re.search(r'<step\s+n="4a".*?</step>\s*<step\s+n="4b".*?</step>\s*<step\s+n="4c".*?</step>', src, re.S)
if not m: sys.exit(0)
body = m.group(0); hits = re.findall(r'<switch\b[^>]*current_state[^>]*>', body)
for st in ["Info-Insufficient","Spec-Uncertain","Non-Bug","RCA-LowConfidence",
           "Curation-Failed","Human-Review","Boundary-Refined","Fix-Confirming"]:
    hits += re.findall(rf'<case\s+if="{re.escape(st)}"\s*>', body)
    hits += re.findall(rf'<check\s+if="[^"]*current_state\s*==\s*"?{re.escape(st)}"?[^"]*"', body)
for h in hits: print(h)
PY
)
[ -n "$HITS" ] && while IFS= read -r ln; do [ -n "$ln" ] && emit_error "硬编码 case 禁出违规（H3）：$ln"; done <<< "$HITS"

[ $fail -eq 0 ] && echo "✅ 通过（registry=$(echo $REG_STATES | wc -w | tr -d ' ') 项 / 双向严格相等 OK / 硬编码 case=0）"
exit $fail
```

**修订理由（V1.1 §3.2.22 加严 / v1.1 Patch C）**：① 三类校验全部 **error 起步**——本脚本不存在「过渡 warning 期」（与 `check-phase-abort-structure.sh` 不同），O10+ 落地即必须强约束「硬编码 case 禁出」，否则同步债只是从 XML 迁到 YAML（V1.1 §3.2.10+ 末尾原话）；② python 提取算法与 `check-phase-abort-structure.sh` ENUM 段同款（DRY）；③ **v1.1 修订**：第 ② 类升级为双向 diff，关闭 registry 多余条目假绿窗口（review Finding 3）；同时 `EXPECTED` 加入 `Boundary-Refined`（v1.1 / Patch A），第 ③ 类黑名单同步加入 `Boundary-Refined`（强制路由态走 registry，禁止退回硬编码）；④ PR-6 引入 `Fix-Confirming` 时由 PR-6 同步把它加入 `EXPECTED` 与黑名单（黑名单已前向兼容，PR-6 仅需扩 1 行）。

**兼容性影响**：① 本脚本**新建**，不影响现有 6 个 CI 脚本；② PR-5 合入瞬间 main 必须三类全绿，否则 PR 红（参见 §3.1）。

---

### 2.5 文件 E · `doc/adr/010-step-pause-registry-data-driven.md`（ADR-D1）+ `doc/adr/000-index.md`（ADR-IDX1）

**操作**：① 把 ADR-010 的「状态」段从 `**draft**` 改为 `**active**`；② 在 ADR-010 文末新增「PR-5 落地纪要」段，列出 6 项 finalize 信息（registry 文件路径 / 6 项 state 字面 / 编排器 4a/4b/4c 行号区间 / CI Check 16 严重度 / 跨平台抽查结果摘要 / 与 PR-6 / PR-7 后续衔接事项 4 条）；③ 在 `doc/adr/000-index.md` 中把 ADR-010 行尾的「`draft`」标记同步为「`active`」+ 追加 PR-5 落地链接。

**修订理由（H4 / 主控 §3）**：ADR 状态机 `draft → active` 是 v4.2 ADR 体例硬约束，PR-1 时 ADR-010 落地为 draft（占位 H4 前置依赖），PR-5 实际交付时必须同步切换状态并补充落地纪要——否则下游 PR-6 / PR-7 引用本 ADR 时会读到陈旧的 draft 警示信息。

**兼容性影响**：纯文档变更，零运行时影响。

---

### 2.5.bis 文件 E' · `doc/adr/016-step-pause-required-params.md`（ADR-D2，**v1.1 新增 / Patch B**）

**操作**：在 ADR-016 文末追加「v4.2 修订段」，明确两点：① v4.2 PR-5 起 `<step-pause>` 拆分为 `inline` / `registry` 两种**互斥**形态；② `inline` 形态保留 ADR-016 原"必填三参数（`title` / `result_field` / `allowed_values`）"约束不变；`registry` 形态独立约束（`registry-key` 必填，原三参数禁出）。原 ADR-016 主体「`<step-pause>` 必填参数表」整体保留，作为 `inline` 形态的精确定义。

**新文（追加段，~25 行）**：

```markdown
---

## v4.2 修订段（PR-5 落地 / 2026-04-21 / 关联 ADR-010 active 化）

**变化背景**：PR-5（O10+ Stage-2）把 `core/workflow.xml` step 4 内 6 个交互态 case
统一改写为 `<step-pause registry-key="${current_state}"/>`，新写法不再携带
`title` / `result_field` / `allowed_values`，而是由编排器 4c 在 LLM 展开前注入
`registry-key`，LLM 按 ADR-010 §0 展开规则查 `core/step-pause-registry.yaml` 渲染
等价 `inline` 形态后，再按 ADR-016 主体的 5 步咒语输出强结构。

**两形态契约（与 `core/core-rules.xml` `<tag name="step-pause"><forms>` 块字面同源）**：

| 形态 | 必填参数 | 禁出参数 | 适用范围 |
|---|---|---|---|
| `inline` | `title` + `result_field` + `allowed_values` | `registry-key` | phase 文件残留（PR-6 删除前过渡） |
| `registry` | `registry-key` | `title` + `result_field` + `allowed_values` + `option` | 编排器 4c（v4.2 PR-5 起唯一新写法） |

**强约束**：① 任何 `<step-pause>` 必须命中且仅命中其中之一；② mutex 违规
（同时含或同时缺）由 `scripts/check-io-contract.sh` 互斥校验段（CI-D1）兜底
为 error；③ `inline` 形态的 5 步咒语 / 输入契约（`[result_field=...]` 强结构）
完全延续 ADR-016 主体；`registry` 形态展开后等价 `inline`，输出契约相同。
```

**修订理由（v1.1 / Patch B / review Finding 2 收口）**：v1.0 仅在 PR 文档与 `core-rules.xml` 内"补丁式"声明 `registry-key` 必填，未同步 ADR-016 → 治理上断层（v4.2 ADR 体例硬要求"协议层契约变更必须有对应 ADR finalize 或修订"）。本段把两形态契约固化进 ADR-016，与 ADR-010 PR-5 落地纪要形成「数据源（010）+ 协议契约（016）」双锚点。

**兼容性影响**：纯文档变更；CI 层由 CI-D1 校验脚本承接行为约束。

---

### 2.6 文件 F · `.github/workflows/qa-workflow-schema-check.yml`（CI-N1）

**操作**：在现有 7 个 Check（PR-1 ~ PR-3' 已落地）之后追加 **Check 16**（编号承接 PR-3' Check 15 / `check-phase-abort-structure.sh`），调用 `mobile-qa-workflow/scripts/check-step-pause-registry.sh`，**默认 error 起步**（无 `continue-on-error: true` 配置，CI 红即阻塞合入）。

**修订理由（主控 §4 / V1.1 §3.2.22）**：本 Check 是 H3「Registry 权威性强约束」唯一的 CI 兜底，必须在 PR-5 合入瞬间生效，否则后续任何对 `core/workflow.xml` step 4 的硬编码回潮无法被自动捕获。

**兼容性影响**：① 主干干净时本 Check 必须输出零 error（DoD §3.2 验证）；② 与其他 7 个 Check 并发执行（独立 step），不影响现有 CI 时长 SLA。

---

### 2.6.bis 文件 F' · `mobile-qa-workflow/scripts/check-io-contract.sh`（CI-D1，**v1.1 新增 / Patch B**）

**操作**：在现有 `check-io-contract.sh`（PR-1 落地）末尾追加 **`<step-pause>` 互斥校验段**（约 30 行 bash + python 提取），与 `core-rules.xml` `<tag name="step-pause"><forms>` 块字面同源。

**校验规则**：扫描三处目标文件——`core/workflow.xml`（编排器 4c 唯一应为 `form=registry`）、`mobile-qa-workflow/phases/p{1..6}-*.md`（PR-6 删除前残留应为 `form=inline`）、`legacy-phase-step-pause-allowlist.txt` 列出的兜底文件——对每个 `<step-pause>` 标签判定形态：

| 命中条件 | 判定 |
|---|---|
| 含 `registry-key` 且不含 `title` / `result_field` / `allowed_values` / `option` | `form=registry` ✓ |
| 含 `title` + `result_field` + `allowed_values` 且不含 `registry-key` | `form=inline` ✓ |
| 同时含 `registry-key` 与 `title` 任一组旧字段 | **mutex 违规 / error**（id: `step-pause-mutex-both`）|
| `registry-key` 缺，且 `title` / `result_field` / `allowed_values` 缺任一 | **mutex 违规 / error**（id: `step-pause-mutex-neither`）|

**骨架（关键提取段）**：

```bash
# === <step-pause> 互斥校验段（v4.2 PR-5 / CI-D1 / Patch B / id: step-pause-mutex）===
mutex_check_file() {
  local f="$1"; [ -f "$f" ] || return 0
  python3 - "$f" <<'PY'
import re, sys
src = open(sys.argv[1], encoding='utf-8').read()
fail = 0
for m in re.finditer(r'<step-pause\b([^/>]*?)/?>|<step-pause\b([^>]*?)>([\s\S]*?)</step-pause>', src):
    attrs = (m.group(1) or m.group(2) or '')
    has_reg   = bool(re.search(r'\bregistry-key\s*=', attrs))
    has_title = bool(re.search(r'\btitle\s*=', attrs))
    has_rf    = bool(re.search(r'\bresult_field\s*=', attrs))
    has_av    = bool(re.search(r'\ballowed_values\s*=', attrs))
    inline_full = has_title and has_rf and has_av
    if has_reg and (has_title or has_rf or has_av):
        print(f"::error::step-pause-mutex-both / {sys.argv[1]} / 同时含 registry-key 与 inline 字段")
        fail = 1
    elif (not has_reg) and (not inline_full):
        print(f"::error::step-pause-mutex-neither / {sys.argv[1]} / 缺 registry-key 且 inline 三必填不齐")
        fail = 1
sys.exit(fail)
PY
}
mutex_targets=("core/workflow.xml" mobile-qa-workflow/phases/p[1-6]-*.md)
for t in "${mutex_targets[@]}"; do mutex_check_file "$t" || fail=1; done
```

**修订理由（v1.1 / Patch B / review Finding 2 收口）**：① 与 `core-rules.xml` `<forms><mutex critical="true">` 协议层声明形成「协议描述 + CI 兜底」闭环——只有协议层 + CI 同时声明并执行，"互斥两形态"才是真正可机器校验的契约；② 选择放在 `check-io-contract.sh` 而非新建脚本：本身这就是 IO 契约的一部分（输入字段集决定 LLM 输出契约），与现有 `check-io-contract.sh` 校验 input-protocol rule n=2 同源（DRY）；③ `step-pause-mutex-both` / `step-pause-mutex-neither` 两类 error id 便于 CI 日志快速定位违规种类。

**兼容性影响**：① PR-1 ~ PR-3' 落地后的 main 经本段扫描应零 error（PR-5 合入前 main 上只有 phase 文件 inline 形态 / 无 registry-key 形态，零混用）；② PR-5 合入瞬间编排器 4c 出现唯一一处 `form=registry`，phase 残留仍为 `form=inline`，零混用；③ PR-6 删除 phase 内联 + 引入 `Fix-Confirming` 时，registry 形态扩展，inline 形态减少，互斥校验仍正确。

---

## 3. PR-level DoD（链接到主控 §4 / §5 + V1.1 §4.2）

### 3.1 静态契约验收

| # | 验证项 | 验证方式 | 阻塞合入 |
|---|------|---------|--------|
| D1 | `core/step-pause-registry.yaml` 7 项 state（**v1.1 修订**：6 个交互态 `kind: step-pause` + 1 个路由态 `kind: route` Boundary-Refined）与编排器期望集合**双向严格相等** | CI Check 16 第 ② 类（v1.1 双向 diff，分类报 missing/unexpected）| ✅ |
| D2 | registry 7 项 state（含 Boundary-Refined）全部在 `workflow-status-template.yaml` enum 集内 | CI Check 16 第 ① 类 | ✅ |
| D3 | 编排器 step 4a/4b/4c 范围内**零硬编码 case**（含 Boundary-Refined / v1.1）（H3） | CI Check 16 第 ③ 类 | ✅ |
| D4 | `core/workflow.xml` 不再存在 `<step n="4" goal=...>` 单 step（必须拆为 4a/4b/4c） | CI Check 16 第 ② 类前置 | ✅ |
| D5 | `core/core-rules.xml` `<step-pause>` 标签**含 `<forms>` 互斥两形态块**（v1.1 / Patch B）+ 含 `<param name="registry-key" required="form:registry">` | grep `<form name="inline">` + `<form name="registry">` + `<mutex critical="true">`（reviewer 人工 + check-io-contract.sh 兜底） | ✅ |
| D5.bis | ADR-016 文末含「v4.2 修订段」（ADR-D2 / v1.1 / Patch B），两形态契约表与 `core-rules.xml` 同源 | grep `## v4.2 修订段` | ✅ |
| D5.tri | `scripts/check-io-contract.sh` 含 `<step-pause>` 互斥校验段（CI-D1 / v1.1 / Patch B），主干干净状态零 error | 本地跑 + grep `step-pause-mutex` | ✅ |
| D6 | ADR-010 状态 `active` + 含「PR-5 落地纪要」+ index 同步 | grep `^>\s*\*\*状态\*\*：\*\*active\*\*` + index 行 | ✅ |
| D7 | 现有 7 个 CI 脚本（PR-1 ~ PR-3' 全部）继续绿 | CI 全量 | ✅ |
| D8 | `legacy-phase-step-pause-allowlist.txt` **未被本 PR 修改或删除**（H3 边界 / O14 留 PR-6） | git diff 校验 | ✅ |
| D9 | `system-prompt.md` **未被本 PR 修改**（H1 + H3 边界 / 留 PR-6 首次构建替换） | git diff 校验 | ✅ |
| D10 | 6 个 phase 文件**未被本 PR 修改**（H3 边界 / O13 留 PR-6） | git diff 校验 | ✅ |
| D11 | `workflow-status-template.yaml` **未被本 PR 修改**（v1.1 修订 / Patch D：DEMO-V1 必须本地验证后 hard reset，禁止 enum 扩展进入 commit）| git diff 校验 | ✅ |

### 3.2 行为验收（跨平台 / 主控 §5 PR-5 行）

| # | 平台 | 验收项 | 期望结果 |
|---|------|--------|---------|
| B1 | Cursor / Claude Code（Full） | eval-cases 全量回归 | mean_score 不降（± 5% 抖动），零分 case 不增 |
| B2 | Trae（Full） | eval-cases 全量回归 | 同上 |
| B3 | Dify（Limited） | eval-cases 全量回归 | 同上 |
| B4 | 单 prompt LLM（Minimal） | 抽 1 用例 | step-pause 弹窗 title / 选项字面与 PR-3' 后版本 100% 一致 |
| B5 | Cursor + Dify | 4 个交互态弹窗截图（Spec-Uncertain / Non-Bug / RCA-LowConfidence / Human-Review）双侧对比 | 100% 一致（registry 数据化保证） |
| **B6 / DEMO-V1**（**v1.1 修订 / Patch D / review Finding 4 收口**）| Cursor 本地 | **新增 stop_state demo case 本地验证脚本**（V1.1 §4.1 B3 末尾约束 / 主控 §6 PR-5 DoD）| 在 `dev/demo-v1-local` **临时分支**上 7 步流程：① 临时在 `workflow-status-template.yaml` enum 集追加新 demo 态 `Demo-Stop`；② 临时在 `step-pause-registry.yaml` 追加 1 项（`state: Demo-Stop` + `title_template` + `result_field` + `allowed_values: [Confirm]` + `options[1]` + `on_success.Confirm: { set_state: Done, terminal: true }`）≈ 8 行；③ 临时在某 phase（如 `p1-intake.md`）某 action 写入 `current_state = Demo-Stop` 触发；④ 跑 `check-state-enum.sh` + `check-step-pause-registry.sh` 双绿（验证 enum 与 registry 双向一致 + 互斥校验通过）；⑤ Cursor 本地手跑 1 个 demo 用例，验证弹窗正常 + Confirm 后路由到 Done；⑥ `git reset --hard origin/feat/qa-workflow-v4.2-pr5-step-pause-registry` 强制回退所有 demo 改动；⑦ reviewer 复核 PR diff 不含任何 demo 残留（D11 校验兜底）。**最终 PR diff 干净**：`workflow-status-template.yaml` / phase 文件 / registry 中均无 `Demo-Stop` 字样 |

### 3.3 通用门禁（V1.1 §4.2）

- `eval-framework/artifact_checker.py` 全量通过
- `eval-cases/seed-10` chains A/B `mean_score` 不降，零分 case 不增
- 路由层抽 5 case 人工读 `workflow-status.yaml` 一致性

---

## 4. PR-level 回滚动作

**回滚原则（V1.1 §7 / 主控 §3 H3）**：本 PR 必须**整 PR 回滚**，不可"只回 SCRIPT-N1 保留 REG-N1 / XML-D1"——因为 SCRIPT-N1 是 H3 强约束的唯一兜底，单独回滚 SCRIPT-N1 等于打开硬编码 case 回潮缺口；反之单独回滚 REG-N1 / XML-D1 会让 SCRIPT-N1 在 main 上长期红，阻塞下游 PR。

**回滚步骤**：

1. `git revert` 本 PR commit（一次性回到 PR-3' 后状态）
2. 验证（**v1.1 修订**：含 8 个文件全部回退）：`core/workflow.xml` step 4 单 step 形态恢复 / 6 case 内联 step-pause 字面恢复（含 `Boundary-Refined` case 333~336 行恢复）/ `core/step-pause-registry.yaml` 文件消失 / `scripts/check-step-pause-registry.sh` 文件消失 / `core/core-rules.xml` `<forms>` 块回退到 PR-1 后的 `<params>` 形态 / `doc/adr/010-step-pause-registry-data-driven.md` 状态回到 `draft` / `doc/adr/016-step-pause-required-params.md` 「v4.2 修订段」消失 / `scripts/check-io-contract.sh` 互斥校验段消失
3. 跑 PR-3' 的 7 个 CI 脚本全量绿（含 `check-io-contract.sh` 回到 PR-1 行为）
4. 跑 eval-cases 全量回归（mean_score 不降）
5. 同步通知下游 PR-6 owner：本 PR 回滚意味着 PR-6 启动需推迟 + 重新评估 H3 串行链

**回滚阻断条件（不允许回滚的情况）**：① PR-6 已合入（PR-6 依赖 registry 就绪 + sp 首次构建包含 registry 注入；回滚 PR-5 必须先回 PR-6）② 已发布 v4.2 release 标签（需走 hotfix 而非 revert）。

---

## 5. 静态契约校验自检（本 PR 视角）

| Check 名 | 严重度 | 本 PR 触发预期 | 自检方式 |
|---|---|---|---|
| `check-state-enum.sh`（PR-1） | error | 绿（registry 7 项 state 都在 enum 内 / 编排器 4c 不写新 state） | 本地 `bash mobile-qa-workflow/scripts/check-state-enum.sh` |
| `check-system-prompt-sync.sh`（PR-2 升级 error） | error | 绿（本 PR 不改 sp） | 本地跑 |
| **`check-io-contract.sh`（PR-1 / 本 PR 追加 CI-D1 互斥校验段 / v1.1 / Patch B）** | error | 绿（编排器 4a 解析逻辑保持 input-protocol rule n=2 契约 + 新增 `<step-pause>` 互斥校验：编排器 4c 唯一 registry 形态命中、phase 残留按 inline 形态命中、零混用）| 本地跑 |
| `check-subagent-params.sh`（PR-1） | error | 绿（不动 SubAgent） | 本地跑 |
| `check-build-system-prompt-precondition.sh`（PR-2） | error → notice（PR-3' Seg-2 已转 notice） | notice（不阻塞） | 本地跑 |
| `check-phase-abort-structure.sh`（PR-3'） | warning（PR-6 升 error） | warning 同前（不动 phase 文件 / P4 notice 同前） | 本地跑 |
| **`check-step-pause-registry.sh`（PR-5 / 本 PR 新增）** | **error** | **绿**（三类校验全过 / 含双向严格相等 / 详见 §2.4） | 本地 `bash mobile-qa-workflow/scripts/check-step-pause-registry.sh` |

**reviewer 人工抽查**（reviewer 必跑，CI 不覆盖项）：
1. 字面对照 §2.1 registry 7 项（6 交互态 + 1 路由态 Boundary-Refined / **v1.1**）与 PR-3' 后 `core/workflow.xml` step 4 case 字面是否 1:1 等价（DEMO-V1 验收前置）
2. ADR-010 「PR-5 落地纪要」必须显式列出与 PR-6（O13/O14）/ PR-7（O15）的衔接事项；ADR-016 「v4.2 修订段」（**v1.1**）两形态契约表与 `core-rules.xml` `<forms>` 块字面同源
3. registry yaml schema 注释（顶部 50 行）必须与 ADR-010 §0 展开规则段一致；含 `kind` 字段说明（**v1.1**）
4. CI Check 16 第 ③ 类硬编码黑名单中 `Fix-Confirming` 已前向兼容；含 `Boundary-Refined`（**v1.1**）；PR-6 落地时无需再改脚本
5. **DEMO-V1（v1.1 / Patch D）实际在 `dev/demo-v1-local` 临时分支验证后已 hard reset，PR diff 不含 `Demo-Stop` 残留**

---

## 6. Reviewer 关注点 / 已知风险

### 6.1 Reviewer 必看项（对应 §1 表「Reviewer」列展开）

- **方案 owner**：① §2.1 字面等价性（按下方附录 §A.1 字面对照表逐字校对，**v1.1**：含 Boundary-Refined 行）② §2.3 step 4a/4b/4c 三段是否覆盖 v4.1 step 4 全部行为（含 stepsCompleted / lastStep / 重试熔断 / parse_error_count 4 类副作用 + **v1.1**：4c 按 `kind` 派发 `route` / `step-pause` 两形态）③ Non-Bug `Reflow check` 表达式是否与 P2 写入端一致（`< 2 → 重审 / >= 2 → Human-Review`）④ Spec-Uncertain `selected_spec_index` 三个 write 取值（1 / 2 / parallel）与 `workflow-status-template.yaml` 字段注释一致 ⑤ **v1.1**：`<step-pause>` 互斥两形态契约（`core-rules.xml` `<forms>` 块 + ADR-016 v4.2 修订段表 + `check-io-contract.sh` 互斥校验段）三方字面同源 ⑥ **v1.1**：`Boundary-Refined` 改为 registry `kind: route`，`set_state = RCA-Designing` + `goto step_2` 与 v4.1 `core/workflow.xml:333-336` 等价
- **平台 owner**：① CI Check 16 在干净主干零 error（**v1.1**：含第 ② 类双向 diff）② 跨平台 4 类弹窗截图对比 ≥ 5 例 ③ Limited 平台 LLM `registry-key` 查表展开记录 ≥ 5 例 0 漏展开 ④ **v1.1**：DEMO-V1 在 `dev/demo-v1-local` 临时分支验证后 hard reset，最终 PR diff 干净（D11 兜底校验）⑤ **v1.1**：`check-io-contract.sh` 互斥校验段（CI-D1）在干净主干零 error，能识别 phase 残留 inline 形态与编排器 registry 形态

### 6.2 已知风险与缓解

| 风险 | 等级 | 缓解动作 |
|---|---|---|
| LLM 看到 `<step-pause registry-key="${current_state}"/>` 不查 registry 而仍用旧 5 步咒语 | 中 | TAG-D1 在 `core-rules.xml` `<forms>` 块协议层显式声明两形态展开规则（**v1.1 / Patch B**）+ ADR-010 §0 + ADR-016 v4.2 修订段双锚点文档化 + PR-6 把 registry 注入 system-prompt L1 |
| Limited 平台（Dify）在 PR-6 sp 首次构建前看不到 registry | 低 | 本 PR 范围内 sp 仍含 PR-3' 后字面（与 registry 同源），Limited 平台行为 100% 等价；PR-6 首次构建后自动一致 |
| Check 16 第 ③ 类黑名单遗漏未来新交互态 | 低 | 已前向兼容 `Fix-Confirming` + `Boundary-Refined`（**v1.1**）；PR-6 / PR-7 引入新交互态时同步扩 `EXPECTED` + 黑名单 1 行 |
| ~~Boundary-Refined 「重新路由 RCA 策略」语义被简化为 default~~ | ~~低~~ | ~~v1.0 误判为低风险~~ → **v1.1 已修复（Patch A）**：纳入 registry `kind: route` 项，`set_state = RCA-Designing` 显式改态，与 v4.1 严格等价 |
| `mirror_to_top: true` 未来误新增导致顶层字段污染 | 低 | 主控 §6 PR-5 DoD 显式约束「新增 mirror_to_top 需 PR Review 批准」；遗留 #3 删除后下线 |
| Registry 多余条目（unexpected）造成 H3 权威性松弛 | **已闭环（v1.1）** | Check 16 第 ② 类双向 diff（**Patch C**）兜底，`UNEXPECTED = REGISTRY − EXPECTED` 任意非空即 error |
| DEMO-V1 改动残留进入 commit 污染主干 | **已闭环（v1.1）** | D11 校验 `workflow-status-template.yaml` 未被本 PR 修改（**Patch D**）+ DEMO-V1 强制 hard reset 流程 |

---

## 7. 修订日志

- **2026-04-21（v1.1，当前生效版）**：基于 [`pr-5-d14-step-pause-registry-REVIEW-2026-04-21.md`](./pr-5-d14-step-pause-registry-REVIEW-2026-04-21.md)（2 High + 2 Medium）整体修订，4 项 Patch 块：**A — 路由完整性修订**（Finding 1：`Boundary-Refined` 纳入 registry `kind: route` 项，关闭 P3 自循环回归 / §2.1 + §2.3 + §3.1 + §A）/ **B — `<step-pause>` 互斥形态契约**（Finding 2：`core-rules.xml` 重构为 `<forms>` 块 + ADR-016 v4.2 修订段（ADR-D2）+ `check-io-contract.sh` 互斥校验段（CI-D1）/ §1 + §2.2 + §2.5.bis + §2.6.bis）/ **C — Check 16 第 ② 类双向严格相等**（Finding 3：`comm -23 / -13` 双向 diff，关闭 unexpected 假绿窗口 / §2.4 + §3.1 D1）/ **D — DEMO-V1 重定义**（Finding 4：本地验证脚本 / 7 步流程 / 强制 hard reset / D11 兜底校验 / §3.2 B6 + §6.1）。变更点数 12 → 14；工作量 0.6d → 0.7d；涉及文件 6 → 8（新增 ADR-016 + check-io-contract.sh 修改）。v1.0 主体骨架完全保留，未引入新 V1.1 项。详见 §0 修订摘要。
- **2026-04-21（v1.0，已 superseded）**：v1.0 初版（基于主控 §6 PR-5 + V1.1 §3.2.10+（Stage-1 + Stage-2 + Registry 权威性约束）+ §3.2.22（CI 三类校验加严）+ ADR-010 草稿。整体 6 类 12 个变更点；与 PR-3'（PR-3 + PR-4 合并）后的 main 一致；严守 H3 边界——不动 sp / 不动 6 phase / 不动 allowlist / 不动 workflow-status-template）。

---

## 附录 A · 字面对照表（reviewer 校对用 / 不参与文档行数统计）

> 附录 §A 为 reviewer 字面校对工具表（registry 7 项 ↔ PR-3' 后 `core/workflow.xml` step 4 case 字面 1:1 对照 / **v1.1 修订**：新增 Boundary-Refined 路由项行）；如发现任何字面差异 = registry 与编排器不一致 = 本 PR 红。

| registry state | kind | title_template | result_field | allowed_values | options 数 | 编排器原 case 行号区间（基于 PR-3' 后 main） |
|---|---|---|---|---|---|---|
| Info-Insufficient | step-pause | 「信息不足，需要用户补充以下缺失项：\n{missing_items}」 | info_insufficient_action | [Submit] | 1 | 138~165 |
| Spec-Uncertain | step-pause | 「Spec 存在歧义，请确认 Expected Behavior：\n{spec_options}」 | spec_uncertain_choice | [1, 2, S] | 3 | 167~210 |
| Non-Bug | step-pause | 「Non-Bug 判定结果，请确认处理方向：\n\n{non_bug_context}」 | non_bug_user_choice | [Accept, Reflow] | 2 | 212~235（Reflow 熔断在 P2 写入端 / phase_history 反查 / mirror_to_top: true） |
| RCA-LowConfidence | step-pause | 「根因分析置信度不足（< 0.5），建议处理方向：{suggestion}」 | rca_lowconf_action | [Retry, Human] | 2 | 237~270 |
| Curation-Failed | step-pause | 「上下文策展失败（置信度 < 0.4），请补充信息或转人工」 | curation_failed_action | [Retry, Human] | 2 | 338~365 |
| Human-Review | step-pause | 「⚠️ 需要人工介入，请处理后告知继续方向」 | human_review_continue | [Continue] | 1 | 273~331（含 interpret_freetext 自由文本解释段） |
| **Boundary-Refined**（**v1.1 / Patch A**）| **route** | — | — | — | — | **333~336**（v4.1：`<action>边界等级已精化，重新路由 RCA 策略</action><action>更新 {workflow_status}：current_state = RCA-Designing</action><goto step="2"/>` → registry `on_route: { set_state: RCA-Designing, goto: step_2 }` 严格等价）|

**附录使用说明**：reviewer 在 PR-5 commit diff 中按本表逐项打开 `core/step-pause-registry.yaml` 与 PR-3' 后 `core/workflow.xml` 行号区间，字面对照；如发现差异，要求 PR owner 修正 registry 字面（不允许"既保留行为差异又通过 review"）。

