#!/usr/bin/env python3
"""sync-core-rules-aggregate.py (v4.2 PR-7 / O23 / D-AGG-1)

把 core/core-rules-essential.xml + core/core-rules-dsl-reference.xml 聚合为
唯一下游产物 core/core-rules.xml。PR-7 起 core-rules.xml = 生成产物，禁止手改。

聚合契约（D-AGG-1）：
  · essential.xml 是骨架，含唯一占位标记 `<!-- AGG-INSERT: core-rules-dsl-reference.xml -->`
  · dsl-reference.xml 是 <supported-tags> 子集（含嵌套 <input-protocol>）
  · 脚本步骤：
      1. 读 essential.xml，把根 <core-rules-essential id name> 重命名为
         <core-rules id="mobile-qa/core-rules.xml" name="Mobile QA Workflow Core Rules">
      2. 读 dsl-reference.xml，去掉外层 <core-rules-dsl-reference> 根与首注释块，
         按 essential 占位标记所在行的缩进，注入 body
      3. 在文件首插入 AUTOGEN 警告注释
      4. 写出（--write）或对账（--check）

CI（Check 18 / required）：
  · workflow 走 `--check`：若 essential / dsl-reference 已改但 core-rules.xml
    未同步，构建失败并提示运行 `--write`
  · 工程师本地：编辑两个源文件后必须运行 `python3 scripts/sync-core-rules-aggregate.py --write`

用法：
  python3 mobile-qa-workflow/scripts/sync-core-rules-aggregate.py --check
  python3 mobile-qa-workflow/scripts/sync-core-rules-aggregate.py --write
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Optional


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_ROOT = REPO_ROOT / "mobile-qa-workflow"

ESSENTIAL_REL = "core/core-rules-essential.xml"
DSL_REL = "core/core-rules-dsl-reference.xml"
TARGET_REL = "core/core-rules.xml"

AGGREGATE_ID = "mobile-qa/core-rules.xml"
AGGREGATE_NAME = "Mobile QA Workflow Core Rules"

INSERT_MARKER_RE = re.compile(
    r"^(?P<indent>[ \t]*)<!--\s*AGG-INSERT:\s*core-rules-dsl-reference\.xml\s*-->[ \t]*$",
    re.M,
)

ESSENTIAL_ROOT_OPEN_RE = re.compile(
    r"<core-rules-essential\b[^>]*>"
)
ESSENTIAL_ROOT_CLOSE_RE = re.compile(r"</core-rules-essential>\s*$")

DSL_ROOT_OPEN_RE = re.compile(r"<core-rules-dsl-reference\b[^>]*>")
DSL_ROOT_CLOSE_RE = re.compile(r"</core-rules-dsl-reference>\s*$")

AUTOGEN_HEADER = (
    "<!--\n"
    "  ============================================================\n"
    "  AUTOGEN — DO NOT EDIT\n"
    "  Sources:\n"
    "    · core/core-rules-essential.xml      (skeleton + insertion marker)\n"
    "    · core/core-rules-dsl-reference.xml  (supported-tags subset)\n"
    "  Generator: scripts/sync-core-rules-aggregate.py (v4.2 PR-7 / O23 / D-AGG-1)\n"
    "  本文件由聚合脚本生成；任何手改将被 CI Check 18 (sync-core-rules-aggregate)\n"
    "  以及 Check 10 (system-prompt-sync 间接) 拦截。\n"
    "  编辑请改两个源文件之一，然后运行：\n"
    "    python3 mobile-qa-workflow/scripts/sync-core-rules-aggregate.py --write\n"
    "  ============================================================\n"
    "-->\n"
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


LEADING_COMMENT_RE = re.compile(r"\A\n[ \t]*<!--.*?-->[ \t]*\n+", re.S)


def _extract_essential_body(text: str) -> str:
    """从 essential.xml 中抽取 root 内 body，去掉首部说明注释块。

    说明性注释块的语义已固化到聚合产物的 AUTOGEN 警告头中，源文件内的说明注释块不
    再回流到聚合产物（避免重复 / 字节漂移）。
    """
    m_open = ESSENTIAL_ROOT_OPEN_RE.search(text)
    if not m_open:
        raise SystemExit(
            f"::error::{ESSENTIAL_REL} 未找到 <core-rules-essential ...> 根标签"
        )
    body = text[m_open.end():]
    body = ESSENTIAL_ROOT_CLOSE_RE.sub("", body)
    stripped = LEADING_COMMENT_RE.sub("", body)
    if stripped != body:
        stripped = "\n" + stripped.lstrip("\n")
    return stripped.rstrip("\n")


def _extract_dsl_body(text: str) -> str:
    """从 dsl-reference.xml 中抽取 root 内 body，去掉首部说明注释块（同 essential 处理）。"""
    m_open = DSL_ROOT_OPEN_RE.search(text)
    if not m_open:
        raise SystemExit(
            f"::error::{DSL_REL} 未找到 <core-rules-dsl-reference ...> 根标签"
        )
    body = text[m_open.end():]
    body = DSL_ROOT_CLOSE_RE.sub("", body)
    body = LEADING_COMMENT_RE.sub("", body)
    return body.strip("\n")



def aggregate(workflow_root: Path = WORKFLOW_ROOT) -> str:
    """聚合 essential + dsl-reference 为 core-rules.xml 文本。

    缩进契约（D-AGG-1）：
      · essential.xml 与 dsl-reference.xml 内 body 内容均以"4 空格基础缩进"撰写，
        与原 core-rules.xml 一致；
      · marker 行 `    <!-- AGG-INSERT: ... -->` 自身处于 4 空格缩进，整行被 dsl body
        替换（dsl body 自带匹配的 4 空格基础缩进），保持原始扁平结构。
    """
    essential_text = _read(workflow_root / ESSENTIAL_REL)
    dsl_text = _read(workflow_root / DSL_REL)

    essential_body = _extract_essential_body(essential_text)
    dsl_body = _extract_dsl_body(dsl_text)

    m_marker = INSERT_MARKER_RE.search(essential_body)
    if not m_marker:
        raise SystemExit(
            f"::error::{ESSENTIAL_REL} 未找到 AGG-INSERT 占位标记"
        )

    new_body = (
        essential_body[: m_marker.start()]
        + dsl_body
        + essential_body[m_marker.end():]
    )

    aggregated_open = (
        f'<core-rules id="{AGGREGATE_ID}" name="{AGGREGATE_NAME}">'
    )
    aggregated = (
        AUTOGEN_HEADER
        + aggregated_open
        + new_body
        + "\n</core-rules>\n"
    )
    return aggregated


def cmd_write(workflow_root: Path) -> int:
    target = workflow_root / TARGET_REL
    new_text = aggregate(workflow_root)
    target.write_text(new_text, encoding="utf-8")
    print(f"OK: 写入 {target} ({len(new_text.splitlines())} 行)")
    return 0


def cmd_check(workflow_root: Path) -> int:
    target = workflow_root / TARGET_REL
    if not target.is_file():
        print(
            f"::error::{TARGET_REL} 不存在；请先运行 --write 生成聚合产物",
            file=sys.stderr,
        )
        return 1
    expected = aggregate(workflow_root)
    actual = _read(target)
    if expected == actual:
        print(f"OK: {TARGET_REL} 与两源同步（{len(actual.splitlines())} 行）")
        return 0
    print(
        f"::error::{TARGET_REL} 与源文件不同步；请运行：\n"
        f"  python3 mobile-qa-workflow/scripts/sync-core-rules-aggregate.py --write",
        file=sys.stderr,
    )
    expected_lines = expected.splitlines()
    actual_lines = actual.splitlines()
    diff_count = 0
    for i in range(min(len(expected_lines), len(actual_lines))):
        if expected_lines[i] != actual_lines[i]:
            print(
                f"  line {i + 1}:\n    expected: {expected_lines[i]!r}\n    actual:   {actual_lines[i]!r}",
                file=sys.stderr,
            )
            diff_count += 1
            if diff_count >= 5:
                break
    if len(expected_lines) != len(actual_lines):
        print(
            f"  行数差异: expected={len(expected_lines)} actual={len(actual_lines)}",
            file=sys.stderr,
        )
    return 1


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="sync-core-rules-aggregate.py (v4.2 PR-7 / O23 / D-AGG-1)"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="对账模式（CI 用）")
    group.add_argument("--write", action="store_true", help="写入模式（本地编辑后用）")
    parser.add_argument(
        "--workflow-root",
        type=Path,
        default=WORKFLOW_ROOT,
        help="workflow 根目录（默认从脚本路径推断）",
    )
    args = parser.parse_args(argv)
    wfr = args.workflow_root.resolve()

    if args.write:
        return cmd_write(wfr)
    return cmd_check(wfr)


if __name__ == "__main__":
    sys.exit(main())
