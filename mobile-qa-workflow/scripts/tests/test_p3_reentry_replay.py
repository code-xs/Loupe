#!/usr/bin/env python3
"""test_p3_reentry_replay.py — P3 重入 fanout_mode 反查算法等价回放

不调用 LLM，仅用 python 实现 READ-N1 在 p3-root-cause.md step 4 的反查算法的等价副本，
对 fixture 跑一次，断言能从 phase_history 末项 qa-root-cause 元素还原 fanout_mode。
等价性约束：本脚本算法与 p3-root-cause.md step 4 的描述保持一致；若调整描述或字段名，
需同步更新本脚本与 fixtures。
"""
import unittest
from pathlib import Path

try:
    from ruamel.yaml import YAML
    _USE_RUAMEL = True
except ImportError:
    import yaml as _pyyaml
    _USE_RUAMEL = False


FIXTURE_DIR = Path(__file__).parent / "fixtures"
FIXTURE = FIXTURE_DIR / "p3-reentry-null-fanout-with-phase-history.yaml"
FIXTURE_EMPTY_HISTORY = FIXTURE_DIR / "p3-reentry-null-fanout-without-phase-history.yaml"
FIXTURE_ALREADY_SET = FIXTURE_DIR / "p3-reentry-fanout-already-set.yaml"


def _load_yaml(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if _USE_RUAMEL:
        return YAML(typ="safe").load(text)
    return _pyyaml.safe_load(text)


def reentry_restore_fanout_mode(status: dict) -> dict:
    """READ-N1 算法等价副本：fanout_mode == null 且 phase_history 非空时反查末项 qa-root-cause。"""
    if status.get("fanout_mode") is not None:
        return status
    history = status.get("phase_history") or []
    for item in reversed(history):
        if (
            isinstance(item, dict)
            and item.get("phase") == "qa-root-cause"
            and item.get("fanout_mode")
        ):
            status["fanout_mode"] = item["fanout_mode"]
            break
    return status


class TestP3ReentryReplay(unittest.TestCase):
    def test_restore_from_phase_history_last_item(self):
        status = _load_yaml(FIXTURE)
        self.assertIsNone(
            status["fanout_mode"], "前置条件：fixture 应满足 fanout_mode == null"
        )
        restored = reentry_restore_fanout_mode(status)
        self.assertEqual(
            restored["fanout_mode"],
            "medium-challenge",
            msg="READ-N1 应从 phase_history 末项 qa-root-cause 还原 fanout_mode",
        )

    def test_skip_when_fanout_mode_already_set(self):
        status = {
            "fanout_mode": "simple-single",
            "phase_history": [
                {"phase": "qa-root-cause", "fanout_mode": "medium-challenge"}
            ],
        }
        restored = reentry_restore_fanout_mode(status)
        self.assertEqual(
            restored["fanout_mode"],
            "simple-single",
            msg="新会话主路径 fanout_mode 已写时不应被反查覆盖",
        )

    def test_no_qa_root_cause_in_history_keeps_null(self):
        status = {
            "fanout_mode": None,
            "phase_history": [{"phase": "qa-spec-defining", "fanout_mode": None}],
        }
        restored = reentry_restore_fanout_mode(status)
        self.assertIsNone(
            restored["fanout_mode"],
            msg="phase_history 不含 qa-root-cause 时应保持 null，由 spec 推断路径接管",
        )

    def test_fixture_empty_history_keeps_null(self):
        status = _load_yaml(FIXTURE_EMPTY_HISTORY)
        restored = reentry_restore_fanout_mode(status)
        self.assertIsNone(
            restored["fanout_mode"],
            msg="phase_history == [] 时反查应跳过，保持 null",
        )

    def test_fixture_idempotent_when_already_set(self):
        status = _load_yaml(FIXTURE_ALREADY_SET)
        restored = reentry_restore_fanout_mode(status)
        self.assertEqual(
            restored["fanout_mode"],
            "high-fanout",
            msg="幂等：fanout_mode 已有值时不应被 phase_history 末项覆盖",
        )


if __name__ == "__main__":
    unittest.main()
