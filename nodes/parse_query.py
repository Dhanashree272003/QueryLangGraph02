"""
Parse Query Node for Query LangGraph (querylanggraph02).

This node uses Gemini 2.5 Flash (via the google-genai SDK) to convert natural
language queries into a structured QueryIntent (Pydantic JSON format).

Authentication:
  - AQ.* token  -> google.oauth2.credentials.Credentials (OAuth2 bearer)
  - AIza* key   -> genai.Client(api_key=...)
  - sk-or-v1*   -> OpenRouter REST fallback

Responsibilities:
- Deep semantic analysis of natural language queries -> Structured QueryIntent schema.
- Extract entities: categories, metrics, services, failure modes, time ranges,
  aggregations, visualization requests, filters, sorting.
- Pure parsing only (no validation, no SQL generation, no DB access, no business logic).
"""

import os
import json
import logging
import re
from typing import Dict, Any, Optional

logger = logging.getLogger("QueryLangGraph.Nodes.ParseQuery")

MODEL = "models/gemini-flash-latest"


def _build_genai_client(api_key: str):
    """
    Build and return a google.genai.Client using the correct auth strategy
    for the given key format.

    AQ.* tokens are OAuth2 access tokens issued by Google AI Studio and must
    be wrapped in google.oauth2.credentials.Credentials so the new SDK sends
    them as a Bearer header rather than a ?key= query parameter.
    """
    from google import genai

    if api_key.startswith("AQ."):
        from google.oauth2.credentials import Credentials
        creds = Credentials(token=api_key)
        return genai.Client(credentials=creds)

    # Standard Google AI Studio API key (AIza...) or other formats
    return genai.Client(api_key=api_key)


class ParseQueryNode:
    """
    Parse Query Node using Gemini 2.5 Flash (google-genai SDK).

    Transforms user query string into structured QueryIntent payload.
    """

    SYSTEM_PROMPT = """You are an Enterprise AIOps Query Parser powered by Gemini 2.5 Flash.
Your task is to analyze ANY natural language query (standard, complex, conversational, non-standard, multi-part, or implicit) and map it accurately into a structured JSON representation of intent.

DEEP SEMANTIC ANALYSIS RULES:
1. Category Classification: Identify all applicable categories (Single or Combinational):
   - "metrics": Telemetry metrics (CPU, Memory, Disk, Network, Latency, Error Rate, Throughput).
   - "incident": Outages, crashes, root causes, alerts, incident history.
   - "severity": Severity levels (CRITICAL, HIGH, MEDIUM, LOW, P0, P1), escalation states.
   - "forecast": Time-to-failure (TTF), metric predictions, anomaly probabilities.
   - "feature_contribution": Feature importance, component impact analysis.
   - "system_health": System status, service health overviews.
   - "reliability": Service reliability, SLA/SLO percentages, uptime, error budget status.
   - "combinational": Set is_combinational=true if query spans 2 or more of the categories above.

2. Implicit Entity & Domain Mapping:
   - Map colloquial terms (e.g. "choking/slow" -> latency/error_rate; "crash/spike" -> memory_leak/cpu_usage).
   - Map informal time phrases (e.g. "yesterday" -> past 24h, "last night" -> past 12h, "recently" -> last_1_hour).

3. Visualization Intent Detection:
   - Set visualization_request.is_requested=true if user explicitly or implicitly asks for a chart, graph, plot, visual, trend line, compare, or visual breakdown.

Output strictly raw valid JSON adhering to the following structure:
{
  "categories": ["metrics", "incident"],
  "is_combinational": false,
  "metrics": ["cpu_usage"],
  "services": ["auth-service"],
  "failure_modes": [],
  "time_range": {
    "start_time": null,
    "end_time": null,
    "duration": "last_1_hour",
    "raw_expression": "past hour"
  },
  "aggregation": {
    "function": "avg",
    "group_by": ["service"]
  },
  "visualization_request": {
    "is_requested": false,
    "chart_type": "line",
    "x_axis": "timestamp",
    "y_axis": "value",
    "title": "AIOps Query Analysis"
  },
  "filters": {},
  "sorting": {
    "order_by": "timestamp",
    "order_direction": "DESC"
  },
  "additional_entities": {}
}

Return ONLY raw valid JSON without markdown fences or outside commentary."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        """
        Initialize the ParseQueryNode with API credentials.

        Args:
            api_key (Optional[str]): Gemini / OpenRouter API key.
                                     If omitted, reads from environment.
        """
        self.api_key = (
            api_key
            or os.environ.get("GEMINI_API_KEY")
            or os.environ.get("OPENROUTER_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
        )
        if not self.api_key:
            logger.warning("ParseQueryNode: No API key found in parameters or environment variables.")

    def parse_with_llm(self, query: str) -> Dict[str, Any]:
        """
        Invokes Gemini 2.5 Flash (new google-genai SDK) to parse natural language
        into structured QueryIntent JSON.

        Args:
            query (str): Raw user query string.

        Returns:
            Dict[str, Any]: Structured query intent dictionary.
        """
        if not self.api_key:
            logger.error("ParseQueryNode: Cannot invoke LLM without API Key.")
            return self._fallback_rule_based_parse(query)

        prompt = f"{self.SYSTEM_PROMPT}\n\nUser Query: {query}"

        # ------------------------------------------------------------------ #
        # Path 1: google-genai SDK (AQ.* OAuth2 token or AIza* API key)
        # ------------------------------------------------------------------ #
        if not self.api_key.startswith("sk-or-v1"):
            try:
                client = _build_genai_client(self.api_key)
                response = client.models.generate_content(
                    model=MODEL,
                    contents=prompt,
                )
                response_text = response.text
                logger.info("ParseQueryNode: LLM response received via google-genai SDK.")
                return self._clean_and_parse_json(response_text)
            except Exception as sdk_err:
                logger.error(f"ParseQueryNode: google-genai SDK call failed: {sdk_err}. Falling back to rule-based parser.")
                return self._fallback_rule_based_parse(query)

        # ------------------------------------------------------------------ #
        # Path 2: OpenRouter REST (sk-or-v1* keys)
        # ------------------------------------------------------------------ #
        try:
            import urllib.request
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "google/gemini-2.5-flash",
                "messages": [
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": query},
                ],
                "temperature": 0.0,
            }
            req = urllib.request.Request(
                url, data=json.dumps(payload).encode("utf-8"), headers=headers
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                response_text = resp_data["choices"][0]["message"]["content"]
            return self._clean_and_parse_json(response_text)
        except Exception as e:
            logger.error(f"ParseQueryNode: OpenRouter REST call failed ({e}). Falling back to rule-based parser.")
            return self._fallback_rule_based_parse(query)

    def _clean_and_parse_json(self, raw_response: str) -> Dict[str, Any]:
        """Strips markdown code fences and parses JSON string."""
        cleaned = raw_response.strip()
        cleaned = re.sub(r"^```(json)?", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as err:
            logger.error(f"ParseQueryNode: Failed to parse JSON from LLM output: {err}")
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    pass
            return self._fallback_rule_based_parse(cleaned)

    def _fallback_rule_based_parse(self, query: str) -> Dict[str, Any]:
        """Rule-based heuristic parsing fallback if LLM is unreachable."""
        q_lower = query.lower()
        categories = []

        if any(w in q_lower for w in ["cpu", "memory", "latency", "metric", "throughput", "usage"]):
            categories.append("metrics")
        if any(w in q_lower for w in ["incident", "alert", "outage", "failure", "crash"]):
            categories.append("incident")
        if any(w in q_lower for w in ["severity", "critical", "high", "p0", "p1"]):
            categories.append("severity")
        if any(w in q_lower for w in ["forecast", "predict", "time to failure", "ttf"]):
            categories.append("forecast")
        if any(w in q_lower for w in ["reliability", "slo", "sla", "uptime"]):
            categories.append("reliability")
        if any(w in q_lower for w in ["health", "status"]):
            categories.append("system_health")

        if not categories:
            categories = ["metrics"]

        is_combinational = len(categories) > 1
        if is_combinational:
            categories.append("combinational")

        is_vis = any(w in q_lower for w in ["chart", "graph", "plot", "show", "visualize", "compare", "breakdown"])

        return {
            "categories": categories,
            "is_combinational": is_combinational,
            "metrics": ["cpu_usage"] if "cpu" in q_lower else ["memory_usage"] if "memory" in q_lower else [],
            "services": ["auth-service"] if "auth" in q_lower else ["payment-service"] if "payment" in q_lower else [],
            "failure_modes": [],
            "time_range": {"duration": "last_1_hour", "raw_expression": query},
            "aggregation": {"function": "avg", "group_by": []},
            "visualization_request": {
                "is_requested": is_vis,
                "chart_type": "line" if is_vis else None,
                "x_axis": "timestamp",
                "y_axis": "value",
                "title": "AIOps Query Telemetry",
            },
            "filters": {},
            "sorting": {"order_by": "timestamp", "order_direction": "DESC"},
            "additional_entities": {},
        }

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        LangGraph execution entry point.

        Args:
            state (Dict[str, Any]): QueryState dictionary.

        Returns:
            Dict[str, Any]: Updated QueryState dictionary containing query_intent.
        """
        query = state.get("user_query", "")
        logger.info(f"ParseQueryNode: Deep parsing query: '{query}'")

        parsed_intent = self.parse_with_llm(query)

        updated_state = dict(state)
        updated_state["query_intent"] = parsed_intent
        updated_state["parsed_successfully"] = True

        return updated_state


def run_parse_query(state: Dict[str, Any]) -> Dict[str, Any]:
    """Functional node wrapper for LangGraph workflow."""
    node = ParseQueryNode()
    return node.execute(state)
