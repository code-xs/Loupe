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
                    "L5-subagent-inline-block.md",
                ],
                msg="v4.2 PR-7 / GEN-PR7：layered 应包含 6 个分层产物（新增 L5）",
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


# ──────────────────────────────────────────────────────────────────────
# v4.2 PR-6 / GEN-D3 单测增量（6 项）
# ──────────────────────────────────────────────────────────────────────


class TestGenD3Increments(unittest.TestCase):
    """GEN-D1 + GEN-D2 + GEN-D3 / verify_core_consistency v4.2 兼容 增量校验。"""

    def test_l1_includes_phase_abort_rule(self):
        """GEN-D1: build_l1 输出必须含 `## phase-abort 宏展开规则` 段（O21 / ADR-021）。"""
        text = build_module.build_l1_execution_rules(WORKFLOW_ROOT)
        self.assertIn("## phase-abort 宏展开规则", text)
        self.assertIn("update_config", text, "RULES-D4 update_config 第 3 步必须落地")

    def test_l1_includes_phase_complete_rule(self):
        """GEN-D1: build_l1 输出必须含 `## phase-complete 宏展开规则` 段。"""
        text = build_module.build_l1_execution_rules(WORKFLOW_ROOT)
        self.assertIn("## phase-complete 宏展开规则", text)

    def test_l1_includes_step_pause_routing_table(self):
        """GEN-D2: build_l1 输出必须含 8 项 state（含 Fix-Confirming）的 markdown 表格。"""
        text = build_module.build_l1_execution_rules(WORKFLOW_ROOT)
        self.assertIn("step-pause-registry 路由表", text)
        for state in (
            "Info-Insufficient",
            "Spec-Uncertain",
            "Non-Bug",
            "RCA-LowConfidence",
            "Curation-Failed",
            "Human-Review",
            "Fix-Confirming",
            "Boundary-Refined",
        ):
            self.assertIn(f"`{state}`", text, f"routing table missing state: {state}")

    def test_full_mode_emits_fix_confirming_in_enum(self):
        """GEN-D3: full mode 输出（含 L0 状态机段）必须含 Fix-Confirming。"""
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "preview.md"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--mode=full", "--output", str(target)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=f"stderr: {result.stderr}")
            content = target.read_text(encoding="utf-8")
            self.assertIn("Fix-Confirming", content)

    def test_full_mode_no_inline_step_pause(self):
        """GEN-D3: full mode 输出**不含** `<step-pause title=` 行（registry 形态除外）。"""
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "preview.md"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--mode=full", "--output", str(target)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=f"stderr: {result.stderr}")
            content = target.read_text(encoding="utf-8")
            for line in content.splitlines():
                stripped = line.strip()
                if stripped.startswith("<step-pause") and "title=" in stripped:
                    self.fail(f"inline step-pause leaked into full output: {line!r}")

    def test_verify_mode_passes_v42(self):
        """GEN-D3: verify mode 在含 Fix-Confirming enum 时通过（不报 illegal）。"""
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--mode=verify"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, msg=f"stderr: {result.stderr}")
        # 同时确认 ENUM_BLOCK_REGEX 升级后能解出 v4.2 完整集合
        from pathlib import Path as _P

        enum = build_module._extract_template_enum(
            _P(WORKFLOW_ROOT) / "core" / "workflow-status-template.yaml"
        )
        self.assertIn("Fix-Confirming", enum)
        self.assertGreaterEqual(len(enum), 15, f"v4.2 完整集合 应≥15 项，实际 {len(enum)}")


# ──────────────────────────────────────────────────────────────────────
# v4.2 PR-7 / GEN-PR7 单测增量（L5 SubAgent 等价内联块）
# ──────────────────────────────────────────────────────────────────────


class TestGenPR7L5SubagentInline(unittest.TestCase):
    """GEN-PR7 §4 第 3 条 / §2.2：L5 段必须从 core/core-rules-subagent.xml 同源抽取。"""

    def test_l5_extracts_subagent_context_block(self):
        text = build_module.build_l5_subagent_inline_block(WORKFLOW_ROOT)
        self.assertIn("# L5 · Limited 平台 SubAgent 等价内联块", text)
        self.assertIn("subagent-context", text)
        self.assertIn("子对话隔离 SubAgent", text)
        self.assertIn("missing_required_field", text)

    def test_l5_extracts_subagent_output_protocol_block(self):
        text = build_module.build_l5_subagent_inline_block(WORKFLOW_ROOT)
        self.assertIn("subagent-output-protocol", text)
        self.assertIn("置信度", text)
        self.assertIn("phase-abort", text)
        self.assertIn("invoke-subagent", text)

    def test_l5_emits_xml_code_blocks(self):
        text = build_module.build_l5_subagent_inline_block(WORKFLOW_ROOT)
        self.assertIn("```xml", text)
        self.assertIn("</subagent-context>", text)
        self.assertIn("</subagent-output-protocol>", text)

    def test_l5_handles_missing_source_gracefully(self):
        with tempfile.TemporaryDirectory() as td:
            tmp_root = Path(td) / "mobile-qa-workflow"
            shutil.copytree(WORKFLOW_ROOT, tmp_root)
            (tmp_root / "core" / "core-rules-subagent.xml").unlink()
            text = build_module.build_l5_subagent_inline_block(tmp_root)
            self.assertIn("L5", text)
            self.assertIn("缺失", text)

    def test_full_mode_includes_l5_section(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "preview.md"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--mode=full", "--output", str(target)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=f"stderr: {result.stderr}")
            content = target.read_text(encoding="utf-8")
            self.assertIn("# L5 · Limited 平台 SubAgent 等价内联块", content)
            self.assertIn("</subagent-output-protocol>", content)

    def test_layered_emits_l5_file(self):
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
            l5 = outdir / "L5-subagent-inline-block.md"
            self.assertTrue(l5.exists())
            body = l5.read_text(encoding="utf-8")
            self.assertIn("subagent-context", body)
            self.assertIn("subagent-output-protocol", body)

    def test_l5_source_is_subagent_xml_not_full_core_rules(self):
        """O25 关键约束：L5 必须从 subagent.xml 抽取，禁止把完整 core-rules.xml 文本嵌入。"""
        text = build_module.build_l5_subagent_inline_block(WORKFLOW_ROOT)
        self.assertNotIn("<WORKFLOW-RULES>", text, "L5 不应嵌入 WORKFLOW-RULES（编排层）")
        self.assertNotIn("<agent-taxonomy>", text, "L5 不应嵌入 agent-taxonomy（编排层）")
        self.assertNotIn("<available-agents>", text, "L5 不应嵌入 available-agents 表（编排层）")
        self.assertNotIn("<human-review-protocol>", text, "L5 不应嵌入 human-review-protocol（父对话）")


class TestGenPR7AutogenHeader(unittest.TestCase):
    """GEN-PR7：AUTOGEN 头必须列出 D-AGG-1 / D-AGG-2 / O25 三个新增源。"""

    def test_autogen_header_lists_pr7_sources(self):
        text = build_module.build_header_block(WORKFLOW_ROOT)
        self.assertIn("D-AGG-1", text, "AUTOGEN 头应标注 core-rules.xml 是 D-AGG-1 聚合产物")
        self.assertIn("D-AGG-2", text, "AUTOGEN 头应标注 reasoning-chain.md 是 D-AGG-2 聚合产物")
        self.assertIn("core-rules-subagent.xml", text, "AUTOGEN 头应列出 O25 新增源")


if __name__ == "__main__":
    unittest.main()
