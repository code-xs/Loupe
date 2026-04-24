"""
Loupe AI 自检自测系统 — Baseline Runner (Chain D 裸跑执行器)
读取 Case 输入，拼为单条 Prompt，不使用任何工作流编排，
使用与 Loupe 相同的底座模型确保对比公平性。
"""

import os
import json
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# Prompt 模板
BASELINE_PROMPT_TEMPLATE = """你是一位高级移动端工程师，拥有 10 年以上的 Android/iOS 开发经验。
请分析以下移动端问题，一次性给出完整的分析结果。

## 分析要求
请严格按照以下结构输出分析结果：

### 1. 主要根因（Primary Root Cause）
- 根因分类: [代码缺陷/竞态条件/资源泄漏/配置错误/API误用/设计缺陷/第三方缺陷/环境因素]
- 根因描述: [详细描述因果机制]
- 代码位置: [如果能定位，给出 file:line]
- 置信度: [High/Medium/Low，附理由]

### 2. 贡献因子（Contributing Factors）
- [因子1]: [描述及关联性]
- [因子2]: [描述及关联性]
- ...

### 3. 完整因果链
[触发条件] → [中间状态变化] → ... → [最终异常表现]

### 4. 推荐修复方案（Fix Recommendation）
- 修复策略: [策略名称]
- 修复方案: [具体修改内容]
- 修复理由: [为什么这个方案能解决问题]
- 变更范围: [涉及的文件/模块]

### 5. 防御性建议
- [建议1]: [描述]
- [建议2]: [描述]

---

## 问题描述
{issue_description}

## 相关日志
{logs}

## 代码片段
{code_snapshot}
"""


@dataclass
class BaselineOutput:
    """裸跑输出"""
    case_id: str = ""
    raw_response: str = ""
    primary_root_cause: str = ""
    contributing_factors: list = field(default_factory=list)
    fix_recommendation: str = ""
    model: str = ""
    tokens_used: int = 0
    duration_seconds: float = 0.0


class BaselineRunner:
    """
    Chain D 裸跑执行器
    直接调用 LLM API，不使用任何工作流编排
    """

    def __init__(self, model: str = "claude-sonnet-4-20250514",
                 temperature: float = 0.1,
                 api_key: Optional[str] = None):
        self.model = model
        self.temperature = temperature
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")

    def run(self, issue_description: str, logs: str = "",
            code_snapshot: str = "", case_id: str = "") -> BaselineOutput:
        """
        执行单次 LLM 裸跑分析

        Args:
            issue_description: 问题描述文本
            logs: 相关日志
            code_snapshot: 代码片段
            case_id: Case 标识

        Returns:
            BaselineOutput
        """
        prompt = BASELINE_PROMPT_TEMPLATE.format(
            issue_description=issue_description,
            logs=logs if logs else "[无日志提供]",
            code_snapshot=code_snapshot if code_snapshot else "[无代码片段提供]",
        )

        try:
            response = self._call_llm(prompt)
            output = BaselineOutput(
                case_id=case_id,
                raw_response=response,
                model=self.model,
            )
            # 尝试解析结构化输出
            self._parse_response(response, output)
            return output

        except Exception as e:
            logger.error(f"Baseline run failed for {case_id}: {e}")
            return BaselineOutput(
                case_id=case_id,
                raw_response=f"ERROR: {str(e)}",
                model=self.model,
            )

    def run_from_files(self, issue_desc_path: str,
                       logs_dir: str = "",
                       code_dir: str = "",
                       output_dir: str = "") -> Optional[BaselineOutput]:
        """
        从文件读取输入并执行裸跑

        Args:
            issue_desc_path: issue-description.md 路径
            logs_dir: logs/ 目录路径
            code_dir: code-snapshot/ 目录路径
            output_dir: 输出目录

        Returns:
            BaselineOutput or None
        """
        # 读取 issue description
        issue_description = self._read_file(issue_desc_path)
        if not issue_description:
            logger.error(f"Issue description not found: {issue_desc_path}")
            return None

        # 读取日志
        logs = self._read_directory(logs_dir) if logs_dir else ""

        # 读取代码片段
        code_snapshot = self._read_directory(code_dir) if code_dir else ""

        # 从路径推断 case_id
        case_id = Path(issue_desc_path).parent.parent.name

        # 执行
        output = self.run(issue_description, logs, code_snapshot, case_id)

        # 保存结果
        if output_dir:
            self._save_output(output, output_dir)

        return output

    def batch_run(self, cases: list[dict]) -> list[BaselineOutput]:
        """
        批量执行裸跑

        Args:
            cases: Case 列表，每个包含 issue_description, logs, code_snapshot, case_id

        Returns:
            BaselineOutput 列表
        """
        results = []
        for case in cases:
            output = self.run(
                issue_description=case.get("issue_description", ""),
                logs=case.get("logs", ""),
                code_snapshot=case.get("code_snapshot", ""),
                case_id=case.get("case_id", ""),
            )
            results.append(output)
        return results

    def _call_llm(self, prompt: str) -> str:
        """
        调用 LLM API
        支持 Anthropic Claude API
        """
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self.api_key)
            message = client.messages.create(
                model=self.model,
                max_tokens=8192,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text

        except ImportError:
            # Fallback: 模拟输出（用于无 API 环境的测试）
            logger.warning(
                "anthropic package not installed, "
                "generating placeholder output"
            )
            return self._generate_placeholder(prompt)

    def _generate_placeholder(self, prompt: str) -> str:
        """生成 fallback 输出（用于无 API 环境的测试）。"""
        return """### 1. 主要根因（Primary Root Cause）
- 根因分类: [fallback]
- 根因描述: [fallback output: configure ANTHROPIC_API_KEY for live analysis]
- 代码位置: [未知]
- 置信度: Low

### 2. 贡献因子（Contributing Factors）
- [fallback]: [configure ANTHROPIC_API_KEY for live analysis]

### 3. 完整因果链
[fallback] → [fallback] → [fallback]

### 4. 推荐修复方案（Fix Recommendation）
- 修复策略: [fallback]
- 修复方案: [fallback output: configure ANTHROPIC_API_KEY for live analysis]
- 修复理由: [fallback]
- 变更范围: [fallback]

### 5. 防御性建议
- [fallback]

> Note: fallback output (no live LLM call). Configure ANTHROPIC_API_KEY for real results.
"""

    @staticmethod
    def _parse_response(response: str, output: BaselineOutput):
        """解析 LLM 响应，提取结构化字段"""
        lines = response.split("\n")

        current_section = ""
        for line in lines:
            stripped = line.strip()

            if "主要根因" in stripped or "Primary Root Cause" in stripped:
                current_section = "root_cause"
            elif "贡献因子" in stripped or "Contributing Factors" in stripped:
                current_section = "contributing"
            elif "修复方案" in stripped or "Fix Recommendation" in stripped:
                current_section = "fix"

            if current_section == "root_cause" and "根因描述" in stripped:
                output.primary_root_cause = stripped.split(":", 1)[-1].strip()
            elif current_section == "contributing" and stripped.startswith("-"):
                factor = stripped.lstrip("- ").strip()
                if factor and "[" not in factor[:3]:
                    output.contributing_factors.append(factor)
            elif current_section == "fix" and "修复方案" in stripped:
                output.fix_recommendation = stripped.split(":", 1)[-1].strip()

    @staticmethod
    def _read_file(path: str) -> str:
        """安全读取文件"""
        if not path or not os.path.exists(path):
            return ""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Failed to read {path}: {e}")
            return ""

    @staticmethod
    def _read_directory(dir_path: str, max_files: int = 10,
                        max_chars: int = 50000) -> str:
        """读取目录下所有文本文件，拼接返回"""
        if not dir_path or not os.path.isdir(dir_path):
            return ""

        parts = []
        total_chars = 0

        for fname in sorted(os.listdir(dir_path))[:max_files]:
            fpath = os.path.join(dir_path, fname)
            if not os.path.isfile(fpath):
                continue
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                if total_chars + len(content) > max_chars:
                    content = content[:max_chars - total_chars]
                    parts.append(f"\n--- {fname} (truncated) ---\n{content}")
                    break
                parts.append(f"\n--- {fname} ---\n{content}")
                total_chars += len(content)
            except Exception:
                continue

        return "\n".join(parts)

    def _save_output(self, output: BaselineOutput, output_dir: str):
        """保存裸跑结果到文件"""
        os.makedirs(output_dir, exist_ok=True)

        # 保存 Markdown 格式
        md_path = os.path.join(output_dir, "baseline-output.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# Baseline Analysis — {output.case_id}\n\n")
            f.write(f"**Model**: {output.model}\n\n")
            f.write(f"---\n\n")
            f.write(output.raw_response)

        # 保存 JSON 格式
        json_path = os.path.join(output_dir, "baseline-output.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({
                "case_id": output.case_id,
                "model": output.model,
                "primary_root_cause": output.primary_root_cause,
                "contributing_factors": output.contributing_factors,
                "fix_recommendation": output.fix_recommendation,
                "tokens_used": output.tokens_used,
                "duration_seconds": output.duration_seconds,
            }, f, indent=2, ensure_ascii=False)
