# ADR-021: `<phase-abort>` / `<phase-complete>` 宏标签

> **命名冲突规避声明**：本 ADR 描述的 `<phase-abort>` / `<phase-complete>` 是
> **核心 DSL 宏标签**（V1.1 O21 / §3.2.21 / PR-3 落地），用于声明式表达 phase 出口
> 的"state / fields / ABORT / 退出"4 步动作；这与 v2.2 PR-4 子文档名
> `phase-abort-fanout-isolation.md` 描述的"phase 内 ABORT 标记 + fanout 字段隔离"
> 是**完全不同范畴**的工作 —— 后者是 v4.1 protocol-level B1\* 修复，使用 v3 既有
> `<action>设置 current_phase_result = ABORT</action>` 写法；本 ADR 描述的宏标签
> 是 v4.2 在该 protocol 之上新增的"声明式语法糖"，用宏一行展开后等价于
> v2.2 PR-4 写入的"5 步咒语"。

> **状态**：**draft**（PR-3 落地依赖；本 PR 仅落地草稿提供 H4 前置依赖）
> **关联决定**：V1.1 O21（v4.2 新增）
> **关联 PR**：**v4.2 PR-3（实际交付）**

> **草稿状态声明**：本 ADR 描述的 `<phase-abort>` / `<phase-complete>` 宏标签 **由 v4.2 PR-3 实际交付**；本 PR（v4.2 PR-1）仅落地本草稿文件，目的是满足主控 §3 H4 强约束（"ADR 必须先于代码 PR 落地"）。
> 草稿落地后到 PR-3 实际交付前，本 ADR 状态保持 `draft`，PR-3 落地时同步切换为 `active`，并在本节末尾追加"PR-3 落地纪要"。

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
