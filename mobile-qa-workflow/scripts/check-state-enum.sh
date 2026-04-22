#!/usr/bin/env bash
# check-state-enum.sh
# 守门：current_state 写入值必须落在 workflow-status-template.yaml 头部 enum 集内
# 关联：V1.1 §3.1 O5 配套 / §3.2.22 / 主控 §4 PR-1 启用
# 等级：error（PR-1 启用即生效）

set -euo pipefail
cd "$(dirname "$0")/.."

ENUM_FILE="core/workflow-status-template.yaml"
ALLOWED=$(awk '/v4\.[12] 完整集合/,/^[^#]/' "$ENUM_FILE" \
  | grep -oE '[A-Z][A-Za-z-]+' | sort -u)

HITS=$(grep -rEn 'current_state\s*=\s*[A-Z][A-Za-z-]+' \
  phases/ system-prompt.md core/workflow.xml 2>/dev/null \
  | sed -E 's/.*current_state[[:space:]]*=[[:space:]]*([A-Z][A-Za-z-]+).*/\1/' | sort -u)

fail=0
for v in $HITS; do
  if ! echo "$ALLOWED" | grep -qx "$v"; then
    echo "::error::非法 current_state 写入: $v（不在 $ENUM_FILE 头部 enum 集内）"
    fail=1
  fi
done

[ $fail -eq 0 ] && echo "✅ check-state-enum.sh 通过（HITS=$(echo "$HITS" | wc -w | tr -d ' ') / ALLOWED=$(echo "$ALLOWED" | wc -w | tr -d ' ')）"
exit $fail
