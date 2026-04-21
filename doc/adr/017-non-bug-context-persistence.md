# ADR-017: `non_bug_context` 字段入 schema 持久化

> **状态**：active
> **关联决定**：D17（v2.2 review 第 P0-1 项）
> **关联 PR**：v4.1 PR-1（已合入）

## 1. 背景

`non_bug_context` 已被 PR-2 / PR-3 当作持久化状态字段使用（编排器 case Non-Bug 的 step-pause 标题占位 + Non-Bug 判定说明承载），但 PR-1 schema 清单与 PR-7 入口文档同步都未注册它。这样落地后，"P2 → 编排器 case Non-Bug" 会依赖一个"写了但不在状态契约里"的隐式字段。

## 2. 决定

PR-1 在 `core/workflow-status-template.yaml` 显式新增 `non_bug_context: null`：
- **用途**：① 供编排器 case Non-Bug 的 step-pause 标题占位使用；② 仅承载最近一次 Non-Bug 判定说明
- **生命周期**：非长期业务字段，允许在后续会话中被覆盖
- **迁移脚本**：v3 → v4 迁移时补齐 `null`
- **PR-7 三处入口文档同步**：PLATFORM-GUIDE.md / SKILL.md / system-prompt.md 字段表新增本字段

## 3. 替代方案

- **方案 X**（不持久化，改成运行时变量）：被拒绝。理由：① 跨回合需要承载（用户回到对话时仍可看到 Non-Bug 判定说明）；② step-pause 标题占位需要在 LLM 推理时可见。

## 4. 影响

- **协议层**：`core/workflow-status-template.yaml` 头部新增字段定义
- **迁移脚本**：v3 → v4 补齐
- **CI**：`Check 4 — 顶层镜像字段过渡标注` 不直接守门本字段（仅守门 `non_bug_user_choice`），但本字段属于 ADR-015 镜像白名单的语义同侧

## 5. 引用

- v2.2 主文档 §6 D17 拍板纪要（v2.2 review P0-1）
- ADR-015（顶层镜像白名单）
