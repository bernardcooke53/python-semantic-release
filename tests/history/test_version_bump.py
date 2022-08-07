import mock

from semantic_release.history import evaluate_version_bump

from . import *


# TODO: fix this so they work
from semantic_release.settings import Config
from semantic_release.history import angular_parser


config = Config()
commit_parser = lambda message: angular_parser(
    message,
    config.parser_angular_allowed_types,
    config.parser_angular_minor_types,
    config.parser_angular_patch_types,
    config.parser_angular_default_level_bump,
)
#

def test_major():
    with mock.patch(
        "semantic_release.history.logs.get_commit_log",
        lambda *a, **kw: ALL_KINDS_OF_COMMIT_MESSAGES,
    ):
        assert evaluate_version_bump(commit_parser, "0.0.0", "v{version}") == "major"


def test_minor():
    with mock.patch(
        "semantic_release.history.logs.get_commit_log",
        lambda *a, **kw: MINOR_AND_PATCH_COMMIT_MESSAGES,
    ):
        assert evaluate_version_bump(commit_parser, "0.0.0", "v{version}") == "minor"


def test_patch():
    with mock.patch(
        "semantic_release.history.logs.get_commit_log",
        lambda *a, **kw: PATCH_COMMIT_MESSAGES,
    ):
        assert evaluate_version_bump(commit_parser, "0.0.0", "v{version}") == "patch"


def test_nothing_if_no_tag():
    with mock.patch(
        "semantic_release.history.logs.get_commit_log",
        lambda *a, **kw: [("", "...")],
    ):
        assert evaluate_version_bump(commit_parser, "0.0.0", "v{version}") is None


def test_force():
    assert evaluate_version_bump(commit_parser, "0.0.0", "v{version}", force="major") == "major"
    assert evaluate_version_bump(commit_parser, "0.0.0", "v{version}", force="minor") == "minor"
    assert evaluate_version_bump(commit_parser, "0.0.0", "v{version}", force="patch") == "patch"


def test_should_not_skip_commits_mentioning_other_commits():
    with mock.patch(
        "semantic_release.history.logs.get_commit_log",
        lambda *a, **kw: MAJOR_MENTIONING_LAST_VERSION,
    ):
        assert evaluate_version_bump(commit_parser, "1.0.0", "v{version}") == "major"


@mock.patch("semantic_release.history.logs.get_commit_log", lambda *a, **kw: [MINOR])
def test_should_minor_with_patch_without_tag():
    assert evaluate_version_bump(commit_parser, "1.1.0", "v{version}", patch_without_tag=True) == "minor"


@mock.patch("semantic_release.history.logs.get_commit_log", lambda *a, **kw: [NO_TAG])
def test_should_patch_without_tagged_commits():
    assert evaluate_version_bump(commit_parser, "1.1.0", "v{version}", patch_without_tag=True) == "patch"


@mock.patch("semantic_release.history.logs.get_commit_log", lambda *a, **kw: [NO_TAG])
def test_should_return_none_without_tagged_commits():
    assert evaluate_version_bump(commit_parser, "1.1.0", "v{version}", patch_without_tag=False) is None


@mock.patch("semantic_release.history.logs.get_commit_log", lambda *a, **kw: [])
def test_should_return_none_without_commits():
    """
    Make sure that we do not release if there are no commits since last release.
    """
    assert evaluate_version_bump(commit_parser, "1.1.0", "v{version}", patch_without_tag=True, major_on_zero=True) is None

    assert evaluate_version_bump(commit_parser, "1.1.0", "v{version}", patch_without_tag=False, major_on_zero=False) is None


@mock.patch("semantic_release.history.logs.get_commit_log", lambda *a, **kw: [MAJOR])
def test_should_minor_without_major_on_zero():
    assert evaluate_version_bump(commit_parser, "0.1.0", "v{version}", major_on_zero=False) == "minor"
