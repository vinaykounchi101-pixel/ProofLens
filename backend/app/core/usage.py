"""Usage tracking and in-memory rate limiting to enforce free-tier limits (FR-14)."""

import time
from typing import Dict, List
from app.core.config import settings
from app.core.errors import QuotaExhaustedException


class UsageTracker:
    def __init__(self):
        # Maps workspace_id -> list of unix timestamps
        self._request_timestamps: Dict[str, List[float]] = {}
        # Maps workspace_id -> daily count
        self._daily_counts: Dict[str, int] = {}
        self._last_day_reset = time.strftime("%Y-%m-%d")

    def _reset_if_new_day(self):
        current_day = time.strftime("%Y-%m-%d")
        if current_day != self._last_day_reset:
            self._daily_counts.clear()
            self._last_day_reset = current_day

    def check_and_record(self, workspace_id: str) -> None:
        """Enforces RPM and daily query limits without silent paid fallbacks."""
        self._reset_if_new_day()
        now = time.time()

        # Check daily limit
        daily_count = self._daily_counts.get(workspace_id, 0)
        if daily_count >= settings.MAX_DAILY_QUERIES:
            raise QuotaExhaustedException(
                message=f"Daily AI query limit of {settings.MAX_DAILY_QUERIES} reached for this workspace.",
                details={"workspace_id": workspace_id, "limit": settings.MAX_DAILY_QUERIES},
            )

        # Check per-minute rate limit
        window_start = now - 60.0
        timestamps = self._request_timestamps.get(workspace_id, [])
        # Prune old timestamps
        timestamps = [ts for ts in timestamps if ts > window_start]
        self._request_timestamps[workspace_id] = timestamps

        if len(timestamps) >= settings.RATE_LIMIT_PER_MINUTE:
            raise QuotaExhaustedException(
                message=f"Rate limit exceeded: maximum {settings.RATE_LIMIT_PER_MINUTE} requests per minute allowed.",
                details={"workspace_id": workspace_id, "limit": settings.RATE_LIMIT_PER_MINUTE},
            )

        # Record this request
        timestamps.append(now)
        self._daily_counts[workspace_id] = daily_count + 1


usage_tracker = UsageTracker()
