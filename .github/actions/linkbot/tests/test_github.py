from datetime import datetime
import os

import pytest

from linkbot.checks import RepoStats
from linkbot.github import Client, repo_full_name_from_url


def test_repo_name_from_url():
    assert (repo_full_name_from_url('https://github.com/bellkev/ToneBoard') == 'bellkev/ToneBoard')
    assert (repo_full_name_from_url('https://github.com/FairwindsOps/') == None)


@pytest.mark.network
def test_get_repo_stats():
    gh = Client(os.environ.get('LINKBOT_GH_TOKEN'))
    expected_pushed = datetime.fromisoformat('2017-04-17T06:45:27Z')
    expected_latest_default_commit = datetime.fromisoformat('2014-05-26T17:11:56Z')
    expected = RepoStats(full_name='bellkev/dacom', url='https://github.com/bellkev/dacom', archived=True,
                         pushed_at=expected_pushed, latest_default_commit=expected_latest_default_commit)     
    assert gh.get_repo_stats('https://github.com/bellkev/dacom') == expected


@pytest.mark.network
def test_get_open_issue_messages():
    gh = Client(os.environ.get('LINKBOT_GH_TOKEN'))
    expected = 'java.lang.IllegalArgumentException'
    messages = gh.get_open_issue_messages('https://github.com/bellkev/dacom', 'r00k')
    assert len(messages) == 1
    assert expected in messages[0]