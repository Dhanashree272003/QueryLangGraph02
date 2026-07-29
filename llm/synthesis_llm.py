"""
Synthesis LLM Interface for Query LangGraph (querylanggraph02).

Provides dedicated LLM interface wrapper for natural language response synthesis using Gemini 2.5 Flash.
"""

from typing import Dict, Any, Optional
from nodes.synthesis import SynthesisNode


class SynthesisLLMInterface:
    """LLM interface wrapper for response synthesis."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.node = SynthesisNode(api_key=api_key)

    def synthesize_response(
        self,
        user_query: str,
        retrieved_data: Dict[str, Any],
        retrieval_metadata: Dict[str, Any],
        visualization_payload: Optional[Dict[str, Any]] = None
    ) -> str:
        """Synthesizes grounded natural language answer from database records."""
        return self.node.synthesize(user_query, retrieved_data, retrieval_metadata, visualization_payload)
