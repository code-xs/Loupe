#!/usr/bin/env bash
# check-system-prompt-sync.sh (v1.1)
# 守门：system-prompt.md 与 core/ 关键 token 必须同步
# 关联：V1.1 §3.1 O5 配套 / 主控 §4 PR-1 启用为 warning，PR-2 升级为 error
# v1.1 算法：声明块对声明块 + 高风险 token 白名单

set -euo pipefail
cd "$(dirname "$0")/.."

SEVERITY="${SP_SYNC_SEVERITY:-warning}"
fail=0

# ──────────────────────────────────────────────────────────
# 校验 1：ENUM 声明块严格相等
# 提取 system-prompt.md 中 <!-- ENUM-DECLARATION-BLOCK --> ... <!-- /ENUM-DECLARATION-BLOCK -->
# 内的状态名集合，与 core/workflow-status-template.yaml 头部 enum 集做集合相等比对
# ──────────────────────────────────────────────────────────
ENUM_CORE=$(awk '/v4.1 完整集合/,/^[^#]/' core/workflow-status-template.yaml \
  | grep -oE '[A-Z][A-Za-z-]+' | sort -u)

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
# 2a)
SU_CORE=$(grep -oE 'allowed_values=[^"]*' core/workflow.xml | head -1 || echo "")
SU_SP=$(grep -oE 'allowed_values=[^"]*' system-prompt.md | head -1 || echo "")
if [ -n "$SU_CORE" ] && [ -n "$SU_SP" ] && [ "$SU_CORE" != "$SU_SP" ]; then
  echo "::${SEVERITY}::Spec-Uncertain allowed_values 字面不一致 (core: $SU_CORE / sp: $SU_SP)"
  [ "$SEVERITY" = "error" ] && fail=1
fi

# 2b)
for state in "Non-Bug" "RCA-LowConfidence" "Curation-Failed" "Human-Review"; do
  if ! grep -q "$state" system-prompt.md; then
    echo "::${SEVERITY}::system-prompt.md 缺关键 stop_state 引用: $state"
    [ "$SEVERITY" = "error" ] && fail=1
  fi
done

[ $fail -eq 0 ] && echo "✅ check-system-prompt-sync.sh (v1.1) 通过（severity=$SEVERITY）"
exit $fail
