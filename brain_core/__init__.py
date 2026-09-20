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
from brain_core.security.redactor import ZeroLeakRedactor, mask_sensitive_pii
from brain_core.security.honeypot import HoneypotVault, is_decoy_card
from brain_core.providers.fallbacks import PersonaFallbackManager
from brain_core.providers.router import MultiProviderRouter, ProviderEndpoint
from brain_core.neural.neuron import MajorTrunk, NeuronNode, SynapseEdge, ActivationResult
from brain_core.neural.cortex import NeuralCortex, create_standard_cortex
from brain_core.neural.activation import SpreadingActivation
from brain_core.neural.plasticity import SynapticPlasticity
from brain_core.client import BrainClient
from brain_core.tools.code_review import OpenCodeReviewTool
from brain_core.voice.tts import (
    clean_text_for_speech,
    generate_speech_bytes,
    generate_speech_file,
    VOICE_PROFILES,
)
from brain_core.voice.rvc import convert_to_anya_voice

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
    "OpenCodeReviewTool",
    "ZeroLeakRedactor",
    "mask_sensitive_pii",
    "HoneypotVault",
    "is_decoy_card",
    "PersonaFallbackManager",
    "MultiProviderRouter",
    "ProviderEndpoint",
    "MajorTrunk",
    "NeuronNode",
    "SynapseEdge",
    "ActivationResult",
    "NeuralCortex",
    "create_standard_cortex",
    "SpreadingActivation",
    "SynapticPlasticity",
    "BrainClient",
    "clean_text_for_speech",
    "generate_speech_bytes",
    "generate_speech_file",
    "VOICE_PROFILES",
    "convert_to_anya_voice",
]
