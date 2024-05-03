from .checks import CheckFailures


def render_title(stats, failure):
    if failure == CheckFailures.ARCHIVED:
        title = f'Reference to an archived project ({stats.full_name})'
    elif failure in [CheckFailures.TOO_LONG_SINCE_PUSH, CheckFailures.TOO_LONG_SINCE_DEFAULT_COMMIT]:
        title = f'Reference to a potentially unmaintained project ({stats.full_name})'
    else:
        raise ValueError('Unknown failure type')
    return title


def render_body(stats, failure):
    if failure == CheckFailures.ARCHIVED:
        message = f'The project [{stats.full_name}]({stats.url}) has been archived by its maintainers.'
    elif failure == CheckFailures.TOO_LONG_SINCE_PUSH:
        message = (
            f'The project [{stats.full_name}]({stats.url}) has not been pushed to since '
            f'{stats.pushed_at.date().isoformat()}. Please check if the project is still maintained.'
        )
    elif failure == CheckFailures.TOO_LONG_SINCE_DEFAULT_COMMIT:
        message = (
            f'The project [{stats.full_name}]({stats.url}) does not have any commits to its default branch since '
            f'{stats.latest_default_commit.date().isoformat()}. Please check if the project is still maintained.'
        )
    else:
        raise ValueError('Unknown failure type')
    return message


def debug_message(stats, failure):
    if failure == CheckFailures.ARCHIVED:
        return str(failure)
    elif failure == CheckFailures.TOO_LONG_SINCE_PUSH:
        return f'{failure}: {stats.pushed_at.date().isoformat()}'
    elif failure == CheckFailures.TOO_LONG_SINCE_DEFAULT_COMMIT:
        return f'{failure}: {stats.latest_default_commit.date().isoformat()}'
    else:
        raise ValueError('Unknown failure type')