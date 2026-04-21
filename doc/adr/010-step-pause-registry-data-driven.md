# ADR-010: `step-pause-registry.yaml` 数据驱动方案

> **状态**：**draft**（PR-5 落地依赖；本 PR 仅落地草稿提供 H4 前置依赖）
> **关联决定**：D10（v2.0 附录 B 占位）+ V1.1 O10+ Stage-1
> **关联 PR**：**v4.2 PR-5（实际交付）**

> **草稿状态声明**：本 ADR 描述的 `core/step-pause-registry.yaml` **由 v4.2 PR-5 实际交付**；本 PR（v4.2 PR-1）仅落地本草稿文件，目的是满足主控 §3 H4 强约束（"ADR 必须先于代码 PR 落地"）。
> 草稿落地后到 PR-5 实际交付前，本 ADR 状态保持 `draft`，PR-5 落地时同步切换为 `active`，并在本节末尾追加"PR-5 落地纪要"。

## 1. 背景

v4.1 的 6 个 `<step-pause>` 在编排器 step 4 case 中以"硬编码 case 分支"形式存在，每个 case 重复 `title` / `result_field` / `allowed_values` / `option` 等 5 步配置。维护成本高 + 新增 step-pause 需要改编排器 XML。

## 2. 决定（草稿，PR-5 实施时 finalize）

引入 `core/step-pause-registry.yaml` 作为**数据驱动**的 step-pause 配置中心：
- 所有 step-pause 配置集中在 registry，按 `current_state` 索引
- 编排器 step 4 case 退化为通用模板：`<step-pause registry-key="${current_state}" />`，运行时按 key 查 registry 展开
- registry 单一权威源；CI `check-step-pause-registry.sh`（PR-5 启用 error）守门 registry 与编排器一致性

## 3. 替代方案

- **方案 X**（继续硬编码）：被拒绝。理由：① 维护成本随 step-pause 数量线性增加；② 新增配置需要 XML 编辑；③ 阻碍未来生成器化。

## 4. 影响

- **协议层**：`core/core-rules.xml` `<step-pause>` 标签定义新增 `registry-key` 属性
- **编排器**：`core/workflow.xml` step 4 case 由 6 处硬编码退化为 1 处通用模板
- **CI**：`check-step-pause-registry.sh`（PR-5 启用）守门 registry 完整性
- **跨平台**：Limited / Minimal 平台需要 registry 同步注入到 system-prompt（PR-6 build-system-prompt.py 处理）

## 5. 引用

- V1.1 §3.2.10+ Stage-1（O10+ 拆分）
- v2.2 主文档 §6 D10（占位）
- v4.2 README §6 PR-5（实际落地）
- ADR-016（`<step-pause>` 必填参数表 / registry 元素 schema 复用）
