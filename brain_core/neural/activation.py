"""Spreading Activation algorithm for Brain-Core Neural Cortex."""
from __future__ import annotations

import re
from typing import Dict, List, Set, Tuple
from brain_core.neural.neuron import NeuronNode, SynapseEdge, ActivationResult


class SpreadingActivation:
    """Propagates cognitive activation across synaptic pathways."""

    def __init__(
        self,
        decay_factor: float = 0.65,
        threshold: float = 0.25,
        max_depth: int = 3,
    ) -> None:
        self.decay_factor = decay_factor
        self.threshold = threshold
        self.max_depth = max_depth

    def activate(
        self,
        query: str,
        neurons: Dict[str, NeuronNode],
        synapses: Dict[str, List[SynapseEdge]],
    ) -> ActivationResult:
        """Find seed neurons matching query and spread activation along synaptic links."""
        # 1. Reset transient activations
        for n in neurons.values():
            n.activation = 0.0

        q_lower = query.lower().strip()
        if not q_lower:
            return ActivationResult(primary_insight="", fired_neurons=[], path_traces=[], confidence=0.0)

        q_terms = set(re.findall(r"[A-Za-z0-9_]+", q_lower))

        # 2. Identify Seed Neurons
        seed_scores: List[Tuple[NeuronNode, float]] = []
        for n in neurons.values():
            score = 0.0
            content_lower = n.content.lower()
            id_lower = n.id.lower()

            # Tag and keyword matches (handles both Thai continuous scripts and space-separated terms)
            for tag in n.tags:
                t_low = tag.lower()
                if t_low in q_lower:
                    score += 0.50
                elif t_low in q_terms:
                    score += 0.45

            # ID / Content matches
            if id_lower in q_lower:
                score += 0.40
            for term in q_terms:
                if len(term) >= 2 and (term in id_lower or term in content_lower):
                    score += 0.25

            if score > 0:
                seed_scores.append((n, min(1.0, score * n.baseline_weight)))

        if not seed_scores:
            return ActivationResult(primary_insight="", fired_neurons=[], path_traces=[], confidence=0.0)

        # 3. Spreading Activation Queue
        path_traces: List[str] = []
        # queue item: (neuron_id, current_energy, depth, path_str)
        queue: List[Tuple[str, float, int, str]] = []

        for node, initial_energy in seed_scores:
            node.stimulate(initial_energy)
            queue.append((node.id, initial_energy, 1, f"[{node.trunk.value}:{node.id}]"))

        visited_in_depth: Set[Tuple[str, int]] = set()

        while queue:
            curr_id, curr_energy, depth, path = queue.pop(0)
            if depth >= self.max_depth:
                continue

            state_key = (curr_id, depth)
            if state_key in visited_in_depth:
                continue
            visited_in_depth.add(state_key)

            # Look up outgoing synapses
            outgoing = synapses.get(curr_id, [])
            for syn in outgoing:
                target_node = neurons.get(syn.target_id)
                if not target_node:
                    continue

                # Energy transfers proportional to synapse weight and decay factor
                transmitted_energy = curr_energy * syn.weight * self.decay_factor
                if transmitted_energy >= self.threshold:
                    new_act = target_node.stimulate(transmitted_energy)
                    new_path = f"{path} --({syn.relation}:{syn.weight:.2f})--> [{target_node.trunk.value}:{target_node.id}]"
                    path_traces.append(new_path)
                    queue.append((target_node.id, transmitted_energy, depth + 1, new_path))

        # 4. Gather Fired Neurons
        fired = [n for n in neurons.values() if n.activation >= self.threshold]
        fired.sort(key=lambda n: n.activation, reverse=True)

        primary_insight = fired[0].content if fired else ""
        max_act = fired[0].activation if fired else 0.0

        return ActivationResult(
            primary_insight=primary_insight,
            fired_neurons=fired,
            path_traces=path_traces,
            max_activation=max_act,
            confidence=min(1.0, max_act),
        )
