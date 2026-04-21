#!/usr/bin/env python3
"""test_build_system_prompt.py — build-system-prompt.py 单元测试（v4.2 PR-2 / GEN-N2）

覆盖：
  - verify 模式：clean main 应通过；注入故意漂移后必须报错
  - --mode=full：在 ALLOW_FIRST_BUILD 未设置 + 输出 system-prompt.md 时必须退出 3
  - --mode=full：使用其他 filename 或设置 ALLOW_FIRST_BUILD=1 时必须可跑
  - --mode=layered：输出 5 个分层文件
  - L0/L1/L3 关键 token 断言（V1 §6 第 1 条 OVHSC 不可触动）
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOW_ROOT = REPO_ROOT / "mobile-qa-workflow"
SCRIPT = WORKFLOW_ROOT / "scripts" / "build-system-prompt.py"

# 直接 import 模块用于 unit 级断言
SCRIPTS_DIR = WORKFLOW_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
import importlib.util as _ilu

_spec = _ilu.spec_from_file_location("build_system_prompt", str(SCRIPT))
assert _spec is not None and _spec.loader is not None
build_module = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(build_module)


class TestVerifyMode(unittest.TestCase):
    def test_verify_passes_on_clean_main(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--mode=verify"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, msg=f"stderr: {result.stderr}")

    def test_verify_fails_on_injected_drift(self):
        # 把整套 mobile-qa-workflow 复制到临时目录，注入非法 state 写入到 workflow.xml，
        # 期望 verify 检测到非法 state 并退出非 0
        with tempfile.TemporaryDirectory() as td:
            tmp_root = Path(td) / "mobile-qa-workflow"
            shutil.copytree(WORKFLOW_ROOT, tmp_root)
            wf = tmp_root / "core" / "workflow.xml"
            text = wf.read_text(encoding="utf-8")
            wf.write_text(
                text
                + "\n<!-- inject illegal state for test -->\n"
                + '<action>更新 {workflow_status}：current_state = NotAState</action>\n',
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--mode=verify",
                    "--workflow-root",
                    str(tmp_root),
                ],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0, msg=f"stdout: {result.stdout}")
            self.assertIn("NotAState", result.stderr)


class TestFullMode(unittest.TestCase):
    def test_full_mode_blocked_when_targeting_system_prompt(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "system-prompt.md"
            env = os.environ.copy()
            env.pop("ALLOW_FIRST_BUILD", None)
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--mode=full", "--output", str(target)],
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(result.returncode, 3, msg=f"stderr: {result.stderr}")
            self.assertIn("禁止", result.stderr)

    def test_full_mode_allowed_with_env_flag(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "system-prompt.md"
            env = os.environ.copy()
            env["ALLOW_FIRST_BUILD"] = "1"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--mode=full", "--output", str(target)],
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(result.returncode, 0, msg=f"stderr: {result.stderr}")
            self.assertTrue(target.exists())
            self.assertGreater(len(target.read_text().splitlines()), 100)

    def test_full_mode_allowed_for_other_filename(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "preview.md"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--mode=full", "--output", str(target)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=f"stderr: {result.stderr}")
            self.assertTrue(target.exists())


class TestLayeredMode(unittest.TestCase):
    def test_layered_outputs_5_files(self):
        with tempfile.TemporaryDirectory() as td:
            outdir = Path(td) / "layered"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--mode=layered",
                    "--output-dir",
                    str(outdir),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=f"stderr: {result.stderr}")
            files = sorted(p.name for p in outdir.iterdir())
            self.assertEqual(
                files,
                [
                    "L0-identity.md",
                    "L1-execution-rules.md",
                    "L2-phase-logic.md",
                    "L3-reasoning-toolbox.md",
                    "L4-platform-knowledge.md",
                ],
            )


class TestLayerBuilders(unittest.TestCase):
    def test_l0_contains_six_phase_sequence(self):
        text = build_module.build_l0_identity(WORKFLOW_ROOT)
        for phase in (
            "qa-intake",
            "qa-spec-definition",
            "qa-root-cause",
            "qa-fix-design",
            "qa-fix-impl",
            "qa-verification",
        ):
            self.assertIn(phase, text, f"L0 missing phase: {phase}")

    def test_l1_contains_step_pause_protocol(self):
        text = build_module.build_l1_execution_rules(WORKFLOW_ROOT)
        self.assertIn("input-protocol", text)
        self.assertIn("result_field", text)
        self.assertIn("allowed_values", text)
        self.assertIn("workflow-result-protocol", text)

    def test_l3_preserves_ovhsc_full(self):
        text = build_module.build_l3_reasoning_toolbox(WORKFLOW_ROOT)
        for token in ("OBSERVE", "HYPOTHESIZE", "VERIFY", "SCORE", "CHAIN"):
            self.assertIn(token, text, f"L3 missing OVHSC step: {token}")
        self.assertIn("置信度", text)

    def test_l4_contains_platform_sections(self):
        text = build_module.build_l4_platform_knowledge(WORKFLOW_ROOT)
        self.assertIn("Android", text)
        self.assertIn("iOS", text)


if __name__ == "__main__":
    unittest.main()
