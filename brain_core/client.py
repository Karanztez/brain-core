"""Brain-Core API Client.

Allows any bot or service to interact with Brain-Core API over HTTP.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
import httpx


class BrainClient:
    """Synchronous & Asynchronous REST Client for Brain-Core API."""

    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    # -------------------------------------------------------------
    # Synchronous Methods
    # -------------------------------------------------------------

    def health(self) -> Dict[str, Any]:
        """Check API service health."""
        with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
            resp = client.get("/health")
            resp.raise_for_status()
            return resp.json()

    def list_personas(self) -> List[Dict[str, Any]]:
        """List all registered personas."""
        with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
            resp = client.get("/personas")
            resp.raise_for_status()
            return resp.json()

    def decide(
        self,
        persona_id: str,
        prompt: str,
        channel_id: Optional[str] = None,
        allow_web: bool = True,
    ) -> Dict[str, Any]:
        """Evaluate intent and tool routing for a persona prompt."""
        payload = {
            "persona_id": persona_id,
            "prompt": prompt,
            "channel_id": channel_id,
            "allow_web": allow_web,
        }
        with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
            resp = client.post("/decide", json=payload)
            resp.raise_for_status()
            return resp.json()

    def redact(self, text: str) -> Dict[str, Any]:
        """Redact sensitive platform/model tokens from text."""
        with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
            resp = client.post("/redact", json={"text": text})
            resp.raise_for_status()
            return resp.json()

    def neural_activate(
        self,
        cues: List[str],
        trunk_filters: Optional[List[str]] = None,
        max_hops: int = 2,
    ) -> Dict[str, Any]:
        """Trigger spreading activation across neural trunks."""
        payload = {
            "cues": cues,
            "trunk_filters": trunk_filters,
            "max_hops": max_hops,
        }
        with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
            resp = client.post("/neural/activate", json=payload)
            resp.raise_for_status()
            return resp.json()

    def neural_grow(
        self,
        trunk: str,
        content: str,
        tags: Optional[List[str]] = None,
        baseline_weight: float = 1.0,
    ) -> Dict[str, Any]:
        """Grow a new neuron in the cortex."""
        payload = {
            "trunk": trunk,
            "content": content,
            "tags": tags or [],
            "baseline_weight": baseline_weight,
        }
        with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
            resp = client.post("/neural/grow", json=payload)
            resp.raise_for_status()
            return resp.json()

    def neural_connect(
        self,
        source_id: str,
        target_id: str,
        weight: float = 1.0,
        relation: str = "associated_with",
        bidirectional: bool = True,
    ) -> Dict[str, Any]:
        """Connect two neurons with a synapse."""
        payload = {
            "source_id": source_id,
            "target_id": target_id,
            "weight": weight,
            "relation": relation,
            "bidirectional": bidirectional,
        }
        with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
            resp = client.post("/neural/connect", json=payload)
            resp.raise_for_status()
            return resp.json()

    def neural_correct(self, neuron_id: str, corrected_content: str) -> Dict[str, Any]:
        """Apply cognitive correction to an existing neuron."""
        payload = {
            "neuron_id": neuron_id,
            "corrected_content": corrected_content,
        }
        with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
            resp = client.post("/neural/correct", json=payload)
            resp.raise_for_status()
            return resp.json()

    def neural_state(self) -> Dict[str, Any]:
        """Export the full cortex neural state."""
        with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
            resp = client.get("/neural/state")
            resp.raise_for_status()
            return resp.json()

    # -------------------------------------------------------------
    # Asynchronous Methods (for Discord bot asyncio loops)
    # -------------------------------------------------------------

    async def a_decide(
        self,
        persona_id: str,
        prompt: str,
        channel_id: Optional[str] = None,
        allow_web: bool = True,
    ) -> Dict[str, Any]:
        """Async evaluate intent and tool routing."""
        payload = {
            "persona_id": persona_id,
            "prompt": prompt,
            "channel_id": channel_id,
            "allow_web": allow_web,
        }
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            resp = await client.post("/decide", json=payload)
            resp.raise_for_status()
            return resp.json()

    async def a_neural_activate(
        self,
        cues: List[str],
        trunk_filters: Optional[List[str]] = None,
        max_hops: int = 2,
    ) -> Dict[str, Any]:
        """Async trigger spreading activation across neural trunks."""
        payload = {
            "cues": cues,
            "trunk_filters": trunk_filters,
            "max_hops": max_hops,
        }
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            resp = await client.post("/neural/activate", json=payload)
            resp.raise_for_status()
            return resp.json()

    async def a_redact(self, text: str) -> Dict[str, Any]:
        """Async redact sensitive platform/model tokens from text."""
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            resp = await client.post("/redact", json={"text": text})
            resp.raise_for_status()
            return resp.json()
