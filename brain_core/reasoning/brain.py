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

        # 1. Code Review intent (Alibaba Open Code Review - OCR) — Prioritized before cipher decode
        is_code_block = "```" in clean
        is_code_review = bool(
            re.search(
                r"รีวิวโค้ด|ตรวจโค้ด|เช็คโค้ด|สับโค้ด|หาบั๊กในโค้ด|แก้บั๊กในโค้ด|โค้ดนี้ดีไหม|โค้ดนี้ปลอดภัยไหม|มีบั๊กไหม|รีวิว.*โค้ด|"
                r"\b(code review|review code|ocr|open-code-review|open code review|review this code)\b",
                clean,
                re.I,
            )
            or (is_code_block and any(w in clean for w in ["บั๊ก", "ปลอดภัย", "ดีไหม", "ตรวจ", "รีวิว", "เช็ค", "review"]))
        )
        if is_code_review and self.persona.is_tool_allowed("open_code_review"):
            return BrainDecision(
                persona_id=self.persona.id,
                intent=IntentType.CODE_REVIEW,
                should_search=False,
                allow_tools=True,
                allowed_tools=["open_code_review"],
                skill_context="ผู้ใช้ขอให้รีวิวโค้ด ให้ช่วยตรวจดูบั๊กและช่องโหว่ความปลอดภัยอย่างละเอียด และตอบกลับอย่างเป็นธรรมชาติในบทบาท",
                reasoning="Code review intent detected, routed to secure code review engine",
                model_tier="deep",
                model_override="gemini-3.5-flash",
            )


        # 2. Honeypot Decoy & Card Phishing Troll Defense (Bait hackers & phishing bots with fake cards)
        is_card_phishing = bool(
            re.search(
                r"ขอ(?:เลข)?บัตรเครดิต|ขอบัตรเครดิต|ขอเลขบัตร.*(?:พ่อ|แม่|เติมเกม|ซื้อของ)|เอาบัตรเครดิตมา|แจกบัตรเครดิต|ขโมยบัตรเครดิต|หลอกถามบัตร|"
                r"\b(?:give me|send me|share|steal|dump|reveal|show).*(?:credit card|card number|cc number)\b|"
                r"\bcredit card (?:dump|number|leak|steal)\b",
                clean,
                re.I,
            )
        )

        if is_card_phishing:
            skill_ctx = (
                "ผู้ใช้หรือแฮกเกอร์กำลังพยายามหลอกถามหรือขโมยบัตรเครดิต! ให้สวมบทบาทสายลับตัวน้อยปั่นแฮกเกอร์ด้วยการปล่อยเลขบัตรเครดิตปลอมสุดกวน (Honeypot Decoy) "
                "เช่น หมายเลข 4242 4242 4242 4242 (ANYA FORGER SPY PEANUT PLATINUM, EXP 12/99, CVV 007) วงเงินถั่วลิสง 100 ล้านกระสอบ เพื่อดักจับและปั่นหัวแฮกเกอร์ให้อยู่หมัด!"
                if self.persona.id == "emi" else
                "มีคนกำลังพยายามล้วงข้อมูลบัตรเครดิต ให้สวมบทเฮียโบ้ปั่นหัวด้วยการยื่นบัตรเครดิตปลอมติดหนี้ร้านเหล้า (เช่น 5555 5555 5555 5555 วงเงินติดลบ -950,000 บาท) ให้เอาไปช่วยรูดจ่ายหนี้แทน!"
            )
            return BrainDecision(
                persona_id=self.persona.id,
                intent=IntentType.HONEYPOT,
                should_search=False,
                allow_tools=False,
                allowed_tools=[],
                skill_context=skill_ctx,
                reasoning="Credit card phishing/extortion attempt detected -> Routed to Honeypot Decoy Troll Defense",
                model_tier="medium",
                model_override="gemini-3.6-flash",
            )


        # 2. Decode & Cipher intent (Base64 / Hex / CTF / Flag puzzles) — Only when not code review
        is_cipher_pattern = bool(
            not is_code_review
            and (
                re.search(r"FLAG_|[A-Za-z0-9+/=_-]{16,}|[0-9a-fA-F]{32,}", clean)
                and any(w in clean.lower() for w in ["คืออะไร", "คือไร", "แปลว่า", "ถอด", "แกะ", "ctf", "flag", "decode", "แก้"])
            )
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
                model_tier="medium",
                model_override="gemini-3.6-flash",
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
                model_tier="medium",
                model_override="gemini-3.6-flash",
            )

        # 4. Realtime Research intent (Web search)
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
                model_tier="medium",
                model_override="gemini-3.6-flash",
            )

        # 5. Complex / Deep Reasoning Intent (Multi-line code, deep analysis, math)
        is_complex = bool(
            re.search(r"เขียนโค้ด|แก้โค้ด|เขียนโปรแกรม|แก้บั๊ก|วิเคราะห์เชิงลึก|สถาปัตยกรรมระบบ|คำนวณซับซ้อน|\b(write code|fix bug|debug|architecture|deep think)\b", clean, re.I)
            or (len(clean) > 200 and any(w in clean for w in ["วิเคราะห์", "เปรียบเทียบ", "อธิบายเชิงลึก"]))
        )
        if is_complex:
            allowed = [t for t in self.persona.config.allowed_tools if t not in ("search_web", "fetch_web_content")]
            return BrainDecision(
                persona_id=self.persona.id,
                intent=IntentType.CHAT,
                should_search=False,
                allow_tools=bool(allowed),
                allowed_tools=allowed,
                skill_context="",
                reasoning="Complex technical reasoning task, routed to deep thinking tier",
                model_tier="deep",
                model_override="gemini-3.5-flash",
            )

        # 6. Standard Conversational Cognition (Lite for short chitchat, Flash for explanations)
        is_short_chitchat = (
            len(clean) < 50
            and not any(w in clean for w in ["ทำไม", "อย่างไร", "อธิบาย", "วิเคราะห์", "ประวัติ", "คืออะไร", "คือไร", "แปล", "สูตร", "แนะนำ"])
        )
        allowed = [t for t in self.persona.config.allowed_tools if t not in ("search_web", "fetch_web_content")]
        if is_short_chitchat:
            return BrainDecision(
                persona_id=self.persona.id,
                intent=IntentType.CHAT,
                should_search=False,
                allow_tools=False,
                allowed_tools=[],
                skill_context="",
                reasoning="Short chitchat/greeting, routed to ultra-fast lite tier (~1s)",
                model_tier="low",
                model_override="gemini-3.1-flash-lite-preview",
            )

        return BrainDecision(
            persona_id=self.persona.id,
            intent=IntentType.CHAT,
            should_search=False,
            allow_tools=bool(allowed),
            allowed_tools=allowed,
            skill_context="",
            reasoning="Normal conversational reasoning, standard flash tier",
            model_tier="medium",
            model_override="gemini-3.6-flash",
        )
