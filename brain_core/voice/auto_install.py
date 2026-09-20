"""Auto-installer for Brain-Core Voice Dependencies.

Automatically detects missing packages (edge-tts) and installs them into the active
Python environment on the fly.
"""
from __future__ import annotations

import importlib
import logging
import subprocess
import sys
from typing import Optional, Any

logger = logging.getLogger("BrainCore.Voice.AutoInstall")

VOICE_REQUIREMENTS = {
    "edge_tts": "edge-tts>=6.1.12",
}


def ensure_voice_dependencies(silent: bool = False) -> bool:
    """Check and auto-install missing voice dependencies into the active environment."""
    missing_packages = []
    for mod_name, pkg_spec in VOICE_REQUIREMENTS.items():
        try:
            importlib.import_module(mod_name)
        except ImportError:
            missing_packages.append(pkg_spec)

    if not missing_packages:
        return True

    logger.info(f"📦 [BrainCore Voice] ตรวจพบแพ็กเกจระบบเสียงยังไม่ครบ: {missing_packages} — กำลังติดตั้งให้อัตโนมัติ...")
    try:
        cmd = [sys.executable, "-m", "pip", "install", "--no-input", *missing_packages]
        subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,
            check=True,
        )
        logger.info(f"✅ [BrainCore Voice] ติดตั้งแพ็กเกจสำเร็จเรียบร้อยแล้ว: {', '.join(missing_packages)}")
        importlib.invalidate_caches()
        return True
    except Exception as e:
        logger.error(f"❌ [BrainCore Voice] ไม่สามารถติดตั้งแพ็กเกจให้อัตโนมัติได้: {e}")
        return False


def get_edge_tts_module() -> Optional[Any]:
    """Dynamically get or auto-install and load the edge_tts module."""
    try:
        return importlib.import_module("edge_tts")
    except ImportError:
        ok = ensure_voice_dependencies()
        if ok:
            try:
                return importlib.import_module("edge_tts")
            except ImportError as e:
                logger.error(f"Failed to import edge_tts after installation: {e}")
    return None
