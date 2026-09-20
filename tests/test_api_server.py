"""Unit tests for Brain-Core FastAPI REST endpoints."""
import unittest
from fastapi.testclient import TestClient
from brain_core.api.server import app


class TestAPIServer(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_endpoint(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), {"status": "ok", "service": "brain-core"})

    def test_list_personas_endpoint(self):
        res = self.client.get("/personas")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(len(data) >= 2)
        p_ids = [p["id"] for p in data]
        self.assertIn("emi", p_ids)
        self.assertIn("bo", p_ids)

    def test_decide_endpoint(self):
        payload = {
            "persona_id": "emi",
            "prompt": "FLAG_Bh6gBlZ= แปลว่าอะไร",
            "allow_web": False,
        }
        res = self.client.post("/decide", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["persona_id"], "emi")
        self.assertEqual(data["intent"], "decode")
        self.assertIn("decode_inspect_data", data["allowed_tools"])

    def test_redact_endpoint(self):
        payload = {"text": "ตรวจพบรูปภาพจาก [Gemini Vision] ค่ะ"}
        res = self.client.post("/redact", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertNotIn("Gemini", data["redacted"])
        self.assertIn("ระบบตรวจจับภาพสแกม", data["redacted"])

    def test_neural_activate_endpoint(self):
        payload = {"query": "ภาพหลอกแจกเงิน fezagamb mrbeast"}
        res = self.client.post("/neural/activate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("fezagamb.com", data["primary_insight"])
        self.assertTrue(data["confidence"] > 0)
        self.assertTrue(len(data["fired_neurons"]) > 0)

    def test_neural_grow_and_state_endpoint(self):
        grow_payload = {
            "trunk": "skills",
            "neuron_id": "api_testing_skill",
            "content": "ทักษะการทดสอบ API ด้วย TestClient",
            "tags": ["api", "testing"],
            "baseline_weight": 1.0,
        }
        res = self.client.post("/neural/grow", json=grow_payload)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "created")

        # Verify in state
        state_res = self.client.get("/neural/state")
        self.assertEqual(state_res.status_code, 200)
        state_data = state_res.json()
        neuron_ids = [n["id"] for n in state_data["neurons"]]
        self.assertIn("api_testing_skill", neuron_ids)


if __name__ == "__main__":
    unittest.main()
