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
# v4.2 PR-2 / SCRIPT-FIX1 改动 1：改用 python 严格抽取完整集合 enum 列表行
# （仅识别 "#   X / Y / Z" 形式；剔除 awk 范围式 + 宽松 PascalCase 抓取的 PRESERVE/FORMAT/SKILL/PLATFORM-GUIDE/PR- 等噪音）
# v4.2 PR-6 / SCRIPT-D2：兼容 v4.1 与 v4.2 锚点（TPL-D1 把锚点改为 v4.2 完整集合）
ENUM_CORE=$(python3 - <<'PYEOF'
import re
content = open('core/workflow-status-template.yaml').read()
m = re.search(r'v4\.[12]\s*完整集合[^\n]*\n((?:#\s+\S.*\n)+)', content)
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
# 仅取 "v4.x 完整集合" 之后那一段，避免抓到说明文字里其它 PascalCase token
# v4.2 PR-6 / SCRIPT-D2：兼容 v4.1/v4.2 锚点
body = m.group(1)
m2 = re.search(r'v4\.[12]\s*完整集合[^\n]*\n(.*)', body, re.S)
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
# 校验 2a：step-pause-registry 三元组结构化同步校验（v4.2 PR-6 起 / v1.1 / Review Finding 4-B 收口 / SCRIPT-D2）
# v4.2 PR-6 替换 ANCHOR-N1/N2 锚点扫描机制：从 core/step-pause-registry.yaml 抽取每项的
#   state + result_field + allowed_values 三元组，并断言 system-prompt.md 中对应内容完整出现。
# v1.0 方案仅 grep state 名（弱校验，存在 result_field/allowed_values 漂移时假绿风险）；
# v1.1 升级为三元组对比，与 SP-N1 由 build-system-prompt.py 生成的 routing table（GEN-D2）形成对账。
# ──────────────────────────────────────────────────────────
python3 - "$SEVERITY" <<'PY' || fail=1
import re, sys
severity = sys.argv[1]
reg = open('core/step-pause-registry.yaml', encoding='utf-8').read()
sp = open('system-prompt.md', encoding='utf-8').read()

# 抽取 registry 每项的 state + result_field + allowed_values
# （兼容 state 行尾带 inline 注释如 "state: Spec-Uncertain # PR-3'"）
items = re.findall(
    r'^\s*-\s*state:\s*([A-Za-z][A-Za-z0-9-]*)\s*(?:#[^\n]*)?\n((?:.|\n)*?)(?=^\s*-\s*state:|\Z)',
    reg, re.M
)
fail = 0
for state, body in items:
    rf_m = re.search(r'\bresult_field:\s*([^\n#]+)', body)
    av_m = re.search(r'\ballowed_values:\s*\[([^\]]+)\]', body)
    is_route = bool(re.search(r'\bkind:\s*route', body))
    rf = rf_m.group(1).strip() if rf_m else None
    av = av_m.group(1).strip() if av_m else None

    # 校验 1：state 名出现
    if state not in sp:
        print(f"::{severity}::sync-2a-state-missing / system-prompt.md 缺 registry state 引用: {state}")
        fail = 1
        continue

    if is_route:
        continue  # route 项无 result_field/allowed_values，跳过 2/3 校验

    # 校验 2：result_field 出现
    if rf and rf not in sp:
        print(f"::{severity}::sync-2a-result_field-missing / state={state} 的 result_field='{rf}' 未在 system-prompt.md 中出现（registry 三元组漂移）")
        fail = 1

    # 校验 3：allowed_values 字面出现（兼容 ["1","2","S"] / [Continue, Revise] 等多种格式）
    if av:
        tokens = [t.strip().strip('"').strip("'") for t in av.split(',')]
        for tok in tokens:
            if tok and tok not in sp:
                print(f"::{severity}::sync-2a-allowed_values-missing / state={state} 的 allowed_values token '{tok}' 未在 system-prompt.md 中出现")
                fail = 1
sys.exit(fail)
PY

# ──────────────────────────────────────────────────────────
# 校验 2b：关键 stop_state 必须出现 ≥ 1 次（v4.2 PR-6 起加入 Fix-Confirming）
# ──────────────────────────────────────────────────────────
for state in "Non-Bug" "RCA-LowConfidence" "Curation-Failed" "Human-Review" "Fix-Confirming"; do
  if ! grep -q "$state" system-prompt.md; then
    echo "::${SEVERITY}::system-prompt.md 缺关键 stop_state 引用: $state"
    [ "$SEVERITY" = "error" ] && fail=1
  fi
done

[ $fail -eq 0 ] && echo "✅ check-system-prompt-sync.sh (v1.1) 通过（severity=$SEVERITY）"
exit $fail
