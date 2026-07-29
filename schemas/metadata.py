"""
Metadata Pydantic Schema for Query LangGraph (querylanggraph02).

Defines execution, retrieval, and telemetry metadata schemas.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class RetrievalMetadataSchema(BaseModel):
    """Metadata detailing persistence database retrieval execution."""

    tables_queried: List[str] = Field(default_factory=list, description="List of SQLite tables accessed")
    categories_fetched: List[str] = Field(default_factory=list, description="Categories retrieved")
    total_records_fetched: int = Field(0, description="Total rows fetched across tables")
    execution_time_ms: float = Field(0.0, description="Query execution latency in milliseconds")
    has_data: bool = Field(False, description="True if at least one row was retrieved")
    query_intent: Dict[str, Any] = Field(default_factory=dict, description="Parsed intent details")
    routing_info: Dict[str, Any] = Field(default_factory=dict, description="Routing metadata")
