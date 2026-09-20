"""Zero-leak redactor and guardrails for Brain-Core.

Prevents AI model names (Gemini, GPT, Claude, etc.), internal architecture terms,
thought signatures, scratchpad leaks, and sensitive secrets from appearing in responses.
"""
from __future__ import annotations

import os
import re
from typing import List, Tuple

# Patterns to scrub outside code blocks
_DEFAULT_SCRUB_RULES: List[Tuple[re.Pattern, str]] = [
    # Reasoning tags & Scratchpad leaks
    (re.compile(r"<think(?:ing)?>[\s\S]*?</think(?:ing)?>", re.I), ""),
    (re.compile(r"<thought(?:_signature)?>[\s\S]*?</thought(?:_signature)?>", re.I), ""),
    (re.compile(r"<\/?(?:think|thought|thought_signature|system_instruction|tool_call|function_call)[^>]*>", re.I), ""),

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


def mask_sensitive_pii(text: str) -> str:
    """Mask sensitive PII such as Thai National IDs, credit cards (excluding binary bitstreams), and phone numbers."""
    if not text:
        return text
    result = str(text)

    # 1. Thai National IDs (13 digits starting with 1-8, excluding unix timestamps)
    def _mask_raw_id(match):
        num = match.group(0)
        if num.startswith(("16", "17", "18", "19")):
            return num
        return f"{num[0]}-xxxx-xxxxx-xx-{num[-1]}"

    result = re.sub(r'\b[1-8]\d{12}\b', _mask_raw_id, result)

    # 2. Credit Card Numbers (16 digits, excluding pure binary bitstreams)
    def _mask_cc(match):
        val = match.group(0)
        digits = re.sub(r"[-\s]", "", val)
        if set(digits).issubset({"0", "1"}):
            return val  # Don't mask binary bitstreams
        return f"{digits[:4]}-xxxx-xxxx-{digits[-4:]}"

    result = re.sub(
        r'\b(\d{4})[-\s]?(\d{4})[-\s]?(\d{4})[-\s]?(\d{4})\b',
        _mask_cc,
        result,
    )

    # 3. Thai Mobile Phone Numbers (08x, 09x, 06x)
    result = re.sub(
        r'\b(0[689]\d)[-\s]?\d{3}[-\s]?(\d{4})\b',
        r'\1-xxx-\2',
        result,
    )
    return result


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
            # Mask PII safely outside code blocks
            chunk = mask_sensitive_pii(chunk)
            parts[i] = chunk

        result = "".join(parts)
        # Collapse multiple newlines
        return re.sub(r"\n{3,}", "\n\n", result).strip()

