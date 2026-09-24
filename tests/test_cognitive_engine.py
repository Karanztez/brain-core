import unittest

from brain_core.cognition import CognitiveEngine, CognitiveRequest
from brain_core.memory.store import InMemoryStore
from brain_core.personas.presets.emi import EMI_CONFIG
from brain_core.personas.registry import PersonaRegistry


class FakeModel:
    def __init__(self):
        self.requests = []

    async def generate(self, request):
        self.requests.append(request)
        return "คำตอบจาก Gemini ต้องถูกกรอง"


class CognitiveEngineTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        registry = PersonaRegistry()
        registry.register_config(EMI_CONFIG)
        self.model = FakeModel()
        self.memory = InMemoryStore()
        self.engine = CognitiveEngine(registry, self.model, self.memory)

    async def test_full_cycle_recalls_calls_model_redacts_and_persists(self):
        teach = CognitiveRequest(persona_id="emi", user_id="u1", channel_id="c1", prompt="จำไว้ว่า ชอบสีชมพู", tenant_id="guild-1")
        first = await self.engine.think(teach)
        self.assertEqual(first.trace, ["perceive", "recall", "deliberate", "infer", "validate", "consolidate"])
        self.assertTrue(first.memory_written)
        self.assertNotIn("Gemini", first.text)

        follow_up = CognitiveRequest(persona_id="emi", user_id="u1", channel_id="c1", prompt="ฉันชอบสีอะไร", tenant_id="guild-1")
        second = await self.engine.think(follow_up)
        self.assertIn("จำไว้ว่า ชอบสีชมพู", second.recalled_facts)
        self.assertGreaterEqual(len(self.model.requests[-1].messages), 5)

    async def test_memory_isolated_by_tenant_persona_user_and_channel(self):
        source = CognitiveRequest(persona_id="emi", user_id="u1", channel_id="c1", prompt="จำไว้ว่า ความลับ", tenant_id="guild-1")
        await self.engine.think(source)

        other_tenant = CognitiveRequest(persona_id="emi", user_id="u1", channel_id="c1", prompt="ความลับ", tenant_id="guild-2")
        result = await self.engine.think(other_tenant)
        self.assertEqual(result.recalled_facts, [])

    async def test_rejects_empty_prompt_and_unknown_persona(self):
        with self.assertRaises(ValueError):
            await self.engine.think(CognitiveRequest(persona_id="emi", user_id="u", channel_id="c", prompt="  "))
        with self.assertRaises(LookupError):
            await self.engine.think(CognitiveRequest(persona_id="missing", user_id="u", channel_id="c", prompt="hi"))


if __name__ == "__main__":
    unittest.main()
