"""Voice Cloning Provider Integration (Fish Audio & ElevenLabs) for Brain-Core.

Enables true voice cloning for Anya Forger (Emi) using dedicated anime models:
1. Fish Audio (SOTA open-source zero-shot anime models with Anya presets)
2. ElevenLabs Multilingual v2 (Anya Voice Clone)
"""
from __future__ import annotations

import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger("BrainCore.Voice.Cloning")

FISH_AUDIO_API_KEY = os.getenv("FISH_AUDIO_API_KEY", "")
FISH_AUDIO_MODEL_ID = os.getenv("FISH_AUDIO_MODEL_ID", "")  # Anya Forger Model ID

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")  # Anya Forger Voice ID


async def generate_cloned_anya_speech(text: str) -> Optional[bytes]:
    """Attempt to generate voice-cloned speech for Anya using configured provider."""
    # 1. Try Fish Audio if configured
    if FISH_AUDIO_API_KEY and FISH_AUDIO_MODEL_ID:
        try:
            audio = await _call_fish_audio(text, FISH_AUDIO_API_KEY, FISH_AUDIO_MODEL_ID)
            if audio:
                logger.info("✨ Generated Anya voice via Fish Audio Clone")
                return audio
        except Exception as e:
            logger.warning(f"Fish Audio generation failed: {e}")

    # 2. Try ElevenLabs if configured
    if ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID:
        try:
            audio = await _call_elevenlabs(text, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID)
            if audio:
                logger.info("✨ Generated Anya voice via ElevenLabs Clone")
                return audio
        except Exception as e:
            logger.warning(f"ElevenLabs generation failed: {e}")

    return None


async def _call_fish_audio(text: str, api_key: str, reference_id: str) -> Optional[bytes]:
    """Call Fish Audio TTS API."""
    url = "https://api.fish.audio/v1/tts"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "reference_id": reference_id,
        "format": "mp3",
        "latency": "normal",
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
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
