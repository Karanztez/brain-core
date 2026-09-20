"""Unit tests for ChannelContextBuffer, SessionMemory, and CognitiveKnowledgeGraph."""
import unittest
from brain_core import (
    ChannelContextBuffer,
    SessionMemory,
    CognitiveKnowledgeGraph,
)


class TestMemoryFabric(unittest.TestCase):
    def test_channel_context_preservation(self):
        buf = ChannelContextBuffer(max_turns=5, max_turn_chars=1800)
        long_analysis = "ภาพนี้คือสแกมคาสิโนปลอมแอบอ้าง MrBeast บนเว็บ fezagamb.com"

        buf.append(
            channel_id=123,
            author="ผู้ใช้",
            bot_scope="emi",
            prompt="อันนี้คือไรเอมิ",
            reply=long_analysis,
        )

        recent = buf.get_recent(123)
        self.assertEqual(len(recent), 1)
        self.assertIn("fezagamb.com", recent[0].reply)

        # Context prompt format
        prompt = buf.format_context_prompt(123)
        self.assertIn("MrBeast", prompt)
        self.assertIn("fezagamb.com", prompt)

    def test_session_memory_isolation(self):
        mem = SessionMemory(max_history=5)
        mem.append("emi", 123, 999, "สวัสดีเอมิ", "สวัสดีค่ะ!")
        mem.append("bo", 123, 999, "เฮียโบ้ทำไรอยู่", "จิบกาแฟอยู่ครับคุณพี่")

        emi_msgs = mem.get_messages("emi", 123, 999)
        bo_msgs = mem.get_messages("bo", 123, 999)

        self.assertEqual(len(emi_msgs), 2)
        self.assertEqual(len(bo_msgs), 2)
        self.assertIn("สวัสดีค่ะ!", emi_msgs[1].content)
        self.assertIn("จิบกาแฟอยู่ครับคุณพี่", bo_msgs[1].content)

    def test_knowledge_graph_developer_facts(self):
        graph = CognitiveKnowledgeGraph()
        graph.set_user_fact(500960631684595722, "พี่ม็อล คือหัวหน้าผู้พัฒนาระบบตัวจริง")

        facts = graph.get_user_facts(500960631684595722)
        self.assertEqual(len(facts), 1)
        self.assertIn("พี่ม็อล", facts[0])


if __name__ == "__main__":
    unittest.main()
