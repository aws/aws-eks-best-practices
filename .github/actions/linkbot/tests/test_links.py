from importlib import resources

from linkbot.links import find_links_in_markdown, is_github_url, github_links_in_files


def test_find_links_in_markdown():
    assert (find_links_in_markdown('[link](https://example.com)') == ['https://example.com'])
    assert (find_links_in_markdown('[link](https://example.com "title")') == ['https://example.com'])


def test_is_github_url():
    assert (is_github_url('https://github.com/bellkev/ToneBoard') == True)
    assert (is_github_url('https://example.com') == False)


def test_github_links_in_files():
    expected = {'https://github.com/kubernetes/kubernetes', 'https://github.com/bellkev/dacom'}
    path = resources.files(__package__) / 'data/markdown'
    assert github_links_in_files(path, '**/*.md') == expected

