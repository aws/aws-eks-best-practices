from datetime import datetime, timedelta, timezone
from importlib import resources

from linkbot.checks import RepoStats, CheckFailures, check_failure_for_stats


def test_archived():
    stats = RepoStats('foo/bar', 'https://github.com/foo/bar', 
                      True, datetime.now(timezone.utc), datetime.now(timezone.utc))
    assert (check_failure_for_stats(stats, 500) == CheckFailures.ARCHIVED)


def test_too_long_since_push():
    stats = RepoStats('foo/bar', 'https://github.com/foo/bar',
                      False, datetime.now(timezone.utc) - timedelta(days=1000), datetime.now(timezone.utc))
    assert (check_failure_for_stats(stats, 500) == CheckFailures.TOO_LONG_SINCE_PUSH)


def test_too_long_since_default_commit():
    stats = RepoStats('foo/bar', 'https://github.com/foo/bar', 
                      False, datetime.now(timezone.utc), datetime.now(timezone.utc) - timedelta(days=1000))
    assert (check_failure_for_stats(stats, 500) == CheckFailures.TOO_LONG_SINCE_DEFAULT_COMMIT)