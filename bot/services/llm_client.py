"""
LLM client with tool calling support.

Usage:
    from services.llm_client import LlmClient
    client = LlmClient(api_key, base_url, model)
    response = await client.chat_with_tools("what labs are available?", tools)
"""

import json
import sys
import httpx
from typing import Any


# Tool definitions for all 9 backend endpoints
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_items",
            "description": "Get list of all labs and tasks. Use this to discover what labs are available.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_learners",
            "description": "Get list of enrolled students and groups. Use for questions about enrollment or student count.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_scores",
            "description": "Get score distribution (4 buckets) for a specific lab.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier, e.g. 'lab-01', 'lab-04'",
                    }
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_pass_rates",
            "description": "Get per-task average scores and attempt counts for a specific lab. Use for comparing task difficulty.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier, e.g. 'lab-01', 'lab-04'",
                    }
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_timeline",
            "description": "Get submissions per day for a specific lab. Use for activity trends.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier, e.g. 'lab-01', 'lab-04'",
                    }
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_groups",
            "description": "Get per-group scores and student counts for a specific lab. Use for comparing group performance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier, e.g. 'lab-01', 'lab-04'",
                    }
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_learners",
            "description": "Get top N learners by score for a specific lab. Use for leaderboards.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier, e.g. 'lab-01', 'lab-04'",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of top learners to return, default 5",
                    },
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_completion_rate",
            "description": "Get completion rate percentage for a specific lab.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {
                        "type": "string",
                        "description": "Lab identifier, e.g. 'lab-01', 'lab-04'",
                    }
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "trigger_sync",
            "description": "Trigger ETL sync to refresh data from autochecker. Use when data seems stale.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]

# System prompt for the LLM
SYSTEM_PROMPT = """You are an LMS assistant helping users query learning management data.

You have access to tools that fetch data from the LMS backend. When a user asks a question:
1. Think about what data you need to answer
2. Call the appropriate tools with the right parameters
3. Once you have the data, summarize it clearly for the user

For multi-step questions (e.g., "which lab has the lowest pass rate?"):
1. First get the list of labs
2. Then get pass rates for each lab
3. Compare and report the lowest

Be concise but informative. Include specific numbers when available.

If the user's message is a greeting or unclear, respond helpfully without calling tools.
"""


class LlmError(Exception):
    """Exception raised when LLM request fails."""

    pass


class LlmClient:
    """Client for LLM with tool calling support."""

    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def chat_with_tools(
        self, user_message: str, tools: list[dict[str, Any]]
    ) -> str:
        """
        Chat with the LLM using tool calling.

        Handles the full loop: send message → get tool calls → execute → feed back → get final answer.

        Args:
            user_message: The user's question or message
            tools: List of tool definitions (OpenAI format)

        Returns:
            The LLM's final response
        """
        # Build conversation messages
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]

        # Main tool calling loop (max 8 iterations to allow for multi-step queries)
        max_iterations = 8
        for iteration in range(max_iterations):
            # Call LLM
            response = await self._call_llm(messages, tools)

            # Check if LLM wants to call tools
            tool_calls = response.get("tool_calls", [])

            if not tool_calls:
                # No tool calls - LLM has final answer
                return response.get(
                    "content", "I don't have enough information to answer that."
                )

            # Execute tool calls and collect results
            tool_results = []
            for tool_call in tool_calls:
                function_name = tool_call["function"]["name"]
                function_args = json.loads(tool_call["function"]["arguments"])

                # Debug logging
                print(
                    f"[tool] LLM called: {function_name}({function_args})",
                    file=sys.stderr,
                )

                # Execute the tool
                result = await self._execute_tool(function_name, function_args)

                # Debug logging for result
                if isinstance(result, list):
                    print(f"[tool] Result: {len(result)} items", file=sys.stderr)
                elif isinstance(result, dict):
                    print(f"[tool] Result: {len(result)} keys", file=sys.stderr)
                else:
                    print(f"[tool] Result: {result}", file=sys.stderr)

                tool_results.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": json.dumps(result)
                        if not isinstance(result, str)
                        else result,
                    }
                )

            # Debug logging
            print(
                f"[summary] Feeding {len(tool_results)} tool result(s) back to LLM",
                file=sys.stderr,
            )

            # Add assistant message with tool calls to conversation
            messages.append(
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": tool_calls,
                }
            )

            # Add tool results to conversation
            messages.extend(tool_results)

        # If we get here, we hit max iterations
        return "I'm having trouble answering this question. Please try rephrasing."

    async def _call_llm(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Make a single LLM call with tool support."""
        payload = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
        }

        try:
            response = await self._client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]
        except httpx.HTTPStatusError as e:
            raise LlmError(f"LLM error: HTTP {e.response.status_code}") from e
        except Exception as e:
            raise LlmError(f"LLM error: {e}") from e

    async def _execute_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Execute a tool by calling the appropriate backend endpoint."""
        from services.api_client import ApiClient, ApiError
        from config import load_config

        config = load_config()
        client = ApiClient(config.lms_api_url, config.lms_api_key)

        try:
            if name == "get_items":
                return await client.get_items()
            elif name == "get_learners":
                return await client.get_learners()
            elif name == "get_scores":
                return await client.get_scores(arguments.get("lab", ""))
            elif name == "get_pass_rates":
                return await client.get_pass_rates(arguments.get("lab", ""))
            elif name == "get_timeline":
                return await client.get_timeline(arguments.get("lab", ""))
            elif name == "get_groups":
                return await client.get_groups(arguments.get("lab", ""))
            elif name == "get_top_learners":
                return await client.get_top_learners(
                    arguments.get("lab", ""), arguments.get("limit", 5)
                )
            elif name == "get_completion_rate":
                return await client.get_completion_rate(arguments.get("lab", ""))
            elif name == "trigger_sync":
                return await client.sync_pipeline()
            else:
                return {"error": f"Unknown tool: {name}"}
        except ApiError as e:
            # Return error message to LLM so it can inform the user
            return {"error": str(e)}
        finally:
            await client.close()
