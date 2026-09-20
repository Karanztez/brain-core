"""Unit tests for Brain-Core Voice Module."""
import io
import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from brain_core.voice.tts import (
    clean_text_for_speech,
    generate_speech_bytes,
    generate_speech_file,
    VOICE_PROFILES,
)
from brain_core import (
    clean_text_for_speech as root_clean,
    generate_speech_bytes as root_gen_bytes,
    VOICE_PROFILES as root_profiles,
)


class TestBrainCoreVoice(unittest.TestCase):
    """Test text sanitization and profile configuration in brain-core."""

    def test_clean_text_for_speech_markdown_and_code(self):
        raw = "```python\nsecret_code = 123\n```\n**หนูเอมิเองค่ะ** ลิงก์ https://google.com <@999>"
        cleaned_emi = clean_text_for_speech(raw, persona="emi")
        self.assertNotIn("secret_code", cleaned_emi)
        self.assertNotIn("```", cleaned_emi)
        self.assertIn("มีโค้ดแนบมาในแชทนะคะ", cleaned_emi)
        self.assertNotIn("https://", cleaned_emi)
        self.assertNotIn("<@", cleaned_emi)
        self.assertIn("หนูเอมิเองค่ะ", cleaned_emi)

        cleaned_bo = clean_text_for_speech(raw, persona="bo")
        self.assertIn("มีโค้ดแนบมาในแชทครับ", cleaned_bo)

    def test_voice_profiles(self):
        self.assertIn("emi", VOICE_PROFILES)
        self.assertIn("bo", VOICE_PROFILES)
        self.assertEqual(VOICE_PROFILES["emi"]["voice"], "th-TH-PremwadeeNeural")
        self.assertEqual(VOICE_PROFILES["bo"]["voice"], "th-TH-NiwatNeural")

    def test_root_exports(self):
        self.assertEqual(clean_text_for_speech, root_clean)
        self.assertEqual(generate_speech_bytes, root_gen_bytes)
        self.assertEqual(VOICE_PROFILES, root_profiles)


class TestBrainCoreVoiceAsync(unittest.IsolatedAsyncioTestCase):
    """Test async TTS audio generation."""

    async def test_generate_speech_bytes(self):
        buf = await generate_speech_bytes("ทดสอบเสียงสังเคราะห์สมองกลางค่ะ", persona="emi")
        self.assertIsInstance(buf, io.BytesIO)
        self.assertGreater(buf.getbuffer().nbytes, 1000)

    async def test_generate_speech_file(self):
        temp_file = await generate_speech_file("เฮียโบ้ทดสอบเสียงไฟล์ครับ", persona="bo")
        try:
            self.assertTrue(os.path.exists(temp_file))
            self.assertGreater(os.path.getsize(temp_file), 1000)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    async def test_convert_to_anya_voice_fallback(self):
        from brain_core.voice.rvc import convert_to_anya_voice
        sample_audio = b"fake-audio-bytes-at-least-1000" * 50
        res = await convert_to_anya_voice(sample_audio)
        self.assertGreater(len(res), 500)


if __name__ == "__main__":
    unittest.main()
