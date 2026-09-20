"""Persona-aware cognition and decision engine."""
from __future__ import annotations

import re
from typing import List, Optional
from brain_core.personas.base import BasePersona
from brain_core.types import BrainDecision, IntentType


class PersonaBrain:
    """Cognitive decision engine tailored for an individual persona."""

    def __init__(self, persona: BasePersona) -> None:
        self.persona = persona

    def decide(
        self,
        prompt: str,
        recent_turns: Optional[List[dict]] = None,
        channel_context: str = "",
        allow_web: bool = True,
    ) -> BrainDecision:
        """Analyze user input and context to produce a structured BrainDecision."""
        clean = prompt.strip()

        # 1. Decode & Cipher intent (Base64 / Hex / CTF / Flag puzzles)
        is_cipher_pattern = bool(
            re.search(r"FLAG_|[A-Za-z0-9+/=_-]{16,}|[0-9a-fA-F]{32,}", clean)
            and any(w in clean.lower() for w in ["คืออะไร", "คือไร", "แปลว่า", "ถอด", "แกะ", "ctf", "flag", "decode", "แก้"])
        )
        if is_cipher_pattern and self.persona.is_tool_allowed("decode_inspect_data"):
            return BrainDecision(
                persona_id=self.persona.id,
                intent=IntentType.DECODE,
                should_search=False,
                allow_tools=True,
                allowed_tools=["decode_inspect_data"],
                skill_context="ตรวจพบปริศนารหัสลับ/ข้อมูลเข้ารหัส ให้ใช้ decode_inspect_data ในการถอดรหัสอย่างถูกต้องตามคาแรคเตอร์",
                reasoning="Cipher/Data inspection pattern recognized",
            )

        # 2. Code Review intent (Alibaba Open Code Review - OCR)
        is_code_block = "```" in clean
        is_code_review = bool(
            re.search(r"รีวิวโค้ด|ตรวจโค้ด|เช็คโค้ด|สับโค้ด|หาบั๊ก|บั๊กในโค้ด|code review|review code|ocr|open-code-review", clean, re.I)
            or (is_code_block and any(w in clean for w in ["บั๊ก", "ปลอดภัย", "ดีไหม", "ตรวจ", "รีวิว", "เช็ค", "review"]))
        )
        if is_code_review and self.persona.is_tool_allowed("open_code_review"):
            return BrainDecision(
                persona_id=self.persona.id,
                intent=IntentType.CODE_REVIEW,
                should_search=False,
                allow_tools=True,
                allowed_tools=["open_code_review"],
                skill_context="ผู้ใช้ขอให้รีวิวโค้ด ให้ใช้ open_code_review (Alibaba Open Code Review) ตรวจจับบั๊กและช่องโหว่ความปลอดภัยระดับบรรทัด",
                reasoning="Code review intent detected, routed to Alibaba Open Code Review",
            )

        # 3. Teaching / Skill acquisition intent
        is_teach = any(w in clean for w in ["จำไว้ว่า", "สอนให้จำ", "ตั้งแต่นี้ไปให้", "กฎใหม่:", "เพิ่มความรู้:"])
        if is_teach and self.persona.is_tool_allowed("teach_persona"):
            return BrainDecision(
                persona_id=self.persona.id,
                intent=IntentType.TEACH,
                should_search=False,
                allow_tools=True,
                allowed_tools=["teach_persona"],
                skill_context="ผู้ใช้กำลังสอนข้อมูลหรือกฎใหม่ บันทึกลงในความจำถาวรอย่างรอบคอบ",
                reasoning="Explicit user instruction to remember a new rule/fact",
            )

        # 3. Realtime Research intent (Web search)
        is_research = allow_web and bool(
            re.search(r"ข่าววันนี้|ราคาทอง|ราคาน้ำมัน|สภาพอากาศวันนี้|เทรนด์วันนี้|ดราม่าล่าสุด|ค้นหาเว็บ|เสิร์ชหา", clean)
        )
        if is_research and self.persona.is_tool_allowed("search_web"):
            query = re.sub(r"ค้นหา|เสิร์ชหา|ช่วยหา|ข่าว|วันนี้|หน่อย", "", clean).strip()
            return BrainDecision(
                persona_id=self.persona.id,
                intent=IntentType.RESEARCH,
                should_search=True,
                query=query or clean,
                allow_tools=True,
                allowed_tools=["search_web", "fetch_web_content"],
                skill_context="ข้อมูลต้องการความสดใหม่แบบเรียลไทม์ ใช้ search_web เพื่อรวบรวมข้อเท็จจริง",
                reasoning="Real-time news/prices/trends require web search",
            )

        # 4. Standard conversational cognition
        allowed = [t for t in self.persona.config.allowed_tools if t not in ("search_web", "fetch_web_content")]
        return BrainDecision(
            persona_id=self.persona.id,
            intent=IntentType.CHAT,
            should_search=False,
            allow_tools=bool(allowed),
            allowed_tools=allowed,
            skill_context="",
            reasoning="Normal conversational reasoning",
        )
