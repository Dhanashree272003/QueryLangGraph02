"""
Metadata Service for Query LangGraph (querylanggraph02).

Generates, enriches, and formats execution and retrieval metadata for workflow records.
"""

import time
import logging
from typing import Dict, Any, List

logger = logging.getLogger("QueryLangGraph.Services.MetadataService")


class MetadataService:
    """Service for enriching query execution telemetry and metadata."""

    def build_metadata(
        self,
        tables_queried: List[str],
        categories_fetched: List[str],
        total_records: int,
        start_time: float,
        query_intent: Dict[str, Any],
        routing_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enriches query metadata with execution statistics.

        Args:
            tables_queried (List[str]): List of SQLite tables accessed.
            categories_fetched (List[str]): Query categories fetched.
            total_records (int): Number of records retrieved.
            start_time (float): Start epoch timestamp.
            query_intent (Dict[str, Any]): Parsed intent dictionary.
            routing_info (Dict[str, Any]): Routing info object.

        Returns:
            Dict[str, Any]: Enriched metadata dictionary.
        """
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        return {
            "tables_queried": tables_queried,
            "categories_fetched": categories_fetched,
            "total_records_fetched": total_records,
            "execution_time_ms": elapsed_ms,
            "has_data": total_records > 0,
            "query_intent": query_intent,
            "routing_info": routing_info
        }
