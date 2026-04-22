#!/usr/bin/env bash
# check-step-pause-form.sh (v4.2 PR-6 v1.1 新增 / Review Finding 4-A 收口 / SCRIPT-D6)
# 守门：v4.2 PR-6 起 <step-pause> 唯一合法形态 = registry-only
#       （含 registry-key 且不含 title / result_field / allowed_values / option）
# 范围：core/workflow.xml + phases/p[1-6]-*.md + functionality-deep-dive/phases/**
# 严重度：error 起步（与 SCRIPT-D1 mutex 兜底防线互补）
# 关联：ADR-016 v4.2 修订段 #2 / RULES-D3 / 主文档 §2.6.3 / Review Finding 4-A
set -euo pipefail
cd "$(dirname "$0")/.."

SEVERITY="${STEP_PAUSE_FORM_SEVERITY:-error}"
fail=0

scan_file() {
  local f="$1"
  [ -f "$f" ] || return 0
  python3 - "$f" "$SEVERITY" <<'PY' || return 1
import re, sys
target, severity = sys.argv[1], sys.argv[2]
src = open(target, encoding='utf-8').read().splitlines(keepends=False)
fail = 0
i = 0
while i < len(src):
    if not re.match(r'^\s*<step-pause\b', src[i]):
        i += 1; continue
    start = i + 1
    j = i; in_q = False; closed = False; buf = []
    while j < len(src):
        seg = src[j]
        if j == i:
            seg = re.sub(r'^\s*<step-pause\b', '', seg, count=1)
        for ch in seg:
            if ch == '"': in_q = not in_q
            elif ch == '>' and not in_q: closed = True; break
            buf.append(ch)
        if closed: break
        buf.append('\n'); j += 1
    attrs = ''.join(buf)
    has_reg = bool(re.search(r'\bregistry-key\s*=', attrs))
    has_inline = bool(re.search(r'\b(title|result_field|allowed_values|option)\s*=', attrs))
    if not has_reg:
        print(f"::{severity}::step-pause-no-registry / {target}:{start} / 缺 registry-key（v4.2 PR-6 起 inline 形态已退役 / ADR-016 v4.2 修订段 #2）")
        fail = 1
    elif has_inline:
        print(f"::{severity}::step-pause-mixed-form / {target}:{start} / 含 registry-key 时禁止同时含 title/result_field/allowed_values/option")
        fail = 1
    i = j + 1
sys.exit(fail)
PY
}

targets=("core/workflow.xml")
for ph in phases/p[1-6]-*.md; do [ -f "$ph" ] && targets+=("$ph"); done
if [ -d functionality-deep-dive/phases ]; then
  for ph in functionality-deep-dive/phases/*.md; do [ -f "$ph" ] && targets+=("$ph"); done
fi
for t in "${targets[@]}"; do
  scan_file "$t" || fail=1
done
[ $fail -eq 0 ] && echo "✅ check-step-pause-form.sh 通过（registry 单形态 / 全仓零 inline 残留）"
exit $fail
