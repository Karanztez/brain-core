"""Shared channel context buffer for real-time cross-agent awareness."""
from __future__ import annotations

import time
from typing import Dict, List, Optional
from brain_core.types import ChannelActivityTurn


class ChannelContextBuffer:
    """Manages recent turns in a channel so multiple personas can coordinate seamlessly."""

    def __init__(self, max_turns: int = 15, max_age_seconds: int = 1800, max_turn_chars: int = 1800) -> None:
        self.max_turns = max_turns
        self.max_age_seconds = max_age_seconds
        self.max_turn_chars = max_turn_chars
        # channel_key -> list of ChannelActivityTurn
        self._channels: Dict[str, List[ChannelActivityTurn]] = {}

    def append(self, channel_id: str | int, author: str, bot_scope: str, prompt: str, reply: str) -> None:
        """Record an activity turn in the shared channel space."""
        ch_key = str(channel_id)
        turn = ChannelActivityTurn(
            author=author,
            bot_scope=bot_scope,
            prompt=prompt,
            reply=reply,
            timestamp=time.time(),
        )
        turns = self._channels.setdefault(ch_key, [])
        turns.append(turn)
        # Prune to max turns
        if len(turns) > self.max_turns:
            self._channels[ch_key] = turns[-self.max_turns:]

    def get_recent(self, channel_id: str | int, exclude_bot_scope: Optional[str] = None) -> List[ChannelActivityTurn]:
        """Fetch active turns within the expiration window."""
        ch_key = str(channel_id)
        now = time.time()
        turns = self._channels.get(ch_key, [])
        valid = [t for t in turns if (now - t.timestamp) <= self.max_age_seconds]
        if exclude_bot_scope:
            valid = [t for t in valid if t.bot_scope != exclude_bot_scope]
        return valid

    def format_context_prompt(self, channel_id: str | int, current_persona_id: str = "") -> str:
        """Build a formatted context string of recent activities for prompt injection."""
        recent = self.get_recent(channel_id)
        if not recent:
            return ""

        lines = ["[บริบทบทสนทนาและกิจกรรมล่าสุดในห้อง (Channel Activity)]"]
        for turn in recent[-4:]:
            author_desc = f"บอท ({turn.bot_scope})" if turn.bot_scope else turn.author
            p_snippet = turn.prompt[:self.max_turn_chars]
            r_snippet = turn.reply[:self.max_turn_chars]
            lines.append(f"📌 ผู้ใช้ถาม:\n{p_snippet}")
            lines.append(f"📌 คำตอบของ {author_desc}:\n{r_snippet}\n")

        lines.append("⚠️ กฎสำคัญ: หากผู้ใช้ถามต่อเนื่องหรือถามถึงสิ่งที่อีกคนเพิ่งตอบ ให้อ้างอิงข้อมูลข้างต้นทันทีตามคาแรคเตอร์ของคุณ ห้ามทวงถามซ้ำ!")
        return "\n".join(lines)
