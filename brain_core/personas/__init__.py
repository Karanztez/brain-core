"""Personas module for Brain-Core."""
from brain_core.personas.base import BasePersona
from brain_core.personas.registry import PersonaRegistry
from brain_core.personas.presets.emi import EMI_CONFIG
from brain_core.personas.presets.bo import BO_CONFIG

__all__ = ["BasePersona", "PersonaRegistry", "EMI_CONFIG", "BO_CONFIG"]
