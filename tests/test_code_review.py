"""Tests for Alibaba Open Code Review integration in Brain-Core."""
import unittest
from starlette.testclient import TestClient

from brain_core import (
    BasePersona,
    PersonaBrain,
    EMI_CONFIG,
    BO_CONFIG,
    IntentType,
    create_standard_cortex,
    MajorTrunk,
    OpenCodeReviewTool,
)
from brain_core.api.server import app


class TestOpenCodeReview(unittest.TestCase):
    def setUp(self):
        self.tool = OpenCodeReviewTool()
        self.emi_persona = BasePersona(EMI_CONFIG)
        self.bo_persona = BasePersona(BO_CONFIG)
        self.emi_brain = PersonaBrain(self.emi_persona)
        self.bo_brain = PersonaBrain(self.bo_persona)
        self.cortex = create_standard_cortex()

    def test_safe_code_review(self):
        safe_code = """
def add_numbers(a: int, b: int) -> int:
    return a + b
"""
        report = self.tool.review_code(safe_code, persona_id="emi")
        self.assertEqual(report["score"], 100)
        self.assertEqual(report["verdict"], "PASSED")
        self.assertEqual(len(report["findings"]), 0)
        self.assertIn("น้องเอมิ", report["formatted_comment"])

    def test_vulnerable_code_detection(self):
        vulnerable_code = """
import os

API_KEY = "sk-1234567890abcdef1234567890"

def get_user(user_id):
    query = "SELECT * FROM users WHERE id = '" + user_id + "'"
    cursor.execute(query)

def dangerous_run(cmd):
    eval(cmd)
"""
        report_emi = self.tool.review_code(vulnerable_code, persona_id="emi")
        self.assertLess(report_emi["score"], 50)
        self.assertEqual(report_emi["verdict"], "FAILED")
        self.assertGreaterEqual(len(report_emi["findings"]), 3)

        categories = [f["category"] for f in report_emi["findings"]]
        self.assertTrue(any("SQL Injection" in c for c in categories))
        self.assertTrue(any("Secret Leak" in c for c in categories))
        self.assertTrue(any("RCE" in c for c in categories))

        # Check Bo's persona comment
        report_bo = self.tool.review_code(vulnerable_code, persona_id="bo")
        self.assertIn("เฮียโบ้", report_bo["formatted_comment"])
        self.assertIn("☕", report_bo["formatted_comment"])

    def test_brain_intent_classification(self):
        prompt_emi = "น้องเอมิ ช่วยรีวิวโค้ดอันนี้ทีว่ามีบั๊กไหม\n```python\nprint('hello')\n```"
        dec_emi = self.emi_brain.decide(prompt_emi)
        self.assertEqual(dec_emi.intent, IntentType.CODE_REVIEW)
        self.assertIn("open_code_review", dec_emi.allowed_tools)

        prompt_bo = "เฮียโบ้ สับโค้ดนี้ให้หน่อย\n```python\nquery = 'SELECT * FROM x WHERE id = ' + x\n```"
        dec_bo = self.bo_brain.decide(prompt_bo)
        self.assertEqual(dec_bo.intent, IntentType.CODE_REVIEW)
        self.assertIn("open_code_review", dec_bo.allowed_tools)

    def test_neural_cortex_code_review_activation(self):
        act = self.cortex.activate("น้องเอมิ ตรวจโค้ดด้วย ocr ให้หน่อย")
        fired_ids = [n.id for n in act.fired_neurons]
        self.assertIn("skill_open_code_review", fired_ids)

        neuron = next(n for n in act.fired_neurons if n.id == "skill_open_code_review")
        self.assertEqual(neuron.trunk, MajorTrunk.SKILLS)
        self.assertIn("Alibaba Open Code Review", neuron.content)

    def test_api_server_code_review_endpoint(self):
        tc = TestClient(app)
        res = tc.post("/tools/code-review", json={
            "code": "cursor.execute('SELECT * FROM users WHERE id = ' + uid)",
            "persona_id": "bo"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("Alibaba Open Code Review", data["engine"])
        self.assertIn("เฮียโบ้", data["formatted_comment"])
        self.assertGreater(data["total_issues"], 0)


if __name__ == "__main__":
    unittest.main()
