"""Voice module for Brain-Core.

Provides Neural TTS generation, text sanitization, and voice profiles for AI personas.
"""
from brain_core.voice.tts import (
    clean_text_for_speech,
    generate_speech_bytes,
    generate_speech_file,
    VOICE_PROFILES,
)

__all__ = [
    "clean_text_for_speech",
    "generate_speech_bytes",
    "generate_speech_file",
    "VOICE_PROFILES",
]
