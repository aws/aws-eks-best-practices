import re

from .github import repo_full_name_from_url


def find_links_in_string(s):
    '''Takes a string and returns a list of links.
    Technically does not allow some things like brackets or parens
    which can be in URLs, but should not be in links to GH projects.'''
    return re.findall(r"https?://[^\s()[\]]+", s)

def is_github_url(link):
    return bool(repo_full_name_from_url(link))


def github_links_in_files(path, glob):
    '''Expects a pathlib Path and glob, returns a set of GH urls'''
    return set(l for p in path.glob(glob) for l in find_links_in_string(p.read_text()) if is_github_url(l))


def github_links_in_strs(strs):
    '''Takes an iterable of strings and returns a set of GH urls'''
    return set(l for s in strs for l in find_links_in_string(s) if is_github_url(l))