"""Loupe AI 自检自测系统 — Report Generator (报告生成器)"""

import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


class ReportGenerator:
    def __init__(self, results_dir: str = "eval-results/"):
        self.results_dir = results_dir

    def generate_baseline_report(self, eval_results: list, scoring_report: dict, comparison_output: dict = None, output_path: str = "") -> str:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        lines = [
            "# Loupe 基准评估报告",
            "",
            f"**生成时间**: {now}",
            f"**评估 Case 数**: {len(set(r.get('case_id', '') for r in eval_results))}",
            f"**总评估次数**: {len(eval_results)}",
            "",
            "---",
            "",
        ]
        chain_stats = scoring_report.get("chain_stats", {})
        if chain_stats:
            lines.extend(["## 链路综合评分", "| Chain | 综合均分 | Case 数 |", "|-------|---------|---------|"])
            for chain, stats in sorted(chain_stats.items()):
                lines.append(f"| {chain} | {stats.get('weighted_mean', 0):.3f} | {stats.get('case_count', 0)} |")
            lines.append("")
        if chain_stats:
            dims = [
                "attribution_accuracy", "contributing_completeness", "fix_correctness", "reasoning_depth",
                "artifact_completeness", "defensive_fix_quality", "contract_first_pass_accuracy",
                "hallucination_interception", "self_healing_rate",
            ]
            lines.extend(["## 维度明细评分"])
            header = "| 维度 |" + "".join(f" {chain} |" for chain in sorted(chain_stats.keys()))
            sep = "|------|" + "".join("------|" for _ in sorted(chain_stats.keys()))
            lines.extend([header, sep])
            for dim in dims:
                row = f"| {dim} |"
                for chain in sorted(chain_stats.keys()):
                    mean = chain_stats[chain].get("dimension_stats", {}).get(dim, {}).get("mean", 0)
                    row += f" {mean:.2f} |"
                lines.append(row)
            lines.append("")
        eff = scoring_report.get("efficiency_metrics", {})
        if eff:
            lines.append("## 效率指标")
            for chain, metrics in sorted(eff.items()):
                lines.append(f"### Chain {chain}")
                lines.append(f"- 平均单 Case agent 数: {metrics.get('avg_agent_count', 0)}")
                lines.append(f"- 每 Agent 得分: {metrics.get('score_per_agent', 0)}")
                lines.append(f"- Deep-Dive 进入率: {metrics.get('deep_dive_activation_rate', 0)}")
                lines.append(f"- P3 fan-out 分布: {metrics.get('fanout_distribution', {})}")
                lines.append(f"- P4 fix 路由分布: {metrics.get('fix_strategy_distribution', {})}")
        if comparison_output and comparison_output.get("efficiency_metrics"):
            lines.append("## 对比效率解读")
            for chain, metrics in sorted(comparison_output["efficiency_metrics"].items()):
                lines.append(f"- Chain {chain}: route_hit={metrics.get('expected_route_hit_rate')}, fanout_hit={metrics.get('expected_fanout_hit_rate')}, specialized_delta={metrics.get('specialized_score_delta')}")
            lines.append("")
        report = "\n".join(lines)
        if not output_path:
            output_path = str(Path(self.results_dir) / "baseline-report.md")
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(report, encoding="utf-8")
        logger.info("Baseline report generated: %s", output_path)
        return report

    def generate_iteration_report(self, iteration_num: int, before_scores: dict, after_scores: dict, improvement_plan: dict, output_path: str = "") -> str:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        lines = [f"# 迭代改进报告 — 第 {iteration_num} 轮", "", f"**时间**: {now}", "", "## 改进前后对比", "| 维度 | 改进前 | 改进后 | 变化 |", "|------|-------|-------|------|"]
        for dim in before_scores:
            before = before_scores.get(dim, 0)
            after = after_scores.get(dim, 0)
            change = after - before
            lines.append(f"| {dim} | {before:.2f} | {after:.2f} | {change:+.2f} |")
        lines.extend(["", "## 改进方案", f"- **目标文件**: {improvement_plan.get('target_file', 'N/A')}", f"- **改进类型**: {improvement_plan.get('type', 'N/A')}", f"- **改进描述**: {improvement_plan.get('description', 'N/A')}"])
        report = "\n".join(lines)
        if output_path:
            Path(output_path).write_text(report, encoding="utf-8")
        return report
