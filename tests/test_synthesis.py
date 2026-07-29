"""
Unit Tests for Synthesis Node and Synthesis Guardrail.
"""

import pytest
from guardrails.synthesis_guard import SynthesisGuardrail
from nodes.synthesis import SynthesisNode


def test_synthesis_guardrail_pre_check():
    guard = SynthesisGuardrail()
    data = {"metrics": [{"service": "auth-service", "metric_value": 45.2}]}
    is_safe, violation, msg = guard.validate_pre_synthesis(data)
    assert is_safe is True


def test_synthesis_fallback():
    node = SynthesisNode(api_key="mock_key")
    data = {"metrics": [{"service": "auth-service", "metric_name": "cpu_usage", "metric_value": 75.0}]}
    answer = node._fallback_synthesis("Show CPU for auth-service", data, None)
    assert "Metrics" in answer
    assert "75.0" in answer or "auth-service" in answer
