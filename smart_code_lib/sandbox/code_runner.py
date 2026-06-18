"""Self-healing sandbox for safe Python execution with LLM-driven error recovery.

Docker-isolated execution is the default sandbox (``USE_DOCKER_SANDBOX=true``).
Requires the Docker CLI on the host or in the API container when using
``docker-compose`` with the Docker socket mounted.
"""

import io
import json
import os
import re
import shutil
import subprocess
import sys
import traceback
from typing import Any, Dict, Optional

from langchain_openai import ChatOpenAI

DOCKER_IMAGE = "python:3.11-slim"
DOCKER_UNAVAILABLE_MSG = (
    "Docker sandbox is unavailable. Install/start Docker, ensure the Docker CLI "
    "is on PATH, or set USE_DOCKER_SANDBOX=false to use in-process execution."
)


def _strip_markdown_fences(text: str) -> str:
    """
    Remove markdown code fences and surrounding backticks from LLM output.

    Handles patterns like ```json ... ```, ``` ... ```, and stray backticks.
    """
    cleaned = text.strip()

    fence_match = re.match(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", cleaned, re.DOTALL | re.IGNORECASE)
    if fence_match:
        return fence_match.group(1).strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if len(lines) >= 2:
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            return "\n".join(lines).strip()

    return cleaned.strip("`").strip()


def _parse_llm_json(content: str) -> Optional[Dict[str, Any]]:
    """
    Parse JSON from LLM response text, tolerating markdown wrapping.

    Returns:
        Parsed dict on success, or None if parsing fails.
    """
    try:
        return json.loads(_strip_markdown_fences(content))
    except (json.JSONDecodeError, TypeError):
        return None


def _is_docker_cli_available() -> bool:
    """Return True when the ``docker`` executable is on PATH."""
    return shutil.which("docker") is not None


def _is_docker_daemon_available() -> bool:
    """Return True when the Docker daemon responds to ``docker info``."""
    if not _is_docker_cli_available():
        return False
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


class SelfHealingSandbox:
    """Executes Python code safely and attempts LLM-based self-healing on failure."""

    def __init__(self, vector_db):
        """
        Initialize the sandbox with a vector store for persisting healing patches.

        Args:
            vector_db: VectorMemoryStore instance used to record successful fixes.
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required but not set."
            )

        self.llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=api_key)
        self.db = vector_db

    def execute_in_docker(self, code_string: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Execute Python code in an ephemeral, resource-limited Docker container.

        Uses ``python:3.11-slim`` with no network, read-only root filesystem,
        and code supplied via stdin. Requires the Docker CLI (subprocess only;
        no Python Docker SDK).

        Args:
            code_string: Python source to execute.
            timeout: Maximum seconds to wait for container completion.

        Returns:
            Dict with keys: success, stdout, error_traceback.
        """
        if not _is_docker_cli_available():
            return {
                "success": False,
                "stdout": "",
                "error_traceback": DOCKER_UNAVAILABLE_MSG,
            }

        if not _is_docker_daemon_available():
            return {
                "success": False,
                "stdout": "",
                "error_traceback": DOCKER_UNAVAILABLE_MSG,
            }

        docker_cmd = [
            "docker",
            "run",
            "--rm",
            "-i",
            "--network",
            "none",
            "--memory",
            "128m",
            "--cpus",
            "0.5",
            "--read-only",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=64m",
            "--security-opt",
            "no-new-privileges",
            "--cap-drop",
            "ALL",
            "--user",
            "65534:65534",
            DOCKER_IMAGE,
            "python",
            "-",
        ]

        try:
            completed = subprocess.run(
                docker_cmd,
                input=code_string,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "error_traceback": f"Execution timed out after {timeout} seconds.",
            }
        except (FileNotFoundError, OSError) as exc:
            return {
                "success": False,
                "stdout": "",
                "error_traceback": f"{DOCKER_UNAVAILABLE_MSG} ({exc})",
            }

        stdout = completed.stdout or ""
        stderr = completed.stderr or ""

        if completed.returncode == 0:
            return {
                "success": True,
                "stdout": stdout,
                "error_traceback": None,
            }

        error_traceback = stderr.strip() or stdout.strip() or (
            f"Container exited with code {completed.returncode}."
        )
        return {
            "success": False,
            "stdout": stdout,
            "error_traceback": error_traceback,
        }

    def _execute_in_process(self, code_string: str) -> Dict[str, Any]:
        """Execute Python code in-process while capturing stdout and exceptions."""
        output_buffer = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = output_buffer

        exec_globals: Dict[str, Any] = {}
        error = None

        try:
            exec(code_string, exec_globals)
        except Exception:
            error = traceback.format_exc()
        finally:
            sys.stdout = old_stdout

        return {
            "success": error is None,
            "stdout": output_buffer.getvalue(),
            "error_traceback": error,
        }

    def _should_use_docker_sandbox(self) -> bool:
        """Return True unless USE_DOCKER_SANDBOX is explicitly set to false."""
        return os.getenv("USE_DOCKER_SANDBOX", "true").lower() != "false"

    def _docker_sandbox_unavailable(self, result: Dict[str, Any]) -> bool:
        """Detect execute_in_docker results that indicate Docker cannot be used."""
        error = result.get("error_traceback") or ""
        return not result["success"] and error.startswith("Docker sandbox is unavailable")

    def safely_execute_python(
        self, code_string: str, timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute Python code with Docker isolation by default.

        When ``USE_DOCKER_SANDBOX`` is not ``false``, runs code in a Docker
        container via :meth:`execute_in_docker`. Falls back to in-process
        ``exec()`` only when Docker is unavailable or ``USE_DOCKER_SANDBOX=false``.

        Returns:
            Dict with keys: success, stdout, error_traceback.
        """
        if self._should_use_docker_sandbox():
            docker_result = self.execute_in_docker(code_string, timeout=timeout)
            if self._docker_sandbox_unavailable(docker_result):
                return self._execute_in_process(code_string)
            return docker_result

        return self._execute_in_process(code_string)

    def heal_and_verify(self, broken_code: str, max_attempts: int = 3) -> Dict[str, Any]:
        """
        Run code and iteratively request LLM fixes until success or max attempts.

        Args:
            broken_code: Python source to execute and heal.
            max_attempts: Maximum heal iterations before giving up.

        Returns:
            Status report with healed code, attempt count, or failure details.
        """
        current_code = broken_code
        result: Dict[str, Any] = {
            "success": False,
            "stdout": "",
            "error_traceback": None,
        }

        for attempt in range(max_attempts):
            result = self.safely_execute_python(current_code)
            if result["success"]:
                return {
                    "status": "Healed",
                    "code": current_code,
                    "attempts": attempt + 1,
                    "stdout": result["stdout"],
                }

            prompt = f"""
            Fix this code. Return a valid JSON dictionary string containing keys: 'fixed_code' and 'explanation'.

            Code to fix:
            {current_code}

            Error Details:
            {result['error_traceback']}
            """

            llm_output = self.llm.invoke(prompt).content
            parsed_fix = _parse_llm_json(llm_output)

            if not parsed_fix or "fixed_code" not in parsed_fix:
                return {
                    "status": "Failed",
                    "code": current_code,
                    "error": result["error_traceback"],
                    "attempts": attempt + 1,
                    "parse_error": "LLM response was not valid JSON with 'fixed_code'.",
                }

            current_code = parsed_fix["fixed_code"]

            self.db.insert_reference(
                content=(
                    f"Fixed error: {result['error_traceback']}. "
                    f"Fix: {parsed_fix.get('explanation', 'No explanation provided.')}"
                ),
                category="Self-Healing Patch",
            )

        return {
            "status": "Failed",
            "code": current_code,
            "error": result.get("error_traceback"),
            "attempts": max_attempts,
        }