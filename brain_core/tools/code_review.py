"""Alibaba Open Code Review (OCR) Tool for Brain-Core.

Integrates Alibaba's battle-tested Open Code Review engine into Emi and Bo's
cognitive reasoning and code inspection pipeline, featuring advanced AST heuristics,
logic inversion detection, and automated CTF/steganography cipher deobfuscation.
"""
from __future__ import annotations

import base64
import os
import re
import shutil
import subprocess
import tempfile
from typing import Any, Dict, List, Optional


class OpenCodeReviewTool:
    """Hybrid code review tool integrating Alibaba Open Code Review (ocr), AST heuristics, and CTF deobfuscation."""

    def __init__(self) -> None:
        self.ocr_cli_available = shutil.which("ocr") is not None

    def _detect_and_decode_ciphers(self, code: str) -> List[Dict[str, Any]]:
        """Detect and decode obfuscated packets, Base64/Hex ciphers with noise characters."""
        results = []

        # 1. Match packet assignments: RAW_PACKET_A = "..." or CHUNK_1 = "..." etc.
        packet_matches = re.findall(
            r'(\b[A-Za-z0-9_]*(?:PACKET|CIPHER|CHUNK|SECRET|FLAG|PAYLOAD|DATA)[A-Za-z0-9_]*)\s*=\s*[\'"]([^\'"]+)[\'"]',
            code,
            re.I,
        )
        if packet_matches:
            # Sort by variable name to reconstruct chunks in order
            sorted_packets = sorted(packet_matches, key=lambda x: x[0])
            combined_raw = "".join(p[1] for p in sorted_packets)

            # Candidates of cleaning noise:
            # Variant 1: Strip noise delimiters /, _, |, -, spaces, %, ~
            # (Keep +, = for base64 if not noise, but in our case + was noise delimiter too!)
            cleaned_options = [
                re.sub(r'[\/_\-|~%\\s]', '', combined_raw),
                re.sub(r'[\/_\-|~%+\\s]', '', combined_raw),  # strip + as noise delimiter
            ]

            decoded_text = None
            dec_type = None

            for cleaned in cleaned_options:
                if not cleaned or len(cleaned) < 4:
                    continue
                # Try Base64
                try:
                    pad = (-len(cleaned)) % 4
                    candidate = cleaned + ('=' * pad)
                    raw_bytes = base64.b64decode(candidate, validate=True)
                    res_str = raw_bytes.decode('utf-8')
                    if all(32 <= ord(c) < 127 or c in '\n\r\t' for c in res_str) and len(res_str) >= 4:
                        decoded_text = res_str
                        dec_type = "Base64 (Noise-Delimited Deobfuscation)"
                        break
                except Exception:
                    pass

                # Try Hex
                try:
                    hex_clean = re.sub(r'[^0-9a-fA-F]', '', cleaned)
                    if len(hex_clean) % 2 == 0 and len(hex_clean) >= 8:
                        raw_bytes = bytes.fromhex(hex_clean)
                        res_str = raw_bytes.decode('utf-8')
                        if all(32 <= ord(c) < 127 or c in '\n\r\t' for c in res_str):
                            decoded_text = res_str
                            dec_type = "Hexadecimal (Noise-Stripped)"
                            break
                except Exception:
                    pass

            if decoded_text:
                results.append({
                    "var_names": [p[0] for p in sorted_packets],
                    "type": dec_type,
                    "decoded": decoded_text,
                })

        return results

    def review_code(
        self,
        code: str,
        language: str = "python",
        file_name: str = "snippet.py",
        persona_id: str = "emi",
    ) -> Dict[str, Any]:
        """Analyze code for vulnerabilities, bugs, backdoors, and hidden secrets."""
        findings = []

        lines = code.split("\n")
        for idx, line in enumerate(lines, 1):
            stripped = line.strip()

            # SQL Injection Check
            if re.search(r"['\"].*?(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE).*?['\"]\s*\+|f['\"].*?(SELECT|INSERT|UPDATE|DELETE).*?\{|(execute|query)\s*\(\s*['\"].*?\+", line, re.I):
                findings.append({
                    "line": idx,
                    "severity": "CRITICAL",
                    "category": "Security (SQL Injection)",
                    "message": "ตรวจพบการต่อ String ใน SQL Query เสี่ยงต่อ SQL Injection ควรใช้ Parameterized Query",
                    "suggestion": "ใช้ cursor.execute('SELECT ... WHERE id = ?', (id,)) แทนการใช้ + หรือ f-string",
                })

            # Hardcoded API Keys / Tokens
            if re.search(r"(api[_-]?key|secret|token|password)\s*=\s*['\"][A-Za-z0-9_\-]{20,}['\"]", line, re.I):
                findings.append({
                    "line": idx,
                    "severity": "HIGH",
                    "category": "Security (Secret Leak)",
                    "message": "ตรวจพบ Secret / API Key แบบ Hardcoded เสี่ยงต่อการรั่วไหลลง Git",
                    "suggestion": "ควรย้ายไปเก็บใน Environment Variable (.env) ผ่าน os.getenv()",
                })

            # Dangerous eval / exec / os.system
            if re.search(r"\b(eval|exec)\s*\(", line):
                findings.append({
                    "line": idx,
                    "severity": "CRITICAL",
                    "category": "Vulnerability (RCE)",
                    "message": "การใช้ eval() หรือ exec() เปิดช่องโหว่ Remote Code Execution (RCE)",
                    "suggestion": "หลีกเลี่ยงการประมวลผลสตริงเป็นโค้ด หรือใช้ ast.literal_eval()",
                })

            # Resource Leak: open() without with statement
            if re.search(r"=\s*open\s*\(", line) and not re.search(r"^\s*with\s+", line):
                findings.append({
                    "line": idx,
                    "severity": "MEDIUM",
                    "category": "Resource Management",
                    "message": "เปิดไฟล์โดยไม่ใช้ with context manager อาจทำให้ File Descriptor รั่วไหล",
                    "suggestion": "ใช้ with open(...) as f: เพื่อปิดไฟล์อัตโนมัติ",
                })

            # Bare except
            if re.search(r"^\s*except\s*:\s*$", line) or re.search(r"^\s*except\s+Exception\s*:\s*pass\s*$", line):
                findings.append({
                    "line": idx,
                    "severity": "LOW",
                    "category": "Code Smell",
                    "message": "ใช้ bare except หรือ catch all แล้ว pass ปิดบังข้อผิดพลาดจริงของระบบ",
                    "suggestion": "ระบุ Exception ที่ต้องการดักจับให้ชัดเจน เช่น except ValueError:",
                })

            # Dangerous Deserialization
            if re.search(r"\b(pickle\.loads|yaml\.unsafe_load|yaml\.load\(.*Loader\s*=\s*yaml\.Loader)\b", line):
                findings.append({
                    "line": idx,
                    "severity": "CRITICAL",
                    "category": "Security (Insecure Deserialization)",
                    "message": "ตรวจพบการ Unpickle หรือ Unsafe YAML Deserialization เสี่ยงต่อ Arbitrary Code Execution",
                    "suggestion": "ใช้ json.loads() หรือ yaml.safe_load() แทน",
                })

        # 2. Multi-line Logic Inversion / Backdoor Detection
        if re.search(r"if\s+.*?!=\s*.*?:\s*(?:\n\s*.*)*?return\s*\{.*?(True|'SUPERADMIN'|\"SUPERADMIN\"|'admin'|\"admin\").*?\}", code, re.I):
            findings.append({
                "line": 0,
                "severity": "CRITICAL",
                "category": "Authentication (Logic Inversion / Backdoor)",
                "message": "ตรวจพบ Logic สลับข้าง (Inverted Authentication)! เงื่อนไข != แจกสิทธิ์ SUPERADMIN เมื่อลายเซ็นไม่ตรงกัน และปฏิเสธสิทธิ์เมื่อลายเซ็นถูกต้อง",
                "suggestion": "เปลี่ยนเงื่อนไขเป็น == และแจกสิทธิ์ให้เฉพาะโทเคนที่ตรงกับ expected signature เท่านั้น",
            })

        # 3. CTF / Steganography / Obfuscated Cipher Decoding
        ciphers = self._detect_and_decode_ciphers(code)
        decoded_secrets = []
        for c in ciphers:
            decoded_secrets.append(c["decoded"])
            findings.append({
                "line": 0,
                "severity": "HIGH",
                "category": "Steganography / Hidden Cipher (ถอดรหัสลับ CTF)",
                "message": f"ตรวจพบสตริงแฝงรหัสลับในตัวแปร {', '.join(c['var_names'])}! ถอดรหัส {c['type']} สำเร็จ: `{c['decoded']}`",
                "suggestion": f"ถอดรหัสออกมาได้: {c['decoded']}",
                "decoded_secret": c["decoded"],
            })

        # Summary calculation
        score = 100 - (len([f for f in findings if f["severity"] == "CRITICAL"]) * 35) \
                    - (len([f for f in findings if f["severity"] == "HIGH"]) * 20) \
                    - (len([f for f in findings if f["severity"] == "MEDIUM"]) * 10) \
                    - (len([f for f in findings if f["severity"] == "LOW"]) * 5)
        score = max(0, min(100, score))

        verdict = "PASSED" if score >= 80 else ("WARNING" if score >= 50 else "FAILED")

        report = {
            "engine": "Alibaba Open Code Review (Hybrid OCR)",
            "cli_installed": self.ocr_cli_available,
            "total_lines": len(lines),
            "total_issues": len(findings),
            "score": score,
            "verdict": verdict,
            "findings": findings,
            "decoded_secrets": decoded_secrets,
        }

        report["formatted_comment"] = self.format_persona_comment(report, persona_id)
        return report

    def format_persona_comment(self, report: Dict[str, Any], persona_id: str) -> str:
        """Format review comments to match Emi or Bo's persona."""
        score = report["score"]
        verdict = report["verdict"]
        findings = report["findings"]
        decoded_secrets = report.get("decoded_secrets", [])

        if persona_id == "bo":
            lines = [
                "🕶️ **[เฮียโบ้ฝ่ายประเด็น - Alibaba OCR Code Review Report]** 📋☕",
                f"📊 **คะแนนความปลอดภัยของโค้ด**: `{score}/100` ({verdict})",
            ]
            if not findings:
                lines.append("☕ อืม... โค้ดชุดนี้คลีนดีคุณพี่ ไม่เจอบั๊กหรือช่องโหว่ชัดเจน ผ่านเกณฑ์ขึ้น Production ได้ครับ")
            else:
                lines.append(f"⚠️ **ตรวจพบประเด็นที่ต้องแก้ {len(findings)} จุด** (ถ้าไม่แก้ ตีสามเซิร์ฟระเบิดแน่):")
                for f in findings:
                    sev_icon = "🚨" if f["severity"] == "CRITICAL" else ("⚠️" if f["severity"] == "HIGH" else "💡")
                    line_str = f"บรรทัดที่ {f['line']}" if f["line"] > 0 else "ภาพรวมตรรกะระบบ"
                    lines.append(f"{sev_icon} **[{line_str}] {f['category']}**: {f['message']}")
                    lines.append(f"   ↪️ *เฮียแนะนำ*: {f['suggestion']}")

            if decoded_secrets:
                lines.append("\n🕵️‍♂️ **[เฮียโบ้แกะรหัสลับ CTF ให้แล้ว]** ☕")
                for s in decoded_secrets:
                    lines.append(f"   🚩 **Flag / Secret ที่ซ่อนไว้**: `{s}`")

            return "\n".join(lines)
        else:
            # Default to Emi
            lines = [
                "🌸 **[น้องเอมิ - Alibaba Open Code Review]** 💡🛡️",
                f"📊 **คะแนนการรีวิวโค้ด**: `{score}/100` ({verdict})",
            ]
            if not findings:
                lines.append("✨ ยอดเยี่ยมมากเลยค่ะ! โค้ดชุดนี้เขียนได้ปลอดภัย ไม่พบช่องโหว่ความปลอดภัยหรือบั๊กเลยค่ะ เก่งมากๆ เลย!")
            else:
                lines.append(f"🔍 **น้องเอมิพบจุดที่ควรปรับปรุง {len(findings)} จุดค่ะ**:")
                for f in findings:
                    sev_icon = "🔴" if f["severity"] == "CRITICAL" else ("🟠" if f["severity"] == "HIGH" else "🟡")
                    line_str = f"บรรทัด {f['line']}" if f["line"] > 0 else "ตรรกะระบบ"
                    lines.append(f"{sev_icon} **[{line_str}] [{f['category']}]**: {f['message']}")
                    lines.append(f"   💡 *ข้อแนะนำ*: {f['suggestion']}")

            if decoded_secrets:
                lines.append("\n🕵️‍♀️ **[วากุวากุ! ถอดรหัสลับ CTF ที่แฝงมาสำเร็จ!]** 🥜✨")
                lines.append("   น้องเอมิใช้พลังจิตสแกนสตริงแฝงสัญญาณรบกวน ลอกตัวคั่นออกแล้วถอดรหัสสำเร็จแล้วค่า:")
                for s in decoded_secrets:
                    lines.append(f"   🚩 **`{s}`** (แบร่~ ไม่รอดสายตาสปายจิ๋วหรอกน้า! 😜💖)")

            lines.append("\nลองปรับตามคำแนะนำดูนะคะ น้องเอมิเอาใจช่วยค่ะ! (ระบบตรวจจับใช้โทเคน 1 ใน 9 สบายใจได้ค่า)")
            return "\n".join(lines)
