"""Persona-adaptive fallback responses."""
from __future__ import annotations

from brain_core.personas.base import BasePersona
from brain_core.types import PersonaGender


class PersonaFallbackManager:
    """Provides voice-consistent error and fallback responses."""

    @staticmethod
    def get_fallback(persona: BasePersona, error_type: str = "empty") -> str:
        """Fetch persona fallback text or generate a gender-appropriate default."""
        custom = persona.get_fallback(error_type)
        if custom:
            return custom

        is_male = persona.gender == PersonaGender.MALE
        is_female = persona.gender == PersonaGender.FEMALE

        if error_type == "empty":
            if is_male:
                return f"{persona.name}ยังไม่พบประเด็นสำคัญในข้อความนี้ครับคุณพี่"
            if is_female:
                return f"{persona.name}ยังสร้างคำตอบไม่ได้ค่ะ"
            return f"{persona.name}ไม่สามารถสร้างคำตอบได้ในขณะนี้"

        if error_type == "rate_limit":
            if is_male:
                return "❌ เซิร์ฟเวอร์ AI ค่อนข้างแน่นครับคุณพี่ ลองใหม่อีกครั้งใน 10-30 วินาทีนะครับ"
            if is_female:
                return "❌ เซิร์ฟเวอร์ AI ยุ่งเกินไปค่ะ ลองใหม่อีกครั้งใน 10-30 วินาทีนะคะ"
            return "❌ เซิร์ฟเวอร์ AI ยุ่งเกินไป ลองใหม่อีกครั้งใน 10-30 วินาที"

        if error_type == "timeout":
            if is_male:
                return "❌ การเชื่อมต่อหมดเวลาครับคุณพี่ กรุณาลองใหม่อีกครั้งนะครับ"
            if is_female:
                return "❌ การเชื่อมต่อหมดเวลาค่ะ ลองใหม่อีกครั้งนะคะ"
            return "❌ การเชื่อมต่อหมดเวลา กรุณาลองใหม่อีกครั้ง"

        return "เกิดข้อผิดพลาดในการประมวลผล"
