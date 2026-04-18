"""Loupe AI 自检自测系统 — Scoring Engine (评分计算引擎)"""

import json
import logging
import statistics
from dataclasses import dataclass, field
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


@dataclass
class DimensionStats:
    dimension: str = ""
    mean: float = 0.0
    median: float = 0.0
    std_dev: float = 0.0
    min_score: float = 0.0
    max_score: float = 0.0
    count: int = 0


@dataclass
class ChainStats:
    chain: str = ""
    weighted_mean: float = 0.0
    dimension_stats: dict = field(default_factory=dict)
    stage_stats: dict = field(default_factory=dict)
    case_count: int = 0


@dataclass
class ScoringReport:
    chain_stats: dict = field(default_factory=dict)
    category_stats: dict = field(default_factory=dict)
    complexity_stats: dict = field(default_factory=dict)
    efficiency_metrics: dict = field(default_factory=dict)
    overall_stats: dict = field(default_factory=dict)


class ScoringEngine:
    DIMENSIONS = [
        "attribution_accuracy",
        "contributing_completeness",
        "fix_correctness",
        "reasoning_depth",
        "artifact_completeness",
        "defensive_fix_quality",
        "contract_first_pass_accuracy",
        "hallucination_interception",
        "self_healing_rate",
    ]
    STAGES = [
        "F1_context_reconstruction",
        "F2_state_topology",
        "F3_temporal_correlation",
        "F4_isolation_debate",
        "F5_defensive_fix",
    ]

    def __init__(self, rubric_path: str = "eval-framework/scoring-rubric-base.yaml"):
        self.rubric = self._load_rubric(rubric_path)
        self.weights = self.rubric.get("weights", {
            "attribution_accuracy": 0.30,
            "contributing_completeness": 0.12,
            "fix_correctness": 0.18,
            "reasoning_depth": 0.08,
            "artifact_completeness": 0.09,
            "defensive_fix_quality": 0.08,
            "contract_first_pass_accuracy": 0.08,
            "hallucination_interception": 0.04,
            "self_healing_rate": 0.03,
        })
        assert abs(sum(self.weights.values()) - 1.0) < 1e-6

    @staticmethod
    def _load_rubric(path: str) -> dict:
        if not Path(path).exists():
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def compute_report(self, eval_results: list[dict], case_metadata: dict = None) -> ScoringReport:
        report = ScoringReport()
        case_metadata = case_metadata or {}
        by_chain = {}
        for r in eval_results:
            by_chain.setdefault(r.get("chain", "unknown"), []).append(r)
        for chain, results in by_chain.items():
            report.chain_stats[chain] = self._compute_chain_stats(chain, results)
        if case_metadata:
            report.category_stats = self._compute_category_stats(eval_results, case_metadata)
            report.complexity_stats = self._compute_complexity_stats(eval_results, case_metadata)
        report.efficiency_metrics = self._compute_efficiency_metrics(eval_results)
        report.overall_stats = self._compute_overall_stats(eval_results)
        return report

    def _compute_chain_stats(self, chain: str, results: list[dict]) -> ChainStats:
        stats = ChainStats(chain=chain, case_count=len(results))
        weighted_scores = [r.get("weighted_score", 0.0) for r in results]
        stats.weighted_mean = statistics.mean(weighted_scores) if weighted_scores else 0.0
        for dim in self.DIMENSIONS:
            scores = [r.get("scores", {}).get(dim, 0.0) for r in results]
            stats.dimension_stats[dim] = self._calc_stats(dim, scores)
        for stage in self.STAGES:
            scores = [r.get("stage_scores", {}).get(stage, 0.0) for r in results]
            if any(s > 0 for s in scores):
                stats.stage_stats[stage] = self._calc_stats(stage, scores)
        return stats

    @staticmethod
    def _calc_stats(name: str, scores: list[float]) -> DimensionStats:
        valid = [s for s in scores if s is not None]
        if not valid:
            return DimensionStats(dimension=name)
        return DimensionStats(
            dimension=name,
            mean=round(statistics.mean(valid), 3),
            median=round(statistics.median(valid), 3),
            std_dev=round(statistics.stdev(valid), 3) if len(valid) > 1 else 0.0,
            min_score=min(valid),
            max_score=max(valid),
            count=len(valid),
        )

    def _compute_category_stats(self, results: list[dict], case_metadata: dict) -> dict:
        by_category = {}
        for r in results:
            meta = case_metadata.get(r.get("case_id", ""), {})
            category = meta.get("category", "unknown")
            by_category.setdefault(category, {}).setdefault(r.get("chain", ""), []).append(r.get("weighted_score", 0.0))
        return {cat: {chain: {"mean": round(statistics.mean(scores), 3) if scores else 0, "count": len(scores)} for chain, scores in chain_results.items()} for cat, chain_results in by_category.items()}

    def _compute_complexity_stats(self, results: list[dict], case_metadata: dict) -> dict:
        by_complexity = {}
        for r in results:
            meta = case_metadata.get(r.get("case_id", ""), {})
            complexity = meta.get("complexity", "unknown")
            by_complexity.setdefault(complexity, {}).setdefault(r.get("chain", ""), []).append(r.get("weighted_score", 0.0))
        return {comp: {chain: {"mean": round(statistics.mean(scores), 3) if scores else 0, "count": len(scores)} for chain, scores in chain_results.items()} for comp, chain_results in by_complexity.items()}

    def _compute_efficiency_metrics(self, results: list[dict]) -> dict:
        by_chain = {}
        for r in results:
            by_chain.setdefault(r.get("chain", ""), []).append(r)
        metrics = {}
        for chain, rows in by_chain.items():
            agent_counts = [r.get("metadata", {}).get("runtime_metrics", {}).get("agent_count") for r in rows]
            agent_counts = [a for a in agent_counts if a is not None]
            fanout_distribution = {}
            fix_distribution = {}
            activation = 0
            for row in rows:
                runtime = row.get("metadata", {}).get("runtime_metrics", {})
                if runtime.get("specialized_workflow_mode"):
                    activation += 1
                if runtime.get("fanout_mode"):
                    fanout_distribution[runtime["fanout_mode"]] = fanout_distribution.get(runtime["fanout_mode"], 0) + 1
                if runtime.get("fix_strategy_mode"):
                    fix_distribution[runtime["fix_strategy_mode"]] = fix_distribution.get(runtime["fix_strategy_mode"], 0) + 1
            avg_agent = round(statistics.mean(agent_counts), 3) if agent_counts else 0.0
            mean_score = round(statistics.mean([r.get("weighted_score", 0.0) for r in rows]), 3) if rows else 0.0
            metrics[chain] = {
                "avg_agent_count": avg_agent,
                "score_per_agent": round(mean_score / avg_agent, 3) if avg_agent else 0.0,
                "deep_dive_activation_rate": round(activation / len(rows), 3) if rows else 0.0,
                "fanout_distribution": fanout_distribution,
                "fix_strategy_distribution": fix_distribution,
            }
        return metrics

    def _compute_overall_stats(self, results: list[dict]) -> dict:
        if not results:
            return {}
        all_scores = [r.get("weighted_score", 0.0) for r in results]
        return {
            "total_evaluations": len(results),
            "overall_mean": round(statistics.mean(all_scores), 3),
            "overall_median": round(statistics.median(all_scores), 3),
            "overall_std_dev": round(statistics.stdev(all_scores), 3) if len(all_scores) > 1 else 0.0,
        }

    def export_report(self, report: ScoringReport, output_path: str):
        data = {
            "chain_stats": {},
            "category_stats": report.category_stats,
            "complexity_stats": report.complexity_stats,
            "efficiency_metrics": report.efficiency_metrics,
            "overall_stats": report.overall_stats,
        }
        for chain, stats in report.chain_stats.items():
            data["chain_stats"][chain] = {
                "weighted_mean": stats.weighted_mean,
                "case_count": stats.case_count,
                "dimension_stats": {k: {"mean": v.mean, "median": v.median, "std_dev": v.std_dev, "min": v.min_score, "max": v.max_score, "count": v.count} for k, v in stats.dimension_stats.items()},
                "stage_stats": {k: {"mean": v.mean, "median": v.median, "std_dev": v.std_dev, "min": v.min_score, "max": v.max_score, "count": v.count} for k, v in stats.stage_stats.items()},
            }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info("Scoring report exported: %s", output_path)
