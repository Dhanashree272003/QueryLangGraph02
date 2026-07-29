"""
LLM Output Parser for Query LangGraph (querylanggraph02).

Parses and validates raw LLM JSON text strings into validated Pydantic schemas.
"""

import json
import logging
from typing import Type, TypeVar, Optional
from pydantic import BaseModel

from utils.helpers import extract_json_block

logger = logging.getLogger("QueryLangGraph.LLM.OutputParser")

T = TypeVar("T", bound=BaseModel)


class LLMOutputParser:
    """Parses raw LLM output into structured Pydantic models."""

    @staticmethod
    def parse(raw_text: str, model_cls: Type[T]) -> Optional[T]:
        """
        Parses raw LLM text into a Pydantic model instance.

        Args:
            raw_text (str): Raw string output from LLM.
            model_cls (Type[T]): Target Pydantic model class.

        Returns:
            Optional[T]: Validated model instance or None on error.
        """
        json_dict = extract_json_block(raw_text)
        if not json_dict:
            logger.error("LLMOutputParser: Failed to extract valid JSON block.")
            return None

        try:
            return model_cls.model_validate(json_dict)
        except Exception as e:
            logger.error(f"LLMOutputParser: Pydantic model validation error: {e}")
            return None
