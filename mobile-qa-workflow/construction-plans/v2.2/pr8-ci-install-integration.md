# PR-8 · CI + install 整合（精简施工单 v1）

> **施工单层级**：精简单（200-400 行；无 v1/v2 多版本）
> **base 分支**：`feat/qa-workflow-v4.1-pr7-docs-entry-sync`（HEAD = `80ed5cd`）
> **本 PR 分支**：`feat/qa-workflow-v4.1-pr8-ci-install-integration`
> **撰写日期**：2026-04-20
> **Reviewer**：Mobile QA Workflow PR-Reviewer
> **预算**：0.43d（v2.2 D19 CI 接线 +0.03d 已含；主文档 §3 PR-8 / §1.1.3）
> **范围标签**：🟢 工程化层 / CI 守门 / install 合并（**不动协议、phase、agents、模板**）

---

## 1. 元信息

### 1.1 与主文档锚点对照

| 主文档锚点 | 本 PR 承担动作 |
|---|---|
| §3 PR-8 段落（涉及文件 / 评审重点 7 项） | 全量承担；评审重点 1-7 → §3.A CI 检查 1-7；§5.1 第 12 项 D18 → §3.A 检查 8 |
| §5.1 第 5/9/10/11/12/13/14/16 项静态校验 | CI 落地为 fail-fast 守门 |
| §5.3 / §7.8 回滚预案 | §6 引用，不重复展开 |
| 附录 C D11 / D12 / D13 / D14 / D15 / D16 / D18 / D19 | 全量遵循；不引入新决定 |

### 1.2 涉及文件清单（实际路径以仓库 `git ls-files` 为准）

> ⚠️ 主文档 §3 PR-8 表述 `install.sh` / `install_trae.sh` 在"仓库根"为口径性概念；**实际物理路径在 `mobile-qa-workflow/install.sh` 与 `mobile-qa-workflow/install_trae.sh`**（PR-1~7 base 上即如此）。本 PR 按实际路径施工，主文档 §3 PR-8 表述无需联动改动（仅"涉及文件清单"由本子文档给出权威列表）。

| # | 文件 | 动作 | 行数预估 | 来源决定 |
|---|---|---|---|---|
| 1 | `mobile-qa-workflow/install.sh` | 修改：新增 `--target=cursor\|trae\|both` 参数 | 现 74 行 → 约 110 行 | D12 |
| 2 | `mobile-qa-workflow/install_trae.sh` | 改为 shim：`exec install.sh --target=trae "$@"` | 现 74 行 → 5 行 | D12 / v4.2 遗留 #5 删除 |
| 3 | `.github/workflows/qa-workflow-schema-check.yml` | **新增**：8 项守门 fail-fast workflow | 约 90 行 | D11 |
| 4 | `mobile-qa-workflow/scripts/check-config-schema.sh` | **新增**：M16 配置键漂移检测脚本（可独立本地运行） | 约 70 行 | D13 同址 / M16 |
| 5 | `mobile-qa-workflow/scripts/legacy-phase-step-pause-allowlist.txt` | **仅消费**（PR-5 已生成 / 2 条） | 0 改动 | D19 |

> 工作量分摊：install 合并 0.10d；CI workflow + 8 项守门 0.25d；config-schema 脚本 0.05d；本施工单 0.03d → 合计 **0.43d**。

### 1.3 不在本 PR 范围（→ 主文档 §1.2 / §7）

- ❌ 不修改 `install.sh` 现有非 `--target` 部分逻辑（symlink 创建 / `--force` / `-h|--help`）
- ❌ 不修改 PR-1~7 已落地的协议字段、phase 文件、agents、templates
- ❌ 不实现 M11/M14（→ v4.2 遗留 #4 / D10）
- ❌ 不修复 `phases/p2-spec-definition.md:188 RCA-InProgress`（hotfix 候选，非 PR-8 范围）
- ❌ 不 push 远端（push 时机由用户决定）

---

## 2. install.sh `--target=` 合并设计（D12）

### 2.1 当前差异分析

`install.sh` 与 `install_trae.sh` 文件级 diff 仅 4 处：

| diff 维度 | install.sh | install_trae.sh |
|---|---|---|
| `--help` Usage 路径文本 | `bash mobile-qa-workflow/install.sh` | `bash mobile-qa-workflow/install_trae.sh` |
| `--help` 描述目标 | `into Cursor` | `into Trae` |
| Symlink 目标目录 | `${PROJECT_ROOT}/.cursor/skills` + `${HOME}/.cursor/skills` | `${PROJECT_ROOT}/.trae/skills` + `${HOME}/.trae/skills` |
| 完成提示语 | `请在 Cursor 中开启新对话以激活 Skill。` | `请在 Trae 中开启新对话以激活 Skill。` |

### 2.2 合并策略：单一脚本 + 目标矩阵

新增解析参数 `--target=cursor|trae|both`（默认 `cursor`，向后兼容旧调用 `bash install.sh`）。

```bash
# 参数解析骨架（与现有 --force / -h|--help 共存）
TARGET="cursor"  # 默认值，保证旧调用 `bash install.sh` 行为不变
for arg in "$@"; do
    case "$arg" in
        --force) FORCE_RELINK=1 ;;
        --target=cursor|--target=trae|--target=both) TARGET="${arg#--target=}" ;;
        --target=*) echo "Unknown --target value: ${arg#--target=}; expected cursor|trae|both" >&2; exit 1 ;;
        -h|--help) print_help; exit 0 ;;
        *) echo "Unknown argument: $arg" >&2; exit 1 ;;
    esac
done

install_one_target() {
    local label="$1"   # "Cursor" / "Trae"
    local subdir="$2"  # ".cursor/skills" / ".trae/skills"
    echo "Installing ${SKILL_ID} for ${label}..."
    create_symlink "${PROJECT_ROOT}/${subdir}"
    create_symlink "${HOME}/${subdir}"
    echo ""
    echo "Done. 请在 ${label} 中开启新对话以激活 Skill。"
}

case "$TARGET" in
    cursor) install_one_target "Cursor" ".cursor/skills" ;;
    trae)   install_one_target "Trae"   ".trae/skills"   ;;
    both)   install_one_target "Cursor" ".cursor/skills"
            install_one_target "Trae"   ".trae/skills" ;;
esac
```

### 2.3 install_trae.sh shim（D12 / v4.2 遗留 #5）

```bash
#!/usr/bin/env bash
# DEPRECATED：v4.1 起已合并到 install.sh，本 shim 维持向后兼容。
# v4.2 D12 / 主文档 §1.2.2 v4.2 遗留 #5：直接删除。
set -euo pipefail
exec bash "$(dirname "${BASH_SOURCE[0]}")/install.sh" --target=trae "$@"
```

### 2.4 兼容性断言（PR-level 自检 → §4）

| 旧调用 | 新行为 | 兼容性 |
|---|---|---|
| `bash mobile-qa-workflow/install.sh` | 默认 `--target=cursor` → 与旧版完全等价 | ✅ |
| `bash mobile-qa-workflow/install.sh --force` | 仍 `--target=cursor` + `FORCE_RELINK=1` | ✅ |
| `bash mobile-qa-workflow/install_trae.sh` | shim 转发到 `install.sh --target=trae` → 与旧版完全等价 | ✅ |
| `bash mobile-qa-workflow/install_trae.sh --force` | shim 转发 `install.sh --target=trae --force` | ✅ |
| `bash mobile-qa-workflow/install.sh --target=both` | **新能力**：同时安装到 Cursor + Trae | ➕ |

---

## 3. CI 8 项守门（GitHub Actions + 检查脚本骨架）

> 设计原则：每项守门**必须 fail-fast**（单 step 失败即整个 workflow 失败），输出可定位（带行号 / 文件路径），不依赖任何外部网络资源（仅 `bash` + `grep`/`awk`/`python3` 标准库）。

### 3.A CI 8 项检查矩阵

| # | 主文档锚点 | 检查名 | 命中模式 | 期望结果 | Fail 信号 | 退出码 |
|---|---|---|---|---|---|---|
| 1 | §3 PR-8 #1 / §5.1 #9 / D16 | step-pause 完整参数 | 全仓 grep `<step-pause`，每命中行起 6 行内必须含 `title=`、`result_field=`、`allowed_values=` 三属性 | 8 处全部齐全（workflow.xml 6 + phases 2） | 缺一项 → `[D16-FAIL] <path>:<line> missing <attr>` | 1 |
| 2 | §3 PR-8 #2 / §5.1 #10 / D14 / D19 | D14 调度作用域守门 | grep `^\s*<step-pause` 在 `mobile-qa-workflow/phases/**/*.md` + `mobile-qa-workflow/functionality-deep-dive/phases/**/*.md` 的命中，必须出现在 `legacy-phase-step-pause-allowlist.txt` 中 | 命中 2 条，全部白名单匹配（按 path:semantic-id；行号容许 ±5） | 出现 allowlist 之外的命中 → `[D14-FAIL] <path>:<line> not in allowlist` | 1 |
| 3 | §3 PR-8 #3 / §5.1 #12 / D15 | D15 顶层白名单守门 | (a) 扫描 `core/workflow.xml` 中所有顶层引用 `{xxx}`（不带 `user_inputs.` 前缀）形式的字段，对比 `core/workflow-status-template.yaml` 顶层字段集；(b) 扫描所有 `<step-pause result_field="X">`，X 不在白名单时不允许在 status-template 顶层有镜像字段 | (a) 顶层引用全部命中已注册字段；(b) 6 个 result_field 中仅 `non_bug_user_choice` 在白名单内 | 顶层引用未注册 → `[D15-FAIL] workflow.xml:<line> ref unknown top-level: {<key>}`；非白名单 result_field 出现顶层镜像 → `[D15-FAIL] result_field <key> mirrors top-level but not in whitelist` | 1 |
| 4 | §3 PR-8 #4 / §5.1 #14 / D8 | 顶层镜像字段过渡注释 | `core/workflow-status-template.yaml` 中所有顶层镜像字段（v4.1 起步集合 = `{non_bug_user_choice}`）必须在该字段上下 5 行内含"v4.2 收敛"或"v4.2 遗留 #3"等等价注释 | 命中"v4.2"+"收敛/遗留 #3"关键字 | 缺注释 → `[Migration-Note-FAIL] non_bug_user_choice missing v4.2 收敛 note` | 1 |
| 5 | §3 PR-8 #5 / D13 | 迁移脚本存在性 | `test -f mobile-qa-workflow/scripts/migrate-workflow-status-v3-to-v4.py` | 文件存在 | 不存在 → `[D13-FAIL] migrate script missing` | 1 |
| 6 | §3 PR-8 #6 / §5.1 #16 / D19 | allowlist 存在且非空 | `test -s mobile-qa-workflow/scripts/legacy-phase-step-pause-allowlist.txt` 且非注释行计数 == **2**（与 PR-5 现状一致） | 文件存在；非注释行 2 条；条目格式 `path:line:semantic-id` | 文件缺失/空 → `[D19-FAIL]`；非注释行数 ≠ 2 → `[D19-DRIFT]` | 1 |
| 7 | §3 PR-8 #7 / §5.1 #5 / M16 | config-schema 键漂移 | 调用 `mobile-qa-workflow/scripts/check-config-schema.sh`：扫描 `phases/**/*.md` + `functionality-deep-dive/phases/**/*.md` 中所有 `更新 .*config_source.*：<key>` 模式的 `<key>`，必须在 `core/config-schema.yaml` `allowed_keys` 内 | 当前所有写入键（≈ 12 个）全部命中 | 未注册键 → `[M16-FAIL] <path>:<line> unknown key: <key>` | 1 |
| 8 | §5.1 #12（D18 4 类动作） | parse-error 生命周期闭合 | `core/workflow.xml` 必须**同时**含 4 类动作：(a) `parse_error_count += 1`；(b) "解析成功"路径下 `parse_error_count = 0`；(c) "进入新 step-pause 前" `parse_error_count = 0`；(d) "熔断"（`parse_error_count >= 3`）后 `parse_error_count = 0` | 4 类动作各 ≥ 1 处命中（当前现状已满足，§3.B step-8 给 grep 表达式） | 缺任一类 → `[D18-FAIL] missing lifecycle action: <a/b/c/d>` | 1 |

### 3.B 8 项检查的 grep/awk 骨架（`.github/workflows/...yml` 内联或下放到 `mobile-qa-workflow/scripts/check-*.sh`）

> 原则：能用 `bash + grep -E + awk` 实现的不引 python；M16 检查（涉及 yaml `allowed_keys` 解析）下放到 `check-config-schema.sh`，可用最简 awk 解析（不引 PyYAML 依赖）。

```bash
# ═══════════════════════════════════════════════════════════════
# 检查 1：D16 step-pause 参数完整性
# ═══════════════════════════════════════════════════════════════
fail=0
while IFS=: read -r f ln _; do
    block=$(awk -v start="$ln" 'NR>=start && NR<=start+6' "$f")
    for attr in title result_field allowed_values; do
        echo "$block" | grep -q "${attr}=" \
            || { echo "[D16-FAIL] $f:$ln missing ${attr}"; fail=1; }
    done
done < <(grep -rnE '<step-pause' mobile-qa-workflow/core/workflow.xml \
                                    mobile-qa-workflow/phases/ \
                                    mobile-qa-workflow/functionality-deep-dive/phases/)
[ $fail -eq 0 ] || exit 1

# ═══════════════════════════════════════════════════════════════
# 检查 2：D14 调度作用域 + D19 allowlist
# ═══════════════════════════════════════════════════════════════
ALLOWLIST=mobile-qa-workflow/scripts/legacy-phase-step-pause-allowlist.txt
fail=0
while IFS=: read -r f ln _; do
    # 提取上下 6 行内的 semantic-id（注释/option title 中的 stepN-xxx 关键字 / fallback：行号容许 ±5）
    if ! awk -v line="$ln" 'NR>=line-5 && NR<=line+5' "$f" \
        | grep -qE '(step[0-9]+-spec-uncertain|step[0-9]+-fix-design-confirm)' ; then
        sem="line-only"
    else
        sem=$(awk -v line="$ln" 'NR>=line-5 && NR<=line+5' "$f" \
              | grep -oE '(step[0-9]+-spec-uncertain|step[0-9]+-fix-design-confirm)' | head -1)
    fi
    # path 匹配 + semantic-id 匹配（line 容许漂移）
    if ! grep -vE '^\s*(#|$)' "$ALLOWLIST" \
       | awk -F: -v p="$f" -v s="$sem" '$1==p && $3==s {found=1} END {exit !found}'; then
        echo "[D14-FAIL] $f:$ln not in allowlist (semantic-id=$sem)"; fail=1
    fi
done < <(grep -rnE '^\s*<step-pause' mobile-qa-workflow/phases/ \
                                       mobile-qa-workflow/functionality-deep-dive/phases/ 2>/dev/null)
[ $fail -eq 0 ] || exit 1

# ═══════════════════════════════════════════════════════════════
# 检查 3：D15 白名单守门（顶层引用 + result_field 镜像）
# ═══════════════════════════════════════════════════════════════
TPL=mobile-qa-workflow/core/workflow-status-template.yaml
TOP_KEYS=$(awk '/^[a-zA-Z_][a-zA-Z0-9_]*:/ {sub(":.*",""); print}' "$TPL" \
           | grep -vE '^(specialized_workflow)$' | sort -u)
# 3a：核心顶层引用 {xxx} 必须在 TOP_KEYS（仅校验形如 {xxx_user_choice} / {non_bug_context} 的状态字段引用，
#      排除 {workflow_status} / {issue_id} / {options} 等编排器局部上下文 — 用静态白名单豁免列）
fail=0
EXEMPT='workflow_status|issue_id|spec_options|missing_items|suggestion|options|output_file|reroute_reason|note'
while IFS=: read -r f ln key; do
    key=$(echo "$key" | sed -E 's/.*\{([a-zA-Z_][a-zA-Z0-9_]*)\}.*/\1/')
    [[ "$key" =~ ^($EXEMPT)$ ]] && continue
    grep -q "^${key}:" "$TPL" \
        || { echo "[D15-FAIL] $f:$ln top-level ref to unknown key: {$key}"; fail=1; }
done < <(grep -nE '\{(non_bug_context|[a-z_]+_user_choice)\}' mobile-qa-workflow/core/workflow.xml)
# 3b：result_field 中若不在 TOP_KEYS，必须不出现在 TPL 顶层
WHITELIST=$(awk '/⚠️ 顶层镜像字段白名单/,/specialized_workflow:/' "$TPL" \
           | grep -E '^[a-z_][a-z0-9_]*:' | sed 's/:.*//' | sort -u)
while read -r rf; do
    if echo "$WHITELIST" | grep -qx "$rf"; then : ; else
        if grep -q "^${rf}:" "$TPL"; then
            echo "[D15-FAIL] result_field $rf not in whitelist but mirrored top-level"; fail=1
        fi
    fi
done < <(grep -hoE 'result_field="[a-z_]+"' mobile-qa-workflow/core/workflow.xml \
                                              mobile-qa-workflow/phases/*.md \
         | sed -E 's/result_field="([a-z_]+)"/\1/' | sort -u)
[ $fail -eq 0 ] || exit 1

# ═══════════════════════════════════════════════════════════════
# 检查 4：顶层镜像字段过渡注释
# ═══════════════════════════════════════════════════════════════
# 仅校验起步白名单 = {non_bug_user_choice}
ln=$(grep -n '^non_bug_user_choice:' "$TPL" | cut -d: -f1)
awk -v line="$ln" 'NR>=line-6 && NR<=line+1' "$TPL" \
    | grep -qE 'v4\.2.*(收敛|遗留\s*#3)' \
    || { echo "[Migration-Note-FAIL] non_bug_user_choice missing 'v4.2 收敛/遗留 #3' note"; exit 1; }

# ═══════════════════════════════════════════════════════════════
# 检查 5：迁移脚本存在性（D13）
# ═══════════════════════════════════════════════════════════════
test -f mobile-qa-workflow/scripts/migrate-workflow-status-v3-to-v4.py \
    || { echo "[D13-FAIL] migrate script missing"; exit 1; }

# ═══════════════════════════════════════════════════════════════
# 检查 6：allowlist 存在且非空（D19，固化 == 2）
# ═══════════════════════════════════════════════════════════════
test -s "$ALLOWLIST" || { echo "[D19-FAIL] allowlist missing/empty"; exit 1; }
n=$(grep -cvE '^\s*(#|$)' "$ALLOWLIST")
[ "$n" -eq 2 ] || { echo "[D19-DRIFT] allowlist non-comment lines = $n, expected 2"; exit 1; }
grep -vE '^\s*(#|$)' "$ALLOWLIST" | grep -vE '^[^:]+:[0-9]+:[a-z0-9-]+$' \
    | grep -q . && { echo "[D19-FORMAT] allowlist contains malformed entry"; exit 1; } || true

# ═══════════════════════════════════════════════════════════════
# 检查 7：M16 config-schema 键漂移（→ check-config-schema.sh）
# ═══════════════════════════════════════════════════════════════
bash mobile-qa-workflow/scripts/check-config-schema.sh || exit 1

# ═══════════════════════════════════════════════════════════════
# 检查 8：D18 parse_error_count 4 类生命周期动作
# ═══════════════════════════════════════════════════════════════
WF=mobile-qa-workflow/core/workflow.xml
declare -A NEED=(
    [increment]='parse_error_count\s*\+=\s*1'
    [reset_on_success]='parse_error_count\s*=\s*0.*(成功|D18\s*解析成功)'
    [reset_before_pause]='parse_error_count\s*=\s*0.*(进入新|D18 进入新)'
    [reset_on_circuit_break]='parse_error_count\s*=\s*0.*(熔断|D18 熔断)'
)
fail=0
for k in "${!NEED[@]}"; do
    grep -qE "${NEED[$k]}" "$WF" \
        || { echo "[D18-FAIL] missing lifecycle action: $k"; fail=1; }
done
[ $fail -eq 0 ] || exit 1
```

> **注**：检查 8 的 4 类动作模式与现状（`workflow.xml` line 124/128/159/210/258/288/319/333）逐一匹配；如未来重构改名/中文措辞调整，需同步更新本表的正则。

### 3.C `check-config-schema.sh` 设计（M16 实现）

```bash
#!/usr/bin/env bash
# mobile-qa-workflow/scripts/check-config-schema.sh
# 用途（M16 / 主文档 §3 PR-8 评审重点 7）：
#   扫描 phases 中所有 "更新 ... config_source ... <key>" 动作，
#   校验 <key> 必须在 core/config-schema.yaml allowed_keys 内。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCHEMA="${ROOT}/mobile-qa-workflow/core/config-schema.yaml"
SCAN_DIRS=(
    "${ROOT}/mobile-qa-workflow/phases"
    "${ROOT}/mobile-qa-workflow/functionality-deep-dive/phases"
)
# 1. 解析 allowed_keys（仅取 "  - <name>" 行；忽略 nested_/known_legacy_）
ALLOWED=$(awk '
    /^allowed_keys:/  {in_block=1; next}
    /^[a-zA-Z_]/      {in_block=0}
    in_block && /^\s*-\s*[a-z_]/ {gsub(/^\s*-\s*/,""); gsub(/\s*#.*/,""); print}
' "$SCHEMA" | sort -u)
# 2. 扫描 phases，提取所有 `更新 {config_source}：<key> = ...` 与多键变体
fail=0
while IFS=: read -r f ln content; do
    keys=$(echo "$content" \
        | grep -oE '(更新|更新.*config_source[：:])\s*[a-z_][a-z0-9_]*\s*=' \
        | grep -oE '[a-z_][a-z0-9_]*\s*=$' \
        | sed 's/[ =]//g')
    extra=$(echo "$content" \
        | grep -oE ',\s*[a-z_][a-z0-9_]*\s*=' \
        | sed 's/[ ,=]//g')
    for k in $keys $extra; do
        echo "$ALLOWED" | grep -qx "$k" \
            || { echo "[M16-FAIL] $f:$ln unknown config_source key: $k"; fail=1; }
    done
done < <(grep -rnE '更新.*config_source' "${SCAN_DIRS[@]}" 2>/dev/null)
exit $fail
```

> **当前现状**：所有写入键（`fix_branch` / `output_issue_card` / `output_verification_report` / `output_knowledge_card` / `output_rca_report` / `output_fix_design` / `output_environment_factor_report` / `output_topology_report` / `output_concurrency_report` / `output_deep_dive_rca` / `output_deep_dive_summary` / `output_defensive_fix_design`）均在 `allowed_keys` 内（`config-schema.yaml` line 21-69）。本检查初次落地预期**全绿**。

### 3.D `.github/workflows/qa-workflow-schema-check.yml` 设计

```yaml
name: QA Workflow Schema Check

# 触发：仅 PR 与 main 推送，且仅当本 SKILL 范围或 CI 自身改动时触发，
# 不阻塞 v4.1 之前旧分支（v4.1 之前分支不含 mobile-qa-workflow/scripts/ 目录）
on:
  pull_request:
    paths:
      - 'mobile-qa-workflow/**'
      - '.github/workflows/qa-workflow-schema-check.yml'
  push:
    branches: [main]
    paths:
      - 'mobile-qa-workflow/**'
      - '.github/workflows/qa-workflow-schema-check.yml'

jobs:
  schema-check:
    name: 8-item schema/protocol guard (D14/D15/D16/D18/D19/M16)
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
      - name: Make scripts executable
        run: chmod +x mobile-qa-workflow/scripts/check-config-schema.sh
      - name: Check 1 — D16 step-pause 完整参数
        run: bash .github/workflows/qa-checks/check-d16-step-pause-attrs.sh
      - name: Check 2 — D14 调度作用域 + D19 allowlist
        run: bash .github/workflows/qa-checks/check-d14-d19-allowlist.sh
      - name: Check 3 — D15 顶层白名单守门
        run: bash .github/workflows/qa-checks/check-d15-whitelist.sh
      - name: Check 4 — 顶层镜像过渡注释
        run: bash .github/workflows/qa-checks/check-migration-note.sh
      - name: Check 5 — 迁移脚本存在性 (D13)
        run: test -f mobile-qa-workflow/scripts/migrate-workflow-status-v3-to-v4.py
      - name: Check 6 — allowlist 存在且非空 (D19)
        run: bash .github/workflows/qa-checks/check-d19-allowlist-presence.sh
      - name: Check 7 — config-schema 键漂移 (M16)
        run: bash mobile-qa-workflow/scripts/check-config-schema.sh
      - name: Check 8 — D18 parse-error 生命周期闭合
        run: bash .github/workflows/qa-checks/check-d18-parse-error-lifecycle.sh
```

> **实施期取舍**（已锁定）：8 个 grep/awk 块**全部内联到 yml `run: |` 块**（与 §3.B 骨架等价），**不再下放到 `.github/workflows/qa-checks/*.sh`**。理由：脚本数量少（8 项每项 5-30 行）、CI 路径定位更直接、避免引入 `mobile-qa-workflow/` 之外的辅助脚本目录维护负担；M16 因为依赖 yaml 解析 + 双向扫描，仍走独立脚本 `mobile-qa-workflow/scripts/check-config-schema.sh`（§3.C）保留可本地复用。本节列出 `qa-checks/*.sh` 仅作为"可读性更佳"的设计稿，实施时按"内联到 yml"路线执行，并在 commit 3 message 中标注。

---

## 4. PR-level DoD 自检（链 §5.1 第 5/9/10/11/12/14/16 项 + D18）

| # | DoD 项 | 主文档 §5.1 编号 | 自检命令 / 验收方式 |
|---|---|---|---|
| 1 | step-pause 参数表完整 | #9 | 本地跑 `bash` 检查 1 → 8 命中、0 fail |
| 2 | D14 调度作用域硬守门 | #10 | 本地跑检查 2 → 命中 2 条 phase step-pause、全部白名单匹配 |
| 3 | step-pause 输入协议完整（间接） | #11 | 检查 1+3 联动通过即可；本 PR 不直接引 input-protocol grep |
| 4 | D15 顶层白名单受限 | #12 | 本地跑检查 3 → 仅 `non_bug_user_choice` 镜像顶层、其余 5 个 result_field 不污染 |
| 5 | 顶层镜像字段过渡标注 | #14 | 本地跑检查 4 → `non_bug_user_choice` 上下含 v4.2 注释 |
| 6 | 配置键名注册（CI 强制） | #5 | 本地跑检查 7 → 12 个 config_source 写入键全部在 allowed_keys |
| 7 | allowlist 交付完整 | #16 | 本地跑检查 6 → 文件存在 + 非注释行 == 2 + 格式合规 |
| 8 | parse-error 生命周期闭合 | #12（D18 配套） | 本地跑检查 8 → 4 类动作各 ≥ 1 处命中 |
| 9 | install_trae.sh shim 等价 | — | (a) `bash install_trae.sh --help` 输出与原版语义等价；(b) `bash install_trae.sh` 安装结果（symlink 路径）与 v4.1 之前完全等价 |
| 10 | CI fail-fast | — | 在临时分支故意制造一个 D14 违规（往 phases 加一行 `<step-pause`）→ workflow 应在 ≤ 60s 内 fail；恢复后绿 |
| 11 | CI 不阻塞 v4.1 之前旧分支 | — | workflow 触发 paths 限制 `mobile-qa-workflow/**` + `.github/workflows/qa-workflow-schema-check.yml`；旧分支不含本 SKILL 目录则不触发；含但未引入新协议字段则因 phases/workflow.xml 仍是 v4.0 状态而 fail，**这是预期行为**（属"v4.1 之前需先合 v4.1 协议层"语义）— Reviewer 评审时确认本理解 |
| 12 | CI 在本 PR 自身 push 上触发并全绿 | — | 推送本 PR 后 GitHub Actions UI 显示 `QA Workflow Schema Check / schema-check ✓` |

---

## 5. Commit 拆分纪律（吸取 PR-5+6 `d68041a` 教训；范本：PR-7 三段式 / PR-5+6 §4.D）

> **每 commit 单一职责**，确保单边 `git revert` 粒度。

| commit | 范围 | message 前缀 | 涉及文件 |
|---|---|---|---|
| **1** | 仅本施工单 | `docs(qa-workflow): PR-8 精简施工单 v1` | `mobile-qa-workflow/construction-plans/v2.2/pr8-ci-install-integration.md`（**仅本文件**） |
| **2** | install 合并 + shim 化 | `feat(qa-workflow): PR-8 install.sh --target= 合并 + install_trae.sh shim 化（D12）` | `mobile-qa-workflow/install.sh` + `mobile-qa-workflow/install_trae.sh` |
| **3** | CI workflow + check-config-schema 脚本 | `feat(qa-workflow): PR-8 CI schema-check workflow + 8 项守门（D14/D15/D16/D18/D19/M16）` | `.github/workflows/qa-workflow-schema-check.yml` + `mobile-qa-workflow/scripts/check-config-schema.sh` |
| **4**（可选） | 主文档 §4 索引行联动 | `docs(qa-workflow): PR-8 主文档 §4 PR-8 索引行联动` | `mobile-qa-workflow/QUALITY-AUDIT-CONSTRUCTION-PLAN-v2.2.md`（仅 §4 PR-8 行 `_待展开_` → 子文档链接） |

**禁止**：把 install / CI / 施工单文件混在同一 commit 内。

**Reviewer 必检**：评审时使用 `git log --oneline <base>..HEAD` 验证 ≥ 3 个相邻 commit（commit 4 可选），且按上表前缀分组。

**CR 与 CR 修复独立成 commit**（参考 PR-7 `b912cf1` / `db561c9` / `80ed5cd` 三段式）：CR 评审留档使用文件名 `pr8-ci-install-integration-REVIEW-YYYY-MM-DD.md`，置于 `construction-plans/v2.2/`。

---

## 6. 回滚动作（链主文档 §7.8）

主文档 §7.8 已定义 PR-8 回滚后状态（CI workflow 移除 / install_trae.sh 还原 / shim 删除），本节不重复。

**本 PR commit 拆分对应的单边 revert 操作**：

| 单边 revert 场景 | 命令 | revert 后状态 |
|---|---|---|
| 仅回滚 install 合并（保留 CI） | `git revert <commit-2-sha>` | install_trae.sh 还原为完整脚本；CI 仍运行（不依赖 install） |
| 仅回滚 CI 守门（保留 install 合并） | `git revert <commit-3-sha>` | CI workflow 删除；check-config-schema.sh 删除；install 合并能力保留 |
| 整 PR 回滚 | `git revert <commit-3-sha> <commit-2-sha> <commit-1-sha>` | 等价于主文档 §7.8 PR-8 回滚后状态 |

> **额外注意**（D12）：若用户已在 v4.1 期间将自定义脚本依赖改为调用 `install.sh --target=trae`，PR-8 回滚后旧用法仍可用（shim 行为等价），**无破坏性**。

---

## 7. 范围之外（明确排除）

- ❌ 不修改 `phases/p2-spec-definition.md:188` 的 `RCA-InProgress`（hotfix 候选，非 PR-8 范围；登记到主文档 §7.8 之外的 v4.1 hotfix 候选清单）
- ❌ 不动 PR-1~7 已落地的协议字段（schema_version / non_bug_context / parse_error_count / 顶层镜像白名单 / 6 个编排器 step-pause 等）
- ❌ 不实现 M11/M14（v4.2 遗留 #4 / D10）
- ❌ 不改 `install.sh` 现有非 `--target` 部分逻辑
- ❌ 不引入新的 v4.2 遗留条目（仅消费已有 D19 / v4.2 遗留 #5）
- ❌ 不 push 远端（push 由用户决定时机）

---

> **施工单版本**：v1（精简单；不再引 v2/v3 多版本，按 CR 评审反馈直接增量修订或独立 REVIEW 文档承载）
> **下一步**：commit 1 落盘本施工单 → 等用户 review → commit 2 install → commit 3 CI + check-config-schema → 本地 dry-run → 报告
