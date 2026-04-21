# ADR-003: DSL 标签白名单边界（仅约束 `<flow>` / `<task>` 内部）

> **状态**：active
> **关联决定**：D3（v1.0 review 拍板）
> **关联 PR**：v4.1 PR-1（已合入）

## 1. 背景

XML 标签的"白名单严格校验"若覆盖整个 SKILL 目录，会误伤元数据标签（`<llm>`、`<mandate>`、`<agent-taxonomy>`、`<human-review-protocol>` 等）。需要明确白名单的作用范围。

## 2. 决定

DSL 标签白名单**仅约束** `<flow>` / `<task>` 内部的可执行 DSL 标签：
- 受白名单约束：`<step>` / `<check>` / `<switch>` / `<case>` / `<action>` / `<goto>` / `<step-pause>` / `<ask>` / `<template-output>` / `<invoke-subagent>` / `<load>` 等
- **不受白名单约束**（元数据 / 文档性标签）：`<llm>` / `<mandate>` / `<agent-taxonomy>` / `<human-review-protocol>` / `<trigger>` / `<output-format>` / `<io-contract>` / `<phase>` 等

## 3. 替代方案

- **方案 X**（全文档统一白名单）：被拒绝。理由：① 元数据标签需要灵活扩展；② 强制约束会污染未来文档化能力；③ LLM 推理时本就只解析 `<flow>` / `<task>` 体内的可执行 DSL。

## 4. 影响

- **协议层**：`core/core-rules.xml` `<supported-tags>` 注释明确"白名单仅约束 `<flow>` / `<task>` 内部"
- **CI**：现有的 schema-check 不对元数据标签做白名单校验
- **后续 PR**：新增的元数据标签（如 ADR-021 宏标签 `<phase-abort>` / `<phase-complete>`）属于可执行 DSL，需要同步加入白名单

## 5. 引用

- v2.2 主文档 §6 D3 拍板纪要（v1.0 review 第 2 项）
- `core/core-rules.xml` `<supported-tags>` 注释
