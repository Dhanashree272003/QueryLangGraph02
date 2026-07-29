"""
Shared Constants Module for Query LangGraph (querylanggraph02).

Defines query categories, chart types, status codes, default thresholds,
and error codes used across nodes, guardrails, routers, and services.
"""

# Query Categories
CATEGORY_METRICS = "metrics"
CATEGORY_INCIDENT = "incident"
CATEGORY_SEVERITY = "severity"
CATEGORY_FORECAST = "forecast"
CATEGORY_FEATURE_CONTRIBUTION = "feature_contribution"
CATEGORY_SYSTEM_HEALTH = "system_health"
CATEGORY_RELIABILITY = "reliability"
CATEGORY_COMBINATIONAL = "combinational"

ALL_QUERY_CATEGORIES = [
    CATEGORY_METRICS,
    CATEGORY_INCIDENT,
    CATEGORY_SEVERITY,
    CATEGORY_FORECAST,
    CATEGORY_FEATURE_CONTRIBUTION,
    CATEGORY_SYSTEM_HEALTH,
    CATEGORY_RELIABILITY,
    CATEGORY_COMBINATIONAL,
]

# Chart Types
CHART_LINE = "line"
CHART_MULTI_LINE = "multi_line"
CHART_BAR = "bar"

SUPPORTED_CHART_TYPES = [CHART_LINE, CHART_MULTI_LINE, CHART_BAR]

# Status Codes & Responses
STATUS_SUCCESS = "success"
STATUS_SECURITY_BLOCKED = "security_blocked"
STATUS_VALIDATION_FAILED = "validation_failed"
STATUS_NO_DATA = "no_data_found"
STATUS_ERROR = "error"

# Default Query Limits & Timeouts
DEFAULT_QUERY_LIMIT = 200
MAX_QUERY_LIMIT = 5000
LLM_TIMEOUT_SECONDS = 20
