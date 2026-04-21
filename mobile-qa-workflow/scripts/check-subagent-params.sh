#!/usr/bin/env bash
# check-subagent-params.sh (v1.1)
# 守门：invoke-subagent 调用按角色驱动注入 — challenger → confidence_input；arbiter → base_score
# 关联：V1.1 §3.2.22 第 4 项 / C2 类 Schema-Violation / 主控 §4 PR-1 启用为 error
# v1.1 增强：补完整 arbiter 实现 + 双向反向断言（角色字段矩阵反转 = error）

set -euo pipefail
cd "$(dirname "$0")/.."

fail=0

python3 - <<'PYEOF' || fail=$?
import re, glob, sys

err_count = 0
total_ch = 0
total_ar = 0

for fp in glob.glob('phases/*.md'):
    content = open(fp).read()
    # 退化方案：按 subagent_type=" 切分块；每块视为一个 invoke-subagent 上下文
    pieces = re.split(r'(?=subagent_type=")', content)
    for piece in pieces:
        m = re.match(r'subagent_type="([^"]+)"', piece)
        if not m: continue
        st = m.group(1)
        # 取本 invoke-subagent 块的合理上下文（到下一个 invoke-subagent 或 1500 字符截断）
        block = piece[:1500]

        if st == 'challenger':
            total_ch += 1
            if 'confidence_input' not in block:
                print(f"::error::{fp} : challenger 调用缺 confidence_input 注入")
                err_count += 1
            if 'base_score' in block:
                print(f"::error::{fp} : challenger 调用错误注入 base_score（角色矩阵反转 / v2.2 PR-4 review Finding 2）")
                err_count += 1

        elif st == 'arbiter':
            total_ar += 1
            if 'base_score' not in block:
                print(f"::error::{fp} : arbiter 调用缺 base_score 注入")
                err_count += 1
            if 'confidence_input' in block:
                print(f"::error::{fp} : arbiter 调用错误注入 confidence_input（角色矩阵反转 / v2.2 PR-4 review Finding 2）")
                err_count += 1

print(f"check-subagent-params.sh (v1.1): challenger={total_ch} / arbiter={total_ar} / errors={err_count}", file=sys.stderr)
sys.exit(1 if err_count else 0)
PYEOF

[ $fail -eq 0 ] && echo "✅ check-subagent-params.sh (v1.1) 通过"
exit $fail
