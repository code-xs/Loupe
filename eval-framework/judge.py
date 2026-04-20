"""
Loupe AI 自检自测系统 — LLM-as-Judge (评分核心)
"""

import os
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class EvalResult:
    case_id: str = ""
    chain: str = ""
    scores: dict = field(default_factory=dict)
    weighted_score: float = 0.0
    reasoning: dict = field(default_factory=dict)
    stage_scores: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)


@dataclass
class ChainOutput:
    output_dir: str = ""
    chain: str = ""
    artifacts: dict = field(default_factory=dict)


@dataclass
class CaseData:
    case_id: str = ""
    input_dir: str = ""
    ground_truth_dir: str = ""
    metadata: dict = field(default_factory=dict)
    expected_root_cause: str = ""
    expected_contributing: str = ""
    expected_fix_direction: str = ""
    scoring_rubric: dict = field(default_factory=dict)


JUDGE_SYSTEM_PROMPT = """你是一位资深的移动端质量评估专家。你的任务是对一个问题分析系统的输出进行盲评。"""

JUDGE_EVAL_PROMPT = """## 评估任务

### Ground Truth（人工标注的正确答案）

**期望主根因:**
{expected_root_cause}

**期望贡献因子:**
{expected_contributing}

**期望修复方向:**
{expected_fix_direction}

### 被评估的分析输出

{analysis_output}

---

### 评分维度及标尺

#### 1. 归因准确率 (attribution_accuracy) — 权重 {w_attribution}
- 10分: 主根因精确匹配 Ground Truth
- 7分: 部分匹配
- 4分: 仅识别了贡献因子
- 0分: 完全未命中

#### 2. 贡献因子完整性 (contributing_completeness) — 权重 {w_contributing}
- 10分: 识别了所有关键贡献因子
- 7分: 识别了 70%+ 的贡献因子
- 4分: 识别了部分贡献因子
- 0分: 未识别任何贡献因子

#### 3. 修复方向正确性 (fix_correctness) — 权重 {w_fix}
- 10分: 修复方案直接解决根因，且无副作用
- 7分: 修复方向正确但方案有瑕疵
- 4分: 修复方向部分正确
- 0分: 修复方向错误

#### 4. 推理链深度 (reasoning_depth) — 权重 {w_reasoning}
- 10分: 因果链完整、证据引用充分、逻辑严密
- 7分: 因果链基本完整，少量证据缺失
- 4分: 有因果分析但不够深入
- 0分: 缺乏结构化推理

#### 5. 产物完整性 (artifact_completeness) — 权重 {w_artifact}
- 10分: 所有模板字段齐全，格式规范
- 7分: 核心字段齐全，部分细节缺失
- 4分: 缺失重要字段
- 0分: 产物严重不完整

#### 6. 防御性修复质量 (defensive_fix_quality) — 权重 {w_defensive}
- 10分: 充分考虑架构鲁棒性
- 7分: 有部分防御性考虑
- 4分: 仅修复直接问题
- 0分: 修复方案可能引入新风险

#### 7. 契约溯源首次通过准确率 (contract_first_pass_accuracy) — 权重 {w_contract}
#### 8. 幻觉拦截率 (hallucination_interception) — 权重 {w_hallucination}
#### 9. 自愈修复率 (self_healing_rate) — 权重 {w_self_healing}

请输出严格 JSON 格式:
```json
{{
  "scores": {{
    "attribution_accuracy": <0-10>,
    "contributing_completeness": <0-10>,
    "fix_correctness": <0-10>,
    "reasoning_depth": <0-10>,
    "artifact_completeness": <0-10>,
    "defensive_fix_quality": <0-10>,
    "contract_first_pass_accuracy": <0-10>,
    "hallucination_interception": <0-10>,
    "self_healing_rate": <0-10>
  }},
  "reasoning": {{
    "attribution_accuracy": "<评分理由>",
    "contributing_completeness": "<评分理由>",
    "fix_correctness": "<评分理由>",
    "reasoning_depth": "<评分理由>",
    "artifact_completeness": "<评分理由>",
    "defensive_fix_quality": "<评分理由>",
    "contract_first_pass_accuracy": "<评分理由>",
    "hallucination_interception": "<评分理由>",
    "self_healing_rate": "<评分理由>"
  }},
  "stage_scores": {{
    "F1_context_reconstruction": <0-10>,
    "F2_state_topology": <0-10>,
    "F3_temporal_correlation": <0-10>,
    "F4_isolation_debate": <0-10>,
    "F5_defensive_fix": <0-10>
  }},
  "overall_comment": "<总体评价>"
}}
```"""


class LLMJudge:
    def __init__(self, model: str = "claude-opus-4-20250514", rubric_path: str = "eval-framework/scoring-rubric-base.yaml", api_key: Optional[str] = None):
        self.model = model
        self.rubric = self._load_rubric(rubric_path)
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.weights = self.rubric.get("weights", {
            "attribution_accuracy": 0.30,
            "contributing_completeness": 0.12,
            "fix_correctness": 0.18,
            "reasoning_depth": 0.08,
            "artifact_completeness": 0.09,
            "defensive_fix_quality": 0.08,
            "contract_first_pass_accuracy": 0.08,
            "hallucination_interception": 0.04,
            "self_healing_rate": 0.03,
        })

    @staticmethod
    def _load_rubric(path: str) -> dict:
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def evaluate(self, case: CaseData, chain_output: ChainOutput) -> EvalResult:
        prompt = JUDGE_EVAL_PROMPT.format(
            expected_root_cause=case.expected_root_cause,
            expected_contributing=case.expected_contributing,
            expected_fix_direction=case.expected_fix_direction,
            analysis_output=self._collect_analysis_text(chain_output),
            w_attribution=self.weights.get("attribution_accuracy", 0.30),
            w_contributing=self.weights.get("contributing_completeness", 0.12),
            w_fix=self.weights.get("fix_correctness", 0.18),
            w_reasoning=self.weights.get("reasoning_depth", 0.08),
            w_artifact=self.weights.get("artifact_completeness", 0.09),
            w_defensive=self.weights.get("defensive_fix_quality", 0.08),
            w_contract=self.weights.get("contract_first_pass_accuracy", 0.08),
            w_hallucination=self.weights.get("hallucination_interception", 0.04),
            w_self_healing=self.weights.get("self_healing_rate", 0.03),
        )
        raw_response = self._call_judge(prompt)
        result = self._parse_judge_response(raw_response)
        result.case_id = case.case_id
        result.chain = chain_output.chain
        result.weighted_score = self._compute_weighted_score(result.scores)
        runtime_metrics = self._collect_runtime_metrics(chain_output.output_dir)
        result.metadata = {**case.metadata, "runtime_metrics": runtime_metrics}
        if case.scoring_rubric:
            result = self._apply_rubric_overrides(result, case.scoring_rubric)
        return result

    def batch_evaluate(self, items: list[tuple]) -> list[EvalResult]:
        results = []
        for case, chain_output in items:
            try:
                results.append(self.evaluate(case, chain_output))
            except Exception as e:
                logger.error("Evaluation failed for %s: %s", case.case_id, e)
                results.append(EvalResult(case_id=case.case_id, chain=chain_output.chain, metadata={"error": str(e)}))
        return results

    def _collect_analysis_text(self, chain_output: ChainOutput) -> str:
        priority_files = [
            "rca-report.md",
            "fix-design.md",
            "spec.md",
            "issue-card.md",
            "impl-report.md",
            "verification-report.md",
            "contract-checklist.md",
            "error-dump.md",
            "deep-dive/deep-dive-summary.md",
            "deep-dive/functionality-deep-dive-rca.md",
            "deep-dive/defensive-fix-design.md",
            "baseline-output.md",
        ]
        parts = []
        for fname in priority_files:
            fpath = os.path.join(chain_output.output_dir, fname)
            if os.path.exists(fpath):
                try:
                    content = Path(fpath).read_text(encoding="utf-8")
                except Exception:
                    continue
                parts.append(f"--- {fname} ---\n{self._redact_chain_info(content)}\n")
        return "\n".join(parts) if parts else "[无产物]"

    @staticmethod
    def _redact_chain_info(text: str) -> str:
        import re
        text = re.sub(r"Chain\s*[ABCD]", "Chain [REDACTED]", text, flags=re.IGNORECASE)
        text = re.sub(r"chain_mode:\s*(standard|expert)", "chain_mode: [REDACTED]", text)
        return text

    def _call_judge(self, prompt: str) -> str:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            message = client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.0,
                system=JUDGE_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text
        except ImportError:
            return self._placeholder_response()

    @staticmethod
    def _placeholder_response() -> str:
        return json.dumps({
            "scores": {
                "attribution_accuracy": 5.0,
                "contributing_completeness": 5.0,
                "fix_correctness": 5.0,
                "reasoning_depth": 5.0,
                "artifact_completeness": 5.0,
                "defensive_fix_quality": 5.0,
                "contract_first_pass_accuracy": 5.0,
                "hallucination_interception": 5.0,
                "self_healing_rate": 5.0,
            },
            "reasoning": {
                "attribution_accuracy": "[占位]",
                "contributing_completeness": "[占位]",
                "fix_correctness": "[占位]",
                "reasoning_depth": "[占位]",
                "artifact_completeness": "[占位]",
                "defensive_fix_quality": "[占位]",
                "contract_first_pass_accuracy": "[占位]",
                "hallucination_interception": "[占位]",
                "self_healing_rate": "[占位]",
            },
            "stage_scores": {
                "F1_context_reconstruction": 5.0,
                "F2_state_topology": 5.0,
                "F3_temporal_correlation": 5.0,
                "F4_isolation_debate": 5.0,
                "F5_defensive_fix": 5.0,
            },
            "overall_comment": "[占位 - 配置 ANTHROPIC_API_KEY 以获取真实评分]",
        })

    def _parse_judge_response(self, raw: str) -> EvalResult:
        result = EvalResult()
        import re
        json_match = re.search(r"```json\s*(.*?)\s*```", raw, re.DOTALL)
        raw_json = json_match.group(1) if json_match else raw
        try:
            data = json.loads(raw_json)
            result.scores = data.get("scores", {})
            result.reasoning = data.get("reasoning", {})
            result.stage_scores = data.get("stage_scores", {})
            result.metadata["overall_comment"] = data.get("overall_comment", "")
        except json.JSONDecodeError:
            result.scores = self._fallback_parse(raw)
        return result

    @staticmethod
    def _fallback_parse(text: str) -> dict:
        import re
        scores = {}
        patterns = {
            "attribution_accuracy": r'attribution_accuracy["\']?\s*:\s*(\d+(?:\.\d+)?)',
            "contributing_completeness": r'contributing_completeness["\']?\s*:\s*(\d+(?:\.\d+)?)',
            "fix_correctness": r'fix_correctness["\']?\s*:\s*(\d+(?:\.\d+)?)',
            "reasoning_depth": r'reasoning_depth["\']?\s*:\s*(\d+(?:\.\d+)?)',
            "artifact_completeness": r'artifact_completeness["\']?\s*:\s*(\d+(?:\.\d+)?)',
            "defensive_fix_quality": r'defensive_fix_quality["\']?\s*:\s*(\d+(?:\.\d+)?)',
            "contract_first_pass_accuracy": r'contract_first_pass_accuracy["\']?\s*:\s*(\d+(?:\.\d+)?)',
            "hallucination_interception": r'hallucination_interception["\']?\s*:\s*(\d+(?:\.\d+)?)',
            "self_healing_rate": r'self_healing_rate["\']?\s*:\s*(\d+(?:\.\d+)?)',
        }
        for key, pattern in patterns.items():
            match = re.search(pattern, text)
            scores[key] = float(match.group(1)) if match else 0.0
        return scores

    def _compute_weighted_score(self, scores: dict) -> float:
        return round(sum(scores.get(dim, 0.0) * weight for dim, weight in self.weights.items()), 3)

    @staticmethod
    def _apply_rubric_overrides(result: EvalResult, rubric: dict) -> EvalResult:
        overrides = {
            "attribution_weight_override": "attribution_accuracy",
            "contributing_weight_override": "contributing_completeness",
            "fix_weight_override": "fix_correctness",
        }
        default_weights = {
            "attribution_accuracy": 0.30,
            "contributing_completeness": 0.12,
            "fix_correctness": 0.18,
            "reasoning_depth": 0.08,
            "artifact_completeness": 0.09,
            "defensive_fix_quality": 0.08,
            "contract_first_pass_accuracy": 0.08,
            "hallucination_interception": 0.04,
            "self_healing_rate": 0.03,
        }
        custom = {dim: rubric[key] for key, dim in overrides.items() if rubric.get(key) is not None}
        if custom:
            weights = {**default_weights, **custom}
            result.weighted_score = round(sum(result.scores.get(dim, 0.0) * weight for dim, weight in weights.items()), 3)
        return result

    @staticmethod
    def _collect_runtime_metrics(output_dir: str) -> dict:
        status_path = Path(output_dir) / "workflow-status.yaml"
        if not status_path.exists():
            return {}
        try:
            status = yaml.safe_load(status_path.read_text(encoding="utf-8")) or {}
        except Exception:
            return {}
        specialized = status.get("specialized_workflow", {}) or {}
        return {
            "analysis_complexity": status.get("analysis_complexity"),
            "fanout_mode": status.get("fanout_mode"),
            "fix_strategy_mode": status.get("fix_strategy_mode"),
            "specialized_workflow_mode": specialized.get("mode"),
            "specialized_workflow_status": specialized.get("status"),
            "agent_count": LLMJudge._estimate_agent_count(status.get("fanout_mode"), status.get("fix_strategy_mode"), specialized.get("mode")),
        }

    @staticmethod
    def _estimate_agent_count(fanout_mode: Optional[str], fix_strategy_mode: Optional[str], specialized_mode: Optional[str]) -> int:
        mapping = {
            "simple-single": 1,
            "medium-challenge": 2,
            "complex-arbitrated": 4,
            "single-proposer": 1,
            "challenged-proposer": 2,
            "contested-arbitrated": 4,
        }
        total = 0
        if fanout_mode:
            total += mapping.get(fanout_mode, 0)
        if fix_strategy_mode:
            total += mapping.get(fix_strategy_mode, 0)
        if specialized_mode == "functionality-deep-dive":
            total += 4
        return total

    @staticmethod
    def load_case_data(case_dir: str) -> CaseData:
        case_path = Path(case_dir)
        def read_file(path: Path) -> str:
            return path.read_text(encoding="utf-8") if path.exists() else ""
        metadata = {}
        meta_path = case_path / "metadata.yaml"
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                metadata = yaml.safe_load(f) or {}
        rubric = {}
        rubric_path = case_path / "ground-truth" / "scoring-rubric.yaml"
        if rubric_path.exists():
            with open(rubric_path, "r", encoding="utf-8") as f:
                rubric = yaml.safe_load(f) or {}
        return CaseData(
            case_id=metadata.get("case_id", case_path.name),
            input_dir=str(case_path / "input"),
            ground_truth_dir=str(case_path / "ground-truth"),
            metadata=metadata,
            expected_root_cause=read_file(case_path / "ground-truth" / "expected-root-cause.md"),
            expected_contributing=read_file(case_path / "ground-truth" / "expected-contributing.md"),
            expected_fix_direction=read_file(case_path / "ground-truth" / "expected-fix-direction.md"),
            scoring_rubric=rubric,
        )

    @staticmethod
    def load_chain_output(output_dir: str, chain: str = "") -> ChainOutput:
        return ChainOutput(output_dir=output_dir, chain=chain)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Loupe Eval Judge")
    parser.add_argument("--results", required=True)
    parser.add_argument("--rubric", default="eval-framework/scoring-rubric-base.yaml")
    parser.add_argument("--cases", default="eval-cases/")
    parser.add_argument("--model", default="claude-opus-4-20250514")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    judge = LLMJudge(model=args.model, rubric_path=args.rubric)
    results_path = Path(args.results)
    cases_path = Path(args.cases)
    all_results = []
    for case_dir in sorted(results_path.iterdir()):
        if not case_dir.is_dir():
            continue
        case_id = case_dir.name
        matching_cases = list(cases_path.rglob(f"*{case_id}*"))
        case_data_dir = matching_cases[0] if matching_cases else None
        if not case_data_dir:
            continue
        case_data = LLMJudge.load_case_data(str(case_data_dir))
        for chain_dir in sorted(case_dir.iterdir()):
            if not chain_dir.is_dir():
                continue
            chain = chain_dir.name.replace("chain-", "")
            result = judge.evaluate(case_data, LLMJudge.load_chain_output(str(chain_dir), chain))
            all_results.append(result)
    output_data = [{
        "case_id": r.case_id,
        "chain": r.chain,
        "weighted_score": r.weighted_score,
        "scores": r.scores,
        "reasoning": r.reasoning,
        "stage_scores": r.stage_scores,
        "metadata": r.metadata,
    } for r in all_results]
    output_path = args.output or str(results_path / "judge-results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print(f"Evaluation complete: {len(all_results)} results -> {output_path}")


if __name__ == "__main__":
    main()
