# ADR-012: `install_trae.sh` 改为 shim 调用

> **状态**：active
> **关联决定**：D12（v2.0 附录 B 拍板）
> **关联 PR**：v4.1 PR-7（已合入）

## 1. 背景

历史上 `install_trae.sh` 与 `install.sh` 两份独立脚本并行维护，逻辑严重重复。需要收敛但不能破坏既有 `bash install_trae.sh` 调用习惯。

## 2. 决定

`install_trae.sh` 改为 shim：
```bash
#!/usr/bin/env bash
exec install.sh --target=trae "$@"
```
- 最大向后兼容：旧调用 `bash install_trae.sh` 仍工作
- 实际逻辑在 `install.sh` 单点维护
- v4.2 / v4.3 可直接删除该 shim（届时调用方需迁移到 `install.sh --target=trae`）

## 3. 替代方案

- **方案 X**（直接删 `install_trae.sh`）：被拒绝。理由：破坏既有调用习惯，需要全员通知。

## 4. 影响

- **CLI 体验**：旧用户无感
- **维护成本**：单点维护
- **未来删除**：v4.3 ADR-020 评估时机

## 5. 引用

- v2.2 主文档 §6 D12 拍板纪要
