"""Loupe AI 自检自测系统 — Comparator (横向对比器)"""

import json
import logging
import statistics
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ComparatorOutput:
    comparison_table: list = field(default_factory=list)
    incremental_analysis: dict = field(default_factory=dict)
    category_breakdown: dict = field(default_factory=dict)
    complexity_breakdown: dict = field(default_factory=dict)
    efficiency_metrics: dict = field(default_factory=dict)
    regression_detected: bool = False
    regression_details: list = field(default_factory=list)


class Comparator:
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
    CHAINS = ["A", "B", "C", "D"]

    def __init__(self, current_results_dir: str, baseline_dir: str = ""):
        self.current_dir = current_results_dir
        self.baseline_dir = baseline_dir
        self.current_results = self._load_results(current_results_dir)
        self.baseline_results = self._load_results(baseline_dir) if baseline_dir else []

    @staticmethod
    def _load_results(dir_path: str) -> list:
        results_file = Path(dir_path) / "judge-results.json"
        if results_file.exists():
            with open(results_file, "r", encoding="utf-8") as f:
                return json.load(f)
        all_results = []
        for jf in Path(dir_path).rglob("judge-results.json"):
            with open(jf, "r", encoding="utf-8") as f:
                all_results.extend(json.load(f))
        return all_results

    def compare(self) -> ComparatorOutput:
        output = ComparatorOutput()
        output.comparison_table = self._build_comparison_table()
        output.incremental_analysis = self._compute_incremental()
        output.category_breakdown = self._breakdown_by_field("category")
        output.complexity_breakdown = self._breakdown_by_field("complexity")
        output.efficiency_metrics = self._compute_efficiency_metrics()
        if self.baseline_results:
            output.regression_detected, output.regression_details = self._detect_regression()
        return output

    def _build_comparison_table(self) -> list:
        chain_means = self._compute_chain_means()
        rows = []
        for dim in self.DIMENSIONS + ["weighted_score"]:
            row = {"dimension": dim}
            for chain in self.CHAINS:
                row[f"chain_{chain.lower()}"] = chain_means.get(chain, {}).get(dim, 0.0)
            a = row.get("chain_a", 0)
            b = row.get("chain_b", 0)
            c = row.get("chain_c", 0)
            d = row.get("chain_d", 0)
            row["b_vs_a_pct"] = self._pct_change(b, a)
            row["b_vs_c_pct"] = self._pct_change(b, c)
            row["b_vs_d_pct"] = self._pct_change(b, d)
            row["a_vs_d_pct"] = self._pct_change(a, d)
            rows.append(row)
        return rows

    def _compute_chain_means(self) -> dict:
        by_chain = {}
        for r in self.current_results:
            by_chain.setdefault(r.get("chain", ""), []).append(r)
        means = {}
        for chain, results in by_chain.items():
            dim_means = {}
            for dim in self.DIMENSIONS:
                scores = [r.get("scores", {}).get(dim, 0) for r in results]
                dim_means[dim] = round(statistics.mean(scores), 3) if scores else 0
            ws = [r.get("weighted_score", 0) for r in results]
            dim_means["weighted_score"] = round(statistics.mean(ws), 3) if ws else 0
            means[chain] = dim_means
        return means

    def _compute_incremental(self) -> dict:
        chain_means = self._compute_chain_means()
        a = chain_means.get("A", {}).get("weighted_score", 0)
        b = chain_means.get("B", {}).get("weighted_score", 0)
        c = chain_means.get("C", {}).get("weighted_score", 0)
        d = chain_means.get("D", {}).get("weighted_score", 0)
        return {
            "expert_vs_standard": {"description": "专家模式 vs 主流程", "formula": "(B-A)/A × 100%", "value": self._pct_change(b, a), "question": "专家模式增量价值多大？"},
            "expert_vs_external": {"description": "专家模式 vs 外部 B2C", "formula": "(B-C)/C × 100%", "value": self._pct_change(b, c), "question": "方案竞争力如何？"},
            "expert_vs_baseline": {"description": "专家模式 vs LLM 裸跑", "formula": "(B-D)/D × 100%", "value": self._pct_change(b, d), "question": "工作流编排价值几何？"},
            "standard_vs_baseline": {"description": "主流程 vs LLM 裸跑", "formula": "(A-D)/D × 100%", "value": self._pct_change(a, d), "question": "标准工作流价值几何？"},
        }

    def _breakdown_by_field(self, field_name: str) -> dict:
        by_group = {}
        for r in self.current_results:
            group = r.get("metadata", {}).get(field_name, r.get("case_id", ""))
            by_group.setdefault(group, {}).setdefault(r.get("chain", ""), []).append(r.get("weighted_score", 0))
        breakdown = {}
        for group, chain_scores in by_group.items():
            breakdown[group] = {
                chain: {"mean": round(statistics.mean(scores), 3) if scores else 0, "count": len(scores)}
                for chain, scores in chain_scores.items()
            }
        return breakdown

    def _compute_efficiency_metrics(self) -> dict:
        result = {}
        by_chain = {}
        for r in self.current_results:
            by_chain.setdefault(r.get("chain", ""), []).append(r)
        for chain, rows in by_chain.items():
            agent_counts = []
            deep_dive_hits = 0
            route_hits = 0
            fanout_hits = 0
            fanout_distribution = {}
            fix_distribution = {}
            scores_with_specialized = []
            scores_without_specialized = []
            for row in rows:
                meta = row.get("metadata", {})
                runtime = meta.get("runtime_metrics", {})
                agent_count = runtime.get("agent_count")
                if agent_count is not None:
                    agent_counts.append(agent_count)
                fanout = runtime.get("fanout_mode")
                if fanout:
                    fanout_distribution[fanout] = fanout_distribution.get(fanout, 0) + 1
                fix_mode = runtime.get("fix_strategy_mode")
                if fix_mode:
                    fix_distribution[fix_mode] = fix_distribution.get(fix_mode, 0) + 1
                specialized = runtime.get("specialized_workflow_mode")
                if specialized:
                    deep_dive_hits += 1
                    scores_with_specialized.append(row.get("weighted_score", 0))
                else:
                    scores_without_specialized.append(row.get("weighted_score", 0))
                expected_route = meta.get("expected_route")
                actual_route = specialized or "standard-rca"
                if expected_route == actual_route:
                    route_hits += 1
                expected_fanout = meta.get("expected_fanout_mode")
                if expected_fanout and expected_fanout == fanout:
                    fanout_hits += 1
            count = len(rows) or 1
            avg_agent_count = round(statistics.mean(agent_counts), 3) if agent_counts else 0.0
            score_per_agent = round((statistics.mean([r.get("weighted_score", 0) for r in rows]) / avg_agent_count), 3) if avg_agent_count else 0.0
            specialized_delta = 0.0
            if scores_with_specialized and scores_without_specialized:
                specialized_delta = round(statistics.mean(scores_with_specialized) - statistics.mean(scores_without_specialized), 3)
            result[chain] = {
                "avg_agent_count": avg_agent_count,
                "score_per_agent": score_per_agent,
                "deep_dive_activation_rate": round(deep_dive_hits / count, 3),
                "expected_route_hit_rate": round(route_hits / count, 3),
                "expected_fanout_hit_rate": round(fanout_hits / count, 3) if any(r.get("metadata", {}).get("expected_fanout_mode") for r in rows) else None,
                "fanout_distribution": fanout_distribution,
                "fix_strategy_distribution": fix_distribution,
                "specialized_score_delta": specialized_delta,
            }
        return result

    def _detect_regression(self, threshold: float = 0.05) -> tuple:
        if not self.baseline_results:
            return False, []
        current_means = self._compute_chain_means()
        baseline_by_chain = {}
        for r in self.baseline_results:
            baseline_by_chain.setdefault(r.get("chain", ""), []).append(r.get("weighted_score", 0))
        details = []
        is_regression = False
        for chain in self.CHAINS:
            baseline_scores = baseline_by_chain.get(chain, [])
            if not baseline_scores:
                continue
            baseline = statistics.mean(baseline_scores)
            current = current_means.get(chain, {}).get("weighted_score", 0)
            change = (current - baseline) / baseline if baseline else 0
            if change < -threshold:
                is_regression = True
                details.append({"chain": chain, "baseline_score": round(baseline, 3), "current_score": current, "change_pct": round(change * 100, 2), "threshold_pct": round(-threshold * 100, 2)})
        return is_regression, details

    def generate_pr_comment(self) -> str:
        return ComparatorReportGenerator.generate_pr_comment(self.compare())

    @staticmethod
    def _pct_change(new: float, old: float) -> float:
        if old == 0:
            return 0.0 if new == 0 else 100.0
        return round((new - old) / old * 100, 2)


class ComparatorReportGenerator:
    @staticmethod
    def generate_full_report(output: ComparatorOutput, output_path: str = "") -> str:
        lines = [
            "# Loupe Eval 横向对比报告",
            "## 总览对比表",
            "| 指标 | Chain A | Chain B | Chain C | Chain D |",
            "|------|---------|---------|---------|---------|",
        ]
        for row in output.comparison_table:
            lines.append("| {} | {} | {} | {} | {} |".format(row["dimension"], row.get("chain_a", "-"), row.get("chain_b", "-"), row.get("chain_c", "-"), row.get("chain_d", "-")))
        lines.extend(["", "## 增量价值分析", "| 对比维度 | 计算公式 | 结果 | 核心问题 |", "|---------|---------|------|---------|"])
        for item in output.incremental_analysis.values():
            lines.append("| {} | {} | {}% | {} |".format(item["description"], item["formula"], item["value"], item["question"]))
        if output.efficiency_metrics:
            lines.extend(["", "## 效率指标"])
            for chain, metrics in sorted(output.efficiency_metrics.items()):
                lines.append(f"### Chain {chain}")
                lines.append("- avg_agent_count: {}".format(metrics.get("avg_agent_count")))
                lines.append("- score_per_agent: {}".format(metrics.get("score_per_agent")))
                lines.append("- deep_dive_activation_rate: {}".format(metrics.get("deep_dive_activation_rate")))
                lines.append("- expected_route_hit_rate: {}".format(metrics.get("expected_route_hit_rate")))
                lines.append("- expected_fanout_hit_rate: {}".format(metrics.get("expected_fanout_hit_rate")))
                lines.append("- specialized_score_delta: {}".format(metrics.get("specialized_score_delta")))
                lines.append("- fanout_distribution: {}".format(metrics.get("fanout_distribution")))
                lines.append("- fix_strategy_distribution: {}".format(metrics.get("fix_strategy_distribution")))
        if output.regression_detected:
            lines.append("## 回归检测")
            for detail in output.regression_details:
                lines.append("- Chain {}: {} -> {} ({}%)".format(detail["chain"], detail["baseline_score"], detail["current_score"], detail["change_pct"]))
        report = "\n".join(lines)
        if output_path:
            Path(output_path).write_text(report, encoding="utf-8")
        return report

    @staticmethod
    def generate_pr_comment(output: ComparatorOutput) -> str:
        inc = output.incremental_analysis
        lines = [
            "## Loupe Eval 结果",
            "**专家模式 vs 主流程**: {:+.1f}%".format(inc.get("expert_vs_standard", {}).get("value", 0)),
            "**专家模式 vs LLM 裸跑**: {:+.1f}%".format(inc.get("expert_vs_baseline", {}).get("value", 0)),
            "| 维度 | Chain A | Chain B | Chain D |",
            "|------|---------|---------|---------|",
        ]
        for row in output.comparison_table:
            dim = "**综合分**" if row["dimension"] == "weighted_score" else row["dimension"]
            lines.append("| {} | {} | {} | {} |".format(dim, row.get("chain_a", "-"), row.get("chain_b", "-"), row.get("chain_d", "-")))
        if output.efficiency_metrics.get("B"):
            lines.append("")
            lines.append("- Chain B avg_agent_count: {}".format(output.efficiency_metrics["B"].get("avg_agent_count")))
            lines.append("- Chain B deep_dive_activation_rate: {}".format(output.efficiency_metrics["B"].get("deep_dive_activation_rate")))
        return "\n".join(lines)


DEFAULT_MONTHLY_CONFIG = {
    "cases": "eval-cases/",
    "chains": ["A", "B", "C", "D"],
    "compare_with_last_month": True,
    "report_format": "markdown",
    "output_path": "eval-results/monthly-report.md",
}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Loupe Eval Comparator")
    parser.add_argument("--current", required=True)
    parser.add_argument("--baseline", default="")
    parser.add_argument("--output", default="eval-results/comparison-report.md")
    parser.add_argument("--pr-comment", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    comparator = Comparator(args.current, args.baseline)
    if args.pr_comment:
        print(comparator.generate_pr_comment())
    else:
        output = comparator.compare()
        ComparatorReportGenerator.generate_full_report(output, args.output)
        print(f"Report generated: {args.output}")


if __name__ == "__main__":
    main()
