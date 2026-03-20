"""
LMS API client - calls the backend with Bearer token auth.

Usage:
    from services.api_client import ApiClient, ApiError
    client = ApiClient(base_url, api_key)
    items = await client.get_items()
"""

import httpx
from typing import Any


class ApiError(Exception):
    """Exception raised when the API request fails."""

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ApiClient:
    """Client for the LMS backend API."""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=30.0,  # Increased timeout for sync operations
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def _request(self, method: str, path: str) -> Any:
        """Make an API request with error handling."""
        try:
            response = await self._client.request(method, path)
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError as e:
            raise ApiError(
                f"connection refused ({self.base_url}). Check that the services are running."
            ) from e
        except httpx.HTTPStatusError as e:
            raise ApiError(
                f"HTTP {e.response.status_code} {e.response.reason_phrase}. "
                f"The backend service may be down."
            ) from e
        except httpx.TimeoutException:
            raise ApiError(
                f"request timed out ({self.base_url}). The backend may be overloaded."
            )
        except Exception as e:
            raise ApiError(f"unexpected error: {e}") from e

    async def get_items(self) -> list[dict[str, Any]]:
        """Get all items (labs and tasks) from the backend."""
        return await self._request("GET", "/items/")

    async def get_learners(self) -> list[dict[str, Any]]:
        """Get all enrolled learners."""
        return await self._request("GET", "/learners/")

    async def get_pass_rates(self, lab: str) -> list[dict[str, Any]]:
        """Get per-task pass rates for a specific lab."""
        return await self._request("GET", f"/analytics/pass-rates?lab={lab}")

    async def get_scores(self, lab: str) -> list[dict[str, Any]]:
        """Get score distribution for a specific lab."""
        return await self._request("GET", f"/analytics/scores?lab={lab}")

    async def get_timeline(self, lab: str) -> list[dict[str, Any]]:
        """Get submission timeline for a specific lab."""
        return await self._request("GET", f"/analytics/timeline?lab={lab}")

    async def get_groups(self, lab: str) -> list[dict[str, Any]]:
        """Get per-group performance for a specific lab."""
        return await self._request("GET", f"/analytics/groups?lab={lab}")

    async def get_top_learners(self, lab: str, limit: int = 5) -> list[dict[str, Any]]:
        """Get top N learners for a specific lab."""
        return await self._request(
            "GET", f"/analytics/top-learners?lab={lab}&limit={limit}"
        )

    async def get_completion_rate(self, lab: str) -> dict[str, Any]:
        """Get completion percentage for a specific lab."""
        return await self._request("GET", f"/analytics/completion-rate?lab={lab}")

    async def sync_pipeline(self) -> dict[str, Any]:
        """Trigger ETL sync."""
        return await self._request("POST", "/pipeline/sync")
