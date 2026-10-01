"""Centralized logging service using standard logging with optional rich formatting."""

import logging
import sys
from pathlib import Path

def get_logger(name: str = "pyinspect") -> logging.Logger:
    """Returns a configured logger instance for the given module name."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

logger = get_logger()
