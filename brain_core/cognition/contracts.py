"""Stable contracts between the brain, model gateway, and memory store."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from brain_core.types import BrainDecision, ChatMessage


@dataclass(frozen=True)
class CognitiveRequest:
    """One thought request, isolated by tenant, persona, user, and channel."""

    persona_id: str
    user_id: str
    channel_id: str
    prompt: str
    tenant_id: str = "default"
    allow_web: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryContext:
    """Relevant memory retrieved before model inference."""

    messages: List[ChatMessage] = field(default_factory=list)
    facts: List[str] = field(default_factory=list)
    channel_context: str = ""


@dataclass
class ModelRequest:
    """Provider-neutral inference request produced by the brain."""

    messages: List[ChatMessage]
    decision: BrainDecision
    tenant_id: str
    persona_id: str
    user_id: str
    channel_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CognitiveResponse:
    """Auditable result of a complete cognitive cycle."""

    text: str
    decision: BrainDecision
    recalled_facts: List[str] = field(default_factory=list)
    memory_written: bool = False
    trace: List[str] = field(default_factory=list)
