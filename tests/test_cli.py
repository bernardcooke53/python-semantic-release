import pytest
from click.testing import CliRunner

import semantic_release
from semantic_release.cli import changelog, main, print_version, publish, version
from semantic_release.errors import GitError, ImproperConfigurationError
from semantic_release.repository import ArtifactRepo
from semantic_release.settings import Config, get_commit_parser

from . import mock
from .mocks import mock_version_file


@pytest.fixture
def runner():
    return CliRunner()


def test_main_should_call_correct_function(mocker, runner):
    config = Config.from_files()
    mock_version = mocker.patch("semantic_release.cli.version")
    result = runner.invoke(main, ["version"])
    mock_version.assert_called_once_with(
        config,
        noop=False,
        post=False,
        force_level=None,
        prerelease=False,
        prerelease_patch=True,
        retry=False,
        define=(),
    )
    assert result.exit_code == 0


@pytest.mark.xfail(reason="Lambdas for commit parsers are different (by id()) - will need rework")
def test_version_by_commit_should_call_correct_functions(mocker):
    config = Config.from_files(commit_version_number=True)
    mock_tag_new_version = mocker.patch("semantic_release.cli.tag_new_version")
    mock_commit_new_version = mocker.patch("semantic_release.cli.commit_new_version")
    mock_set_new_version = mocker.patch("semantic_release.cli.set_new_version")
    mock_new_version = mocker.patch(
        "semantic_release.cli.get_new_version", return_value="2.0.0"
    )
    mock_evaluate_bump = mocker.patch(
        "semantic_release.cli.evaluate_version_bump", return_value="major"
    )
    mock_current_version = mocker.patch(
        "semantic_release.cli.get_current_version", return_value="1.2.3"
    )
    mock_current_release_version = mocker.patch(
        "semantic_release.cli.get_current_release_version", return_value="1.2.3"
    )

    version(config)
    # TODO: a hack to remove
    commit_parser = get_commit_parser(config)

    mock_current_version.assert_called_once()
    mock_current_release_version.assert_called_once()
    mock_evaluate_bump.assert_called_once_with(
        commit_parser,
        "1.2.3",
        config.tag_format,
        config.patch_without_tag,
        config.major_on_zero,
        None,
    )
    mock_new_version.assert_called_once_with("1.2.3", "1.2.3", "major", False, True)
    mock_set_new_version.assert_called_once_with(
        "2.0.0",
        config.version_variable,
        config.version_pattern,
        config.version_toml,
        config.prerelease_tag,
    )
    mock_commit_new_version.assert_called_once_with(
        "2.0.0",
        config.version_variable,
        config.version_pattern,
        config.version_toml,
        config.prerelease_tag,
        config.commit_subject,
        config.commit_message,
        config.commit_author,
    )
    mock_tag_new_version.assert_called_once_with(config.tag_format, "2.0.0")


@pytest.mark.xfail(reason="Lambdas for commit parsers are different (by id()) - will need rework")
def test_version_by_tag_with_commit_version_number_should_call_correct_functions(
    mocker,
):

    config = Config.from_files(version_source="tag", commit_version_number=True)
    mock_set_new_version = mocker.patch("semantic_release.cli.set_new_version")
    mock_tag_new_version = mocker.patch("semantic_release.cli.tag_new_version")
    mock_commit_new_version = mocker.patch("semantic_release.cli.commit_new_version")
    mock_new_version = mocker.patch(
        "semantic_release.cli.get_new_version", return_value="2.0.0"
    )
    mock_evaluate_bump = mocker.patch(
        "semantic_release.cli.evaluate_version_bump", return_value="major"
    )
    mock_current_version = mocker.patch(
        "semantic_release.cli.get_current_version", return_value="1.2.3"
    )
    mock_current_release_version = mocker.patch(
        "semantic_release.cli.get_current_release_version", return_value="1.2.3"
    )

    version(config)

    # TODO: get rid of this
    commit_parser = get_commit_parser(config)

    mock_current_version.assert_called_once()
    mock_current_release_version.assert_called_once()
    mock_evaluate_bump.assert_called_once_with(
        commit_parser,
        "1.2.3",
        config.tag_format,
        config.patch_without_tag,
        config.major_on_zero,
        None,
    )
    mock_new_version.assert_called_once_with("1.2.3", "1.2.3", "major", False, True)
    mock_set_new_version.assert_called_once_with(
        "2.0.0",
        config.version_variable,
        config.version_pattern,
        config.version_toml,
        config.prerelease_tag,
    )
    mock_commit_new_version.assert_called_once_with(
        "2.0.0",
        config.version_variable,
        config.version_pattern,
        config.version_toml,
        config.prerelease_tag,
        config.commit_subject,
        config.commit_message,
        config.commit_author,
    )
    mock_tag_new_version.assert_called_once_with(config.tag_format, "2.0.0")


@pytest.mark.xfail(reason="Lambdas for commit parsers are different (by id()) - will need rework")
def test_version_by_tag_only_with_commit_version_number_should_call_correct_functions(
    mocker,
):

    config = Config.from_files(version_source="tag_only", commit_version_number=True)
    mock_set_new_version = mocker.patch("semantic_release.cli.set_new_version")
    mock_tag_new_version = mocker.patch("semantic_release.cli.tag_new_version")
    mock_commit_new_version = mocker.patch("semantic_release.cli.commit_new_version")
    mock_new_version = mocker.patch(
        "semantic_release.cli.get_new_version", return_value="2.0.0"
    )
    mock_evaluate_bump = mocker.patch(
        "semantic_release.cli.evaluate_version_bump", return_value="major"
    )
    mock_current_version = mocker.patch(
        "semantic_release.cli.get_current_version", return_value="1.2.3"
    )
    mock_current_release_version = mocker.patch(
        "semantic_release.cli.get_current_release_version", return_value="1.2.3"
    )

    version(config)

    # TODO: get rid of this
    commit_parser = get_commit_parser(config)

    mock_current_version.assert_called_once_with()
    mock_current_release_version.assert_called_once()
    mock_evaluate_bump.assert_called_once_with(
        commit_parser,
        "1.2.3",
        config.tag_format,
        config.patch_without_tag,
        config.major_on_zero,
        None,
    )
    mock_new_version.assert_called_once_with("1.2.3", "1.2.3", "major", False, True)
    assert not mock_set_new_version.called
    assert not mock_commit_new_version.called
    mock_tag_new_version.assert_called_once_with(config.tag_format, "2.0.0")


@pytest.mark.xfail(reason="Lambdas for commit parsers are different (by id()) - will need rework")
def test_version_by_tag_should_call_correct_functions(mocker):
    config = Config.from_files(version_source="tag")
    mock_set_new_version = mocker.patch("semantic_release.cli.set_new_version")
    mock_tag_new_version = mocker.patch("semantic_release.cli.tag_new_version")
    mock_new_version = mocker.patch(
        "semantic_release.cli.get_new_version", return_value="2.0.0"
    )
    mock_evaluate_bump = mocker.patch(
        "semantic_release.cli.evaluate_version_bump", return_value="major"
    )
    mock_current_version = mocker.patch(
        "semantic_release.cli.get_current_version", return_value="1.2.3"
    )
    mock_current_release_version = mocker.patch(
        "semantic_release.cli.get_current_release_version", return_value="1.2.3"
    )

    version(config)

    # TODO: get rid of this
    commit_parser = get_commit_parser(config)

    mock_current_version.assert_called_once()
    mock_current_release_version.assert_called_once()
    mock_evaluate_bump.assert_called_once_with(
        commit_parser,
        "1.2.3",
        config.tag_format,
        config.patch_without_tag,
        config.major_on_zero,
        None,
    )
    mock_new_version.assert_called_once_with("1.2.3", "1.2.3", "major", False, True)
    mock_set_new_version.assert_called_once_with(
        "2.0.0",
        config.version_variable,
        config.version_pattern,
        config.version_toml,
        config.prerelease_tag,
    )
    mock_tag_new_version.assert_called_once_with(config.tag_format, "2.0.0")


@pytest.mark.xfail(reason="Lambdas for commit parsers are different (by id()) - will need rework")
def test_version_by_tag_only_should_call_correct_functions(mocker):
    config = Config.from_files(version_source="tag_only")
    mock_set_new_version = mocker.patch("semantic_release.cli.set_new_version")
    mock_tag_new_version = mocker.patch("semantic_release.cli.tag_new_version")
    mock_new_version = mocker.patch(
        "semantic_release.cli.get_new_version", return_value="2.0.0"
    )
    mock_evaluate_bump = mocker.patch(
        "semantic_release.cli.evaluate_version_bump", return_value="major"
    )
    mock_current_version = mocker.patch(
        "semantic_release.cli.get_current_version", return_value="1.2.3"
    )
    mock_current_release_version = mocker.patch(
        "semantic_release.cli.get_current_release_version", return_value="1.2.3"
    )

    version(config)

    # TODO: get rid of this
    commit_parser = get_commit_parser(config)

    mock_current_version.assert_called_once_with()
    mock_current_release_version.assert_called_once()
    mock_evaluate_bump.assert_called_once_with(
        commit_parser,
        "1.2.3",
        config.tag_format,
        config.patch_without_tag,
        config.major_on_zero,
        None,
    )
    mock_new_version.assert_called_once_with("1.2.3", "1.2.3", "major", False, True)
    assert not mock_set_new_version.called
    mock_tag_new_version.assert_called_once_with(config.tag_format, "2.0.0")


@pytest.mark.xfail(reason="Lambdas for commit parsers are different (by id()) - will need rework")
def test_version_by_commit_without_tag_should_call_correct_functions(mocker):
    config = Config.from_files(version_source="commit", tag_commit=False)
    mock_set_new_version = mocker.patch("semantic_release.cli.set_new_version")
    mock_tag_new_version = mocker.patch("semantic_release.cli.tag_new_version")
    mock_commit_new_version = mocker.patch("semantic_release.cli.commit_new_version")
    mock_new_version = mocker.patch(
        "semantic_release.cli.get_new_version", return_value="2.0.0"
    )
    mock_evaluate_bump = mocker.patch(
        "semantic_release.cli.evaluate_version_bump", return_value="major"
    )
    mock_current_version = mocker.patch(
        "semantic_release.cli.get_current_version", return_value="1.2.3"
    )
    mock_current_release_version = mocker.patch(
        "semantic_release.cli.get_current_release_version", return_value="1.2.3"
    )

    version(config)

    # TODO: get rid of this
    commit_parser = get_commit_parser(config)

    mock_current_version.assert_called_once()
    mock_current_release_version.assert_called_once()
    mock_evaluate_bump.assert_called_once_with(
        commit_parser,
        "1.2.3",
        config.tag_format,
        config.patch_without_tag,
        config.major_on_zero,
        None,
    )
    mock_new_version.assert_called_once_with("1.2.3", "1.2.3", "major", False, True)
    mock_set_new_version.assert_called_once_with(
        "2.0.0",
        config.version_variable,
        config.version_pattern,
        config.version_toml,
        config.prerelease_tag,
    )
    mock_commit_new_version.assert_called_once_with(
        "2.0.0",
        config.version_variable,
        config.version_pattern,
        config.version_toml,
        config.prerelease_tag,
        config.commit_subject,
        config.commit_message,
        config.commit_author,
    )
    assert not mock_tag_new_version.called


def test_force_major(mocker, runner, default_config):
    mock_version = mocker.patch("semantic_release.cli.version")
    result = runner.invoke(main, ["version", "--major"])
    mock_version.assert_called_once_with(
        default_config,
        noop=False,
        post=False,
        force_level="major",
        prerelease=False,
        prerelease_patch=True,
        retry=False,
        define=()
    )
    assert mock_version.call_args_list[0][1]["force_level"] == "major"
    assert result.exit_code == 0


def test_force_minor(mocker, runner, default_config):
    mock_version = mocker.patch("semantic_release.cli.version")
    result = runner.invoke(main, ["version", "--minor"])
    mock_version.assert_called_once_with(
        default_config,
        noop=False,
        post=False,
        force_level="minor",
        prerelease=False,
        prerelease_patch=True,
        retry=False,
        define=()
    )
    assert mock_version.call_args_list[0][1]["force_level"] == "minor"
    assert result.exit_code == 0


def test_force_patch(mocker, runner, default_config):
    mock_version = mocker.patch("semantic_release.cli.version")
    result = runner.invoke(main, ["version", "--patch"])
    mock_version.assert_called_once_with(
        default_config,
        noop=False,
        post=False,
        force_level="patch",
        prerelease=False,
        prerelease_patch=True,
        retry=False,
        define=()
    )
    assert mock_version.call_args_list[0][1]["force_level"] == "patch"
    assert result.exit_code == 0


def test_retry(mocker, runner, default_config):
    mock_version = mocker.patch("semantic_release.cli.version")
    result = runner.invoke(main, ["version", "--retry"])
    mock_version.assert_called_once_with(
        default_config,
        noop=False,
        post=False,
        force_level=None,
        prerelease=False,
        prerelease_patch=True,
        retry=True,
        define=()
    )
    assert result.exit_code == 0


def test_prerelease_patch(mocker, runner, default_config):
    mock_version = mocker.patch("semantic_release.cli.version")
    result = runner.invoke(main, ["version", "--no-prerelease-patch"])
    mock_version.assert_called_once_with(
        default_config,
        noop=False,
        post=False,
        force_level=None,
        prerelease=False,
        prerelease_patch=False,
        retry=False,
        define=(),
    )
    assert result.exit_code == 0


def test_noop_mode(mocker, default_config):
    mock_tag_new_version = mocker.patch("semantic_release.cli.tag_new_version")
    mock_set_new = mocker.patch("semantic_release.cli.commit_new_version")
    mock_commit_new = mocker.patch("semantic_release.cli.set_new_version")
    mocker.patch("semantic_release.cli.evaluate_version_bump", lambda *a, **kw: "major")

    version(default_config, noop=True)

    assert not mock_set_new.called
    assert not mock_commit_new.called
    assert not mock_tag_new_version.called


def test_cli_print_version(mocker, runner, default_config):
    mock_print_version = mocker.patch("semantic_release.cli.print_version")
    result = runner.invoke(main, ["print-version"])
    mock_print_version.assert_called_once_with(
        default_config,
        current=False,
        force_level=None,
        prerelease=False,
        prerelease_patch=True,
        noop=False,
        post=False,
        retry=False,
        define=()
    )
    assert result.exit_code == 0


def test_cli_print_version_force_major(mocker, runner, default_config):
    mock_print_version = mocker.patch("semantic_release.cli.print_version")
    result = runner.invoke(main, ["print-version", "--major"])
    mock_print_version.assert_called_once_with(
        default_config,
        current=False,
        force_level="major",
        prerelease=False,
        prerelease_patch=True,
        noop=False,
        post=False,
        retry=False,
        define=()
    )
    assert result.exit_code == 0


def test_cli_print_version_prerelease(mocker, runner, default_config):
    mock_print_version = mocker.patch("semantic_release.cli.print_version")
    result = runner.invoke(main, ["print-version", "--prerelease"])
    mock_print_version.assert_called_once_with(
        default_config,
        current=False,
        force_level=None,
        prerelease=True,
        prerelease_patch=True,
        noop=False,
        post=False,
        retry=False,
        define=()
    )
    assert result.exit_code == 0


def test_cli_print_version_current(mocker, runner, default_config):
    mock_print_version = mocker.patch("semantic_release.cli.print_version")
    result = runner.invoke(main, ["print-version", "--current"])
    mock_print_version.assert_called_once_with(
        default_config,
        current=True,
        force_level=None,
        prerelease=False,
        prerelease_patch=True,
        noop=False,
        post=False,
        retry=False,
        define=()
    )
    assert result.exit_code == 0


def test_cli_print_version_next(mocker, runner, default_config):
    mock_print_version = mocker.patch("semantic_release.cli.print_version")
    result = runner.invoke(main, ["print-version", "--next"])
    mock_print_version.assert_called_once_with(
        default_config,
        current=False,
        force_level=None,
        prerelease=False,
        prerelease_patch=True,
        noop=False,
        post=False,
        retry=False,
        define=()
    )
    assert result.exit_code == 0


@pytest.mark.xfail(reason="Lambdas for commit parsers are different (by id()) - will need rework")
def test_print_version_no_change(mocker, runner, capsys, default_config):
    mock_new_version = mocker.patch(
        "semantic_release.cli.get_new_version", return_value="1.2.3"
    )
    mock_evaluate_bump = mocker.patch(
        "semantic_release.cli.evaluate_version_bump", return_value=None
    )
    mock_current_version = mocker.patch(
        "semantic_release.cli.get_current_version", return_value="1.2.3"
    )
    mock_current_release_version = mocker.patch(
        "semantic_release.cli.get_current_release_version", return_value="1.2.3"
    )

    print_version(default_config)
    outerr = capsys.readouterr()
    assert outerr.out == ""
    assert outerr.err == "No release will be made.\n"

    # TODO: remove
    commit_parser = get_commit_parser(default_config)
    mock_current_version.assert_called_once()
    mock_current_release_version.assert_called_once()
    mock_evaluate_bump.assert_called_once_with(
        commit_parser,
        "1.2.3",
        default_config.tag_format,
        default_config.patch_without_tag,
        default_config.major_on_zero,
        None,
    )
    mock_new_version.assert_called_once_with("1.2.3", "1.2.3", "major", False, True)


@pytest.mark.xfail(reason="Lambdas for commit parsers are different (by id()) - will need rework")
def test_print_version_change(mocker, runner, capsys, default_config):
    mock_current_version = mocker.patch(
        "semantic_release.cli.get_current_version", return_value="1.2.3"
    )
    mock_current_release_version = mocker.patch(
        "semantic_release.cli.get_current_release_version", return_value="1.2.3"
    )
    mock_evaluate_bump = mocker.patch(
        "semantic_release.cli.evaluate_version_bump", return_value="minor"
    )

    print_version(default_config)
    outerr = capsys.readouterr()
    assert outerr.out == "1.3.0"
    assert outerr.err == ""

    # TODO: remove
    commit_parser = get_commit_parser(default_config)
    mock_current_version.assert_called_once()
    mock_current_release_version.assert_called_once()
    mock_evaluate_bump.assert_called_once_with(
        commit_parser,
        "1.2.3",
        default_config.tag_format,
        default_config.patch_without_tag,
        default_config.major_on_zero,
        None,
    )


@pytest.mark.xfail(reason="Lambdas for commit parsers are different (by id()) - will need rework")
def test_print_version_change_prerelease(mocker, runner, capsys, default_config):
    mock_current_version = mocker.patch(
        "semantic_release.cli.get_current_version", return_value="1.2.3"
    )
    mock_current_release_version = mocker.patch(
        "semantic_release.cli.get_current_release_version", return_value="1.2.3"
    )
    mock_evaluate_bump = mocker.patch(
        "semantic_release.cli.evaluate_version_bump", return_value="minor"
    )

    print_version(default_config, prerelease=True)
    outerr = capsys.readouterr()
    assert outerr.out == "1.3.0-beta.1"
    assert outerr.err == ""

    # TODO: remove
    commit_parser = get_commit_parser(default_config)
    mock_current_version.assert_called_once()
    mock_current_release_version.assert_called_once()
    mock_evaluate_bump.assert_called_once_with(
        commit_parser,
        "1.2.3",
        default_config.tag_format,
        default_config.patch_without_tag,
        default_config.major_on_zero,
        None,
    )


@pytest.mark.xfail(reason="Lambdas for commit parsers are different (by id()) - will need rework")
def test_print_version_change_prerelease_no_patch(
    mocker, runner, capsys, default_config
):
    mock_current_version = mocker.patch(
        "semantic_release.cli.get_current_version", return_value="1.2.3"
    )
    mock_current_release_version = mocker.patch(
        "semantic_release.cli.get_current_release_version", return_value="1.2.3"
    )
    mock_evaluate_bump = mocker.patch(
        "semantic_release.cli.evaluate_version_bump", return_value=None
    )

    print_version(prerelease=True, prerelease_patch=False)
    outerr = capsys.readouterr()
    assert outerr.out == ""
    assert outerr.err == "No release will be made.\n"

    # TODO: remove
    commit_parser = get_commit_parser(default_config)
    mock_current_version.assert_called_once()
    mock_current_release_version.assert_called_once()
    mock_evaluate_bump.assert_called_once_with(
        commit_parser,
        "1.2.3",
        default_config.tag_format,
        default_config.patch_without_tag,
        default_config.major_on_zero,
        None,
    )


@pytest.mark.xfail(reason="Lambdas for commit parsers are different (by id()) - will need rework")
def test_print_version_change_prerelease_bump(mocker, runner, capsys, default_config):
    mock_current_version = mocker.patch(
        "semantic_release.cli.get_current_version", return_value="1.2.3"
    )
    mock_current_release_version = mocker.patch(
        "semantic_release.cli.get_current_release_version", return_value="1.2.3"
    )
    mock_evaluate_bump = mocker.patch(
        "semantic_release.cli.evaluate_version_bump", return_value="minor"
    )

    print_version(default_config, prerelease=True)
    outerr = capsys.readouterr()
    assert outerr.out == "1.3.0-beta.1"
    assert outerr.err == ""

    # TODO: remove
    commit_parser = get_commit_parser(default_config)
    mock_current_version.assert_called_once()
    mock_current_release_version.assert_called_once()
    mock_evaluate_bump.assert_called_once_with(
        commit_parser,
        "1.2.3",
        default_config.tag_format,
        default_config.patch_without_tag,
        default_config.major_on_zero,
        None,
    )


@pytest.mark.xfail(reason="Lambdas for commit parsers are different (by id()) - will need rework")
def test_print_version_force_major(mocker, runner, capsys, default_config):
    mock_current_version = mocker.patch(
        "semantic_release.cli.get_current_version", return_value="1.2.3"
    )
    mock_current_release_version = mocker.patch(
        "semantic_release.cli.get_current_release_version", return_value="1.2.3"
    )
    mock_evaluate_bump = mocker.patch(
        "semantic_release.cli.evaluate_version_bump", return_value="major"
    )

    print_version(default_config, force_level="major")
    outerr = capsys.readouterr()
    assert outerr.out == "2.0.0"
    assert outerr.err == ""

    # TODO: remove
    commit_parser = get_commit_parser(default_config)
    mock_current_version.assert_called_once()
    mock_current_release_version.assert_called_once()
    mock_evaluate_bump.assert_called_once_with(
        commit_parser,
        "1.2.3",
        default_config.tag_format,
        default_config.patch_without_tag,
        default_config.major_on_zero,
        "force",
    )


@pytest.mark.xfail(reason="Lambdas for commit parsers are different (by id()) - will need rework")
def test_print_version_force_major_prerelease(mocker, runner, capsys, default_config):
    mock_current_version = mocker.patch(
        "semantic_release.cli.get_current_version", return_value="1.2.3"
    )
    mock_current_release_version = mocker.patch(
        "semantic_release.cli.get_current_release_version", return_value="1.2.3"
    )
    mock_evaluate_bump = mocker.patch(
        "semantic_release.cli.evaluate_version_bump", return_value="major"
    )

    print_version(default_config, force_level="major", prerelease=True)
    outerr = capsys.readouterr()
    assert outerr.out == "2.0.0-beta.1"
    assert outerr.err == ""

    # TODO: remove
    commit_parser = get_commit_parser(default_config)
    mock_current_version.assert_called_once()
    mock_current_release_version.assert_called_once()
    mock_evaluate_bump.assert_called_once_with(
        commit_parser,
        "1.2.3",
        default_config.tag_format,
        default_config.patch_without_tag,
        default_config.major_on_zero,
        "force",
    )


@pytest.mark.xfail(reason="Lambdas for commit parsers are different (by id()) - will need rework")
def test_version_no_change(mocker, runner, default_config):
    mock_tag_new_version = mocker.patch("semantic_release.cli.tag_new_version")
    mock_commit_new_version = mocker.patch("semantic_release.cli.commit_new_version")
    mock_set_new_version = mocker.patch("semantic_release.cli.set_new_version")
    mock_new_version = mocker.patch(
        "semantic_release.cli.get_new_version", return_value="1.2.3"
    )
    mock_evaluate_bump = mocker.patch(
        "semantic_release.cli.evaluate_version_bump", return_value=None
    )
    mock_current_version = mocker.patch(
        "semantic_release.cli.get_current_version", return_value="1.2.3"
    )
    mock_current_release_version = mocker.patch(
        "semantic_release.cli.get_current_release_version", return_value="1.2.3"
    )

    version(default_config)

    # TODO: remove
    commit_parser = get_commit_parser(default_config)

    mock_current_version.assert_called_once()
    mock_current_release_version.assert_called_once()
    mock_evaluate_bump.assert_called_once_with(
        commit_parser,
        "1.2.3",
        default_config.tag_format,
        default_config.patch_without_tag,
        default_config.major_on_zero,
        None,
    )
    mock_new_version.assert_called_once_with("1.2.3", "1.2.3", None, False, True)
    assert not mock_set_new_version.called
    assert not mock_commit_new_version.called
    assert not mock_tag_new_version.called


def test_version_check_build_status_fails(mocker):
    mock_check_build_status = mocker.patch(
        "semantic_release.cli.do_check_build_status", return_value=False
    )
    config = Config.from_files(check_build_status=True)
    mock_tag_new_version = mocker.patch("semantic_release.cli.tag_new_version")
    mock_commit_new = mocker.patch("semantic_release.cli.commit_new_version")
    mock_set_new = mocker.patch("semantic_release.cli.set_new_version")
    mocker.patch("semantic_release.cli.evaluate_version_bump", lambda *x: "major")

    version(config)

    assert mock_check_build_status.called
    assert not mock_set_new.called
    assert not mock_commit_new.called
    assert not mock_tag_new_version.called


def test_version_by_commit_check_build_status_succeeds(mocker):
    config = Config.from_files(check_build_status=True)
    mock_check_build_status = mocker.patch(
        "semantic_release.cli.do_check_build_status", return_value=True
    )
    mock_tag_new_version = mocker.patch("semantic_release.cli.tag_new_version")
    mocker.patch("semantic_release.cli.evaluate_version_bump", lambda *a, **kw: "major")
    mock_commit_new = mocker.patch("semantic_release.cli.commit_new_version")
    mock_set_new = mocker.patch("semantic_release.cli.set_new_version")

    version(config)

    assert mock_check_build_status.called
    assert mock_set_new.called
    assert mock_commit_new.called
    assert mock_tag_new_version.called


def test_version_by_tag_check_build_status_succeeds(mocker):

    config = Config.from_files(
        version_source="tag", commit_version_number=False, check_build_status=True
    )
    mock_check_build_status = mocker.patch(
        "semantic_release.cli.do_check_build_status", return_value=True
    )
    mock_set_new_version = mocker.patch("semantic_release.cli.set_new_version")
    mock_tag_new_version = mocker.patch("semantic_release.cli.tag_new_version")
    mocker.patch("semantic_release.cli.evaluate_version_bump", lambda *a, **kw: "major")

    version(config)

    assert mock_check_build_status.called
    assert mock_set_new_version.called
    assert mock_tag_new_version.called


def test_version_by_tag_only_check_build_status_succeeds(mocker):
    config = Config.from_files(
        version_source="tag_only", commit_version_number=False, check_build_status=True
    )
    mock_check_build_status = mocker.patch(
        "semantic_release.cli.do_check_build_status", return_value=True
    )
    mock_set_new_version = mocker.patch("semantic_release.cli.set_new_version")
    mock_tag_new_version = mocker.patch("semantic_release.cli.tag_new_version")
    mocker.patch("semantic_release.cli.evaluate_version_bump", lambda *a, **kw: "major")

    version(config)

    assert mock_check_build_status.called
    assert not mock_set_new_version.called
    assert mock_tag_new_version.called


def test_version_check_build_status_not_called_if_disabled(mocker):
    config = Config.from_files(check_build_status=False)
    mock_check_build_status = mocker.patch("semantic_release.cli.do_check_build_status")
    mocker.patch("semantic_release.cli.tag_new_version")
    mocker.patch("semantic_release.cli.evaluate_version_bump", lambda *x: "major")
    mocker.patch("semantic_release.cli.commit_new_version")
    mocker.patch("semantic_release.cli.set_new_version")

    version(config)

    assert not mock_check_build_status.called


def test_version_retry_and_giterror(mocker, default_config):
    mocker.patch(
        "semantic_release.cli.get_current_version", mock.Mock(side_effect=GitError())
    )

    result = version(default_config, retry=True)

    assert not result

@pytest.mark.xfail(reason="Lambdas for commit parsers are different (by id()) - will need rework")
def test_version_retry(mocker):
    mock_current_version = mocker.patch(
        "semantic_release.cli.get_current_version", return_value="1.2.3"
    )
    mock_current_release_version = mocker.patch(
        "semantic_release.cli.get_current_release_version", return_value="1.2.3"
    )
    mock_evaluate_bump = mocker.patch(
        "semantic_release.cli.evaluate_version_bump", return_value="patch"
    )
    mock_get_new = mocker.patch(
        "semantic_release.cli.get_new_version", return_value="new"
    )
    config = Config.from_files(check_build_status = False, commit_version_number=False)

    # TODO: remove
    commit_parser = get_commit_parser(config)

    result = version(config, noop=False, retry=True, force_level=False)

    assert result
    mock_current_version.assert_called_once()
    mock_current_release_version.assert_called_once()
    mock_evaluate_bump.assert_called_once_with(
        commit_parser,
        "1.2.3",
        config.tag_format,
        config.patch_without_tag,
        config.major_on_zero,
        False,
    )
    mock_get_new.assert_called_once_with("1.2.3", "1.2.3", "patch", False, True)


def test_publish_should_not_run_pre_commit_by_default(mocker):
    mocker.patch("semantic_release.cli.checkout")
    mocker.patch("semantic_release.cli.ci_checks.check")
    mocker.patch.object(ArtifactRepo, "upload")
    mocker.patch("semantic_release.cli.do_upload_to_release")
    mocker.patch("semantic_release.cli.post_changelog", lambda *a, **kw: True)
    mocker.patch("semantic_release.cli.push_new_version", return_value=True)
    mocker.patch("semantic_release.cli.should_bump_version", return_value=True)
    mocker.patch("semantic_release.cli.markdown_changelog", lambda *x, **y: "CHANGES")
    mocker.patch("semantic_release.cli.update_changelog_file")
    mocker.patch("semantic_release.cli.bump_version")
    mocker.patch("semantic_release.cli.get_new_version", lambda *a, **kw: "2.0.0")
    mocker.patch("semantic_release.cli.check_token", lambda *a, **kw: True)
    run_pre_commit = mocker.patch("semantic_release.cli.run")
    config = Config.from_files(remove_dist=False, upload_to_pypi=False, upload_to_release=False)
    mocker.patch("semantic_release.cli.update_changelog_file", lambda *x, **y: None)

    publish(config)

    assert not run_pre_commit.called


def test_publish_should_not_run_pre_commit_with_empty_command(mocker):
    mocker.patch("semantic_release.cli.checkout")
    mocker.patch("semantic_release.cli.ci_checks.check")
    mocker.patch.object(ArtifactRepo, "upload")
    mocker.patch("semantic_release.cli.do_upload_to_release")
    mocker.patch("semantic_release.cli.post_changelog", lambda *a, **kw: True)
    mocker.patch("semantic_release.cli.push_new_version", return_value=True)
    mocker.patch("semantic_release.cli.should_bump_version", return_value=True)
    mocker.patch("semantic_release.cli.markdown_changelog", lambda *x, **y: "CHANGES")
    mocker.patch("semantic_release.cli.update_changelog_file")
    mocker.patch("semantic_release.cli.bump_version")
    mocker.patch("semantic_release.cli.get_new_version", lambda *x, **kw: "2.0.0")
    mocker.patch("semantic_release.cli.check_token", lambda *a, **kw: True)
    run_pre_commit = mocker.patch("semantic_release.cli.run")
    config = Config.from_files(
        remove_dist=False,
        upload_to_pypi=False,
        upload_to_release=False,
        pre_commit_command="",
    )
    mocker.patch("semantic_release.cli.update_changelog_file", lambda *x, **y: None)

    publish(config)

    assert not run_pre_commit.called


def test_publish_should_run_pre_commit_if_provided(mocker):
    mocker.patch("semantic_release.cli.checkout")
    mocker.patch("semantic_release.cli.ci_checks.check")
    mocker.patch.object(ArtifactRepo, "upload")
    mocker.patch("semantic_release.cli.do_upload_to_release")
    mocker.patch("semantic_release.cli.post_changelog", lambda *x, **kw: True)
    mocker.patch("semantic_release.cli.push_new_version", return_value=True)
    mocker.patch("semantic_release.cli.should_bump_version", return_value=True)
    mocker.patch("semantic_release.cli.markdown_changelog", lambda *x, **y: "CHANGES")
    mocker.patch("semantic_release.cli.update_changelog_file")
    mocker.patch("semantic_release.cli.bump_version")
    mocker.patch("semantic_release.cli.get_new_version", lambda *a, **kw: "2.0.0")
    mocker.patch("semantic_release.cli.check_token", lambda *a, **kw: True)
    run_pre_commit = mocker.patch("semantic_release.cli.run")
    config = Config.from_files(
        remove_dist=False,
        upload_to_pypi=False,
        upload_to_release=False,
        pre_commit_command='echo "Hello, world."',
    )
    mocker.patch("semantic_release.cli.update_changelog_file", lambda *x, **y: None)

    publish(config)

    assert run_pre_commit.called


def test_publish_should_not_upload_to_pypi_if_option_is_false(mocker):
    mocker.patch("semantic_release.cli.checkout")
    mocker.patch("semantic_release.cli.ci_checks.check")
    mock_repository = mocker.patch.object(ArtifactRepo, "upload")
    mock_upload_release = mocker.patch("semantic_release.cli.do_upload_to_release")
    mocker.patch("semantic_release.cli.post_changelog", lambda *a, **kw: True)
    mocker.patch("semantic_release.cli.push_new_version", return_value=True)
    mocker.patch("semantic_release.cli.should_bump_version", return_value=False)
    mocker.patch("semantic_release.cli.markdown_changelog", lambda *x, **y: "CHANGES")
    mocker.patch("semantic_release.cli.update_changelog_file")
    mocker.patch("semantic_release.cli.bump_version")
    mocker.patch("semantic_release.cli.get_new_version", lambda *a, **kw: "2.0.0")
    mocker.patch("semantic_release.cli.check_token", lambda *a, **kw: True)
    config = Config.from_files(
        remove_dist=False,
        upload_to_pypi=False,
        upload_to_release=False,
    )
    mocker.patch("semantic_release.cli.update_changelog_file", lambda *x, **y: None)

    publish(config)

    assert not mock_repository.called
    assert not mock_upload_release.called


def test_publish_should_not_upload_to_repository_if_option_is_false(mocker):
    mocker.patch("semantic_release.cli.checkout")
    mocker.patch("semantic_release.cli.ci_checks.check")
    mock_repository = mocker.patch.object(ArtifactRepo, "upload")
    mock_upload_release = mocker.patch("semantic_release.cli.do_upload_to_release")
    mocker.patch("semantic_release.cli.post_changelog", lambda *a, **kw: True)
    mocker.patch("semantic_release.cli.push_new_version", return_value=True)
    mocker.patch("semantic_release.cli.should_bump_version", return_value=False)
    mocker.patch("semantic_release.cli.markdown_changelog", lambda *x, **y: "CHANGES")
    mocker.patch("semantic_release.cli.update_changelog_file")
    mocker.patch("semantic_release.cli.bump_version")
    mocker.patch("semantic_release.cli.get_new_version", lambda *a, **kw: "2.0.0")
    mocker.patch("semantic_release.cli.check_token", lambda *a, **kw: True)
    config = Config.from_files(
        remove_dist=False,
        upload_to_repository=False,
        upload_to_release=False,
    )
    mocker.patch("semantic_release.cli.update_changelog_file", lambda *x, **y: None)

    publish(config)

    assert not mock_repository.called
    assert not mock_upload_release.called


def test_publish_should_do_nothing_when_not_should_bump_version(mocker, default_config):
    mocker.patch("semantic_release.cli.checkout")
    mocker.patch("semantic_release.cli.get_new_version", lambda *a, **kw: "2.0.0")
    mocker.patch("semantic_release.cli.evaluate_version_bump", lambda *a, **kw: "feature")
    mocker.patch("semantic_release.cli.generate_changelog")
    mock_log = mocker.patch("semantic_release.cli.post_changelog")
    mock_repository = mocker.patch.object(ArtifactRepo, "upload")
    mock_upload_release = mocker.patch("semantic_release.cli.do_upload_to_release")
    mock_push = mocker.patch("semantic_release.cli.push_new_version")
    mock_ci_check = mocker.patch("semantic_release.ci_checks.check")
    mock_should_bump_version = mocker.patch(
        "semantic_release.cli.should_bump_version", return_value=False
    )

    publish(default_config)

    assert mock_should_bump_version.called
    assert not mock_push.called
    assert not mock_repository.called
    assert not mock_upload_release.called
    assert not mock_log.called
    assert mock_ci_check.called


def test_publish_should_call_functions(mocker, default_config):
    mock_push = mocker.patch("semantic_release.cli.push_new_version")
    mock_checkout = mocker.patch("semantic_release.cli.checkout")
    mock_should_bump_version = mocker.patch(
        "semantic_release.cli.should_bump_version", return_value=True
    )
    mock_log = mocker.patch("semantic_release.cli.post_changelog")
    mock_ci_check = mocker.patch("semantic_release.ci_checks.check")
    mocker.patch.dict(
        "os.environ",
        {
            "REPOSITORY_USERNAME": "repo-username",
            "REPOSITORY_PASSWORD": "repo-password",
        },
    )
    mock_repository = mocker.patch.object(ArtifactRepo, "upload")
    mock_release = mocker.patch("semantic_release.cli.do_upload_to_release")
    mock_build_dists = mocker.patch("semantic_release.cli.build_dists")
    mock_remove_dists = mocker.patch("semantic_release.cli.remove_dists")
    mocker.patch(
        "semantic_release.cli.get_repository_owner_and_name",
        return_value=("relekang", "python-semantic-release"),
    )
    mocker.patch("semantic_release.cli.evaluate_version_bump", lambda *a, **kw: "feature")
    mocker.patch("semantic_release.cli.generate_changelog")
    mocker.patch("semantic_release.cli.markdown_changelog", lambda *x, **y: "CHANGES")
    mocker.patch("semantic_release.cli.update_changelog_file")
    mocker.patch("semantic_release.cli.bump_version")
    mocker.patch("semantic_release.cli.get_new_version", lambda *a, **kw: "2.0.0")
    mocker.patch("semantic_release.cli.check_token", lambda *a, **kw: True)

    publish(default_config)

    assert mock_ci_check.called
    assert mock_push.called
    assert mock_remove_dists.called
    assert mock_build_dists.called
    assert mock_repository.called
    assert mock_release.called
    assert mock_should_bump_version.called
    mock_log.assert_called_once_with(
        default_config.hvcs, "relekang", "python-semantic-release", default_config.tag_format, semantic_release.__version__, "CHANGES", default_config.github_token_var, hvcs_domain = default_config.hvcs_domain, hvcs_api_domain=default_config.hvcs_api_domain
    )
    mock_checkout.assert_called_once_with("master")


def test_publish_should_skip_build_when_command_is_empty(mocker):
    mock_push = mocker.patch("semantic_release.cli.push_new_version")
    mock_checkout = mocker.patch("semantic_release.cli.checkout")
    mock_should_bump_version = mocker.patch(
        "semantic_release.cli.should_bump_version", return_value=True
    )
    mock_log = mocker.patch("semantic_release.cli.post_changelog")
    mock_ci_check = mocker.patch("semantic_release.ci_checks.check")
    mocker.patch.dict(
        "os.environ",
        {
            "REPOSITORY_USERNAME": "repo-username",
            "REPOSITORY_PASSWORD": "repo-password",
        },
    )
    mock_repository = mocker.patch.object(ArtifactRepo, "upload")
    mock_release = mocker.patch("semantic_release.cli.do_upload_to_release")
    mock_build_dists = mocker.patch("semantic_release.cli.build_dists")
    mock_remove_dists = mocker.patch("semantic_release.cli.remove_dists")
    mocker.patch(
        "semantic_release.cli.get_repository_owner_and_name",
        return_value=("relekang", "python-semantic-release"),
    )
    mocker.patch("semantic_release.cli.evaluate_version_bump", lambda *a, **kw: "feature")
    mocker.patch("semantic_release.cli.generate_changelog")
    mocker.patch("semantic_release.cli.markdown_changelog", lambda *x, **y: "CHANGES")
    mocker.patch("semantic_release.cli.update_changelog_file")
    mocker.patch("semantic_release.cli.bump_version")
    mocker.patch("semantic_release.cli.get_new_version", lambda *a: "2.0.0")
    mocker.patch("semantic_release.cli.check_token", lambda *a, **kw: True)

    # TODO: this should be isolated from project metadata
    config = Config.from_files(build_command="")
    publish(config)

    assert mock_ci_check.called
    assert mock_push.called
    assert not mock_remove_dists.called
    assert not mock_build_dists.called
    assert mock_repository.called
    assert mock_release.called
    assert mock_should_bump_version.called
    mock_log.assert_called_once_with(
        config.hvcs, "relekang", "python-semantic-release", config.tag_format, semantic_release.__version__, "CHANGES", config.github_token_var, hvcs_domain=config.hvcs_domain, hvcs_api_domain=config.hvcs_api_domain
    )
    mock_checkout.assert_called_once_with("master")


def test_publish_retry_version_fail(mocker):
    mock_get_current = mocker.patch(
        "semantic_release.cli.get_current_version", return_value="current"
    )
    mock_current_release_version = mocker.patch(
        "semantic_release.cli.get_current_release_version", return_value="1.2.3"
    )
    get_previous_release_version = mocker.patch(
        "semantic_release.cli.get_previous_release_version", return_value="previous"
    )
    mock_get_owner_name = mocker.patch(
        "semantic_release.cli.get_repository_owner_and_name",
        return_value=("owner", "name"),
    )
    mock_ci_check = mocker.patch("semantic_release.ci_checks.check")
    mock_checkout = mocker.patch("semantic_release.cli.checkout")
    mock_should_bump_version = mocker.patch(
        "semantic_release.cli.should_bump_version", return_value=False
    )
    config = Config.from_files(branch="my_branch")

    publish(config, noop=False, retry=True, force_level=False)

    mock_get_current.assert_called_once()
    mock_current_release_version.assert_called_once()
    get_previous_release_version.assert_called_once_with(
        "current", config.prerelease_tag, config.commit_subject
    )
    mock_get_owner_name.assert_called_once_with()
    mock_ci_check.assert_called()
    mock_checkout.assert_called_once_with("my_branch")
    mock_should_bump_version.assert_called_once_with(
        current_version="previous",
        new_version="current",
        current_release_version="1.2.3",
        prerelease=False,
        hvcs=config.hvcs,
        check_build_status=config.check_build_status,
        noop=False,
        retry=True,
    )


def test_publish_bad_token(mocker):
    mock_get_current = mocker.patch(
        "semantic_release.cli.get_current_version", return_value="current"
    )
    mock_current_release_version = mocker.patch(
        "semantic_release.cli.get_current_release_version", return_value="1.2.3"
    )
    get_previous_release_version = mocker.patch(
        "semantic_release.cli.get_previous_release_version", return_value="previous"
    )
    mock_get_owner_name = mocker.patch(
        "semantic_release.cli.get_repository_owner_and_name",
        return_value=("owner", "name"),
    )
    mock_ci_check = mocker.patch("semantic_release.ci_checks.check")
    mock_checkout = mocker.patch("semantic_release.cli.checkout")
    mock_should_bump_version = mocker.patch("semantic_release.cli.should_bump_version")
    mock_get_token = mocker.patch(
        "semantic_release.cli.get_token", return_value="SUPERTOKEN"
    )
    mock_get_domain = mocker.patch(
        "semantic_release.cli.get_domain", return_value="domain"
    )
    mock_push = mocker.patch("semantic_release.cli.push_new_version")
    mock_check_token = mocker.patch(
        "semantic_release.cli.check_token", return_value=False
    )
    config = Config.from_files(
        branch="my_branch",
        upload_to_repository=False,
        upload_to_release=False,
        remove_dist=False,
    )

    publish(config, noop=False, retry=True, force_level=False)

    mock_get_current.assert_called_once()
    mock_current_release_version.assert_called_once()
    get_previous_release_version.assert_called_once_with(
        "current", config.prerelease_tag, config.commit_subject
    )
    mock_get_owner_name.assert_called_once_with()
    mock_ci_check.assert_called()
    mock_checkout.assert_called_once_with("my_branch")
    mock_should_bump_version.assert_called_once_with(
        current_version="previous",
        new_version="current",
        current_release_version="1.2.3",
        prerelease=False,
        hvcs=config.hvcs,
        check_build_status=config.check_build_status,
        noop=False,
        retry=True,
    )
    mock_get_token.assert_called()
    mock_get_domain.assert_called()
    mock_push.assert_called_once_with(
        config.hvcs,
        config.ignore_token_for_push,
        auth_token="SUPERTOKEN",
        owner="owner",
        name="name",
        branch="my_branch",
        domain="domain",
    )
    mock_check_token.assert_called_once_with(config.hvcs, config.github_token_var)


@pytest.mark.xfail(reason="Lambdas for commit parsers are different (by id()) - will need rework")
def test_publish_giterror_when_posting(mocker):
    mock_current_version = mocker.patch(
        "semantic_release.cli.get_current_version", return_value="1.2.3"
    )
    mock_current_release_version = mocker.patch(
        "semantic_release.cli.get_current_release_version", return_value="1.2.3"
    )
    mock_evaluate = mocker.patch(
        "semantic_release.cli.evaluate_version_bump", return_value="patch"
    )
    mock_get_new = mocker.patch(
        "semantic_release.cli.get_new_version", return_value="new"
    )
    mock_get_owner_name = mocker.patch(
        "semantic_release.cli.get_repository_owner_and_name",
        return_value=("owner", "name"),
    )
    mock_ci_check = mocker.patch("semantic_release.ci_checks.check")
    mock_checkout = mocker.patch("semantic_release.cli.checkout")
    mock_bump_version = mocker.patch("semantic_release.cli.bump_version")
    mock_should_bump_version = mocker.patch(
        "semantic_release.cli.should_bump_version", return_value=True
    )
    mock_get_token = mocker.patch(
        "semantic_release.cli.get_token", return_value="SUPERTOKEN"
    )
    mock_get_domain = mocker.patch(
        "semantic_release.cli.get_domain", return_value="domain"
    )
    mock_push = mocker.patch("semantic_release.cli.push_new_version")
    mock_check_token = mocker.patch(
        "semantic_release.cli.check_token", return_value=True
    )
    mock_generate = mocker.patch(
        "semantic_release.cli.generate_changelog", return_value="super changelog"
    )
    mock_markdown = mocker.patch(
        "semantic_release.cli.markdown_changelog", return_value="super md changelog"
    )
    mock_update_changelog_file = mocker.patch(
        "semantic_release.cli.update_changelog_file"
    )
    mock_post = mocker.patch(
        "semantic_release.cli.post_changelog", mock.Mock(side_effect=GitError())
    )
    config = Config.from_files(
        branch="my_branch",
        upload_to_repository=False,
        upload_to_release=False,
        remove_dist=False,
    )

    publish(config, noop=False, retry=False, force_level=False)

    # TODO: remove
    commit_parser = get_commit_parser(config)

    mock_current_version.assert_called_once()
    mock_current_release_version.assert_called_once()
    mock_evaluate.assert_called_once_with(
        commit_parser,
        "1.2.3",
        config.tag_format,
        patch_without_tag=config.patch_without_tag,
        major_on_zero=config.major_on_zero,
        force=False,
    )
    mock_get_new.assert_called_once_with("1.2.3", "1.2.3", "patch", False, True)
    mock_get_owner_name.assert_called_once_with()
    mock_ci_check.assert_called()
    mock_checkout.assert_called_once_with("my_branch")
    mock_should_bump_version.assert_called_once_with(
        current_version="1.2.3",
        new_version="new",
        current_release_version="1.2.3",
        prerelease=False,
        hvcs=config.hvcs,
        check_build_status=config.check_build_status,
        noop=False,
        retry=False,
    )
    mock_update_changelog_file.assert_called_once_with(
        "new", "super md changelog", config.changelog_file, config.changelog_placeholder
    )
    mock_bump_version.assert_called_once_with(
        "new",
        "patch",
        prerelease_tag=config.prerelease_tag,
        commit_subject=config.commit_subject,
        commit_message=config.commit_message,
        version_variable=config.version_variable,
        version_pattern=config.version_pattern,
        version_toml=config.version_toml,
        tag_format=config.tag_format,
        commit_author=config.commit_author,
        tag_commit=config.tag_commit,
        commit_version_number=config.commit_version_number,
        version_source=config.version_source,
    )
    mock_get_token.assert_called_once_with()
    mock_get_domain.assert_called_once_with()
    mock_push.assert_called_once_with(
        config.hvcs,
        config.ignore_token_for_push,
        auth_token="SUPERTOKEN",
        owner="owner",
        name="name",
        branch="my_branch",
        domain="domain",
    )
    mock_check_token.assert_called_once_with(config.hvcs, config.github_token_var)
    mock_generate.assert_called_once_with(commit_parser, "1.2.3")
    mock_markdown.assert_called_once_with(
        "owner",
        "name",
        "new",
        "super changelog",
        changelog_sections=config.changelog_sections,
        changelog_components=config.changelog_components,
        hvcs=config.hvcs,
        hvcs_domain=config.hvcs_domain,
        header=False,
        previous_version="1.2.3",
    )
    mock_post.assert_called_once_with(
        config.hvcs,
        "owner",
        "name",
        config.tag_format,
        "new",
        "super md changelog",
        config.github_token_var,
        hvcs_domain=config.hvcs_domain,
        hvcs_api_domain=config.hvcs_api_domain,
    )


def test_changelog_should_call_functions(mocker, runner, default_config):
    mock_changelog = mocker.patch("semantic_release.cli.changelog", return_value=True)
    result = runner.invoke(main, ["changelog"])
    assert result.exit_code == 0
    mock_changelog.assert_called_once_with(
        default_config,
        noop=False,
        post=False,
        force_level=None,
        prerelease=False,
        prerelease_patch=True,
        retry=False,
        unreleased=False,
        define=()
    )


def test_overload_by_cli(mocker, runner):
    mock_read_text = mocker.patch(
        "semantic_release.history.Path.read_text", mock_version_file
    )
    runner.invoke(
        main,
        [
            "version",
            "--noop",
            "--patch",
            "-D",
            "version_variable=my_version_path:my_version_var",
        ],
    )

    mock_read_text.assert_called_once_with()
    mock_read_text.reset_mock()


@pytest.mark.xfail(reason="Lambdas for commit parsers are different (by id()) - will need rework")
def test_changelog_noop(mocker, default_config):
    mocker.patch("semantic_release.cli.get_current_version", return_value="current")
    mock_previous_version = mocker.patch(
        "semantic_release.cli.get_previous_version", return_value="previous"
    )
    mock_generate_changelog = mocker.patch(
        "semantic_release.cli.generate_changelog", return_value="super changelog"
    )
    mock_markdown_changelog = mocker.patch(
        "semantic_release.cli.markdown_changelog", return_value="super changelog"
    )
    mocker.patch(
        "semantic_release.cli.get_repository_owner_and_name",
        return_value=("owner", "name"),
    )

    changelog(default_config, noop=True, unreleased=False)

    # TODO: remove
    commit_parser = get_commit_parser(default_config)

    mock_previous_version.assert_called_once_with("current", default_config.prerelease_tag, default_config.tag_format)
    mock_generate_changelog.assert_called_once_with(
        commit_parser, "previous", "current"
    )
    mock_markdown_changelog.assert_called_once_with(
        "owner",
        "name",
        "current",
        "super changelog",
        changelog_sections=default_config.changelog_sections,
        changelog_components=default_config.changelog_components,
        hvcs=default_config.hvcs,
        hvcs_domain=default_config.hvcs_domain,
        header=False,
        previous_version="previous",
    )


@pytest.mark.xfail(reason="Lambdas for commit parsers are different (by id()) - will need rework")
def test_changelog_post_unreleased_no_token(mocker, default_config):
    mocker.patch("semantic_release.cli.get_current_version", return_value="current")
    mock_previous_version = mocker.patch(
        "semantic_release.cli.get_previous_version", return_value="previous"
    )
    mock_generate_changelog = mocker.patch(
        "semantic_release.cli.generate_changelog", return_value="super changelog"
    )
    mock_markdown_changelog = mocker.patch(
        "semantic_release.cli.markdown_changelog", return_value="super changelog"
    )
    mock_check_token = mocker.patch(
        "semantic_release.cli.check_token", return_value=False
    )
    mocker.patch(
        "semantic_release.cli.get_repository_owner_and_name",
        return_value=("owner", "name"),
    )

    changelog(default_config, unreleased=True, post=True)

    # TODO: remove
    commit_parser = get_commit_parser(default_config)

    mock_previous_version.assert_called_once_with(
        "current", default_config.prerelease_tag, default_config.tag_format
    )
    mock_generate_changelog.assert_called_once_with(commit_parser, "current", None)
    mock_markdown_changelog.assert_called_once_with(
        "owner",
        "name",
        "current",
        "super changelog",
        changelog_sections=default_config.changelog_sections,
        changelog_components=default_config.changelog_components,
        hvcs=default_config.hvcs,
        hvcs_domain=default_config.hvcs_domain,
        header=False,
        previous_version="previous",
    )
    mock_check_token.assert_called_once_with(
        default_config.hvcs, default_config.github_token_var
    )


@pytest.mark.xfail(reason="Lambdas for commit parsers are different (by id()) - will need rework")
def test_changelog_post_complete(mocker, default_config):
    mocker.patch("semantic_release.cli.get_current_version", return_value="current")
    mock_previous_version = mocker.patch(
        "semantic_release.cli.get_previous_version", return_value="previous"
    )
    mock_generate_changelog = mocker.patch(
        "semantic_release.cli.generate_changelog", return_value="super changelog"
    )
    mock_markdown_changelog = mocker.patch(
        "semantic_release.cli.markdown_changelog", return_value="super md changelog"
    )
    mock_check_token = mocker.patch(
        "semantic_release.cli.check_token", return_value=True
    )
    mock_get_owner_name = mocker.patch(
        "semantic_release.cli.get_repository_owner_and_name",
        return_value=("owner", "name"),
    )
    mock_post_changelog = mocker.patch("semantic_release.cli.post_changelog")

    changelog(default_config, unreleased=True, post=True)

    # TODO: remove
    commit_parser = get_commit_parser(default_config)

    mock_previous_version.assert_called_once_with(
        "current", default_config.prerelease_tag, default_config.tag_format
    )
    mock_generate_changelog.assert_called_once_with(commit_parser, "current", None)
    mock_markdown_changelog.assert_any_call(
        "owner", "name", "current", "super changelog", header=False
    )
    mock_check_token.assert_called_once_with()
    mock_get_owner_name.assert_called_once_with()
    mock_post_changelog.assert_called_once_with(
        "owner",
        "name",
        "current",
        "super changelog",
        changelog_sections=default_config.changelog_sections,
        changelog_components=default_config.changelog_components,
        hvcs=default_config.hvcs,
        hvcs_domain=default_config.hvcs_domain,
        header=False,
        previous_version="previous",
    )


def test_changelog_raises_exception_when_no_current_version(mocker, default_config):
    mocker.patch("semantic_release.cli.get_current_version", return_value=None)
    with pytest.raises(ImproperConfigurationError):
        changelog(default_config)
