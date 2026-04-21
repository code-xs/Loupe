#!/usr/bin/env bash
# check-phase-abort-structure.sh (v4.2 PR-3' / Seg-1 / SCRIPT-N1 / O22)
# 守门：phase-abort / phase-complete 宏结构守门（warning 起步，PR-6 升级 error）
#
# 守门目标（V1.1 §3.2.22）：
#   ① <phase-abort> / <phase-complete> 的 state 必须在权威 enum 集内
#      （占位字面 "{...}" 开头时跳过）
#   ② fields key 必须在 workflow-status-template.yaml 顶层字段表内
#   ③ 每个 phase 文件应至少包含 1 处 <phase-complete> 或 <phase-abort> 宏
#      （口径取舍详见下方 check_phase_has_macro 函数注释；PR-3' 仅 P1/P2/P3/P5/P6
#      已对齐，P4 输出 notice 提示"留 PR-6"）
#
# Severity 切换：
#   PHASE_ABORT_SEVERITY=warning（默认，PR-3' 起步）
#   PHASE_ABORT_SEVERITY=error  （PR-6 升级，D14 收口完成后）
#
# 关联：
#   · 主控 §4 PR-3 启用列 / 主文档 §2.9 / 附录 §1.1
#   · ADR-021（phase-abort/complete 宏标签）
#   · 同款 python 严格提取算法基线：scripts/check-system-prompt-sync.sh

set -euo pipefail
# 切到 mobile-qa-workflow 目录（与同目录其他 check-*.sh 一致）
cd "$(dirname "$0")/.."

SEVERITY="${PHASE_ABORT_SEVERITY:-warning}"
TPL="core/workflow-status-template.yaml"
fail=0

if [ ! -f "$TPL" ]; then
  echo "::error::workflow-status-template.yaml 不存在: $TPL"
  exit 1
fi

# ────────────────────────────────────────────────────────────────
# 1) 提取权威 enum 集 + 顶层字段表
#    - ENUM_SET：current_state 合法枚举（来自 yaml 头部 "v4.1 完整集合" 注释块）
#    - FIELD_SET：yaml 顶层字段名（用于 fields key 校验）
# ────────────────────────────────────────────────────────────────
ENUM_SET=$(python3 - "$TPL" <<'PY'
import re, sys
path = sys.argv[1]
with open(path, encoding='utf-8') as f:
    src = f.read()
# 抽取注释块中以 "v4.1 完整集合" 起始、到首个含 "Done" 的注释行结束之间的内容
# （与 scripts/check-state-enum.sh awk '/v4.1 完整集合/,/^[^#]/' 同段，但用 Done 收尾更稳健，
#  避免下游 "SKILL.md / PLATFORM-GUIDE.md" 等示例字面被误抓）
lines = src.splitlines()
collect = False
block = []
for ln in lines:
    if not collect and 'v4.1 完整集合' in ln:
        collect = True
        continue
    if collect:
        if not ln.lstrip().startswith('#'):
            break
        block.append(ln)
        if 'Done' in ln:
            break
text = '\n'.join(block)
tokens = re.findall(r'\b[A-Z][A-Za-z-]+\b', text)
seen = set()
out = []
for t in tokens:
    if t in seen: continue
    seen.add(t)
    out.append(t)
print(' '.join(out))
PY
)

FIELD_SET=$(python3 - "$TPL" <<'PY'
import re, sys
path = sys.argv[1]
with open(path, encoding='utf-8') as f:
    lines = f.readlines()
fields = []
for ln in lines:
    m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*:', ln)
    if m:
        fields.append(m.group(1))
print(' '.join(fields))
PY
)

if [ -z "$ENUM_SET" ]; then
  echo "::error::无法从 $TPL 头部抽取权威 enum 集（v4.1 完整集合注释块缺失？）"
  exit 1
fi

# ────────────────────────────────────────────────────────────────
# 2) 检查每个 phase 文件的宏标签
# ────────────────────────────────────────────────────────────────
abort_count=0
complete_count=0

emit() {
  # $1 = severity (warning|error|notice), $2 = msg
  local sev="$1"; shift
  echo "::${sev}::$*"
  if [ "$sev" = "error" ]; then fail=1; fi
}

check_state() {
  # $1 = file, $2 = line, $3 = state value
  local file="$1" line="$2" state="$3"
  if [ -z "$state" ]; then return; fi
  # 占位字面（以 { 开头）跳过校验，详见 ABORT-D8 / ADR-021 §2 落地纪要
  if [[ "$state" == \{* ]]; then return; fi
  if ! echo " $ENUM_SET " | grep -q " $state "; then
    emit "$SEVERITY" "$file:$line: state='$state' 不在权威 enum 集内"
  fi
}

check_fields_keys() {
  # $1 = file, $2 = line, $3 = fields json literal
  local file="$1" line="$2" json="$3"
  if [ -z "$json" ]; then return; fi
  # 抽取 JSON 字面量中的 key（"<key>": ...）
  local keys
  keys=$(echo "$json" | grep -oE '"[A-Za-z_][A-Za-z0-9_]*"[[:space:]]*:' | sed -E 's/^"([A-Za-z_][A-Za-z0-9_]*)".*/\1/')
  for k in $keys; do
    if ! echo " $FIELD_SET " | grep -q " $k "; then
      emit "$SEVERITY" "$file:$line: fields key '$k' 不在 workflow-status-template.yaml 顶层字段表内"
    fi
  done
}

# Phase 含宏校验：判断 phase 文件是否至少含 1 处 phase-abort/complete 宏。
# 设计取舍（v4.2 PR-3' / v1.2 review Finding #2 收口 / 主文档 §2.2.2 ABORT-D9~D11 特殊性）：
#   · v1.1 草案曾设想"末 step 必含宏"，但部分 phase 物理末 step 是"文档保留段"
#     （如 P5 step 8 失败收口段，宏第 4 步退出 phase 后已不可达 / ABORT-D9 注释），
#     强校验"末 step"会对该类合法布局误报 warning；
#   · 收口为"phase 文件含宏 ≥ 1"作为对齐口径：与 DoD §3.1 "干净主干实跑零 warning" 一致，
#     且语义上等价 — 既然每个 phase 至少有 1 个出口（早退或完成），含宏 ≥ 1 即覆盖
#     "所有出口都用宏改写"的强约束；
#   · P4 因内联 step-pause 整改留 PR-6（主文档 §2.3.2），单独输出 notice。
check_phase_has_macro() {
  local file="$1"
  if grep -qE '<phase-(abort|complete)\b' "$file"; then
    return 0
  fi
  if [[ "$file" == *p4-fix-design* ]]; then
    echo "::notice::$file: P4 未用宏（PR-6 删除内联 step-pause 后改写 / 详见主文档 §2.3.2）"
  else
    emit "$SEVERITY" "$file: 未发现任何 phase-complete/abort 宏（phase 文件至少需含 1 处宏出口）"
  fi
}

# 用 python 一次性提取每个宏的 state / fields，避免多行属性 grep 难度
python_macro_dump() {
  python3 - "$1" <<'PY'
import re, sys
path = sys.argv[1]
with open(path, encoding='utf-8') as f:
    src = f.read()
# 行号映射
def line_no(off):
    return src.count('\n', 0, off) + 1
# 匹配 <phase-abort ...> 或 <phase-complete ...>，含跨行属性
pattern = re.compile(r'<(phase-abort|phase-complete)\b([^>]*?)/?>', re.DOTALL)
for m in pattern.finditer(src):
    tag = m.group(1)
    attrs = m.group(2)
    state_m = re.search(r'state\s*=\s*"([^"]*)"', attrs)
    fields_m = re.search(r"fields\s*=\s*'([^']*)'", attrs)
    state = state_m.group(1) if state_m else ''
    fields = fields_m.group(1) if fields_m else ''
    # 把 fields 中的换行折叠为单行（便于 bash 读取）
    fields_one = re.sub(r'\s+', ' ', fields).strip()
    print(f"{tag}\t{line_no(m.start())}\t{state}\t{fields_one}")
PY
}

# 检查范围：仅主链路 6 个 phase（PR-3' Seg-1 改写范围）；
# functionality-deep-dive/phases/** 不在本 PR 治理范围（后续 PR 单独评估）。
for phase_file in phases/*.md; do
  [ -f "$phase_file" ] || continue
  while IFS=$'\t' read -r tag line state fields; do
    [ -z "$tag" ] && continue
    case "$tag" in
      phase-abort)    abort_count=$((abort_count+1)) ;;
      phase-complete) complete_count=$((complete_count+1)) ;;
    esac
    check_state "$phase_file" "$line" "$state"
    check_fields_keys "$phase_file" "$line" "$fields"
  done < <(python_macro_dump "$phase_file")
  check_phase_has_macro "$phase_file"
done

if [ $fail -eq 0 ]; then
  echo "✅ check-phase-abort-structure.sh 通过（severity=$SEVERITY / phase-abort=$abort_count / phase-complete=$complete_count）"
fi
exit $fail
