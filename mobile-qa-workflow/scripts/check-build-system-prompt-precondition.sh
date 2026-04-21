#!/usr/bin/env bash
# check-build-system-prompt-precondition.sh (v4.2 PR-2 / O22 / H1 守门 / v1.1 锚点提取式)
# 守门：禁止 PR-2 阶段即兴运行 build-system-prompt.py --mode=full 替换 system-prompt.md
#   ① system-prompt.md 中 Spec-Uncertain 段落 allowed_values 必须保持为 1|2|S
#      （而非 core/workflow.xml 当前的 Confirm —— PR-4 O13a 完成后两者才能统一）
#   ② system-prompt.md 与 core/workflow.xml 的 Spec-Uncertain allowed_values
#      若两者一致（都是 1|2|S）说明 PR-4 已合入，可解除本守门
# 关联：V1.1 §4.1.0 H1 / 主控 §3 H1 / 主控 §4 PR-2 启用为 error
# 实现：依赖 ANCHOR-N1（system-prompt.md）+ ANCHOR-N2（core/workflow.xml）稳定锚点；缺锚点直接 error

set -euo pipefail
cd "$(dirname "$0")/.."

ANCHOR='<!-- ANCHOR: spec-uncertain-allowed-values -->'
fail=0

# ──────────────────────────────────────────────────────────
# 工具函数：按锚点定位 + 锚点后 N 行内提取首个 allowed_values=
# 设计要点：
#   · 锚点必须存在，否则 fail 并提示去 PR-2 加锚点（ANCHOR-N1/N2）
#   · 锚点后扫描窗口：默认 25 行（覆盖 step-pause 多行块 / 描述段）
#   · 提取目标：第一个 allowed_values=<TOKEN> 中的 TOKEN
#     仅识别 ASCII enum 字符 [A-Za-z0-9|]，避免吞掉后随的 `）→` 等全角字符
# ──────────────────────────────────────────────────────────
extract_after_anchor() {
  local file="$1" window="${2:-25}"
  if ! grep -qF "$ANCHOR" "$file"; then
    echo "__MISSING_ANCHOR__"
    return
  fi
  awk -v anchor="$ANCHOR" -v win="$window" '
    index($0, anchor) {hit=NR; next}
    hit && NR-hit <= win {print}
  ' "$file" | grep -oE 'allowed_values="?[A-Za-z0-9|]+"?' | head -1 \
    | sed -e 's/^allowed_values=//' -e 's/^"//' -e 's/"$//'
}

SP_SU=$(extract_after_anchor system-prompt.md)
CORE_SU=$(extract_after_anchor core/workflow.xml)

# 1) 锚点缺失硬约束
if [ "$SP_SU" = "__MISSING_ANCHOR__" ]; then
  echo "::error::system-prompt.md 缺 Spec-Uncertain 锚点（应为 '$ANCHOR'）— 见变更点 ANCHOR-N1"
  fail=1
fi
if [ "$CORE_SU" = "__MISSING_ANCHOR__" ]; then
  echo "::error::core/workflow.xml 缺 Spec-Uncertain 锚点（应为 '$ANCHOR'）— 见变更点 ANCHOR-N2"
  fail=1
fi
[ $fail -ne 0 ] && exit $fail

# 2) 锚点后无 allowed_values= 提取硬约束
if [ -z "$SP_SU" ]; then
  echo "::error::system-prompt.md 锚点后 25 行内未找到 allowed_values= 定义"
  fail=1
fi
if [ -z "$CORE_SU" ]; then
  echo "::error::core/workflow.xml 锚点后 25 行内未找到 allowed_values= 定义"
  fail=1
fi
[ $fail -ne 0 ] && exit $fail

# 3) PR-2 阶段强约束：system-prompt.md 必须为 1|2|S
if [ "$SP_SU" != "1|2|S" ]; then
  echo "::error::H1 守门违反：system-prompt.md 中 Spec-Uncertain allowed_values 应为 '1|2|S'，实际为 '$SP_SU'"
  echo "::error::原因：PR-2 阶段禁止运行 build-system-prompt.py --mode=full 替换 system-prompt.md（V1.1 §4.1.0 H1）"
  echo "::error::首次自动构建并替换由 PR-6 触发（依赖 PR-4 O13a 已合入）"
  fail=1
fi

# 4) 兜底提示：若 core/workflow.xml 也已是 1|2|S（PR-4 已合入），可在 PR-6 内解除本守门
if [ "$CORE_SU" = "1|2|S" ]; then
  echo "::notice::core/workflow.xml 中 Spec-Uncertain 已统一为 1|2|S（PR-4 O13a 已合入）；PR-6 内可解除本守门"
fi

[ $fail -eq 0 ] && echo "✅ check-build-system-prompt-precondition.sh 通过（sp=$SP_SU / core=$CORE_SU）"
exit $fail
