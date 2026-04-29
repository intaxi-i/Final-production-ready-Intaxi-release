from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(slots=True)
class BotApiClient:
    base_url: str
    service_token: str | None = None

    def _headers(self, user_token: str | None = None) -> dict[str, str]:
        token = user_token or self.service_token
        return {"Authorization": f"Bearer {token}"} if token else {}

    async def get_current_city_trip(self, user_token: str) -> dict[str, Any]:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=15) as client:
            response = await client.get("/api/v2/city/trips/current", headers=self._headers(user_token))
            response.raise_for_status()
            return response.json()

    async def accept_city_order(self, order_id: int, user_token: str) -> dict[str, Any]:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=15) as client:
            response = await client.post(f"/api/v2/city/orders/{order_id}/accept", headers=self._headers(user_token))
            response.raise_for_status()
            return response.json()

    async def create_counteroffer(self, order_id: int, price: float, user_token: str) -> dict[str, Any]:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=15) as client:
            response = await client.post(
                f"/api/v2/city/orders/{order_id}/counteroffers",
                json={"price": price},
                headers=self._headers(user_token),
            )
            response.raise_for_status()
            return response.json()

    async def update_city_trip_status(self, trip_id: int, status: str, user_token: str) -> dict[str, Any]:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=15) as client:
            response = await client.post(
                f"/api/v2/city/trips/{trip_id}/status",
                json={"status": status},
                headers=self._headers(user_token),
            )
            response.raise_for_status()
            return response.json()
