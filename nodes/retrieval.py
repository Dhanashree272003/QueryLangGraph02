"""
Retrieval Node for Query LangGraph (querylanggraph02).

This node reads from the AIOps persistence database (populated by the Inference Graph),
executes deterministic parameterized SQL queries based on routing information,
generates retrieval metadata, and optionally creates Matplotlib visualizations as Base64.

Responsibilities:
- Build and execute parameterized SQL queries via AIOpsRepository.
- Support single-category and combinational multi-category retrieval.
- Track retrieval metadata (execution time, rows fetched, tables queried).
- Generate Matplotlib visualizations (Line, Multi-Line, Bar) if requested.
- Convert charts to Base64 for downstream transmission.
- NO LLM, NO summarization, NO reasoning — pure data retrieval only.
"""

import time
import logging
from typing import Dict, Any, List, Optional

from persistence.repository import AIOpsRepository

logger = logging.getLogger("QueryLangGraph.Nodes.Retrieval")


class RetrievalNode:
    """
    Pure data retrieval node for the Query LangGraph.

    Reads from AIOps SQLite persistence tables and optionally generates
    Matplotlib-based visualizations encoded as Base64 images.
    """

    def __init__(self, repository: Optional[AIOpsRepository] = None) -> None:
        """
        Initialize RetrievalNode with an optional injected repository.

        Args:
            repository (Optional[AIOpsRepository]): Injected repo for testing; otherwise default.
        """
        self.repository = repository or AIOpsRepository()

    def retrieve_data(
        self,
        routing_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Executes database retrieval based on routing information.

        Args:
            routing_info (Dict[str, Any]): Routing metadata from IntentRouter.

        Returns:
            Dict[str, Any]: Retrieved rows keyed by category.
        """
        services = routing_info.get("services", [])
        metrics = routing_info.get("metrics", [])
        filters = routing_info.get("filters", {})
        limit = int(filters.get("limit", 200))

        # Extract failure modes from original intent (passed through routing_info if present)
        failure_modes = routing_info.get("failure_modes", [])

        is_combinational = routing_info.get("is_combinational", False)
        retrieval_targets = routing_info.get("retrieval_targets", [])

        if is_combinational:
            data = self.repository.get_combinational_data(
                retrieval_targets=retrieval_targets,
                services=services,
                metrics=metrics,
                failure_modes=failure_modes,
                limit=limit
            )
        else:
            primary_category = routing_info.get("primary_category", "metrics")
            dispatch = {
                "metrics":              lambda: {"metrics": self.repository.get_metrics(services, metrics, limit)},
                "incident":             lambda: {"incident": self.repository.get_incidents(services, failure_modes, limit)},
                "severity":             lambda: {"severity": self.repository.get_severity(services, limit)},
                "forecast":             lambda: {"forecast": self.repository.get_forecast(services, metrics, limit)},
                "reliability":          lambda: {"reliability": self.repository.get_reliability(services, limit)},
                "feature_contribution": lambda: {"feature_contribution": self.repository.get_feature_contribution(services, limit)},
                "system_health":        lambda: {"system_health": self.repository.get_system_health(services, limit)},
                "tumbling_window":      lambda: {"tumbling_window": self.repository.get_tumbling_window(services, limit)},
                "human_gate":           lambda: {"human_gate": self.repository.get_human_gate(services, limit)},
            }
            fetcher = dispatch.get(primary_category, dispatch["metrics"])
            data = fetcher()

        return data

    def build_retrieval_metadata(
        self,
        data: Dict[str, Any],
        tables_queried: List[str],
        elapsed_ms: float
    ) -> Dict[str, Any]:
        """
        Constructs retrieval metadata from query execution results.

        Args:
            data (Dict[str, Any]): Retrieved data keyed by category.
            tables_queried (List[str]): Tables accessed during retrieval.
            elapsed_ms (float): Query execution time in milliseconds.

        Returns:
            Dict[str, Any]: Metadata dictionary.
        """
        total_rows = sum(len(rows) if isinstance(rows, list) else 0 for rows in data.values())
        return {
            "tables_queried": tables_queried,
            "categories_fetched": list(data.keys()),
            "total_records_fetched": total_rows,
            "execution_time_ms": round(elapsed_ms, 2),
            "has_data": total_rows > 0
        }

    def generate_visualization(
        self,
        data: Dict[str, Any],
        visualization_request: Dict[str, Any],
        routing_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Delegates visualization generation to VisualizationService.

        Args:
            data (Dict[str, Any]): Retrieved data dictionary.
            visualization_request (Dict[str, Any]): Chart parameters from QueryIntent.
            routing_info (Dict[str, Any]): Routing info for category context.

        Returns:
            Dict[str, Any]: Visualization payload with base64_image and metadata.
        """
        try:
            from services.visualization_service import VisualizationService
            vis_service = VisualizationService()
            return vis_service.generate(
                data=data,
                chart_type=visualization_request.get("chart_type", "line"),
                x_axis=visualization_request.get("x_axis", "timestamp"),
                y_axis=visualization_request.get("y_axis", "metric_value"),
                title=visualization_request.get("title", "AIOps Query Result"),
                primary_category=routing_info.get("primary_category", "metrics")
            )
        except Exception as e:
            logger.error(f"RetrievalNode: Visualization generation failed: {e}")
            return {
                "base64_image": None,
                "chart_type": visualization_request.get("chart_type", "line"),
                "title": visualization_request.get("title", "AIOps Query Result"),
                "error": str(e)
            }

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        LangGraph node entry point.

        Args:
            state (Dict[str, Any]): QueryState dictionary.

        Returns:
            Dict[str, Any]: Updated QueryState with retrieved_data, retrieval_metadata,
                            and optional visualization_payload.
        """
        routing_info = state.get("routing_info", {})
        query_intent = state.get("query_intent", {})

        visualization_request = (
            routing_info.get("visualization_request")
            or query_intent.get("visualization_request", {})
        )

        logger.info(f"RetrievalNode: Starting retrieval for categories: {routing_info.get('all_categories')}")
        start_time = time.time()

        try:
            data = self.retrieve_data(routing_info)
        except Exception as e:
            logger.error(f"RetrievalNode: Data retrieval failed: {e}")
            data = {}

        elapsed_ms = (time.time() - start_time) * 1000
        tables_queried = routing_info.get("target_tables", [])
        retrieval_metadata = self.build_retrieval_metadata(data, tables_queried, elapsed_ms)

        updated_state = dict(state)
        updated_state["retrieved_data"] = data
        updated_state["retrieval_metadata"] = retrieval_metadata
        updated_state["retrieval_successful"] = retrieval_metadata["has_data"]

        # Visualization
        is_vis_requested = (
            isinstance(visualization_request, dict)
            and visualization_request.get("is_requested", False)
        )

        if is_vis_requested and retrieval_metadata["has_data"]:
            logger.info("RetrievalNode: Visualization requested — generating chart.")
            vis_payload = self.generate_visualization(data, visualization_request, routing_info)
            updated_state["visualization_payload"] = vis_payload
        else:
            updated_state["visualization_payload"] = None

        logger.info(
            f"RetrievalNode: Retrieval complete — {retrieval_metadata['total_records_fetched']} rows "
            f"in {retrieval_metadata['execution_time_ms']}ms."
        )
        return updated_state


def run_retrieval(state: Dict[str, Any]) -> Dict[str, Any]:
    """Functional wrapper for LangGraph node execution."""
    node = RetrievalNode()
    return node.execute(state)
