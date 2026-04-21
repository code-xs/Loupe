#!/usr/bin/env python3
"""migrate-workflow-status-v3-to-v4.py

将 mobile-qa-workflow/<workspace>/workflow-status.yaml 从 schema_version=3 迁移到 4。

Requires:
  · Python >= 3.9
  · ruamel.yaml >= 0.17     # pip install -r mobile-qa-workflow/scripts/requirements.txt
                            # 或: pip install 'ruamel.yaml>=0.17'

迁移动作（与 core/workflow-status-template.yaml v4.1 / v4.2 PR-2 schema 一一对应）:
  · schema_version: 3 -> 4
  · 注入 6 个新顶层字段（缺失即注入默认值，存在即保留原值，幂等）:
      - fix_fanout_mode: None
      - phase_history: []
      - user_inputs: {}
      - non_bug_context: None
      - parse_error_count: 0
      - non_bug_user_choice: None        # 顶层镜像白名单（v4.1 起步集，v4.2 收敛删除）
  · v4.2 PR-2 修订（O7 / ADR-007 v4.2 修订段落）：已废弃字段不再注入：
      - rca_fanout_mode_snapshot（删除：方案 A phase_history 反查已是主路径）
      - fix_strategy_mode（合并到 fix_fanout_mode）
    存量 v4 会话使用 `--cleanup-v4-deprecated` 子命令幂等清理。

不做的事:
  · 不重命名任何 v3 已有字段（D7：fanout_mode 保持不变）
  · 不修改 specialized_workflow 嵌套块（PRESERVE_FORMAT 区域）
  · 不写入 current_phase_result（D1：运行时变量，不入 schema）
  · 不支持 v4 → v3 反向迁移

用法:
  python migrate-workflow-status-v3-to-v4.py <path-to-workflow-status.yaml> [--dry-run] [--no-strict]
  python migrate-workflow-status-v3-to-v4.py <path-to-workflow-status.yaml> --cleanup-v4-deprecated [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from ruamel.yaml import YAML
    from ruamel.yaml.comments import CommentedMap, CommentedSeq
except ImportError:
    sys.stderr.write(
        "error: requires ruamel.yaml >= 0.17\n"
        "  install: pip install -r mobile-qa-workflow/scripts/requirements.txt\n"
        "  or:      pip install 'ruamel.yaml>=0.17'\n"
    )
    sys.exit(2)

NEW_FIELDS_DEFAULTS: list[tuple[str, object]] = [
    ("fix_fanout_mode", None),
    ("phase_history", CommentedSeq()),
    ("user_inputs", CommentedMap()),
    ("non_bug_context", None),
    ("parse_error_count", 0),
    ("non_bug_user_choice", None),
]
# v4.2 PR-2 修订（O7 / O8 / ADR-007 v4.2 修订段落）：
# 已废弃字段不再注入：rca_fanout_mode_snapshot（删除）/ fix_strategy_mode（合并到 fix_fanout_mode）。
# 存量会话清理：使用 `--cleanup-v4-deprecated` 子命令幂等处理。
DEPRECATED_FIELDS_V4_2: list[str] = [
    "rca_fanout_mode_snapshot",
    "fix_strategy_mode",
]

# 新字段的锚点：必须插入到该字段之前，确保新字段全部落入
# [PRESERVE_FORMAT] ↔ [END_PRESERVE_FORMAT] 区间内（v1.2 review Finding #2 收口）。
INSERT_ANCHOR_KEY = "specialized_workflow"


def _represent_none_as_null(self, data):
    """让 None 显式渲染为 'null'，与 core/workflow-status-template.yaml v4.1 风格一致。"""
    return self.represent_scalar("tag:yaml.org,2002:null", "null")


def make_yaml() -> YAML:
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.representer.add_representer(type(None), _represent_none_as_null)
    return yaml


def _find_insert_pos(doc: CommentedMap, anchor_key: str) -> int | None:
    """返回 anchor_key 在 doc.keys() 中的 0-based 位置；不存在返回 None（由调用方决定降级策略）。"""
    for idx, key in enumerate(doc.keys()):
        if key == anchor_key:
            return idx
    return None


def migrate(doc: CommentedMap, *, strict: bool = True) -> tuple[bool, list[str]]:
    """对单个 workflow-status doc 执行迁移；返回 (是否变更, 动作日志)。"""
    log: list[str] = []
    current = doc.get("schema_version")

    if current == 4:
        log.append("noop: schema_version already 4 (idempotent)")
        return False, log

    if current != 3:
        if strict:
            raise ValueError(f"unexpected schema_version: {current!r} (expect 3)")
        log.append(f"warn: unexpected schema_version {current!r}, force migrate")

    doc["schema_version"] = 4
    log.append("set schema_version: 3 -> 4")

    pos = _find_insert_pos(doc, INSERT_ANCHOR_KEY)
    if pos is None:
        # 锚点缺失会让新字段尾插到 # [END_PRESERVE_FORMAT] 之外，违反顶层
        # "严格 YAML 格式 + LLM 禁止修改结构" 契约（v1.2 review Finding #2 + v1.3 Finding #15）。
        msg = (
            f"insert anchor key '{INSERT_ANCHOR_KEY}' not found in document; "
            f"refusing to inject new fields outside [PRESERVE_FORMAT] region"
        )
        if strict:
            raise ValueError(msg)
        log.append(f"warn: {msg}; falling back to append at EOF (--no-strict)")
        insert_pos = len(doc)
    else:
        insert_pos = pos
        log.append(
            f"insert anchor: '{INSERT_ANCHOR_KEY}' at idx {insert_pos} "
            f"(new fields will land BEFORE it, inside [PRESERVE_FORMAT])"
        )

    for key, default in NEW_FIELDS_DEFAULTS:
        if key in doc:
            log.append(f"keep existing: {key} = {doc[key]!r}")
            continue
        doc.insert(insert_pos, key, default)
        insert_pos += 1
        log.append(f"inject: {key} = {default!r}")

    return True, log


def cleanup_v4_deprecated(doc: CommentedMap) -> tuple[bool, list[str]]:
    """v4 内部清理（v4.2 PR-2 / O7 + O8）：

    幂等地把存量会话的 fix_strategy_mode 拷贝到 fix_fanout_mode（仅当后者缺失/空），
    再删除 rca_fanout_mode_snapshot 与 fix_strategy_mode 两个已废弃字段。

    返回 (是否变更, 动作日志)。
    """
    log: list[str] = []
    changed = False

    if "fix_strategy_mode" in doc and doc.get("fix_strategy_mode") is not None:
        if not doc.get("fix_fanout_mode"):
            doc["fix_fanout_mode"] = doc["fix_strategy_mode"]
            log.append(
                f"copy: fix_strategy_mode -> fix_fanout_mode "
                f"(value={doc['fix_strategy_mode']!r}; previous fix_fanout_mode was empty)"
            )
            changed = True
        else:
            log.append(
                f"skip-copy: fix_fanout_mode already set "
                f"(={doc['fix_fanout_mode']!r}); leaving fix_strategy_mode alone for delete"
            )

    for field in DEPRECATED_FIELDS_V4_2:
        if field in doc:
            del doc[field]
            log.append(f"remove: {field} (v4.2 PR-2 deprecated)")
            changed = True
        else:
            log.append(f"noop: {field} not present (idempotent)")

    if not changed:
        log.append("noop: no v4.2 deprecated fields to clean (idempotent)")
    return changed, log


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate workflow-status.yaml v3 -> v4")
    parser.add_argument("path", type=Path, help="path to workflow-status.yaml")
    parser.add_argument("--dry-run", action="store_true", help="print planned changes without writing")
    parser.add_argument("--no-strict", action="store_true", help="allow unknown schema_version (force migrate)")
    parser.add_argument(
        "--cleanup-v4-deprecated",
        action="store_true",
        help=(
            "对存量 v4 会话做 v4.2 PR-2 字段清理（拷值 fix_strategy_mode -> fix_fanout_mode + "
            "删除 rca_fanout_mode_snapshot / fix_strategy_mode），与主路径迁移互斥"
        ),
    )
    args = parser.parse_args()

    if not args.path.is_file():
        sys.stderr.write(f"error: not a file: {args.path}\n")
        return 2

    yaml = make_yaml()

    with args.path.open("r", encoding="utf-8") as f:
        doc = yaml.load(f)

    if args.cleanup_v4_deprecated:
        try:
            changed, log = cleanup_v4_deprecated(doc)
        except ValueError as e:
            sys.stderr.write(f"error: {e}\n")
            return 1
        for line in log:
            print(f"[cleanup-v4-deprecated] {line}")
        if not changed:
            return 0
        if args.dry_run:
            print("[cleanup-v4-deprecated] --dry-run: no file written")
            return 0
        with args.path.open("w", encoding="utf-8") as f:
            yaml.dump(doc, f)
        print(f"[cleanup-v4-deprecated] wrote: {args.path}")
        return 0

    try:
        changed, log = migrate(doc, strict=not args.no_strict)
    except ValueError as e:
        sys.stderr.write(f"error: {e}\n")
        return 1

    for line in log:
        print(f"[migrate] {line}")

    if not changed:
        return 0

    if args.dry_run:
        print("[migrate] --dry-run: no file written")
        return 0

    with args.path.open("w", encoding="utf-8") as f:
        yaml.dump(doc, f)
    print(f"[migrate] wrote: {args.path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
