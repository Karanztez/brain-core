"""Fact and Knowledge Graph storage for Brain-Core."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class KnowledgeNode:
    key: str
    content: str
    tags: Set[str] = field(default_factory=set)
    confidence: float = 1.0


class CognitiveKnowledgeGraph:
    """Stores persistent facts about users, entities, and skills."""

    def __init__(self) -> None:
        # user_id -> list of facts
        self._user_facts: Dict[str, List[str]] = {}
        # node_key -> KnowledgeNode
        self._nodes: Dict[str, KnowledgeNode] = {}

    def set_user_fact(self, user_id: str | int, fact: str) -> None:
        """Add a learned fact about a user (e.g. developer identity, nickname, preference)."""
        uid = str(user_id)
        facts = self._user_facts.setdefault(uid, [])
        if fact not in facts:
            facts.append(fact)

    def get_user_facts(self, user_id: str | int) -> List[str]:
        """Fetch all facts known about this user."""
        return list(self._user_facts.get(str(user_id), []))

    def add_knowledge_node(self, key: str, content: str, tags: Optional[Set[str]] = None) -> None:
        """Register a factual or procedural knowledge node."""
        self._nodes[key] = KnowledgeNode(key=key, content=content, tags=tags or set())

    def search_knowledge(self, query: str) -> List[KnowledgeNode]:
        """Search knowledge nodes matching query terms."""
        q = query.lower()
        results = []
        for node in self._nodes.values():
            if q in node.key.lower() or q in node.content.lower() or any(q in t.lower() for t in node.tags):
                results.append(node)
        return results
