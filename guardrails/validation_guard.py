"""
Validation Guardrail Module for Query LangGraph (querylanggraph02).

This module runs after query parsing and prior to business rule validation.
It verifies that the parsed QueryIntent conforms to structural security rules,
schema safety requirements, and sensitive data access constraints.
"""

import re
import logging
from typing import Dict, Any, Tuple, List

logger = logging.getLogger("QueryLangGraph.Guardrails.ValidationGuard")


class ValidationGuardrail:
    """
    Guardrail before Validation Node.

    Responsibilities:
    - Validate Intent Structure (checks JSON schema completeness and valid categories)
    - Schema Safety Check (detects nested script or injection fragments inside parsed structures)
    - Sensitive Data Check (restricts access to credentials, secret tokens, and PII)
    """

    RESTRICTED_ENTITIES = [
        "password", "secret", "token", "api_key", "credit_card", "ssn",
        "private_key", "auth_token", "hash", "salt", "credential"
    ]

    MALICIOUS_SCHEMA_PATTERNS = [
        r"<\s*script",
        r"javascript\s*:",
        r"UNION\s+SELECT",
        r"--\s*$",
        r"/\*.*\*/",
        r"exec\s*\(",
        r"eval\s*\(",
    ]

    ALLOWED_CATEGORIES = {
        "metrics", "incident", "severity", "forecast",
        "feature_contribution", "system_health", "reliability", "combinational"
    }

    def __init__(self) -> None:
        """Compile regex patterns for schema safety checks."""
        self._malicious_schema_regex = re.compile(
            "|".join(self.MALICIOUS_SCHEMA_PATTERNS), re.IGNORECASE
        )

    def validate_intent_security(self, query_intent: Dict[str, Any]) -> Tuple[bool, str, str]:
        """
        Executes security checks on the parsed QueryIntent object.

        Args:
            query_intent (Dict[str, Any]): The structured intent output from Parse Query Node.

        Returns:
            Tuple[bool, str, str]:
                - is_safe (bool): True if intent is structurally safe and compliant.
                - violation_type (str): Type of violation detected.
                - message (str): Explanation message.
        """
        if not query_intent or not isinstance(query_intent, dict):
            return False, "invalid_structure", "The query intent structure is missing or malformed."

        # 1. Intent Structure Validation
        categories = query_intent.get("categories", [])
        if not isinstance(categories, list) or not categories:
            return False, "missing_categories", "Query intent must specify at least one valid query category."

        for cat in categories:
            if str(cat).lower() not in self.ALLOWED_CATEGORIES:
                return False, "invalid_category", f"Category '{cat}' is not recognized by the platform."

        # 2. Sensitive Data Check
        intent_str = str(query_intent).lower()
        for restricted in self.RESTRICTED_ENTITIES:
            if restricted in intent_str:
                logger.warning(f"ValidationGuardrail: Sensitive entity access attempt detected: '{restricted}'")
                return (
                    False,
                    "sensitive_data_restriction",
                    f"Security Alert: Request references restricted entity or sensitive field '{restricted}'."
                )

        # 3. Schema Safety Check
        if self._malicious_schema_regex.search(intent_str):
            logger.warning("ValidationGuardrail: Malicious payload pattern found in parsed query intent.")
            return (
                False,
                "schema_safety_violation",
                "Security Alert: Potentially harmful scripting or injection pattern detected within parsed intent parameters."
            )

        logger.info("ValidationGuardrail: Parsed QueryIntent passed all structural & security checks.")
        return True, "none", "QueryIntent passed validation guardrail checks."

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        LangGraph node entry point for the Validation Guardrail.

        Args:
            state (Dict[str, Any]): The QueryState dictionary.

        Returns:
            Dict[str, Any]: Updated QueryState dictionary.
        """
        query_intent = state.get("query_intent", {})
        is_safe, violation_type, detail_msg = self.validate_intent_security(query_intent)

        updated_state = dict(state)
        updated_state["is_safe"] = is_safe
        updated_state["guardrail_stage"] = "validation"

        if not is_safe:
            updated_state["error_type"] = "security_violation"
            updated_state["security_violation"] = {
                "guardrail": "validation_guard",
                "violation_type": violation_type,
                "message": detail_msg
            }
            updated_state["final_response"] = {
                "status": "security_blocked",
                "error_code": f"SEC_{violation_type.upper()}",
                "message": detail_msg,
                "data": None,
                "metadata": {
                    "stage": "validation_guardrail",
                    "passed": False
                }
            }

        return updated_state


def run_validation_guard(state: Dict[str, Any]) -> Dict[str, Any]:
    """Functional wrapper for LangGraph node execution."""
    guard = ValidationGuardrail()
    return guard.execute(state)
