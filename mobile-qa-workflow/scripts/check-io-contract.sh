#!/usr/bin/env bash
# check-io-contract.sh (v1.1)
# 守门：core/workflow.xml <io-contract> 中每个 <phase output="..."> 声明的 basename
#       必须能在某个 phase 文件的 <template-output ... file="..."> 中被实际产出
# 关联：V1.1 §3.2.22 第 3 项 / 主控 §4 PR-1 启用为 warning（PR-2 评估升级 error）
# v1.1 算法：basename 匹配模型（兼容变量化路径如 file="{output_file}" / file="{workspace_folder}/spec.md"）

set -euo pipefail
cd "$(dirname "$0")/.."

SEVERITY="${IO_CONTRACT_SEVERITY:-warning}"

# ──────────────────────────────────────────────────────────
# Step 1：从 <io-contract> 中提取每个 <phase> 的 output 属性，
#         按 ',' 拆分并清理修饰词（"可选: " / "条件必需: " / "条件生成: " 等）
# ──────────────────────────────────────────────────────────
DECLARED=$(python3 - <<'PYEOF'
import re
content = open('core/workflow.xml').read()
m = re.search(r'<io-contract\b[^>]*>(.*?)</io-contract>', content, re.S)
if not m:
    raise SystemExit("ERROR: 未找到 <io-contract> 块")
phases = re.findall(r'<phase\s+name="([^"]+)"[^>]*output="([^"]+)"', m.group(1))
basenames = set()
for _, out in phases:
    out = re.sub(r'(可选|条件必需|条件生成)\s*[:：]\s*', '', out)
    for token in out.split(','):
        token = token.strip()
        bn = re.findall(r'[\w-]+\.md', token)
        basenames.update(bn)
for b in sorted(basenames): print(b)
PYEOF
)

# ──────────────────────────────────────────────────────────
# Step 2：从所有 phase 文件 + system-prompt.md 抽取 <template-output ... file="...">
#         的 file 属性，提取其中的 basename（含变量化路径的尾段）
# ──────────────────────────────────────────────────────────
ACTUAL=$(grep -hoE '<template-output[^/]*file="[^"]+"' phases/*.md system-prompt.md 2>/dev/null \
  | sed -E 's/.*file="([^"]+)".*/\1/' \
  | sed -E 's@.*/@@' \
  | grep -oE '[A-Za-z_-]+\.md|\{[a-z_]+\}' \
  | sort -u)

# ──────────────────────────────────────────────────────────
# Step 3：对每个 DECLARED basename，要么在 ACTUAL 中直接命中，
#         要么 ACTUAL 中存在变量化路径（{output_*}）—— PR-1 阶段允许变量化路径作为 wildcard 命中
# ──────────────────────────────────────────────────────────
fail=0
HAS_VARIABLE=$(echo "$ACTUAL" | grep -c '^{' || true)
for b in $DECLARED; do
  if echo "$ACTUAL" | grep -qx "$b"; then
    continue
  fi
  if [ "$HAS_VARIABLE" -gt 0 ]; then
    echo "::notice::声明的 io-contract basename 未直接命中，但存在变量化路径兜底: $b"
    continue
  fi
  echo "::${SEVERITY}::声明的 io-contract basename 未被任何 phase 输出: $b"
  [ "$SEVERITY" = "error" ] && fail=1
done

[ $fail -eq 0 ] && echo "✅ check-io-contract.sh (v1.1) 通过（DECLARED=$(echo "$DECLARED" | wc -w | tr -d ' ') / ACTUAL=$(echo "$ACTUAL" | wc -w | tr -d ' ') / SEVERITY=$SEVERITY）"
exit $fail
