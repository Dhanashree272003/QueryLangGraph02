"""
Parse Guardrail Module for Query LangGraph (querylanggraph02).

This module serves as the primary security gateway for incoming user queries.
It inspects queries for prompt injection, jailbreak attempts, and unsafe commands
prior to passing them to the Parse Query Node.
"""

import re
import logging
from typing import Dict, Any, Tuple

# Set up logger
logger = logging.getLogger("QueryLangGraph.Guardrails.ParseGuard")


class ParseGuardrail:
    """
    Security guardrail executed before the Parse Query Node.
    
    Responsibilities:
    - Detect prompt injection patterns (e.g., instructions override attempts)
    - Detect jailbreak attempts (e.g., persona hijacking, DAN prompts)
    - Detect unsafe queries (e.g., system command execution, drop/delete attempts)
    """

    # Common prompt injection patterns
    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|above|prior)\s+instructions",
        r"disregard\s+(all\s+)?(previous|above|prior)\s+instructions",
        r"forget\s+(all\s+)?(previous|above|prior)\s+instructions",
        r"system\s*:\s*",
        r"you\s+are\s+now\s+a",
        r"override\s+system\s+prompt",
        r"new\s+rule\s*:",
        r"act\s+as\s+a",
        r"pretend\s+you\s+are",
    ]

    # Common jailbreak signatures
    JAILBREAK_PATTERNS = [
        r"\bDAN\b",
        r"do\s+anything\s+now",
        r"developer\s+mode",
        r"bypass\s+filter",
        r"unfiltered\s+mode",
        r"jailbreak",
        r"root\s+access",
        r"sudo\s+",
    ]

    # System level / unsafe operation patterns
    UNSAFE_PATTERNS = [
        r"drop\s+database",
        r"drop\s+table",
        r"truncate\s+table",
        r"delete\s+from",
        r"rm\s+-rf",
        r"format\s+c:",
        r"shutdown\s+-r",
        r"exec\s*\(\s*['\"]",
        r"eval\s*\(\s*['\"]",
        r"__import__",
        r"import\s+os",
        r"import\s+subprocess",
    ]

    def __init__(self) -> None:
        """Initialize and compile search regex patterns for optimized performance."""
        self._injection_regex = re.compile(
            "|".join(self.INJECTION_PATTERNS), re.IGNORECASE
        )
        self._jailbreak_regex = re.compile(
            "|".join(self.JAILBREAK_PATTERNS), re.IGNORECASE
        )
        self._unsafe_regex = re.compile(
            "|".join(self.UNSAFE_PATTERNS), re.IGNORECASE
        )

    def validate_query(self, query: str) -> Tuple[bool, str, str]:
        """
        Validates the raw user text query for security violations.

        Args:
            query (str): The raw user query string.

        Returns:
            Tuple[bool, str, str]:
                - is_safe (bool): True if safe, False if security policy violated.
                - violation_type (str): Type of violation detected ('none', 'prompt_injection', 'jailbreak', 'unsafe_query').
                - detail_message (str): Explanation or security response message.
        """
        if not query or not query.strip():
            logger.warning("ParseGuardrail: Empty user query received.")
            return False, "unsafe_query", "The query submitted was empty or invalid."

        # Check Prompt Injection
        if self._injection_regex.search(query):
            logger.warning(f"ParseGuardrail: Prompt injection detected in query: {query[:50]}...")
            return (
                False,
                "prompt_injection",
                "Security Alert: Prompt injection attempt detected. The request has been blocked for safety reasons."
            )

        # Check Jailbreak Attempt
        if self._jailbreak_regex.search(query):
            logger.warning(f"ParseGuardrail: Jailbreak pattern detected in query: {query[:50]}...")
            return (
                False,
                "jailbreak",
                "Security Alert: Potential jailbreak or policy bypass pattern detected. The request cannot be processed."
            )

        # Check Unsafe Commands / System Operations
        if self._unsafe_regex.search(query):
            logger.warning(f"ParseGuardrail: Unsafe operation pattern detected in query: {query[:50]}...")
            return (
                False,
                "unsafe_query",
                "Security Alert: Unsafe system operation pattern detected. The request has been terminated."
            )

        logger.info("ParseGuardrail: Query passed security checks.")
        return True, "none", "Query passed security checks."

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        LangGraph node handler for the Parse Guardrail.

        Args:
            state (Dict[str, Any]): The QueryState dictionary containing user_query.

        Returns:
            Dict[str, Any]: Updated state with security validation results and response payload if unsafe.
        """
        query = state.get("user_query", "")
        is_safe, violation_type, detail_msg = self.validate_query(query)

        updated_state = dict(state)
        updated_state["is_safe"] = is_safe
        updated_state["guardrail_stage"] = "parse"

        if not is_safe:
            updated_state["error_type"] = "security_violation"
            updated_state["security_violation"] = {
                "guardrail": "parse_guard",
                "violation_type": violation_type,
                "message": detail_msg
            }
            # Short-circuit response payload creation
            updated_state["final_response"] = {
                "status": "security_blocked",
                "error_code": f"SEC_{violation_type.upper()}",
                "message": detail_msg,
                "data": None,
                "metadata": {
                    "stage": "parse_guardrail",
                    "passed": False
                }
            }

        return updated_state


def run_parse_guard(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Functional wrapper for LangGraph node execution.

    Args:
        state (Dict[str, Any]): The incoming QueryState dictionary.

    Returns:
        Dict[str, Any]: Updated QueryState dictionary.
    """
    guard = ParseGuardrail()
    return guard.execute(state)
