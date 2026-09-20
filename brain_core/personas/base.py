"""Base Persona abstraction and lifecycle management."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from brain_core.types import PersonaConfig, PersonaGender


class BasePersona:
    """Base class for any Persona running inside Brain-Core."""

    def __init__(self, config: PersonaConfig) -> None:
        self.config = config

    @property
    def id(self) -> str:
        return self.config.id

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def gender(self) -> PersonaGender:
        return self.config.gender

    def build_system_prompt(self, additional_context: str = "") -> str:
        """Construct the prompt grounding this persona's voice and constraints."""
        prompt = self.config.system_prompt
        if additional_context:
            prompt += f"\n\n[บริบทแวดล้อมเพิ่มเติม]:\n{additional_context}"
        return prompt

    def is_tool_allowed(self, tool_name: str) -> bool:
        """Check whether this persona is authorized to use a given tool."""
        if not self.config.allowed_tools:
            return True
        return tool_name in self.config.allowed_tools

    def get_fallback(self, fallback_type: str = "empty") -> str:
        """Return persona-authentic fallback text when an error or empty response occurs."""
        if fallback_type == "empty":
            return self.config.empty_fallback or "ไม่สามารถสร้างคำตอบได้ในขณะนี้"
        if fallback_type == "error":
            return self.config.error_fallback or "เกิดข้อผิดพลาดในการประมวลผล"
        if fallback_type == "timeout":
            return self.config.timeout_fallback or "การเชื่อมต่อหมดเวลา กรุณาลองใหม่อีกครั้ง"
        if fallback_type == "rate_limit":
            return self.config.rate_limit_fallback or "ระบบกำลังยุ่ง กรุณารอสักครู่"
        return self.config.empty_fallback
