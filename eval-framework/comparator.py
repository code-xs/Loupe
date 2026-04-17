"""
Loupe AI 自检自测系统 — Comparator (横向对比器)
对比不同 Chain 的评分结果，生成增量价值分析和回归检测。
"""

import json
import logging
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ComparisonRow:
    """单维度对比行"""
    dimension: str = ""
    chain_a: float = 0.0
    chain_b: float = 0.0
    chain_c: float = 0.0
    chain_d: float = 0.0
    b_vs_a_pct: float = 0.0   # (B-A)/A × 100%
    b_vs_c_pct: float = 0.0   # (B-C)/C × 100%
    b_vs_d_pct: float = 0.0   # (B-D)/D × 100%
    a_vs_d_pct: float = 0.0   # (A-D)/D × 100%


@dataclass
class ComparatorOutput:
    """对比器输出"""
    comparison_table: list = field(default_factory=list)  # ComparisonRow list
    incremental_analysis: dict = field(default_factory=dict)
    category_breakdown: dict = field(default_factory=dict)
    complexity_breakdown: dict = field(default_factory=dict)
    efficiency_metrics: dict = field(default_factory=dict)
    regression_detected: bool = False
    regression_details: list = field(default_factory=list)


class Comparator:
    """
    横向对比器
    支持当前结果 vs 基线结果的对比
    """

    DIMENSIONS = [
        "attribution_accuracy",
        "contributing_completeness",
        "fix_correctness",
        "reasoning_depth",
        "artifact_completeness",
        "defensive_fix_quality",
    ]

    CHAINS = ["A", "B", "C", "D"]

    def __init__(self, current_results_dir: str,
                 baseline_dir: str = ""):
        self.current_dir = current_results_dir
        self.baseline_dir = baseline_dir
        self.current_results = self._load_results(current_results_dir)
        self.baseline_results = (
            self._load_results(baseline_dir) if baseline_dir else []
        )

    @staticmethod
    def _load_results(dir_path: str) -> list[dict]:
        """加载评分结果"""
        results_file = Path(dir_path) / "judge-results.json"
        if results_file.exists():
            with open(results_file, "r", encoding="utf-8") as f:
                return json.load(f)

        # 尝试从子目录收集
        all_results = []
        path = Path(dir_path)
        for jf in path.rglob("judge-results.json"):
            with open(jf, "r", encoding="utf-8") as f:
                all_results.extend(json.load(f))
        return all_results

    def compare(self) -> ComparatorOutput:
        """执行完整对比分析"""
        output = ComparatorOutput()

        # 1. 总览对比表
        output.comparison_table = self._build_comparison_table()

        # 2. 增量价值分析
        output.incremental_analysis = self._compute_incremental()

        # 3. 分场景对比
        output.category_breakdown = self._breakdown_by_field("category")
        output.complexity_breakdown = self._breakdown_by_field("complexity")

        # 4. 回归检测
        if self.baseline_results:
            output.regression_detected, output.regression_details = (
                self._detect_regression()
            )

        return output

    def _build_comparison_table(self) -> list[dict]:
        """构建总览对比表"""
        chain_means = self._compute_chain_means()
        rows = []

        for dim in self.DIMENSIONS + ["weighted_score"]:
            row = {"dimension": dim}
            for chain in self.CHAINS:
                row[f"chain_{chain.lower()}"] = chain_means.get(chain, {}).get(dim, 0.0)

            # 计算增量百分比
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
        """计算各 Chain 各维度均分"""
        by_chain: dict[str, list] = {}
        for r in self.current_results:
            chain = r.get("chain", "")
            by_chain.setdefault(chain, []).append(r)

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
        """增量价值分析"""
        chain_means = self._compute_chain_means()
        a = chain_means.get("A", {}).get("weighted_score", 0)
        b = chain_means.get("B", {}).get("weighted_score", 0)
        c = chain_means.get("C", {}).get("weighted_score", 0)
        d = chain_means.get("D", {}).get("weighted_score", 0)

        return {
            "expert_vs_standard": {
                "description": "专家模式 vs 主流程",
                "formula": "(B-A)/A × 100%",
                "value": self._pct_change(b, a),
                "question": "专家模式增量价值多大？",
            },
            "expert_vs_external": {
                "description": "专家模式 vs 外部 B2C",
                "formula": "(B-C)/C × 100%",
                "value": self._pct_change(b, c),
                "question": "方案竞争力如何？",
            },
            "expert_vs_baseline": {
                "description": "专家模式 vs LLM 裸跑",
                "formula": "(B-D)/D × 100%",
                "value": self._pct_change(b, d),
                "question": "工作流编排价值几何？",
            },
            "standard_vs_baseline": {
                "description": "主流程 vs LLM 裸跑",
                "formula": "(A-D)/D × 100%",
                "value": self._pct_change(a, d),
                "question": "标准工作流价值几何？",
            },
        }

    def _breakdown_by_field(self, field_name: str) -> dict:
        """按指定字段分组对比"""
        # 需要 case metadata，暂时按 case_id 分组
        by_group: dict[str, dict[str, list]] = {}

        for r in self.current_results:
            case_id = r.get("case_id", "")
            chain = r.get("chain", "")
            group = r.get("metadata", {}).get(field_name, case_id)
            by_group.setdefault(group, {}).setdefault(chain, []).append(
                r.get("weighted_score", 0)
            )

        breakdown = {}
        for group, chain_scores in by_group.items():
            breakdown[group] = {}
            for chain, scores in chain_scores.items():
                breakdown[group][chain] = {
                    "mean": round(statistics.mean(scores), 3) if scores else 0,
                    "count": len(scores),
                }
        return breakdown

    def _detect_regression(self, threshold: float = 0.05) -> tuple:
        """
        检测回归

        Returns:
            (is_regression, details)
        """
        if not self.baseline_results:
            return False, []

        current_means = self._compute_chain_means()

        # 计算 baseline 均分
        baseline_by_chain: dict[str, list] = {}
        for r in self.baseline_results:
            chain = r.get("chain", "")
            baseline_by_chain.setdefault(chain, []).append(
                r.get("weighted_score", 0)
            )

        baseline_means = {}
        for chain, scores in baseline_by_chain.items():
            baseline_means[chain] = round(statistics.mean(scores), 3) if scores else 0

        details = []
        is_regression = False

        for chain in self.CHAINS:
            current = current_means.get(chain, {}).get("weighted_score", 0)
            baseline = baseline_means.get(chain, 0)

            if baseline > 0:
                change = (current - baseline) / baseline
                if change < -threshold:
                    is_regression = True
                    details.append({
                        "chain": chain,
                        "baseline_score": baseline,
                        "current_score": current,
                        "change_pct": round(change * 100, 2),
                        "threshold_pct": round(-threshold * 100, 2),
                    })

        return is_regression, details

    def check_regression(self, threshold: float = 0.05) -> bool:
        """快速回归检查"""
        is_regression, _ = self._detect_regression(threshold)
        return is_regression

    def generate_pr_comment(self) -> str:
        """生成 PR Comment 格式的对比报告"""
        output = self.compare()
        return ReportGenerator.generate_pr_comment(output)

    @staticmethod
    def _pct_change(new: float, old: float) -> float:
        """计算百分比变化"""
        if old == 0:
            return 0.0 if new == 0 else 100.0
        return round((new - old) / old * 100, 2)


class ReportGenerator:
    """
    报告生成器
    支持 Markdown 格式的完整对比报告和 PR Comment 简报
    """

    @staticmethod
    def generate_full_report(output: ComparatorOutput,
                             output_path: str = "") -> str:
        """生成完整对比报告（Markdown 格式）"""
        lines = ["# Loupe Eval 横向对比报告\n"]

        # 总览对比表
        lines.append("## 总览对比表\n")
        lines.append("| 指标 | Chain A (主流程) | Chain B (专家) | Chain C (外部B2C) | Chain D (裸跑) |")
        lines.append("|------|-----------------|---------------|------------------|---------------|")
        for row in output.comparison_table:
            dim = row["dimension"]
            a = row.get("chain_a", "-")
            b = row.get("chain_b", "-")
            c = row.get("chain_c", "-")
            d = row.get("chain_d", "-")
            lines.append(f"| {dim} | {a} | {b} | {c} | {d} |")
        lines.append("")

        # 增量价值分析
        lines.append("## 增量价值分析\n")
        lines.append("| 对比维度 | 计算公式 | 结果 | 核心问题 |")
        lines.append("|---------|---------|------|---------|")
        for key, item in output.incremental_analysis.items():
            lines.append(
                f"| {item['description']} | {item['formula']} | "
                f"{item['value']}% | {item['question']} |"
            )
        lines.append("")

        # 回归检测
        if output.regression_detected:
            lines.append("## ⚠️ 回归检测\n")
            for detail in output.regression_details:
                lines.append(
                    f"- **Chain {detail['chain']}**: "
                    f"{detail['baseline_score']} → {detail['current_score']} "
                    f"({detail['change_pct']}%)"
                )
            lines.append("")

        # 分场景对比
        if output.category_breakdown:
            lines.append("## 分类型对比\n")
            for cat, chain_data in output.category_breakdown.items():
                lines.append(f"### {cat}\n")
                for chain, stats in chain_data.items():
                    lines.append(
                        f"- Chain {chain}: mean={stats['mean']}, n={stats['count']}"
                    )
                lines.append("")

        report = "\n".join(lines)

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report)

        return report

    @staticmethod
    def generate_pr_comment(output: ComparatorOutput) -> str:
        """生成 PR Comment 简报"""
        lines = [
            "## 🔍 Loupe Eval 结果\n",
        ]

        # 核心指标
        inc = output.incremental_analysis
        expert_vs_std = inc.get("expert_vs_standard", {}).get("value", 0)
        expert_vs_base = inc.get("expert_vs_baseline", {}).get("value", 0)

        lines.append(f"**专家模式 vs 主流程**: {expert_vs_std:+.1f}%")
        lines.append(f"**专家模式 vs LLM 裸跑**: {expert_vs_base:+.1f}%\n")

        # 简表
        lines.append("| 维度 | Chain A | Chain B | Chain D |")
        lines.append("|------|---------|---------|---------|")
        for row in output.comparison_table:
            dim = row["dimension"]
            if dim == "weighted_score":
                dim = "**综合分**"
            a = row.get("chain_a", "-")
            b = row.get("chain_b", "-")
            d = row.get("chain_d", "-")
            lines.append(f"| {dim} | {a} | {b} | {d} |")

        # 回归警告
        if output.regression_detected:
            lines.append("\n⚠️ **检测到回归**：")
            for d in output.regression_details:
                lines.append(f"- Chain {d['chain']}: {d['change_pct']}%")

        return "\n".join(lines)


# ─── 月度对比配置 ───────────────────────────────────────────────

DEFAULT_MONTHLY_CONFIG = {
    "cases": "eval-cases/",
    "chains": ["A", "B", "C", "D"],
    "compare_with_last_month": True,
    "report_format": "markdown",
    "output_path": "eval-results/monthly-report.md",
}


# ─── CLI ────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Loupe Eval Comparator")
    parser.add_argument("--current", required=True, help="Current results dir")
    parser.add_argument("--baseline", default="", help="Baseline results dir")
    parser.add_argument("--output", default="eval-results/comparison-report.md")
    parser.add_argument("--pr-comment", action="store_true",
                        help="Output PR comment format")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    comparator = Comparator(args.current, args.baseline)

    if args.pr_comment:
        comment = comparator.generate_pr_comment()
        print(comment)
    else:
        output = comparator.compare()
        report = ReportGenerator.generate_full_report(output, args.output)
        print(f"Report generated: {args.output}")


if __name__ == "__main__":
    main()
