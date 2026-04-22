#!/usr/bin/env bash
# check-coder-entry.sh (v4.2 PR-7 / O11+ / §2.1 E1)
# ============================================================
# 守门：Coder SubAgent 入口唯一性 + 下游子文件只能由入口加载
#
# 立法依据（构建计划 §2.1 E1）：
#   - P5 / 任意 invoke Coder 路径：有且仅有一条 <load coder-agent.md>
#   - 禁止在同一段调用链上再单独 <load coder-workflow.md> 或
#     <load contract-checklist-spec.md>（**P6 例外**：单独 load
#     contract-checklist-spec.md 仅在 P6-only-checklist 场景允许；
#     当前 v4.2 PR-7 内主链 P6 不触发，本通路保留为 v4.3 接口）
#   - 禁止「入口与 phase 各 load 一段」的双写口径
#
# 严重度：error 起步（与 sync-core-rules-aggregate / sync-reasoning-chain-aggregate /
# check-subagent-load-target 一致；任何回流都直接挡 PR）。
#
# CI：注册为 `qa-workflow-schema-check.yml` 的 Check 22（O11+ 配套）。
# ============================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORKFLOW_ROOT="$REPO_ROOT/mobile-qa-workflow"

# 扫描范围：主链 phase + deep-dive phase + 所有 agents（除入口自身）
SCAN_DIRS=(
  "$WORKFLOW_ROOT/phases"
  "$WORKFLOW_ROOT/functionality-deep-dive/phases"
  "$WORKFLOW_ROOT/functionality-deep-dive/core"
  "$WORKFLOW_ROOT/agents"
  "$WORKFLOW_ROOT/core"
)

# 入口文件白名单（可以 <load> 子文件）
ENTRY_WHITELIST=(
  "$WORKFLOW_ROOT/agents/coder-agent.md"
)

# 下游子文件
DOWNSTREAM_FILES=(
  "agents/coder-workflow.md"
  "reference/contract-checklist-spec.md"
)

# P6 例外路径（允许单独 load contract-checklist-spec.md；当前不触发）
P6_EXCEPTION_FILE="$WORKFLOW_ROOT/phases/p6-verification.md"
P6_EXCEPTION_TARGET="reference/contract-checklist-spec.md"

violations=0

# ────────────────────────────────────────────────────────────────
# 守门 1：下游子文件只能由入口或本身（链式 load）引入
# ────────────────────────────────────────────────────────────────
for downstream in "${DOWNSTREAM_FILES[@]}"; do
  pattern="target=[\"']mobile-qa-workflow/${downstream//\//\\/}[\"']"

  # 列出所有引用该下游文件的位置
  while IFS= read -r match; do
    [[ -z "$match" ]] && continue
    file=$(echo "$match" | cut -d: -f1)
    lineno=$(echo "$match" | cut -d: -f2)

    # 入口白名单跳过
    is_entry=0
    for entry in "${ENTRY_WHITELIST[@]}"; do
      if [[ "$file" == "$entry" ]]; then
        is_entry=1
        break
      fi
    done
    [[ "$is_entry" -eq 1 ]] && continue

    # P6 例外：仅 contract-checklist-spec.md 在 p6-verification.md 内允许
    if [[ "$file" == "$P6_EXCEPTION_FILE" && "$downstream" == "$P6_EXCEPTION_TARGET" ]]; then
      echo "::notice file=phases/p6-verification.md,line=$lineno::P6 例外通路 (§2.1) 命中：单独 load contract-checklist-spec.md。当前为 v4.3 预留接口，保留通过。"
      continue
    fi

    rel="${file#$REPO_ROOT/}"
    echo "::error file=$rel,line=$lineno::禁止在 $rel 内单独 <load> $downstream；该子文件只能由 agents/coder-agent.md 入口加载（§2.1 E1）"
    violations=$((violations+1))
  done < <(grep -rEn "$pattern" "${SCAN_DIRS[@]}" 2>/dev/null || true)
done

# ────────────────────────────────────────────────────────────────
# 守门 2：入口文件必须按固定顺序 load 两个下游子文件
# ────────────────────────────────────────────────────────────────
entry="$WORKFLOW_ROOT/agents/coder-agent.md"
if [[ ! -f "$entry" ]]; then
  echo "::error::入口文件不存在：agents/coder-agent.md"
  violations=$((violations+1))
else
  workflow_line=$(grep -n "target=\"mobile-qa-workflow/agents/coder-workflow.md\"" "$entry" | head -1 | cut -d: -f1 || true)
  checklist_line=$(grep -n "target=\"mobile-qa-workflow/reference/contract-checklist-spec.md\"" "$entry" | head -1 | cut -d: -f1 || true)

  if [[ -z "$workflow_line" ]]; then
    echo "::error file=agents/coder-agent.md::入口缺失 <load coder-workflow.md>（§2.1 E1 固定顺序第 1 条）"
    violations=$((violations+1))
  fi
  if [[ -z "$checklist_line" ]]; then
    echo "::error file=agents/coder-agent.md::入口缺失 <load contract-checklist-spec.md>（§2.1 E1 固定顺序第 2 条）"
    violations=$((violations+1))
  fi
  if [[ -n "$workflow_line" && -n "$checklist_line" && "$workflow_line" -ge "$checklist_line" ]]; then
    echo "::error file=agents/coder-agent.md,line=$workflow_line::入口两条下游 <load> 顺序违例：coder-workflow.md (line $workflow_line) 必须在 contract-checklist-spec.md (line $checklist_line) 之前（§2.1 E1）"
    violations=$((violations+1))
  fi
fi

# ────────────────────────────────────────────────────────────────
# 守门 3：P5（fix-impl）必须仅 load coder-agent.md，不得绕开入口
# ────────────────────────────────────────────────────────────────
p5="$WORKFLOW_ROOT/phases/p5-fix-impl.md"
if [[ -f "$p5" ]]; then
  has_entry=$(grep -c "target=['\"]mobile-qa-workflow/agents/coder-agent.md['\"]" "$p5" || true)
  if [[ "$has_entry" -eq 0 ]]; then
    echo "::error file=phases/p5-fix-impl.md::P5 必须 <load coder-agent.md>（§2.1 E1 唯一入口）"
    violations=$((violations+1))
  fi
fi

if [[ "$violations" -gt 0 ]]; then
  echo ""
  echo "FAIL: 发现 $violations 处违例（O11+ Coder 入口唯一性 / 顺序契约）"
  exit 1
fi

echo "OK: Coder 入口唯一性守门通过（agents/coder-agent.md 是唯一入口；coder-workflow.md / contract-checklist-spec.md 仅由入口加载；固定顺序与 P5 触达均合规）"
exit 0
