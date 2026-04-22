#!/usr/bin/env bash
# mobile-qa-workflow/scripts/check-config-schema.sh
# 用途（M16 / 主文档 §3 PR-8 评审重点 7 / §5.1 第 5 项）：
#   扫描 phases 中所有 "更新 ... config_source ... <key> = ..." 动作，
#   校验 <key> 必须在 core/config-schema.yaml allowed_keys 内。
#
# 退出码：
#   0 = 全部 config_source 写入键已注册
#   1 = 至少一个未注册键 / schema 文件缺失 / scan 目录缺失
#
# 设计：仅依赖 bash + grep + awk + sed（无 PyYAML 依赖，便于 CI 上零依赖运行）

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCHEMA="${ROOT}/mobile-qa-workflow/core/config-schema.yaml"
SCAN_DIRS=(
    "${ROOT}/mobile-qa-workflow/phases"
    "${ROOT}/mobile-qa-workflow/functionality-deep-dive/phases"
)

if [ ! -f "$SCHEMA" ]; then
    echo "[M16-FAIL] config-schema.yaml not found at: $SCHEMA" >&2
    exit 1
fi
for d in "${SCAN_DIRS[@]}"; do
    if [ ! -d "$d" ]; then
        echo "[M16-FAIL] scan dir missing: $d" >&2
        exit 1
    fi
done

# 1. 解析 allowed_keys（仅取 "  - <name>" 行；忽略 nested_/known_legacy_ 与注释/空行）
ALLOWED=$(awk '
    /^allowed_keys:/                     {in_block=1; next}
    /^[a-zA-Z_]/                         {in_block=0}
    in_block && /^[[:space:]]*-[[:space:]]+[a-z_]/ {
        sub(/^[[:space:]]*-[[:space:]]+/, "", $0)
        sub(/[[:space:]]*#.*$/, "", $0)
        print
    }
' "$SCHEMA" | sort -u)

if [ -z "$ALLOWED" ]; then
    echo "[M16-FAIL] failed to parse allowed_keys from $SCHEMA" >&2
    exit 1
fi

# 2. 扫描 phases，提取所有 "更新 ... config_source ... <key> = ..." 写入动作
#    支持两种语法：
#      a)  更新 {config_source}：<key> = ...
#      b)  更新 {config_source}：<k1> = v1, <k2> = v2, ...（多键）
fail=0
seen_keys=""

while IFS=: read -r f ln content; do
    # 仅在 content 含 "config_source" 时继续（grep -E 命中保险一次）
    echo "$content" | grep -q 'config_source' || continue

    # 抽取 "config_source" 之后所有形如 " <key> =" 的 token（key 必须以小写字母/下划线开头）
    keys=$(echo "$content" \
        | sed -E 's/.*config_source[^：:]*[：:]//' \
        | grep -oE '[a-z][a-z0-9_]*[[:space:]]*=' \
        | sed -E 's/[[:space:]]*=$//' \
        | sort -u || true)

    if [ -z "$keys" ]; then
        continue
    fi

    for k in $keys; do
        seen_keys="${seen_keys}
${k}"
        if ! echo "$ALLOWED" | grep -qx "$k"; then
            echo "[M16-FAIL] $f:$ln unknown config_source key: $k"
            fail=1
        fi
    done
done < <(grep -rnE '更新.*config_source' "${SCAN_DIRS[@]}" 2>/dev/null || true)

# 3. v4.2 PR-6 / SCRIPT-D7（v1.1 / Fix-6）：覆盖 <phase-complete>/<phase-abort> 宏 update_config 属性的 key 校验
#    宏属性 update_config='{"k1": "...", "k2": "..."}' 的顶层 key 等价于"更新 {config_source}：k = ..."
#    若仅扫描显式文本，宏 key 会成为 M16 校验盲区。
macro_keys=$(python3 - "${SCAN_DIRS[@]}" <<'PY'
import json, os, re, sys
roots = sys.argv[1:]
out = []  # (file, lineno, key)
pattern = re.compile(
    r"<phase-(?:abort|complete)\b([^>]*?)/?>",
    re.DOTALL,
)
for root in roots:
    if not os.path.isdir(root):
        continue
    for dirpath, _, files in os.walk(root):
        for name in files:
            if not name.endswith(".md"):
                continue
            path = os.path.join(dirpath, name)
            try:
                src = open(path, encoding="utf-8").read()
            except Exception:
                continue
            for m in pattern.finditer(src):
                attrs = m.group(1)
                u = re.search(r"update_config\s*=\s*'([^']*)'", attrs)
                if not u:
                    continue
                line_no = src.count("\n", 0, m.start()) + 1
                try:
                    obj = json.loads(u.group(1))
                except Exception:
                    print(f"__PARSE_FAIL__\t{path}\t{line_no}\t{u.group(1)}")
                    continue
                if isinstance(obj, dict):
                    for k in obj.keys():
                        print(f"{path}\t{line_no}\t{k}")
PY
)

if [ -n "$macro_keys" ]; then
    while IFS=$'\t' read -r path line k; do
        [ -z "$path" ] && continue
        if [ "$path" = "__PARSE_FAIL__" ]; then
            echo "[M16-FAIL] $line:$k macro update_config JSON 解析失败"
            fail=1
            continue
        fi
        seen_keys="${seen_keys}
${k}"
        if ! echo "$ALLOWED" | grep -qx "$k"; then
            echo "[M16-FAIL] $path:$line unknown macro update_config key: $k"
            fail=1
        fi
    done <<< "$macro_keys"
fi

if [ "$fail" -eq 0 ]; then
    n_seen=$(printf '%s\n' "$seen_keys" | grep -v '^$' | sort -u | wc -l | tr -d ' ')
    echo "[M16-OK] all ${n_seen} config_source write keys registered in config-schema.yaml"
fi

exit "$fail"
