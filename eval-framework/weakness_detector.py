"""
Loupe AI 自检自测系统 — Weakness Detector (薄弱环节定位)
分析评估结果，定位低分 Case 类型和 Stage，输出改进优先级。
"""

import logging
import statistics
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class WeaknessItem:
    """单个薄弱环节"""
    category: str = ""          # Case 类型 / Stage / 维度
    dimension: str = ""         # 薄弱维度
    mean_score: float = 0.0
    threshold: float = 7.0
    gap: float = 0.0            # threshold - mean_score
    affected_cases: list = field(default_factory=list)
    priority: int = 0           # 越高越优先
    improvement_type: str = ""  # prompt | reference | agent | template | architecture


@dataclass
class WeaknessReport:
    """薄弱环节分析报告"""
    weaknesses: list = field(default_factory=list)  # WeaknessItem list
    cross_analysis: dict = field(default_factory=dict)  # category × stage → weakness
    top_priorities: list = field(default_factory=list)
    summary: str = ""


class WeaknessDetector:
    """
    薄弱环节定位器
    分析逻辑:
    1. 按 Case 类型分组，计算各维度均分
    2. 按 Stage 分组 (F1-F5)，计算各阶段均分
    3. 交叉分析：哪种类型的哪个阶段最弱
    4. 按 低分 Case 数 × 分差 排序，输出改进优先级
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

    # 维度到改进类型的映射
    DIM_TO_IMPROVEMENT = {
        "attribution_accuracy": "prompt",
        "contributing_completeness": "reference",
        "fix_correctness": "prompt",
        "reasoning_depth": "agent",
        "artifact_completeness": "template",
        "defensive_fix_quality": "reference",
    }

    STAGE_TO_FILE = {
        "F1_context_reconstruction": "functionality-deep-dive/phases/f1-context-reconstruction.md",
        "F2_state_topology": "functionality-deep-dive/phases/f2-state-topology.md",
        "F3_temporal_correlation": "functionality-deep-dive/phases/f3-temporal-correlation.md",
        "F4_isolation_debate": "functionality-deep-dive/phases/f4-isolation-debate.md",
        "F5_defensive_fix": "functionality-deep-dive/phases/f5-defensive-fix-design.md",
    }

    def __init__(self, threshold: float = 7.0):
        self.threshold = threshold

    def analyze(self, eval_results: list[dict],
                case_metadata: dict = None) -> WeaknessReport:
        """
        执行薄弱环节分析

        Args:
            eval_results: Judge 评分结果列表
            case_metadata: case_id → metadata 映射

        Returns:
            WeaknessReport
        """
        report = WeaknessReport()
        case_metadata = case_metadata or {}

        # 1. 按 Case 类型分组，计算各维度均分
        type_weaknesses = self._analyze_by_type(eval_results, case_metadata)
        report.weaknesses.extend(type_weaknesses)

        # 2. 按 Stage 分组，计算各阶段均分
        stage_weaknesses = self._analyze_by_stage(eval_results)
        report.weaknesses.extend(stage_weaknesses)

        # 3. 交叉分析
        report.cross_analysis = self._cross_analyze(
            eval_results, case_metadata
        )

        # 4. 排序优先级
        for w in report.weaknesses:
            w.priority = int(w.gap * len(w.affected_cases) * 10)

        report.weaknesses.sort(key=lambda x: x.priority, reverse=True)
        report.top_priorities = report.weaknesses[:5]

        # 5. 生成摘要
        report.summary = self._generate_summary(report)

        return report

    def _analyze_by_type(self, results: list[dict],
                          metadata: dict) -> list[WeaknessItem]:
        """按问题类型分析薄弱维度"""
        by_type: dict[str, list] = {}
        for r in results:
            case_id = r.get("case_id", "")
            meta = metadata.get(case_id, {})
            cat = meta.get("category", "unknown")
            by_type.setdefault(cat, []).append(r)

        weaknesses = []
        for cat, cat_results in by_type.items():
            for dim in self.DIMENSIONS:
                scores = [r.get("scores", {}).get(dim, 0) for r in cat_results]
                mean = statistics.mean(scores) if scores else 0

                if mean < self.threshold:
                    affected = [
                        r.get("case_id", "")
                        for r in cat_results
                        if r.get("scores", {}).get(dim, 0) < self.threshold
                    ]
                    weaknesses.append(WeaknessItem(
                        category=cat,
                        dimension=dim,
                        mean_score=round(mean, 3),
                        threshold=self.threshold,
                        gap=round(self.threshold - mean, 3),
                        affected_cases=affected,
                        improvement_type=self.DIM_TO_IMPROVEMENT.get(dim, "prompt"),
                    ))

        return weaknesses

    def _analyze_by_stage(self, results: list[dict]) -> list[WeaknessItem]:
        """按 Stage 分析薄弱阶段"""
        weaknesses = []

        for stage in self.STAGES:
            scores = [
                r.get("stage_scores", {}).get(stage, 0)
                for r in results
                if r.get("stage_scores", {}).get(stage, 0) > 0
            ]
            if not scores:
                continue

            mean = statistics.mean(scores)
            if mean < self.threshold:
                affected = [
                    r.get("case_id", "")
                    for r in results
                    if r.get("stage_scores", {}).get(stage, 0) < self.threshold
                    and r.get("stage_scores", {}).get(stage, 0) > 0
                ]
                weaknesses.append(WeaknessItem(
                    category=f"Stage:{stage}",
                    dimension=stage,
                    mean_score=round(mean, 3),
                    threshold=self.threshold,
                    gap=round(self.threshold - mean, 3),
                    affected_cases=affected,
                    improvement_type="prompt",
                ))

        return weaknesses

    def _cross_analyze(self, results: list[dict],
                        metadata: dict) -> dict:
        """交叉分析: Case 类型 × Stage"""
        cross: dict[str, dict[str, list]] = {}

        for r in results:
            case_id = r.get("case_id", "")
            meta = metadata.get(case_id, {})
            cat = meta.get("category", "unknown")

            for stage in self.STAGES:
                score = r.get("stage_scores", {}).get(stage, 0)
                if score > 0:
                    cross.setdefault(cat, {}).setdefault(stage, []).append(score)

        # 计算均分
        result = {}
        for cat, stages in cross.items():
            result[cat] = {}
            for stage, scores in stages.items():
                mean = round(statistics.mean(scores), 3) if scores else 0
                result[cat][stage] = {
                    "mean": mean,
                    "count": len(scores),
                    "below_threshold": mean < self.threshold,
                }

        return result

    def _generate_summary(self, report: WeaknessReport) -> str:
        """生成分析摘要"""
        if not report.weaknesses:
            return "✅ 所有维度和阶段均达标，无薄弱环节。"

        total = len(report.weaknesses)
        top = report.top_priorities

        lines = [f"发现 {total} 个薄弱环节，Top 5 改进优先级：\n"]
        for i, w in enumerate(top, 1):
            lines.append(
                f"{i}. **{w.category} / {w.dimension}**: "
                f"均分 {w.mean_score:.1f} (阈值 {w.threshold}), "
                f"差距 {w.gap:.1f}, 影响 {len(w.affected_cases)} 个 Case, "
                f"建议改进类型: {w.improvement_type}"
            )

        return "\n".join(lines)
