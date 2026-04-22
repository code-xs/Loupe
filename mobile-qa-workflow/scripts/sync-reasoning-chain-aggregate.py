#!/usr/bin/env python3
"""sync-reasoning-chain-aggregate.py (v4.2 PR-7 / O24 / D-AGG-2 / R24-1 / C1)

把 reference/reasoning-chain-core.md + 4 个 reasoning-guide-*.md 聚合为
唯一下游产物 reference/reasoning-chain.md。PR-7 起 reasoning-chain.md = 生成产物
（C1 静态拼贴定版），禁止手改；P3 step 5 默认按 R24-1 算法分类加载 core + 单 guide，
未命中则 fallback 加载 core + 4 guides 全文（reasoning-chain.md 也作为便捷加载备选）。

聚合契约（D-AGG-2）：
  · core.md 是骨架，含唯一占位标记 `<!-- AGG-INSERT-GUIDES -->`
  · 每个 guide 文件内的 `<!-- AGG-INJECT-START --> ... <!-- AGG-INJECT-END -->`
    区块 body 是 inject 内容（区块外是文件级 header / 加载入口说明）
  · 注入顺序固定：functional → ui → network → compat（与 R24-1 表行序一致）
  · 脚本步骤：
      1. 读 core.md，剥掉首部说明注释块
      2. 读 4 个 guide 文件，依次抽取 INJECT 区块 body
      3. 把 4 个 inject body 用单空行连接，替换 core.md 中的 AGG-INSERT-GUIDES marker
      4. 在文件首插入 AUTOGEN 警告注释
      5. 写出（--write）或对账（--check）

CI（Check 20 / required）：
  · workflow 走 `--check`：若 core / 任一 guide 已改但 reasoning-chain.md
    未同步，构建失败并提示运行 `--write`
  · 工程师本地：编辑两个源文件后必须运行 `python3 scripts/sync-reasoning-chain-aggregate.py --write`

用法：
  python3 mobile-qa-workflow/scripts/sync-reasoning-chain-aggregate.py --check
  python3 mobile-qa-workflow/scripts/sync-reasoning-chain-aggregate.py --write
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Optional


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_ROOT = REPO_ROOT / "mobile-qa-workflow"

CORE_REL = "reference/reasoning-chain-core.md"
TARGET_REL = "reference/reasoning-chain.md"

GUIDE_ORDER = ["functional", "ui", "network", "compat"]
GUIDE_REL_TEMPLATE = "reference/reasoning-guide-{kind}.md"

INSERT_MARKER_RE = re.compile(
    r"^(?P<indent>[ \t]*)<!--\s*AGG-INSERT-GUIDES\s*-->[ \t]*$",
    re.M,
)

INJECT_BLOCK_RE = re.compile(
    r"<!--\s*AGG-INJECT-START\s*-->\s*\n(?P<body>.*?)\n[ \t]*<!--\s*AGG-INJECT-END\s*-->",
    re.S,
)

LEADING_COMMENT_AFTER_INTRO_RE = re.compile(
    r"(\A# [^\n]+\n\n[^\n]+\n\n)<!--.*?-->\s*\n+",
    re.S,
)

AUTOGEN_HEADER = (
    "<!--\n"
    "  ============================================================\n"
    "  AUTOGEN — DO NOT EDIT\n"
    "  Sources:\n"
    "    · reference/reasoning-chain-core.md             (skeleton + insertion marker)\n"
    "    · reference/reasoning-guide-functional.md       (inject #1)\n"
    "    · reference/reasoning-guide-ui.md               (inject #2)\n"
    "    · reference/reasoning-guide-network.md          (inject #3)\n"
    "    · reference/reasoning-guide-compat.md           (inject #4)\n"
    "  Generator: scripts/sync-reasoning-chain-aggregate.py (v4.2 PR-7 / O24 / D-AGG-2 / C1)\n"
    "  本文件由聚合脚本生成；任何手改将被 CI Check 20 (sync-reasoning-chain-aggregate)\n"
    "  以及 Check 10 (system-prompt-sync 间接) 拦截。\n"
    "  编辑请改 5 个源文件之一，然后运行：\n"
    "    python3 mobile-qa-workflow/scripts/sync-reasoning-chain-aggregate.py --write\n"
    "  ============================================================\n"
    "-->\n"
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _strip_core_leading_comment(text: str) -> str:
    """跳过 core.md 首部紧跟 intro 的说明注释块。

    保留：`# 标题\n\n<intro段>\n\n` 然后跳过紧随的 `<!-- ... -->\n+` 块。
    若没有匹配则原样返回（向后兼容）。
    """
    m = LEADING_COMMENT_AFTER_INTRO_RE.match(text)
    if not m:
        return text
    return m.group(1) + text[m.end():]


def _extract_guide_inject(text: str, guide_name: str) -> str:
    m = INJECT_BLOCK_RE.search(text)
    if not m:
        raise SystemExit(
            f"::error::{guide_name} 未找到 AGG-INJECT-START / AGG-INJECT-END 区块"
        )
    return m.group("body").rstrip()


def aggregate(workflow_root: Path = WORKFLOW_ROOT) -> str:
    """聚合 core + 4 guides 为 reasoning-chain.md 文本。

    缩进契约（D-AGG-2）：
      · core.md 与 guide 文件的 inject body 均使用 0 缩进 markdown；
      · marker 行 `<!-- AGG-INSERT-GUIDES -->` 自身处于 0 缩进，整行被合并的 guide
        body 替换（保持原 reasoning-chain.md 的扁平结构）。

    顺序契约：
      · 注入顺序固定 functional → ui → network → compat（与 R24-1 真值表行序一致）；
      · 各 guide 之间用单空行分隔（与原 reasoning-chain.md 的子节排版一致）。
    """
    core_text = _strip_core_leading_comment(_read(workflow_root / CORE_REL))

    guide_bodies: list[str] = []
    for kind in GUIDE_ORDER:
        rel = GUIDE_REL_TEMPLATE.format(kind=kind)
        gtext = _read(workflow_root / rel)
        guide_bodies.append(_extract_guide_inject(gtext, rel))

    joined_guides = "\n\n".join(guide_bodies)

    m_marker = INSERT_MARKER_RE.search(core_text)
    if not m_marker:
        raise SystemExit(
            f"::error::{CORE_REL} 未找到 AGG-INSERT-GUIDES 占位标记"
        )

    new_text = (
        core_text[: m_marker.start()]
        + joined_guides
        + core_text[m_marker.end():]
    )

    aggregated = AUTOGEN_HEADER + "\n" + new_text
    if not aggregated.endswith("\n"):
        aggregated += "\n"
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
        print(f"OK: {TARGET_REL} 与 5 源同步（{len(actual.splitlines())} 行）")
        return 0
    print(
        f"::error::{TARGET_REL} 与源文件不同步；请运行：\n"
        f"  python3 mobile-qa-workflow/scripts/sync-reasoning-chain-aggregate.py --write",
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
        description="sync-reasoning-chain-aggregate.py (v4.2 PR-7 / O24 / D-AGG-2)"
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
