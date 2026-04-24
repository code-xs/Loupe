"""
Unit tests for LLMJudge._fallback_parse()
Covers: new dimension extraction, mixed old/new output, boundary values, missing dimensions.
验证 9 维度正则解析的正确性。
"""

import re
import unittest


def _fallback_parse(text: str) -> dict:
    """Copy of LLMJudge._fallback_parse for isolated testing (avoids Python 3.7 import issues)"""
    scores = {}
    patterns = {
        "attribution_accuracy": r"attribution_accuracy[\"']?\s*:\s*(\d+(?:\.\d+)?)",
        "contributing_completeness": r"contributing_completeness[\"']?\s*:\s*(\d+(?:\.\d+)?)",
        "fix_correctness": r"fix_correctness[\"']?\s*:\s*(\d+(?:\.\d+)?)",
        "reasoning_depth": r"reasoning_depth[\"']?\s*:\s*(\d+(?:\.\d+)?)",
        "artifact_completeness": r"artifact_completeness[\"']?\s*:\s*(\d+(?:\.\d+)?)",
        "defensive_fix_quality": r"defensive_fix_quality[\"']?\s*:\s*(\d+(?:\.\d+)?)",
        "contract_first_pass_accuracy": r"contract_first_pass_accuracy[\"']?\s*:\s*(\d+(?:\.\d+)?)",
        "hallucination_interception": r"hallucination_interception[\"']?\s*:\s*(\d+(?:\.\d+)?)",
        "self_healing_rate": r"self_healing_rate[\"']?\s*:\s*(\d+(?:\.\d+)?)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            scores[key] = float(match.group(1))
        else:
            scores[key] = 0.0
    return scores


class TestFallbackParse(unittest.TestCase):
    """_fallback_parse 正则解析单元测试"""

    def test_all_nine_dimensions_normal(self):
        """正常提取全部 9 维度分数"""
        text = """
        "attribution_accuracy": 8.5,
        "contributing_completeness": 7.0,
        "fix_correctness": 9.0,
        "reasoning_depth": 6.5,
        "artifact_completeness": 8.0,
        "defensive_fix_quality": 7.5,
        "contract_first_pass_accuracy": 9.0,
        "hallucination_interception": 8.0,
        "self_healing_rate": 7.0
        """
        scores = _fallback_parse(text)
        self.assertEqual(scores["attribution_accuracy"], 8.5)
        self.assertEqual(scores["contributing_completeness"], 7.0)
        self.assertEqual(scores["fix_correctness"], 9.0)
        self.assertEqual(scores["reasoning_depth"], 6.5)
        self.assertEqual(scores["artifact_completeness"], 8.0)
        self.assertEqual(scores["defensive_fix_quality"], 7.5)
        self.assertEqual(scores["contract_first_pass_accuracy"], 9.0)
        self.assertEqual(scores["hallucination_interception"], 8.0)
        self.assertEqual(scores["self_healing_rate"], 7.0)

    def test_new_dimensions_only(self):
        """仅包含新维度分数时能正确提取"""
        text = """
        contract_first_pass_accuracy: 10,
        hallucination_interception: 4,
        self_healing_rate: 0
        """
        scores = _fallback_parse(text)
        self.assertEqual(scores["contract_first_pass_accuracy"], 10.0)
        self.assertEqual(scores["hallucination_interception"], 4.0)
        self.assertEqual(scores["self_healing_rate"], 0.0)

    def test_mixed_old_new_dimensions(self):
        """新旧维度混合输出的正确解析"""
        text = """
        attribution_accuracy: 8,
        fix_correctness: 7,
        contract_first_pass_accuracy: 9,
        self_healing_rate: 6
        """
        scores = _fallback_parse(text)
        self.assertEqual(scores["attribution_accuracy"], 8.0)
        self.assertEqual(scores["fix_correctness"], 7.0)
        self.assertEqual(scores["contract_first_pass_accuracy"], 9.0)
        self.assertEqual(scores["self_healing_rate"], 6.0)
        # 缺失的维度应为 0.0
        self.assertEqual(scores["contributing_completeness"], 0.0)
        self.assertEqual(scores["hallucination_interception"], 0.0)

    def test_boundary_value_zero(self):
        """边界值: 0 分"""
        text = '"contract_first_pass_accuracy": 0'
        scores = _fallback_parse(text)
        self.assertEqual(scores["contract_first_pass_accuracy"], 0.0)

    def test_boundary_value_ten(self):
        """边界值: 10 分"""
        text = '"self_healing_rate": 10'
        scores = _fallback_parse(text)
        self.assertEqual(scores["self_healing_rate"], 10.0)

    def test_boundary_value_decimal(self):
        """边界值: 小数分数"""
        text = '"hallucination_interception": 7.5'
        scores = _fallback_parse(text)
        self.assertEqual(scores["hallucination_interception"], 7.5)

    def test_missing_all_dimensions(self):
        """所有维度缺失时应返回 0.0"""
        text = "This text contains no scores at all."
        scores = _fallback_parse(text)
        self.assertEqual(len(scores), 9)
        for dim, score in scores.items():
            self.assertEqual(score, 0.0, "{} should be 0.0 when missing".format(dim))

    def test_missing_new_dimensions_only(self):
        """仅缺失新维度时，旧维度正常提取，新维度为 0.0"""
        text = """
        "attribution_accuracy": 8,
        "contributing_completeness": 7,
        "fix_correctness": 9,
        "reasoning_depth": 6,
        "artifact_completeness": 8,
        "defensive_fix_quality": 7
        """
        scores = _fallback_parse(text)
        self.assertEqual(scores["attribution_accuracy"], 8.0)
        self.assertEqual(scores["contract_first_pass_accuracy"], 0.0)
        self.assertEqual(scores["hallucination_interception"], 0.0)
        self.assertEqual(scores["self_healing_rate"], 0.0)

    def test_json_with_quotes(self):
        """带引号的 JSON 格式字符串"""
        text = '''
        {
            "scores": {
                "attribution_accuracy": 8,
                "contributing_completeness": 7,
                "fix_correctness": 9,
                "reasoning_depth": 6,
                "artifact_completeness": 8,
                "defensive_fix_quality": 7,
                "contract_first_pass_accuracy": 9,
                "hallucination_interception": 8,
                "self_healing_rate": 7
            }
        }
        '''
        scores = _fallback_parse(text)
        self.assertEqual(scores["contract_first_pass_accuracy"], 9.0)
        self.assertEqual(scores["hallucination_interception"], 8.0)
        self.assertEqual(scores["self_healing_rate"], 7.0)

    def test_returns_exactly_nine_keys(self):
        """返回结果必须恰好包含 9 个维度"""
        text = ""
        scores = _fallback_parse(text)
        self.assertEqual(len(scores), 9)
        expected_keys = {
            "attribution_accuracy",
            "contributing_completeness",
            "fix_correctness",
            "reasoning_depth",
            "artifact_completeness",
            "defensive_fix_quality",
            "contract_first_pass_accuracy",
            "hallucination_interception",
            "self_healing_rate",
        }
        self.assertEqual(set(scores.keys()), expected_keys)


if __name__ == "__main__":
    unittest.main()
