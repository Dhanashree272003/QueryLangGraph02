"""
Response Handling Utilities for Query LangGraph (querylanggraph02).

Provides utility methods for constructing API responses and client payloads.
"""

from typing import Dict, Any
from services.response_formatter import ResponseFormatter


class ResponseService:
    """Service wrapper for client response formatting."""

    def __init__(self) -> None:
        self.formatter = ResponseFormatter()

    def build_response(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Constructs standardized client response dictionary."""
        return self.formatter.format_response(state)
