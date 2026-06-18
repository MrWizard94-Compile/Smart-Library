"""Self-healing sandbox for safe Python execution with LLM-driven error recovery."""

import io
import json
import os
import re
import sys
import traceback
from typing import Any, Dict, Optional

from langchain_openai import ChatOpenAI


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

    def safely_execute_python(self, code_string: str) -> Dict[str, Any]:
        """
        Execute Python code in-process while capturing stdout and exceptions.

        Returns:
            Dict with keys: success, stdout, error_traceback.
        """
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