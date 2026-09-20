"""Data contracts, enums, and models for Brain-Core."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class IntentType(str, Enum):
    """Categorized intent for persona decision engine."""
    CHAT = "chat"          # Normal conversation, roleplay, chitchat, advice, humor
    RESEARCH = "research"  # Realtime web search, live data, viral events, news
    TEACH = "teach"        # Teaching facts, user preferences, permanent skills
    DECODE = "decode"      # Data decoding (Base64, Hex, Cipher, CTF, multiplexed streams)
    MODERATE = "moderate"  # Anti-scam, toxicity inspection, rule enforcement
    TASK = "task"          # Explicit instructions, code generation, step-by-step guidance
    CODE_REVIEW = "code_review"  # AI code review using Alibaba Open Code Review (OCR)


class PersonaGender(str, Enum):
    FEMALE = "female"
    MALE = "male"
    NEUTRAL = "neutral"


@dataclass
class PersonaConfig:
    """Configuration defining a persona's distinct identity and cognitive boundaries."""
    id: str
    name: str
    title: str = ""
    gender: PersonaGender = PersonaGender.NEUTRAL
    system_prompt: str = ""
    greeting: str = ""
    empty_fallback: str = ""
    error_fallback: str = ""
    timeout_fallback: str = ""
    rate_limit_fallback: str = ""
    allowed_tools: List[str] = field(default_factory=list)
    forbidden_terms: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BrainDecision:
    """Outcome of the reasoning step determining intent, tools, and guided context."""
    persona_id: str
    intent: IntentType
    should_search: bool = False
    query: str = ""
    allow_tools: bool = False
    allowed_tools: List[str] = field(default_factory=list)
    skill_context: str = ""
    reasoning: str = ""
    model_tier: str = "medium"  # "low" (Lite/1s), "medium" (Flash/2s), "deep" (Reasoning/Co-Thinker)
    model_override: str = ""


@dataclass
class ChannelActivityTurn:
    """Turn in the shared channel awareness buffer across all agents/bots."""
    author: str
    bot_scope: str
    prompt: str
    reply: str
    timestamp: float = 0.0


@dataclass
class ChatMessage:
    """Standardized chat message."""
    role: str
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
