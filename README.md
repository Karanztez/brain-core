# 🧠 Brain-Core

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

**Brain-Core** คือระบบสมองกล AI กลาง (Cognition & Reasoning Core) สำหรับสถาปัตยกรรมแบบ **Multi-Persona / Multi-Agent** ที่ออกแบบมาเพื่อแยกตัวตน, การใช้เหตุผล, ความจำ, เครื่องมือ และการสวมบทบาทระหว่างบอทหลายตัว (เช่น **น้องเอมิ**, **เฮียโบ้** หรือบอทตัวใหม่ๆ) ออกจากกันอย่างเด็ดขาด ป้องกันการจำสลับตัวตน และมาพร้อมระบบความปลอดภัย **Zero-Leak Redaction** ป้องกันชื่อโมเดล AI รั่วไหล 100%

---

## ✨ คุณสมบัติเด่น (Features)

1. **🎭 Decoupled Persona Cognition (`PersonaBrain`)**
   - แยกชุดความคิดและการตัดสินใจ (Intent Classification) ตามบริบทของแต่ละ Persona
   - กำหนดสิทธิ์เครื่องมือ (Tool Permissions), สรรพนาม, และข้อห้ามแยกเป็นรายตัวตน
2. **🔄 Shared Channel Context Buffer (`ChannelContextBuffer`)**
   - บัฟเฟอร์กิจกรรมส่วนกลางของช่องแชท ให้บอททุกตัวรับรู้คำถามและคำตอบของกันและกันแบบเรียลไทม์
   - ป้องกันการถามหาโจทย์ซ้ำ และช่วยให้บอทตัวที่สองสามารถรับลูกต่อจากบอทตัวแรกได้อย่างแนบเนียน
3. **🛡️ Zero-Leak Redactor (`ZeroLeakRedactor`)**
   - กรองและตัดชื่อโมเดล AI (เช่น `Gemini Vision`, `Gemini`, `GPT`, `Claude`) ออกจากข้อความและ Discord Embeds นอกโค้ดบล็อก
4. **💬 Persona-Adaptive Fallbacks (`PersonaFallbackManager`)**
   - คืนค่าข้อความตอบสนองเมื่อเกิด Error / Timeout / Empty Response ตรงตามเพศและบุคลิกของบอท (โบ้ไม่หลุดพูด "ค่ะ", เอมิไม่หลุดพูด "ครับ")
5. **⚖️ Multi-Agent Turn Arbitration (`TurnEvaluator`)**
   - ตัดสินใจว่าบอทตัวใดควรตอบในกรณีห้องส่วนตัว, ห้องประจำการร่วม (Shared Station), หรือการเรียกชื่อเจาะจง
6. **🌐 Dual Mode: Python Library & REST API**
   - ใช้งานเป็น Python Package (`import brain_core`) หรือรันเป็น HTTP Microservice ด้วย FastAPI

---

## 📦 การติดตั้ง (Installation)

### 1. ติดตั้งแบบ Local Package (Editable Mode)
```bash
cd brain-core
pip install -e .
```

### 2. ติดตั้งพร้อม API Server (FastAPI + Uvicorn)
```bash
pip install -e ".[api]"
```

---

## 🚀 ตัวอย่างการใช้งาน (Quickstart)

### 1. การใช้งานในฐานะ Python Library

```python
from brain_core import (
    PersonaRegistry,
    PersonaBrain,
    EMI_CONFIG,
    BO_CONFIG,
    ChannelContextBuffer,
    ZeroLeakRedactor,
    PersonaFallbackManager
)

# 1. ลงทะเบียน Persona
registry = PersonaRegistry()
emi = registry.register_config(EMI_CONFIG, aliases=["น้องเอมิ"])
bo = registry.register_config(BO_CONFIG, aliases=["เฮียโบ้"])

# 2. วิเคราะห์ Intent ด้วยสมองของแต่ละตัวตน
emi_brain = PersonaBrain(emi)
bo_brain = PersonaBrain(bo)

decision_emi = emi_brain.decide("FLAG_UmlZ_VGhpcz0= คืออะไร")
print(decision_emi.intent)  # IntentType.DECODE
print(decision_emi.allowed_tools)  # ['decode_inspect_data']

# 3. Fallback ตามบุคลิกภาพ
fallback_bo = PersonaFallbackManager.get_fallback(bo, error_type="empty")
print(fallback_bo)  # 'เฮียโบ้ยังไม่พบสาระสำคัญในคำตอบนี้ครับคุณพี่'

# 4. ลบการรั่วไหลของชื่อโมเดลภายนอก
redactor = ZeroLeakRedactor()
clean_text = redactor.redact("ตรวจพบรูปภาพอันตรายโดย [Gemini Vision]")
print(clean_text)  # 'ตรวจพบรูปภาพอันตรายโดย [ระบบตรวจจับภาพสแกม]'
```

### 2. การสร้าง Persona ใหม่ (Custom Persona)

```python
from brain_core import PersonaConfig, PersonaGender, BasePersona

investigator_config = PersonaConfig(
    id="detective",
    name="นักสืบโคนัน",
    gender=PersonaGender.MALE,
    system_prompt="คุณคือนักสืบเอกชนผู้คลี่คลายปริศนาด้วยเหตุผลและหลักฐาน",
    greeting="ความจริงมีเพียงหนึ่งเดียวเท่านั้น!",
    empty_fallback="หลักฐานยังไม่เพียงพอที่จะสรุปคดีครับ",
    allowed_tools=["decode_inspect_data", "search_web"]
)

detective = registry.register_config(investigator_config)
```

### 3. รันเป็น REST API Microservice

```bash
uvicorn brain_core.api.server:app --host 0.0.0.0 --port 8000
```

- **GET** `/personas`: ดูรายชื่อบอท/Persona ทั้งหมด
- **POST** `/decide`: วิเคราะห์ Intent และเครื่องมือที่ควรใช้
- **POST** `/redact`: กรองข้อความรั่วไหล

---

## 🧪 การทดสอบ (Testing)

```bash
pytest tests/ -v
# หรือใช้ unittest
python -m unittest discover tests
```

---

## 📄 License
MIT License - Karanztez
