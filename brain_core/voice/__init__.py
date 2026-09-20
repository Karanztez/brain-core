"""Voice module for Brain-Core.

Provides Neural TTS generation, text sanitization, and voice profiles for AI personas.
"""
from brain_core.voice.tts import (
    clean_text_for_speech,
    generate_speech_bytes,
    generate_speech_file,
    VOICE_PROFILES,
)
from brain_core.voice.rvc import convert_to_anya_voice

__all__ = [
    "clean_text_for_speech",
    "generate_speech_bytes",
    "generate_speech_file",
    "VOICE_PROFILES",
    "convert_to_anya_voice",
]
