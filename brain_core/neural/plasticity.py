"""Synaptic Plasticity: learning, reinforcement, pruning, and self-correction."""
from __future__ import annotations

import logging
from typing import Dict, List, Optional
from brain_core.neural.neuron import NeuronNode, SynapseEdge

logger = logging.getLogger("BrainCore.Neural.Plasticity")


class SynapticPlasticity:
    """Simulates biological synaptic plasticity (LTP, pruning, and rewiring)."""

    @staticmethod
    def reinforce_synapse(
        synapses: Dict[str, List[SynapseEdge]],
        source_id: str,
        target_id: str,
        delta: float = 0.08,
    ) -> bool:
        """Strengthen an association when a thought pathway proves successful (LTP)."""
        edges = synapses.get(source_id, [])
        for edge in edges:
            if edge.target_id == target_id:
                edge.weight = min(1.0, edge.weight + delta)
                edge.reinforced_count += 1
                logger.debug(f"Reinforced synapse {source_id} -> {target_id} (weight={edge.weight:.2f})")
                return True
        return False

    @staticmethod
    def weaken_synapse(
        synapses: Dict[str, List[SynapseEdge]],
        source_id: str,
        target_id: str,
        penalty: float = 0.25,
    ) -> bool:
        """Weaken an association when user indicates an error or contradiction."""
        edges = synapses.get(source_id, [])
        for edge in edges:
            if edge.target_id == target_id:
                edge.weight = max(0.05, edge.weight - penalty)
                logger.debug(f"Weakened synapse {source_id} -> {target_id} (weight={edge.weight:.2f})")
                return True
        return False

    @staticmethod
    def prune_synapses(
        synapses: Dict[str, List[SynapseEdge]],
        min_weight: float = 0.10,
    ) -> int:
        """Remove connections whose synaptic strength drops below viable threshold."""
        pruned_count = 0
        for src, edge_list in synapses.items():
            surviving = [e for e in edge_list if e.weight >= min_weight]
            pruned_count += len(edge_list) - len(surviving)
            synapses[src] = surviving
        return pruned_count
