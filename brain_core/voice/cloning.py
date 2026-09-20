"""Voice Cloning Provider Integration (Fish Audio & ElevenLabs) for Brain-Core.

Enables true voice cloning for Anya Forger (Emi) using dedicated anime models:
1. Fish Audio (SOTA open-source zero-shot anime models with Anya presets)
2. ElevenLabs Multilingual v2 (Anya Voice Clone)
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional

import httpx

import re

logger = logging.getLogger("BrainCore.Voice.Cloning")

FISH_AUDIO_MODEL_ID = os.getenv("FISH_AUDIO_MODEL_ID", "78fc6c9c1e2b4d68affaa2cca995da3e")  # Emi Snaptik Cute Thai (Clean Vowels & No Noise)
FISH_AUDIO_MODEL = os.getenv("FISH_AUDIO_MODEL", "s2.1-pro-free")  # Free Tier S2.1 Pro Model

# Concurrency limiter to strictly adhere to Fish Audio 5 concurrent requests limit (prevents 429 Too Many Requests)
_fish_audio_semaphore: Optional[asyncio.Semaphore] = None


def _get_fish_audio_semaphore() -> asyncio.Semaphore:
    global _fish_audio_semaphore
    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        current_loop = None

    if _fish_audio_semaphore is None or getattr(_fish_audio_semaphore, "_loop", None) != current_loop:
        _fish_audio_semaphore = asyncio.Semaphore(5)
        setattr(_fish_audio_semaphore, "_loop", current_loop)
    return _fish_audio_semaphore

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")  # Anya Forger Voice ID


THAI_DIGITS = ["ศูนย์", "หนึ่ง", "สอง", "สาม", "สี่", "ห้า", "หก", "เจ็ด", "แปด", "เก้า"]
THAI_UNITS = ["", "สิบ", "ร้อย", "พัน", "หมื่น", "แสน", "ล้าน"]


def int_to_thai_text(n: int) -> str:
    """Convert an integer up to billions to Thai text words."""
    if n == 0:
        return "ศูนย์"
    if n < 0:
        return "ลบ" + int_to_thai_text(-n)

    if n >= 10_000_000:
        millions = n // 1_000_000
        rem = n % 1_000_000
        res = int_to_thai_text(millions) + "ล้าน"
        if rem > 0:
            res += int_to_thai_text(rem)
        return res

    s = str(n)
    length = len(s)
    result = []

    for i, ch in enumerate(s):
        digit = int(ch)
        pos = length - i - 1
        if digit == 0:
            continue

        unit = THAI_UNITS[pos]
        if pos == 1:
            if digit == 1:
                result.append("สิบ")
            elif digit == 2:
                result.append("ยี่สิบ")
            else:
                result.append(THAI_DIGITS[digit] + "สิบ")
        elif pos == 0:
            if digit == 1 and length > 1:
                result.append("เอ็ด")
            else:
                result.append(THAI_DIGITS[digit])
        else:
            result.append(THAI_DIGITS[digit] + unit)

    return "".join(result)


def convert_numbers_in_text(text: str) -> str:
    """Convert numbers, decimals, and percentages to spoken Thai text."""
    # 1. Clean commas in numbers (e.g. 1,000 -> 1000)
    text = re.sub(r"(\d),(\d)", r"\1\2", text)
    # 2. Percentages (e.g. 100% -> 100 เปอร์เซ็นต์)
    text = re.sub(r"(\d+)%", r"\1 เปอร์เซ็นต์", text)

    # 3. Decimals (e.g. 10.5 -> สิบจุดห้า)
    def replace_decimal(match):
        integer_part = match.group(1)
        decimal_part = match.group(2)
        int_thai = int_to_thai_text(int(integer_part))
        dec_thai = "".join(THAI_DIGITS[int(d)] for d in decimal_part)
        return f" {int_thai}จุด{dec_thai} "

    text = re.sub(r"\b(\d+)\.(\d+)\b", replace_decimal, text)

    # 4. Standard integers (e.g. 100 -> หนึ่งร้อย)
    def replace_int(match):
        num = int(match.group(0))
        return f" {int_to_thai_text(num)} "

    text = re.sub(r"\b\d+\b", replace_int, text)
    return text


THAI_PHONETIC_REPLACEMENTS = [
    # คำสมาส / บาลีสันสกฤต สระอะลดรูป และคำที่ AI มักอ่านควบ/กลืนเสียง
    (r"ภารกิจ", "พาระกิด"),
    (r"ปฏิบัติ", "ปะติบัด"),
    (r"กิจกรรม", "กิดจะกำ"),
    (r"ธรรมชาติ", "ทำมะชาด"),
    (r"ประวัติศาสตร์", "ประหวัดติสาด"),
    (r"โทรทัศน์", "โทระทัด"),
    (r"โทรศัพท์", "โทระสับ"),
    (r"อุณหภูมิ", "อุนหะพูม"),
    (r"มหัศจรรย์", "มะหัดสะจัน"),
    (r"สมาธิ", "สะมาทิ"),
    (r"สัปดาห์", "สับดา"),
    (r"มัธยม", "มัดทะยม"),
    (r"สาธารณะ", "สาทาระนะ"),
    (r"ราชการ", "ราดชะกาน"),
    (r"สุขภาพ", "สุกขะพาบ"),
    (r"สุขศึกษา", "สุกขะสึกสา"),
    (r"ศิลปะ", "สินละปะ"),
    (r"เกษตร", "กะเสด"),
    (r"โอกาส", "โอกาด"),
    (r"กิโลเมตร", "กิโลเมด"),
    (r"มกราคม", "มกกะราคม"),
    (r"กุมภาพันธ์", "กุมพาพัน"),
    (r"มีนาคม", "มีนาคม"),
    (r"เมษายน", "เมสายง"),
    (r"พฤษภาคม", "พรึดสะพาคม"),
    (r"มิถุนายน", "มิถุนายง"),
    (r"กรกฎาคม", "กะระกะดาคม"),
    (r"สิงหาคม", "สิงหาคม"),
    (r"กันยายน", "กันยายง"),
    (r"ตุลาคม", "ตุลาคม"),
    (r"พฤศจิกายน", "พรึดสะจิกายง"),
    (r"ธันวาคม", "ทันวาคม"),
    (r"คุณครู", "คุน ครู"),
    (r"สำคัญ", "สำคัน"),
    (r"ปัจจุบัน", "ปัดจุบัน"),
    (r"พัฒนา", "พัดทะนา"),
    (r"อัจฉริยะ", "อัดฉะริยะ"),
    (r"มนุษย์", "มะนุด"),
    (r"สัญลักษณ์", "สันยาลัก"),
    (r"กษัตริย์", "กะสัด"),
    (r"บรรยากาศ", "บันยากาด"),
    (r"สวรรค์", "สะหวัน"),
    (r"ประโยชน์", "ประโหยด"),
    (r"สมบูรณ์", "สมบูน"),
    (r"พิเศษ", "พิเสด"),
    (r"สำเร็จ", "สำเหร็ด"),
    (r"อนาคต", "อะนาคด"),
    (r"อัศจรรย์", "อัดสะจัน"),
    (r"ปลอดภัย", "ปลอดพัย"),
    (r"บริสุทธิ์", "บอริสุด"),
    (r"บริจาค", "บอริจาก"),
    (r"ปัญญา", "ปันยา"),
    (r"จักรวาล", "จักกระวาน"),
    (r"ปฏิเสธ", "ปะติเสด"),
    (r"ทัศนคติ", "ทัดสะนะคะติ"),
    (r"บุคลิกภาพ", "บุกคะลิกพะพาบ"),
    (r"วิทยาศาสตร์", "วิดทะยาสาด"),
    (r"เทคโนโลยี", "เทกโนโลยี"),
]


def prepare_thai_text_for_fish_audio(text: str) -> str:
    """Optimize Thai text phonetics, clause pacing, numbers, and vowel clarity for Fish Audio S2.1."""
    if not text:
        return text

    # 1. Expand maiyamok (ๆ) with clear separation
    cleaned = re.sub(r"(\S)ๆ", r"\1 \1", text)

    # 2. Convert all numbers to spoken Thai text (e.g. 100 -> หนึ่งร้อย, 1,000 -> หนึ่งพัน)
    cleaned = convert_numbers_in_text(cleaned)

    # 3. Apply Thai phonetic dictionary for implicit syllables and Sanskrit/Pali words (e.g. ภารกิจ -> พาระกิด)
    for pat, repl in THAI_PHONETIC_REPLACEMENTS:
        cleaned = re.sub(pat, repl, cleaned)

    # 4. Fix "เป็นไง" / "ยังไง" / "ไง" / "เป็นไหง" to phonetic "งัย"
    # Eliminates the unwanted "ห นำ" (ไหง/เหน่อ) sound in Fish Audio
    cleaned = re.sub(r"เป็น\s*ไหง", "เป็นงัย", cleaned)
    cleaned = re.sub(r"เป็น\s*ไง", "เป็นงัย", cleaned)
    cleaned = re.sub(r"ยัง\s*ไง", "ยังงัย", cleaned)
    cleaned = re.sub(r"(?<=\s)ไง(?=[\s!?,\.คะครับจ้า]|$)", "งัย", cleaned)

    # 4. Ensure clear syllable boundaries around "เหมือน" so leading 'ห' is always articulated (never swallowed as 'เมือน')
    cleaned = re.sub(r"([^\s])เหมือน", r"\1 เหมือน", cleaned)
    cleaned = re.sub(r"เหมือน([^\s])", r"เหมือน \1", cleaned)

    # 5. Convert question particle "ไหม" / "มั้ย" to high-tone "มั๊ย"
    # Prevents Fish Audio from reading "มั้ย" as slow formal rising "ไหม"
    cleaned = re.sub(r"(?<=[\sก-๙])ไหม(?=[\s!?,\.คะครับจ้า]|$)(?![่-๋์])", "มั๊ย", cleaned)
    cleaned = re.sub(r"(?<=[\sก-๙])มั้ย(?=[\s!?,\.คะครับจ้า]|$)(?![่-๋์])", "มั๊ย", cleaned)
    cleaned = re.sub(r"^ไหม(?=[\s!?,\.คะครับจ้า]|$)(?![่-๋์])", "มั๊ย", cleaned)
    cleaned = re.sub(r"^มั้ย(?=[\s!?,\.คะครับจ้า]|$)(?![่-๋์])", "มั๊ย", cleaned)

    # 6. Ensure separation before "มั๊ย" if directly glued to preceding word
    cleaned = re.sub(r"([^\s])มั๊ย", r"\1 มั๊ย", cleaned)

    # 7. Ensure natural pauses before standard Thai particles (นะคะ, ค่ะ, ครับ, จ้า, นะ)
    cleaned = re.sub(r"([^\s])(นะคะ|นะค่ะ|ค่ะ|ครับ|จ้า|นะจ๊ะ|นะคะ!|ค่ะ!|ครับ!)", r"\1 \2", cleaned)

    # 8. Ensure natural pauses around punctuation and sentence boundaries
    cleaned = re.sub(r"([!?,])(?=[^\s])", r"\1 ", cleaned)

    # 9. Normalize whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


async def generate_cloned_anya_speech(text: str) -> Optional[bytes]:
    """Attempt to generate voice-cloned speech for Anya using configured provider."""
    api_key = os.getenv("FISH_AUDIO_API_KEY") or FISH_AUDIO_API_KEY
    model_id = os.getenv("FISH_AUDIO_MODEL_ID") or FISH_AUDIO_MODEL_ID
    model = os.getenv("FISH_AUDIO_MODEL") or FISH_AUDIO_MODEL

    logger.info(f"🎙️ [VoiceCloning] Requesting Anya voice clone (key={api_key[:8]}... model_id={model_id[:8]}... model={model})")

    # 1. Try Fish Audio if configured (defaults to free tier model s2.1-pro-free)
    if api_key and model_id:
        try:
            audio = await _call_fish_audio(text, api_key, model_id, model=model)
            if audio:
                logger.info(f"✨ [FishAudio] Successfully generated Anya voice ({len(audio)} bytes)")
                return audio
            else:
                logger.warning("⚠️ [FishAudio] API returned empty audio")
        except Exception as e:
            logger.error(f"❌ [FishAudio] Exception during generation: {e}", exc_info=True)
    else:
        logger.warning(f"⚠️ [VoiceCloning] Missing credentials: api_key={bool(api_key)}, model_id={bool(model_id)}")

    # 2. Try ElevenLabs if configured
    el_key = os.getenv("ELEVENLABS_API_KEY") or ELEVENLABS_API_KEY
    el_voice = os.getenv("ELEVENLABS_VOICE_ID") or ELEVENLABS_VOICE_ID
    if el_key and el_voice:
        try:
            audio = await _call_elevenlabs(text, el_key, el_voice)
            if audio:
                logger.info("✨ Generated Anya voice via ElevenLabs Clone")
                return audio
        except Exception as e:
            logger.warning(f"ElevenLabs generation failed: {e}")

    return None


# Persistent Keep-Alive HTTP client pool (saves 1.0-1.2s TCP+TLS handshake per request)
_fish_audio_client: Optional[httpx.AsyncClient] = None


def _get_fish_audio_client() -> httpx.AsyncClient:
    global _fish_audio_client
    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        current_loop = None

    if (
        _fish_audio_client is None
        or _fish_audio_client.is_closed
        or getattr(_fish_audio_client, "_loop", None) != current_loop
    ):
        _fish_audio_client = httpx.AsyncClient(
            timeout=25.0,
            limits=httpx.Limits(max_keepalive_connections=8, max_connections=20, keepalive_expiry=120.0),
        )
        setattr(_fish_audio_client, "_loop", current_loop)
    return _fish_audio_client


async def _call_fish_audio(
    text: str,
    api_key: str,
    reference_id: str,
    model: str = "s2.1-pro-free",
) -> Optional[bytes]:
    """Call Fish Audio TTS API with optimized Thai phonetic clarity parameters."""
    url = "https://api.fish.audio/v1/tts"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "model": model,
    }
    payload = {
        "text": prepare_thai_text_for_fish_audio(text),
        "reference_id": reference_id,
        "format": "mp3",
        "latency": os.getenv("FISH_AUDIO_LATENCY", "normal"),
        "temperature": float(os.getenv("FISH_AUDIO_TEMPERATURE", "0.65")),
        "normalize": os.getenv("FISH_AUDIO_NORMALIZE", "true").lower() == "true",
        "prosody": {
            "speed": float(os.getenv("FISH_AUDIO_SPEED", "1.0")),
            "volume": 0.0,
            "normalize_loudness": True,
        },
    }
    client = _get_fish_audio_client()
    async with _get_fish_audio_semaphore():
        res = await client.post(url, headers=headers, json=payload)
        if res.status_code == 200 and len(res.content) > 1000:
            return res.content
        logger.warning(f"Fish Audio returned {res.status_code}: {res.text[:150]}")
    return None


async def _call_elevenlabs(text: str, api_key: str, voice_id: str) -> Optional[bytes]:
    """Call ElevenLabs Multilingual v2 API."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.45,
            "similarity_boost": 0.85,
            "style": 0.35,
        },
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.post(url, headers=headers, json=payload)
        if res.status_code == 200 and len(res.content) > 1000:
            return res.content
        logger.warning(f"ElevenLabs returned {res.status_code}: {res.text[:150]}")
    return None
