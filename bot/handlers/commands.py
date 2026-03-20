"""
Command handlers for slash commands - with real backend data.

Each handler is a pure function: takes input string, returns response string.
No Telegram dependencies here - same function works from --test, tests, or Telegram.

The handlers use asyncio to call the async API client. They work in both:
- Sync context (--test mode): uses asyncio.run()
- Async context (Telegram): uses await directly via async versions
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


async def handle_health_async(user_input: str = "") -> str:
    """Async health check - for use in Telegram handlers."""
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
    """Handle /health command - backend status check.

    Works in sync context (--test mode).
    For async context (Telegram), use handle_health_async().
    """
    try:
        loop = asyncio.get_running_loop()
        # We're in an async context - should use async version
        raise RuntimeError("no running event loop")
    except RuntimeError:
        # No running loop - safe to use asyncio.run()
        return asyncio.run(handle_health_async(user_input))


def _format_lab_name(item: dict[str, Any]) -> str:
    """Format a lab item for display."""
    lab_id = item.get("id", "unknown")
    lab_title = item.get("title", item.get("name", "Unknown Lab"))
    return f"- Lab {lab_id} — {lab_title}"


async def handle_labs_async(user_input: str = "") -> str:
    """Async labs listing - for use in Telegram handlers."""
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
    """Handle /labs command - list available labs.

    Works in sync context (--test mode).
    For async context (Telegram), use handle_labs_async().
    """
    try:
        loop = asyncio.get_running_loop()
        raise RuntimeError("no running event loop")
    except RuntimeError:
        return asyncio.run(handle_labs_async(user_input))


async def handle_scores_async(lab: str) -> str:
    """Async scores lookup - for use in Telegram handlers."""
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
    """Handle /scores command - show scores for a lab.

    Works in sync context (--test mode).
    For async context (Telegram), use handle_scores_async().
    """
    try:
        loop = asyncio.get_running_loop()
        raise RuntimeError("no running event loop")
    except RuntimeError:
        return asyncio.run(handle_scores_async(user_input.strip()))
