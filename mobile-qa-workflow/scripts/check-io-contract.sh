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

# ════════════════════════════════════════════════════════════════════════════
# === <step-pause> 互斥校验段（v4.2 PR-5 / CI-D1 / Patch B / id: step-pause-mutex）
# ════════════════════════════════════════════════════════════════════════════
# 与 core-rules.xml <tag name="step-pause"><forms> 块字面同源，强制：
#   ① form=registry：含 registry-key 且不含 title / result_field / allowed_values / option
#   ② form=inline：  含 title + result_field + allowed_values 三必填且不含 registry-key
#   ③ mutex 违规  ：同时含或同时缺 → error
# 范围：core/workflow.xml + phases/p[1-6]-*.md
# 豁免：v4.2 PR-6 起 D19 allowlist 已物理删除（FILE-D1），无任何豁免；
#       mutex 段保留作为 inline 形态回潮兜底防线（与 SCRIPT-D6 single-form 强守门互补）。
# 注释 mention 排除：与 D14/D16 同款，仅匹配 ^\s*<step-pause（行首属硬标签起始）。
# ════════════════════════════════════════════════════════════════════════════
mutex_check_file() {
  local f="$1"
  [ -f "$f" ] || return 0
  python3 - "$f" <<'PY' || return 1
import re, sys
target = sys.argv[1]

src_lines = open(target, encoding='utf-8').read().splitlines(keepends=False)
src = '\n'.join(src_lines)

# 抓"行首 <step-pause"开始，跨行直到首个未被引号包裹的 '>'（即整个开标签）
fail = 0
n_checked = 0
n_skipped_comment = 0
i = 0
while i < len(src_lines):
    line = src_lines[i]
    if not re.match(r'^\s*<step-pause\b', line):
        i += 1
        continue
    start_line = i + 1  # 1-indexed
    # 跨行收集属性区直到第一个未在引号内的 '>'
    attrs_buf = []
    j = i
    in_quote = False
    closed = False
    while j < len(src_lines):
        seg = src_lines[j]
        if j == i:
            seg = re.sub(r'^\s*<step-pause\b', '', seg, count=1)
        for ch in seg:
            if ch == '"':
                in_quote = not in_quote
            elif ch == '>' and not in_quote:
                closed = True
                break
            attrs_buf.append(ch)
        if closed:
            break
        attrs_buf.append('\n')
        j += 1
    attrs = ''.join(attrs_buf)

    # 1) 注释 mention 排除：本来 ^\s*<step-pause 已规避，但安全起见再排除一次
    if '<!--' in src_lines[max(i-1, 0)] and '-->' in src_lines[min(j+1, len(src_lines)-1)]:
        n_skipped_comment += 1
        i = j + 1
        continue

    # 2) v4.2 PR-6 起 allowlist 豁免已下线（FILE-D1 物理删除 / SCRIPT-D1 v1.1 / Fix-3）
    #    inline 形态零容忍由 SCRIPT-D6 (Check 17 / error) 单形态强守门承担；
    #    本 mutex 段降为"两形态互斥"兜底防线，防 inline 形态意外回潮。

    # 3) 形态判定
    has_reg   = bool(re.search(r'\bregistry-key\s*=', attrs))
    has_title = bool(re.search(r'\btitle\s*=', attrs))
    has_rf    = bool(re.search(r'\bresult_field\s*=', attrs))
    has_av    = bool(re.search(r'\ballowed_values\s*=', attrs))
    inline_full = has_title and has_rf and has_av
    n_checked += 1

    if has_reg and (has_title or has_rf or has_av):
        print(f"::error::step-pause-mutex-both / {target}:{start_line} / 同时含 registry-key 与 inline 字段")
        fail = 1
    elif (not has_reg) and (not inline_full):
        print(f"::error::step-pause-mutex-neither / {target}:{start_line} / 缺 registry-key 且 inline 三必填不齐 (title={has_title} result_field={has_rf} allowed_values={has_av})")
        fail = 1
    # registry-only（has_reg 且 inline 三字段全无）/ inline-full 均为合规

    i = j + 1

print(f"[mutex] {target}: checked={n_checked}, skipped_comment={n_skipped_comment}", file=sys.stderr)
sys.exit(fail)
PY
}
mutex_targets=("core/workflow.xml")
for ph in phases/p[1-6]-*.md; do
  [ -f "$ph" ] && mutex_targets+=("$ph")
done
mutex_fail=0
for t in "${mutex_targets[@]}"; do
  mutex_check_file "$t" || mutex_fail=1
done
if [ $mutex_fail -ne 0 ]; then
  fail=1
fi

# ── 总结输出（保持原 v1.1 行为）─────────────────────────────────────────────
[ $fail -eq 0 ] && echo "✅ check-io-contract.sh (v1.1 + CI-D1 step-pause-mutex) 通过（DECLARED=$(echo "$DECLARED" | wc -w | tr -d ' ') / ACTUAL=$(echo "$ACTUAL" | wc -w | tr -d ' ') / SEVERITY=$SEVERITY / mutex 段：error 起步）"
exit $fail
