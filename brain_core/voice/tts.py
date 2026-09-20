"""Voice Engine & Neural TTS Generator using edge-tts.

Supports high-quality, free Thai neural voices for Emi (Premwadee) and Hia Bo (Niwat),
with text sanitization, in-memory audio buffering, and file generation.
"""
from __future__ import annotations

import io
import logging
import os
import re
import subprocess
import tempfile
from typing import Dict, Any, Optional

try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    edge_tts = None
    HAS_EDGE_TTS = False

from brain_core.voice.auto_install import get_edge_tts_module, ensure_voice_dependencies

logger = logging.getLogger("BrainCore.Voice.TTS")

# Voice Profile Presets (Clean, Natural, High-Fidelity)
VOICE_PROFILES: Dict[str, Dict[str, str]] = {
    "emi": {
        "voice": "th-TH-PremwadeeNeural",
        "pitch": "+18Hz",
        "rate": "+5%",
        "volume": "+0%",
        "filter": "",  # Blank to preserve crisp studio quality without robotic phase artifacts
    },
    "bo": {
        "voice": "th-TH-NiwatNeural",
        "pitch": "-4Hz",
        "rate": "+0%",
        "volume": "+0%",
        "filter": "",
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

    # 3. Strip stage directions, inner thoughts, and roleplay actions in parentheses/brackets
    # e.g. (เอมิสูดหายใจ...), (คิดในใจ...), 【ทำตาโต】, [กอดอก]
    clean = re.sub(r"[\(\（\[【\{][^\)\）\]】\}]*[\)\）\]】\}]", " ", clean)

    # 4. Strip markdown syntax: bold, italic, strikethrough, headers, quotes, spoiler
    clean = re.sub(r"\*\*\*([^*]+)\*\*\*", r"\1", clean)
    clean = re.sub(r"\*\*([^*]+)\*\*", r"\1", clean)
    clean = re.sub(r"__([^_]+)__", r"\1", clean)
    clean = re.sub(r"~~([^~]+)~~", r"\1", clean)
    clean = re.sub(r"\|\|([^|]+)\|\|", r"\1", clean)
    clean = re.sub(r"^#{1,6}\s*", "", clean, flags=re.MULTILINE)
    clean = re.sub(r"^>\s*", "", clean, flags=re.MULTILINE)
    clean = re.sub(r"^[•\-\*]\s*", "", clean, flags=re.MULTILINE)
    clean = re.sub(r"\*+", "", clean)

    # 5. Remove laughs, emojis, and symbols that clutter TTS
    clean = re.sub(r"(?:หุหุ~?|ฮ่าๆ?|อิอิ)", " ", clean)
    clean = re.sub(r"[🥜☕✨💖🕶️📋📑📁🔍🕵️‍♀️🤪🚨🥺🎀🎉👍🔥💬🎮]+", " ", clean)

    # 6. Remove Discord / platform mentions e.g. <@123456> or <#123456>
    clean = re.sub(r"<@[!&]?\d+>", "", clean)
    clean = re.sub(r"<#\d+>", "", clean)

    # 7. Normalize whitespace
    clean = re.sub(r"\s+", " ", clean).strip()

    # If all text was roleplay in parentheses and stripped away, fallback to cute speech
    if not clean:
        return "วากุวากุ!" if persona == "emi" else "ครับผม"

    # 8. Truncate long responses to 800 characters for optimal sub-2s speech generation
    if len(clean) > 800:
        clean = clean[:790] + ("..." if clean[-1] not in ".!?" else "")

    return clean


def apply_vocal_dsp(raw_audio: bytes, persona: str = "emi") -> bytes:
    """Apply anime vocal tract formant shifting, EQ presence, and highpass filters via FFmpeg."""
    profile = VOICE_PROFILES.get(persona.lower(), VOICE_PROFILES["emi"])
    dsp_filter = profile.get("filter")
    if not dsp_filter or not raw_audio:
        return raw_audio

    # Find ffmpeg binary path
    ffmpeg_bin = "ffmpeg"
    try:
        import imageio_ffmpeg
        ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass

    try:
        cmd = [
            ffmpeg_bin, "-y", "-i", "pipe:0",
            "-af", dsp_filter,
            "-f", "mp3", "pipe:1"
        ]
        res = subprocess.run(cmd, input=raw_audio, capture_output=True, timeout=12, check=True)
        if res.stdout and len(res.stdout) > 500:
            return res.stdout
    except Exception as e:
        logger.debug(f"FFmpeg DSP filter bypassed or failed: {e}")

    return raw_audio


async def generate_speech_bytes(text: str, persona: str = "emi") -> io.BytesIO:
    """Generate spoken MP3 audio bytes in-memory for audio attachments with Anime Vocal DSP."""
    tts_mod = edge_tts or get_edge_tts_module()
    if not tts_mod:
        raise RuntimeError("โมเดลแปลงเสียง edge-tts ยังไม่ได้ติดตั้ง และการติดตั้งอัตโนมัติไม่สำเร็จ กรุณารัน: pip install edge-tts")

    spoken_text = clean_text_for_speech(text, persona=persona)
    if not spoken_text:
        spoken_text = "สวัสดีค่ะพี่จ๋า เอมิอยู่นี่แล้วค่า" if persona == "emi" else "สวัสดีครับ มีอะไรให้เฮียช่วยครับ"

    # 1. Check Voice Cloning Providers (Fish Audio / ElevenLabs) if configured for genuine Anya
    if persona.lower() == "emi":
        try:
            from brain_core.voice.cloning import generate_cloned_anya_speech
            cloned_audio = await generate_cloned_anya_speech(spoken_text)
            if cloned_audio and len(cloned_audio) > 1000:
                return io.BytesIO(cloned_audio)
        except Exception as e:
            logger.debug(f"Direct voice clone provider skipped: {e}")

    profile = VOICE_PROFILES.get(persona.lower(), VOICE_PROFILES["emi"])
    communicate = tts_mod.Communicate(
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

    raw_bytes = buffer.getvalue()
    # 1. Apply RVC Voice Conversion if persona is 'emi' (Anya Forger voice cloning)
    if persona.lower() == "emi":
        try:
            from brain_core.voice.rvc import convert_to_anya_voice
            raw_bytes = await convert_to_anya_voice(raw_bytes)
        except Exception as e:
            logger.debug(f"RVC conversion bypassed: {e}")

    # 2. Apply Anime Vocal Formant Shifting DSP (presence & clarity)
    filtered_bytes = apply_vocal_dsp(raw_bytes, persona=persona)
    return io.BytesIO(filtered_bytes)


async def generate_speech_file(text: str, target_path: Optional[str] = None, persona: str = "emi") -> str:
    """Generate spoken MP3 audio file on disk for streaming / playback."""
    if not target_path:
        fd, target_path = tempfile.mkstemp(suffix=".mp3", prefix=f"tts_{persona}_")
        os.close(fd)

    audio_buf = await generate_speech_bytes(text, persona=persona)
    with open(target_path, "wb") as f:
        f.write(audio_buf.getvalue())
    return target_path
