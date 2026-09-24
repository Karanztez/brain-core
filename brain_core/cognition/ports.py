"""Dependency-inversion ports owned by Brain-Core."""
from __future__ import annotations

from typing import Protocol

from brain_core.cognition.contracts import CognitiveRequest, MemoryContext, ModelRequest


class ModelGateway(Protocol):
    """A model only performs inference; it never owns memory policy."""

    async def generate(self, request: ModelRequest) -> str:
        ...


class MemoryStore(Protocol):
    """Database-neutral durable memory operations required by the brain."""

    async def recall(self, request: CognitiveRequest, limit: int = 12) -> MemoryContext:
        ...

    async def save_turn(self, request: CognitiveRequest, response: str) -> None:
        ...

    async def remember_fact(self, request: CognitiveRequest, fact: str) -> None:
        ...

    async def health(self) -> dict:
        ...
