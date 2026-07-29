"""
Visualization Response Pydantic Schema for Query LangGraph (querylanggraph02).

Defines structure for Base64-encoded Matplotlib chart images and metadata.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class VisualizationResponseSchema(BaseModel):
    """Schema for Base64 visualization and chart metadata payload."""

    base64_image: Optional[str] = Field(None, description="Base64 encoded PNG chart string")
    chart_type: str = Field("line", description="Chart type: line, multi_line, or bar")
    title: str = Field("AIOps Telemetry Visualization", description="Chart title")
    x_axis: Optional[str] = Field(None, description="Column mapped to X axis")
    y_axis: Optional[str] = Field(None, description="Column mapped to Y axis")
    data_points: Optional[int] = Field(0, description="Total data points plotted")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Image DPI, format, and theme metadata")
