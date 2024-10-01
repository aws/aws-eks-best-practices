import pathlib

from github.GithubException import GithubException, RateLimitExceededException

from .checks import check_failure_for_stats
from .config import LinkBotConfig
from .links import github_links_in_files, github_links_in_strs
from . import github
from .report import render_title, render_body, debug_message


conf = LinkBotConfig()
gh = github.Client(conf.gh_token)
repo_root = pathlib.Path(conf.repo_root)
all_links = github_links_in_files(repo_root, conf.glob)
bot_messages = gh.get_all_issue_messages(conf.repo_url, conf.gh_user)
existing_links = github_links_in_strs(bot_messages)
for link in all_links:
    try:
        if link in existing_links:
            print(f'Issue already exists for {link}, skipping.')
            continue
        print(f'Fetching data for {link}')
        stats = gh.get_repo_stats(link)
        failure = check_failure_for_stats(stats, conf.max_days_old)
        if not failure:
            continue
        print(f'Check failed for {link}: {debug_message(stats, failure)}')
        if conf.dry_run:
            print('Dry run, not creating issue.')
            continue
        issue = gh.create_issue(conf.repo_url, render_title(stats, failure), render_body(stats, failure))
        print(f'Created issue {issue.number} for {link}')
    except RateLimitExceededException as e:
        # Do not continue in the face of rate limit exceptions
        raise e
    except GithubException as e:
        # Sometimes repo-specific exceptions occur, such as org-level IP allowlists blocking API calls
        # Proceed to next issues in such cases
        print('WARNING: Encountered unexpected GitHub exception:', e)
        continue