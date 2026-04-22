#!/usr/bin/env python3
"""test_sync_core_rules_aggregate.py — sync-core-rules-aggregate.py 单测
（v4.2 PR-7 / O23 / D-AGG-1）

覆盖：
  - --check：clean main 应通过（聚合产物 = aggregate(essential + dsl-reference)）
  - --check：注入漂移到 essential / dsl-reference / 聚合产物 任一后必报错
  - --write：写出后再 --check 必通过（幂等）
  - aggregate() 输出必须含 <core-rules id="..." name="..."> 根 + AUTOGEN 警告头
  - aggregate() 输出必须含 <supported-tags> / <input-protocol> / <workflow-result-protocol>
    / <human-review-protocol>（保证 build-system-prompt.py 4 处正则抽取仍命中）
  - aggregate() 输出按 marker 注入 dsl body，不引入双倍缩进
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOW_ROOT = REPO_ROOT / "mobile-qa-workflow"
SCRIPT = WORKFLOW_ROOT / "scripts" / "sync-core-rules-aggregate.py"

ESSENTIAL = WORKFLOW_ROOT / "core" / "core-rules-essential.xml"
DSL_REF = WORKFLOW_ROOT / "core" / "core-rules-dsl-reference.xml"
TARGET = WORKFLOW_ROOT / "core" / "core-rules.xml"

import importlib.util as _ilu

_spec = _ilu.spec_from_file_location("sync_core_rules_aggregate", str(SCRIPT))
assert _spec is not None and _spec.loader is not None
sync_module = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(sync_module)


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )


class TestCheckMode(unittest.TestCase):
    def test_check_passes_on_clean_main(self):
        result = _run(["--check"])
        self.assertEqual(
            result.returncode, 0,
            msg=f"--check 应在 clean main 通过\nstdout={result.stdout}\nstderr={result.stderr}",
        )
        self.assertIn("OK:", result.stdout)


class TestWriteMode(unittest.TestCase):
    def test_write_then_check_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            tmp_workflow = Path(td) / "mobile-qa-workflow"
            shutil.copytree(WORKFLOW_ROOT, tmp_workflow, symlinks=True)

            r1 = subprocess.run(
                [sys.executable, str(SCRIPT), "--write",
                 f"--workflow-root={tmp_workflow}"],
                capture_output=True, text=True,
            )
            self.assertEqual(r1.returncode, 0, msg=r1.stderr)
            r2 = subprocess.run(
                [sys.executable, str(SCRIPT), "--check",
                 f"--workflow-root={tmp_workflow}"],
                capture_output=True, text=True,
            )
            self.assertEqual(r2.returncode, 0, msg=r2.stderr)


class TestDriftDetection(unittest.TestCase):
    def _setup_temp(self) -> tuple[tempfile.TemporaryDirectory, Path]:
        td = tempfile.TemporaryDirectory()
        tmp_workflow = Path(td.name) / "mobile-qa-workflow"
        shutil.copytree(WORKFLOW_ROOT, tmp_workflow, symlinks=True)
        return td, tmp_workflow

    def test_drift_in_aggregated_target_detected(self):
        td, tmp_workflow = self._setup_temp()
        try:
            target = tmp_workflow / "core" / "core-rules.xml"
            target.write_text(
                target.read_text() + "\n<!-- drift -->\n",
                encoding="utf-8",
            )
            r = subprocess.run(
                [sys.executable, str(SCRIPT), "--check",
                 f"--workflow-root={tmp_workflow}"],
                capture_output=True, text=True,
            )
            self.assertEqual(r.returncode, 1)
            self.assertIn("不同步", r.stderr)
        finally:
            td.cleanup()

    def test_drift_in_essential_detected(self):
        td, tmp_workflow = self._setup_temp()
        try:
            ess = tmp_workflow / "core" / "core-rules-essential.xml"
            text = ess.read_text()
            text = text.replace(
                '<rule n="1">step 按精确的数字顺序执行 (1, 2, 3...)</rule>',
                '<rule n="1">DRIFT-INJECTED</rule>',
            )
            ess.write_text(text, encoding="utf-8")
            r = subprocess.run(
                [sys.executable, str(SCRIPT), "--check",
                 f"--workflow-root={tmp_workflow}"],
                capture_output=True, text=True,
            )
            self.assertEqual(r.returncode, 1)
            self.assertIn("不同步", r.stderr)
        finally:
            td.cleanup()

    def test_drift_in_dsl_reference_detected(self):
        td, tmp_workflow = self._setup_temp()
        try:
            dsl = tmp_workflow / "core" / "core-rules-dsl-reference.xml"
            text = dsl.read_text()
            text = text.replace(
                '<tag name="flow"><rule>定义工作流程的顶层容器</rule></tag>',
                '<tag name="flow"><rule>DRIFT-INJECTED</rule></tag>',
            )
            dsl.write_text(text, encoding="utf-8")
            r = subprocess.run(
                [sys.executable, str(SCRIPT), "--check",
                 f"--workflow-root={tmp_workflow}"],
                capture_output=True, text=True,
            )
            self.assertEqual(r.returncode, 1)
            self.assertIn("不同步", r.stderr)
        finally:
            td.cleanup()


class TestAggregateOutput(unittest.TestCase):
    """aggregate() 函数输出形态断言（保护下游消费者契约）。"""

    def setUp(self) -> None:
        self.text = sync_module.aggregate(WORKFLOW_ROOT)

    def test_root_is_core_rules(self):
        self.assertTrue(
            re.search(
                r'<core-rules\s+id="mobile-qa/core-rules\.xml"\s+name="Mobile QA Workflow Core Rules">',
                self.text,
            ),
            msg="聚合产物根标签必须重命名为 <core-rules ...>",
        )
        self.assertTrue(self.text.rstrip().endswith("</core-rules>"))

    def test_autogen_header_present(self):
        self.assertIn("AUTOGEN — DO NOT EDIT", self.text)
        self.assertIn("sync-core-rules-aggregate.py", self.text)

    def test_no_source_root_tags_leak(self):
        """essential / dsl-reference 的根标签不得出现在聚合产物中。"""
        self.assertNotIn("<core-rules-essential", self.text)
        self.assertNotIn("</core-rules-essential>", self.text)
        self.assertNotIn("<core-rules-dsl-reference", self.text)
        self.assertNotIn("</core-rules-dsl-reference>", self.text)

    def test_no_agg_insert_marker_leak(self):
        """marker 注释 `<!-- AGG-INSERT: core-rules-dsl-reference.xml -->`
        本身不得出现在聚合产物 body 中（AUTOGEN header 中作为说明文字
        提到 'AGG-INSERT marker' 字眼属于固定描述，与 marker 注释不同）。"""
        self.assertNotIn("AGG-INSERT: core-rules-dsl-reference.xml", self.text)

    def test_build_system_prompt_extraction_anchors_present(self):
        """build-system-prompt.py 在 L1 阶段用 4 处正则抽取本聚合产物，
        必须保证下列锚点全部存在（详见 scripts/build-system-prompt.py
        build_l1_execution_rules）。"""
        for pat in [
            r"^\s*<WORKFLOW-RULES\b",
            r"^\s*<input-protocol\b",
            r"^\s*<workflow-result-protocol\b",
            r"^\s*<human-review-protocol\b",
            r'^\s*<tag name="phase-abort">',
            r'^\s*<tag name="phase-complete">',
        ]:
            self.assertRegex(
                self.text, re.compile(pat, re.M),
                msg=f"build-system-prompt.py 抽取锚点缺失: {pat}",
            )

    def test_supported_tags_indent_is_four_spaces(self):
        """注入后 <supported-tags> 必须保持 4 空格基础缩进（与原 core-rules.xml 一致）。"""
        self.assertRegex(
            self.text,
            re.compile(r'^    <supported-tags\b', re.M),
            msg="<supported-tags> 必须以 4 空格开头（无双倍缩进）",
        )

    def test_aggregate_matches_committed_target(self):
        """aggregate() 输出必须 = 当前提交在 core-rules.xml 中的内容（防漂移）。"""
        committed = TARGET.read_text(encoding="utf-8")
        self.assertEqual(
            self.text, committed,
            msg="aggregate() 输出与 core/core-rules.xml 不一致；"
                "请运行 --write 同步或更新源文件",
        )


if __name__ == "__main__":
    unittest.main()
