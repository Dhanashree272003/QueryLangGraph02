"""
Custom Exception Classes for Query LangGraph (querylanggraph02).

Defines an enterprise-grade exception hierarchy for error handling across nodes,
guardrails, routers, and services.
"""


class QueryGraphError(Exception):
    """Base exception for all Query LangGraph errors."""

    def __init__(self, message: str, error_code: str = "ERR_QUERY_GRAPH_UNKNOWN") -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class GuardrailViolationError(QueryGraphError):
    """Raised when a security guardrail detects an unsafe query or malicious input."""

    def __init__(self, message: str, guardrail_stage: str, violation_type: str) -> None:
        super().__init__(message, error_code=f"SEC_{violation_type.upper()}")
        self.guardrail_stage = guardrail_stage
        self.violation_type = violation_type


class BusinessValidationError(QueryGraphError):
    """Raised when query intent violates business validation rules or schema bounds."""

    def __init__(self, message: str, issues: list = None, suggestions: list = None) -> None:
        super().__init__(message, error_code="ERR_BUSINESS_VALIDATION_FAILED")
        self.issues = issues or []
        self.suggestions = suggestions or []


class PersistenceRetrievalError(QueryGraphError):
    """Raised when database query execution fails."""

    def __init__(self, message: str, table_name: str = None) -> None:
        super().__init__(message, error_code="ERR_RETRIEVAL_FAILED")
        self.table_name = table_name


class LLMSynthesisError(QueryGraphError):
    """Raised when LLM invocation or parsing fails."""

    def __init__(self, message: str, node_name: str) -> None:
        super().__init__(message, error_code="ERR_LLM_SYNTHESIS_FAILED")
        self.node_name = node_name
