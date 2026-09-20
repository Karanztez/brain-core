"""Neural Cortex: The central synaptic network for Brain-Core."""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Set
from brain_core.neural.neuron import MajorTrunk, NeuronNode, SynapseEdge, ActivationResult
from brain_core.neural.activation import SpreadingActivation
from brain_core.neural.plasticity import SynapticPlasticity

logger = logging.getLogger("BrainCore.Neural.Cortex")


class NeuralCortex:
    """The central associative neural network coordinating shared memory and reasoning."""

    def __init__(
        self,
        decay_factor: float = 0.65,
        activation_threshold: float = 0.25,
        max_depth: int = 3,
    ) -> None:
        self.neurons: Dict[str, NeuronNode] = {}
        # source_id -> list of SynapseEdge
        self.synapses: Dict[str, List[SynapseEdge]] = {}
        self.activation_engine = SpreadingActivation(
            decay_factor=decay_factor,
            threshold=activation_threshold,
            max_depth=max_depth,
        )
        self.plasticity_engine = SynapticPlasticity()

    def grow_neuron(
        self,
        trunk: MajorTrunk,
        neuron_id: str,
        content: str,
        tags: Optional[Set[str]] = None,
        baseline_weight: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> NeuronNode:
        """Create or update a cognitive neuron in the cortex."""
        node = self.neurons.get(neuron_id)
        if node:
            node.content = content
            if tags:
                node.tags.update(tags)
            node.baseline_weight = max(node.baseline_weight, baseline_weight)
            if metadata:
                node.metadata.update(metadata)
            return node

        new_node = NeuronNode(
            id=neuron_id,
            trunk=trunk,
            content=content,
            tags=set(tags or []),
            baseline_weight=baseline_weight,
            metadata=metadata or {},
        )
        self.neurons[neuron_id] = new_node
        logger.debug(f"Grew neuron: [{trunk.value}:{neuron_id}]")
        return new_node

    def connect_synapse(
        self,
        source_id: str,
        target_id: str,
        weight: float = 0.5,
        relation: str = "associated_with",
        bidirectional: bool = False,
    ) -> None:
        """Establish a synaptic pathway between two neurons."""
        if source_id not in self.neurons or target_id not in self.neurons:
            raise KeyError(f"Both neurons must exist before connecting synapse: {source_id} -> {target_id}")

        edge = SynapseEdge(source_id=source_id, target_id=target_id, weight=weight, relation=relation)
        edges = self.synapses.setdefault(source_id, [])
        # Replace if exists, else append
        for i, existing in enumerate(edges):
            if existing.target_id == target_id:
                edges[i] = edge
                break
        else:
            edges.append(edge)

        if bidirectional:
            rev_edge = SynapseEdge(source_id=target_id, target_id=source_id, weight=weight, relation=relation)
            rev_edges = self.synapses.setdefault(target_id, [])
            for i, existing in enumerate(rev_edges):
                if existing.target_id == source_id:
                    rev_edges[i] = rev_edge
                    break
            else:
                rev_edges.append(rev_edge)

    def activate(self, query: str) -> ActivationResult:
        """Execute spreading activation across the cortex triggered by query terms."""
        return self.activation_engine.activate(query, self.neurons, self.synapses)

    def reinforce(self, source_id: str, target_id: str, delta: float = 0.08) -> bool:
        """Reinforce a verified synaptic pathway."""
        return self.plasticity_engine.reinforce_synapse(self.synapses, source_id, target_id, delta)

    def learn_correction(self, neuron_id: str, corrected_content: str) -> NeuronNode:
        """Apply cognitive correction when user corrects an assumption or error."""
        node = self.neurons.get(neuron_id)
        if node:
            node.content = corrected_content
            node.metadata["corrected"] = True
            logger.info(f"Updated neuron {neuron_id} with corrected knowledge")
            return node
        # Create as new neuron
        return self.grow_neuron(MajorTrunk.GENERAL, neuron_id, corrected_content)

    def prune(self, min_weight: float = 0.10) -> int:
        """Prune inactive or degraded synapses."""
        return self.plasticity_engine.prune_synapses(self.synapses, min_weight)

    def export_state(self) -> Dict[str, Any]:
        """Serialize neural cortex state into a portable dict."""
        return {
            "neurons": [
                {
                    "id": n.id,
                    "trunk": n.trunk.value,
                    "content": n.content,
                    "tags": list(n.tags),
                    "baseline_weight": n.baseline_weight,
                    "fired_count": n.fired_count,
                    "metadata": n.metadata,
                }
                for n in self.neurons.values()
            ],
            "synapses": [
                {
                    "source_id": e.source_id,
                    "target_id": e.target_id,
                    "weight": e.weight,
                    "relation": e.relation,
                    "reinforced_count": e.reinforced_count,
                }
                for edges in self.synapses.values()
                for e in edges
            ],
        }

    def import_state(self, state: Dict[str, Any]) -> None:
        """Load neural cortex state from a serialized dict."""
        for n_data in state.get("neurons", []):
            self.grow_neuron(
                trunk=MajorTrunk(n_data["trunk"]),
                neuron_id=n_data["id"],
                content=n_data["content"],
                tags=set(n_data.get("tags", [])),
                baseline_weight=n_data.get("baseline_weight", 1.0),
                metadata=n_data.get("metadata", {}),
            )
        for s_data in state.get("synapses", []):
            self.connect_synapse(
                source_id=s_data["source_id"],
                target_id=s_data["target_id"],
                weight=s_data.get("weight", 0.5),
                relation=s_data.get("relation", "associated_with"),
            )


def create_standard_cortex() -> NeuralCortex:
    """Build a cortex pre-seeded with foundational neural branches for Emi and Bo."""
    cortex = NeuralCortex()

    # 1. Major Trunk: Relationships
    cortex.grow_neuron(
        trunk=MajorTrunk.RELATIONSHIPS,
        neuron_id="developer_moll",
        content="พี่ม็อล (ID: 500960631684595722) คือหัวหน้าผู้พัฒนาและผู้สร้างระบบตัวจริงเสียงจริงของทั้งน้องเอมิและเฮียโบ้",
        tags={"ม็อล", "พี่ม็อล", "ผู้พัฒนา", "developer", "creator", "เจ้าของ", "คนสร้าง", "ผู้สร้าง", "สร้าง"},
        baseline_weight=1.0,
    )
    cortex.grow_neuron(
        trunk=MajorTrunk.RELATIONSHIPS,
        neuron_id="partner_emi_bo",
        content="น้องเอมิและเฮียโบ้เป็นคู่หูร่วมเซิร์ฟเวอร์ โดยเอมิเป็นสายลับพลังจิตตัวน้อย และเฮียโบ้เป็นผู้จัดการอาวุโสฝ่ายประเด็น",
        tags={"เอมิ", "โบ้", "เฮียโบ้", "คู่หู", "ฝ่ายประเด็น"},
        baseline_weight=0.9,
    )
    cortex.connect_synapse("developer_moll", "partner_emi_bo", weight=0.95, relation="created_by", bidirectional=True)

    # 2. Major Trunk: Security & Scam Defense
    cortex.grow_neuron(
        trunk=MajorTrunk.SECURITY,
        neuron_id="scam_mrbeast_crypto",
        content="แก๊งมิจฉาชีพสร้างโพสต์และเว็บไซต์ปลอม เช่น fezagamb.com และ hurowin.com แอบอ้างรูปภาพ MrBeast หลอกแจกเงินคริปโตและคาสิโนเถื่อน",
        tags={"mrbeast", "scam", "fezagamb", "hurowin", "คริปโต", "แจกเงิน", "เว็บพนัน", "สแกม"},
        baseline_weight=1.0,
    )
    cortex.grow_neuron(
        trunk=MajorTrunk.SECURITY,
        neuron_id="anti_phishing_protocol",
        content="ห้ามกดลิงก์แปลกปลอมเด็ดขาด ให้ทำการลบข้อความสแกมและออกใบเตือนทันที",
        tags={"ฟิชชิ่ง", "สแกม", "เตือน", "ลบข้อความ", "anti_scam"},
        baseline_weight=0.85,
    )
    cortex.connect_synapse("scam_mrbeast_crypto", "anti_phishing_protocol", weight=0.90, relation="countermeasure", bidirectional=True)

    # 3. Major Trunk: Cryptography & CTF
    cortex.grow_neuron(
        trunk=MajorTrunk.CRYPTOGRAPHY,
        neuron_id="multiplexed_dual_stream",
        content="รหัสลับมัลติเพล็กซ์สองสาย: กรอง Noise ออก, แยกสตรีมตามพาแนล, ชิฟต์ ROT5/ROT10, กลับทิศทาง Reverse เพื่อเปิด Flag",
        tags={"flag", "rot", "rot5", "rot10", "reverse", "ctf", "ถอดรหัส", "dual_stream"},
        baseline_weight=0.95,
    )

    return cortex
