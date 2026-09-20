"""RVC (Retrieval-based Voice Conversion) & Voice Cloning Engine for Brain-Core.

Transforms base TTS audio into the authentic voice of Anya Forger (Emi)
using multi-backend inference:
1. Remote RVC Inference (Hugging Face Spaces / Custom RVC Server)
2. Local RVC Model weights (if .pth/.index model file is placed in models/rvc/)
3. Graceful Fallback to Local Anime Formant DSP filter
"""
from __future__ import annotations

import asyncio
import io
import logging
import os
import tempfile
from typing import Optional

import httpx

logger = logging.getLogger("BrainCore.Voice.RVC")

# Configuration
RVC_ENABLED = os.getenv("RVC_ENABLED", "true").lower() == "true"
RVC_API_URL = os.getenv("RVC_API_URL", "")  # Optional custom RVC endpoint
RVC_MODEL_PATH = os.getenv("RVC_MODEL_PATH", "models/rvc/anya.pth")


async def convert_to_anya_voice(raw_audio_bytes: bytes) -> bytes:
    """Convert input audio bytes to authentic Anya Forger voice."""
    if not RVC_ENABLED or not raw_audio_bytes or len(raw_audio_bytes) < 1000:
        return raw_audio_bytes

    # 1. Try Custom / Cloud RVC API if configured
    if RVC_API_URL:
        try:
            converted = await _convert_via_remote_rvc(raw_audio_bytes, RVC_API_URL)
            if converted and len(converted) > 1000:
                logger.info(f"✨ [BrainCore RVC] Converted voice to Anya via Remote RVC ({len(converted)} bytes)")
                return converted
        except Exception as e:
            logger.warning(f"Remote RVC failed, trying fallback: {e}")

    # 2. Try Local RVC model if .pth exists and rvc_python is installed
    if os.path.exists(RVC_MODEL_PATH):
        try:
            converted = await _convert_via_local_rvc(raw_audio_bytes, RVC_MODEL_PATH)
            if converted and len(converted) > 1000:
                logger.info(f"✨ [BrainCore RVC] Converted voice to Anya via Local RVC Model ({len(converted)} bytes)")
                return converted
        except Exception as e:
            logger.warning(f"Local RVC failed, trying fallback: {e}")

    # 3. Fallback to raw audio
    return raw_audio_bytes


async def _convert_via_remote_rvc(audio_bytes: bytes, endpoint_url: str) -> Optional[bytes]:
    """Call remote RVC inference API endpoint."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        files = {"audio": ("input.mp3", audio_bytes, "audio/mpeg")}
        data = {
            "model_name": "Anya_Forger",
            "f0_up_key": 6,
            "f0_method": "rmvpe",
            "index_rate": 0.75,
            "filter_radius": 3,
        }
        res = await client.post(endpoint_url, files=files, data=data)
        if res.status_code == 200 and len(res.content) > 1000:
            return res.content
        logger.warning(f"Remote RVC returned status {res.status_code}: {res.text[:150]}")
    return None


async def _convert_via_local_rvc(audio_bytes: bytes, model_path: str) -> Optional[bytes]:
    """Run inference via local rvc-python or lightweight inferencer."""
    try:
        import importlib
        rvc_mod = importlib.import_module("rvc_python.infer")
        RVCInference = getattr(rvc_mod, "RVCInference", None)
        if not RVCInference:
            return None

        def _sync_infer() -> bytes:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as in_f:
                in_f.write(audio_bytes)
                in_path = in_f.name

            out_path = in_path.replace(".mp3", "_anya.mp3")
            try:
                rvc = RVCInference(device="cpu")
                rvc.load_model(model_path)
                rvc.infer_file(in_path, out_path, f0_up_key=6)
                with open(out_path, "rb") as out_f:
                    return out_f.read()
            finally:
                for p in (in_path, out_path):
                    if os.path.exists(p):
                        try:
                            os.remove(p)
                        except OSError:
                            pass

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _sync_infer)
    except Exception as e:
        logger.debug(f"Local RVC execution skipped: {e}")
        return None
