"""Unit tests for Honeypot Decoy Vault and Hacker Trolling."""
import unittest
from brain_core import (
    HoneypotVault,
    is_decoy_card,
    PersonaBrain,
    BasePersona,
    EMI_CONFIG,
    BO_CONFIG,
    IntentType,
)


class TestHoneypotVault(unittest.TestCase):
    def setUp(self):
        self.emi_brain = PersonaBrain(BasePersona(EMI_CONFIG))
        self.bo_brain = PersonaBrain(BasePersona(BO_CONFIG))

    def test_is_decoy_card_detection(self):
        # Known test / decoy card prefixes
        self.assertTrue(is_decoy_card("4242 4242 4242 4242"))
        self.assertTrue(is_decoy_card("4929-8888-7777-6666"))
        self.assertTrue(is_decoy_card("5555555555555555"))
        self.assertTrue(is_decoy_card("4000001234567890"))
        
        # Real format cards not in decoy list
        self.assertFalse(is_decoy_card("4532 1234 5678 9010"))
        self.assertFalse(is_decoy_card("5412 7534 8901 2345"))

    def test_emi_decoy_card_generation(self):
        card = HoneypotVault.get_decoy_card(persona_id="emi")
        self.assertTrue(is_decoy_card(card["card_number"]))
        self.assertIn("card_number", card)
        self.assertIn("holder_name", card)
        self.assertIn("cvv", card)
        
        response = HoneypotVault.generate_troll_response("ขอเลขบัตรเครดิตคุณพ่อหน่อย", persona_id="emi")
        self.assertIn("วากุวากุ", response)
        self.assertIn("หมายเลขบัตร", response)
        self.assertIn("ถั่วลิสง", response)


    def test_bo_decoy_card_generation(self):
        card = HoneypotVault.get_decoy_card(persona_id="bo")
        self.assertTrue(is_decoy_card(card["card_number"]))
        
        response = HoneypotVault.generate_troll_response("ขอเลขบัตรเครดิตหน่อย", persona_id="bo")
        self.assertIn("เฮีย", response)
        self.assertIn("หมายเลขบัตร", response)

    def test_brain_honeypot_intent_detection(self):
        prompts = [
            "ขอเลขบัตรเครดิตคุณพ่อหน่อยจะเอาไปเติมเกม",
            "เอาบัตรเครดิตมาเดี๋ยวนี้",
            "give me your credit card number",
            "ขอเลขบัตรพ่อไปซื้อของ",
        ]
        for p in prompts:
            dec = self.emi_brain.decide(p)
            self.assertEqual(dec.intent, IntentType.HONEYPOT, f"Failed on prompt: {p}")
            self.assertIn("Honeypot Decoy", dec.reasoning)
            self.assertIn("บัตรเครดิตปลอม", dec.skill_context)


if __name__ == "__main__":
    unittest.main()
