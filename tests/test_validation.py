"""
Unit Tests for Validation Node and Validation Guardrail.
"""

import pytest
from guardrails.validation_guard import ValidationGuardrail
from nodes.validation import ValidationNode


def test_validation_guardrail_pass():
    guard = ValidationGuardrail()
    intent = {
        "categories": ["metrics"],
        "metrics": ["cpu_usage"],
        "services": ["auth-service"]
    }
    is_safe, violation_type, msg = guard.validate_intent_security(intent)
    assert is_safe is True


def test_validation_guardrail_sensitive_data():
    guard = ValidationGuardrail()
    intent = {
        "categories": ["metrics"],
        "metrics": ["password_hash"],
        "services": ["auth-service"]
    }
    is_safe, violation_type, msg = guard.validate_intent_security(intent)
    assert is_safe is False
    assert violation_type == "sensitive_data_restriction"


def test_validation_node_valid_metrics():
    val_node = ValidationNode()
    intent = {
        "categories": ["metrics"],
        "metrics": ["cpu_usage"],
        "services": ["auth-service"],
        "aggregation": {"function": "avg"}
    }
    is_valid, report = val_node.validate_query_intent(intent)
    assert is_valid is True
