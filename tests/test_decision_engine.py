"""Unit tests for PersonaBrain decision engine and TurnEvaluator."""
import unittest
from brain_core import (
    PersonaBrain,
    BasePersona,
    EMI_CONFIG,
    BO_CONFIG,
    IntentType,
    TurnEvaluator,
)


class TestDecisionEngine(unittest.TestCase):
    def setUp(self):
        self.emi = BasePersona(EMI_CONFIG)
        self.bo = BasePersona(BO_CONFIG)
        self.emi_brain = PersonaBrain(self.emi)
        self.bo_brain = PersonaBrain(self.bo)

    def test_cipher_intent_detection(self):
        prompt = "FLAG_Bh6gBlZ_BNMgB|LgBVLNB=LNGGqW คืออะไร ช่วยถอดหน่อย"
        dec = self.emi_brain.decide(prompt)
        self.assertEqual(dec.intent, IntentType.DECODE)
        self.assertTrue(dec.allow_tools)
        self.assertIn("decode_inspect_data", dec.allowed_tools)

    def test_research_intent_detection(self):
        prompt = "เช็ค ข่าววันนี้ หรือราคาทองหน่อย"
        dec = self.emi_brain.decide(prompt)
        self.assertEqual(dec.intent, IntentType.RESEARCH)
        self.assertTrue(dec.should_search)

    def test_code_review_priority_over_cipher(self):
        # Even if code contains Base64 or Flag-like patterns, code review intent takes absolute priority
        prompt = "ช่วยรีวิวโค้ดอันนี้ทีว่ามีบั๊กไหม\n```python\nSECRET = 'FLAG_0123456789abcdef0123456789'\n```"
        dec = self.emi_brain.decide(prompt)
        self.assertEqual(dec.intent, IntentType.CODE_REVIEW)
        self.assertEqual(dec.model_tier, "deep")
        self.assertIn("open_code_review", dec.allowed_tools)

    def test_model_tier_assignment(self):
        # Short chitchat -> low tier
        dec_short = self.emi_brain.decide("สวัสดีตอนเช้า")
        self.assertEqual(dec_short.model_tier, "low")
        self.assertEqual(dec_short.model_override, "gemini-3.1-flash-lite-preview")

        # Standard explanation -> medium tier
        dec_med = self.emi_brain.decide("ช่วยอธิบายประวัติศาสตร์อยุธยาแบบละเอียดหน่อย")
        self.assertEqual(dec_med.model_tier, "medium")
        self.assertEqual(dec_med.model_override, "gemini-3.6-flash")

        # Complex technical / deep architecture -> deep tier
        dec_deep = self.emi_brain.decide("ช่วยออกแบบสถาปัตยกรรมระบบ Microservices พร้อมเขียนโค้ดตัวอย่าง")
        self.assertEqual(dec_deep.model_tier, "deep")
        self.assertEqual(dec_deep.model_override, "gemini-3.5-flash")

    def test_turn_arbitration(self):
        # 1. Direct name call to Emi
        should_emi = TurnEvaluator.should_bot_reply(
            bot_id="emi", is_my_station=False, is_other_station=True,
            is_cross_bot=False, is_explicit_call=False,
            explicit_targets=set(), name_targets={"emi"}
        )
        should_bo = TurnEvaluator.should_bot_reply(
            bot_id="bo", is_my_station=True, is_other_station=False,
            is_cross_bot=False, is_explicit_call=False,
            explicit_targets=set(), name_targets={"emi"}
        )
        self.assertTrue(should_emi)
        self.assertFalse(should_bo)

        # 2. Both called
        self.assertTrue(TurnEvaluator.should_bot_reply(
            bot_id="emi", is_my_station=False, is_other_station=True,
            is_cross_bot=False, is_explicit_call=False,
            explicit_targets=set(), name_targets={"emi", "bo"}
        ))
        self.assertTrue(TurnEvaluator.should_bot_reply(
            bot_id="bo", is_my_station=True, is_other_station=False,
            is_cross_bot=False, is_explicit_call=False,
            explicit_targets=set(), name_targets={"emi", "bo"}
        ))


if __name__ == "__main__":
    unittest.main()

