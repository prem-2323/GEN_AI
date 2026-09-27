"""Centralized logging configuration."""
from __future__ import annotations

import logging
import os
import sys

# Silence third-party warnings in environment
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Initialize structured application logging."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure root logger format if not already configured
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
        force=True,
    )
    
    # Silence overly verbose external libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("pypdf").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    logging.getLogger("datasets").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    logger = logging.getLogger("gen-transform")
    logger.setLevel(level)
    return logger


def get_logger(name: str) -> logging.Logger:
    """Obtain a namespaced child logger."""
    if name.startswith("gen-transform"):
        return logging.getLogger(name)
    return logging.getLogger(f"gen-transform.{name}")
