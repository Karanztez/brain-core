"""Unit tests for persona identity isolation and fallback behaviors."""
import unittest
from brain_core import (
    PersonaRegistry,
    BasePersona,
    EMI_CONFIG,
    BO_CONFIG,
    PersonaGender,
    PersonaFallbackManager,
)


class TestPersonaIsolation(unittest.TestCase):
    def setUp(self):
        self.registry = PersonaRegistry()
        self.emi = self.registry.register_config(EMI_CONFIG, aliases=["น้องเอมิ", "emi"])
        self.bo = self.registry.register_config(BO_CONFIG, aliases=["เฮียโบ้", "bo"])

    def test_distinct_identities_and_genders(self):
        self.assertEqual(self.emi.id, "emi")
        self.assertEqual(self.emi.gender, PersonaGender.FEMALE)
        self.assertEqual(self.bo.id, "bo")
        self.assertEqual(self.bo.gender, PersonaGender.MALE)

        # Lookup by aliases
        self.assertEqual(self.registry.get("น้องเอมิ").id, "emi")
        self.assertEqual(self.registry.get("เฮียโบ้").id, "bo")

    def test_fallbacks_never_cross_genders(self):
        # Emi fallback must have 'ค่ะ' and not 'ครับ'
        emi_fallback = PersonaFallbackManager.get_fallback(self.emi, "empty")
        self.assertIn("ค่ะ", emi_fallback)
        self.assertNotIn("ครับ", emi_fallback)
        self.assertNotIn("เฮีย", emi_fallback)

        # Bo fallback must have 'ครับ' and not 'ค่ะ'
        bo_fallback = PersonaFallbackManager.get_fallback(self.bo, "empty")
        self.assertIn("ครับ", bo_fallback)
        self.assertNotIn("ค่ะ", bo_fallback)
        self.assertNotIn("หนู", bo_fallback)

    def test_timeout_and_rate_limit_fallbacks(self):
        bo_timeout = PersonaFallbackManager.get_fallback(self.bo, "timeout")
        self.assertIn("ครับ", bo_timeout)

        emi_rate_limit = PersonaFallbackManager.get_fallback(self.emi, "rate_limit")
        self.assertIn("ค่ะ", emi_rate_limit)


if __name__ == "__main__":
    unittest.main()
