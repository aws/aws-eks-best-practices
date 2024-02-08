from collections import namedtuple
from datetime import datetime, timedelta, timezone
from enum import Enum


RepoStats = namedtuple('RepoStats', ['full_name', 'url', 'archived', 'pushed_at', 'latest_default_commit'])

CheckFailures = Enum('CheckFailures', ['ARCHIVED', 'TOO_LONG_SINCE_PUSH', 'TOO_LONG_SINCE_DEFAULT_COMMIT'])


def check_failure_for_stats(stats, max_days_old):
    if stats.archived:
        return CheckFailures.ARCHIVED
    if stats.pushed_at < (datetime.now(timezone.utc) - timedelta(days=max_days_old)):
        return CheckFailures.TOO_LONG_SINCE_PUSH
    if stats.latest_default_commit < (datetime.now(timezone.utc) - timedelta(days=max_days_old)):
        return CheckFailures.TOO_LONG_SINCE_DEFAULT_COMMIT
