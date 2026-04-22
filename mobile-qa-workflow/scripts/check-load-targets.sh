#!/usr/bin/env bash
# check-load-targets.sh (v4.2 PR-7 / GEN-PR7 / Check 18)
# 守门：扫描 workflow 关键目录内所有 <load target="..."> / <load target='...'>，
# 并断言 target 路径可达（test -f 语义）。
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

python3 - "$REPO_ROOT" <<'PY'
import os
import re
import sys
from pathlib import Path

repo_root = Path(sys.argv[1]).resolve()
wf = repo_root / "mobile-qa-workflow"

scan_roots = [
    wf / "phases",
    wf / "agents",
    wf / "reference",
    wf / "core",
    wf / "SKILL.md",
    wf / "functionality-deep-dive" / "phases",
    wf / "functionality-deep-dive" / "agents",
    wf / "functionality-deep-dive" / "reference",
    wf / "functionality-deep-dive" / "core",
]

must_exist_sources = [
    "mobile-qa-workflow/core/core-rules-subagent.xml",
    "mobile-qa-workflow/reference/reasoning-chain-core.md",
    "mobile-qa-workflow/reference/reasoning-guide-functional.md",
    "mobile-qa-workflow/reference/reasoning-guide-ui.md",
    "mobile-qa-workflow/reference/reasoning-guide-network.md",
    "mobile-qa-workflow/reference/reasoning-guide-compat.md",
    "mobile-qa-workflow/agents/coder-workflow.md",
    "mobile-qa-workflow/reference/contract-checklist-spec.md",
    "mobile-qa-workflow/agents/shared-input-guard.md",
]

must_be_loaded = [
    "mobile-qa-workflow/core/core-rules-subagent.xml",
    "mobile-qa-workflow/agents/coder-workflow.md",
    "mobile-qa-workflow/reference/contract-checklist-spec.md",
    "mobile-qa-workflow/agents/shared-input-guard.md",
]

load_re = re.compile(r"<load\b[^>]*?\btarget\s*=\s*([\"'])([^\"']+)\1", re.S)
violations = 0
total = 0
seen_targets: set[str] = set()

def iter_files(root: Path):
    if root.is_file():
        yield root
        return
    if not root.is_dir():
        return
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in ("archive", "v3-legacy") for part in p.parts):
            continue
        if p.suffix not in (".md", ".xml"):
            continue
        yield p

for f in scan_roots:
    for path in iter_files(f):
        text = path.read_text(encoding="utf-8")
        for m in load_re.finditer(text):
            total += 1
            target = m.group(2)
            lineno = text.count("\n", 0, m.start()) + 1
            rel_file = path.relative_to(repo_root).as_posix()

            # 占位符 / 文档示例路径：不做 file existence 强校验
            if ("{" in target and "}" in target) or "..." in target:
                continue

            if target.startswith("mobile-qa-workflow/"):
                resolved = (repo_root / target).resolve()
            elif target.startswith("/"):
                resolved = Path(target).resolve()
            else:
                resolved = (path.parent / target).resolve()

            if not resolved.is_file():
                print(
                    f"::error file={rel_file},line={lineno}::"
                    f"<load target> 路径不可达：{target} -> {resolved}"
                )
                violations += 1
                continue
            seen_targets.add(target)

for rel in must_exist_sources:
    if not (repo_root / rel).is_file():
        print(f"::error::PR-7 新增源文件不存在：{rel}")
        violations += 1

for rel in must_be_loaded:
    if rel not in seen_targets:
        print(f"::error::PR-7 新增源文件 {rel} 未被任何 <load> 触达")
        violations += 1

if violations:
    print(f"FAIL: 发现 {violations} 处违例（共扫描 {total} 个 <load target> 触达点）")
    raise SystemExit(1)

print(
    f"OK: {total} 个 <load target> 触达点路径全部可达；"
    "PR-7 新增 9 个源文件存在性 + 4 个必触达载入点全部就绪"
)
PY
