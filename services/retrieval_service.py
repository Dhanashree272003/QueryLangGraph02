"""
Retrieval Service for Query LangGraph (querylanggraph02).

Orchestrates parameterized SQL execution and data fetching from AIOps persistence DB.
"""

from typing import Dict, Any, Optional
from persistence.repository import AIOpsRepository


class RetrievalService:
    """Service layer orchestrating database access for Query LangGraph."""

    def __init__(self, repository: Optional[AIOpsRepository] = None) -> None:
        self.repository = repository or AIOpsRepository()

    def fetch_data_for_routing(self, routing_info: Dict[str, Any]) -> Dict[str, Any]:
        """Fetches data for single or combinational query routing."""
        services = routing_info.get("services", [])
        metrics = routing_info.get("metrics", [])
        filters = routing_info.get("filters", {})
        limit = int(filters.get("limit", 200))
        failure_modes = routing_info.get("failure_modes", [])

        if routing_info.get("is_combinational", False):
            return self.repository.get_combinational_data(
                retrieval_targets=routing_info.get("retrieval_targets", []),
                services=services,
                metrics=metrics,
                failure_modes=failure_modes,
                limit=limit
            )

        cat = routing_info.get("primary_category", "metrics")
        if cat == "metrics":
            return {"metrics": self.repository.get_metrics(services, metrics, limit)}
        elif cat == "incident":
            return {"incident": self.repository.get_incidents(services, failure_modes, limit)}
        elif cat == "severity":
            return {"severity": self.repository.get_severity(services, limit)}
        elif cat == "forecast":
            return {"forecast": self.repository.get_forecast(services, metrics, limit)}
        elif cat == "reliability":
            return {"reliability": self.repository.get_reliability(services, limit)}
        elif cat == "feature_contribution":
            return {"feature_contribution": self.repository.get_feature_contribution(services, limit)}
        elif cat == "system_health":
            return {"system_health": self.repository.get_system_health(services, limit)}
        return {"metrics": self.repository.get_metrics(services, metrics, limit)}
