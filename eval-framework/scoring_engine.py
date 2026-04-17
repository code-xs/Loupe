"""
Loupe AI 自检自测系统 — Scoring Engine (评分计算引擎)
负责评分维度计算、加权汇总、统计分析。
支持阶段级拆分评分 (F1-F5 / P1-P6) 和 Case 分组统计。
"""

import json
import logging
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class DimensionStats:
    """单维度统计"""
    dimension: str = ""
    mean: float = 0.0
    median: float = 0.0
    std_dev: float = 0.0
    min_score: float = 0.0
    max_score: float = 0.0
    count: int = 0


@dataclass
class ChainStats:
    """单链路统计"""
    chain: str = ""
    weighted_mean: float = 0.0
    dimension_stats: dict = field(default_factory=dict)
    stage_stats: dict = field(default_factory=dict)
    case_count: int = 0


@dataclass
class ScoringReport:
    """评分报告"""
    chain_stats: dict = field(default_factory=dict)   # chain → ChainStats
    category_stats: dict = field(default_factory=dict) # category → {chain → stats}
    complexity_stats: dict = field(default_factory=dict)
    overall_stats: dict = field(default_factory=dict)


class ScoringEngine:
    """
    评分维度计算与加权汇总引擎
    """

    DIMENSIONS = [
        "attribution_accuracy",
        "contributing_completeness",
        "fix_correctness",
        "reasoning_depth",
        "artifact_completeness",
        "defensive_fix_quality",
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
            "attribution_accuracy": 0.35,
            "contributing_completeness": 0.15,
            "fix_correctness": 0.20,
            "reasoning_depth": 0.10,
            "artifact_completeness": 0.10,
            "defensive_fix_quality": 0.10,
        })

    @staticmethod
    def _load_rubric(path: str) -> dict:
        if not Path(path).exists():
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def compute_report(self, eval_results: list[dict],
                       case_metadata: dict = None) -> ScoringReport:
        """
        从评分结果计算完整报告

        Args:
            eval_results: Judge 输出的评分结果列表
            case_metadata: case_id → metadata 映射

        Returns:
            ScoringReport
        """
        report = ScoringReport()
        case_metadata = case_metadata or {}

        # 按 Chain 分组
        by_chain: dict[str, list[dict]] = {}
        for r in eval_results:
            chain = r.get("chain", "unknown")
            by_chain.setdefault(chain, []).append(r)

        # 计算每个 Chain 的统计
        for chain, results in by_chain.items():
            report.chain_stats[chain] = self._compute_chain_stats(chain, results)

        # 按类别分组统计
        if case_metadata:
            report.category_stats = self._compute_category_stats(
                eval_results, case_metadata
            )
            report.complexity_stats = self._compute_complexity_stats(
                eval_results, case_metadata
            )

        # 全局统计
        report.overall_stats = self._compute_overall_stats(eval_results)

        return report

    def _compute_chain_stats(self, chain: str,
                             results: list[dict]) -> ChainStats:
        """计算单链路统计"""
        stats = ChainStats(chain=chain, case_count=len(results))

        # 综合分统计
        weighted_scores = [r.get("weighted_score", 0.0) for r in results]
        stats.weighted_mean = (
            statistics.mean(weighted_scores) if weighted_scores else 0.0
        )

        # 各维度统计
        for dim in self.DIMENSIONS:
            scores = [r.get("scores", {}).get(dim, 0.0) for r in results]
            stats.dimension_stats[dim] = self._calc_stats(dim, scores)

        # 阶段级统计
        for stage in self.STAGES:
            scores = [r.get("stage_scores", {}).get(stage, 0.0) for r in results]
            if any(s > 0 for s in scores):
                stats.stage_stats[stage] = self._calc_stats(stage, scores)

        return stats

    @staticmethod
    def _calc_stats(name: str, scores: list[float]) -> DimensionStats:
        """计算描述性统计"""
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

    def _compute_category_stats(self, results: list[dict],
                                 case_metadata: dict) -> dict:
        """按问题分类计算统计"""
        by_category: dict[str, dict[str, list]] = {}

        for r in results:
            case_id = r.get("case_id", "")
            meta = case_metadata.get(case_id, {})
            category = meta.get("category", "unknown")
            chain = r.get("chain", "")
            by_category.setdefault(category, {}).setdefault(chain, []).append(r)

        stats = {}
        for cat, chain_results in by_category.items():
            stats[cat] = {}
            for chain, results_list in chain_results.items():
                scores = [r.get("weighted_score", 0.0) for r in results_list]
                stats[cat][chain] = {
                    "mean": round(statistics.mean(scores), 3) if scores else 0,
                    "count": len(scores),
                }
        return stats

    def _compute_complexity_stats(self, results: list[dict],
                                   case_metadata: dict) -> dict:
        """按复杂度等级计算统计"""
        by_complexity: dict[str, dict[str, list]] = {}

        for r in results:
            case_id = r.get("case_id", "")
            meta = case_metadata.get(case_id, {})
            complexity = meta.get("complexity", "unknown")
            chain = r.get("chain", "")
            by_complexity.setdefault(complexity, {}).setdefault(chain, []).append(r)

        stats = {}
        for comp, chain_results in by_complexity.items():
            stats[comp] = {}
            for chain, results_list in chain_results.items():
                scores = [r.get("weighted_score", 0.0) for r in results_list]
                stats[comp][chain] = {
                    "mean": round(statistics.mean(scores), 3) if scores else 0,
                    "count": len(scores),
                }
        return stats

    def _compute_overall_stats(self, results: list[dict]) -> dict:
        """全局统计"""
        if not results:
            return {}

        all_scores = [r.get("weighted_score", 0.0) for r in results]
        return {
            "total_evaluations": len(results),
            "overall_mean": round(statistics.mean(all_scores), 3),
            "overall_median": round(statistics.median(all_scores), 3),
            "overall_std_dev": (
                round(statistics.stdev(all_scores), 3)
                if len(all_scores) > 1 else 0.0
            ),
        }

    def export_report(self, report: ScoringReport, output_path: str):
        """导出报告为 JSON"""
        data = {
            "chain_stats": {},
            "category_stats": report.category_stats,
            "complexity_stats": report.complexity_stats,
            "overall_stats": report.overall_stats,
        }

        for chain, stats in report.chain_stats.items():
            data["chain_stats"][chain] = {
                "weighted_mean": stats.weighted_mean,
                "case_count": stats.case_count,
                "dimension_stats": {
                    k: {
                        "mean": v.mean, "median": v.median,
                        "std_dev": v.std_dev, "min": v.min_score,
                        "max": v.max_score, "count": v.count,
                    }
                    for k, v in stats.dimension_stats.items()
                },
                "stage_stats": {
                    k: {
                        "mean": v.mean, "median": v.median,
                        "std_dev": v.std_dev, "min": v.min_score,
                        "max": v.max_score, "count": v.count,
                    }
                    for k, v in stats.stage_stats.items()
                },
            }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Scoring report exported: {output_path}")
