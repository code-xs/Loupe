#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SKILL_ID="mobile-qa-workflow"
FORCE_RELINK="${FORCE_RELINK:-0}"
TARGET="cursor"

print_help() {
    cat <<EOF
Usage: bash mobile-qa-workflow/install.sh [--target=cursor|trae|both] [--force]

Install ${SKILL_ID} into Cursor and/or Trae by creating symlinks.

Options:
  --target=<x>   Install target. One of: cursor (default), trae, both.
                 Equivalent legacy entry: bash mobile-qa-workflow/install_trae.sh
                 (now a thin shim that calls this script with --target=trae)
  --force        Replace an existing physical directory at the install path.
  -h, --help     Show this help message and exit.

Examples:
  bash mobile-qa-workflow/install.sh                     # install for Cursor (default)
  bash mobile-qa-workflow/install.sh --target=trae       # install for Trae
  bash mobile-qa-workflow/install.sh --target=both       # install for both Cursor and Trae
  bash mobile-qa-workflow/install.sh --target=both --force
EOF
}

for arg in "$@"; do
    case "$arg" in
        --force)
            FORCE_RELINK=1
            ;;
        --target=cursor|--target=trae|--target=both)
            TARGET="${arg#--target=}"
            ;;
        --target=*)
            echo "Unknown --target value: ${arg#--target=}; expected cursor|trae|both" >&2
            exit 1
            ;;
        -h|--help)
            print_help
            exit 0
            ;;
        *)
            echo "Unknown argument: $arg" >&2
            print_help >&2
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
  bash mobile-qa-workflow/install.sh --target=${TARGET} --force
EOF
            exit 1
        fi
        rm -rf "$link_path"
    fi

    ln -s "$SCRIPT_DIR" "$link_path"
    echo "✓ Linked → $link_path"
}

install_one_target() {
    local label="$1"
    local subdir="$2"

    echo "Installing ${SKILL_ID} for ${label}..."
    echo ""

    create_symlink "${PROJECT_ROOT}/${subdir}"
    create_symlink "${HOME}/${subdir}"

    echo ""
    echo "Done. 请在 ${label} 中开启新对话以激活 Skill。"
}

case "$TARGET" in
    cursor)
        install_one_target "Cursor" ".cursor/skills"
        ;;
    trae)
        install_one_target "Trae" ".trae/skills"
        ;;
    both)
        install_one_target "Cursor" ".cursor/skills"
        echo ""
        install_one_target "Trae" ".trae/skills"
        ;;
esac
