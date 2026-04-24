"""
Loupe AI 自检自测系统 — Metrics (公共指标工具)

提供跨模块共享的:
- DEFAULT_WEIGHTS: 评分维度默认权重 (与 scoring-rubric-base.yaml 保持一致)
- estimate_agent_count: 估算 Agent 数量
- collect_runtime_metrics: 从 workflow-status.yaml 收集运行时指标
"""

import logging
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)

# 评分维度默认权重 — 单一事实源 (Single Source of Truth)
# 与 scoring-rubric-base.yaml 中 weights 节保持一致
DEFAULT_WEIGHTS: dict[str, float] = {
    "attribution_accuracy": 0.30,
    "contributing_completeness": 0.12,
    "fix_correctness": 0.18,
    "reasoning_depth": 0.08,
    "artifact_completeness": 0.09,
    "defensive_fix_quality": 0.08,
    "contract_first_pass_accuracy": 0.08,
    "hallucination_interception": 0.04,
    "self_healing_rate": 0.03,
}

# Agent 数量映射表
_FANOUT_AGENT_COUNTS: dict[str, int] = {
    "simple-single": 1,
    "medium-challenge": 2,
    "complex-arbitrated": 4,
    "single-proposer": 1,
    "challenged-proposer": 2,
    "contested-arbitrated": 4,
}


def estimate_agent_count(
    fanout_mode: Optional[str],
    fix_strategy_mode: Optional[str],
    specialized_mode: Optional[str],
) -> int:
    total = 0
    if fanout_mode:
        total += _FANOUT_AGENT_COUNTS.get(fanout_mode, 0)
    if fix_strategy_mode:
        total += _FANOUT_AGENT_COUNTS.get(fix_strategy_mode, 0)
    if specialized_mode == "functionality-deep-dive":
        total += 4
    return total


def collect_runtime_metrics(output_dir: str) -> dict:
    status_path = Path(output_dir) / "workflow-status.yaml"
    if not status_path.exists():
        return {}
    try:
        status = yaml.safe_load(status_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    specialized = status.get("specialized_workflow", {}) or {}
    fanout_mode = status.get("fanout_mode")
    fix_strategy_mode = status.get("fix_strategy_mode")
    mode = specialized.get("mode")
    agent_count = estimate_agent_count(fanout_mode, fix_strategy_mode, mode)
    return {
        "analysis_complexity": status.get("analysis_complexity"),
        "fanout_mode": fanout_mode,
        "fix_strategy_mode": fix_strategy_mode,
        "specialized_workflow_mode": mode,
        "specialized_workflow_status": specialized.get("status"),
        "agent_count": agent_count,
    }
