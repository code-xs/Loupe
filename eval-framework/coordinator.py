"""
Loupe AI 自检自测系统 — Coordinator (协调器)
核心职责：
1. 读取 eval-config.yaml，解析执行参数
2. 扫描 eval-cases/ 目录，构建 Case 队列
3. 为每个 Case × Chain 组合创建执行任务
4. V1: 串行调度 / V2: 并行调度
5. 收集产物、执行完整性校验
6. 校验失败 → 重试（最多 2 次）
7. 汇总结果到 eval-results/
"""

import os
import json
import time
import asyncio
import logging
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Optional

import yaml

from session_manager import IDESessionManager, SessionParams, SessionResult
from artifact_checker import ArtifactChecker, CheckResult
from baseline_runner import BaselineRunner

logger = logging.getLogger(__name__)


# ─── Data Models ────────────────────────────────────────────────

@dataclass
class Task:
    """单个评估任务：Case × Chain 的唯一组合"""
    case_id: str
    chain: str                  # A | B | C | D
    input_dir: str
    output_dir: str
    status: str = "pending"     # pending | running | completed | failed
    retry_count: int = 0
    error_message: Optional[str] = None

    @property
    def task_id(self) -> str:
        return f"{self.case_id}__{self.chain}"


@dataclass
class TaskResult:
    """任务执行结果"""
    task: Task
    artifacts: list = field(default_factory=list)
    validation_passed: bool = False
    check_result: Optional[dict] = None
    error_message: Optional[str] = None
    duration_seconds: float = 0.0


@dataclass
class EvalRunSummary:
    """评估运行汇总"""
    run_id: str
    total_tasks: int
    completed: int = 0
    failed: int = 0
    skipped: int = 0
    results: list = field(default_factory=list)
    start_time: str = ""
    end_time: str = ""
    duration_seconds: float = 0.0
    config_path: str = ""


# ─── Coordinator ────────────────────────────────────────────────

class Coordinator:
    """
    核心协调器 — 串行模式 (V1)
    负责 Case 队列构建、任务调度、产物校验、结果汇总
    """

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self._load_config(config_path)
        self.session_manager = IDESessionManager.from_config(self.config)
        self.artifact_checker = ArtifactChecker(
            checklist_path=self.config.get("artifact_checklist_path",
                                           "eval-framework/artifact-checklist.yaml")
        )
        self.baseline_runner = BaselineRunner(
            model=self.config.get("runner_config", {}).get("baseline_model",
                                                           "claude-sonnet-4-20250514"),
            temperature=self.config.get("runner_config", {}).get("temperature", 0.1),
        )
        self.max_retries = self.config.get("runner_config", {}).get("max_retries", 2)
        self.results_dir = self.config.get("output_config", {}).get("results_dir",
                                                                     "eval-results/")

    @staticmethod
    def _load_config(path: str) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    # ── Queue Building ──────────────────────────────────────────

    def build_queue(self, cases_dir: str, chains: list[str]) -> list[Task]:
        """
        扫描 cases_dir，为每个 Case × Chain 组合创建 Task
        """
        tasks: list[Task] = []
        cases_path = Path(cases_dir)

        if not cases_path.exists():
            raise FileNotFoundError(f"Cases directory not found: {cases_dir}")

        # 递归查找含 metadata.yaml 的 Case 目录
        case_dirs = sorted(
            d.parent for d in cases_path.rglob("metadata.yaml")
        )

        if not case_dirs:
            raise ValueError(f"No cases found in {cases_dir}")

        run_id = self._generate_run_id()
        run_output_base = Path(self.results_dir) / run_id

        for case_dir in case_dirs:
            metadata = self._load_case_metadata(case_dir)
            case_id = metadata.get("case_id", case_dir.name)

            for chain in chains:
                output_dir = str(run_output_base / case_id / f"chain-{chain}")
                os.makedirs(output_dir, exist_ok=True)

                tasks.append(Task(
                    case_id=case_id,
                    chain=chain,
                    input_dir=str(case_dir / "input"),
                    output_dir=output_dir,
                ))

        logger.info(f"Built queue: {len(tasks)} tasks "
                     f"({len(case_dirs)} cases × {len(chains)} chains)")
        return tasks

    def _load_case_metadata(self, case_dir: Path) -> dict:
        meta_path = case_dir / "metadata.yaml"
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    @staticmethod
    def _generate_run_id() -> str:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        h = hashlib.sha256(str(time.time()).encode()).hexdigest()[:6]
        return f"eval-{ts}-{h}"

    # ── Task Execution ──────────────────────────────────────────

    def execute_task(self, task: Task) -> TaskResult:
        """执行单个评估任务"""
        start = time.time()
        task.status = "running"
        logger.info(f"Executing task: {task.task_id}")

        try:
            if task.chain == "D":
                result = self._execute_baseline(task)
            elif task.chain == "C":
                result = self._execute_manual(task)
            else:
                result = self._execute_ide_session(task)

            result.duration_seconds = time.time() - start
            return result

        except Exception as e:
            task.status = "failed"
            task.error_message = str(e)
            logger.error(f"Task {task.task_id} failed: {e}")
            return TaskResult(
                task=task,
                error_message=str(e),
                duration_seconds=time.time() - start,
            )

    def _execute_ide_session(self, task: Task) -> TaskResult:
        """通过 IDE 会话执行 Chain A/B"""
        chain_def = self.config.get("chain_definitions", {}).get(task.chain, {})
        mode = chain_def.get("mode", "standard")

        params = SessionParams(
            skill=chain_def.get("skill", "mobile-qa-workflow"),
            input_file=os.path.join(task.input_dir, "issue-description.md"),
            workspace=task.output_dir,
            auto_reply_config=self.config.get("ide_config", {}).get(
                "auto_reply_config", "eval-framework/auto-reply-rules.yaml"
            ),
            chain_mode=mode,
            timeout=self.config.get("runner_config", {}).get("timeout_per_case", 1800),
            output_dir=task.output_dir,
        )

        session_result: SessionResult = self.session_manager.run_session(params)

        task.status = "completed" if session_result.exit_code == 0 else "failed"
        return TaskResult(
            task=task,
            artifacts=session_result.artifacts,
            error_message=session_result.stderr_log if session_result.exit_code != 0 else None,
        )

    def _execute_baseline(self, task: Task) -> TaskResult:
        """Chain D: LLM 裸跑"""
        issue_desc_path = os.path.join(task.input_dir, "issue-description.md")
        logs_dir = os.path.join(task.input_dir, "logs")
        code_dir = os.path.join(task.input_dir, "code-snapshot")

        output = self.baseline_runner.run_from_files(
            issue_desc_path=issue_desc_path,
            logs_dir=logs_dir,
            code_dir=code_dir,
            output_dir=task.output_dir,
        )

        task.status = "completed" if output else "failed"
        artifacts = [os.path.join(task.output_dir, "baseline-output.md")] if output else []
        return TaskResult(task=task, artifacts=artifacts)

    def _execute_manual(self, task: Task) -> TaskResult:
        """Chain C: 人工录入 — 检查是否已有录入文件"""
        manual_file = os.path.join(task.output_dir, "manual-input.md")
        if os.path.exists(manual_file):
            task.status = "completed"
            return TaskResult(task=task, artifacts=[manual_file])
        else:
            task.status = "skipped"
            return TaskResult(
                task=task,
                error_message="Manual input file not found, skipping Chain C",
            )

    # ── Artifact Validation ─────────────────────────────────────

    def validate_artifacts(self, result: TaskResult) -> bool:
        """校验任务产物完整性"""
        if result.task.chain == "D":
            # Chain D 只需检查 baseline-output.md 存在
            output_file = os.path.join(result.task.output_dir, "baseline-output.md")
            return os.path.exists(output_file)

        if result.task.chain == "C":
            return result.task.status == "completed"

        chain_mode = "expert" if result.task.chain == "B" else "standard"
        check: CheckResult = self.artifact_checker.check(
            result.task.output_dir, chain_mode
        )

        result.validation_passed = check.passed
        result.check_result = {
            "passed": check.passed,
            "missing_files": check.missing_files,
            "below_threshold": check.below_threshold,
            "missing_sections": check.missing_sections,
            "warnings": check.warnings,
        }
        return check.passed

    # ── Retry Logic ─────────────────────────────────────────────

    def retry_task(self, task: Task, max_retries: int = 2) -> TaskResult:
        """带重试的任务执行"""
        result = self.execute_task(task)

        while (not self.validate_artifacts(result)
               and task.retry_count < max_retries):
            task.retry_count += 1
            task.status = "pending"
            logger.warning(f"Retrying task {task.task_id} "
                          f"(attempt {task.retry_count}/{max_retries})")
            result = self.execute_task(task)

        if not result.validation_passed and task.retry_count >= max_retries:
            task.status = "failed"
            task.error_message = (
                f"All {max_retries} retries exhausted, "
                f"validation still failed"
            )
            logger.error(f"Task {task.task_id} failed after {max_retries} retries")

        return result

    # ── Main Run Loop ───────────────────────────────────────────

    def run(self, cases_dir: str = None, chains: list[str] = None,
            profile: str = None) -> EvalRunSummary:
        """
        主运行入口 — 串行模式
        """
        # 解析执行参数
        if profile:
            prof = self.config.get("execution_profiles", {}).get(profile, {})
            cases_dir = cases_dir or prof.get("cases", "eval-cases/")
            chains = chains or prof.get("chains", ["A", "B"])
        else:
            cases_dir = cases_dir or "eval-cases/"
            chains = chains or ["A", "B"]

        run_id = self._generate_run_id()
        start_time = datetime.now(timezone.utc)
        summary = EvalRunSummary(
            run_id=run_id,
            total_tasks=0,
            start_time=start_time.isoformat(),
            config_path=self.config_path,
        )

        # 构建队列
        tasks = self.build_queue(cases_dir, chains)
        summary.total_tasks = len(tasks)

        # 保存初始状态
        self._save_state(run_id, tasks)

        # 串行执行
        results: list[TaskResult] = []
        for task in tasks:
            result = self.retry_task(task, self.max_retries)
            results.append(result)
            self._save_state(run_id, tasks)  # 每个任务后更新状态

        # 汇总
        end_time = datetime.now(timezone.utc)
        summary.end_time = end_time.isoformat()
        summary.duration_seconds = (end_time - start_time).total_seconds()
        summary.completed = sum(1 for r in results if r.task.status == "completed")
        summary.failed = sum(1 for r in results if r.task.status == "failed")
        summary.skipped = sum(1 for r in results if r.task.status == "skipped")
        summary.results = [self._serialize_result(r) for r in results]

        # 保存汇总
        self._save_summary(run_id, summary)

        logger.info(f"Eval run {run_id} completed: "
                    f"{summary.completed}/{summary.total_tasks} passed, "
                    f"{summary.failed} failed, {summary.skipped} skipped")
        return summary

    # ── Resume (断点续跑) ───────────────────────────────────────

    def resume(self, state_path: str) -> EvalRunSummary:
        """从中断状态恢复执行"""
        with open(state_path, "r", encoding="utf-8") as f:
            state = json.load(f)

        run_id = state["run_id"]
        start_time = datetime.now(timezone.utc)

        tasks: list[Task] = []
        for t in state["tasks"]:
            task = Task(
                case_id=t["case_id"],
                chain=t["chain"],
                input_dir=t["input_dir"],
                output_dir=t["output_dir"],
                status=t["status"],
                retry_count=t.get("retry_count", 0),
            )
            tasks.append(task)

        # 筛选需要执行的任务
        pending_tasks = [
            t for t in tasks if t.status in ("pending", "running")
        ]
        # running 状态视为中断失败，需重新执行
        for t in pending_tasks:
            if t.status == "running":
                t.status = "pending"

        logger.info(f"Resuming run {run_id}: "
                    f"{len(pending_tasks)} tasks remaining")

        results: list[TaskResult] = []
        for task in pending_tasks:
            result = self.retry_task(task, self.max_retries)
            results.append(result)
            self._save_state(run_id, tasks)

        end_time = datetime.now(timezone.utc)
        summary = EvalRunSummary(
            run_id=run_id,
            total_tasks=len(tasks),
            completed=sum(1 for t in tasks if t.status == "completed"),
            failed=sum(1 for t in tasks if t.status == "failed"),
            skipped=sum(1 for t in tasks if t.status == "skipped"),
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            duration_seconds=(end_time - start_time).total_seconds(),
            config_path=self.config_path,
        )

        self._save_summary(run_id, summary)
        return summary

    # ── State Persistence ───────────────────────────────────────

    def _save_state(self, run_id: str, tasks: list[Task]):
        """保存运行状态（支持断点续跑）"""
        state = {
            "run_id": run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "config": self.config_path,
            "tasks": [asdict(t) for t in tasks],
        }
        state_dir = Path(self.results_dir) / run_id
        os.makedirs(state_dir, exist_ok=True)
        state_path = state_dir / "eval-state.json"
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

    def _save_summary(self, run_id: str, summary: EvalRunSummary):
        """保存运行汇总"""
        summary_dir = Path(self.results_dir) / run_id
        os.makedirs(summary_dir, exist_ok=True)
        summary_path = summary_dir / "eval-summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(asdict(summary), f, indent=2, ensure_ascii=False)

    @staticmethod
    def _serialize_result(result: TaskResult) -> dict:
        return {
            "task_id": result.task.task_id,
            "case_id": result.task.case_id,
            "chain": result.task.chain,
            "status": result.task.status,
            "validation_passed": result.validation_passed,
            "duration_seconds": round(result.duration_seconds, 2),
            "error_message": result.error_message,
            "artifacts": result.artifacts,
            "check_result": result.check_result,
        }


# ─── ParallelCoordinator (V2) ──────────────────────────────────

class ParallelCoordinator(Coordinator):
    """
    并行调度协调器 (V2)
    支持多个 IDE 会话并发执行，调度策略: chain_first
    """

    def __init__(self, config_path: str):
        super().__init__(config_path)
        self.max_sessions = self.config.get("parallel_config", {}).get(
            "max_sessions", 4
        )
        self.poll_interval = 5  # 秒

    async def run_parallel(self, cases_dir: str = None,
                           chains: list[str] = None,
                           profile: str = None) -> EvalRunSummary:
        """
        并行运行入口
        调度策略 chain_first: 优先为同一 Case 启动不同 Chain
        """
        if profile:
            prof = self.config.get("execution_profiles", {}).get(profile, {})
            cases_dir = cases_dir or prof.get("cases", "eval-cases/")
            chains = chains or prof.get("chains", ["A", "B"])
        else:
            cases_dir = cases_dir or "eval-cases/"
            chains = chains or ["A", "B"]

        run_id = self._generate_run_id()
        start_time = datetime.now(timezone.utc)

        tasks = self.build_queue(cases_dir, chains)

        # 按 chain_first 策略排序: 同 Case 的不同 Chain 相邻
        tasks.sort(key=lambda t: (t.case_id, t.chain))

        summary = EvalRunSummary(
            run_id=run_id,
            total_tasks=len(tasks),
            start_time=start_time.isoformat(),
            config_path=self.config_path,
        )

        # 并行调度
        results: list[TaskResult] = []
        pending = list(tasks)
        running: dict[str, asyncio.Task] = {}  # task_id -> asyncio.Task

        while pending or running:
            # 填充空位
            while pending and len(running) < self.max_sessions:
                task = pending.pop(0)
                atask = asyncio.create_task(
                    self._async_execute(task)
                )
                running[task.task_id] = atask

            # 等待任意一个完成
            if running:
                done, _ = await asyncio.wait(
                    running.values(),
                    timeout=self.poll_interval,
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for completed_task in done:
                    result: TaskResult = completed_task.result()
                    results.append(result)
                    # 从 running 中移除
                    tid = result.task.task_id
                    running.pop(tid, None)

                    # 校验 + 重试
                    if not self.validate_artifacts(result):
                        if result.task.retry_count < self.max_retries:
                            result.task.retry_count += 1
                            result.task.status = "pending"
                            pending.append(result.task)
                            logger.warning(
                                f"Re-queuing {tid} "
                                f"(attempt {result.task.retry_count})"
                            )

            self._save_state(run_id, tasks)

        end_time = datetime.now(timezone.utc)
        summary.end_time = end_time.isoformat()
        summary.duration_seconds = (end_time - start_time).total_seconds()
        summary.completed = sum(1 for r in results
                                if r.task.status == "completed")
        summary.failed = sum(1 for r in results
                             if r.task.status == "failed")
        summary.results = [self._serialize_result(r) for r in results]

        self._save_summary(run_id, summary)
        return summary

    async def _async_execute(self, task: Task) -> TaskResult:
        """异步包装同步执行"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.execute_task, task)


# ─── CLI Entry Point ────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Loupe Eval Coordinator")
    subparsers = parser.add_subparsers(dest="command")

    # run 子命令
    run_parser = subparsers.add_parser("run", help="Run evaluation")
    run_parser.add_argument("--config", required=True, help="Config YAML path")
    run_parser.add_argument("--cases", help="Cases directory")
    run_parser.add_argument("--chains", help="Comma-separated chain list")
    run_parser.add_argument("--parallel", type=int, default=1,
                            help="Max parallel sessions")
    run_parser.add_argument("--profile", help="Execution profile name")

    # resume 子命令
    resume_parser = subparsers.add_parser("resume", help="Resume interrupted run")
    resume_parser.add_argument("--state", required=True,
                               help="Path to eval-state.json")
    resume_parser.add_argument("--config", required=True, help="Config YAML path")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if args.command == "run":
        chains = args.chains.split(",") if args.chains else None

        if args.parallel > 1:
            coord = ParallelCoordinator(args.config)
            summary = asyncio.run(coord.run_parallel(
                cases_dir=args.cases, chains=chains, profile=args.profile
            ))
        else:
            coord = Coordinator(args.config)
            summary = coord.run(
                cases_dir=args.cases, chains=chains, profile=args.profile
            )

        print(json.dumps(asdict(summary), indent=2, ensure_ascii=False))

    elif args.command == "resume":
        coord = Coordinator(args.config)
        summary = coord.resume(args.state)
        print(json.dumps(asdict(summary), indent=2, ensure_ascii=False))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
