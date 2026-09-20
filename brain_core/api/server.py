"""FastAPI service layer for Brain-Core.

Allows running Brain-Core as an HTTP/REST microservice:
    uvicorn brain_core.api.server:app --port 8000
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from brain_core.personas.base import BasePersona
from brain_core.personas.registry import PersonaRegistry
from brain_core.personas.presets.emi import EMI_CONFIG
from brain_core.personas.presets.bo import BO_CONFIG
from brain_core.reasoning.brain import PersonaBrain
from brain_core.security.redactor import ZeroLeakRedactor
from brain_core.memory.buffer import ChannelContextBuffer

try:
    from fastapi import FastAPI, HTTPException
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False


# Default registry pre-loaded with Emi and Bo
default_registry = PersonaRegistry()
default_registry.register_config(EMI_CONFIG, aliases=["น้องเอมิ", "emi"])
default_registry.register_config(BO_CONFIG, aliases=["เฮียโบ้", "bo"])

default_channel_buffer = ChannelContextBuffer()
default_redactor = ZeroLeakRedactor()


class DecideRequest(BaseModel):
    persona_id: str
    prompt: str
    channel_id: Optional[str] = None
    allow_web: bool = True


class DecideResponse(BaseModel):
    persona_id: str
    intent: str
    should_search: bool
    query: str
    allow_tools: bool
    allowed_tools: List[str]
    skill_context: str
    reasoning: str


class RedactRequest(BaseModel):
    text: str


class RedactResponse(BaseModel):
    redacted: str


if HAS_FASTAPI:
    app = FastAPI(
        title="Brain-Core API",
        version="0.1.0",
        description="Multi-Persona AI Cognition & Reasoning Engine Service",
    )

    @app.get("/health")
    def health() -> Dict[str, str]:
        return {"status": "ok", "service": "brain-core"}

    @app.get("/personas")
    def list_personas() -> List[Dict[str, Any]]:
        return [
            {
                "id": p.id,
                "name": p.name,
                "title": p.config.title,
                "gender": p.gender.value,
                "allowed_tools": p.config.allowed_tools,
            }
            for p in default_registry.list_personas()
        ]

    @app.post("/decide", response_model=DecideResponse)
    def decide(req: DecideRequest) -> DecideResponse:
        persona = default_registry.get(req.persona_id)
        if not persona:
            raise HTTPException(status_code=404, detail=f"Persona '{req.persona_id}' not found")
        brain = PersonaBrain(persona)
        channel_ctx = default_channel_buffer.format_context_prompt(req.channel_id) if req.channel_id else ""
        decision = brain.decide(req.prompt, channel_context=channel_ctx, allow_web=req.allow_web)
        return DecideResponse(
            persona_id=decision.persona_id,
            intent=decision.intent.value,
            should_search=decision.should_search,
            query=decision.query,
            allow_tools=decision.allow_tools,
            allowed_tools=decision.allowed_tools,
            skill_context=decision.skill_context,
            reasoning=decision.reasoning,
        )

    @app.post("/redact", response_model=RedactResponse)
    def redact(req: RedactRequest) -> RedactResponse:
        return RedactResponse(redacted=default_redactor.redact(req.text))
else:
    app = None
