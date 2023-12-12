import os


class LinkBotConfig:

    def __init__(self):
        try:
            # Repository to scan and in which issues will be opened
            self.repo_url = os.environ['LINKBOT_REPO_URL']
            # Location of repo on local filesystem
            self.repo_root = os.environ['LINKBOT_REPO_ROOT']
            # Glob pattern for markdown files to check
            self.glob = os.environ['LINKBOT_GLOB']
            # Max amount of time within which a project needs to have been updated
            self.max_days_old = int(os.environ['LINKBOT_MAX_DAYS_OLD'])
            # Whether to run in dry-run mode, without actually creating any GH issues
            self.dry_run = os.environ.get('LINKBOT_DRY_RUN', 'false').lower() == 'true'
            # GH login info used for creating issues
            self.gh_user = os.environ['LINKBOT_GH_USER']
            # Allow unauthenticated use, handy for e.g. testing rate limits
            self.gh_token = os.environ.get('LINKBOT_GH_TOKEN')
        except KeyError as e:
            print('Error: %s is a required config value' % e)
            exit(1)