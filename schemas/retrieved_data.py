"""
Retrieved Data Pydantic Schemas for Query LangGraph (querylanggraph02).

Defines structured schemas for telemetry metrics, incidents, severity updates,
forecasts, reliability metrics, and feature contribution outputs.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class MetricRecord(BaseModel):
    timestamp: str
    service: str
    metric_name: str
    metric_value: float
    unit: Optional[str] = None


class IncidentRecord(BaseModel):
    incident_id: str
    timestamp: str
    service: str
    failure_mode: str
    confidence: float
    root_cause: Optional[str] = None


class SeverityRecord(BaseModel):
    incident_id: str
    timestamp: str
    service: str
    initial_severity: str
    updated_severity: str
    escalation_reason: Optional[str] = None


class ForecastRecord(BaseModel):
    timestamp: str
    service: str
    metric_name: str
    forecast_value: float
    time_to_failure_mins: Optional[float] = None
    anomaly_probability: Optional[float] = None


class ReliabilityRecord(BaseModel):
    timestamp: str
    service: str
    slo_percentage: float
    uptime_percentage: float
    error_budget_remaining: float


class FeatureContributionRecord(BaseModel):
    incident_id: str
    timestamp: str
    service: str
    feature_name: str
    importance_score: float
    additional_metadata: Optional[str] = None


class RetrievedDataPayload(BaseModel):
    """Container for retrieved persistence data across categories."""
    metrics: List[Dict[str, Any]] = Field(default_factory=list)
    incident: List[Dict[str, Any]] = Field(default_factory=list)
    severity: List[Dict[str, Any]] = Field(default_factory=list)
    forecast: List[Dict[str, Any]] = Field(default_factory=list)
    reliability: List[Dict[str, Any]] = Field(default_factory=list)
    feature_contribution: List[Dict[str, Any]] = Field(default_factory=list)
    system_health: List[Dict[str, Any]] = Field(default_factory=list)
