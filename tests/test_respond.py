"""
Unit Tests for Respond Node and Response Formatter.
"""

import pytest
from nodes.respond import RespondNode
from services.response_formatter import ResponseFormatter


def test_response_formatter_success():
    formatter = ResponseFormatter()
    state = {
        "start_time": 1000.0,
        "synthesized_answer": "System CPU usage is normal at 45%.",
        "retrieved_data": {"metrics": [{"service": "auth-service", "metric_value": 45.0}]},
        "retrieval_metadata": {"total_records_fetched": 1, "has_data": True},
        "query_intent": {"categories": ["metrics"]}
    }
    res = formatter.format_response(state)
    assert res["status"] == "success"
    assert res["answer"] == "System CPU usage is normal at 45%."
    assert res["data"] is not None


def test_respond_node_execution():
    node = RespondNode()
    state = {
        "synthesized_answer": "Test answer",
        "retrieved_data": {},
        "retrieval_metadata": {"has_data": False}
    }
    res = node.execute(state)
    assert "final_response" in res
    assert res["execution_completed"] is True
