#!/usr/bin/env bash
# check-subagent-load-target.sh (v4.2 PR-7 / O25 / §2.2 / §3.5)
# ============================================================
# 守门：phases/{p3,p4,p5}.md + functionality-deep-dive/phases/{f1..f5}.md
#       的 invoke-subagent.subagent_prompt 内必须 load
#       `core/core-rules-subagent.xml`（O25 Full 平台轻量化路径），
#       禁止再 load 完整 `core/core-rules.xml`。
#
# 立法依据：
#   - 施工单 §2.2：Full 平台 invoke-subagent 必须用 core-rules-subagent.xml
#   - 施工单 §3.5：O25 替换 phases/p3/p4/p5 + deep-dive f1-f5 内的 load
#   - §A.1 触达表：本脚本守门 §A.1 标记 "O25 命中" 的 14+6 = 20 处
#
# 排除：
#   - phases/p2-spec-definition.md L128（curator subagent，按 §A 走 essential，
#     非 O25 范围；该处 essential 改造由后续小段提交承担，与本守门无冲突）
#   - phase 首步 `<load target="...core-rules.xml" ...>` 双引号形态（属
#     phase 主对话上下文，O23 essential 改造由后续小段提交承担）
#
# 严重度：error 起步（与 sync-core-rules-aggregate / sync-reasoning-chain-aggregate
# 一致；任何回流都直接挡 PR）。
#
# CI：注册为 `qa-workflow-schema-check.yml` 的 Check 21（O25 配套）。
# ============================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORKFLOW_ROOT="$REPO_ROOT/mobile-qa-workflow"

PHASES_O25=(
  "phases/p3-root-cause.md"
  "phases/p4-fix-design.md"
  "phases/p5-fix-impl.md"
  "functionality-deep-dive/phases/f1-context-reconstruction.md"
  "functionality-deep-dive/phases/f2-state-topology.md"
  "functionality-deep-dive/phases/f3-temporal-correlation.md"
  "functionality-deep-dive/phases/f4-isolation-debate.md"
  "functionality-deep-dive/phases/f5-defensive-fix-design.md"
)

# 期望命中数（与 §A.1 一致）：p3=6, p4=7, p5=1, f1=1, f2=1, f3=1, f4=2, f5=1 → 20
EXPECTED_TOTAL=20

violations=0
total_subagent=0

for rel in "${PHASES_O25[@]}"; do
  f="$WORKFLOW_ROOT/$rel"
  if [[ ! -f "$f" ]]; then
    echo "::error file=$rel::文件不存在"
    violations=$((violations+1))
    continue
  fi

  # 单引号形态 = invoke-subagent.subagent_prompt 内 load
  bad=$(grep -n "target='mobile-qa-workflow/core/core-rules\.xml'" "$f" || true)
  if [[ -n "$bad" ]]; then
    while IFS= read -r line; do
      lineno="${line%%:*}"
      echo "::error file=$rel,line=$lineno::invoke-subagent 内不得 load 完整 core-rules.xml；请改 core-rules-subagent.xml（O25 / §2.2）"
      violations=$((violations+1))
    done <<<"$bad"
  fi

  cnt=$(grep -c "target='mobile-qa-workflow/core/core-rules-subagent\.xml'" "$f" || true)
  total_subagent=$((total_subagent + cnt))
done

if [[ "$total_subagent" -ne "$EXPECTED_TOTAL" ]]; then
  echo "::error::core-rules-subagent.xml 在 8 个 O25 phase 文件中命中数 = $total_subagent，期望 = $EXPECTED_TOTAL"
  echo "  若新增 / 删除了 invoke-subagent，请同步更新 EXPECTED_TOTAL（脚本顶部）+ 施工单 §A.1。"
  violations=$((violations+1))
fi

# 排除项自检：p2 L128 必须仍是完整 core-rules.xml（守住"essential 由后续小段提交"边界）
p2="$WORKFLOW_ROOT/phases/p2-spec-definition.md"
if ! grep -q "target='mobile-qa-workflow/core/core-rules\.xml'" "$p2"; then
  echo "::error file=phases/p2-spec-definition.md::按 §A.1 设计，invoke curator 内 load 应保留为 core-rules.xml（待后续 essential 小段提交改造）；当前未命中表示已被错误改造，请回滚或更新本脚本与施工单。"
  violations=$((violations+1))
fi

if [[ "$violations" -gt 0 ]]; then
  echo ""
  echo "FAIL: 发现 $violations 处违例（O25 invoke-subagent 内 core-rules.xml 路径合规性）"
  exit 1
fi

echo "OK: 8 个 O25 phase 文件中 invoke-subagent 内全部 load core-rules-subagent.xml ($total_subagent / $EXPECTED_TOTAL)；p2 L128 essential 边界保持。"
exit 0
