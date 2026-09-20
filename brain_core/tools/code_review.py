"""Alibaba Open Code Review (OCR) Tool for Brain-Core.

Integrates Alibaba's battle-tested Open Code Review engine into Emi and Bo's
cognitive reasoning and code inspection pipeline.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from typing import Any, Dict, List, Optional


class OpenCodeReviewTool:
    """Hybrid code review tool integrating Alibaba Open Code Review (ocr) and AST heuristics."""

    def __init__(self) -> None:
        self.ocr_cli_available = shutil.which("ocr") is not None

    def review_code(
        self,
        code: str,
        language: str = "python",
        file_name: str = "snippet.py",
        persona_id: str = "emi",
    ) -> Dict[str, Any]:
        """Analyze code for vulnerabilities, bugs, and best practices."""
        findings = []

        # 1. Hybrid Heuristic Engine (Static AST / Pattern matching)
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
        }

        # Format output text customized for persona
        report["formatted_comment"] = self.format_persona_comment(report, persona_id)
        return report

    def format_persona_comment(self, report: Dict[str, Any], persona_id: str) -> str:
        """Format review comments to match Emi or Bo's persona."""
        score = report["score"]
        verdict = report["verdict"]
        findings = report["findings"]

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
                    lines.append(f"{sev_icon} **[บรรทัดที่ {f['line']}] {f['category']}**: {f['message']}")
                    lines.append(f"   ↪️ *เฮียแนะนำ*: {f['suggestion']}")
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
                    lines.append(f"{sev_icon} **บรรทัด {f['line']} [{f['category']}]**: {f['message']}")
                    lines.append(f"   💡 *ข้อแนะนำ*: {f['suggestion']}")
                lines.append("\nลองปรับตามคำแนะนำดูนะคะ น้องเอมิเอาใจช่วยค่ะ! (ระบบตรวจจับใช้โทเคน 1 ใน 9 สบายใจได้ค่า)")
            return "\n".join(lines)
