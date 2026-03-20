"""
Intent router - uses LLM to understand user messages and call appropriate tools.

Usage:
    from handlers.intent_router import route_intent
    response = await route_intent("what labs are available?")
"""

import asyncio
from typing import Any

from services.llm_client import LlmClient, LlmError, TOOLS
from config import load_config


def _get_llm_client() -> LlmClient:
    """Create an LLM client from config."""
    config = load_config()
    return LlmClient(config.llm_api_key, config.llm_api_base_url, config.llm_api_model)


async def route_intent_async(user_message: str) -> str:
    """
    Route a user message using the LLM.
    
    The LLM decides which tools to call based on the user's intent.
    Tool results are fed back to the LLM for the final answer.
    
    Args:
        user_message: The user's question or message
        
    Returns:
        The LLM's response
    """
    client = _get_llm_client()
    try:
        response = await client.chat_with_tools(user_message, TOOLS)
        return response
    except LlmError as e:
        return f"LLM error: {e}. Please try again later."
    finally:
        await client.close()


def route_intent(user_message: str) -> str:
    """
    Route a user message using the LLM (sync version for --test mode).
    
    For async context (Telegram), use route_intent_async().
    """
    try:
        loop = asyncio.get_running_loop()
        raise RuntimeError("no running event loop")
    except RuntimeError:
        return asyncio.run(route_intent_async(user_message))
