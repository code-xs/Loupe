#!/usr/bin/env bash
# check-system-prompt-sync.sh (v1.1)
# 守门：system-prompt.md 与 core/ 关键 token 必须同步
# 关联：V1.1 §3.1 O5 配套 / 主控 §4 PR-1 启用为 warning，PR-2 升级为 error
# v1.1 算法：声明块对声明块 + 高风险 token 白名单

set -euo pipefail
cd "$(dirname "$0")/.."

SEVERITY="${SP_SYNC_SEVERITY:-error}"  # v4.2 PR-2 / CI-U1b：升级默认 warning → error（前置：SCRIPT-FIX1 + ANCHOR-N1/N2 实跑零 warning）
fail=0

# ──────────────────────────────────────────────────────────
# 校验 1：ENUM 声明块严格相等
# 提取 system-prompt.md 中 <!-- ENUM-DECLARATION-BLOCK --> ... <!-- /ENUM-DECLARATION-BLOCK -->
# 内的状态名集合，与 core/workflow-status-template.yaml 头部 enum 集做集合相等比对
# ──────────────────────────────────────────────────────────
# v4.2 PR-2 / SCRIPT-FIX1 改动 1：改用 python 严格抽取 v4.1 完整集合 enum 列表行
# （仅识别 "#   X / Y / Z" 形式；剔除 awk 范围式 + 宽松 PascalCase 抓取的 PRESERVE/FORMAT/SKILL/PLATFORM-GUIDE/PR- 等噪音）
ENUM_CORE=$(python3 - <<'PYEOF'
import re
content = open('core/workflow-status-template.yaml').read()
m = re.search(r'v4\.1\s*完整集合[^\n]*\n((?:#\s+\S.*\n)+)', content)
if not m:
    print('__MISSING__')
    raise SystemExit(0)
states = []
for line in m.group(1).splitlines():
    body = re.sub(r'^#\s+', '', line)
    if '/' not in body:
        continue
    states += [s.strip() for s in body.split('/')]
states = sorted({s for s in states if re.fullmatch(r'[A-Z][A-Za-z-]+', s)})
for s in states: print(s)
PYEOF
)

ENUM_SP=$(python3 - <<'PYEOF'
import re, sys
content = open('system-prompt.md').read()
m = re.search(r'<!-- ENUM-DECLARATION-BLOCK -->(.*?)<!-- /ENUM-DECLARATION-BLOCK -->', content, re.S)
if not m:
    print('__MISSING__'); sys.exit(0)
# 仅取 "v4.1 完整集合" 之后那一段，避免抓到说明文字里其它 PascalCase token
body = m.group(1)
m2 = re.search(r'v4\.1\s*完整集合[^\n]*\n(.*)', body, re.S)
text = m2.group(1) if m2 else body
names = re.findall(r'\b([A-Z][A-Za-z-]+)\b', text)
states = sorted(set(n for n in names if not any(c.isdigit() for c in n)))
for s in states: print(s)
PYEOF
)

if [ "$ENUM_SP" = "__MISSING__" ]; then
  echo "::${SEVERITY}::system-prompt.md 缺少 ENUM-DECLARATION-BLOCK 注释块（v1.1 PR-1 SP-H1 落地后必须存在）"
  [ "$SEVERITY" = "error" ] && fail=1
elif [ "$ENUM_CORE" != "$ENUM_SP" ]; then
  echo "::${SEVERITY}::ENUM-DECLARATION-BLOCK 与 core/workflow-status-template.yaml 头部 enum 集不一致"
  echo "core 独有: $(comm -23 <(echo "$ENUM_CORE") <(echo "$ENUM_SP") | tr '\n' ' ')"
  echo "sp 独有:   $(comm -13 <(echo "$ENUM_CORE") <(echo "$ENUM_SP") | tr '\n' ' ')"
  [ "$SEVERITY" = "error" ] && fail=1
fi

# ──────────────────────────────────────────────────────────
# 校验 2：高风险 token 白名单（PR-1 阶段兜底，PR-2 全量声明块比对后可降为可选）
# 2a) Spec-Uncertain allowed_values：当前 main 是 Confirm（v3 残留），PR-4 改为 1|2|S
#     PR-1 阶段不强校验取值，但要求 system-prompt.md 与 core/workflow.xml 出现的取值"字面一致"
# 2b) 关键 stop_state：Non-Bug / RCA-LowConfidence / Curation-Failed / Human-Review 必须在 system-prompt.md 中至少出现 1 次（基本完整性）
# ──────────────────────────────────────────────────────────
# 2a) v4.2 PR-2 / SCRIPT-FIX1 改动 2：依赖 ANCHOR-N1/N2 稳定锚点定位（窗口式扫描）
# 实现要点（与 check-build-system-prompt-precondition.sh 的 extract_after_anchor 对称）：
#   · 缺锚点直接 fail（severity 决定 warning/error）
#   · 锚点后窗口 25 行（覆盖 core/workflow.xml 的 step-pause 多行块；sp 段单行已足够）
#   · regex 仅识别 ASCII enum 字符 [A-Za-z0-9|]，避免吞掉 sp 段后面的 `）→` 全角字符
ANCHOR_LINE='<!-- ANCHOR: spec-uncertain-allowed-values -->'
extract_after_anchor() {
  local file="$1" window="${2:-25}"
  if ! grep -qF "$ANCHOR_LINE" "$file"; then
    echo "__MISSING_ANCHOR__"
    return
  fi
  awk -v anchor="$ANCHOR_LINE" -v win="$window" '
    index($0, anchor) {hit=NR; next}
    hit && NR-hit <= win {print}
  ' "$file" | grep -oE 'allowed_values="?[A-Za-z0-9|]+"?' | head -1 \
    | sed -e 's/^allowed_values=//' -e 's/^"//' -e 's/"$//'
}
SU_CORE=$(extract_after_anchor core/workflow.xml)
SU_SP=$(extract_after_anchor system-prompt.md)
if [ "$SU_CORE" = "__MISSING_ANCHOR__" ] || [ "$SU_SP" = "__MISSING_ANCHOR__" ]; then
  echo "::${SEVERITY}::Spec-Uncertain ANCHOR 缺失（core: '$SU_CORE' / sp: '$SU_SP'）— 见 ANCHOR-N1/N2"
  [ "$SEVERITY" = "error" ] && fail=1
elif [ -z "$SU_CORE" ] || [ -z "$SU_SP" ]; then
  echo "::${SEVERITY}::Spec-Uncertain 锚点窗口内未提取到 allowed_values（core: '$SU_CORE' / sp: '$SU_SP'）"
  [ "$SEVERITY" = "error" ] && fail=1
fi
# 注：core 与 sp 的 allowed_values 在 PR-2 阶段允许不同（core=Confirm / sp=1|2|S）；
# 字面一致性的强约束由 check-build-system-prompt-precondition.sh（H1 守门）单独承担。
# 本脚本只校验"两侧锚点窗口都能提取到 allowed_values"，不再做字面相等判定。

# 2b)
for state in "Non-Bug" "RCA-LowConfidence" "Curation-Failed" "Human-Review"; do
  if ! grep -q "$state" system-prompt.md; then
    echo "::${SEVERITY}::system-prompt.md 缺关键 stop_state 引用: $state"
    [ "$SEVERITY" = "error" ] && fail=1
  fi
done

[ $fail -eq 0 ] && echo "✅ check-system-prompt-sync.sh (v1.1) 通过（severity=$SEVERITY）"
exit $fail
