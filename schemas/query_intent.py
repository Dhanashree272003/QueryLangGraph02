"""
Query Intent Pydantic Schemas for Query LangGraph (querylanggraph02).

Defines structured data models for parsed intent, categories, time ranges, aggregations,
and visualization requests.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class TimeRangeSchema(BaseModel):
    """Time range constraint schema."""
    start_time: Optional[str] = Field(None, description="ISO timestamp for time window start")
    end_time: Optional[str] = Field(None, description="ISO timestamp for time window end")
    duration: Optional[str] = Field("last_1_hour", description="Relative duration code e.g. last_1_hour")
    raw_expression: Optional[str] = Field(None, description="Raw natural language time expression")


class AggregationSchema(BaseModel):
    """Telemetry aggregation parameters."""
    function: Optional[str] = Field("avg", description="Aggregation function (avg, max, min, sum, count, p95, p99)")
    group_by: List[str] = Field(default_factory=list, description="Columns to group by")


class VisualizationRequestSchema(BaseModel):
    """Chart visualization request settings."""
    is_requested: bool = Field(False, description="Whether client requested a visual chart")
    chart_type: Optional[str] = Field("line", description="Chart type: line, multi_line, or bar")
    x_axis: Optional[str] = Field("timestamp", description="Target X axis column")
    y_axis: Optional[str] = Field("metric_value", description="Target Y axis column")
    title: Optional[str] = Field("AIOps Telemetry Chart", description="Chart title")


class QueryIntent(BaseModel):
    """
    Complete structured QueryIntent schema produced by ParseQueryNode.
    """
    categories: List[str] = Field(default_factory=lambda: ["metrics"], description="List of query categories")
    is_combinational: bool = Field(False, description="True if query spans multiple categories")
    metrics: List[str] = Field(default_factory=list, description="Requested metric names")
    services: List[str] = Field(default_factory=list, description="Target service names")
    failure_modes: List[str] = Field(default_factory=list, description="Target failure modes")
    time_range: TimeRangeSchema = Field(default_factory=TimeRangeSchema, description="Time window constraints")
    aggregation: AggregationSchema = Field(default_factory=AggregationSchema, description="Aggregation constraints")
    visualization_request: VisualizationRequestSchema = Field(default_factory=VisualizationRequestSchema, description="Visualization settings")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary Key-Value filters")
    sorting: Dict[str, str] = Field(default_factory=lambda: {"order_by": "timestamp", "order_direction": "DESC"}, description="Sorting options")
    additional_entities: Dict[str, Any] = Field(default_factory=dict, description="Extracted domain entities")
