"""Conversation session memory per persona, user, and channel."""
from __future__ import annotations

import time
from typing import Dict, List, Optional
from brain_core.types import ChatMessage


class SessionMemory:
    """Manages short-term dialog history for a specific persona-user-channel interaction."""

    def __init__(self, max_history: int = 20) -> None:
        self.max_history = max_history
        # key = "{persona_id}:{channel_id}:{user_id}" -> list of ChatMessage
        self._sessions: Dict[str, List[ChatMessage]] = {}

    def _key(self, persona_id: str, channel_id: str | int, user_id: str | int) -> str:
        return f"{persona_id}:{channel_id}:{user_id}"

    def append(self, persona_id: str, channel_id: str | int, user_id: str | int, user_message: str, assistant_reply: str) -> None:
        """Record a turn into the user's isolated session with this persona."""
        k = self._key(persona_id, channel_id, user_id)
        history = self._sessions.setdefault(k, [])
        history.append(ChatMessage(role="user", content=user_message))
        history.append(ChatMessage(role="assistant", content=assistant_reply))
        if len(history) > self.max_history * 2:
            self._sessions[k] = history[-(self.max_history * 2):]

    def get_messages(self, persona_id: str, channel_id: str | int, user_id: str | int) -> List[ChatMessage]:
        """Retrieve the recent message history for this session."""
        k = self._key(persona_id, channel_id, user_id)
        return list(self._sessions.get(k, []))

    def clear(self, persona_id: str, channel_id: str | int, user_id: str | int) -> None:
        """Clear memory for a specific interaction session."""
        k = self._key(persona_id, channel_id, user_id)
        self._sessions.pop(k, None)
