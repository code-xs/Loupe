"""
Loupe AI 自检自测系统 — Session Manager (IDE 会话管理)
封装 IDE CLI/API 调用，提供统一的会话生命周期管理。
基于 IDEAdapter 抽象层，支持多种 IDE 实现（Trae/Cursor/Extension API）。
"""

import os
import time
import signal
import subprocess
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)


# ─── Data Models ────────────────────────────────────────────────

@dataclass
class SessionParams:
    """IDE 会话启动参数"""
    skill: str = "mobile-qa-workflow"
    input_file: str = ""
    workspace: str = ""
    auto_reply_config: str = ""
    chain_mode: str = "standard"     # standard | expert
    timeout: int = 1800              # 超时秒数
    output_dir: str = ""
    env_vars: dict = field(default_factory=dict)


@dataclass
class Session:
    """运行中的 IDE 会话"""
    session_id: str = ""
    pid: int = 0
    params: SessionParams = field(default_factory=SessionParams)
    start_time: float = 0.0
    status: str = "pending"          # pending | running | completed | failed | timeout
    process: Optional[subprocess.Popen] = field(default=None, repr=False)


@dataclass
class SessionResult:
    """会话执行结果"""
    session: Session = field(default_factory=Session)
    exit_code: int = -1
    artifacts: list = field(default_factory=list)
    stdout_log: str = ""
    stderr_log: str = ""


# ─── IDE Adapter 抽象层 ─────────────────────────────────────────

class IDEAdapter(ABC):
    """
    IDE 适配器抽象基类
    隔离 IDE 实现差异，支持 Trae/Cursor/Extension API
    """

    @abstractmethod
    def build_command(self, params: SessionParams) -> list[str]:
        """构建 IDE 启动命令"""
        ...

    @abstractmethod
    def parse_output(self, stdout: str, stderr: str,
                     output_dir: str) -> list[str]:
        """解析会话输出，返回产物文件列表"""
        ...

    def start(self, params: SessionParams) -> Session:
        """启动 IDE 会话"""
        cmd = self.build_command(params)
        session_id = f"session-{int(time.time())}-{os.getpid()}"

        logger.info(f"Starting IDE session {session_id}: {' '.join(cmd)}")

        env = os.environ.copy()
        env.update(params.env_vars)
        # 专家模式：设置环境变量强制触发 Deep-Dive
        if params.chain_mode == "expert":
            env["LOUPE_FORCE_DEEP_DIVE"] = "true"

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=params.workspace,
        )

        session = Session(
            session_id=session_id,
            pid=process.pid,
            params=params,
            start_time=time.time(),
            status="running",
            process=process,
        )
        return session

    def poll(self, session: Session) -> str:
        """检查会话状态"""
        if session.process is None:
            return "failed"
        ret = session.process.poll()
        if ret is None:
            # 检查超时
            elapsed = time.time() - session.start_time
            if elapsed > session.params.timeout:
                return "timeout"
            return "running"
        return "completed" if ret == 0 else "failed"

    def terminate(self, session: Session, graceful_timeout: int = 10):
        """终止会话：先 SIGTERM，超时后 SIGKILL"""
        if session.process is None:
            return
        try:
            session.process.send_signal(signal.SIGTERM)
            try:
                session.process.wait(timeout=graceful_timeout)
            except subprocess.TimeoutExpired:
                logger.warning(
                    f"Session {session.session_id} did not stop gracefully, "
                    f"sending SIGKILL"
                )
                session.process.kill()
                session.process.wait(timeout=5)
        except ProcessLookupError:
            pass  # 进程已退出


class TraeCLIAdapter(IDEAdapter):
    """Plan A: Trae CLI 无头调用"""

    def build_command(self, params: SessionParams) -> list[str]:
        cmd = [
            "trae",
            "--headless",
            "--skill", params.skill,
            "--input", params.input_file,
            "--output", params.output_dir,
            "--workspace", params.workspace,
        ]
        if params.auto_reply_config:
            cmd.extend(["--auto-reply", params.auto_reply_config])
        if params.chain_mode == "expert":
            cmd.extend(["--env", "LOUPE_FORCE_DEEP_DIVE=true"])
        return cmd

    def parse_output(self, stdout: str, stderr: str,
                     output_dir: str) -> list[str]:
        artifacts = []
        if os.path.isdir(output_dir):
            for root, _, files in os.walk(output_dir):
                for f in files:
                    if f.endswith(".md") or f.endswith(".yaml"):
                        artifacts.append(os.path.join(root, f))
        return sorted(artifacts)


class CursorCLIAdapter(IDEAdapter):
    """Plan A: Cursor CLI 无头调用"""

    def build_command(self, params: SessionParams) -> list[str]:
        cmd = [
            "cursor",
            "--headless",
            "--skill", params.skill,
            "--input", params.input_file,
            "--output", params.output_dir,
            "--workspace", params.workspace,
        ]
        if params.auto_reply_config:
            cmd.extend(["--auto-reply", params.auto_reply_config])
        return cmd

    def parse_output(self, stdout: str, stderr: str,
                     output_dir: str) -> list[str]:
        artifacts = []
        if os.path.isdir(output_dir):
            for root, _, files in os.walk(output_dir):
                for f in files:
                    if f.endswith(".md") or f.endswith(".yaml"):
                        artifacts.append(os.path.join(root, f))
        return sorted(artifacts)


class ExtensionAPIAdapter(IDEAdapter):
    """Plan B: 通过扩展 API 编程方式创建会话"""

    def __init__(self, extension_path: str = ""):
        self.extension_path = extension_path

    def build_command(self, params: SessionParams) -> list[str]:
        cmd = [
            "node", self.extension_path,
            "--skill", params.skill,
            "--input", params.input_file,
            "--output", params.output_dir,
            "--workspace", params.workspace,
        ]
        return cmd

    def parse_output(self, stdout: str, stderr: str,
                     output_dir: str) -> list[str]:
        artifacts = []
        if os.path.isdir(output_dir):
            for root, _, files in os.walk(output_dir):
                for f in files:
                    if f.endswith(".md") or f.endswith(".yaml"):
                        artifacts.append(os.path.join(root, f))
        return sorted(artifacts)


class DirectLLMAdapter(IDEAdapter):
    """
    Plan D: 直接调用 LLM API + Prompt 拼接
    绕过 IDE，将 SKILL.md 和所有 Phase Prompt 拼为 System Prompt
    """

    def __init__(self, skill_dir: str = "mobile-qa-workflow"):
        self.skill_dir = skill_dir

    def build_command(self, params: SessionParams) -> list[str]:
        # 此适配器不使用 subprocess，由 run_direct 处理
        return ["echo", "DirectLLMAdapter does not use subprocess"]

    def parse_output(self, stdout: str, stderr: str,
                     output_dir: str) -> list[str]:
        artifacts = []
        if os.path.isdir(output_dir):
            for root, _, files in os.walk(output_dir):
                for f in files:
                    if f.endswith(".md") or f.endswith(".yaml"):
                        artifacts.append(os.path.join(root, f))
        return sorted(artifacts)


# ─── Auto-Reply Engine ──────────────────────────────────────────

class AutoReplyEngine:
    """
    自动回复引擎 — 处理 <step-pause> 交互
    """

    def __init__(self, rules_path: str):
        self.rules = self._load_rules(rules_path)
        self.unrecognized_count = 0
        self.max_unrecognized = 3

    @staticmethod
    def _load_rules(path: str) -> dict:
        if not os.path.exists(path):
            return {"auto_reply_rules": [], "fallback": {}}
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def get_reply(self, pause_text: str) -> Optional[str]:
        """根据暂停文本匹配回复规则"""
        rules = self.rules.get("auto_reply_rules", [])

        for rule in rules:
            pattern = rule.get("trigger_pattern", "")
            context = rule.get("context_match", "")

            try:
                if re.search(pattern, pause_text):
                    if context and not re.search(context, pause_text):
                        continue
                    self.unrecognized_count = 0
                    return rule.get("reply", "[C] Continue")
            except re.error:
                continue

        # 无匹配
        self.unrecognized_count += 1
        fallback = self.rules.get("fallback", {})
        if self.unrecognized_count >= fallback.get("max_unrecognized_pauses", 3):
            return None  # 表示应强制终止

        return "[C] Continue"  # 默认继续


# ─── Session Manager ────────────────────────────────────────────

class IDESessionManager:
    """
    IDE 会话管理器 — 统一的会话生命周期管理
    """

    def __init__(self, adapter: IDEAdapter,
                 auto_reply_engine: Optional[AutoReplyEngine] = None):
        self.adapter = adapter
        self.auto_reply = auto_reply_engine
        self.active_sessions: dict[str, Session] = {}

    @classmethod
    def from_config(cls, config: dict) -> "IDESessionManager":
        """从配置创建 SessionManager"""
        ide_config = config.get("ide_config", {})
        adapter_type = ide_config.get("adapter", "trae")

        adapter: IDEAdapter
        if adapter_type == "trae":
            adapter = TraeCLIAdapter()
        elif adapter_type == "cursor":
            adapter = CursorCLIAdapter()
        elif adapter_type == "extension_api":
            adapter = ExtensionAPIAdapter(
                extension_path=ide_config.get("extension_path", "")
            )
        elif adapter_type == "direct_llm":
            adapter = DirectLLMAdapter(
                skill_dir=ide_config.get("skill_path", "mobile-qa-workflow")
            )
        else:
            raise ValueError(f"Unknown IDE adapter: {adapter_type}")

        auto_reply_config = ide_config.get("auto_reply_config", "")
        auto_reply = (
            AutoReplyEngine(auto_reply_config)
            if auto_reply_config and os.path.exists(auto_reply_config)
            else None
        )

        return cls(adapter=adapter, auto_reply_engine=auto_reply)

    def start_session(self, params: SessionParams) -> Session:
        """启动会话"""
        session = self.adapter.start(params)
        self.active_sessions[session.session_id] = session
        return session

    def wait_for_completion(self, session: Session) -> SessionResult:
        """等待会话完成"""
        graceful_timeout = 10

        while True:
            status = self.adapter.poll(session)

            if status == "timeout":
                logger.warning(f"Session {session.session_id} timed out")
                self.adapter.terminate(session, graceful_timeout)
                session.status = "timeout"
                break
            elif status in ("completed", "failed"):
                session.status = status
                break

            time.sleep(2)

        # 收集输出
        stdout = ""
        stderr = ""
        exit_code = -1

        if session.process is not None:
            try:
                stdout_bytes, stderr_bytes = session.process.communicate(timeout=15)
                stdout = stdout_bytes.decode("utf-8", errors="replace")
                stderr = stderr_bytes.decode("utf-8", errors="replace")
                exit_code = session.process.returncode or 0
            except subprocess.TimeoutExpired:
                session.process.kill()
                # 回收子进程资源，防止僵尸进程
                try:
                    out, err = session.process.communicate(timeout=5)
                    stdout = out.decode("utf-8", errors="replace") if out else ""
                    stderr = err.decode("utf-8", errors="replace") if err else ""
                except Exception:
                    pass
                exit_code = -1

        # 保存会话日志
        self._save_session_log(session, stdout, stderr)

        # 收集产物
        artifacts = self.adapter.parse_output(
            stdout, stderr, session.params.output_dir
        )

        # 清理
        self.active_sessions.pop(session.session_id, None)

        return SessionResult(
            session=session,
            exit_code=exit_code,
            artifacts=artifacts,
            stdout_log=stdout,
            stderr_log=stderr,
        )

    def run_session(self, params: SessionParams) -> SessionResult:
        """启动并等待会话完成（便捷方法）"""
        session = self.start_session(params)
        return self.wait_for_completion(session)

    def force_terminate(self, session: Session):
        """强制终止会话"""
        self.adapter.terminate(session, graceful_timeout=0)
        session.status = "failed"
        self.active_sessions.pop(session.session_id, None)

    def collect_artifacts(self, session: Session) -> list[str]:
        """收集会话产物"""
        return self.adapter.parse_output("", "", session.params.output_dir)

    def check_health(self, session: Session) -> bool:
        """检查会话健康状态"""
        status = self.adapter.poll(session)
        return status == "running"

    def _save_session_log(self, session: Session,
                          stdout: str, stderr: str):
        """保存会话日志到输出目录"""
        log_dir = session.params.output_dir
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, "session.log")
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(f"=== Session: {session.session_id} ===\n")
                f.write(f"Status: {session.status}\n")
                f.write(f"PID: {session.pid}\n")
                f.write(f"Duration: {time.time() - session.start_time:.1f}s\n")
                f.write(f"\n=== STDOUT ===\n{stdout}\n")
                f.write(f"\n=== STDERR ===\n{stderr}\n")

    def get_active_count(self) -> int:
        """获取活跃会话数"""
        return len(self.active_sessions)

    def terminate_all(self):
        """终止所有活跃会话"""
        for session in list(self.active_sessions.values()):
            self.force_terminate(session)
