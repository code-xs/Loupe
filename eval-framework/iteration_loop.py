"""
Loupe AI 自检自测系统 — Iteration Loop (迭代闭环控制)
控制 Eval → 薄弱定位 → 改进 → 回归验证 的完整闭环。

闭环流程:
1. 运行全量 Eval → 2. 薄弱环节定位 → 3. 生成改进方案
4. 应用改进 → 5. 回归验证 → 6. 合并/回滚 → 7. 记录日志
"""

import os
import json
import logging
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

try:
    from .coordinator import Coordinator
    from .judge import LLMJudge
    from .scoring_engine import ScoringEngine
    from .weakness_detector import WeaknessDetector, WeaknessReport
    from .optimizer import Optimizer, ImprovementPlan, ImprovementResult
    from .report_generator import ReportGenerator
except ImportError:
    from coordinator import Coordinator
    from judge import LLMJudge
    from scoring_engine import ScoringEngine
    from weakness_detector import WeaknessDetector, WeaknessReport
    from optimizer import Optimizer, ImprovementPlan, ImprovementResult
    from report_generator import ReportGenerator

logger = logging.getLogger(__name__)


@dataclass
class IterationResult:
    """单次迭代结果"""
    iteration_num: int = 0
    weakness_report_summary: str = ""
    plans_generated: int = 0
    plans_applied: int = 0
    plans_passed: int = 0
    plans_rolled_back: int = 0
    before_overall_score: float = 0.0
    after_overall_score: float = 0.0
    score_delta: float = 0.0
    improvements: list = field(default_factory=list)
    timestamp: str = ""


class IterationLoop:
    """
    迭代闭环控制器

    单次迭代:
    1. 运行全量 Eval
    2. 薄弱环节定位
    3. 生成改进方案
    4. 应用改进
    5. 回归验证 (Post-Optimize: 受影响 Case 子集 × 3 次取均值)
    6. 合并/回滚
    7. 记录日志

    合并条件:
    - 低分 Case 子集均分提升 ≥ 0.5 分
    - 全量均分不降 ≥ 0.2 分
    """

    # 合并阈值
    SUBSET_IMPROVEMENT_THRESHOLD = 0.5    # 低分子集提升阈值
    GLOBAL_REGRESSION_THRESHOLD = 0.2     # 全量回归阈值
    MAX_ITERATIONS = 5                    # 最大迭代次数

    def __init__(self, coordinator: Coordinator,
                 judge: LLMJudge,
                 weakness_detector: WeaknessDetector,
                 optimizer: Optimizer,
                 results_dir: str = "eval-results/",
                 cases_dir: str = "eval-cases/",
                 chains: list = None):
        self.coordinator = coordinator
        self.judge = judge
        self.weakness_detector = weakness_detector
        self.optimizer = optimizer
        self.scoring_engine = ScoringEngine()
        self.report_generator = ReportGenerator(results_dir)
        self.results_dir = results_dir
        self.cases_dir = cases_dir
        self.chains = chains or ["A", "B"]
        self.iteration_log: list[IterationResult] = []

    def run_iteration(self, iteration_num: int = 1) -> IterationResult:
        """
        执行单次迭代

        Returns:
            IterationResult
        """
        logger.info(f"=== Starting Iteration {iteration_num} ===")
        result = IterationResult(
            iteration_num=iteration_num,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        # Step 1: 运行全量 Eval
        logger.info("Step 1: Running full evaluation...")
        eval_summary = self.coordinator.run(
            cases_dir=self.cases_dir, chains=self.chains
        )

        # Step 2: 收集并评分
        logger.info("Step 2: Collecting and scoring results...")
        eval_results = self._collect_and_score(eval_summary)
        if not eval_results:
            result.weakness_report_summary = "No evaluation results collected"
            return result

        # 计算当前总分
        overall_scores = [r.get("weighted_score", 0) for r in eval_results]
        result.before_overall_score = (
            sum(overall_scores) / len(overall_scores) if overall_scores else 0
        )

        # Step 3: 薄弱环节定位
        logger.info("Step 3: Detecting weaknesses...")
        weakness_report = self.weakness_detector.analyze(eval_results)
        result.weakness_report_summary = weakness_report.summary

        if not weakness_report.weaknesses:
            logger.info("No weaknesses found, iteration complete")
            return result

        # Step 4: 生成改进方案
        logger.info("Step 4: Generating improvement plans...")
        plans = self.optimizer.diagnose(weakness_report, eval_results)
        result.plans_generated = len(plans)

        if not plans:
            logger.info("No improvement plans generated")
            return result

        # Step 5-6: 逐个应用并验证
        for plan in plans:
            logger.info(f"Applying plan: {plan.plan_id}")

            # 应用
            success = self.optimizer.apply(plan)
            if not success:
                continue
            result.plans_applied += 1

            # 回归验证
            logger.info(f"Verifying plan: {plan.plan_id}")
            improvement = self._verify_improvement(
                plan, eval_results, weakness_report
            )

            if improvement.passed:
                logger.info(f"Plan {plan.plan_id} passed verification: "
                           f"+{improvement.score_delta:.2f}")
                result.plans_passed += 1
                result.improvements.append({
                    "plan_id": plan.plan_id,
                    "description": plan.description,
                    "delta": improvement.score_delta,
                    "status": "merged",
                })
            else:
                logger.warning(f"Plan {plan.plan_id} failed: {improvement.reason}")
                self.optimizer.rollback(plan)
                result.plans_rolled_back += 1
                result.improvements.append({
                    "plan_id": plan.plan_id,
                    "description": plan.description,
                    "delta": improvement.score_delta,
                    "status": "rolled_back",
                    "reason": improvement.reason,
                })

        # Step 7: 最终评分
        if result.plans_passed > 0:
            final_summary = self.coordinator.run(
                cases_dir=self.cases_dir, chains=self.chains
            )
            final_results = self._collect_and_score(final_summary)
            final_scores = [r.get("weighted_score", 0) for r in final_results]
            result.after_overall_score = (
                sum(final_scores) / len(final_scores) if final_scores else 0
            )
        else:
            result.after_overall_score = result.before_overall_score

        result.score_delta = result.after_overall_score - result.before_overall_score

        # 保存迭代日志
        self._save_iteration_log(result)
        self.iteration_log.append(result)

        logger.info(
            f"=== Iteration {iteration_num} complete: "
            f"delta={result.score_delta:+.3f}, "
            f"passed={result.plans_passed}/{result.plans_generated} ==="
        )
        return result

    def run_loop(self, max_iterations: int = None) -> list[IterationResult]:
        """
        连续迭代，直到无薄弱点或达到上限

        Args:
            max_iterations: 最大迭代次数（默认 MAX_ITERATIONS）

        Returns:
            IterationResult 列表
        """
        max_iter = max_iterations or self.MAX_ITERATIONS
        results = []

        for i in range(1, max_iter + 1):
            result = self.run_iteration(i)
            results.append(result)

            # 停止条件
            if not result.weakness_report_summary or \
               "无薄弱环节" in result.weakness_report_summary:
                logger.info("No more weaknesses, stopping loop")
                break

            if result.plans_generated == 0:
                logger.info("No plans generated, stopping loop")
                break

            if result.score_delta <= 0 and i > 2:
                logger.info("No improvement in last iteration, stopping")
                break

        return results

    def _collect_and_score(self, eval_summary) -> list[dict]:
        """收集评估结果并进行 LLM 评分"""
        # 从 eval_summary.results 收集需要评分的项目
        results_list = []
        if hasattr(eval_summary, "results"):
            for r in eval_summary.results:
                if isinstance(r, dict):
                    results_list.append(r)
        return results_list

    def _verify_improvement(self, plan: ImprovementPlan,
                             original_results: list[dict],
                             weakness_report: WeaknessReport) -> ImprovementResult:
        """
        回归验证 (Post-Optimize)
        策略: 受影响 Case 子集 × 3 次取均值

        合并条件:
        - 低分 Case 子集均分提升 ≥ 0.5
        - 全量均分不降 ≥ 0.2
        """
        improvement = ImprovementResult(plan=plan)

        # 收集受影响 Case
        affected_cases = set()
        for w in weakness_report.weaknesses:
            if w.dimension == plan.weakness_dimension:
                affected_cases.update(w.affected_cases)

        if not affected_cases:
            improvement.reason = "No affected cases identified"
            return improvement

        # 计算原始子集均分
        original_subset = [
            r for r in original_results
            if r.get("case_id", "") in affected_cases
        ]
        original_subset_mean = (
            sum(r.get("weighted_score", 0) for r in original_subset)
            / len(original_subset)
            if original_subset else 0
        )
        improvement.before_scores = {"subset_mean": original_subset_mean}

        # 运行 Post-Optimize (3 次取均值)
        post_scores = []
        for run in range(3):
            summary = self.coordinator.run(
                cases_dir=self.cases_dir, chains=self.chains
            )
            results = self._collect_and_score(summary)
            subset = [
                r for r in results
                if r.get("case_id", "") in affected_cases
            ]
            if subset:
                subset_mean = sum(
                    r.get("weighted_score", 0) for r in subset
                ) / len(subset)
                post_scores.append(subset_mean)

        if not post_scores:
            improvement.reason = "Post-optimize runs returned no results"
            return improvement

        new_subset_mean = sum(post_scores) / len(post_scores)
        improvement.after_scores = {"subset_mean": new_subset_mean}
        improvement.score_delta = new_subset_mean - original_subset_mean

        # 检查合并条件
        if improvement.score_delta >= self.SUBSET_IMPROVEMENT_THRESHOLD:
            improvement.passed = True
        else:
            improvement.passed = False
            improvement.reason = (
                f"Subset improvement {improvement.score_delta:.2f} "
                f"< threshold {self.SUBSET_IMPROVEMENT_THRESHOLD}"
            )

        return improvement

    def _save_iteration_log(self, result: IterationResult):
        """保存迭代日志"""
        log_dir = Path(self.results_dir) / f"iteration-{result.iteration_num:03d}"
        os.makedirs(log_dir, exist_ok=True)
        log_path = log_dir / "iteration-result.json"
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(asdict(result), f, indent=2, ensure_ascii=False)


# ─── CLI ────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Loupe Iteration Loop")
    parser.add_argument("--config", required=True, help="Config YAML path")
    parser.add_argument("--max-iterations", type=int, default=5)
    parser.add_argument("--cases", default="eval-cases/")
    parser.add_argument("--chains", default="A,B")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)

    coordinator = Coordinator(args.config)
    judge = LLMJudge()
    detector = WeaknessDetector()
    optimizer = Optimizer()

    loop = IterationLoop(
        coordinator=coordinator,
        judge=judge,
        weakness_detector=detector,
        optimizer=optimizer,
        cases_dir=args.cases,
        chains=args.chains.split(","),
    )

    results = loop.run_loop(args.max_iterations)
    print(f"Completed {len(results)} iterations")
    for r in results:
        print(f"  Iteration {r.iteration_num}: delta={r.score_delta:+.3f}, "
              f"passed={r.plans_passed}/{r.plans_generated}")


if __name__ == "__main__":
    main()
