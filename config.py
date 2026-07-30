"""
Configuration Module for Query LangGraph (querylanggraph02).

Centralizes environment settings, database locations, LLM model parameters,
and execution limits for the Query LangGraph workflow.
"""

import os
from dataclasses import dataclass, field

# Load .env from project root — must happen before any os.getenv() calls
try:
    from dotenv import load_dotenv
    _env_path = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(_env_path, override=True)
except ImportError:
    pass  # python-dotenv not installed; rely on shell environment


@dataclass
class GraphConfig:
    """Centralized configuration settings for the Query LangGraph system."""

    # Project metadata
    PROJECT_NAME: str = "QueryLangGraph02"
    VERSION: str = "2.5.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")

    # LLM Settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", os.getenv("OPENROUTER_API_KEY", ""))
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-2.5-flash")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))

    # Database Settings
    AIOPS_DB_PATH: str = os.getenv(
        "AIOPS_DB_PATH",
        os.path.join(os.path.dirname(__file__), "persistence", "aiops.db")
    )
    MAX_QUERY_RECORD_LIMIT: int = int(os.getenv("MAX_QUERY_RECORD_LIMIT", "2000"))

    # Visualization Settings
    CHART_THEME: str = os.getenv("CHART_THEME", "dark")
    CHART_DPI: int = int(os.getenv("CHART_DPI", "120"))
    ENABLE_VISUALIZATION: bool = os.getenv("ENABLE_VISUALIZATION", "true").lower() == "true"

    # Security & Guardrails
    ENABLE_STRICT_GUARDRAILS: bool = os.getenv("ENABLE_STRICT_GUARDRAILS", "true").lower() == "true"

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


# Global singleton instance
config = GraphConfig()
