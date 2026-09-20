"""Tests for BrainClient."""
from __future__ import annotations
import unittest
from starlette.testclient import TestClient
from brain_core.api.server import app
from brain_core.client import BrainClient


class TestBrainClient(unittest.TestCase):
    def test_brain_client_instantiation(self):
        client = BrainClient("http://testserver")
        self.assertEqual(client.base_url, "http://testserver")

    def test_server_routes_work_with_test_client(self):
        tc = TestClient(app)
        health = tc.get("/health").json()
        self.assertEqual(health["status"], "ok")

        personas = tc.get("/personas").json()
        self.assertGreaterEqual(len(personas), 2)
        persona_ids = [p["id"] for p in personas]
        self.assertIn("emi", persona_ids)
        self.assertIn("bo", persona_ids)
