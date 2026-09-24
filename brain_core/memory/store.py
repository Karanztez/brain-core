"""Reference stores for durable, isolated cognitive memory."""
from __future__ import annotations

import asyncio
import re
import time
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Tuple

from brain_core.cognition.contracts import CognitiveRequest, MemoryContext
from brain_core.types import ChatMessage


def _scope(request: CognitiveRequest) -> Tuple[str, str, str, str]:
    return (request.tenant_id, request.persona_id, request.channel_id, request.user_id)


def _terms(text: str) -> set[str]:
    return {term for term in re.findall(r"[\w\u0E00-\u0E7F]+", text.lower()) if len(term) > 1}


class InMemoryStore:
    """Concurrency-safe development store with production-equivalent isolation."""

    def __init__(self, max_messages: int = 40, max_facts_per_user: int = 200) -> None:
        self.max_messages = max_messages
        self.max_facts_per_user = max_facts_per_user
        self._turns: Dict[Tuple[str, str, str, str], List[ChatMessage]] = defaultdict(list)
        self._facts: Dict[Tuple[str, str, str], List[str]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def recall(self, request: CognitiveRequest, limit: int = 12) -> MemoryContext:
        fact_scope = (request.tenant_id, request.persona_id, request.user_id)
        async with self._lock:
            messages = list(self._turns.get(_scope(request), []))[-self.max_messages :]
            facts = list(self._facts.get(fact_scope, []))
        query_terms = _terms(request.prompt)
        ranked = sorted(
            enumerate(facts),
            key=lambda item: (len(query_terms & _terms(item[1])), item[0]),
            reverse=True,
        )
        return MemoryContext(messages=messages, facts=[fact for _, fact in ranked[: max(0, limit)]])

    async def save_turn(self, request: CognitiveRequest, response: str) -> None:
        async with self._lock:
            turns = self._turns[_scope(request)]
            turns.extend((ChatMessage(role="user", content=request.prompt), ChatMessage(role="assistant", content=response)))
            del turns[: max(0, len(turns) - self.max_messages)]

    async def remember_fact(self, request: CognitiveRequest, fact: str) -> None:
        key = (request.tenant_id, request.persona_id, request.user_id)
        clean = fact.strip()
        if not clean:
            return
        async with self._lock:
            facts = self._facts[key]
            if clean not in facts:
                facts.append(clean)
            del facts[: max(0, len(facts) - self.max_facts_per_user)]

    async def health(self) -> dict:
        return {"status": "ok", "backend": "memory"}


class MongoMemoryStore:
    """MongoDB store with ordered multi-cluster failover and strict scopes."""

    def __init__(self, uris: Iterable[str], database: str = "brain_core", server_selection_timeout_ms: int = 3000) -> None:
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
        except ImportError as exc:
            raise RuntimeError("Install brain-core[mongodb] to use MongoMemoryStore") from exc
        clean_uris = [uri.strip() for uri in uris if uri and uri.strip()]
        if not clean_uris:
            raise ValueError("at least one MongoDB URI is required")
        self._databases = [
            AsyncIOMotorClient(uri, serverSelectionTimeoutMS=server_selection_timeout_ms)[database]
            for uri in clean_uris
        ]
        self._active = 0

    async def _run(self, operation):
        last_error: Exception | None = None
        for offset in range(len(self._databases)):
            index = (self._active + offset) % len(self._databases)
            try:
                result = await operation(self._databases[index])
                self._active = index
                return result
            except Exception as exc:
                last_error = exc
        raise RuntimeError("all MongoDB clusters are unavailable") from last_error

    @staticmethod
    def _base(request: CognitiveRequest) -> Dict[str, str]:
        return {"tenant_id": request.tenant_id, "persona_id": request.persona_id, "user_id": request.user_id}

    async def recall(self, request: CognitiveRequest, limit: int = 12) -> MemoryContext:
        base = self._base(request)

        async def operation(db):
            cursor = db.turns.find({**base, "channel_id": request.channel_id}, {"_id": 0, "prompt": 1, "response": 1}).sort("created_at", -1).limit(20)
            turns = await cursor.to_list(length=20)
            turns.reverse()
            messages: List[ChatMessage] = []
            for turn in turns:
                messages.extend((ChatMessage(role="user", content=turn["prompt"]), ChatMessage(role="assistant", content=turn["response"])))
            facts = await db.facts.find(base, {"_id": 0, "content": 1}).sort("updated_at", -1).limit(max(0, limit)).to_list(length=max(0, limit))
            return MemoryContext(messages=messages, facts=[item["content"] for item in facts])

        return await self._run(operation)

    async def save_turn(self, request: CognitiveRequest, response: str) -> None:
        document: Dict[str, Any] = {**self._base(request), "channel_id": request.channel_id, "prompt": request.prompt, "response": response, "metadata": dict(request.metadata), "created_at": time.time()}
        await self._run(lambda db: db.turns.insert_one(document))

    async def remember_fact(self, request: CognitiveRequest, fact: str) -> None:
        clean = fact.strip()
        if not clean:
            return

        async def operation(db):
            return await db.facts.update_one(
                {**self._base(request), "content": clean},
                {"$set": {"updated_at": time.time()}, "$setOnInsert": {"created_at": time.time()}},
                upsert=True,
            )

        await self._run(operation)

    async def ensure_indexes(self) -> None:
        async def operation(db):
            await db.turns.create_index([("tenant_id", 1), ("persona_id", 1), ("channel_id", 1), ("user_id", 1), ("created_at", -1)])
            await db.facts.create_index([("tenant_id", 1), ("persona_id", 1), ("user_id", 1), ("content", 1)], unique=True)
            return True
        await self._run(operation)

    async def health(self) -> dict:
        async def operation(db):
            await db.command("ping")
            return {"status": "ok", "backend": "mongodb", "active_cluster": self._active}
        return await self._run(operation)
