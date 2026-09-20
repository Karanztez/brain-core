"""Multi-model provider router with failover."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import httpx

logger = logging.getLogger("BrainCore.Providers")


@dataclass
class ProviderEndpoint:
    name: str
    base_url: str
    api_key: str
    model: str
    weight: int = 1
    is_active: bool = True


class MultiProviderRouter:
    """Manages AI model pools and executes requests with automatic failover."""

    def __init__(self, endpoints: Optional[List[ProviderEndpoint]] = None) -> None:
        self.endpoints = endpoints or []

    def add_endpoint(self, endpoint: ProviderEndpoint) -> None:
        self.endpoints.append(endpoint)

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1500,
        preferred_pool: str = "",
        model_override: str = "",
        model_tier: str = "medium",
    ) -> Optional[str]:
        """Execute chat completion across active endpoints with automatic failover."""
        candidates = [ep for ep in self.endpoints if ep.is_active]
        if preferred_pool:
            candidates.sort(key=lambda ep: 0 if ep.name == preferred_pool else 1)

        for ep in candidates:
            target_model = model_override or ep.model
            try:
                headers = {
                    "Authorization": f"Bearer {ep.api_key}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": target_model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(f"{ep.base_url.rstrip('/')}/chat/completions", headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        return data["choices"][0]["message"].get("content", "")
                    logger.warning(f"Endpoint {ep.name} (model: {target_model}) returned HTTP {resp.status_code}")
            except Exception as err:
                logger.warning(f"Endpoint {ep.name} call failed: {err}")
                continue

        return None

