"""Central registry for discovering, registering, and retrieving personas."""
from __future__ import annotations

import logging
from typing import Dict, List, Optional
from brain_core.personas.base import BasePersona
from brain_core.types import PersonaConfig

logger = logging.getLogger("BrainCore.Registry")


class PersonaRegistry:
    """Registry maintaining active persona cognition units."""

    def __init__(self) -> None:
        self._personas: Dict[str, BasePersona] = {}
        self._alias_map: Dict[str, str] = {}

    def register(self, persona: BasePersona, aliases: Optional[List[str]] = None) -> None:
        """Register a persona instance with optional name aliases."""
        self._personas[persona.id] = persona
        self._alias_map[persona.id.lower()] = persona.id
        self._alias_map[persona.name.lower()] = persona.id
        if aliases:
            for alias in aliases:
                self._alias_map[alias.lower()] = persona.id
        logger.debug(f"Registered persona: {persona.id} ({persona.name})")

    def register_config(self, config: PersonaConfig, aliases: Optional[List[str]] = None) -> BasePersona:
        """Register directly from a PersonaConfig object."""
        persona = BasePersona(config)
        self.register(persona, aliases)
        return persona

    def get(self, identifier: str) -> Optional[BasePersona]:
        """Lookup a persona by ID, exact name, or alias."""
        norm = identifier.lower().strip()
        target_id = self._alias_map.get(norm, identifier)
        return self._personas.get(target_id)

    def list_personas(self) -> List[BasePersona]:
        """Return all registered personas."""
        return list(self._personas.values())

    def unregister(self, identifier: str) -> bool:
        """Unregister a persona by ID."""
        persona = self.get(identifier)
        if persona and persona.id in self._personas:
            del self._personas[persona.id]
            # Clean up aliases pointing to this persona
            to_del = [k for k, v in self._alias_map.items() if v == persona.id]
            for k in to_del:
                del self._alias_map[k]
            return True
        return False
