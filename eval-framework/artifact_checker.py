"""
Loupe AI 自检自测系统 — Artifact Checker (产物完整性校验)
结合文件存在性 + 最小字数 + 关键段落存在性校验。
内容质量判定由 LLM-as-Judge 负责，此处仅做轻量存在性校验。

V1.2 增强: 新增 required_sections 关键段落存在性校验
V3.1 增强: 新增 conditional 条件必需产物校验 + Schema 兼容层
"""

import os
import re
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

import yaml

logger = logging.getLogger(__name__)


# ─── V3.1: 元信息解析函数（单一数据源） ────────────────────────

# 展示格式 → 程序化格式的唯一标准化映射
FIELD_MAPPING: Dict[str, str] = {
    'Repair-Route': 'repair_route',
    'Execution-Status': 'execution_status',
}


def parse_impl_report_metadata(content: str) -> Dict[str, Optional[str]]:
    """从 impl-report.md 元信息区提取标准化键值。

    解析 **Key**: value 格式的 Markdown 加粗标题行，
    并将展示格式键名标准化为 snake_case。

    Args:
        content: impl-report.md 的完整文本内容

    Returns:
        标准化后的键值字典，例如：
        {'repair_route': 'code-fix', 'execution_status': 'Success'}
    """
    metadata = {}
    # 匹配 **Key**: value 格式
    pattern = re.compile(r'\*\*(.+?)\*\*:\s*(.+)')
    for match in pattern.finditer(content):
        display_key = match.group(1).strip()
        value = match.group(2).strip()
        # 标准化映射
        normalized_key = FIELD_MAPPING.get(display_key)
        if normalized_key:
            metadata[normalized_key] = value
    return metadata


# ─── Data Models ────────────────────────────────────────────────

@dataclass
class CheckResult:
    """校验结果"""
    passed: bool = True
    missing_files: list = field(default_factory=list)
    below_threshold: list = field(default_factory=list)
    missing_sections: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    details: dict = field(default_factory=dict)


class ArtifactChecker:
    """
    产物完整性校验器
    根据 artifact-checklist.yaml 检查产物文件的：
    1. 存在性
    2. 最小字数
    3. 关键段落存在性 (V1.2 新增)
    4. 条件必需产物 (V3.1 新增)
    """

    def __init__(self, checklist_path: str):
        self.checklist = self._load_checklist(checklist_path)

    @staticmethod
    def _load_checklist(path: str) -> dict:
        if not os.path.exists(path):
            logger.warning(f"Checklist not found: {path}, using defaults")
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def check(self, output_dir: str, chain_mode: str = "standard") -> CheckResult:
        """
        执行完整校验流程

        Args:
            output_dir: 产物输出目录
            chain_mode: standard | expert

        Returns:
            CheckResult 包含校验详情
        """
        result = CheckResult()

        # V3.1: 预先解析 impl-report 元信息（供条件必需产物校验使用）
        metadata = self._load_impl_report_metadata(output_dir)

        # 1. 校验标准产物
        standard = self.checklist.get("standard_artifacts", {})
        required_items = standard.get("required", [])

        for item in required_items:
            required_type = item.get('required', True)  # 默认 True 保持兼容

            if required_type == 'conditional':
                # V3.1 新增：条件必需产物
                condition = item.get('condition', {})
                condition_field = condition.get('field')
                condition_value = condition.get('value')
                # 从 impl-report 元信息中读取实际值
                actual_value = metadata.get(condition_field)
                if actual_value == condition_value:
                    # 条件满足 → 视为 required
                    self._check_artifact(output_dir, item, result)
                else:
                    # 条件不满足 → 跳过不扣分
                    continue
            elif required_type is True or required_type == True:
                # 原逻辑：必需产物
                self._check_artifact(output_dir, item, result)
            else:
                # 原逻辑：可选产物
                self._check_artifact(output_dir, item, result,
                                    is_optional=True)

        # 2. 校验专家模式产物（仅 Chain B）
        if chain_mode == "expert":
            expert = self.checklist.get("expert_mode_artifacts", {})
            # 检查条件：workflow-status.yaml 中 specialized_workflow.status
            if self._check_expert_condition(output_dir, expert):
                expert_required = expert.get("required", [])
                for item in expert_required:
                    self._check_artifact(output_dir, item, result,
                                        prefix="deep-dive/")

                expert_optional = expert.get("optional", [])
                for item in expert_optional:
                    self._check_artifact(output_dir, item, result,
                                        prefix="deep-dive/",
                                        is_optional=True)

        # 综合判定
        policy = self.checklist.get("validation_policy", {})
        if result.missing_files:
            action = policy.get("missing_required", "RETRY")
            if action == "RETRY":
                result.passed = False
        if result.below_threshold:
            action = policy.get("size_below_threshold", "RETRY")
            if action == "RETRY":
                result.passed = False
        if result.missing_sections:
            action = policy.get("missing_required_sections", "RETRY")
            if action == "RETRY":
                result.passed = False

        return result

    @staticmethod
    def _load_impl_report_metadata(output_dir: str) -> Dict[str, Optional[str]]:
        """V3.1: 加载 impl-report.md 元信息"""
        impl_report_path = os.path.join(output_dir, 'impl-report.md')
        if os.path.exists(impl_report_path):
            try:
                with open(impl_report_path, 'r', encoding='utf-8') as f:
                    return parse_impl_report_metadata(f.read())
            except Exception as e:
                logger.warning(f"Failed to parse impl-report metadata: {e}")
        return {}

    def _check_artifact(self, output_dir: str, item: dict,
                        result: CheckResult,
                        prefix: str = "",
                        is_optional: bool = False):
        """检查单个产物文件"""
        # V3.1 Schema 兼容层：同时支持 path/file 和 min_size/min_size_bytes
        rel_path = item.get("path") or item.get("file", "")
        full_path = os.path.join(output_dir, prefix, rel_path)
        min_size = item.get("min_size") or item.get("min_size_bytes", 0)
        phase = item.get("phase", "unknown")
        sections = item.get("required_sections", [])

        # 1. 文件存在性
        if not os.path.exists(full_path):
            if is_optional:
                result.warnings.append(
                    f"Optional file missing: {rel_path} ({phase})"
                )
            else:
                result.missing_files.append({
                    "path": rel_path,
                    "phase": phase,
                })
                # V3.1: 记录 on_missing 动作
                on_missing = item.get("on_missing", "fail")
                if on_missing == "fail":
                    logger.warning(f"Missing required artifact: {full_path} (on_missing=fail)")
                else:
                    logger.warning(f"Missing required artifact: {full_path}")
            return

        # 2. 最小字数
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            result.missing_files.append({
                "path": rel_path,
                "phase": phase,
                "error": str(e),
            })
            return

        char_count = len(content.strip())
        if char_count < min_size:
            result.below_threshold.append({
                "path": rel_path,
                "phase": phase,
                "min_required": min_size,
                "actual_size": char_count,
            })
            logger.warning(
                f"Artifact below threshold: {rel_path} "
                f"({char_count} < {min_size})"
            )

        # 3. 关键段落存在性 (V1.2 新增)
        if sections:
            missing = self._check_required_sections(content, sections)
            if missing:
                result.missing_sections.append({
                    "path": rel_path,
                    "phase": phase,
                    "missing": missing,
                })

    def _check_required_sections(self, content: str,
                                  sections: list[dict]) -> list[str]:
        """
        轻量级段落存在性校验
        检查文件中是否包含指定的标题 (heading) 或关键字 (keyword)
        不判定内容质量，仅判定"是否存在"

        Args:
            content: 文件内容
            sections: 需要检查的段落列表

        Returns:
            缺失的段落描述列表
        """
        missing = []

        for section in sections:
            heading = section.get("heading", "")
            alternatives = section.get("alternatives", [])
            keyword = section.get("keyword", "")

            found = False

            # 检查标题（Markdown heading: # ## ### 等）
            all_headings = [heading] + alternatives
            for h in all_headings:
                if not h:
                    continue
                # 匹配 Markdown 标题格式
                pattern = rf"^#{1,6}\s+.*{re.escape(h)}.*$"
                if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                    found = True
                    break
                # 也匹配加粗文本作为标题
                pattern2 = rf"\*\*{re.escape(h)}\*\*"
                if re.search(pattern2, content, re.IGNORECASE):
                    found = True
                    break
                # 直接文本匹配（最宽松）
                if h.lower() in content.lower():
                    found = True
                    break

            # 检查关键字
            if not found and keyword:
                if keyword.lower() in content.lower():
                    found = True

            if not found:
                desc = heading or keyword
                missing.append(desc)

        return missing

    # TODO(tech-debt): 当前硬编码 workflow-status.yaml 路径和状态值判定，
    #   若未来新增其他专项模式需重构为通用条件表达式引擎
    def _check_expert_condition(self, output_dir: str,
                                expert_config: dict) -> bool:
        """检查专家模式产物的触发条件"""
        condition = expert_config.get("conditional_on", "")
        if not condition:
            return True

        # 检查 workflow-status.yaml
        status_path = os.path.join(output_dir, "workflow-status.yaml")
        if not os.path.exists(status_path):
            return False

        try:
            with open(status_path, "r", encoding="utf-8") as f:
                status = yaml.safe_load(f) or {}
            sw = status.get("specialized_workflow", {})
            sw_status = sw.get("status", "")
            return sw_status in ("DD-Completed", "Merged")
        except Exception:
            return False
