"""
Common Helper Functions for Query LangGraph (querylanggraph02).

Provides utility functions for datetime manipulation, dictionary sanitization,
JSON cleaning, and string formatting across the graph workflow.
"""

import re
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


def get_utc_timestamp() -> str:
    """Returns current ISO 8601 UTC timestamp string."""
    return datetime.now(timezone.utc).isoformat()


def sanitize_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively removes null values and empty dictionaries from a payload."""
    cleaned = {}
    for k, v in d.items():
        if isinstance(v, dict):
            sub = sanitize_dict(v)
            if sub:
                cleaned[k] = sub
        elif v is not None and v != "":
            cleaned[k] = v
    return cleaned


def extract_json_block(text: str) -> Optional[Dict[str, Any]]:
    """Extracts and parses JSON dictionary from text containing markdown or fences."""
    if not text:
        return None
    cleaned = text.strip()
    cleaned = re.sub(r"^```(json)?", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
        return None
