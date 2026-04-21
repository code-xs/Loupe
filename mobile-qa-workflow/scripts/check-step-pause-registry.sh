#!/usr/bin/env bash
# check-step-pause-registry.sh (v4.2 PR-5 / O10+ / O22 / SCRIPT-N1)
#
# 三类校验（V1.1 §3.2.22 / ADR-010 §4 / v1.1 Patch C 双向严格相等）：
#   ① Registry 状态名合法性 —— 抽 workflow-status-template.yaml 头部 enum 注释块；
#      registry 每个 state 必须 ∈ ENUM_SET。
#   ② Registry 双向严格相等 —— EXPECTED = 6 交互态 + Boundary-Refined（Patch A）；
#      MISSING / UNEXPECTED 各自 error。
#   ③ 硬编码 case 禁出（H3） —— 仅在 step 4a/4b/4c 区间内 grep <switch current_state>
#      / <case if="<交互态>"> / <check if="... current_state == <交互态> ..."> 三类。
#      黑名单含 Boundary-Refined（v1.1）+ Fix-Confirming（PR-6 前向兼容）。
#
# 默认 error 起步（无 warning 过渡）；任何违规 = exit 1，CI 红。

set -euo pipefail
cd "$(dirname "$0")/.."

REG="core/step-pause-registry.yaml"
XML="core/workflow.xml"
TPL="core/workflow-status-template.yaml"

fail=0
emit_error() { echo "::error::$*"; fail=1; }

# ── 前置：文件存在性 ─────────────────────────────────────────────
[ -f "$REG" ] || { emit_error "registry 文件不存在: $REG"; exit 1; }
[ -f "$XML" ] || { emit_error "编排器文件不存在: $XML"; exit 1; }
[ -f "$TPL" ] || { emit_error "状态模板文件不存在: $TPL"; exit 1; }

# ── ENUM_SET：从 workflow-status-template.yaml 头部注释块提取（与 check-state-enum.sh 同款 DRY） ──
ENUM_SET=$(python3 - "$TPL" <<'PY'
import re, sys
src = open(sys.argv[1], encoding='utf-8').read().splitlines()
collect, block = False, []
for ln in src:
    if not collect and 'v4.1 完整集合' in ln:
        collect = True
        continue
    if collect:
        if not ln.lstrip().startswith('#'):
            break
        block.append(ln)
        if 'Done' in ln:
            break
print(' '.join(sorted(set(re.findall(r'\b[A-Z][A-Za-z-]+\b', '\n'.join(block))))))
PY
)

# ── REG_STATES：从 registry 抽出所有 state（仅匹配顶层 - state: 行） ────
REG_STATES=$(python3 -c "import re; print(' '.join(re.findall(r'^\s*-\s*state:\s*([A-Za-z][A-Za-z0-9-]*)', open('$REG').read(), flags=re.M)))")

# ──────────────────────────────────────────────────────────────────
# ① state 合法性
# ──────────────────────────────────────────────────────────────────
for st in $REG_STATES; do
  echo " $ENUM_SET " | grep -q " $st " || emit_error "registry state='$st' 不在 enum 集内（参见 core/workflow-status-template.yaml 头部）"
done

# ──────────────────────────────────────────────────────────────────
# ② 拆分检测 + 双向严格相等（v1.1 / Patch C）
# ──────────────────────────────────────────────────────────────────
python3 -c "
import re, sys
src = open('$XML').read()
m = re.search(r'<step\s+n=\"4a\".*?</step>\s*<step\s+n=\"4b\".*?</step>\s*<step\s+n=\"4c\".*?</step>', src, re.S)
sys.exit(0 if m else 1)
" || emit_error "$XML 内未发现 step 4a/4b/4c 三段拆分（O10+ Stage-2 未落地）"

# v1.1：6 交互态 + 1 路由态 Boundary-Refined（Patch A）
EXPECTED="Info-Insufficient Spec-Uncertain Non-Bug RCA-LowConfidence Curation-Failed Human-Review Boundary-Refined"
EXP_SORTED=$(echo "$EXPECTED" | tr ' ' '\n' | sort -u)
REG_SORTED=$(echo "$REG_STATES" | tr ' ' '\n' | sort -u)
MISSING=$(comm -23 <(echo "$EXP_SORTED") <(echo "$REG_SORTED") || true)
UNEXPECTED=$(comm -13 <(echo "$EXP_SORTED") <(echo "$REG_SORTED") || true)
if [ -n "$MISSING" ]; then
  while IFS= read -r s; do
    [ -n "$s" ] && emit_error "registry 缺失条目（漏注册）: $s"
  done <<< "$MISSING"
fi
if [ -n "$UNEXPECTED" ]; then
  while IFS= read -r s; do
    [ -n "$s" ] && emit_error "registry 多余条目（H3 权威性 / 未审批的 demo 残留？）: $s"
  done <<< "$UNEXPECTED"
fi

# ──────────────────────────────────────────────────────────────────
# ③ 硬编码 case 禁出（仅在 step 4a/4b/4c 区间内 / v1.1 黑名单含 Boundary-Refined）
# ──────────────────────────────────────────────────────────────────
HITS=$(python3 - "$XML" <<'PY'
import re, sys
src = open(sys.argv[1], encoding='utf-8').read()
m = re.search(r'<step\s+n="4a".*?</step>\s*<step\s+n="4b".*?</step>\s*<step\s+n="4c".*?</step>', src, re.S)
if not m:
    sys.exit(0)
body = m.group(0)
hits = re.findall(r'<switch\b[^>]*current_state[^>]*>', body)
for st in ["Info-Insufficient", "Spec-Uncertain", "Non-Bug", "RCA-LowConfidence",
           "Curation-Failed", "Human-Review", "Boundary-Refined", "Fix-Confirming"]:
    hits += re.findall(rf'<case\s+if="{re.escape(st)}"\s*>', body)
    hits += re.findall(rf'<check\s+if="[^"]*current_state\s*==\s*"?{re.escape(st)}"?[^"]*"', body)
for h in hits:
    print(h)
PY
)
if [ -n "$HITS" ]; then
  while IFS= read -r ln; do
    [ -n "$ln" ] && emit_error "硬编码 case 禁出违规（H3）: $ln"
  done <<< "$HITS"
fi

# ── 总结输出 ─────────────────────────────────────────────────────
n_reg=$(echo $REG_STATES | wc -w | tr -d ' ')
if [ $fail -eq 0 ]; then
  echo "✅ 通过（registry=${n_reg} 项 / 双向严格相等 OK / 硬编码 case=0）"
fi
exit $fail
