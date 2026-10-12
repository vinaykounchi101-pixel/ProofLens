"""Unit tests for rate-limiting and quota controls (FR-14)."""

import pytest
from app.core.config import settings
from app.core.errors import QuotaExhaustedException
from app.core.usage import UsageTracker


def test_rate_limit_exceeded_raises_quota_exhausted():
    tracker = UsageTracker()
    ws_id = "test_workspace_quota"

    # Fill quota up to limit
    for _ in range(settings.RATE_LIMIT_PER_MINUTE):
        tracker.check_and_record(ws_id)

    # Next call must raise QuotaExhaustedException
    with pytest.raises(QuotaExhaustedException, match="Rate limit exceeded"):
        tracker.check_and_record(ws_id)
