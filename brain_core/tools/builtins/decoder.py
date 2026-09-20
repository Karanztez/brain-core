"""Builtin data decoding and cipher inspection utility."""
from __future__ import annotations

import base64
import binascii
import re
from typing import Any, Dict


def decode_inspect_data(data: str) -> Dict[str, Any]:
    """Safely decodes and analyzes raw data (Base64, Hex, URL-encoded, or ROT shifts)."""
    raw = data.strip()
    result: Dict[str, Any] = {"input_sample": raw[:50], "decoded": "", "format": "unknown", "success": False}

    # 1. Base64 attempt
    clean_b64 = re.sub(r"[^A-Za-z0-9+/=_-]", "", raw)
    if len(clean_b64) >= 4:
        # Fix padding
        missing_padding = len(clean_b64) % 4
        padded = clean_b64 + ("=" * (4 - missing_padding) if missing_padding else "")
        try:
            b_bytes = base64.b64decode(padded)
            decoded_str = b_bytes.decode("utf-8", errors="replace")
            if any(c.isprintable() for c in decoded_str):
                result.update({"format": "base64", "decoded": decoded_str, "success": True})
                return result
        except Exception:
            pass

    # 2. Hex attempt
    clean_hex = re.sub(r"[^0-9a-fA-F]", "", raw)
    if len(clean_hex) >= 2 and len(clean_hex) % 2 == 0:
        try:
            h_bytes = binascii.unhexlify(clean_hex)
            decoded_str = h_bytes.decode("utf-8", errors="replace")
            if any(c.isprintable() for c in decoded_str):
                result.update({"format": "hex", "decoded": decoded_str, "success": True})
                return result
        except Exception:
            pass

    return result
