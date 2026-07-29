"""
Base64 Encoding Utilities for Query LangGraph (querylanggraph02).

Provides helper methods for encoding and decoding binary images and data buffers
to/from Base64 strings.
"""

import base64
from typing import Optional


def bytes_to_base64(data: bytes) -> str:
    """Converts raw bytes to Base64 encoded UTF-8 string."""
    if not data:
        return ""
    return base64.b64encode(data).decode("utf-8")


def base64_to_bytes(encoded_str: str) -> bytes:
    """Converts Base64 string back to raw bytes."""
    if not encoded_str:
        return b""
    return base64.b64decode(encoded_str.encode("utf-8"))


def format_data_uri(base64_str: str, mime_type: str = "image/png") -> str:
    """Formats raw Base64 string into an HTML image data URI."""
    if not base64_str:
        return ""
    return f"data:{mime_type};base64,{base64_str}"
