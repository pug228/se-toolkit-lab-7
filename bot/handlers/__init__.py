"""
Command handlers - pure functions with no Telegram dependency.

These handlers take input and return text. They can be called from:
- --test mode (direct function calls)
- Unit tests
- Telegram bot (via aiogram or python-telegram-bot)
"""

from .commands import (
    handle_start,
    handle_help,
    handle_health,
    handle_labs,
    handle_scores,
    handle_health_async,
    handle_labs_async,
    handle_scores_async,
)

__all__ = [
    "handle_start",
    "handle_help",
    "handle_health",
    "handle_labs",
    "handle_scores",
    "handle_health_async",
    "handle_labs_async",
    "handle_scores_async",
]
