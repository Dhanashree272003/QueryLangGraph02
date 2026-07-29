"""
Synthesis Node for Query LangGraph (querylanggraph02).

This node uses Gemini 2.5 Flash to convert structured retrieved AIOps persistence data
into a grounded, natural language response.

Requirements:
- Grounded explanations based strictly on retrieved database records.
- Summarizes insights, failure modes, severity levels, and metric trends.
- Explains generated Matplotlib charts when a visualization is attached.
- Explicitly mentions if retrieved data is incomplete or empty.
- Zero tolerance for hallucinations, fabricated numbers, or unsupported assumptions.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("QueryLangGraph.Nodes.Synthesis")


class SynthesisNode:
    """
    Synthesis Node using Gemini 2.5 Flash.

    Converts retrieved database rows, query intent, and chart metadata into natural language answers.
    """

    SYSTEM_PROMPT = """You are an Enterprise AIOps System Architect and Senior Reliability Analyst powered by Gemini 2.5 Flash.
Your task is to synthesize structured database retrieval outputs into a clear, professional, evidence-based natural language response for the client.

STRICT GROUNDING RULES:
1. Base all statements strictly and exclusively on the provided retrieved data.
2. DO NOT hallucinate, fabricate metrics, invent timestamps, or guess root causes not present in the data.
3. If data is incomplete or truncated, state this explicitly to the user.
4. If a visualization chart payload is present, explain what the chart depicts (metrics, axes, trends, or anomalies).
5. Structure your output clearly into:
   - **Executive Summary**: Direct answer to the user's query.
   - **Key Findings & Evidence**: Specific metrics, timestamps, services, and failure modes retrieved.
   - **Visualization Insight** (if applicable): Explanation of the attached chart.
   - **Recommendations / Next Steps**: Actionable operational guidance grounded in the data.
"""

    def __init__(self, api_key: Optional[str] = None) -> None:
        """
        Initialize SynthesisNode with API key.

        Args:
            api_key (Optional[str]): Gemini API key. If omitted, reads from environment.
        """
        self.api_key = (
            api_key
            or os.environ.get("GEMINI_API_KEY")
            or os.environ.get("OPENROUTER_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
        )
        if not self.api_key:
            logger.warning("SynthesisNode: No API key found in environment.")

    def synthesize(
        self,
        user_query: str,
        retrieved_data: Dict[str, Any],
        retrieval_metadata: Dict[str, Any],
        visualization_payload: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Invokes LLM (Gemini 2.5 Flash) to synthesize response.

        Args:
            user_query (str): Raw user query text.
            retrieved_data (Dict[str, Any]): Grounding data dictionary.
            retrieval_metadata (Dict[str, Any]): Metadata on query execution.
            visualization_payload (Optional[Dict[str, Any]]): Base64 chart payload if present.

        Returns:
            str: Synthesized natural language response.
        """
        if not self.api_key:
            logger.error("SynthesisNode: Cannot invoke LLM synthesis without API Key.")
            return self._fallback_synthesis(user_query, retrieved_data, visualization_payload)

        # Prepare context payload for LLM
        has_chart = (
            visualization_payload is not None
            and visualization_payload.get("base64_image") is not None
        )
        chart_info = {
            "has_chart": has_chart,
            "chart_type": visualization_payload.get("chart_type") if has_chart else None,
            "title": visualization_payload.get("title") if has_chart else None,
            "x_axis": visualization_payload.get("x_axis") if has_chart else None,
            "y_axis": visualization_payload.get("y_axis") if has_chart else None
        } if visualization_payload else {"has_chart": False}

        prompt_context = f"""
{self.SYSTEM_PROMPT}

User Query: "{user_query}"

Retrieval Metadata:
{json.dumps(retrieval_metadata, indent=2)}

Visualization Info:
{json.dumps(chart_info, indent=2)}

Retrieved Persistence Data:
{json.dumps(retrieved_data, indent=2, default=str)}
"""

        try:
            # 1. Try google.generativeai
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                model = genai.GenerativeModel("gemini-2.5-flash")
                response = model.generate_content(prompt_context)
                return response.text
            except Exception as google_err:
                logger.debug(f"Direct google.generativeai failed ({google_err}), trying REST fallback...")

                # 2. HTTP REST Fallback (OpenRouter or direct Gemini API)
                import urllib.request
                if self.api_key.startswith("sk-or-v1"):
                    url = "https://openrouter.ai/api/v1/chat/completions"
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "model": "google/gemini-2.5-flash",
                        "messages": [
                            {"role": "system", "content": self.SYSTEM_PROMPT},
                            {"role": "user", "content": prompt_context}
                        ],
                        "temperature": 0.2
                    }
                else:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"
                    headers = {"Content-Type": "application/json"}
                    payload = {
                        "contents": [{"parts": [{"text": prompt_context}]}]
                    }

                req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
                with urllib.request.urlopen(req, timeout=20) as resp:
                    resp_data = json.loads(resp.read().decode('utf-8'))
                    if "choices" in resp_data:
                        return resp_data["choices"][0]["message"]["content"]
                    else:
                        return resp_data["candidates"][0]["content"]["parts"][0]["text"]

        except Exception as e:
            logger.error(f"SynthesisNode: LLM invocation failed ({e}). Using deterministic fallback.")
            return self._fallback_synthesis(user_query, retrieved_data, visualization_payload)

    def _fallback_synthesis(
        self,
        user_query: str,
        retrieved_data: Dict[str, Any],
        visualization_payload: Optional[Dict[str, Any]]
    ) -> str:
        """Deterministic rule-based summary generator if LLM endpoint is unreachable."""
        sections = [f"### Query Analysis: '{user_query}'\n"]

        total_records = 0
        for category, rows in retrieved_data.items():
            if isinstance(rows, list):
                count = len(rows)
                total_records += count
                sections.append(f"- **{category.title()}**: Retrieved {count} record(s).")
                if count > 0:
                    sample = rows[0]
                    sections.append(f"  - Sample Record: {json.dumps(sample, default=str)}")

        if visualization_payload and visualization_payload.get("base64_image"):
            title = visualization_payload.get("title", "Chart")
            chart_type = visualization_payload.get("chart_type", "line")
            sections.append(f"\n- **Visualization**: Generated a {chart_type} chart titled '{title}'.")

        sections.append(f"\n**Total Data Points Retrieved**: {total_records}")
        return "\n".join(sections)

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        LangGraph node entry point.

        Args:
            state (Dict[str, Any]): QueryState dictionary.

        Returns:
            Dict[str, Any]: Updated QueryState dictionary.
        """
        user_query = state.get("user_query", "")
        retrieved_data = state.get("retrieved_data", {})
        retrieval_metadata = state.get("retrieval_metadata", {})
        visualization_payload = state.get("visualization_payload")

        logger.info(f"SynthesisNode: Synthesizing natural language answer for query: '{user_query}'")
        answer = self.synthesize(user_query, retrieved_data, retrieval_metadata, visualization_payload)

        updated_state = dict(state)
        updated_state["synthesized_answer"] = answer
        updated_state["synthesis_completed"] = True
        return updated_state


def run_synthesis(state: Dict[str, Any]) -> Dict[str, Any]:
    """Functional wrapper for Synthesis Node execution."""
    node = SynthesisNode()
    return node.execute(state)
