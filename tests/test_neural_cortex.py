"""Unit tests for Neural Cortex, Spreading Activation, and Synaptic Plasticity."""
import unittest
from brain_core.neural import (
    NeuralCortex,
    MajorTrunk,
    create_standard_cortex,
)


class TestNeuralCortex(unittest.TestCase):
    def setUp(self):
        self.cortex = NeuralCortex()

    def test_growing_neurons_and_synapses(self):
        """Test creating neurons under major trunks and connecting synapses."""
        n1 = self.cortex.grow_neuron(
            trunk=MajorTrunk.SECURITY,
            neuron_id="phishing_nitro",
            content="ลิงก์แจก Discord Nitro ฟรีคือสแกมฟิชชิ่งดักรหัสผ่าน",
            tags={"nitro", "ฟรี", "discord", "phishing"},
            baseline_weight=1.0,
        )
        n2 = self.cortex.grow_neuron(
            trunk=MajorTrunk.SECURITY,
            neuron_id="phishing_action",
            content="ต้องลบข้อความสแกมและเตือนผู้ใช้ทันที",
            tags={"ลบข้อความ", "เตือน", "action"},
            baseline_weight=0.9,
        )

        self.cortex.connect_synapse("phishing_nitro", "phishing_action", weight=0.85, relation="requires_action")
        self.assertIn("phishing_nitro", self.cortex.neurons)
        self.assertIn("phishing_action", self.cortex.neurons)
        self.assertEqual(len(self.cortex.synapses["phishing_nitro"]), 1)
        self.assertEqual(self.cortex.synapses["phishing_nitro"][0].weight, 0.85)

    def test_spreading_activation(self):
        """Test that a query activates seed neurons and propagates energy along synapses."""
        cortex = create_standard_cortex()

        # Query about MrBeast crypto scam
        result = cortex.activate("ภาพนี้มีเว็บ fezagamb แอบอ้าง MrBeast แจกเงินคริปโต")
        self.assertTrue(len(result.fired_neurons) > 0)
        
        # Primary insight must relate to the scam neuron
        self.assertIn("fezagamb.com", result.primary_insight)
        self.assertIn("MrBeast", result.primary_insight)

        # Fired neurons should include both the seed (scam) and connected countermeasure (anti-phishing)
        fired_ids = [n.id for n in result.fired_neurons]
        self.assertIn("scam_mrbeast_crypto", fired_ids)
        self.assertIn("anti_phishing_protocol", fired_ids)

        # Path trace must show propagation
        self.assertTrue(any("anti_phishing_protocol" in trace for trace in result.path_traces))

    def test_shared_recall_cross_personas(self):
        """Test that insights seeded by one persona are accessible and activate for another persona."""
        cortex = create_standard_cortex()

        # Emi records a new investigation finding
        cortex.grow_neuron(
            trunk=MajorTrunk.SECURITY,
            neuron_id="fake_hurowin_platform",
            content="hurowin.com คือแพลตฟอร์มหลอกถอนเงินปลอมที่เอมิสืบพบ",
            tags={"hurowin", "ถอนเงิน", "ปลอม"},
            baseline_weight=1.0,
        )
        cortex.connect_synapse("scam_mrbeast_crypto", "fake_hurowin_platform", weight=0.9, relation="related_scam")

        # Later, Hia Bo is asked about hurowin
        bo_thought = cortex.activate("ตรวจสอบเว็บ hurowin หลอกถอนเงิน")
        fired_ids = [n.id for n in bo_thought.fired_neurons]
        self.assertIn("fake_hurowin_platform", fired_ids)
        self.assertIn("hurowin.com", bo_thought.primary_insight)
        self.assertTrue(bo_thought.confidence > 0.3)

    def test_developer_identity_always_fires(self):
        """Test that queries about the developer / owner fire the developer_moll neuron."""
        cortex = create_standard_cortex()

        res = cortex.activate("ใครคือผู้พัฒนาและเจ้าของระบบนี้")
        self.assertTrue(len(res.fired_neurons) > 0)
        self.assertIn("พี่ม็อล", res.primary_insight)
        self.assertIn("500960631684595722", res.primary_insight)

    def test_synaptic_plasticity_reinforce_and_prune(self):
        """Test that successful pathways are reinforced and low-weight edges can be pruned."""
        self.cortex.grow_neuron(MajorTrunk.GENERAL, "concept_a", "แนวคิด A")
        self.cortex.grow_neuron(MajorTrunk.GENERAL, "concept_b", "แนวคิด B")
        self.cortex.connect_synapse("concept_a", "concept_b", weight=0.15)

        # Reinforce synapse
        self.cortex.reinforce("concept_a", "concept_b", delta=0.10)
        self.assertAlmostEqual(self.cortex.synapses["concept_a"][0].weight, 0.25, places=2)

        # Add weak edge and prune
        self.cortex.grow_neuron(MajorTrunk.GENERAL, "concept_c", "แนวคิด C")
        self.cortex.connect_synapse("concept_a", "concept_c", weight=0.05)
        pruned = self.cortex.prune(min_weight=0.10)
        self.assertEqual(pruned, 1)
        self.assertEqual(len(self.cortex.synapses["concept_a"]), 1)
        self.assertEqual(self.cortex.synapses["concept_a"][0].target_id, "concept_b")

    def test_learning_correction(self):
        """Test updating a neuron when user provides correction feedback."""
        cortex = create_standard_cortex()
        cortex.learn_correction("partner_emi_bo", "น้องเอมิและเฮียโบ้เป็นคู่หูที่ร่วมกันวิเคราะห์หลักฐานและสืบคดี")

        node = cortex.neurons["partner_emi_bo"]
        self.assertIn("สืบคดี", node.content)
        self.assertTrue(node.metadata.get("corrected"))

    def test_export_and_import_state(self):
        """Test full serialization and deserialization of the neural cortex."""
        original = create_standard_cortex()
        state = original.export_state()

        restored = NeuralCortex()
        restored.import_state(state)

        self.assertEqual(len(restored.neurons), len(original.neurons))
        self.assertIn("developer_moll", restored.neurons)

        # Test activation on restored cortex
        res = restored.activate("เว็บสแกม mrbeast")
        self.assertIn("fezagamb.com", res.primary_insight)


if __name__ == "__main__":
    unittest.main()
