"""Tool registry and persona permission router."""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional
from brain_core.personas.base import BasePersona
from brain_core.tools.builtins.decoder import decode_inspect_data


class PersonaToolRouter:
    """Dispatches tool execution while enforcing persona boundaries."""

    def __init__(self) -> None:
        self._registry: Dict[str, Callable[..., Any]] = {
            "decode_inspect_data": decode_inspect_data,
        }

    def register_tool(self, name: str, func: Callable[..., Any]) -> None:
        """Register a new callable tool."""
        self._registry[name] = func

    def get_allowed_tools(self, persona: BasePersona) -> List[str]:
        """Return the list of registered tools permitted for this persona."""
        return [name for name in self._registry.keys() if persona.is_tool_allowed(name)]

    def execute(self, persona: BasePersona, tool_name: str, **kwargs: Any) -> Any:
        """Execute a tool if permitted for this persona."""
        if not persona.is_tool_allowed(tool_name):
            raise PermissionError(f"Persona '{persona.name}' ({persona.id}) is not permitted to use tool '{tool_name}'")
        if tool_name not in self._registry:
            raise KeyError(f"Tool '{tool_name}' is not registered in ToolRouter")
        return self._registry[tool_name](**kwargs)
