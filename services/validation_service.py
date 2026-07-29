"""
Validation Service for Query LangGraph (querylanggraph02).

Encapsulates business validation rules, metrics verification, and bounds checking.
"""

from typing import Dict, Any, Tuple
from nodes.validation import ValidationNode


class ValidationService:
    """Service wrapper for business validation rules."""

    def __init__(self) -> None:
        self._validator = ValidationNode()

    def validate(self, query_intent: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Validates query intent parameters against business rules."""
        return self._validator.validate_query_intent(query_intent)
