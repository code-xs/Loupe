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

## 6. v4.2 PR-3' 修订 — Spec-Uncertain 契约统一（O13a / 2026-04-21）

**修订点**：编排器 `core/workflow.xml` step 4 case `Spec-Uncertain` 的 `step-pause` `allowed_values` 由原 `Confirm`（单选）改为 `1|2|S` 三选；下游 `<switch>` 同步扩展为 `1` / `2` / `S` 三个 `case` 分支；`workflow_status` 新增协议字段 `selected_spec_index`（取值 ∈ {1, 2, parallel}）由编排器写入。

**理由**：
1. **跨平台行为对齐**：Limited 平台（Dify / Coze）历史上 `system-prompt.md` 内 P2 内联段已是 `[1] {option_1}` / `[2] {option_2}` / `[S] Skip` 三选；Full 平台（Cursor / Trae）通过编排器 `<step-pause>` 渲染 Spec-Uncertain 弹窗，原 `Confirm` 单选导致 Cursor 用户只能"确认后继续"，与 Limited 平台不一致。本次修订将 Limited 平台已有的三选行为升格为跨平台权威契约。
2. **"恢复语义"而非"扩展能力"**：Cursor / Trae 用户从单选变三选，本质是恢复 Limited 平台已有的语义，不是新增能力（PR-7 O15 才会让 P2 按 `selected_spec_index` 走差异化路径）。
3. **D14 调度作用域不变**：本次修订 **仅扩展 step-pause `allowed_values` 字面**，不引入 phase 内新的 step-pause；D14 + D19 守门规则原样有效。

**关联 PR-6 依赖**：
- PR-6 删除 P2 step 4 / P4 step 6 的 phase 内联 `<step-pause>`（D19 allowlist 清零）后，Spec-Uncertain 路径的事实标准 = 编排器 step 4 case 唯一渲染弹窗 = `1|2|S` 三选 + 写入 `selected_spec_index`；PR-6 的 P2 改写需消费 `selected_spec_index` 字段（O15）。
- 在 PR-6 完成 D14 收口前，本字段 **仅由编排器写入，P2 暂不消费**；属"协议显式化但无消费方"过渡态，YAML 字段写入但读取方 default null（详见 v4.2 PR-3' 主控文档 §7 议题 #3 收口）。

**关联引用**：
- ADR-021（phase-abort 宏 / 同 PR Seg-1）
- v4.2 PR-3' 主控文档 §2.5 / §2.6 / §2.7（CONTRACT-D1 / SP-N1 / CONTRACT-D3 完整字面）
- v1.1 优化方案 §3.2.13a（O13a）
