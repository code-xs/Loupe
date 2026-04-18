"""Loupe AI 自检自测系统 — Quality Gate (CI 质量门禁)"""

import json
import sys
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class GateResult:
    passed: bool = False
    score: float = 0.0
    min_score: float = 0.75
    regression: float = 0.0
    max_regression: float = 0.05
    zero_score_cases: int = 0
    artifact_pass_rate: float = 0.0
    avg_agent_count: float = 0.0
    max_avg_agent_count: Optional[float] = None
    failures: list = None
    details: dict = None

    def __post_init__(self):
        if self.failures is None:
            self.failures = []
        if self.details is None:
            self.details = {}


class QualityGate:
    def __init__(self, min_score: float = 0.75, max_regression: float = 0.05, min_artifact_rate: float = 0.90, max_avg_agent_count: Optional[float] = None):
        self.min_score = min_score
        self.max_regression = max_regression
        self.min_artifact_rate = min_artifact_rate
        self.max_avg_agent_count = max_avg_agent_count

    def check(self, results_dir: str, baseline_dir: str = "") -> GateResult:
        result = GateResult(min_score=self.min_score, max_regression=self.max_regression, max_avg_agent_count=self.max_avg_agent_count)
        eval_results = self._load_results(results_dir)
        if not eval_results:
            result.failures.append("No evaluation results found")
            return result
        weighted_scores = [r.get("weighted_score", 0) for r in eval_results]
        result.score = sum(weighted_scores) / len(weighted_scores)
        if result.score < self.min_score:
            result.failures.append(f"Score {result.score:.3f} < min {self.min_score}")
        if baseline_dir:
            baseline_results = self._load_results(baseline_dir)
            if baseline_results:
                baseline_scores = [r.get("weighted_score", 0) for r in baseline_results]
                baseline_mean = sum(baseline_scores) / len(baseline_scores)
                if baseline_mean > 0:
                    result.regression = (baseline_mean - result.score) / baseline_mean
                    if result.regression > self.max_regression:
                        result.failures.append(f"Regression {result.regression:.3f} > max {self.max_regression}")
        result.zero_score_cases = sum(1 for r in eval_results if r.get("weighted_score", 0) == 0)
        if result.zero_score_cases > 0:
            result.failures.append(f"{result.zero_score_cases} case(s) scored zero")
        total = len(eval_results)
        passed = sum(1 for r in eval_results if r.get("check_result", {}).get("passed", True))
        result.artifact_pass_rate = passed / total if total > 0 else 0
        if result.artifact_pass_rate < self.min_artifact_rate:
            result.failures.append(f"Artifact pass rate {result.artifact_pass_rate:.1%} < {self.min_artifact_rate:.0%}")
        agent_counts = [r.get("metadata", {}).get("runtime_metrics", {}).get("agent_count") for r in eval_results]
        agent_counts = [a for a in agent_counts if a is not None]
        result.avg_agent_count = (sum(agent_counts) / len(agent_counts)) if agent_counts else 0.0
        if self.max_avg_agent_count is not None and result.avg_agent_count > self.max_avg_agent_count:
            result.failures.append(f"Average agent count {result.avg_agent_count:.3f} > max {self.max_avg_agent_count}")
        result.passed = len(result.failures) == 0
        result.details = {
            "total_evaluations": len(eval_results),
            "mean_score": round(result.score, 3),
            "regression": round(result.regression, 3),
            "zero_score_cases": result.zero_score_cases,
            "artifact_pass_rate": round(result.artifact_pass_rate, 3),
            "avg_agent_count": round(result.avg_agent_count, 3),
        }
        return result

    @staticmethod
    def _load_results(dir_path: str) -> list[dict]:
        path = Path(dir_path)
        jf = path / "judge-results.json"
        if jf.exists():
            with open(jf, "r", encoding="utf-8") as f:
                return json.load(f)
        sf = path / "eval-summary.json"
        if sf.exists():
            with open(sf, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("results", [])
        all_results = []
        for f in path.rglob("judge-results.json"):
            with open(f, "r", encoding="utf-8") as fh:
                all_results.extend(json.load(fh))
        return all_results

    def format_report(self, result: GateResult) -> str:
        status = "PASSED" if result.passed else "FAILED"
        lines = [
            f"## Quality Gate: {status}",
            "| Metric | Value | Threshold | Status |",
            "|--------|-------|-----------|--------|",
            f"| Score | {result.score:.3f} | >= {result.min_score} | {'OK' if result.score >= result.min_score else 'FAIL'} |",
            f"| Regression | {result.regression:.3f} | <= {result.max_regression} | {'OK' if result.regression <= result.max_regression else 'FAIL'} |",
            f"| Zero Cases | {result.zero_score_cases} | 0 | {'OK' if result.zero_score_cases == 0 else 'FAIL'} |",
            f"| Artifact Rate | {result.artifact_pass_rate:.1%} | >= {self.min_artifact_rate:.0%} | {'OK' if result.artifact_pass_rate >= self.min_artifact_rate else 'FAIL'} |",
            f"| Avg Agent Count | {result.avg_agent_count:.3f} | <= {self.max_avg_agent_count if self.max_avg_agent_count is not None else 'N/A'} | {'OK' if self.max_avg_agent_count is None or result.avg_agent_count <= self.max_avg_agent_count else 'FAIL'} |",
        ]
        if result.failures:
            lines.append("")
            lines.append("### Failures")
            for failure in result.failures:
                lines.append(f"- {failure}")
        return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Loupe Quality Gate")
    parser.add_argument("--results", required=True)
    parser.add_argument("--baseline", default="")
    parser.add_argument("--min-score", type=float, default=0.75)
    parser.add_argument("--max-regression", type=float, default=0.05)
    parser.add_argument("--max-avg-agent-count", type=float, default=None)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    gate = QualityGate(min_score=args.min_score, max_regression=args.max_regression, max_avg_agent_count=args.max_avg_agent_count)
    result = gate.check(args.results, args.baseline)
    print(gate.format_report(result))
    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
