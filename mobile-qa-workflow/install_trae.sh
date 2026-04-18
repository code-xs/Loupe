#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SKILL_ID="mobile-qa-workflow"
FORCE_RELINK="${FORCE_RELINK:-0}"

for arg in "$@"; do
    case "$arg" in
        --force)
            FORCE_RELINK=1
            ;;
        -h|--help)
            cat <<EOF
Usage: bash mobile-qa-workflow/install_trae.sh [--force]

Install ${SKILL_ID} into Trae by creating symlinks.

Options:
  --force    Replace an existing physical directory at the install path.
EOF
            exit 0
            ;;
        *)
            echo "Unknown argument: $arg" >&2
            exit 1
            ;;
    esac
done

create_symlink() {
    local target_dir="$1"
    local link_path="${target_dir}/${SKILL_ID}"

    mkdir -p "$target_dir"

    if [ -L "$link_path" ]; then
        rm "$link_path"
    elif [ -d "$link_path" ]; then
        if [ "$FORCE_RELINK" != "1" ]; then
            cat <<EOF
Detected an existing physical directory at:
  $link_path

This installer keeps the repository source-of-truth in:
  $SCRIPT_DIR

To avoid deleting local changes by accident, the installer will not replace
the directory automatically. Re-run with --force after you confirm it is safe
to remove the directory:
  bash mobile-qa-workflow/install_trae.sh --force
EOF
            exit 1
        fi
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
