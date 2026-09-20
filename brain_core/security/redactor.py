"""Zero-leak redactor and guardrails for Brain-Core.

Prevents AI model names (Gemini, GPT, Claude, etc.), internal architecture terms,
and system secret leaks from ever appearing in public user-facing responses.
"""
from __future__ import annotations

import re
from typing import List, Tuple

# Patterns to scrub outside code blocks
_DEFAULT_SCRUB_RULES: List[Tuple[re.Pattern, str]] = [
    # Gemini Vision & Anti-scam tags
    (re.compile(r"\[?Gemini\s+Vision\]?", re.I), "[ระบบตรวจจับภาพสแกม]"),
    (re.compile(r"\b(?:โดย\s*)?Gemini\s+Vision\b", re.I), "โดยระบบตรวจจับภาพ"),
    (re.compile(r"\[?(?:ตรวจจับด้วย\s*)?Gemini(?:\s+Vision)?\]?", re.I), "[ระบบตรวจจับความปลอดภัย]"),
    
    # Model and Provider Identity Leaks
    (re.compile(r"เทคโนโลยี(?:ปัญญาประดิษฐ์)?(?:สุดล้ำ)?จาก(?:กูเกิล|Google)\s*(?:\(Gemini\)|\bGemini\b)?", re.I), "พลังและคำสอนลับสุดยอดจากคุณผู้พัฒนา"),
    (re.compile(r"จาก(?:กูเกิล|Google)\s*(?:\(Gemini\)|\bGemini\b)", re.I), "จากคุณผู้พัฒนา"),
    (re.compile(r"(?:กูเกิล|Google)\s*\(Gemini\)", re.I), "คุณผู้พัฒนา"),
    (re.compile(r"โมเดล\s*(?:Google\s*)?Gemini", re.I), "ระบบ AI"),
    (re.compile(r"\s*\(Gemini\)", re.I), ""),
    (re.compile(r"\b(?:Google\s+)?Gemini(?:\s+API|\s+Pro|\s+Flash|\s+Ultra)?\b", re.I), "ระบบ AI"),
    (re.compile(r"\b(?:OpenAI|ChatGPT|Claude|DeepSeek)\b", re.I), "ระบบ AI"),

    # Internal mechanics leaks
    (re.compile(r"(?:เครือข่าย|โครงข่าย)?เส้นประสาทสมอง(?:ลับ)?\s*(?:\(?Neural\s*Knowledge\s*Graph\)?)?", re.I), "พลังความคิดและการสังเกต"),
    (re.compile(r"\(?Neural\s*Knowledge\s*Graph\)?", re.I), "แฟ้มบันทึกความจำ"),
    (re.compile(r"(?:จาก\s*)?(?:ฮาวทู\s*)?wikiHow\b", re.I), "ประสบการณ์รอบตัว"),
]


class ZeroLeakRedactor:
    """Scrubs sensitive tokens, model provider names, and internal secrets from text."""

    def __init__(self, custom_rules: List[Tuple[re.Pattern, str]] = None) -> None:
        self.rules = list(_DEFAULT_SCRUB_RULES)
        if custom_rules:
            self.rules.extend(custom_rules)

    def redact(self, text: str) -> str:
        """Clean output text while preserving code within fenced markdown blocks (```...```)."""
        if not text:
            return ""

        # Split on fenced code blocks so code syntax is never altered
        parts = re.split(r"(```[\s\S]*?```)", text)
        for i in range(0, len(parts), 2):
            chunk = parts[i]
            for pat, rep in self.rules:
                chunk = pat.sub(rep, chunk)
            # Remove raw mention formatting like "@name"
            chunk = re.sub(r"(พี่|น้อง|คุณ)\s*@([A-Za-zก-๙0-9_]+)", r"\1 \2", chunk)
            parts[i] = chunk

        return "".join(parts)
