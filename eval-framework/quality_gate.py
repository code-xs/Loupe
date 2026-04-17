"""
Loupe AI 自检自测系统 — Quality Gate (CI 质量门禁)
PR 合并前的自动质量检查，判定 Pass/Fail。

Pass 条件（全部满足）：
1. 综合加权分 ≥ min_score
2. 相比 baseline 回归幅度 ≤ max_regression
3. 无 Case 评分归零（严重异常）
4. 产物完整率 ≥ 90%
"""

import json
import sys
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class GateResult:
    """门禁判定结果"""
    passed: bool = False
    score: float = 0.0
    min_score: float = 0.75
    regression: float = 0.0
    max_regression: float = 0.05
    zero_score_cases: int = 0
    artifact_pass_rate: float = 0.0
    failures: list = None
    details: dict = None

    def __post_init__(self):
        if self.failures is None:
            self.failures = []
        if self.details is None:
            self.details = {}


class QualityGate:
    """
    CI 质量门禁
    """

    def __init__(self, min_score: float = 0.75,
                 max_regression: float = 0.05,
                 min_artifact_rate: float = 0.90):
        self.min_score = min_score
        self.max_regression = max_regression
        self.min_artifact_rate = min_artifact_rate

    def check(self, results_dir: str,
              baseline_dir: str = "") -> GateResult:
        """
        执行质量门禁检查

        Args:
            results_dir: 当前评估结果目录
            baseline_dir: 基线结果目录（可选）

        Returns:
            GateResult
        """
        result = GateResult(
            min_score=self.min_score,
            max_regression=self.max_regression,
        )

        # 加载评分结果
        eval_results = self._load_results(results_dir)
        if not eval_results:
            result.failures.append("No evaluation results found")
            return result

        # 1. 综合加权分检查
        weighted_scores = [r.get("weighted_score", 0) for r in eval_results]
        result.score = sum(weighted_scores) / len(weighted_scores)

        if result.score < self.min_score:
            result.failures.append(
                f"Score {result.score:.3f} < min {self.min_score}"
            )

        # 2. 回归检查
        if baseline_dir:
            baseline_results = self._load_results(baseline_dir)
            if baseline_results:
                baseline_scores = [
                    r.get("weighted_score", 0) for r in baseline_results
                ]
                baseline_mean = sum(baseline_scores) / len(baseline_scores)
                if baseline_mean > 0:
                    result.regression = (baseline_mean - result.score) / baseline_mean
                    if result.regression > self.max_regression:
                        result.failures.append(
                            f"Regression {result.regression:.3f} > max "
                            f"{self.max_regression}"
                        )

        # 3. 零分检查
        result.zero_score_cases = sum(
            1 for r in eval_results if r.get("weighted_score", 0) == 0
        )
        if result.zero_score_cases > 0:
            result.failures.append(
                f"{result.zero_score_cases} case(s) scored zero"
            )

        # 4. 产物完整率
        total = len(eval_results)
        passed = sum(
            1 for r in eval_results
            if r.get("check_result", {}).get("passed", True)
        )
        result.artifact_pass_rate = passed / total if total > 0 else 0

        if result.artifact_pass_rate < self.min_artifact_rate:
            result.failures.append(
                f"Artifact pass rate {result.artifact_pass_rate:.1%} < "
                f"{self.min_artifact_rate:.0%}"
            )

        # 综合判定
        result.passed = len(result.failures) == 0

        result.details = {
            "total_evaluations": len(eval_results),
            "mean_score": round(result.score, 3),
            "regression": round(result.regression, 3),
            "zero_score_cases": result.zero_score_cases,
            "artifact_pass_rate": round(result.artifact_pass_rate, 3),
        }

        return result

    @staticmethod
    def _load_results(dir_path: str) -> list[dict]:
        """加载评分结果"""
        path = Path(dir_path)

        # 尝试 judge-results.json
        jf = path / "judge-results.json"
        if jf.exists():
            with open(jf, "r", encoding="utf-8") as f:
                return json.load(f)

        # 尝试 eval-summary.json
        sf = path / "eval-summary.json"
        if sf.exists():
            with open(sf, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("results", [])

        # 递归查找
        all_results = []
        for f in path.rglob("judge-results.json"):
            with open(f, "r", encoding="utf-8") as fh:
                all_results.extend(json.load(fh))
        return all_results

    def format_report(self, result: GateResult) -> str:
        """格式化门禁报告"""
        status = "✅ PASSED" if result.passed else "❌ FAILED"
        lines = [
            f"## Quality Gate: {status}\n",
            f"| Metric | Value | Threshold | Status |",
            f"|--------|-------|-----------|--------|",
            f"| Score | {result.score:.3f} | ≥ {result.min_score} | "
            f"{'✅' if result.score >= result.min_score else '❌'} |",
            f"| Regression | {result.regression:.3f} | ≤ {result.max_regression} | "
            f"{'✅' if result.regression <= result.max_regression else '❌'} |",
            f"| Zero Cases | {result.zero_score_cases} | 0 | "
            f"{'✅' if result.zero_score_cases == 0 else '❌'} |",
            f"| Artifact Rate | {result.artifact_pass_rate:.1%} | "
            f"≥ {self.min_artifact_rate:.0%} | "
            f"{'✅' if result.artifact_pass_rate >= self.min_artifact_rate else '❌'} |",
        ]

        if result.failures:
            lines.append("\n### Failures\n")
            for f in result.failures:
                lines.append(f"- ❌ {f}")

        return "\n".join(lines)


# ─── CLI ────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Loupe Quality Gate")
    parser.add_argument("--results", required=True, help="Results directory")
    parser.add_argument("--baseline", default="", help="Baseline directory")
    parser.add_argument("--min-score", type=float, default=0.75)
    parser.add_argument("--max-regression", type=float, default=0.05)

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)

    gate = QualityGate(
        min_score=args.min_score,
        max_regression=args.max_regression,
    )

    result = gate.check(args.results, args.baseline)
    report = gate.format_report(result)
    print(report)

    # 非零退出码表示失败
    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
