#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SKILL_ID="mobile-qa-workflow"

create_symlink() {
    local target_dir="$1"
    local link_path="${target_dir}/${SKILL_ID}"

    mkdir -p "$target_dir"

    if [ -L "$link_path" ]; then
        rm "$link_path"
    elif [ -d "$link_path" ]; then
        rm -rf "$link_path"
    fi

    ln -s "$SCRIPT_DIR" "$link_path"
    echo "✓ Linked → $link_path"
}

echo "Installing ${SKILL_ID} for Trae..."
echo ""

# 1. 项目级 Skill（当前工程 .trae/skills/）
create_symlink "${PROJECT_ROOT}/.trae/skills"

# 2. 个人级 Skill（~/.trae/skills/，跨项目可用）
create_symlink "${HOME}/.trae/skills"

echo ""
echo "Done. 请在 Trae 中开启新对话以激活 Skill。"
