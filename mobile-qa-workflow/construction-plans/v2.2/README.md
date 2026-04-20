# Mobile QA Workflow v4.1 — PR 详细施工单（v2.2）

> 主文档：[`../../QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md`](../../QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md)
> 本目录性质：主文档 §4 的"详细施工单"按 PR 拆分到本目录。

## 子文档清单

- PR-1 · schema 协议层 → [`pr1-schema-protocol.md`](./pr1-schema-protocol.md)
- PR-2 · 编排器 step-pause 双写 + step3 传参 → [`pr2-orchestrator-step-pause.md`](./pr2-orchestrator-step-pause.md)
- PR-3 · P2 Non-Bug 闭环 + Context-Curating → 待展开
- PR-4 · P3/P4/P6 ABORT + 字段隔离 + base_score → 待展开
- PR-5 · Deep-Dive 落盘 + step-pause 现状盘点 + allowlist → 待展开
- PR-6 · agents/templates 治理（最小子集） → 待展开
- PR-7 · SKILL/system-prompt/PLATFORM-GUIDE 同步 → 待展开
- PR-8 · CI + install 整合 → 待展开

## 子文档骨架

```
# PR-{N} · {名称}

> 主文档：../../QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md
> 协议依赖：附录 C D{x}/D{y}

## 1. PR 元信息（分支 / Base / 层级 / Reviewer / 关联 issue / 工作量 / 涉及文件）
## 2. 文件级 diff 列表（每个文件：修改类型 / 修复条目锚点 / 原文 / 新文 / 修订理由 / 兼容性影响）
## 3. PR-level DoD 子集（链接到主文档 §5）
## 4. PR-level 回滚动作（链接到主文档 §7）
## 5. §5.1 静态契约校验自检（本 PR 视角）
```

## 约定

- 跨 PR 横切契约（D1-D19 / §5 DoD / §6 迁移脚本 / §7 回滚）只在主文档维护，子文档**链接而非复述**。
- 行号锚点使用 `startLine:endLine:filepath` 三段式 fenced code reference。
- 子文档展开前**重新对齐 main 行号**（避免基于过期锚点）。
