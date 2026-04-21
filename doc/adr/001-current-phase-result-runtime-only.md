# ADR-001: `current_phase_result` 设计为运行时变量（方案 A）

> **状态**：active
> **关联决定**：D1（来自 v2.2 主文档 §6 D 表 / V1.1 §2.5 协议层）
> **关联 PR**：v4.1 PR-1（DSL 协议）+ v4.1 PR-2（编排器实现）（均已合入）

## 1. 背景

phase 早退路径需要一个变量承载"本 phase 是否提前结束、原因为何"的语义，供编排器 step 2 路由判定。曾讨论两个方案：
- **方案 A**：`current_phase_result` 作为**运行时变量**，仅在编排器 step 4 case 切换上下文中存在，**不持久化**到 `workflow-status.yaml`
- **方案 B**：作为持久化字段写入 `workflow-status.yaml`

## 2. 决定

采用**方案 A**：
- `current_phase_result` 是编排器 step 4 的运行时变量，生命周期 = 单次 phase 退出 → 编排器 step 2 路由判定 → 立即销毁
- 取值仅 `ABORT` 一种语义；其余分支按 `current_state` + `stepsCompleted` 推断
- **不写入** `core/workflow-status-template.yaml`，避免污染状态契约

## 3. 替代方案

- **方案 B**（持久化字段）：被拒绝。理由：① 该值仅作"phase → 编排器"单向短路信号，无跨回合恢复需求；② 持久化会引入"过期值复用"风险（旧 ABORT 残留误触新分支）；③ 不必要扩张 schema 表面积。

## 4. 影响

- **协议层**：`core/core-rules.xml` 显式声明 `current_phase_result` 为运行时变量
- **phase 文件**：phase 早退必须配 `<action>设置 current_phase_result = ABORT</action>` 单独动作
- **编排器**：`core/workflow.xml` step 4 在路由判定后**必须立即清除**该变量
- **CI**：无直接守门（由 ADR-021 宏标签落地后通过 `check-phase-abort-structure.sh` 兜底）
- **跨平台**：对 Limited / Minimal 平台无影响（运行时变量在单 prompt 注入语境下退化为局部上下文）

## 5. 引用

- v2.2 主文档 §6 D1 拍板纪要
- v2.2 PR-4 子文档 `pr4-phase-abort-fanout-isolation.md`（D1 落地的 5 步咒语）
- ADR-021（`<phase-abort>` 宏标签 / 在 D1 protocol 之上的声明式语法糖）
