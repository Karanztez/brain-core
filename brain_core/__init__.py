"""Brain-Core: Multi-Persona AI Cognition & Reasoning Engine."""
from __future__ import annotations

from brain_core.types import (
    IntentType,
    BrainDecision,
    PersonaConfig,
    PersonaGender,
    ChatMessage,
    ChannelActivityTurn,
)
from brain_core.personas.base import BasePersona
from brain_core.personas.registry import PersonaRegistry
from brain_core.personas.presets.emi import EMI_CONFIG
from brain_core.personas.presets.bo import BO_CONFIG
from brain_core.reasoning.brain import PersonaBrain
from brain_core.reasoning.evaluator import TurnEvaluator
from brain_core.memory.buffer import ChannelContextBuffer
from brain_core.memory.conversation import SessionMemory
from brain_core.memory.graph import CognitiveKnowledgeGraph
from brain_core.tools.router import PersonaToolRouter
from brain_core.security.redactor import ZeroLeakRedactor
from brain_core.providers.fallbacks import PersonaFallbackManager
from brain_core.providers.router import MultiProviderRouter, ProviderEndpoint

__version__ = "0.1.0"

__all__ = [
    "IntentType",
    "BrainDecision",
    "PersonaConfig",
    "PersonaGender",
    "ChatMessage",
    "ChannelActivityTurn",
    "BasePersona",
    "PersonaRegistry",
    "EMI_CONFIG",
    "BO_CONFIG",
    "PersonaBrain",
    "TurnEvaluator",
    "ChannelContextBuffer",
    "SessionMemory",
    "CognitiveKnowledgeGraph",
    "PersonaToolRouter",
    "ZeroLeakRedactor",
    "PersonaFallbackManager",
    "MultiProviderRouter",
    "ProviderEndpoint",
]
