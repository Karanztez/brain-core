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

    def test_scrub_thought_tags(self):
        thought_leak = "<think>Let me reason about this step by step...</think>สวัสดีค่ะ! วันนี้อากาศดีมากเลย"
        clean = self.redactor.redact(thought_leak)
        self.assertNotIn("<think>", clean)
        self.assertNotIn("Let me reason", clean)
        self.assertEqual(clean, "สวัสดีค่ะ! วันนี้อากาศดีมากเลย")

    def test_binary_bitstream_safety(self):
        # 16-bit binary streams should NOT be mangled by credit card masking
        binary_text = "ผลลัพธ์ของรหัสไบนารีคือ 0011001111011111 และ 1100110000110011 จ้า"
        clean = self.redactor.redact(binary_text)
        self.assertIn("0011001111011111", clean)
        self.assertIn("1100110000110011", clean)
        self.assertNotIn("xxxx", clean)

    def test_credit_card_pii_masking(self):
        # Actual credit card numbers should still be masked
        card_text = "บัตรเครดิตหมายเลข 4532 1234 5678 9010 สำหรับชำระเงิน"
        clean = self.redactor.redact(card_text)
        self.assertIn("4532-xxxx-xxxx-9010", clean)
        self.assertNotIn("1234 5678", clean)


if __name__ == "__main__":
    unittest.main()

