"""Voice Engine & Neural TTS Generator using edge-tts.

Supports high-quality, free Thai neural voices for Emi (Premwadee) and Hia Bo (Niwat),
with text sanitization, in-memory audio buffering, and file generation.
"""
from __future__ import annotations

import io
import logging
import os
import re
import tempfile
from typing import Dict, Any, Optional

try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    edge_tts = None
    HAS_EDGE_TTS = False

logger = logging.getLogger("BrainCore.Voice.TTS")

# Voice Profile Presets
VOICE_PROFILES: Dict[str, Dict[str, str]] = {
    "emi": {
        "voice": "th-TH-PremwadeeNeural",
        "pitch": "+12Hz",
        "rate": "+8%",
        "volume": "+0%",
    },
    "bo": {
        "voice": "th-TH-NiwatNeural",
        "pitch": "-4Hz",
        "rate": "+0%",
        "volume": "+0%",
    },
}


def clean_text_for_speech(text: str, persona: str = "emi") -> str:
    """Clean markdown, code blocks, URLs, and noisy symbols so TTS sounds natural."""
    if not text:
        return ""
    clean = str(text)

    # 1. Replace code blocks with spoken placeholder
    code_notice = " มีโค้ดแนบมาในแชทนะคะ " if persona == "emi" else " มีโค้ดแนบมาในแชทครับ "
    clean = re.sub(r"```[\s\S]*?```", code_notice, clean)
    clean = re.sub(r"`[^`]+`", " โค้ดคำสั่ง ", clean)

    # 2. Replace URLs with simple label
    clean = re.sub(r"https?://\S+", " ลิงก์แนบ ", clean)

    # 3. Strip markdown syntax: bold, italic, strikethrough, headers, quotes, spoiler
    clean = re.sub(r"\*\*([^*]+)\*\*", r"\1", clean)
    clean = re.sub(r"\*([^*]+)\*", r"\1", clean)
    clean = re.sub(r"__([^_]+)__", r"\1", clean)
    clean = re.sub(r"~~([^~]+)~~", r"\1", clean)
    clean = re.sub(r"\|\|([^|]+)\|\|", r"\1", clean)
    clean = re.sub(r"^#{1,6}\s*", "", clean, flags=re.MULTILINE)
    clean = re.sub(r"^>\s*", "", clean, flags=re.MULTILINE)
    clean = re.sub(r"^[•\-\*]\s*", "", clean, flags=re.MULTILINE)

    # 4. Remove laughs, emojis, and symbols that clutter TTS
    clean = re.sub(r"(?:หุหุ~?|ฮ่าๆ?|อิอิ)", " ", clean)
    clean = re.sub(r"[🥜☕✨💖🕶️📋📑📁🔍🕵️‍♀️🤪🚨]+", " ", clean)

    # 5. Remove Discord / platform mentions e.g. <@123456> or <#123456>
    clean = re.sub(r"<@[!&]?\d+>", "", clean)
    clean = re.sub(r"<#\d+>", "", clean)

    # 6. Normalize whitespace
    clean = re.sub(r"\s+", " ", clean).strip()

    # 7. Truncate long responses to 800 characters for optimal sub-2s speech generation
    if len(clean) > 800:
        clean = clean[:790] + ("..." if clean[-1] not in ".!?" else "")

    return clean


async def generate_speech_bytes(text: str, persona: str = "emi") -> io.BytesIO:
    """Generate spoken MP3 audio bytes in-memory for audio attachments."""
    if not HAS_EDGE_TTS:
        raise RuntimeError("โมเดลแปลงเสียง edge-tts ยังไม่ได้ติดตั้ง กรุณารัน: pip install edge-tts")

    spoken_text = clean_text_for_speech(text, persona=persona)
    if not spoken_text:
        spoken_text = "สวัสดีค่ะพี่จ๋า เอมิอยู่นี่แล้วค่า" if persona == "emi" else "สวัสดีครับ มีอะไรให้เฮียช่วยครับ"

    profile = VOICE_PROFILES.get(persona.lower(), VOICE_PROFILES["emi"])
    communicate = edge_tts.Communicate(
        text=spoken_text,
        voice=profile["voice"],
        pitch=profile["pitch"],
        rate=profile["rate"],
        volume=profile["volume"],
    )

    buffer = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buffer.write(chunk["data"])

    buffer.seek(0)
    return buffer


async def generate_speech_file(text: str, target_path: Optional[str] = None, persona: str = "emi") -> str:
    """Generate spoken MP3 audio file on disk for streaming / playback."""
    if not HAS_EDGE_TTS:
        raise RuntimeError("โมเดลแปลงเสียง edge-tts ยังไม่ได้ติดตั้ง กรุณารัน: pip install edge-tts")

    if not target_path:
        fd, target_path = tempfile.mkstemp(suffix=".mp3", prefix=f"tts_{persona}_")
        os.close(fd)

    spoken_text = clean_text_for_speech(text, persona=persona)
    if not spoken_text:
        spoken_text = "สวัสดีค่ะพี่จ๋า เอมิอยู่นี่แล้วค่า" if persona == "emi" else "สวัสดีครับ มีอะไรให้เฮียช่วยครับ"

    profile = VOICE_PROFILES.get(persona.lower(), VOICE_PROFILES["emi"])
    communicate = edge_tts.Communicate(
        text=spoken_text,
        voice=profile["voice"],
        pitch=profile["pitch"],
        rate=profile["rate"],
        volume=profile["volume"],
    )
    await communicate.save(target_path)
    return target_path
