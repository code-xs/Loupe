#!/usr/bin/env python3
"""build-system-prompt.py (v4.2 PR-2 / O17+ Stage 1)

从 core/ + phases/ + reference/ + agents/ 自动构建 system-prompt.md，输出 L0-L4
分层产物。本脚本是"最小完整实现"（v1.1 review Major 3 修订口径）：5 个 builder
全部可跑、三种 mode 全部可跑，禁止 NotImplementedError stub。

目标产物结构（与 V1.1 §3.3.17 Stage 2 表对齐）：
  L0: 核心身份（角色定义 + 6 阶段序列 + 状态机转换图）
  L1: 执行规则（步骤顺序 + ABORT 协议 + step-pause 输入规范）
  L2: 当前阶段逻辑（按 current_state 动态展开；默认全量 6 阶段）
  L3: 推理工具箱（OVHSC 五步 + 置信度公式 + Challenger 维度 + Arbiter）
  L4: 平台知识（按命中分类注入，全量时输出 Android + iOS 两段）

输出策略：
  - --mode=full        生成 Limited 平台单 prompt 模式产物（L0+L1+L2 全量+L3+L4 全量）
  - --mode=layered     生成 5 个独立片段文件（L0-identity.md / L1-execution-rules.md / ...）
  - --mode=verify      仅校验 core/ 关键 token 一致性，不输出文件（用于 CI sync 守门）

用法：
  python build-system-prompt.py --mode=verify
  python build-system-prompt.py --mode=full --output=preview.md
  python build-system-prompt.py --mode=layered --output-dir=build/system-prompt-layered/

⚠️ v4.2 PR-2 阶段：本脚本只交付，禁止运行 --mode=full 替换 system-prompt.md
   （H1 守门：见 check-build-system-prompt-precondition.sh + 本脚本内 ALLOW_FIRST_BUILD 门）。
   首次构建并替换在 PR-6 内执行（依赖 PR-4 O13a 已合入）。
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Optional


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_ROOT = REPO_ROOT / "mobile-qa-workflow"


# ──────────────────────────────────────────────────────────────────────
# 通用工具
# ──────────────────────────────────────────────────────────────────────

def _read(path: Path) -> str:
    """读取文件并返回字符串；保持简单错误传播。"""
    return path.read_text(encoding="utf-8")


def _extract_section(text: str, start_pattern: str, end_pattern: Optional[str] = None) -> str:
    """从 text 中按正则提取 start_pattern 起、到 end_pattern（或 EOF）止的段落。"""
    m = re.search(start_pattern, text, re.M)
    if not m:
        return ""
    start = m.start()
    if end_pattern is None:
        return text[start:]
    m2 = re.search(end_pattern, text[m.end():], re.M)
    if not m2:
        return text[start:]
    return text[start : m.end() + m2.start()]


# ──────────────────────────────────────────────────────────────────────
# L0: 核心身份
# ──────────────────────────────────────────────────────────────────────

PHASE_ORDER_FALLBACK = [
    "qa-intake",
    "qa-spec-definition",
    "qa-root-cause",
    "qa-fix-design",
    "qa-fix-impl",
    "qa-verification",
]

STATE_TRANSITIONS_HUMAN = """\
状态机概览（权威源 = core/workflow-status-template.yaml v4.1 完整集合）：
  Intake → Spec-Defining → (Spec-Uncertain ↺ | Context-Curating → Curation-Failed ↺)
       → Boundary-Refined → RCA-Designing → (RCA-LowConfidence ↺ | Fix-Designing)
       → Fix-Implementing → Verifying → Done
  Non-Bug 早退：Spec-Defining → Non-Bug → (Done | Spec-Defining 重审 | Human-Review)
  熔断兜底：任意 stop_state 累计触发 → Human-Review
"""


def _extract_phase_order(workflow_root: Path) -> list[str]:
    """从 workflow-model.yaml 中提取 6 阶段顺序；解析失败回退到硬编码。"""
    path = workflow_root / "core" / "workflow-model.yaml"
    if not path.is_file():
        return PHASE_ORDER_FALLBACK
    text = _read(path)
    phases: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^\s*-\s*\d+\.\s*(qa-[a-z-]+)\s*[:：]", line)
        if m:
            phases.append(m.group(1))
    return phases or PHASE_ORDER_FALLBACK


def build_l0_identity(workflow_root: Path = WORKFLOW_ROOT) -> str:
    """L0：从 SKILL.md / workflow-model.yaml / workflow-status-template.yaml 拼装核心身份段。"""
    skill_md = _read(workflow_root / "SKILL.md")
    intro_match = re.search(
        r"^# Mobile QA B2C Workflow .*?\n(.*?)(?=^##|\Z)",
        skill_md,
        re.S | re.M,
    )
    intro = (intro_match.group(0).strip() + "\n") if intro_match else ""

    phases = _extract_phase_order(workflow_root)
    phase_seq = "\n".join(f"  {idx + 1}. {p}" for idx, p in enumerate(phases))

    return (
        "# L0 · 核心身份\n\n"
        + intro
        + "\n## 6 阶段序列\n\n"
        + phase_seq
        + "\n\n## 状态机概览\n\n"
        + "```\n" + STATE_TRANSITIONS_HUMAN.rstrip() + "\n```\n"
    )


# ──────────────────────────────────────────────────────────────────────
# L1: 执行规则
# ──────────────────────────────────────────────────────────────────────

def build_l1_execution_rules(workflow_root: Path = WORKFLOW_ROOT) -> str:
    """L1：从 core-rules.xml 提取 WORKFLOW-RULES、step-pause input-protocol、workflow-result-protocol。"""
    core_rules = _read(workflow_root / "core" / "core-rules.xml")

    workflow_rules = _extract_section(
        core_rules, r"^\s*<WORKFLOW-RULES\b[^>]*>", r"^\s*</WORKFLOW-RULES>"
    )
    input_protocol = _extract_section(
        core_rules, r"^\s*<input-protocol\b[^>]*>", r"^\s*</input-protocol>"
    )
    result_protocol = _extract_section(
        core_rules, r"^\s*<workflow-result-protocol\b[^>]*>", r"^\s*</workflow-result-protocol>"
    )
    human_review = _extract_section(
        core_rules, r"^\s*<human-review-protocol\b[^>]*>", r"^\s*</human-review-protocol>"
    )

    parts = ["# L1 · 执行规则\n"]
    if workflow_rules:
        parts.append("## WORKFLOW-RULES\n\n```xml\n" + workflow_rules.strip() + "\n```\n")
    if input_protocol:
        parts.append("## step-pause input-protocol\n\n```xml\n" + input_protocol.strip() + "\n```\n")
    if result_protocol:
        parts.append("## workflow-result-protocol（ABORT 协议）\n\n```xml\n" + result_protocol.strip() + "\n```\n")
    if human_review:
        parts.append("## human-review-protocol（熔断触发器）\n\n```xml\n" + human_review.strip() + "\n```\n")
    return "\n".join(parts)


# ──────────────────────────────────────────────────────────────────────
# L2: 当前阶段逻辑
# ──────────────────────────────────────────────────────────────────────

PHASE_FILE_MAP = {
    "qa-intake": "phases/p1-intake.md",
    "qa-spec-definition": "phases/p2-spec-definition.md",
    "qa-root-cause": "phases/p3-root-cause.md",
    "qa-fix-design": "phases/p4-fix-design.md",
    "qa-fix-impl": "phases/p5-fix-impl.md",
    "qa-verification": "phases/p6-verification.md",
}


def _summarize_phase_file(text: str) -> str:
    """从 phase 文件中提取 step 标题和关键 action（首个 action / check 的简短摘要）。"""
    lines: list[str] = []
    for m in re.finditer(r'<step\s+n="(\d+)"\s+goal="([^"]+)"', text):
        n, goal = m.group(1), m.group(2)
        lines.append(f"- step {n}: {goal}")
    if not lines:
        return "(未找到 <step> 节点；请检查 phase 文件结构)"
    return "\n".join(lines)


def build_l2_phase_logic(
    workflow_root: Path = WORKFLOW_ROOT, phase: Optional[str] = None
) -> str:
    """L2：默认全量 6 阶段；指定 phase 时仅输出该 phase + 前后 1 个相邻阶段。"""
    phases = _extract_phase_order(workflow_root)
    if phase is not None:
        if phase not in phases:
            return f"# L2 · 当前阶段逻辑\n\n(未知 phase: {phase})"
        idx = phases.index(phase)
        target_phases = phases[max(0, idx - 1) : idx + 2]
    else:
        target_phases = phases

    parts = ["# L2 · 当前阶段逻辑\n"]
    for p in target_phases:
        rel = PHASE_FILE_MAP.get(p)
        if rel is None:
            continue
        path = workflow_root / rel
        if not path.is_file():
            parts.append(f"## {p}\n\n(缺失 phase 文件: {rel})\n")
            continue
        body = _read(path)
        parts.append(
            f"## {p}\n\n来源：`{rel}`\n\n### Step 概览\n\n"
            + _summarize_phase_file(body)
            + "\n"
        )
    return "\n".join(parts)


# ──────────────────────────────────────────────────────────────────────
# L3: 推理工具箱
# ──────────────────────────────────────────────────────────────────────

def build_l3_reasoning_toolbox(workflow_root: Path = WORKFLOW_ROOT) -> str:
    """L3：保留 reasoning-chain.md 中的 OVHSC 五步 + 置信度规则（V1 §6 第 1 条不可触动）。"""
    path = workflow_root / "reference" / "reasoning-chain.md"
    if not path.is_file():
        return "# L3 · 推理工具箱\n\n(缺失 reference/reasoning-chain.md)"
    text = _read(path)

    five_steps = _extract_section(text, r"^## 推理链五步骤", r"^## ")
    output_format = _extract_section(text, r"^## 推理链输出格式", r"^## ")
    confidence = _extract_section(text, r"^## 置信度计算规则", r"^## ")

    parts = ["# L3 · 推理工具箱（OVHSC 不可触动）\n"]
    if five_steps:
        parts.append(five_steps.rstrip() + "\n")
    if output_format:
        parts.append(output_format.rstrip() + "\n")
    if confidence:
        parts.append(confidence.rstrip() + "\n")
    return "\n".join(parts)


# ──────────────────────────────────────────────────────────────────────
# L4: 平台知识
# ──────────────────────────────────────────────────────────────────────

PLATFORM_SECTION_MAP = {
    "common": (r"^## 通用规则", r"^# Android"),
    "android": (r"^## Android 平台检查清单", r"^---\n+## iOS"),
    "ios": (r"^## iOS 平台检查清单", r"^---\n+## "),
    "functional": (r"^## Android 平台检查清单", r"^---\n+## iOS"),
    "ui": (r"^## Android 平台检查清单", r"^---\n+## iOS"),
    "network": (r"^## Android 平台检查清单", r"^---\n+## iOS"),
    "compat": (r"^## Android 平台检查清单", r"^---\n+## iOS"),
}


def build_l4_platform_knowledge(
    workflow_root: Path = WORKFLOW_ROOT, category: Optional[str] = None
) -> str:
    """L4：按 category 提取段落；不指定 category 时输出 common + Android + iOS 全量。"""
    path = workflow_root / "reference" / "platform-checklist.md"
    if not path.is_file():
        return "# L4 · 平台知识\n\n(缺失 reference/platform-checklist.md)"
    text = _read(path)

    parts = ["# L4 · 平台知识\n"]
    if category and category in PLATFORM_SECTION_MAP:
        start, end = PLATFORM_SECTION_MAP[category]
        seg = _extract_section(text, start, end)
        parts.append(seg.rstrip() + "\n" if seg else f"(category={category} 段落未命中)\n")
    else:
        for key in ("common", "android", "ios"):
            start, end = PLATFORM_SECTION_MAP[key]
            seg = _extract_section(text, start, end)
            if seg:
                parts.append(seg.rstrip() + "\n")
    return "\n".join(parts)


# ──────────────────────────────────────────────────────────────────────
# verify 模式：core/ 一致性校验
# ──────────────────────────────────────────────────────────────────────

ENUM_BLOCK_REGEX = re.compile(
    r"v4\.1\s*完整集合[^\n]*\n((?:#\s+\S.*\n)+)"
)
STATE_TOKEN_REGEX = re.compile(r"[A-Z][A-Za-z-]+")


def _extract_template_enum(template_path: Path) -> set[str]:
    """从 workflow-status-template.yaml 注释块中提取 v4.1 完整集合 enum 名。"""
    if not template_path.is_file():
        return set()
    text = _read(template_path)
    m = ENUM_BLOCK_REGEX.search(text)
    if not m:
        return set()
    states: set[str] = set()
    for line in m.group(1).splitlines():
        body = re.sub(r"^#\s+", "", line)
        if "/" not in body:
            continue
        for chunk in body.split("/"):
            tok = chunk.strip()
            if STATE_TOKEN_REGEX.fullmatch(tok):
                states.add(tok)
    return states


def _extract_workflow_state_writes(workflow_xml_path: Path) -> set[str]:
    """从 workflow.xml 中提取所有写到 current_state = X 的 X 取值。"""
    if not workflow_xml_path.is_file():
        return set()
    text = _read(workflow_xml_path)
    return set(re.findall(r"current_state\s*=\s*([A-Z][A-Za-z-]+)", text))


def verify_core_consistency(workflow_root: Path = WORKFLOW_ROOT) -> list[str]:
    """校验 core/ 关键 token 自洽，返回 issue 列表（空 = 通过）。"""
    issues: list[str] = []
    template_path = workflow_root / "core" / "workflow-status-template.yaml"
    workflow_path = workflow_root / "core" / "workflow.xml"

    enum_template = _extract_template_enum(template_path)
    if not enum_template:
        issues.append(
            f"workflow-status-template.yaml 未提取到 v4.1 完整集合 enum 注释块"
        )
    enum_writes = _extract_workflow_state_writes(workflow_path)
    illegal = enum_writes - enum_template
    if enum_template and illegal:
        issues.append(
            f"workflow.xml 写入了不在 template enum 集内的 state: {sorted(illegal)}"
        )
    return issues


# ──────────────────────────────────────────────────────────────────────
# main
# ──────────────────────────────────────────────────────────────────────

LAYERED_FILES = [
    ("L0-identity.md", build_l0_identity),
    ("L1-execution-rules.md", build_l1_execution_rules),
    ("L2-phase-logic.md", build_l2_phase_logic),
    ("L3-reasoning-toolbox.md", build_l3_reasoning_toolbox),
    ("L4-platform-knowledge.md", build_l4_platform_knowledge),
]


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="build-system-prompt.py (v4.2 PR-2)")
    parser.add_argument("--mode", choices=["full", "layered", "verify"], default="verify")
    parser.add_argument("--output", type=Path, default=None, help="--mode=full 输出文件路径")
    parser.add_argument(
        "--output-dir", type=Path, default=None, help="--mode=layered 输出目录"
    )
    parser.add_argument(
        "--phase", default=None, help="--mode=full/layered 时指定 L2 phase"
    )
    parser.add_argument(
        "--category",
        default=None,
        help="L4 命中分类（functional / ui / network / compat / android / ios / common）",
    )
    parser.add_argument(
        "--workflow-root",
        type=Path,
        default=WORKFLOW_ROOT,
        help="workflow 根目录（默认从脚本路径推断）",
    )
    args = parser.parse_args(argv)

    wfr = args.workflow_root.resolve()

    if args.mode == "verify":
        issues = verify_core_consistency(wfr)
        if issues:
            for issue in issues:
                print(f"::error::{issue}", file=sys.stderr)
            return 1
        print("OK: build-system-prompt.py --mode=verify 通过")
        return 0

    if args.mode == "full":
        if args.output is None:
            sys.stderr.write("error: --mode=full 需要 --output\n")
            return 2
        # H1 守门：禁止 PR-2 阶段替换 system-prompt.md
        if (
            os.environ.get("ALLOW_FIRST_BUILD") != "1"
            and args.output.name == "system-prompt.md"
        ):
            sys.stderr.write(
                "error: v4.2 PR-2 阶段禁止 --mode=full 输出到 system-prompt.md；"
                "首次构建由 PR-6 触发（设置 ALLOW_FIRST_BUILD=1 解锁）\n"
            )
            return 3
        full_content = "\n\n".join(
            [
                build_l0_identity(wfr),
                build_l1_execution_rules(wfr),
                build_l2_phase_logic(wfr, args.phase),
                build_l3_reasoning_toolbox(wfr),
                build_l4_platform_knowledge(wfr, args.category),
            ]
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(full_content, encoding="utf-8")
        print(f"OK: 写入 {args.output} ({len(full_content.splitlines())} 行)")
        return 0

    if args.mode == "layered":
        if args.output_dir is None:
            sys.stderr.write("error: --mode=layered 需要 --output-dir\n")
            return 2
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for name, builder in LAYERED_FILES:
            if name == "L2-phase-logic.md":
                content = builder(wfr, args.phase)  # type: ignore[call-arg]
            elif name == "L4-platform-knowledge.md":
                content = builder(wfr, args.category)  # type: ignore[call-arg]
            else:
                content = builder(wfr)  # type: ignore[call-arg]
            (args.output_dir / name).write_text(content, encoding="utf-8")
        print(f"OK: 写入 {args.output_dir} (5 个分层文件)")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
