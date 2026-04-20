#!/usr/bin/env bash
# DEPRECATED：v4.1 起已合并到 install.sh，本 shim 维持向后兼容。
# v4.2 D12 / 主文档 §1.2.2 v4.2 遗留 #5：用户群完成迁移到
# `install.sh --target=trae` 后直接删除本文件。
set -euo pipefail
exec bash "$(dirname "${BASH_SOURCE[0]}")/install.sh" --target=trae "$@"
