"""
Final API Response Pydantic Schema for Query LangGraph (querylanggraph02).

Defines unified standardized JSON output returned to the client.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from schemas.visualization_response import VisualizationResponseSchema
from schemas.metadata import RetrievalMetadataSchema


class QueryResponseSchema(BaseModel):
    """Unified standardized API response schema for Query LangGraph."""

    status: str = Field(..., description="Execution status: 'success', 'security_blocked', 'validation_failed', 'no_data_found'")
    error_code: Optional[str] = Field(None, description="Error or security code if applicable")
    answer: str = Field(..., description="Synthesized natural language answer or status message")
    data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Retrieved raw persistence data")
    visualization: Optional[VisualizationResponseSchema] = Field(None, description="Base64 visualization payload if generated")
    details: Optional[List[str]] = Field(None, description="Validation issues if failed")
    suggested_corrections: Optional[List[str]] = Field(None, description="Parameter suggestions if failed")
    metadata: RetrievalMetadataSchema = Field(default_factory=RetrievalMetadataSchema, description="Execution and retrieval metadata")
