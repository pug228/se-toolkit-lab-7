"""
Command handlers for slash commands - now with real backend data.

Each handler is a pure function: takes input string, returns response string.
No Telegram dependencies here - same function works from --test, tests, or Telegram.
"""

import asyncio
from typing import Any

from services.api_client import ApiClient, ApiError
from config import load_config


def _get_client() -> ApiClient:
    """Create an API client from config."""
    config = load_config()
    return ApiClient(config.lms_api_url, config.lms_api_key)


def handle_start(user_input: str = "") -> str:
    """Handle /start command - welcome message."""
    return "Welcome! I'm your LMS assistant bot. Use /help to see available commands."


def handle_help(user_input: str = "") -> str:
    """Handle /help command - list available commands."""
    return """Available commands:
/start - Welcome message
/help - Show this help
/health - Check backend status
/labs - List available labs
/scores <lab> - Show scores for a lab"""


async def _handle_health_async() -> str:
    """Async implementation of health check."""
    client = _get_client()
    try:
        items = await client.get_items()
        item_count = len(items) if isinstance(items, list) else 0
        return f"Backend is healthy. {item_count} items available."
    except ApiError as e:
        return f"Backend error: {e.message}"
    finally:
        await client.close()


def handle_health(user_input: str = "") -> str:
    """Handle /health command - backend status check."""
    return asyncio.run(_handle_health_async())


def _format_lab_name(item: dict[str, Any]) -> str:
    """Format a lab item for display."""
    lab_id = item.get("id", "unknown")
    lab_title = item.get("title", item.get("name", "Unknown Lab"))
    return f"- Lab {lab_id} — {lab_title}"


async def _handle_labs_async() -> str:
    """Async implementation of labs listing."""
    client = _get_client()
    try:
        items = await client.get_items()
        if not items:
            return "No labs available."

        # Filter for labs (not tasks)
        labs = [item for item in items if item.get("type") == "lab"]

        if not labs:
            # If no type field, assume all items are labs
            labs = items

        lines = ["Available labs:"]
        for lab in labs:
            lines.append(_format_lab_name(lab))
        return "\n".join(lines)
    except ApiError as e:
        return f"Backend error: {e.message}"
    finally:
        await client.close()


def handle_labs(user_input: str = "") -> str:
    """Handle /labs command - list available labs."""
    return asyncio.run(_handle_labs_async())


async def _handle_scores_async(lab: str) -> str:
    """Async implementation of scores lookup."""
    if not lab:
        return "Please specify a lab, e.g., /scores lab-04"

    client = _get_client()
    try:
        pass_rates = await client.get_pass_rates(lab)

        if not pass_rates:
            return f"No scores found for {lab}. Check the lab ID."

        lines = [f"Pass rates for {lab}:"]
        for task in pass_rates:
            task_name = task.get("task", "Unknown Task")
            avg_score = task.get("avg_score", 0)
            attempts = task.get("attempts", 0)
            # Format as percentage
            percentage = (
                f"{avg_score:.1f}%"
                if isinstance(avg_score, (int, float))
                else str(avg_score)
            )
            lines.append(f"- {task_name}: {percentage} ({attempts} attempts)")

        return "\n".join(lines)
    except ApiError as e:
        return f"Backend error: {e.message}"
    finally:
        await client.close()


def handle_scores(user_input: str = "") -> str:
    """Handle /scores command - show scores for a lab."""
    return asyncio.run(_handle_scores_async(user_input.strip()))
