"""
Loupe AI 自检自测系统 V3 — Eval Framework

评估框架核心模块，提供完整的自检自测闭环能力：

模块说明:
    coordinator         - 核心协调器（V1 串行 / V2 并行）
    session_manager     - IDE 会话生命周期管理 + IDEAdapter 适配层
    artifact_checker    - 产物完整性校验（含 required_sections）
    baseline_runner     - Chain D LLM 裸跑执行器
    judge               - LLM-as-Judge 评分核心（6 维度盲评）
    scoring_engine      - 评分维度计算与加权统计
    comparator          - 横向链路对比器
    report_generator    - 多格式报告生成器
    weakness_detector   - 薄弱环节定位（Case 类型 × Stage 交叉分析）
    optimizer           - 低分归因分析 + 自动改进生成
    iteration_loop      - 迭代闭环控制（Eval → Optimize → Verify → Merge/Rollback）
    quality_gate        - CI 质量门禁

Chains:
    A - 主流程（标准 RCA）
    B - 专家模式（Functionality Deep-Dive）
    C - 外部 B2C 方案（人工录入）
    D - LLM 裸跑基线

Scoring Dimensions (6):
    attribution_accuracy        (35%) - 归因准确率
    contributing_completeness   (15%) - 贡献因子完整性
    fix_correctness             (20%) - 修复方向正确性
    reasoning_depth             (10%) - 推理链深度
    artifact_completeness       (10%) - 产物完整性
    defensive_fix_quality       (10%) - 防御性修复质量
"""

__version__ = "3.0.0"
__author__ = "Loupe Team"

from .coordinator import Coordinator, ParallelCoordinator, Task, TaskResult, EvalRunSummary
from .session_manager import IDESessionManager, IDEAdapter, SessionParams, Session, SessionResult
from .artifact_checker import ArtifactChecker, CheckResult
from .baseline_runner import BaselineRunner
from .judge import LLMJudge, EvalResult
from .scoring_engine import ScoringEngine, ScoringReport
from .comparator import Comparator, ComparatorOutput
from .report_generator import ReportGenerator
from .weakness_detector import WeaknessDetector, WeaknessReport
from .optimizer import Optimizer, ImprovementPlan
from .iteration_loop import IterationLoop, IterationResult
from .quality_gate import QualityGate, GateResult

__all__ = [
    # Coordinator
    "Coordinator", "ParallelCoordinator", "Task", "TaskResult", "EvalRunSummary",
    # Session Management
    "IDESessionManager", "IDEAdapter", "SessionParams", "Session", "SessionResult",
    # Artifact Checking
    "ArtifactChecker", "CheckResult",
    # Baseline
    "BaselineRunner",
    # Judge & Scoring
    "LLMJudge", "EvalResult", "ScoringEngine", "ScoringReport",
    # Comparison & Reporting
    "Comparator", "ComparatorOutput", "ReportGenerator",
    # Optimization Loop
    "WeaknessDetector", "WeaknessReport",
    "Optimizer", "ImprovementPlan",
    "IterationLoop", "IterationResult",
    # Quality Gate
    "QualityGate", "GateResult",
]
