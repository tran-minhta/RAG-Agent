"""
RAG-ALL: Structured Logging
Centralized logging configuration for all services.
"""

import logging
import sys
from pathlib import Path


def setup_logger(
    name: str,
    level: str = "INFO",
    log_file: str | None = None,
) -> logging.Logger:
    """
    Tạo structured logger cho service.

    Args:
        name: Tên service/logger (e.g., "gateway", "agent", "rag")
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file path để ghi log

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # === Console Handler ===
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    # Format: [TIMESTAMP] [LEVEL] [SERVICE] message
    console_format = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-12s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # === File Handler (optional) ===
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)

        file_format = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)-12s | %(funcName)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    return logger


# === Pre-configured loggers for each service ===
gateway_logger = setup_logger("gateway", log_file="data/logs/gateway.log")
agent_logger = setup_logger("agent", log_file="data/logs/agent.log")
rag_logger = setup_logger("rag", log_file="data/logs/rag.log")
document_logger = setup_logger("document", log_file="data/logs/document.log")
research_logger = setup_logger("research", log_file="data/logs/research.log")
editor_logger = setup_logger("editor", log_file="data/logs/editor.log")
voice_logger = setup_logger("voice", log_file="data/logs/voice.log")
