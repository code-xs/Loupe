"""
Loupe AI 自检自测系统 — Report Generator (报告生成器)
生成各类评估报告：完整报告、PR Comment、月度对比、趋势分析。

V3.1: 适配 9 维度展示
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ReportGenerator:
    """多格式评估报告生成器"""

    def __init__(self, results_dir: str = "eval-results/"):
        self.results_dir = results_dir

    def generate_baseline_report(self, eval_results: list,
                                  scoring_report: dict,
                                  comparison_output: dict = None,
                                  output_path: str = "") -> str:
        """
        生成基准报告 (baseline-report.md)

        Args:
            eval_results: Judge 评分结果
            scoring_report: ScoringEngine 输出
            comparison_output: Comparator 输出（可选）
            output_path: 输出路径

        Returns:
            报告 Markdown 文本
        """
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        lines = [
            "# Loupe 基准评估报告",
            "",
            "**生成时间**: {}".format(now),
            "**评估 Case 数**: {}".format(len(set(r.get('case_id', '') for r in eval_results))),
            "**评估链路数**: {}".format(len(set(r.get('chain', '') for r in eval_results))),
            "**总评估次数**: {}".format(len(eval_results)),
            "",
            "---",
            "",
        ]

        # 链路统计
        chain_stats = scoring_report.get("chain_stats", {})
        if chain_stats:
            lines.append("## 链路综合评分\n")
            lines.append("| Chain | 综合均分 | Case 数 |")
            lines.append("|-------|---------|---------|")
            for chain, stats in sorted(chain_stats.items()):
                lines.append(
                    "| {} | {:.3f} | {} |".format(
                        chain, stats.get('weighted_mean', 0), stats.get('case_count', 0))
                )
            lines.append("")

        # 维度明细 (V3.1: 9 维度)
        if chain_stats:
            lines.append("## 维度明细评分\n")
            dims = [
                "attribution_accuracy", "contributing_completeness",
                "fix_correctness", "reasoning_depth",
                "artifact_completeness", "defensive_fix_quality",
                "contract_first_pass_accuracy", "hallucination_interception",
                "self_healing_rate",
            ]
            header = "| 维度 |"
            sep = "|------|"
            for chain in sorted(chain_stats.keys()):
                header += " {} |".format(chain)
                sep += "------|"
            lines.append(header)
            lines.append(sep)

            for dim in dims:
                row = "| {} |".format(dim)
                for chain in sorted(chain_stats.keys()):
                    dim_stats = chain_stats[chain].get("dimension_stats", {}).get(dim, {})
                    mean = dim_stats.get("mean", 0)
                    row += " {:.2f} |".format(mean)
                lines.append(row)
            lines.append("")

        # 阶段级评分
        any_stage = any(
            stats.get("stage_stats")
            for stats in chain_stats.values()
        )
        if any_stage:
            lines.append("## 阶段级评分 (Functionality Deep-Dive)\n")
            stages = [
                "F1_context_reconstruction", "F2_state_topology",
                "F3_temporal_correlation", "F4_isolation_debate",
                "F5_defensive_fix",
            ]
            header = "| Stage |"
            sep = "|-------|"
            for chain in sorted(chain_stats.keys()):
                header += " {} |".format(chain)
                sep += "------|"
            lines.append(header)
            lines.append(sep)

            for stage in stages:
                row = "| {} |".format(stage)
                for chain in sorted(chain_stats.keys()):
                    s_stats = chain_stats[chain].get("stage_stats", {}).get(stage, {})
                    mean = s_stats.get("mean", 0)
                    row += " {:.2f} |".format(mean) if mean > 0 else " N/A |"
                lines.append(row)
            lines.append("")

        # 分类型分布
        cat_stats = scoring_report.get("category_stats", {})
        if cat_stats:
            lines.append("## 分类型评分分布\n")
            for cat, chain_data in sorted(cat_stats.items()):
                lines.append("### {}\n".format(cat))
                for chain, data in sorted(chain_data.items()):
                    lines.append("- Chain {}: mean={:.3f} (n={})".format(
                        chain, data.get('mean', 0), data.get('count', 0)))
                lines.append("")

        # 复杂度分布
        comp_stats = scoring_report.get("complexity_stats", {})
        if comp_stats:
            lines.append("## 复杂度级别评分分布\n")
            for comp, chain_data in sorted(comp_stats.items()):
                lines.append("### {}\n".format(comp))
                for chain, data in sorted(chain_data.items()):
                    lines.append("- Chain {}: mean={:.3f} (n={})".format(
                        chain, data.get('mean', 0), data.get('count', 0)))
                lines.append("")

        # 低分 Case 列表
        low_score_cases = [
            r for r in eval_results if r.get("weighted_score", 10) < 5.0
        ]
        if low_score_cases:
            lines.append("## ⚠️ 低分 Case 列表 (< 5.0)\n")
            lines.append("| Case ID | Chain | Score | 主要薄弱维度 |")
            lines.append("|---------|-------|-------|-------------|")
            for r in sorted(low_score_cases, key=lambda x: x.get("weighted_score", 0)):
                scores = r.get("scores", {})
                weakest = min(scores, key=scores.get) if scores else "N/A"
                lines.append(
                    "| {} | {} | {:.2f} | {} |".format(
                        r.get('case_id', ''), r.get('chain', ''),
                        r.get('weighted_score', 0), weakest)
                )
            lines.append("")

        report = "\n".join(lines)

        if not output_path:
            output_path = str(Path(self.results_dir) / "baseline-report.md")
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
        logger.info("Baseline report generated: {}".format(output_path))

        return report

    def generate_iteration_report(self, iteration_num: int,
                                   before_scores: dict,
                                   after_scores: dict,
                                   improvement_plan: dict,
                                   output_path: str = "") -> str:
        """生成迭代改进报告"""
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        lines = [
            "# 迭代改进报告 — 第 {} 轮".format(iteration_num),
            "",
            "**时间**: {}".format(now),
            "",
            "## 改进前后对比\n",
            "| 维度 | 改进前 | 改进后 | 变化 |",
            "|------|-------|-------|------|",
        ]

        for dim in before_scores:
            before = before_scores.get(dim, 0)
            after = after_scores.get(dim, 0)
            change = after - before
            emoji = "📈" if change > 0 else ("📉" if change < 0 else "➡️")
            lines.append(
                "| {} | {:.2f} | {:.2f} | {} {:+.2f} |".format(
                    dim, before, after, emoji, change)
            )

        lines.append("")
        lines.append("## 改进方案\n")
        lines.append("- **目标文件**: {}".format(improvement_plan.get('target_file', 'N/A')))
        lines.append("- **改进类型**: {}".format(improvement_plan.get('type', 'N/A')))
        lines.append("- **改进描述**: {}".format(improvement_plan.get('description', 'N/A')))

        report = "\n".join(lines)

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report)

        return report
