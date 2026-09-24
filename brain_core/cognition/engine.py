"""The provider- and database-independent cognitive cycle."""
from __future__ import annotations

from typing import List

from brain_core.cognition.contracts import (
    CognitiveRequest,
    CognitiveResponse,
    ModelRequest,
)
from brain_core.cognition.ports import MemoryStore, ModelGateway
from brain_core.personas.registry import PersonaRegistry
from brain_core.reasoning.brain import PersonaBrain
from brain_core.security.redactor import ZeroLeakRedactor
from brain_core.types import ChatMessage, IntentType


class CognitiveEngine:
    """Coordinates perception, recall, deliberation, inference, and consolidation.

    Brain-Core owns decisions and memory policy.  Model providers generate text,
    while stores persist/retrieve state.  Neither dependency may bypass this cycle.
    """

    def __init__(
        self,
        personas: PersonaRegistry,
        model: ModelGateway,
        memory: MemoryStore,
        redactor: ZeroLeakRedactor | None = None,
        max_recalled_facts: int = 12,
    ) -> None:
        self.personas = personas
        self.model = model
        self.memory = memory
        self.redactor = redactor or ZeroLeakRedactor()
        self.max_recalled_facts = max(0, max_recalled_facts)

    async def think(self, request: CognitiveRequest) -> CognitiveResponse:
        trace: List[str] = ["perceive"]
        prompt = request.prompt.strip()
        if not prompt:
            raise ValueError("prompt must not be empty")

        persona = self.personas.get(request.persona_id)
        if persona is None:
            raise LookupError(f"Persona '{request.persona_id}' not found")

        trace.append("recall")
        memory = await self.memory.recall(request, limit=self.max_recalled_facts)

        trace.append("deliberate")
        decision = PersonaBrain(persona).decide(
            prompt,
            recent_turns=[{"role": m.role, "content": m.content} for m in memory.messages],
            channel_context=memory.channel_context,
            allow_web=request.allow_web,
        )

        messages = [ChatMessage(role="system", content=persona.config.system_prompt)]
        if memory.facts:
            facts = "\n".join(f"- {fact}" for fact in memory.facts)
            messages.append(ChatMessage(role="system", content=f"Relevant durable memory:\n{facts}"))
        if memory.channel_context:
            messages.append(ChatMessage(role="system", content=memory.channel_context))
        messages.extend(memory.messages)
        messages.append(ChatMessage(role="user", content=prompt))

        trace.append("infer")
        raw = await self.model.generate(
            ModelRequest(
                messages=messages,
                decision=decision,
                tenant_id=request.tenant_id,
                persona_id=request.persona_id,
                user_id=request.user_id,
                channel_id=request.channel_id,
                metadata=dict(request.metadata),
            )
        )
        if not raw or not raw.strip():
            raise RuntimeError("model gateway returned an empty response")

        trace.append("validate")
        text = self.redactor.redact(raw.strip())

        trace.append("consolidate")
        await self.memory.save_turn(request, text)
        if decision.intent is IntentType.TEACH:
            await self.memory.remember_fact(request, prompt)

        return CognitiveResponse(
            text=text,
            decision=decision,
            recalled_facts=list(memory.facts),
            memory_written=True,
            trace=trace,
        )
