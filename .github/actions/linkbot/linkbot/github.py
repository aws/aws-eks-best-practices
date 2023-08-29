import datetime
import re

from github import Auth, Github

from .checks import RepoStats


class Client:

    def __init__(self, token):
        self._pygh = Github(auth=Auth.Token(token))

    @staticmethod
    def repo_full_name_from_url(url):
        return re.search(r"github.com/([^/]+/[^/]+)", url).group(1)

    @staticmethod
    def latest_commit_date_on_default_branch(repo):
        return repo.get_commits()[0].commit.author.date
    
    def get_repo_stats(self, url):
        full_name = self.repo_full_name_from_url(url)
        repo = self._pygh.get_repo(full_name)
        return RepoStats(
            # Keeping the original name/URL here rather than the one from the API
            # to ensure it can be easily traced back to the offending link
            full_name=full_name,
            url=url,
            archived=repo.archived,
            # Adding tzinfo should be unncessary after this is released:
            # https://github.com/PyGithub/PyGithub/pull/2565
            pushed_at=repo.pushed_at.replace(tzinfo=datetime.timezone.utc),
            # This more specific check for commits on default branch is necessary
            # because "pushed_at" can often be misleadingly recent. E.g. it seems to even
            # be updated for PRs opened by dependabot.
            latest_default_commit=self.latest_commit_date_on_default_branch(repo).replace(tzinfo=datetime.timezone.utc),
        )


    def get_open_issue_messages(self, repo_url, user):
        full_name = self.repo_full_name_from_url(repo_url)
        repo = self._pygh.get_repo(full_name)
        return [issue.body for issue in repo.get_issues(state='open', creator=user)]


    def create_issue(self, repo_url, title, body):
        full_name = self.repo_full_name_from_url(repo_url)
        repo = self._pygh.get_repo(full_name)
        return repo.create_issue(title, body)