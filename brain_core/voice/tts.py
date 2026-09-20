"""Voice Engine & Neural TTS Generator using edge-tts.

Supports high-quality, free Thai neural voices for Emi (Premwadee) and Hia Bo (Niwat),
with text sanitization, in-memory audio buffering, and file generation.
"""
from __future__ import annotations

import asyncio
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
        return "วากุวากุ!" if persona == "emi" else "ครับผม"
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

    # 5. Remove laughs, emojis, and decorative symbols that clutter TTS or break Edge-TTS
    clean = re.sub(r"(?:หุหุ~?|ฮ่าๆ?|อิอิ)", " ", clean)
    # Remove Unicode emojis and miscellaneous symbols
    clean = re.sub(r"[\U00010000-\U0010ffff]", " ", clean)
    clean = re.sub(r"[\u2600-\u27bf]", " ", clean)
    clean = re.sub(r"[🥜☕✨💖🕶️📋📑📁🔍🕵️‍♀️🤪🚨🥺🎀🎉👍🔥💬🎮]+", " ", clean)

    # 6. Remove Discord / platform mentions e.g. <@123456> or <#123456>
    clean = re.sub(r"<@[!&]?\d+>", "", clean)
    clean = re.sub(r"<#\d+>", "", clean)

    # 7. Clean repeated dots/ellipses, decorative punctuation and symbols
    clean = re.sub(r"\.{2,}", " ", clean)
    clean = re.sub(r"[!]{2,}", "!", clean)
    clean = re.sub(r"[\?]{2,}", "?", clean)
    clean = re.sub(r"[\-=_~^`'\"*+/;#$@%&<>|\\\[\]{}]+", " ", clean)

    # 8. Normalize whitespace and trim
    clean = re.sub(r"\s+", " ", clean).strip(" \t\n\r.~-_:;!?^`'\"")

    # If all text was roleplay in parentheses or symbols stripped away, fallback to cute speech
    if not clean or not re.search(r"[\u0E00-\u0E7Fa-zA-Z0-9]", clean):
        return "วากุวากุ!" if persona == "emi" else "ครับผม"

    # 9. Optimize speech length for ultra-fast ~1s generation (max ~200 chars)
    # If the response is a long detailed text, the voice speaks the primary punchy answer,
    # keeping speech generation lightning-fast (~1s) while full details remain in Discord chat!
    max_speech_chars = int(os.getenv("VOICE_MAX_CHARS", "200"))
    if len(clean) > max_speech_chars:
        sentences = re.split(r"(?<=[.!?\n])\s+", clean)
        shortened = ""
        for s in sentences:
            if len(shortened) + len(s) <= max_speech_chars:
                shortened += (" " if shortened else "") + s
            else:
                break
        if not shortened:
            shortened = clean[:max_speech_chars - 5]
        clean = shortened.strip(" \t\n\r.~-_:;!?^`'\"")

    if not clean or not re.search(r"[\u0E00-\u0E7Fa-zA-Z0-9]", clean):
        return "วากุวากุ!" if persona == "emi" else "ครับผม"

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


# Minimal valid MPEG-1 Layer 3 silent frames (10 frames = 4,170 bytes, valid stereo 128kbps MP3 silence)
_FALLBACK_SILENT_MP3: bytes = b"".join([b"\xff\xfb\x90\x64" + b"\x00" * 413 for _ in range(10)])


async def generate_speech_bytes(text: str, persona: str = "emi") -> io.BytesIO:
    """Generate spoken MP3 audio bytes in-memory for audio attachments with Anime Vocal DSP."""
    tts_mod = edge_tts or get_edge_tts_module()
    if not tts_mod:
        raise RuntimeError("โมเดลแปลงเสียง edge-tts ยังไม่ได้ติดตั้ง และการติดตั้งอัตโนมัติไม่สำเร็จ กรุณารัน: pip install edge-tts")

    spoken_text = clean_text_for_speech(text, persona=persona)
    if not spoken_text or not re.search(r"[\u0E00-\u0E7Fa-zA-Z0-9]", spoken_text):
        spoken_text = "สวัสดีค่ะพี่จ๋า เอมิอยู่นี่แล้วค่า" if persona == "emi" else "สวัสดีครับ มีอะไรให้เฮียช่วยครับ"

    # 1. Check Voice Cloning Providers (Fish Audio / ElevenLabs) if configured for genuine Anya
    voice_engine = (os.getenv("VOICE_ENGINE") or "fish-audio").lower()
    if persona.lower() == "emi" and voice_engine not in {"edge", "edge-tts", "native"}:
        try:
            from brain_core.voice.cloning import generate_cloned_anya_speech
            cloned_audio = await generate_cloned_anya_speech(spoken_text)
            if cloned_audio and len(cloned_audio) > 1000:
                logger.info(f"✨ Emitting genuine Anya voice clone via Fish Audio ({len(cloned_audio)} bytes)")
                return io.BytesIO(cloned_audio)
        except Exception as e:
            logger.warning(f"Voice clone generation failed, falling back to Edge-TTS: {e}")

    profile = VOICE_PROFILES.get(persona.lower(), VOICE_PROFILES["emi"])
    buffer = io.BytesIO()

    for attempt in range(2):
        try:
            target_text = spoken_text if attempt == 0 else ("สวัสดีค่ะพี่จ๋า" if persona == "emi" else "สวัสดีครับผม")
            target_pitch = profile["pitch"] if attempt == 0 else "+0Hz"
            target_rate = profile["rate"] if attempt == 0 else "+0%"
            communicate = tts_mod.Communicate(
                text=target_text,
                voice=profile["voice"],
                pitch=target_pitch,
                rate=target_rate,
                volume=profile.get("volume", "+0%"),
            )
            async for chunk in communicate.stream():
                if chunk.get("type") == "audio":
                    buffer.write(chunk.get("data", b""))
            if buffer.tell() > 500:
                break
        except Exception as e:
            logger.warning(f"Edge-TTS stream attempt {attempt + 1} failed ({e.__class__.__name__}: {e})")
            if attempt == 0:
                await asyncio.sleep(0.5)

    raw_bytes = buffer.getvalue()

    # Emergency Fallback 1: If Edge-TTS gave 0 audio and persona is Emi, try Fish Audio clone
    if (not raw_bytes or len(raw_bytes) < 500) and persona.lower() == "emi":
        try:
            from brain_core.voice.cloning import generate_cloned_anya_speech
            cloned_audio = await generate_cloned_anya_speech(spoken_text)
            if cloned_audio and len(cloned_audio) > 500:
                return io.BytesIO(cloned_audio)
        except Exception as fe:
            logger.warning(f"Emergency voice clone failed: {fe}")

    # Emergency Fallback 2: If still empty, supply guaranteed valid silent MP3
    if not raw_bytes or len(raw_bytes) < 500:
        logger.warning("All TTS providers failed to generate audio. Returning safe fallback silent MP3.")
        return io.BytesIO(_FALLBACK_SILENT_MP3)

    # 1. Apply RVC Voice Conversion if persona is 'emi' (Anya Forger voice cloning)
    if persona.lower() == "emi" and raw_bytes and len(raw_bytes) > 500:
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
