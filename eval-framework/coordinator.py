"""
Loupe AI 自检自测系统 — Coordinator (协调器)
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

try:
    from .session_manager import IDESessionManager, SessionParams, SessionResult
    from .artifact_checker import ArtifactChecker, CheckResult
    from .baseline_runner import BaselineRunner
    from .metrics import collect_runtime_metrics, estimate_agent_count
except ImportError:
    from session_manager import IDESessionManager, SessionParams, SessionResult
    from artifact_checker import ArtifactChecker, CheckResult
    from baseline_runner import BaselineRunner
    from metrics import collect_runtime_metrics, estimate_agent_count

logger = logging.getLogger(__name__)


@dataclass
class Task:
    case_id: str
    chain: str
    input_dir: str
    output_dir: str
    status: str = "pending"
    retry_count: int = 0
    error_message: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    @property
    def task_id(self) -> str:
        return f"{self.case_id}__{self.chain}"


@dataclass
class TaskResult:
    task: Task
    artifacts: list = field(default_factory=list)
    validation_passed: bool = False
    check_result: Optional[dict] = None
    error_message: Optional[str] = None
    duration_seconds: float = 0.0
    runtime_metrics: dict = field(default_factory=dict)


@dataclass
class EvalRunSummary:
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


class Coordinator:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self._load_config(config_path)
        self.session_manager = IDESessionManager.from_config(self.config)
        self.artifact_checker = ArtifactChecker(
            checklist_path=self.config.get(
                "artifact_checklist_path",
                "eval-framework/artifact-checklist.yaml",
            )
        )
        self.baseline_runner = BaselineRunner(
            model=self.config.get("runner_config", {}).get(
                "baseline_model", "claude-sonnet-4-20250514"
            ),
            temperature=self.config.get("runner_config", {}).get("temperature", 0.1),
        )
        self.max_retries = self.config.get("runner_config", {}).get("max_retries", 2)
        self.results_dir = self.config.get("output_config", {}).get(
            "results_dir", "eval-results/"
        )

    @staticmethod
    def _load_config(path: str) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def build_queue(self, cases_dir: str, chains: list[str]) -> list[Task]:
        tasks: list[Task] = []
        cases_path = Path(cases_dir)
        if not cases_path.exists():
            raise FileNotFoundError(f"Cases directory not found: {cases_dir}")
        case_dirs = sorted(d.parent for d in cases_path.rglob("metadata.yaml"))
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
                tasks.append(
                    Task(
                        case_id=case_id,
                        chain=chain,
                        input_dir=str(case_dir / "input"),
                        output_dir=output_dir,
                        metadata=metadata,
                    )
                )
        logger.info("Built queue: %s tasks", len(tasks))
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

    def execute_task(self, task: Task) -> TaskResult:
        start = time.time()
        task.status = "running"
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
            logger.error("Task %s failed: %s", task.task_id, e)
            return TaskResult(
                task=task,
                error_message=str(e),
                duration_seconds=time.time() - start,
            )

    def _execute_ide_session(self, task: Task) -> TaskResult:
        chain_def = self.config.get("chain_definitions", {}).get(task.chain, {})
        params = SessionParams(
            skill=chain_def.get("skill", "mobile-qa-workflow"),
            input_file=os.path.join(task.input_dir, "issue-description.md"),
            workspace=task.output_dir,
            auto_reply_config=self.config.get("ide_config", {}).get(
                "auto_reply_config", "eval-framework/auto-reply-rules.yaml"
            ),
            chain_mode=chain_def.get("mode", "standard"),
            timeout=self.config.get("runner_config", {}).get("timeout_per_case", 1800),
            output_dir=task.output_dir,
        )
        session_result: SessionResult = self.session_manager.run_session(params)
        task.status = "completed" if session_result.exit_code == 0 else "failed"
        return TaskResult(
            task=task,
            artifacts=session_result.artifacts,
            error_message=(session_result.stderr_log if session_result.exit_code != 0 else None),
            runtime_metrics=self._collect_runtime_metrics(task.output_dir),
        )

    def _execute_baseline(self, task: Task) -> TaskResult:
        output = self.baseline_runner.run_from_files(
            issue_desc_path=os.path.join(task.input_dir, "issue-description.md"),
            logs_dir=os.path.join(task.input_dir, "logs"),
            code_dir=os.path.join(task.input_dir, "code-snapshot"),
            output_dir=task.output_dir,
        )
        task.status = "completed" if output else "failed"
        return TaskResult(
            task=task,
            artifacts=[os.path.join(task.output_dir, "baseline-output.md")] if output else [],
            runtime_metrics=self._collect_runtime_metrics(task.output_dir),
        )

    def _execute_manual(self, task: Task) -> TaskResult:
        manual_file = os.path.join(task.output_dir, "manual-input.md")
        if os.path.exists(manual_file):
            task.status = "completed"
            return TaskResult(
                task=task,
                artifacts=[manual_file],
                runtime_metrics=self._collect_runtime_metrics(task.output_dir),
            )
        task.status = "skipped"
        return TaskResult(task=task, error_message="Manual input file not found, skipping Chain C")

    def validate_artifacts(self, result: TaskResult) -> bool:
        if result.task.chain == "D":
            output_file = os.path.join(result.task.output_dir, "baseline-output.md")
            result.validation_passed = os.path.exists(output_file)
            return result.validation_passed
        if result.task.chain == "C":
            result.validation_passed = result.task.status == "completed"
            return result.validation_passed
        chain_mode = "expert" if result.task.chain == "B" else "standard"
        check: CheckResult = self.artifact_checker.check(result.task.output_dir, chain_mode)
        result.validation_passed = check.passed
        result.check_result = {
            "passed": check.passed,
            "missing_files": check.missing_files,
            "below_threshold": check.below_threshold,
            "missing_sections": check.missing_sections,
            "warnings": check.warnings,
        }
        return check.passed

    def retry_task(self, task: Task, max_retries: int = 2) -> TaskResult:
        result = self.execute_task(task)
        while (not self.validate_artifacts(result)) and task.retry_count < max_retries:
            task.retry_count += 1
            task.status = "pending"
            logger.warning("Retrying task %s (%s/%s)", task.task_id, task.retry_count, max_retries)
            result = self.execute_task(task)
        if not result.validation_passed and task.retry_count >= max_retries:
            task.status = "failed"
            task.error_message = f"All {max_retries} retries exhausted, validation still failed"
        return result

    def _resolve_profile(self, profile: str) -> dict:
        prof = self.config.get("execution_profiles", {}).get(profile, {})
        if "config_file" in prof:
            resolved = dict(prof)
            ext_config = self._load_config(prof["config_file"])
            if isinstance(ext_config, dict):
                top = ext_config.get(next(iter(ext_config)), ext_config) if len(ext_config) == 1 and isinstance(next(iter(ext_config.values())), dict) else ext_config
                resolved.setdefault("cases", top.get("cases_dir") or top.get("cases"))
                resolved.setdefault("chains", top.get("chains"))
                resolved.setdefault("runs_per_case", top.get("runs_per_case"))
            return resolved
        return prof

    def run(self, cases_dir: str = None, chains: list[str] = None, profile: str = None) -> EvalRunSummary:
        if profile:
            prof = self._resolve_profile(profile)
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
        tasks = self.build_queue(cases_dir, chains)
        summary.total_tasks = len(tasks)
        self._save_state(run_id, tasks)
        results: list[TaskResult] = []
        for task in tasks:
            result = self.retry_task(task, self.max_retries)
            results.append(result)
            self._save_state(run_id, tasks)
        end_time = datetime.now(timezone.utc)
        summary.end_time = end_time.isoformat()
        summary.duration_seconds = (end_time - start_time).total_seconds()
        summary.completed = sum(1 for r in results if r.task.status == "completed")
        summary.failed = sum(1 for r in results if r.task.status == "failed")
        summary.skipped = sum(1 for r in results if r.task.status == "skipped")
        summary.results = [self._serialize_result(r) for r in results]
        self._save_summary(run_id, summary)
        return summary

    def resume(self, state_path: str) -> EvalRunSummary:
        with open(state_path, "r", encoding="utf-8") as f:
            state = json.load(f)
        run_id = state["run_id"]
        start_time = datetime.now(timezone.utc)
        tasks: list[Task] = []
        for t in state["tasks"]:
            tasks.append(
                Task(
                    case_id=t["case_id"],
                    chain=t["chain"],
                    input_dir=t["input_dir"],
                    output_dir=t["output_dir"],
                    status=t["status"],
                    retry_count=t.get("retry_count", 0),
                    metadata=t.get("metadata", {}),
                )
            )
        pending_tasks = [t for t in tasks if t.status in ("pending", "running")]
        for t in pending_tasks:
            if t.status == "running":
                t.status = "pending"
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

    def _save_state(self, run_id: str, tasks: list[Task]):
        state = {
            "run_id": run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "config": self.config_path,
            "tasks": [asdict(t) for t in tasks],
        }
        state_dir = Path(self.results_dir) / run_id
        os.makedirs(state_dir, exist_ok=True)
        with open(state_dir / "eval-state.json", "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

    def _save_summary(self, run_id: str, summary: EvalRunSummary):
        summary_dir = Path(self.results_dir) / run_id
        os.makedirs(summary_dir, exist_ok=True)
        with open(summary_dir / "eval-summary.json", "w", encoding="utf-8") as f:
            json.dump(asdict(summary), f, indent=2, ensure_ascii=False)

    @staticmethod
    def _collect_runtime_metrics(output_dir: str) -> dict:
        return collect_runtime_metrics(output_dir)

    @staticmethod
    def _estimate_agent_count(fanout_mode: Optional[str], fix_strategy_mode: Optional[str], specialized_mode: Optional[str]) -> int:
        return estimate_agent_count(fanout_mode, fix_strategy_mode, specialized_mode)

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
            "metadata": result.task.metadata,
            "runtime_metrics": result.runtime_metrics,
        }


class ParallelCoordinator(Coordinator):
    def __init__(self, config_path: str):
        super().__init__(config_path)
        self.max_sessions = self.config.get("parallel_config", {}).get("max_sessions", 4)
        self.poll_interval = 5

    async def run_parallel(self, cases_dir: str = None, chains: list[str] = None, profile: str = None) -> EvalRunSummary:
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
        tasks.sort(key=lambda t: (t.case_id, t.chain))
        summary = EvalRunSummary(run_id=run_id, total_tasks=len(tasks), start_time=start_time.isoformat(), config_path=self.config_path)
        results: list[TaskResult] = []
        pending = list(tasks)
        running: dict[str, asyncio.Task] = {}
        while pending or running:
            while pending and len(running) < self.max_sessions:
                task = pending.pop(0)
                running[task.task_id] = asyncio.create_task(self._async_execute(task))
            if running:
                done, _ = await asyncio.wait(running.values(), timeout=self.poll_interval, return_when=asyncio.FIRST_COMPLETED)
                for completed_task in done:
                    result: TaskResult = completed_task.result()
                    results.append(result)
                    running.pop(result.task.task_id, None)
                    if not self.validate_artifacts(result) and result.task.retry_count < self.max_retries:
                        result.task.retry_count += 1
                        result.task.status = "pending"
                        pending.append(result.task)
            self._save_state(run_id, tasks)
        end_time = datetime.now(timezone.utc)
        summary.end_time = end_time.isoformat()
        summary.duration_seconds = (end_time - start_time).total_seconds()
        summary.completed = sum(1 for r in results if r.task.status == "completed")
        summary.failed = sum(1 for r in results if r.task.status == "failed")
        summary.results = [self._serialize_result(r) for r in results]
        self._save_summary(run_id, summary)
        return summary

    async def _async_execute(self, task: Task) -> TaskResult:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.execute_task, task)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Loupe Eval Coordinator")
    subparsers = parser.add_subparsers(dest="command")
    run_parser = subparsers.add_parser("run", help="Run evaluation")
    run_parser.add_argument("--config", required=True, help="Config YAML path")
    run_parser.add_argument("--cases", help="Cases directory")
    run_parser.add_argument("--chains", help="Comma-separated chain list")
    run_parser.add_argument("--parallel", type=int, default=1, help="Max parallel sessions")
    run_parser.add_argument("--profile", help="Execution profile name")
    resume_parser = subparsers.add_parser("resume", help="Resume interrupted run")
    resume_parser.add_argument("--state", required=True, help="Path to eval-state.json")
    resume_parser.add_argument("--config", required=True, help="Config YAML path")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    if args.command == "run":
        chains = args.chains.split(",") if args.chains else None
        if args.parallel > 1:
            coord = ParallelCoordinator(args.config)
            summary = asyncio.run(coord.run_parallel(cases_dir=args.cases, chains=chains, profile=args.profile))
        else:
            coord = Coordinator(args.config)
            summary = coord.run(cases_dir=args.cases, chains=chains, profile=args.profile)
        print(json.dumps(asdict(summary), indent=2, ensure_ascii=False))
    elif args.command == "resume":
        coord = Coordinator(args.config)
        summary = coord.resume(args.state)
        print(json.dumps(asdict(summary), indent=2, ensure_ascii=False))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
