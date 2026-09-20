"""Voice Cloning Provider Integration (Fish Audio & ElevenLabs) for Brain-Core.

Enables true voice cloning for Anya Forger (Emi) using dedicated anime models:
1. Fish Audio (SOTA open-source zero-shot anime models with Anya presets)
2. ElevenLabs Multilingual v2 (Anya Voice Clone)
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional

import httpx

import re

logger = logging.getLogger("BrainCore.Voice.Cloning")

FISH_AUDIO_API_KEY = os.getenv("FISH_AUDIO_API_KEY", "sk-fish-lIn7Q1ZGjbI76W5lHGA0OM6RQKxSuRXDmAyDpiy5GKs")
FISH_AUDIO_MODEL_ID = os.getenv("FISH_AUDIO_MODEL_ID", "f5ecc5a5f74b4ae49a9e8a041f0376a1")  # Anya Forger Thai Voice Clone
FISH_AUDIO_MODEL = os.getenv("FISH_AUDIO_MODEL", "s2.1-pro-free")  # Free Tier S2.1 Pro Model

# Concurrency limiter to strictly adhere to Fish Audio 5 concurrent requests limit (prevents 429 Too Many Requests)
_fish_audio_semaphore: Optional[asyncio.Semaphore] = None


def _get_fish_audio_semaphore() -> asyncio.Semaphore:
    global _fish_audio_semaphore
    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        current_loop = None

    if _fish_audio_semaphore is None or getattr(_fish_audio_semaphore, "_loop", None) != current_loop:
        _fish_audio_semaphore = asyncio.Semaphore(5)
        setattr(_fish_audio_semaphore, "_loop", current_loop)
    return _fish_audio_semaphore

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")  # Anya Forger Voice ID


def prepare_thai_text_for_fish_audio(text: str) -> str:
    """Optimize Thai text phonetics, clause pacing, and vowel clarity for Fish Audio S2.1."""
    if not text:
        return text
    # Expand maiyamok (ๆ) with clear separation so Fish Audio doesn't skip or slur the repetition
    cleaned = re.sub(r"(\S)ๆ", r"\1 \1", text)
    # Ensure natural pauses around punctuation and sentence boundaries
    cleaned = re.sub(r"([!?,])(?=[^\s])", r"\1 ", cleaned)
    # Normalize whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


async def generate_cloned_anya_speech(text: str) -> Optional[bytes]:
    """Attempt to generate voice-cloned speech for Anya using configured provider."""
    api_key = os.getenv("FISH_AUDIO_API_KEY") or FISH_AUDIO_API_KEY
    model_id = os.getenv("FISH_AUDIO_MODEL_ID") or FISH_AUDIO_MODEL_ID
    model = os.getenv("FISH_AUDIO_MODEL") or FISH_AUDIO_MODEL

    # 1. Try Fish Audio if configured (defaults to free tier model s2.1-pro-free)
    if api_key and model_id:
        try:
            audio = await _call_fish_audio(text, api_key, model_id, model=model)
            if audio:
                logger.info(f"✨ Generated Anya voice via Fish Audio Clone (model: {model}, bytes: {len(audio)})")
                return audio
        except Exception as e:
            logger.warning(f"Fish Audio generation failed: {e}")

    # 2. Try ElevenLabs if configured
    el_key = os.getenv("ELEVENLABS_API_KEY") or ELEVENLABS_API_KEY
    el_voice = os.getenv("ELEVENLABS_VOICE_ID") or ELEVENLABS_VOICE_ID
    if el_key and el_voice:
        try:
            audio = await _call_elevenlabs(text, el_key, el_voice)
            if audio:
                logger.info("✨ Generated Anya voice via ElevenLabs Clone")
                return audio
        except Exception as e:
            logger.warning(f"ElevenLabs generation failed: {e}")

    return None


# Persistent Keep-Alive HTTP client pool (saves 1.0-1.2s TCP+TLS handshake per request)
_fish_audio_client: Optional[httpx.AsyncClient] = None


def _get_fish_audio_client() -> httpx.AsyncClient:
    global _fish_audio_client
    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        current_loop = None

    if (
        _fish_audio_client is None
        or _fish_audio_client.is_closed
        or getattr(_fish_audio_client, "_loop", None) != current_loop
    ):
        _fish_audio_client = httpx.AsyncClient(
            timeout=25.0,
            limits=httpx.Limits(max_keepalive_connections=8, max_connections=20, keepalive_expiry=120.0),
        )
        setattr(_fish_audio_client, "_loop", current_loop)
    return _fish_audio_client


async def _call_fish_audio(
    text: str,
    api_key: str,
    reference_id: str,
    model: str = "s2.1-pro-free",
) -> Optional[bytes]:
    """Call Fish Audio TTS API with optimized Thai phonetic clarity parameters."""
    url = "https://api.fish.audio/v1/tts"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "model": model,
    }
    payload = {
        "text": prepare_thai_text_for_fish_audio(text),
        "reference_id": reference_id,
        "format": "mp3",
        "latency": os.getenv("FISH_AUDIO_LATENCY", "normal"),
        "temperature": float(os.getenv("FISH_AUDIO_TEMPERATURE", "0.65")),
        "normalize": os.getenv("FISH_AUDIO_NORMALIZE", "true").lower() == "true",
        "prosody": {
            "speed": float(os.getenv("FISH_AUDIO_SPEED", "1.0")),
            "volume": 0.0,
            "normalize_loudness": True,
        },
    }
    client = _get_fish_audio_client()
    async with _get_fish_audio_semaphore():
        res = await client.post(url, headers=headers, json=payload)
        if res.status_code == 200 and len(res.content) > 1000:
            return res.content
        logger.warning(f"Fish Audio returned {res.status_code}: {res.text[:150]}")
    return None


async def _call_elevenlabs(text: str, api_key: str, voice_id: str) -> Optional[bytes]:
    """Call ElevenLabs Multilingual v2 API."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.45,
            "similarity_boost": 0.85,
            "style": 0.35,
        },
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.post(url, headers=headers, json=payload)
        if res.status_code == 200 and len(res.content) > 1000:
            return res.content
        logger.warning(f"ElevenLabs returned {res.status_code}: {res.text[:150]}")
    return None
