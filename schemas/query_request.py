"""
Query Request Pydantic Schema for Query LangGraph (querylanggraph02).

Defines input payload structure for API requests entering the Query Graph.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Client request schema for Query LangGraph API endpoint."""

    user_query: str = Field(..., min_length=1, description="Natural language query string from client")
    client_id: Optional[str] = Field("default_client", description="Optional client/tenant identifier")
    session_id: Optional[str] = Field(None, description="Optional conversation correlation ID")
    request_metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary client metadata")
