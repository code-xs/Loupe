# ADR-011: CI 起点 = `.github/workflows/qa-workflow-schema-check.yml`

> **状态**：active
> **关联决定**：D11（v2.0 附录 B 拍板）
> **关联 PR**：v4.1 PR-8（已合入）

## 1. 背景

CI 守门启用需要确定 GitHub Actions workflow 文件位置。仓库现状盘点：`.github/workflows/eval.yml` 已存在，无需新建目录。

## 2. 决定

CI 起点 = `.github/workflows/qa-workflow-schema-check.yml`，与现有 `eval.yml` 同级：
- 触发条件：仅当 SKILL 范围（`mobile-qa-workflow/**`）或本 workflow 自身改动时运行
- 不阻塞 v4.1 之前不含本 SKILL 目录的旧分支
- fail-fast：每个 step 独立失败 → 整个 job 立即失败

## 3. 替代方案

- **方案 X**（新建 `.github/workflows/qa/` 子目录）：被拒绝。理由：① 与 `eval.yml` 不一致；② GitHub Actions 默认按文件扫描，子目录无功能收益。

## 4. 影响

- **CI 文件位置**：所有 schema/protocol 守门 step 集中到本文件
- **触发路径**：`pull_request` 与 `push to main` 限定 `paths:` 过滤
- **超时**：`timeout-minutes: 5`（防意外卡死）

## 5. 引用

- v2.2 主文档 §6 D11 拍板纪要
- `.github/workflows/qa-workflow-schema-check.yml`（已落地，含 8 + 4 = 12 项守门）
