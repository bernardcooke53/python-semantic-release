import pytest

from semantic_release.dist import build_dists, should_build, should_remove_dist
from semantic_release.settings import Config


@pytest.mark.parametrize(
    "command",
    ["sdist bdist_wheel", "sdist", "bdist_wheel", "sdist bdist_wheel custom_cmd"],
)
def test_build_command(mocker, command):
    config = Config(build_command=command)
    mock_run = mocker.patch("semantic_release.dist.run")
    build_dists(config.build_command)
    mock_run.assert_called_once_with(command)


@pytest.mark.parametrize(
    "config,expected",
    [
        (
            Config(
                upload_to_pypi=True,
                upload_to_repository=True,
                upload_to_release=True,
                build_command="python setup.py build",
            ),
            True,
        ),
        (
            Config(
                upload_to_pypi=True,
                upload_to_repository=True,
                upload_to_release=True,
                build_command=False,
            ),
            False,
        ),
        (
            Config(
                upload_to_pypi=True,
                upload_to_repository=True,
                upload_to_release=True,
                build_command=None,
            ),
            False,
        ),
        (
            Config(
                upload_to_pypi=True,
                upload_to_repository=True,
                upload_to_release=True,
                build_command="",
            ),
            False,
        ),
        (
            Config(
                upload_to_pypi=True,
                upload_to_repository=True,
                upload_to_release=True,
                build_command="false",
            ),
            False,
        ),
        (
            Config(
                upload_to_pypi=True,
                upload_to_repository=False,
                upload_to_release=True,
                build_command="python setup.py build",
            ),
            True,
        ),
        (
            Config(
                upload_to_pypi=False,
                upload_to_repository=True,
                upload_to_release=True,
                build_command="python setup.py build",
            ),
            True,
        ),
        (
            Config(
                upload_to_pypi=False,
                upload_to_repository=False,
                upload_to_release=True,
                build_command="python setup.py build",
            ),
            True,
        ),
        (
            Config(
                upload_to_pypi=False,
                upload_to_repository=True,
                upload_to_release=False,
                build_command="python setup.py build",
            ),
            False,
        ),
        (
            Config(
                upload_to_pypi=False,
                upload_to_repository=False,
                upload_to_release=False,
                build_command="python setup.py build",
            ),
            False,
        ),
    ],
)
def test_should_build(config, expected):
    assert (
        should_build(
            config.upload_to_repository,
            config.upload_to_pypi,
            config.upload_to_release,
            config.build_command,
        )
        == expected
    )


@pytest.mark.parametrize(
    "config,expected",
    [
        (
            Config(
                upload_to_pypi=True,
                upload_to_repository=True,
                upload_to_release=True,
                build_command="python setup.py build",
                remove_dist=True,
            ),
            True,
        ),
        (
            Config(
                upload_to_pypi=False,
                upload_to_repository=True,
                upload_to_release=True,
                build_command="python setup.py build",
                remove_dist=True,
            ),
            True,
        ),
        (
            Config(
                upload_to_pypi=True,
                upload_to_repository=False,
                upload_to_release=True,
                build_command="python setup.py build",
                remove_dist=True,
            ),
            True,
        ),
        (
            Config(
                upload_to_pypi=True,
                upload_to_repository=False,
                upload_to_release=False,
                build_command="python setup.py build",
                remove_dist=True,
            ),
            False,
        ),
        (
            Config(
                upload_to_pypi=True,
                upload_to_repository=True,
                upload_to_release=True,
                build_command="python setup.py build",
                remove_dist=False,
            ),
            False,
        ),
        (
            Config(
                upload_to_pypi=False,
                upload_to_repository=False,
                upload_to_release=False,
                build_command=False,
                remove_dist=True,
            ),
            False,
        ),
        (
            Config(
                upload_to_pypi=False,
                upload_to_repository=False,
                upload_to_release=False,
                build_command="false",
                remove_dist=True,
            ),
            False,
        ),
    ],
)
def test_should_remove_dist(config, expected):
    assert (
        should_remove_dist(
            config.remove_dist,
            config.upload_to_repository,
            config.upload_to_pypi,
            config.upload_to_release,
            config.build_command,
        )
        == expected
    )
