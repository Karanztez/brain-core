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

logger = logging.getLogger("BrainCore.Voice.Cloning")

FISH_AUDIO_API_KEY = os.getenv("FISH_AUDIO_API_KEY", "")
FISH_AUDIO_MODEL_ID = os.getenv("FISH_AUDIO_MODEL_ID", "")  # Anya Forger Model ID
FISH_AUDIO_MODEL = os.getenv("FISH_AUDIO_MODEL", "s2.1-pro-free")  # Free Tier S2.1 Pro Model

# Concurrency limiter to strictly adhere to Fish Audio 5 concurrent requests limit (prevents 429 Too Many Requests)
_FISH_AUDIO_SEMAPHORE = asyncio.Semaphore(5)

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")  # Anya Forger Voice ID


async def generate_cloned_anya_speech(text: str) -> Optional[bytes]:
    """Attempt to generate voice-cloned speech for Anya using configured provider."""
    api_key = os.getenv("FISH_AUDIO_API_KEY", FISH_AUDIO_API_KEY)
    model_id = os.getenv("FISH_AUDIO_MODEL_ID", FISH_AUDIO_MODEL_ID)
    model = os.getenv("FISH_AUDIO_MODEL", FISH_AUDIO_MODEL)

    # 1. Try Fish Audio if configured (defaults to free tier model s2.1-pro-free)
    if api_key and model_id:
        try:
            audio = await _call_fish_audio(text, api_key, model_id, model=model)
            if audio:
                logger.info(f"✨ Generated Anya voice via Fish Audio Clone (model: {model})")
                return audio
        except Exception as e:
            logger.warning(f"Fish Audio generation failed: {e}")

    # 2. Try ElevenLabs if configured
    el_key = os.getenv("ELEVENLABS_API_KEY", ELEVENLABS_API_KEY)
    el_voice = os.getenv("ELEVENLABS_VOICE_ID", ELEVENLABS_VOICE_ID)
    if el_key and el_voice:
        try:
            audio = await _call_elevenlabs(text, el_key, el_voice)
            if audio:
                logger.info("✨ Generated Anya voice via ElevenLabs Clone")
                return audio
        except Exception as e:
            logger.warning(f"ElevenLabs generation failed: {e}")

    return None


async def _call_fish_audio(
    text: str,
    api_key: str,
    reference_id: str,
    model: str = "s2.1-pro-free",
) -> Optional[bytes]:
    """Call Fish Audio TTS API. Uses 'model: s2.1-pro-free' header for free zero-credit usage."""
    url = "https://api.fish.audio/v1/tts"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "model": model,
    }
    payload = {
        "text": text,
        "reference_id": reference_id,
        "format": "mp3",
        "latency": os.getenv("FISH_AUDIO_LATENCY", "low"),
    }
    async with _FISH_AUDIO_SEMAPHORE:
        async with httpx.AsyncClient(timeout=25.0) as client:
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
