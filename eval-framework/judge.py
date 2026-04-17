"""
Loupe AI 自检自测系统 — LLM-as-Judge (评分核心)
使用独立高能力模型 (Claude Opus) 对链路输出进行盲评。
设计要点:
- 在干净上下文中工作，读取静态产物文件
- Judge 不得看到 Chain 标识（盲评）
- 每次评分独立上下文（无跨 Case 记忆）
- 6 维度评估: 归因准确率/贡献因子完整性/修复方向正确性/推理链深度/产物完整性/防御性修复质量
"""

import os
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)


# ─── Data Models ────────────────────────────────────────────────

@dataclass
class EvalResult:
    """单条链路评估结果"""
    case_id: str = ""
    chain: str = ""
    scores: dict = field(default_factory=dict)       # 维度 → 分数
    weighted_score: float = 0.0                      # 加权综合分
    reasoning: dict = field(default_factory=dict)    # 维度 → 评分理由
    stage_scores: dict = field(default_factory=dict) # 阶段级拆分 (F1-F5 / P1-P6)
    metadata: dict = field(default_factory=dict)


@dataclass
class ChainOutput:
    """链路输出产物集合"""
    output_dir: str = ""
    chain: str = ""
    artifacts: dict = field(default_factory=dict)  # filename → content


@dataclass
class CaseData:
    """Case 数据 (含 ground-truth)"""
    case_id: str = ""
    input_dir: str = ""
    ground_truth_dir: str = ""
    metadata: dict = field(default_factory=dict)
    expected_root_cause: str = ""
    expected_contributing: str = ""
    expected_fix_direction: str = ""
    scoring_rubric: dict = field(default_factory=dict)


# ─── Judge Prompts ──────────────────────────────────────────────

JUDGE_SYSTEM_PROMPT = """你是一位资深的移动端质量评估专家。你的任务是对一个问题分析系统的输出进行盲评。

评估规则:
1. 你不知道这个输出来自哪个系统或链路
2. 每个维度独立评分，0-10 分
3. 必须给出具体的评分理由
4. 对比 Ground Truth 进行客观评估
5. 不因输出篇幅长短而加分或减分，只看质量

请严格按照 JSON 格式输出评分结果。"""

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
- 7分: 部分匹配（识别了正确方向但不够精确）
- 4分: 仅识别了贡献因子，未找到主根因
- 0分: 完全未命中
- -2分: 给出了错误的根因（false positive，从 0 分中扣减）

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
- 10分: 充分考虑架构鲁棒性，包含熔断/断言/守卫等防御措施
- 7分: 有部分防御性考虑
- 4分: 仅修复直接问题，无防御考虑
- 0分: 修复方案可能引入新风险

请输出严格 JSON 格式:
```json
{{
  "scores": {{
    "attribution_accuracy": <0-10>,
    "contributing_completeness": <0-10>,
    "fix_correctness": <0-10>,
    "reasoning_depth": <0-10>,
    "artifact_completeness": <0-10>,
    "defensive_fix_quality": <0-10>
  }},
  "reasoning": {{
    "attribution_accuracy": "<评分理由>",
    "contributing_completeness": "<评分理由>",
    "fix_correctness": "<评分理由>",
    "reasoning_depth": "<评分理由>",
    "artifact_completeness": "<评分理由>",
    "defensive_fix_quality": "<评分理由>"
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


# ─── LLM Judge ──────────────────────────────────────────────────

class LLMJudge:
    """
    LLM-as-Judge 评分核心
    """

    def __init__(self, model: str = "claude-opus-4-20250514",
                 rubric_path: str = "eval-framework/scoring-rubric-base.yaml",
                 api_key: Optional[str] = None):
        self.model = model
        self.rubric = self._load_rubric(rubric_path)
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.weights = self.rubric.get("weights", {
            "attribution_accuracy": 0.35,
            "contributing_completeness": 0.15,
            "fix_correctness": 0.20,
            "reasoning_depth": 0.10,
            "artifact_completeness": 0.10,
            "defensive_fix_quality": 0.10,
        })

    @staticmethod
    def _load_rubric(path: str) -> dict:
        if not os.path.exists(path):
            logger.warning(f"Rubric not found: {path}")
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def evaluate(self, case: CaseData,
                 chain_output: ChainOutput) -> EvalResult:
        """
        评估单条链路输出

        Args:
            case: Case 数据 (含 ground-truth)
            chain_output: 链路产物

        Returns:
            EvalResult
        """
        # 构建评估输入（盲评：不包含 chain 标识）
        analysis_text = self._collect_analysis_text(chain_output)

        # 构建 prompt
        prompt = JUDGE_EVAL_PROMPT.format(
            expected_root_cause=case.expected_root_cause,
            expected_contributing=case.expected_contributing,
            expected_fix_direction=case.expected_fix_direction,
            analysis_output=analysis_text,
            w_attribution=self.weights.get("attribution_accuracy", 0.35),
            w_contributing=self.weights.get("contributing_completeness", 0.15),
            w_fix=self.weights.get("fix_correctness", 0.20),
            w_reasoning=self.weights.get("reasoning_depth", 0.10),
            w_artifact=self.weights.get("artifact_completeness", 0.10),
            w_defensive=self.weights.get("defensive_fix_quality", 0.10),
        )

        # 调用 LLM
        raw_response = self._call_judge(prompt)

        # 解析结果
        result = self._parse_judge_response(raw_response)
        result.case_id = case.case_id
        result.chain = chain_output.chain

        # 计算加权综合分
        result.weighted_score = self._compute_weighted_score(result.scores)

        # 应用 Case 特定评分调整
        if case.scoring_rubric:
            result = self._apply_rubric_overrides(result, case.scoring_rubric)

        return result

    def batch_evaluate(self, items: list[tuple]) -> list[EvalResult]:
        """
        批量评估

        Args:
            items: (CaseData, ChainOutput) 元组列表

        Returns:
            EvalResult 列表
        """
        results = []
        for case, chain_output in items:
            try:
                result = self.evaluate(case, chain_output)
                results.append(result)
            except Exception as e:
                logger.error(f"Evaluation failed for {case.case_id}: {e}")
                results.append(EvalResult(
                    case_id=case.case_id,
                    chain=chain_output.chain,
                    metadata={"error": str(e)},
                ))
        return results

    def _collect_analysis_text(self, chain_output: ChainOutput) -> str:
        """收集链路产物为文本（盲评模式：不暴露 chain 标识）"""
        output_dir = chain_output.output_dir

        # 按优先级收集文件
        priority_files = [
            "rca-report.md",
            "fix-design.md",
            "spec.md",
            "issue-card.md",
            "impl-report.md",
            "verification-report.md",
            "deep-dive/deep-dive-summary.md",
            "deep-dive/functionality-deep-dive-rca.md",
            "deep-dive/defensive-fix-design.md",
            "baseline-output.md",  # Chain D
        ]

        parts = []
        for fname in priority_files:
            fpath = os.path.join(output_dir, fname)
            if os.path.exists(fpath):
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        content = f.read()
                    # 移除可能暴露 Chain 的信息
                    content = self._redact_chain_info(content)
                    parts.append(f"--- {fname} ---\n{content}\n")
                except Exception:
                    continue

        return "\n".join(parts) if parts else "[无产物]"

    @staticmethod
    def _redact_chain_info(text: str) -> str:
        """移除可能暴露 Chain 标识的信息"""
        import re
        text = re.sub(r"Chain\s*[ABCD]", "Chain [REDACTED]", text, flags=re.IGNORECASE)
        text = re.sub(r"chain_mode:\s*(standard|expert)", "chain_mode: [REDACTED]", text)
        return text

    def _call_judge(self, prompt: str) -> str:
        """调用 Judge LLM"""
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
            logger.warning("anthropic not installed, using placeholder scores")
            return self._placeholder_response()

    @staticmethod
    def _placeholder_response() -> str:
        """占位符评分（测试用）"""
        return json.dumps({
            "scores": {
                "attribution_accuracy": 5.0,
                "contributing_completeness": 5.0,
                "fix_correctness": 5.0,
                "reasoning_depth": 5.0,
                "artifact_completeness": 5.0,
                "defensive_fix_quality": 5.0,
            },
            "reasoning": {
                "attribution_accuracy": "[占位 - 需要真实 Judge LLM]",
                "contributing_completeness": "[占位]",
                "fix_correctness": "[占位]",
                "reasoning_depth": "[占位]",
                "artifact_completeness": "[占位]",
                "defensive_fix_quality": "[占位]",
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
        """解析 Judge LLM 输出"""
        result = EvalResult()

        # 提取 JSON 块
        import re
        json_match = re.search(r"```json\s*(.*?)\s*```", raw, re.DOTALL)
        if json_match:
            raw_json = json_match.group(1)
        else:
            raw_json = raw

        try:
            data = json.loads(raw_json)
            result.scores = data.get("scores", {})
            result.reasoning = data.get("reasoning", {})
            result.stage_scores = data.get("stage_scores", {})
            result.metadata["overall_comment"] = data.get("overall_comment", "")
        except json.JSONDecodeError:
            logger.warning("Failed to parse Judge JSON, attempting line-by-line")
            result.scores = self._fallback_parse(raw)

        return result

    @staticmethod
    def _fallback_parse(text: str) -> dict:
        """后备解析：从文本中提取分数"""
        import re
        scores = {}
        patterns = {
            "attribution_accuracy": r"attribution_accuracy[\"']?\s*:\s*(\d+(?:\.\d+)?)",
            "contributing_completeness": r"contributing_completeness[\"']?\s*:\s*(\d+(?:\.\d+)?)",
            "fix_correctness": r"fix_correctness[\"']?\s*:\s*(\d+(?:\.\d+)?)",
            "reasoning_depth": r"reasoning_depth[\"']?\s*:\s*(\d+(?:\.\d+)?)",
            "artifact_completeness": r"artifact_completeness[\"']?\s*:\s*(\d+(?:\.\d+)?)",
            "defensive_fix_quality": r"defensive_fix_quality[\"']?\s*:\s*(\d+(?:\.\d+)?)",
        }
        for key, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                scores[key] = float(match.group(1))
            else:
                scores[key] = 0.0
        return scores

    def _compute_weighted_score(self, scores: dict) -> float:
        """计算加权综合分"""
        total = 0.0
        for dim, weight in self.weights.items():
            total += scores.get(dim, 0.0) * weight
        return round(total, 3)

    @staticmethod
    def _apply_rubric_overrides(result: EvalResult,
                                rubric: dict) -> EvalResult:
        """应用 Case 特定的评分权重覆盖"""
        # 权重覆盖
        overrides = {
            "attribution_weight_override": "attribution_accuracy",
            "contributing_weight_override": "contributing_completeness",
            "fix_weight_override": "fix_correctness",
        }
        custom_weights = {}
        for override_key, dim_key in overrides.items():
            val = rubric.get(override_key)
            if val is not None:
                custom_weights[dim_key] = val

        if custom_weights:
            # 用自定义权重重算
            total = 0.0
            default_weights = {
                "attribution_accuracy": 0.35,
                "contributing_completeness": 0.15,
                "fix_correctness": 0.20,
                "reasoning_depth": 0.10,
                "artifact_completeness": 0.10,
                "defensive_fix_quality": 0.10,
            }
            weights = {**default_weights, **custom_weights}
            for dim, weight in weights.items():
                total += result.scores.get(dim, 0.0) * weight
            result.weighted_score = round(total, 3)

        return result

    @staticmethod
    def load_case_data(case_dir: str) -> CaseData:
        """从 Case 目录加载完整数据"""
        case_path = Path(case_dir)

        def read_file(path: Path) -> str:
            if path.exists():
                return path.read_text(encoding="utf-8")
            return ""

        metadata = {}
        meta_path = case_path / "metadata.yaml"
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                metadata = yaml.safe_load(f) or {}

        gt_dir = case_path / "ground-truth"
        rubric = {}
        rubric_path = gt_dir / "scoring-rubric.yaml"
        if rubric_path.exists():
            with open(rubric_path, "r", encoding="utf-8") as f:
                rubric = yaml.safe_load(f) or {}

        return CaseData(
            case_id=metadata.get("case_id", case_path.name),
            input_dir=str(case_path / "input"),
            ground_truth_dir=str(gt_dir),
            metadata=metadata,
            expected_root_cause=read_file(gt_dir / "expected-root-cause.md"),
            expected_contributing=read_file(gt_dir / "expected-contributing.md"),
            expected_fix_direction=read_file(gt_dir / "expected-fix-direction.md"),
            scoring_rubric=rubric,
        )

    @staticmethod
    def load_chain_output(output_dir: str, chain: str = "") -> ChainOutput:
        """加载链路输出产物"""
        return ChainOutput(output_dir=output_dir, chain=chain)


# ─── CLI Entry Point ────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Loupe Eval Judge")
    parser.add_argument("--results", required=True, help="Results directory")
    parser.add_argument("--rubric", default="eval-framework/scoring-rubric-base.yaml")
    parser.add_argument("--cases", default="eval-cases/")
    parser.add_argument("--model", default="claude-opus-4-20250514")
    parser.add_argument("--output", default=None, help="Output JSON path")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    judge = LLMJudge(model=args.model, rubric_path=args.rubric)

    results_path = Path(args.results)
    cases_path = Path(args.cases)

    all_results = []

    # 遍历结果目录
    for case_dir in sorted(results_path.iterdir()):
        if not case_dir.is_dir():
            continue
        case_id = case_dir.name

        # 查找对应 Case 数据
        matching_cases = list(cases_path.rglob(f"*{case_id}*"))
        case_data_dir = matching_cases[0] if matching_cases else None

        if not case_data_dir:
            logger.warning(f"No case data found for {case_id}")
            continue

        case_data = LLMJudge.load_case_data(str(case_data_dir))

        # 评估每个 Chain
        for chain_dir in sorted(case_dir.iterdir()):
            if not chain_dir.is_dir():
                continue
            chain = chain_dir.name.replace("chain-", "")
            chain_output = LLMJudge.load_chain_output(str(chain_dir), chain)
            result = judge.evaluate(case_data, chain_output)
            all_results.append(result)

    # 输出
    output_data = [{
        "case_id": r.case_id,
        "chain": r.chain,
        "weighted_score": r.weighted_score,
        "scores": r.scores,
        "reasoning": r.reasoning,
        "stage_scores": r.stage_scores,
    } for r in all_results]

    output_path = args.output or str(results_path / "judge-results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"Evaluation complete: {len(all_results)} results → {output_path}")


if __name__ == "__main__":
    main()
