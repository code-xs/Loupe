#!/usr/bin/env python3
"""test_sync_reasoning_chain_aggregate.py — sync-reasoning-chain-aggregate.py 单测
（v4.2 PR-7 / O24 / D-AGG-2 / R24-1 / C1）

覆盖：
  - --check：clean main 应通过（聚合产物 = aggregate(core + 4 guides)）
  - --check：注入漂移到 core / 任一 guide / 聚合产物 任一后必报错
  - --write：写出后再 --check 必通过（幂等）
  - aggregate() 输出必须含 AUTOGEN 警告头 + 文件级标题保留
  - aggregate() 输出必须含 build-system-prompt.py L3 抽取的 3 个段头
    （## 推理链五步骤 / ## 推理链输出格式 / ## 置信度计算规则）
  - aggregate() 输出按固定顺序 functional → ui → network → compat 注入 4 个 guide
  - aggregate() 末尾以 4 个 guide 之一结束（兼容性类问题），不引入异常尾部
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
SCRIPT = WORKFLOW_ROOT / "scripts" / "sync-reasoning-chain-aggregate.py"

CORE = WORKFLOW_ROOT / "reference" / "reasoning-chain-core.md"
TARGET = WORKFLOW_ROOT / "reference" / "reasoning-chain.md"
GUIDE_FILES = {
    "functional": WORKFLOW_ROOT / "reference" / "reasoning-guide-functional.md",
    "ui": WORKFLOW_ROOT / "reference" / "reasoning-guide-ui.md",
    "network": WORKFLOW_ROOT / "reference" / "reasoning-guide-network.md",
    "compat": WORKFLOW_ROOT / "reference" / "reasoning-guide-compat.md",
}

import importlib.util as _ilu

_spec = _ilu.spec_from_file_location("sync_reasoning_chain_aggregate", str(SCRIPT))
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
            target = tmp_workflow / "reference" / "reasoning-chain.md"
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

    def test_drift_in_core_detected(self):
        td, tmp_workflow = self._setup_temp()
        try:
            core = tmp_workflow / "reference" / "reasoning-chain-core.md"
            text = core.read_text()
            text = text.replace(
                "## 推理链五步骤",
                "## 推理链五步骤-DRIFT",
                1,
            )
            core.write_text(text, encoding="utf-8")
            r = subprocess.run(
                [sys.executable, str(SCRIPT), "--check",
                 f"--workflow-root={tmp_workflow}"],
                capture_output=True, text=True,
            )
            self.assertEqual(r.returncode, 1)
            self.assertIn("不同步", r.stderr)
        finally:
            td.cleanup()

    def test_drift_in_each_guide_detected(self):
        for kind, path in GUIDE_FILES.items():
            with self.subTest(guide=kind):
                td, tmp_workflow = self._setup_temp()
                try:
                    g = tmp_workflow / "reference" / f"reasoning-guide-{kind}.md"
                    text = g.read_text()
                    text = text.replace(
                        "**OBSERVE 阶段重点**",
                        "**OBSERVE 阶段重点 [DRIFT]**",
                        1,
                    )
                    g.write_text(text, encoding="utf-8")
                    r = subprocess.run(
                        [sys.executable, str(SCRIPT), "--check",
                         f"--workflow-root={tmp_workflow}"],
                        capture_output=True, text=True,
                    )
                    self.assertEqual(r.returncode, 1, msg=f"{kind}: {r.stderr}")
                    self.assertIn("不同步", r.stderr)
                finally:
                    td.cleanup()


class TestAggregateOutput(unittest.TestCase):
    """aggregate() 函数输出形态断言（保护下游消费者契约）。"""

    def setUp(self) -> None:
        self.text = sync_module.aggregate(WORKFLOW_ROOT)

    def test_autogen_header_present(self):
        self.assertIn("AUTOGEN — DO NOT EDIT", self.text)
        self.assertIn("sync-reasoning-chain-aggregate.py", self.text)

    def test_file_title_preserved(self):
        self.assertRegex(
            self.text, re.compile(r"^# OVHSC 结构化推理链规范$", re.M),
            msg="文件级一级标题必须保留",
        )

    def test_no_marker_or_inject_tags_leak(self):
        self.assertNotIn("AGG-INSERT-GUIDES", self.text)
        self.assertNotIn("AGG-INJECT-START", self.text)
        self.assertNotIn("AGG-INJECT-END", self.text)

    def test_build_system_prompt_l3_anchors_present(self):
        """build-system-prompt.py 在 L3 阶段用 3 处正则抽取本聚合产物，
        必须保证下列段头全部存在（详见 scripts/build-system-prompt.py
        build_l3_reasoning_toolbox）。"""
        for pat in [
            r"^## 推理链五步骤$",
            r"^## 推理链输出格式$",
            r"^## 置信度计算规则$",
        ]:
            self.assertRegex(
                self.text, re.compile(pat, re.M),
                msg=f"build-system-prompt.py L3 抽取锚点缺失: {pat}",
            )

    def test_guide_subsections_in_fixed_order(self):
        """4 个 guide 的 ### 子节必须按 functional → ui → network → compat 顺序出现，
        与 R24-1 真值表行序一致。"""
        positions = []
        for header in [
            "### 功能类问题",
            "### UI/UX 类问题",
            "### 网络类问题",
            "### 兼容性类问题",
        ]:
            idx = self.text.find(header)
            self.assertGreater(idx, 0, msg=f"缺失子节: {header}")
            positions.append(idx)
        self.assertEqual(
            positions, sorted(positions),
            msg="4 个 guide 子节顺序不符（应为 功能 → UI/UX → 网络 → 兼容性）",
        )

    def test_aggregate_matches_committed_target(self):
        """aggregate() 输出必须 = 当前提交在 reasoning-chain.md 中的内容（防漂移）。"""
        committed = TARGET.read_text(encoding="utf-8")
        self.assertEqual(
            self.text, committed,
            msg="aggregate() 输出与 reference/reasoning-chain.md 不一致；"
                "请运行 --write 同步或更新源文件",
        )


if __name__ == "__main__":
    unittest.main()
