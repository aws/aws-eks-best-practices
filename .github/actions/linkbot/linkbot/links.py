import re


def find_links_in_markdown(markdown):
    '''Takes a markdown string and returns a list of links'''
    return re.findall(r"\[.+?\]\((https?://.+?)(?:\s+\".*?\")?\)", markdown)


def is_github_url(link):
    return bool(re.match(r"https?://github\.com.*", link))


def github_links_in_files(path, glob):
    '''Expects a pathlib Path and glob, returns a set of GH urls'''
    return set(l for p in path.glob(glob) for l in find_links_in_markdown(p.read_text()) if is_github_url(l))


def github_links_in_strs(strs):
    '''Takes an iterable of strings and returns a set of GH urls'''
    return set(l for s in strs for l in find_links_in_markdown(s) if is_github_url(l))