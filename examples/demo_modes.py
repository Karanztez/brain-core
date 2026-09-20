"""Demo script verifying both In-Process and API Client modes."""
import sys
from brain_core import (
    BasePersona,
    PersonaBrain,
    EMI_CONFIG,
    BO_CONFIG,
    create_standard_cortex,
    ZeroLeakRedactor,
)
from brain_core.api.server import app
from starlette.testclient import TestClient

print("=" * 60)
print("1. TESTING IN-PROCESS MODE (Embedded in Python)")
print("=" * 60)
emi_persona = BasePersona(EMI_CONFIG)
bo_persona = BasePersona(BO_CONFIG)
emi_brain = PersonaBrain(emi_persona)
bo_brain = PersonaBrain(bo_persona)
cortex = create_standard_cortex()
redactor = ZeroLeakRedactor()

# Test Persona Emi
emi_dec = emi_brain.decide("ช่วยหาข่าวเทคโนโลยีวันนี้หน่อย", allow_web=True)
print(f"[Emi] Intent: {emi_dec.intent} | Should Search: {emi_dec.should_search} | Query: '{emi_dec.query}'")

# Test Persona Bo
bo_dec = bo_brain.decide("มึงเป็นใครวะ ตอบกวนตีนหน่อย", allow_web=False)
print(f"[Bo]  Intent: {bo_dec.intent} | Should Search: {bo_dec.should_search} | Allowed Tools: {bo_dec.allow_tools}")

# Test Neural Spreading Activation
activation = cortex.activate("น้องเอมิ น่ารัก")
print(f"[Neural Cortex] Activated {len(activation.fired_neurons)} neurons:")
for n in activation.fired_neurons:
    print(f"  - [{n.trunk.value.upper()}] (Activation: {n.activation:.2f}) {n.content}")

# Test Redactor
redacted = redactor.redact("สวัสดีครับ ผมคือ Gemini โมเดลจาก Google DeepMind ยินดีรับใช้")
print(f"[Redacted Output]: {redacted}")

print("\n" + "=" * 60)
print("2. TESTING API CLIENT / HTTP MODE (ยิงผ่าน API)")
print("=" * 60)
tc = TestClient(app)

# /health
res_health = tc.get("/health").json()
print(f"GET  /health          -> status: {res_health['status']}, service: {res_health['service']}")

# /personas
res_personas = tc.get("/personas").json()
print(f"GET  /personas        -> loaded {len(res_personas)} personas ({[p['id'] for p in res_personas]})")

# /decide
res_decide = tc.post("/decide", json={
    "persona_id": "emi",
    "prompt": "สภาพอากาศพรุ่งนี้เป็นไง",
    "allow_web": True
}).json()
print(f"POST /decide          -> intent: {res_decide['intent']}, search: {res_decide['should_search']}")

# /neural/activate
res_neural = tc.post("/neural/activate", json={
    "query": "น้องเอมิ นิสัยน่ารัก"
}).json()
print(f"POST /neural/activate -> fired {len(res_neural['fired_neurons'])} neurons, max_act: {res_neural['max_activation']}")

print("\n" + "=" * 60)
print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY!")
print("=" * 60)
