# ADR-021: `<phase-abort>` / `<phase-complete>` 宏标签

> **命名冲突规避声明**：本 ADR 描述的 `<phase-abort>` / `<phase-complete>` 是
> **核心 DSL 宏标签**（V1.1 O21 / §3.2.21 / PR-3 落地），用于声明式表达 phase 出口
> 的"state / fields / ABORT / 退出"4 步动作；这与 v2.2 PR-4 子文档名
> `phase-abort-fanout-isolation.md` 描述的"phase 内 ABORT 标记 + fanout 字段隔离"
> 是**完全不同范畴**的工作 —— 后者是 v4.1 protocol-level B1\* 修复，使用 v3 既有
> `<action>设置 current_phase_result = ABORT</action>` 写法；本 ADR 描述的宏标签
> 是 v4.2 在该 protocol 之上新增的"声明式语法糖"，用宏一行展开后等价于
> v2.2 PR-4 写入的"5 步咒语"。

> **状态**：**active**（v4.2 PR-3' 已落地）
> **关联决定**：V1.1 O21（v4.2 新增）
> **关联 PR**：**v4.2 PR-3'（已合入）**

> **落地状态声明**：本 ADR 描述的 `<phase-abort>` / `<phase-complete>` 宏标签 **由 v4.2 PR-3' 实际交付**（v4.2 PR-1 仅落地草稿满足 H4 前置依赖）。
> PR-3' 合入后状态切换为 `active`，落地纪要见本文末 §6。

## 1. 背景

v4.1 PR-4 落地的"phase 内 ABORT 标记 + fanout 字段隔离"协议要求每个 phase 出口写入 5 步咒语：
```xml
<action>设置 current_state = <下一状态></action>
<action>更新 {workflow_status}：current_state = <下一状态></action>
<action>fix_fanout_mode = <值></action>  <!-- 仅 Fix 阶段 -->
<action>设置 current_phase_result = ABORT</action>  <!-- 仅早退 -->
<action>退出本 phase（编排器 step 4 case 接管）</action>
```
6 个 phase × 平均 5 处出口 ≈ 30 处重复，可读性差且易写错。

## 2. 决定（草稿，PR-3 实施时 finalize）

引入 2 个**核心 DSL 宏标签**：

### `<phase-abort reason="ADR-XXX" next-state="..." />`
展开等价于：
```xml
<action>设置 current_state = <next-state></action>
<action>更新 {workflow_status}：current_state = <next-state></action>
<action>设置 current_phase_result = ABORT</action>
<action>退出本 phase（编排器 step 4 case 接管）</action>
```

### `<phase-complete next-state="..." [fix-fanout-mode="..."] />`
展开等价于：
```xml
<action>设置 current_state = <next-state></action>
<action>更新 {workflow_status}：current_state = <next-state></action>
<action>fix_fanout_mode = <fix-fanout-mode></action>  <!-- 仅当属性存在 -->
<action>退出本 phase</action>
```

## 3. 替代方案

- **方案 X**（继续手写 5 步咒语）：被拒绝。理由：可读性差 / 易漏写 / 无法统一守门。
- **方案 Y**（用 ADR-001 的 current_phase_result 替代 phase-abort）：被拒绝。理由：① 二者是不同抽象层级（D1 是 protocol，本 ADR 是 syntax sugar）；② 仍需手写其余 4 步。

## 4. 影响

- **协议层**：`core/core-rules.xml` `<supported-tags>` 新增 2 个标签 + 子标签 schema
- **phase 层**：6 个 phase 出口的 5 步咒语替换为 1 行宏（净减 ~120 行）
- **CI**：`check-phase-abort-structure.sh`（PR-3 启用 warning，PR-6 升级 error）守门宏展开正确性
- **跨平台**：Limited / Minimal 平台需 system-prompt 生成器（PR-2 交付）展开宏后注入

## 5. 引用

- V1.1 §3.2.21 O21 描述
- ADR-001（current_phase_result 运行时变量 / 本宏标签的下层 protocol）
- ADR-014（D14 调度作用域 / `<phase-abort reason="ADR-014">` 的常见调用）
- v2.2 PR-4 子文档 `pr4-phase-abort-fanout-isolation.md`（**完全不同范畴**，详见首段命名冲突规避声明）

## 6. PR-3' 落地纪要（v4.2 / 2026-04-21）

### 6.1 落地命中点（11 处 ABORT + 5 处 phase-complete）

**11 处 `<phase-abort>` 命中点**：

| # | 文件 | 锚点段 | 目标 state | reason |
|---|---|---|---|---|
| ABORT-D1 | `phases/p2-spec-definition.md` | step 4 / Non-Bug 早退 | `Non-Bug` | ADR-014 |
| ABORT-D2 | `phases/p2-spec-definition.md` | step 7 / Curation-Failed | `Curation-Failed` | ADR-001 |
| ABORT-D3 | `phases/p3-root-cause.md` | step 2 / 纯 C 级证据阈值未通过 | `Spec-Defining` | ADR-001 |
| ABORT-D4 | `phases/p3-root-cause.md` | step 5 / simple-single 升级 | `RCA-Designing`（fanout→medium）| ADR-015 |
| ABORT-D5 | `phases/p3-root-cause.md` | step 5 / medium-challenge 升级 | `RCA-Designing`（fanout→complex）| ADR-015 |
| ABORT-D6 | `phases/p3-root-cause.md` | step 5 / complex-arbitrated 不收敛 | `Human-Review` | ADR-015 |
| ABORT-D7 | `phases/p3-root-cause.md` | step 10 / RCA-LowConfidence | `RCA-LowConfidence` | ADR-001 |
| ABORT-D8 | `phases/p6-verification.md` | step 6 / 失败回流 | `{workflow_status}.current_state`（占位字面）| ADR-001 |
| ABORT-D9 | `phases/p5-fix-impl.md` | step 6 / error-dump 存在 | `Human-Review` | ADR-001 |
| ABORT-D10 | `phases/p5-fix-impl.md` | step 6 / contract-checklist 缺失 | `Human-Review` | ADR-001 |
| ABORT-D11 | `phases/p5-fix-impl.md` | step 6 / 两产物均不存在 | `Human-Review` | ADR-001 |

**5 处 `<phase-complete>` 命中点**（P4 phase-complete 留 PR-6，与内联 step-pause 删除同 commit）：

| # | 文件 | 锚点段 | 目标 state | 含属性 |
|---|---|---|---|---|
| COMP-D1 | `phases/p3-root-cause.md` | step 10 / 成功路径 | `Fix-Designing` | fields + append_history + update_config |
| COMP-D2 | `phases/p1-intake.md` | step 7 / Issue Card 输出 | `Spec-Defining` | fields + update_config |
| COMP-D3 | `phases/p2-spec-definition.md` | step 9 / 成功路径 | `RCA-Designing` | update_config |
| COMP-D4 | `phases/p5-fix-impl.md` | step 7 / 输出与状态流转 | `Verifying` | update_config（`output_contract_checklist` 条件写入显式拆出宏外，宏 `update_config` 仅含 `output_impl_report`；详见 §6.3 绝对禁止清单 #5）|
| COMP-D5 | `phases/p6-verification.md` | step 8 / PR/MR 生成 | `Done` | （无附加属性）|

### 6.2 「state 占位字面 = 沿用上文」补充约定（ABORT-D8 特殊性）

`<phase-abort>` 第 1 步「更新 `current_state` = `<state>`」的 `<state>` 取值规则：
- **常规取值**：必须落在 `core/workflow-status-template.yaml` 头部权威 enum 集内（CI Check 15 守门）；
- **占位字面（特例）**：当 `state` 取值以 `{` 开头时（典型形如 `state="{workflow_status}.current_state"`），LLM 应理解为「沿用本 step 内 switch / case 上文已写入的 `current_state`」，**不重新赋值**；CI Check 15 跳过该字面的 enum 校验。
- 应用场景：P6 step 6 失败回流（ABORT-D8）— 上文 switch 已按 `verification_failure_type` 写入 `Fix-Designing` / `RCA-Designing` / `Human-Review` 三种 `current_state`，宏统一以占位字面继承上文已写值，避免改写后失去三分支语义。

### 6.3 宏改写后的「绝对禁止清单」摘要

1. **❌ 漏写 `<phase-abort>` 第 3 步 ABORT** — 违反 D1 → `stepsCompleted` 错误追加 → B1\* 主链路 bug 复发；CI Check 15 通过"phase 文件含宏 ≥ 1"硬约束兜底。
2. **❌ 把 `fields` 内字段拆出宏外单独写 `<action>`** — 违反原子性，让 LLM 误以为可分轮次执行。
3. **❌ 在 `<phase-abort>` 与 `<phase-complete>` 之间互相嵌套** — 语义冲突，行为未定义。
4. **❌ 跨 LLM 输出轮次拆分宏的 sub-action** — 每个宏必须在单轮内完成 4/5 步全部执行。
5. **❌ 把"按运行时单 key 跳过"的条件写入压进宏 `update_config`** — 宏协议明确为「全部 key=value 写入」（无 conditional / null-skip）。如 P5 step 7 的 `output_contract_checklist`（仅当存在才写入）必须显式拆为宏外 `<check>`，宏 `update_config` 仅含必写 key（v1.1 review Finding #3 收口 / 详见附录 §2.5）。

### 6.4 CI 守门

- **Check 15** `scripts/check-phase-abort-structure.sh`（v4.2 PR-3' 启用 warning，PR-6 升级 error）守门：① `state` ∈ 权威 enum 集（占位字面跳过）；② `fields` key ∈ template 顶层字段表；③ phase 文件含宏 ≥ 1（P4 输出 notice 提示「PR-6 删除内联 step-pause 后改写」）。
- 干净主干实跑：phase-abort = 11 / phase-complete = 5 / 0 warning / 1 notice（P4）。
