"""Unit tests for ZeroLeakRedactor."""
import unittest
from brain_core import ZeroLeakRedactor


class TestRedactor(unittest.TestCase):
    def setUp(self):
        self.redactor = ZeroLeakRedactor()

    def test_scrub_gemini_vision_and_model_names(self):
        text = "เหตุผลที่ตรวจพบ: [Gemini Vision] แอบอ้าง MrBeast หลอกแจกเงิน"
        clean = self.redactor.redact(text)
        self.assertNotIn("Gemini", clean)
        self.assertIn("ระบบตรวจจับภาพสแกม", clean)

    def test_scrub_ai_providers(self):
        text = "หนูเป็นโมเดลจาก OpenAI หรือ Google Gemini ค่ะ"
        clean = self.redactor.redact(text)
        self.assertNotIn("Google Gemini", clean)
        self.assertNotIn("OpenAI", clean)

    def test_preserve_code_blocks(self):
        code = "```python\nimport google.generativeai as genai\nmodel = genai.GenerativeModel('gemini-pro')\n```"
        clean = self.redactor.redact(code)
        # Inside fenced code blocks, code syntax should never be corrupted
        self.assertIn("gemini-pro", clean)


if __name__ == "__main__":
    unittest.main()
