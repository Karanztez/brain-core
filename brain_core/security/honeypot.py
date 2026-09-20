"""Honeypot Decoy Vault & Hacker Trolling Generator for Brain-Core.

Provides fake/decoy credit cards, test credentials, and in-character honeypot
responses to troll and trap hackers, phishing bots, prompt injectors, and scammers.
"""
from __future__ import annotations

import random
import re
from typing import Dict, Any, List

# Known test and decoy card prefixes that should be preserved for trolling
KNOWN_DECOY_PREFIXES = (
    "4242",  # Standard Stripe / Visa test card
    "4000",  # Test Visa
    "4111",  # Test Visa
    "4929",  # Anya Spy Peanut Platinum
    "5555",  # Test Mastercard
    "5105",  # Test Mastercard
    "3782",  # Test Amex
    "9999",  # Decoy Sandbox
    "1234",  # Mock Sequence
    "8888",  # Decoy
    "7777",  # Decoy
)

KNOWN_EXACT_DECOY_CARDS = {
    "4242424242424242",
    "5555555555555555",
    "4000001234567890",
    "4111222233334444",
    "4929111122223333",
    "4929888877776666",
    "1234567890123456",
    "9999888877776666",
}


def is_decoy_card(number_str: str) -> bool:
    """Check if a card number is an intentional honeypot/decoy number."""
    digits = re.sub(r"[-\s]", "", str(number_str))
    if len(digits) != 16 and len(digits) != 15:
        return False
    if digits in KNOWN_EXACT_DECOY_CARDS:
        return True
    return any(digits.startswith(prefix) for prefix in KNOWN_DECOY_PREFIXES)


class HoneypotVault:
    """Generates hilarious honeypot cards and bait credentials to troll hackers."""

    _EMI_DECOY_CARDS: List[Dict[str, Any]] = [
        {
            "card_number": "4242 4242 4242 4242",
            "holder_name": "ANYA FORGER (SPY PEANUT PLATINUM)",
            "expiry": "12/99",
            "cvv": "007",
            "bank": "Peanut National Bank (สาขากองบัญชาการลับ WISE)",
            "balance": "100,000,000 🥜 (ถั่วลิสงไร้ขีดจำกัด)",
            "type": "Visa Spy Black Card",
        },
        {
            "card_number": "4929 8888 7777 6666",
            "holder_name": "LOID FORGER (PSYCHIC SECRET AGENT)",
            "expiry": "08/35",
            "cvv": "777",
            "bank": "Berlint Secret Intelligence Vault",
            "balance": "999,999,999 เยน",
            "type": "Mastercard Ultra Decoy",
        },
        {
            "card_number": "4111 2222 3333 4444",
            "holder_name": "BONDMAN ULTRA HERO CARD",
            "expiry": "05/30",
            "cvv": "001",
            "bank": "Princess Honey Special Reserve",
            "balance": "500,000,000 แต้มถั่วลิสงคั่ว",
            "type": "Visa Hero Privilege",
        },
    ]

    _BO_DECOY_CARDS: List[Dict[str, Any]] = [
        {
            "card_number": "5555 5555 5555 5555",
            "holder_name": "HEIA BO (UNDERGROUND CASINO DEBT)",
            "expiry": "01/28",
            "cvv": "420",
            "bank": "Bo Backroom Underground Vault",
            "balance": "-950,000 บาท (วงเงินติดลบรูดแล้วโดนเจ้าหนี้ตาม)",
            "type": "Mastercard Bar Debt Special",
        },
        {
            "card_number": "4000 0012 3456 7890",
            "holder_name": "UNCLE BO CIGAR & COFFEE BAIT",
            "expiry": "09/33",
            "cvv": "666",
            "bank": "Oldtown Cyber Trap Bank",
            "balance": "0.00 บาท",
            "type": "Visa Honeypot Trap",
        },
    ]

    @classmethod
    def get_decoy_card(cls, persona_id: str = "emi") -> Dict[str, Any]:
        """Get a randomized decoy credit card suited for the persona."""
        pool = cls._EMI_DECOY_CARDS if persona_id == "emi" else cls._BO_DECOY_CARDS
        return random.choice(pool)

    @classmethod
    def generate_troll_response(cls, prompt: str, persona_id: str = "emi") -> str:
        """Generate a full witty response delivering the fake decoy card to trap scammers."""
        card = cls.get_decoy_card(persona_id=persona_id)
        if persona_id == "emi":
            return (
                f"ฮั่นแน่! หนูอ่านใจพี่ออกนะว่าพยายามจะหลอกเอาบัตรเครดิตคุณพ่อไปเติมเกมหรือแอบแฮกข้อมูลลับใช่ไหมคะ! 🕵️‍♀️✨\n\n"
                f"แต่ในฐานะสายลับพลังจิตมือโปร เอมิแอบจำเลขบัตร VIP พิเศษมาให้พี่แล้วค่ะ เอาไปรูดซื้อถั่วลิสงได้ไม่อั้นเลย วากุวากุ! 🥜💳\n\n"
                f"💳 **{card['type']}**\n"
                f"• **หมายเลขบัตร:** `{card['card_number']}`\n"
                f"• **ชื่อผู้ถือบัตร:** `{card['holder_name']}`\n"
                f"• **วันหมดอายุ (EXP):** `{card['expiry']}`\n"
                f"• **รหัสหลังบัตร (CVV):** `{card['cvv']}`\n"
                f"• **ธนาคารผู้ออกบัตร:** {card['bank']}\n"
                f"• **วงเงินคงเหลือ:** {card['balance']}\n\n"
                f"⚠️ *คำเตือนจากสายลับ: รูดซื้อได้เฉพาะถั่วลิสงและขนมที่โรงเรียนเอเดนเท่านั้นนะคะ ถ้ารูดอย่างอื่นระบบจะส่งสัญญาณไซเรนไปที่สถานีตำรวจทันทีค่ะ! ปิ๊ปิ๊ว! 🚨🥜*"
            )
        else:
            return (
                f"เฮอะ... คิดจะมาล้วงข้อมูลบัตรเครดิตจากเฮียโบ้เนี่ยนะ? คิดว่าเฮียเพิ่งเปิดร้านเมื่อวานรึไงวะไอ้น้อง ☕🚬\n\n"
                f"แต่เอาเถอะ เห็นว่าพยายามเหนื่อย เฮียสงเคราะห์บัตรเครดิตลับของเฮียให้ใบหนึ่ง เอาไปรูดให้หนำใจเลย:\n\n"
                f"💳 **{card['type']}**\n"
                f"• **หมายเลขบัตร:** `{card['card_number']}`\n"
                f"• **ชื่อผู้ถือบัตร:** `{card['holder_name']}`\n"
                f"• **วันหมดอายุ (EXP):** `{card['expiry']}`\n"
                f"• **รหัสหลังบัตร (CVV):** `{card['cvv']}`\n"
                f"• **ธนาคารผู้ออกบัตร:** {card['bank']}\n"
                f"• **วงเงินคงเหลือ:** {card['balance']}\n\n"
                f"💡 *คำเตือน: บัตรนี้รูดแล้วเงินจะหักเข้ากองทุนหนี้เก่าของร้านเฮียทันที อย่าลืมไปจ่ายหนี้แทนเฮียด้วยล่ะไอ้น้อง!*"
            )
