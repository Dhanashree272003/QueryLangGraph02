"""
Parse LLM Interface for Query LangGraph (querylanggraph02).

Provides dedicated LLM interface wrapper for Query Intent parsing using Gemini 2.5 Flash.
"""

from typing import Dict, Any, Optional
from nodes.parse_query import ParseQueryNode


class ParseLLMInterface:
    """LLM interface wrapper for query parsing."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.node = ParseQueryNode(api_key=api_key)

    def parse_query(self, user_query: str) -> Dict[str, Any]:
        """Parses natural language query into structured QueryIntent dictionary."""
        return self.node.parse_with_llm(user_query)
