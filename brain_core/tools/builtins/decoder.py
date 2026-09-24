"""Safe, bounded decoding and CTF inspection utilities."""
from __future__ import annotations

import base64
import binascii
import codecs
import gzip
import html
import math
import re
import urllib.parse
import zlib
from collections import Counter, deque
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

MAX_INPUT_BYTES = 64 * 1024
MAX_OUTPUT_BYTES = 64 * 1024
MAX_DEPTH = 6
MAX_CANDIDATES = 64
FLAG_PATTERN = re.compile(r"(?i)(?:flag|ctf|picoctf|htb|thm|hackthebox|tryhackme)\{[^\r\n{}]{1,256}\}")
MAGIC_SIGNATURES: Tuple[Tuple[bytes, str], ...] = (
    (b"\x89PNG\r\n\x1a\n", "png"), (b"\xff\xd8\xff", "jpeg"),
    (b"GIF87a", "gif"), (b"GIF89a", "gif"), (b"PK\x03\x04", "zip"),
    (b"\x1f\x8b", "gzip"), (b"%PDF-", "pdf"), (b"\x7fELF", "elf"),
    (b"MZ", "windows-pe"), (b"SQLite format 3\x00", "sqlite"),
)


@dataclass
class _Candidate:
    data: bytes
    path: List[str]
    score: float = 0.0


def _limited(data: bytes) -> bytes:
    if len(data) > MAX_OUTPUT_BYTES:
        raise ValueError("decoded output exceeds safety limit")
    return data


def _text(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")


def _printable_ratio(text: str) -> float:
    return 0.0 if not text else sum(c.isprintable() or c in "\r\n\t" for c in text) / len(text)


def _entropy(data: bytes) -> float:
    if not data:
        return 0.0
    size = len(data)
    return -sum((count / size) * math.log2(count / size) for count in Counter(data).values())


def _magic(data: bytes) -> Optional[str]:
    return next((name for prefix, name in MAGIC_SIGNATURES if data.startswith(prefix)), None)


def _flags(text: str) -> List[str]:
    return list(dict.fromkeys(match.group(0) for match in FLAG_PATTERN.finditer(text)))


def _score(data: bytes) -> float:
    text = _text(data)
    score = _printable_ratio(text) * 55
    score += min(len(_flags(text)) * 35, 35)
    score += 15 if _magic(data) else 0
    score += 8 if re.search(r"(?i)\b(the|this|flag|รหัส|คำตอบ|ข้อความ)\b", text) else 0
    score -= min(text.count("\ufffd") * 2, 25)
    return round(max(0.0, min(score, 100.0)), 2)


def _decode_hex(text: str) -> bytes:
    compact = re.sub(r"(?:0x)|[\s:_-]", "", text, flags=re.I)
    if len(compact) < 2 or len(compact) % 2 or not re.fullmatch(r"[0-9a-fA-F]+", compact):
        raise ValueError
    return _limited(binascii.unhexlify(compact))


def _decode_base64(text: str) -> bytes:
    compact = re.sub(r"\s+", "", text)
    if len(compact) < 4 or not re.fullmatch(r"[A-Za-z0-9+/_=-]+", compact):
        raise ValueError
    compact += "=" * (-len(compact) % 4)
    return _limited(base64.b64decode(compact, altchars=b"-_", validate=True))


def _decode_base32(text: str) -> bytes:
    compact = re.sub(r"\s+", "", text).upper()
    if len(compact) < 8 or not re.fullmatch(r"[A-Z2-7=]+", compact):
        raise ValueError
    compact += "=" * (-len(compact) % 8)
    return _limited(base64.b32decode(compact, casefold=True))


def _decode_base85(text: str) -> bytes:
    compact = re.sub(r"\s+", "", text)
    if len(compact) < 5:
        raise ValueError
    return _limited(base64.b85decode(compact))


def _decode_url(text: str) -> bytes:
    if not re.search(r"%[0-9a-fA-F]{2}|\+", text):
        raise ValueError
    decoded = urllib.parse.unquote_to_bytes(text.replace("+", " "))
    if decoded == text.encode():
        raise ValueError
    return _limited(decoded)


def _decode_html(text: str) -> bytes:
    if not re.search(r"&(?:#\d+|#x[0-9a-fA-F]+|[A-Za-z]+);", text):
        raise ValueError
    decoded = html.unescape(text)
    if decoded == text:
        raise ValueError
    return _limited(decoded.encode())


def _decode_unicode(text: str) -> bytes:
    if not re.search(r"\\(?:u[0-9a-fA-F]{4}|U[0-9a-fA-F]{8}|x[0-9a-fA-F]{2})", text):
        raise ValueError
    return _limited(codecs.decode(text, "unicode_escape").encode())


def _decode_numbers(text: str, base: int, pattern: str) -> bytes:
    parts = re.findall(pattern, text)
    if not parts or re.sub(pattern, "", text).strip(" ,;:_-"):
        raise ValueError
    return _limited(bytes(int(part, base) for part in parts))


def _rot13(text: str) -> bytes:
    if not re.search(r"[A-Za-z]", text):
        raise ValueError
    return codecs.decode(text, "rot_13").encode()


def _reverse(text: str) -> bytes:
    if len(text) < 4:
        raise ValueError
    return text[::-1].encode()


TEXT_DECODERS: Tuple[Tuple[str, Callable[[str], bytes]], ...] = (
    ("hex", _decode_hex), ("base64", _decode_base64), ("base32", _decode_base32),
    ("base85", _decode_base85), ("url", _decode_url), ("html-entity", _decode_html),
    ("unicode-escape", _decode_unicode),
    ("binary-ascii", lambda v: _decode_numbers(v, 2, r"(?<![01])[01]{8}(?![01])")),
    ("octal-ascii", lambda v: _decode_numbers(v, 8, r"(?<![0-7])[0-7]{3}(?![0-7])")),
    ("decimal-ascii", lambda v: _decode_numbers(v, 10, r"(?<!\d)(?:[3-9]\d|1[01]\d|12[0-7])(?!\d)")),
    ("rot13", _rot13), ("reverse", _reverse),
)


def _byte_decoders(data: bytes) -> Iterable[Tuple[str, bytes]]:
    if data.startswith(b"\x1f\x8b"):
        try:
            yield "gzip", _limited(gzip.decompress(data))
        except (OSError, EOFError, ValueError):
            pass
    if len(data) >= 2 and data[0] == 0x78:
        try:
            yield "zlib", _limited(zlib.decompress(data))
        except (zlib.error, ValueError):
            pass


def _xor_candidates(data: bytes, limit: int = 3) -> Iterable[Tuple[str, bytes]]:
    if not data or len(data) > 4096:
        return
    ranked = []
    for key in range(1, 256):
        decoded = bytes(value ^ key for value in data)
        score = _score(decoded)
        if score >= 55:
            ranked.append((score, key, decoded))
    for _, key, decoded in sorted(ranked, reverse=True)[:limit]:
        yield f"xor-single-byte:0x{key:02x}", decoded


def analyze_ctf_data(data: str, max_depth: int = MAX_DEPTH) -> Dict[str, Any]:
    """Recursively decode and rank candidates without executing decoded data."""
    raw = data.strip().encode()
    if not raw:
        return {"success": False, "error": "empty input", "candidates": [], "flags": []}
    if len(raw) > MAX_INPUT_BYTES:
        return {"success": False, "error": "input exceeds 64 KiB safety limit", "candidates": [], "flags": []}
    depth_limit = max(0, min(max_depth, MAX_DEPTH))
    queue = deque([_Candidate(raw, [])])
    seen = {raw}
    found: List[_Candidate] = []
    while queue and len(seen) <= MAX_CANDIDATES:
        current = queue.popleft()
        if current.path:
            current.score = _score(current.data)
            found.append(current)
        if len(current.path) >= depth_limit:
            continue
        transformations = list(_byte_decoders(current.data))
        text = _text(current.data)
        if "\ufffd" not in text:
            for name, decoder in TEXT_DECODERS:
                try:
                    transformations.append((name, decoder(text)))
                except (ValueError, TypeError, binascii.Error, UnicodeError):
                    pass
        transformations.extend(_xor_candidates(current.data))
        for name, decoded in transformations:
            if not decoded or decoded == current.data or decoded in seen:
                continue
            seen.add(decoded)
            queue.append(_Candidate(decoded, current.path + [name]))
            if len(seen) >= MAX_CANDIDATES:
                break
    ranked = sorted(found, key=lambda c: (bool(_flags(_text(c.data))), c.score), reverse=True)
    results, all_flags = [], []
    for candidate in ranked[:10]:
        text = _text(candidate.data)
        flags = _flags(text)
        all_flags.extend(flags)
        results.append({"path": candidate.path, "format": candidate.path[-1], "decoded": text[:4096],
                        "score": candidate.score, "flags": flags, "file_type": _magic(candidate.data),
                        "entropy": round(_entropy(candidate.data), 3), "size": len(candidate.data)})
    return {"success": bool(results), "input_sample": data.strip()[:50], "candidates": results,
            "flags": list(dict.fromkeys(all_flags)),
            "limits": {"max_depth": depth_limit, "max_candidates": MAX_CANDIDATES, "max_bytes": MAX_OUTPUT_BYTES},
            "warnings": ["Decoded content was inspected only; nothing was executed or opened."]}


def decode_inspect_data(data: str) -> Dict[str, Any]:
    """Backward-compatible wrapper returning the highest-ranked candidate."""
    report = analyze_ctf_data(data)
    candidates = report.get("candidates", [])
    if not candidates:
        return {**report, "decoded": "", "format": "unknown"}
    best = candidates[0]
    return {**report, "decoded": best["decoded"], "format": best["format"],
            "path": best["path"], "score": best["score"]}
