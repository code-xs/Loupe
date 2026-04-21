# ADR-013: 迁移脚本路径锁定 `mobile-qa-workflow/scripts/migrate-workflow-status-v3-to-v4.py`

> **状态**：active
> **关联决定**：D13（v2.0 附录 B 拍板）
> **关联 PR**：v4.1 PR-1（已合入）

## 1. 背景

v3 → v4 迁移脚本需要分发给所有用户。曾讨论几个路径：① 仓库根目录 `scripts/`；② SKILL 目录内 `mobile-qa-workflow/scripts/`；③ 独立 npm/pip 包。

## 2. 决定

迁移脚本路径锁定：`mobile-qa-workflow/scripts/migrate-workflow-status-v3-to-v4.py`
- 随 SKILL 自包含分发（用户 `bash install.sh` 后即拥有迁移能力）
- 与 `legacy-phase-step-pause-allowlist.txt`（D19）等其他 SKILL 工具同目录
- CI 守门 `Check 5 — 迁移脚本存在性`（已落地）固定该路径

## 3. 替代方案

- **方案 X**（仓库根 `scripts/`）：被拒绝。理由：用户 install 时不携带，需要额外下载步骤。
- **方案 Y**（独立包）：被拒绝。理由：分发链路过长，CI 守门难度增加。

## 4. 影响

- **CI**：`Check 5` 固定路径检测
- **PLATFORM-GUIDE.md / SKILL.md / system-prompt.md**：3 处入口文档的迁移引导文本固定该路径
- **未来重命名**：需要同步本 ADR + 3 处入口文档 + CI 守门

## 5. 引用

- v2.2 主文档 §6 D13 拍板纪要
- `mobile-qa-workflow/scripts/migrate-workflow-status-v3-to-v4.py`（已落地）
