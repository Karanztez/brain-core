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
from brain_core.neural.cortex import NeuralCortex, create_standard_cortex
from brain_core.neural.neuron import MajorTrunk
from brain_core.tools.code_review import OpenCodeReviewTool

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
default_cortex = create_standard_cortex()
default_code_reviewer = OpenCodeReviewTool()


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


class NeuralActivateRequest(BaseModel):
    query: str


class NeuralNeuronDTO(BaseModel):
    id: str
    trunk: str
    content: str
    activation: float


class NeuralActivateResponse(BaseModel):
    primary_insight: str
    max_activation: float
    confidence: float
    fired_neurons: List[NeuralNeuronDTO]
    path_traces: List[str]


class GrowNeuronRequest(BaseModel):
    trunk: str
    neuron_id: str
    content: str
    tags: Optional[List[str]] = None
    baseline_weight: float = 1.0


class ConnectSynapseRequest(BaseModel):
    source_id: str
    target_id: str
    weight: float = 0.5
    relation: str = "associated_with"
    bidirectional: bool = False


class CorrectNeuronRequest(BaseModel):
    neuron_id: str
    corrected_content: str


class CodeReviewRequest(BaseModel):
    code: str
    language: str = "python"
    file_name: str = "snippet.py"
    persona_id: str = "emi"


class CodeReviewResponse(BaseModel):
    engine: str
    cli_installed: bool
    total_lines: int
    total_issues: int
    score: int
    verdict: str
    findings: List[Dict[str, Any]]
    formatted_comment: str


if HAS_FASTAPI:
    app = FastAPI(
        title="Brain-Core API",
        version="0.1.0",
        description="Multi-Persona AI Cognition, Neural Cortex & Reasoning Engine Service",
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

    @app.post("/neural/activate", response_model=NeuralActivateResponse)
    def neural_activate(req: NeuralActivateRequest) -> NeuralActivateResponse:
        res = default_cortex.activate(req.query)
        fired_dtos = [
            NeuralNeuronDTO(
                id=n.id,
                trunk=n.trunk.value,
                content=n.content,
                activation=round(n.activation, 3),
            )
            for n in res.fired_neurons
        ]
        return NeuralActivateResponse(
            primary_insight=res.primary_insight,
            max_activation=round(res.max_activation, 3),
            confidence=round(res.confidence, 3),
            fired_neurons=fired_dtos,
            path_traces=res.path_traces,
        )

    @app.post("/neural/grow")
    def neural_grow(req: GrowNeuronRequest) -> Dict[str, Any]:
        try:
            trunk_enum = MajorTrunk(req.trunk.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid trunk. Allowed: {[t.value for t in MajorTrunk]}")
        node = default_cortex.grow_neuron(
            trunk=trunk_enum,
            neuron_id=req.neuron_id,
            content=req.content,
            tags=set(req.tags or []),
            baseline_weight=req.baseline_weight,
        )
        return {"status": "created", "neuron_id": node.id, "trunk": node.trunk.value}

    @app.post("/neural/connect")
    def neural_connect(req: ConnectSynapseRequest) -> Dict[str, Any]:
        try:
            default_cortex.connect_synapse(
                source_id=req.source_id,
                target_id=req.target_id,
                weight=req.weight,
                relation=req.relation,
                bidirectional=req.bidirectional,
            )
            return {"status": "connected", "source": req.source_id, "target": req.target_id}
        except KeyError as err:
            raise HTTPException(status_code=404, detail=str(err))

    @app.post("/neural/correct")
    def neural_correct(req: CorrectNeuronRequest) -> Dict[str, Any]:
        node = default_cortex.learn_correction(req.neuron_id, req.corrected_content)
        return {"status": "corrected", "neuron_id": node.id, "content": node.content}

    @app.get("/neural/state")
    def neural_state() -> Dict[str, Any]:
        return default_cortex.export_state()

    @app.post("/tools/code-review", response_model=CodeReviewResponse)
    def review_code(req: CodeReviewRequest) -> CodeReviewResponse:
        report = default_code_reviewer.review_code(
            code=req.code,
            language=req.language,
            file_name=req.file_name,
            persona_id=req.persona_id,
        )
        return CodeReviewResponse(**report)
else:
    app = None


def main() -> None:
    """Run the Brain-Core API server via uvicorn CLI entrypoint."""
    import uvicorn
    uvicorn.run("brain_core.api.server:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
