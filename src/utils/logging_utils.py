"""Logging helpers for the Composio Tool Router demo."""
from __future__ import annotations

import logging
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler

_RICH_HANDLER: Optional[RichHandler] = None


def configure_logging(level: int | str = logging.INFO) -> None:
    """Configure global logging with Rich formatting."""
    global _RICH_HANDLER
    if _RICH_HANDLER is not None:
        return
    handler = RichHandler(console=Console(), show_path=False, rich_tracebacks=True)
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[handler],
    )
    _RICH_HANDLER = handler


def get_logger(name: str) -> logging.Logger:
    """Return a module-scoped logger, ensuring Rich is configured."""
    if _RICH_HANDLER is None:
        configure_logging()
    return logging.getLogger(name)
