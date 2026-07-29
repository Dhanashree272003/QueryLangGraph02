"""
Sufficiency Router Module for Query LangGraph (querylanggraph02).

This router checks whether the retrieved persistence data is sufficient for LLM synthesis.
If data exists, execution proceeds to the Synthesis Guardrail. If no data was found,
it bypasses synthesis entirely and short-circuits to the Response Formatter.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger("QueryLangGraph.Routers.SufficiencyRouter")


class SufficiencyRouter:
    """
    Router for evaluating data sufficiency prior to natural language synthesis.

    Responsibilities:
    - Inspect retrieved_data dictionary for record count.
    - Route to Synthesis Guardrail if data is present.
    - Route to Response Formatter with a structured 'No Data Available' payload if data is empty.
    """

    def check_sufficiency(self, retrieved_data: Dict[str, Any]) -> bool:
        """
        Determines whether retrieved data contains at least one record.

        Args:
            retrieved_data (Dict[str, Any]): Dictionary of retrieved data keyed by category.

        Returns:
            bool: True if sufficient data exists, False otherwise.
        """
        if not retrieved_data or not isinstance(retrieved_data, dict):
            return False

        total_rows = 0
        for category, rows in retrieved_data.items():
            if isinstance(rows, list):
                total_rows += len(rows)

        logger.info(f"SufficiencyRouter: Total records found across all categories: {total_rows}")
        return total_rows > 0

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        LangGraph node entry point.

        Args:
            state (Dict[str, Any]): QueryState dictionary.

        Returns:
            Dict[str, Any]: Updated QueryState dictionary.
        """
        retrieved_data = state.get("retrieved_data", {})
        is_sufficient = self.check_sufficiency(retrieved_data)

        updated_state = dict(state)
        updated_state["is_sufficient"] = is_sufficient

        if not is_sufficient:
            logger.warning("SufficiencyRouter: Data is insufficient/empty. Short-circuiting synthesis.")
            query_intent = state.get("query_intent", {})
            services = query_intent.get("services", [])
            metrics = query_intent.get("metrics", [])
            categories = query_intent.get("categories", [])

            service_str = f" for service(s) '{', '.join(services)}'" if services else ""
            metric_str = f" matching metric(s) '{', '.join(metrics)}'" if metrics else ""

            msg = (
                f"No telemetric or operational data was found in the persistence database"
                f"{service_str}{metric_str} for category '{', '.join(categories)}'."
            )

            updated_state["no_data_response"] = {
                "status": "no_data_found",
                "message": msg,
                "data": {},
                "metadata": {
                    "stage": "sufficiency_router",
                    "sufficient": False
                }
            }
            updated_state["final_response"] = {
                "status": "no_data_found",
                "answer": msg,
                "metadata": state.get("retrieval_metadata", {}),
                "data": {},
                "visualization": None
            }

        return updated_state


def run_sufficiency_router(state: Dict[str, Any]) -> Dict[str, Any]:
    """Functional wrapper for Sufficiency Router execution."""
    router = SufficiencyRouter()
    return router.execute(state)
