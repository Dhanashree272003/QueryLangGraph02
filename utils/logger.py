"""
Centralized Application Logging Module for Query LangGraph (querylanggraph02).

Configures structured logging across all workflow nodes, guardrails, services, and routers.
"""

import sys
import logging
from typing import Optional


def setup_logger(
    name: str = "QueryLangGraph",
    level: str = "INFO",
    log_format: Optional[str] = None
) -> logging.Logger:
    """
    Configures and returns a logger instance.

    Args:
        name (str): Logger name namespace.
        level (str): Logging level (DEBUG, INFO, WARNING, ERROR).
        log_format (Optional[str]): Custom log line format string.

    Returns:
        logging.Logger: Configured logger object.
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        fmt = log_format or "%(asctime)s - [%(name)s] - %(levelname)s - %(message)s"
        formatter = logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


# Primary logger instance
logger = setup_logger()
