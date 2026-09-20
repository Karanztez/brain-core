"""Neuron and Synapse definitions for Brain-Core Neural Cortex."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class MajorTrunk(str, Enum):
    """Major neural pathways (เส้นประสาทหลัก) in the cortex."""
    SECURITY = "security"            # การป้องกันสแกม, ฟิชชิ่ง, ภัยคุกคาม
    CRYPTOGRAPHY = "cryptography"    # การถอดรหัส, CTF, Ciphers, Base64
    RELATIONSHIPS = "relationships"  # สายสัมพันธ์, ตัวตนผู้พัฒนา, ผู้ใช้
    SKILLS = "skills"                # ทักษะ, How-To, ขั้นตอนการทำงาน
    PHILOSOPHY = "philosophy"        # คติประจำใจ, วุฒิภาวะ, สไตล์การตอบ
    GENERAL = "general"              # ความรู้รอบตัวและข้อเท็จจริงทั่วไป


@dataclass
class SynapseEdge:
    """Connection between two neurons with associative weight."""
    source_id: str
    target_id: str
    weight: float = 0.5             # 0.0 to 1.0 connection strength
    relation: str = "associated_with" # causes, solves, belongs_to, investigated_by
    reinforced_count: int = 1
    last_stimulated: float = field(default_factory=time.time)


@dataclass
class NeuronNode:
    """Individual cognitive neuron holding knowledge, experience, or rules."""
    id: str
    trunk: MajorTrunk
    content: str
    tags: Set[str] = field(default_factory=set)
    activation: float = 0.0          # Current excitation level
    baseline_weight: float = 1.0     # Inherent importance
    fired_count: int = 0
    last_fired: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def stimulate(self, energy: float) -> float:
        """Inject energy into this neuron, capping at 1.0."""
        self.activation = min(1.0, self.activation + energy)
        self.fired_count += 1
        self.last_fired = time.time()
        return self.activation

    def decay(self, decay_rate: float = 0.5) -> None:
        """Decay transient activation back toward 0."""
        self.activation = max(0.0, self.activation * decay_rate)


@dataclass
class ActivationResult:
    """Result of spreading activation across the neural cortex."""
    primary_insight: str
    fired_neurons: List[NeuronNode]
    path_traces: List[str]
    max_activation: float = 0.0
    confidence: float = 0.0
