"""
Loupe AI 自检自测系统 — Optimizer (自检迭代器)
低分归因分析 + 改进方案生成 + 应用/回滚
安全机制: 单次最多改 2 个文件, 改进前 git tag, 全量回归验证
"""

import os
import json
import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ImprovementPlan:
    """改进方案"""
    plan_id: str = ""
    weakness_category: str = ""
    weakness_dimension: str = ""
    target_files: list = field(default_factory=list)  # 修改的文件列表（最多 2 个）
    improvement_type: str = ""   # prompt | reference | agent | template
    description: str = ""
    diff_content: dict = field(default_factory=dict)  # file → diff 内容
    expected_improvement: float = 0.0
    git_tag: str = ""           # 改进前的 git tag
    applied: bool = False
    verified: bool = False
    rolled_back: bool = False


@dataclass
class ImprovementResult:
    """改进执行结果"""
    plan: ImprovementPlan = field(default_factory=ImprovementPlan)
    before_scores: dict = field(default_factory=dict)
    after_scores: dict = field(default_factory=dict)
    score_delta: float = 0.0
    passed: bool = False
    reason: str = ""


# ─── Diagnosis Prompt ───────────────────────────────────────────

DIAGNOSIS_PROMPT = """你是 Loupe 工作流优化专家。分析以下薄弱环节并给出精确到文件和段落的改进方案。

## 薄弱环节
- 类型: {weakness_category}
- 维度: {weakness_dimension}
- 均分: {mean_score}（阈值: {threshold}）
- 影响 Case: {affected_cases}

## 低分 Case 产物摘要
{low_score_outputs}

## 当前 Phase Prompt 内容
{current_prompt_content}

## 改进要求
1. 精确指出当前 Prompt/Reference/Template 的不足
2. 给出具体的修改内容（diff 格式）
3. 每次最多修改 2 个文件
4. 修改必须保持向后兼容
5. 不要改动 workflow.xml 等架构文件（需人工审批）

请输出 JSON 格式:
```json
{{
  "target_files": ["path/to/file1.md"],
  "improvement_type": "prompt",
  "description": "改进描述",
  "changes": {{
    "path/to/file1.md": {{
      "action": "append|replace|insert_after",
      "location": "## Section Name",
      "content": "新增/替换的内容"
    }}
  }},
  "expected_improvement": 0.5
}}
```
"""


class Optimizer:
    """
    自检迭代器
    诊断流程:
    1. 读取低分 Case 的完整执行产物
    2. 读取对应的 Phase Prompt 文件
    3. 让高能力 LLM 对比分析差距
    4. 生成精确到文件和段落的改进 diff
    """

    # 安全限制
    MAX_FILES_PER_CHANGE = 2
    MAX_AUTO_ITERATIONS = 5
    GROUND_TRUTH_DIRS = ["ground-truth", "eval-cases"]
    ARCHITECTURE_FILES = [
        "core/workflow.xml",
        "core/workflow-model.yaml",
        "core/core-rules.xml",
    ]

    def __init__(self, model: str = "claude-opus-4-20250514",
                 workspace_root: str = "mobile-qa-workflow",
                 api_key: Optional[str] = None):
        self.model = model
        self.workspace_root = workspace_root
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._plan_counter = 0

    def diagnose(self, weakness_report,
                 eval_results: list[dict]) -> list[ImprovementPlan]:
        """
        诊断并生成改进方案

        Args:
            weakness_report: WeaknessDetector 输出
            eval_results: 评分结果

        Returns:
            ImprovementPlan 列表
        """
        plans = []

        for weakness in weakness_report.top_priorities:
            # 收集低分 Case 产物
            low_score_outputs = self._collect_low_score_outputs(
                weakness, eval_results
            )

            # 读取当前 Prompt 内容
            current_content = self._read_related_prompt(weakness)

            # 调用 LLM 生成改进方案
            plan = self._generate_plan(weakness, low_score_outputs, current_content)
            if plan:
                # 安全检查
                if self._safety_check(plan):
                    plans.append(plan)
                else:
                    logger.warning(
                        f"Plan {plan.plan_id} rejected by safety check"
                    )

        return plans

    def apply(self, plan: ImprovementPlan) -> bool:
        """
        应用改进方案

        安全流程:
        1. Git tag 当前状态
        2. 应用改进
        3. 标记 applied = True
        """
        # 1. Git tag
        plan.git_tag = f"pre-optimize-{plan.plan_id}"
        self._git_tag(plan.git_tag)

        # 2. 应用改进
        for file_path, change in plan.diff_content.items():
            full_path = os.path.join(self.workspace_root, file_path)
            if not os.path.exists(full_path):
                logger.error(f"Target file not found: {full_path}")
                return False

            try:
                self._apply_change(full_path, change)
            except Exception as e:
                logger.error(f"Failed to apply change to {full_path}: {e}")
                self.rollback(plan)
                return False

        plan.applied = True
        logger.info(f"Applied improvement plan: {plan.plan_id}")
        return True

    def rollback(self, plan: ImprovementPlan) -> bool:
        """回滚改进方案"""
        if not plan.git_tag:
            logger.error("No git tag for rollback")
            return False

        try:
            subprocess.run(
                ["git", "checkout", plan.git_tag, "--", "."],
                cwd=self.workspace_root,
                capture_output=True, check=True,
            )
            plan.rolled_back = True
            plan.applied = False
            logger.info(f"Rolled back plan: {plan.plan_id}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Rollback failed: {e}")
            return False

    def _generate_plan(self, weakness, low_score_outputs: str,
                        current_content: str) -> Optional[ImprovementPlan]:
        """调用 LLM 生成改进方案"""
        prompt = DIAGNOSIS_PROMPT.format(
            weakness_category=weakness.category,
            weakness_dimension=weakness.dimension,
            mean_score=weakness.mean_score,
            threshold=weakness.threshold,
            affected_cases=", ".join(weakness.affected_cases[:5]),
            low_score_outputs=low_score_outputs[:5000],
            current_prompt_content=current_content[:3000],
        )

        try:
            response = self._call_llm(prompt)
            return self._parse_plan_response(response, weakness)
        except Exception as e:
            logger.error(f"Plan generation failed: {e}")
            return None

    def _parse_plan_response(self, response: str,
                              weakness) -> Optional[ImprovementPlan]:
        """解析 LLM 改进方案输出"""
        import re

        json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
        if json_match:
            raw = json_match.group(1)
        else:
            raw = response

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Failed to parse optimizer JSON response")
            return None

        self._plan_counter += 1
        plan = ImprovementPlan(
            plan_id=f"opt-{self._plan_counter:03d}",
            weakness_category=weakness.category,
            weakness_dimension=weakness.dimension,
            target_files=data.get("target_files", []),
            improvement_type=data.get("improvement_type", "prompt"),
            description=data.get("description", ""),
            diff_content=data.get("changes", {}),
            expected_improvement=data.get("expected_improvement", 0.5),
        )
        return plan

    def _safety_check(self, plan: ImprovementPlan) -> bool:
        """改进方案安全检查"""
        # 1. 文件数限制
        if len(plan.target_files) > self.MAX_FILES_PER_CHANGE:
            logger.warning(
                f"Plan modifies {len(plan.target_files)} files "
                f"(max {self.MAX_FILES_PER_CHANGE})"
            )
            return False

        # 2. 架构文件保护
        for f in plan.target_files:
            if any(arch in f for arch in self.ARCHITECTURE_FILES):
                logger.warning(
                    f"Plan touches architecture file: {f} — needs manual approval"
                )
                return False

        # 3. ground-truth 保护
        for f in plan.target_files:
            if any(gt in f for gt in self.GROUND_TRUTH_DIRS):
                logger.warning(
                    f"Plan touches ground-truth: {f} — needs manual confirmation"
                )
                return False

        return True

    def _collect_low_score_outputs(self, weakness,
                                    eval_results: list[dict]) -> str:
        """收集薄弱 Case 的产物摘要"""
        affected = set(weakness.affected_cases)
        parts = []

        for r in eval_results:
            if r.get("case_id", "") in affected:
                reasoning = r.get("reasoning", {}).get(weakness.dimension, "")
                parts.append(
                    f"Case {r['case_id']} (score: "
                    f"{r.get('scores', {}).get(weakness.dimension, 0)}):\n"
                    f"  Reasoning: {reasoning}\n"
                )

        return "\n".join(parts[:5])

    def _read_related_prompt(self, weakness) -> str:
        """读取与薄弱环节相关的 Prompt 文件"""
        # Stage → 文件映射
        from weakness_detector import WeaknessDetector
        stage_files = WeaknessDetector.STAGE_TO_FILE

        dim = weakness.dimension
        if dim in stage_files:
            path = os.path.join(self.workspace_root, stage_files[dim])
        elif weakness.improvement_type == "prompt":
            # 根据维度推断文件
            path = os.path.join(
                self.workspace_root,
                "functionality-deep-dive/phases/",
            )
        else:
            path = ""

        if path and os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                return ""
        return ""

    @staticmethod
    def _apply_change(file_path: str, change: dict):
        """应用单个文件改动"""
        action = change.get("action", "append")
        location = change.get("location", "")
        content = change.get("content", "")

        with open(file_path, "r", encoding="utf-8") as f:
            original = f.read()

        if action == "append":
            modified = original + "\n" + content
        elif action == "replace" and location:
            # 替换指定 section
            import re
            pattern = rf"(## {re.escape(location)}\n)(.*?)(\n## |\Z)"
            replacement = f"\\1{content}\n\\3"
            modified = re.sub(pattern, replacement, original, flags=re.DOTALL)
        elif action == "insert_after" and location:
            idx = original.find(location)
            if idx >= 0:
                insert_pos = original.find("\n", idx) + 1
                modified = original[:insert_pos] + content + "\n" + original[insert_pos:]
            else:
                modified = original + "\n" + content
        else:
            modified = original + "\n" + content

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(modified)

    def _git_tag(self, tag: str):
        """创建 git tag"""
        try:
            subprocess.run(
                ["git", "tag", tag],
                cwd=self.workspace_root,
                capture_output=True, check=True,
            )
        except subprocess.CalledProcessError:
            logger.warning(f"Git tag failed: {tag}")

    def _call_llm(self, prompt: str) -> str:
        """调用 LLM"""
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            message = client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text
        except ImportError:
            logger.warning("anthropic not installed")
            return "{}"
