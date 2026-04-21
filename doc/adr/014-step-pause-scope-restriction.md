# ADR-014: `<step-pause>` 调度作用域限定（仅编排器 step 4）

> **状态**：active
> **关联决定**：D14（v2.1 review 拍板，v2.2 强化）
> **关联 PR**：v4.1 PR-1 + PR-2（已合入）

> **本 ADR 是 O4+ 散布注释短引用化的高频引用目标**（约 ~50 处 `<!-- ADR-014 -->` 替换；v4.2 PR-3 / PR-6 长注释删除时整体迁出）。

## 1. 背景

phase 内 `<step-pause>` 跨回合恢复协议缺口：编排器 `core/workflow.xml` step 4 通过 `current_state` 路由 + `{xxx_user_choice}` 顶层字段恢复（已是事实标准），但若 phase 文件内继续新增内联 step-pause，会与编排器重复弹窗 + 缺乏统一恢复协议。

## 2. 决定

**step-pause 调度归一**：
1. `<step-pause>` **仅允许出现在** `core/workflow.xml` 编排器 step 4 内（按 `current_state` 路由，覆盖 v4.1 全部 6 个 step-pause 场景）
2. **phase 文件禁止新增内联 `<step-pause>`**；phase 内有暂停需求时，写 `current_phase_result = ABORT` 让编排器 step 4 接管（详见 ADR-001）
3. **例外：v3 现存条目登记** `mobile-qa-workflow/scripts/legacy-phase-step-pause-allowlist.txt`（D19 / ADR-019）；CI `Check 2 — D14 调度作用域 + D19 allowlist 双向匹配` 守门
4. v4.1 起步 allowlist = 2 个条目（P2 step 4 Spec-Uncertain / P4 step 6 Fix-Designing）；v4.2 遗留 #6 整改清零

## 3. 替代方案

- **方案 X**（允许 phase 内任意位置 step-pause）：被拒绝。理由：① 跨回合恢复协议无法统一；② 与编排器 step 4 重复弹窗；③ CI 守门难度增加。
- **方案 Y**（v4.1 立即清零所有 phase 内 step-pause）：被拒绝。理由：现存 2 处规范化需 +0.3d，超出 v4.1 范围；v4.2 整改更合时机。

## 4. 影响

- **协议层**：`core/core-rules.xml` `<step-pause>` 标签定义注释明确"调度作用域 = 仅编排器 step 4"
- **phase 层**：6 个 phase 文件头部注释提示（v4.2 PR-1 PHASE-C1~C6 落地）
- **CI**：`Check 2 — D14 调度作用域 + D19 allowlist 双向匹配`（已落地，error 级）
- **回滚**：本 ADR 状态变更需要同步全仓 ~50 处短引用 + allowlist 文件

## 5. 引用

- v2.2 主文档 §6 D14 拍板纪要
- ADR-019（legacy step-pause allowlist）
- ADR-001（current_phase_result 运行时变量 / phase 早退协议）
- ADR-021（phase-abort 宏标签 / v4.2 在 D14 protocol 之上的语法糖）
