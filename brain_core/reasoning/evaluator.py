"""Turn evaluator and multi-agent dialogue arbiter."""
from __future__ import annotations

from typing import Set


class TurnEvaluator:
    """Arbitrates which bot should respond when multiple bots share a channel or server."""

    @staticmethod
    def should_bot_reply(
        bot_id: str | int,
        is_my_station: bool,
        is_other_station: bool,
        is_cross_bot: bool,
        is_explicit_call: bool,
        explicit_targets: Set[str | int],
        name_targets: Set[str | int],
        is_primary_bot: bool = False,
        has_active_thread: bool = False,
    ) -> bool:
        """Deterministic arbitration of bot replies."""
        b_id = str(bot_id)
        targets_str = {str(t) for t in (explicit_targets | name_targets)}

        # 1. Direct call (by mention or by name)
        if targets_str:
            return b_id in targets_str

        # 2. Cross-bot loop prevention
        if is_cross_bot:
            return False

        # 3. Active ongoing thread with user
        if has_active_thread:
            return True

        # 4. Exclusive Home Station (Only this bot belongs here)
        if is_my_station and not is_other_station:
            return True

        # 5. Other bot's exclusive station
        if not is_my_station and is_other_station:
            return False

        # 6. Shared Station (Both bots belong here)
        if is_my_station and is_other_station:
            # Default to primary bot unless targeted
            return is_primary_bot

        # Default fallback
        return is_primary_bot
