from importlib import resources

from linkbot.links import find_links_in_string, is_github_url, github_links_in_files


def test_find_links_in_string():
    assert (find_links_in_string('[link](https://example.com)') == ['https://example.com'])
    assert (find_links_in_string('[link](https://example.com "title")') == ['https://example.com'])


def test_is_github_url():
    assert (is_github_url('https://github.com/bellkev/ToneBoard') == True)
    assert (is_github_url('https://example.com') == False)


def test_github_links_in_files():
    expected = {'https://github.com/kubernetes/kubernetes', 'https://github.com/bellkev/dacom'}
    path = resources.files(__package__) / 'data/markdown'
    assert github_links_in_files(path, '**/*.md') == expected


def test_md_adoc_compatibility():
    path = resources.files(__package__) / 'data/adoc-compat'
    md = github_links_in_files(path, 'runtime.md')
    adoc = github_links_in_files(path, 'runtime.adoc')
    assert md == adoc