import os
import platform
from textwrap import dedent
from unittest import TestCase

from semantic_release.errors import ImproperConfigurationError
from semantic_release.history import parser_angular
from semantic_release.settings import Config, get_commit_parser

import pytest

from . import mock  # , reset_config

# assert reset_config


# Set path to this directory
temp_dir = (
    os.path.join(os.path.abspath(os.path.dirname(__file__)), "tmp")
    if platform.system() == "Windows"
    else "/tmp/"
)


class ConfigTests(TestCase):
    @mock.patch(
        "semantic_release.settings.getcwd",
        return_value=os.path.abspath(os.path.dirname(os.path.dirname(__file__))),
    )
    def test_config(self, mock_getcwd):
        config = Config.from_files()
        self.assertEqual(
            config.version_variable,
            "semantic_release/__init__.py:__version__",
        )

    @mock.patch("semantic_release.settings.getcwd", return_value=temp_dir)
    def test_defaults(self, mock_getcwd):
        config = Config.from_files()
        mock_getcwd.assert_called_once_with()
        self.assertEqual(config.minor_tag, ":sparkles:")
        self.assertEqual(config.fix_tag, ":nut_and_bolt:")
        self.assertFalse(config.patch_without_tag)
        self.assertTrue(config.major_on_zero)
        self.assertFalse(config.check_build_status)
        self.assertEqual(config.hvcs, "github")
        self.assertEqual(config.upload_to_repository, True)
        self.assertEqual(config.github_token_var, "GH_TOKEN")
        self.assertEqual(config.gitea_token_var, "GITEA_TOKEN")
        self.assertEqual(config.gitlab_token_var, "GL_TOKEN")
        self.assertEqual(config.pypi_pass_var, "PYPI_PASSWORD")
        self.assertEqual(config.pypi_token_var, "PYPI_TOKEN")
        self.assertEqual(config.pypi_user_var, "PYPI_USERNAME")
        self.assertEqual(config.repository_user_var, "REPOSITORY_USERNAME")
        self.assertEqual(config.repository_pass_var, "REPOSITORY_PASSWORD")

    @mock.patch("semantic_release.settings.getcwd", return_value=temp_dir)
    def test_toml_override(self, mock_getcwd):
        # create temporary toml config file
        dummy_conf_path = os.path.join(temp_dir, "pyproject.toml")
        os.makedirs(os.path.dirname(dummy_conf_path), exist_ok=True)
        toml_conf_content = """
[tool.foo]
version_source = "commit"
[tool.semantic_release]
upload_to_repository = false
version_source = "tag"
"""
        with open(dummy_conf_path, "w") as dummy_conf_file:
            dummy_conf_file.write(toml_conf_content)

        config = Config.from_files()
        mock_getcwd.assert_called_once_with()
        self.assertEqual(config.hvcs, "github")
        self.assertEqual(config.upload_to_repository, False)
        self.assertEqual(config.version_source, "tag")

        # delete temporary toml config file
        os.remove(dummy_conf_path)

    @mock.patch("semantic_release.settings.logger.warning")
    @mock.patch("semantic_release.settings.getcwd", return_value=temp_dir)
    def test_no_raise_toml_error(self, mock_getcwd, mock_warning):
        # create temporary toml config file
        dummy_conf_path = os.path.join(temp_dir, "pyproject.toml")
        bad_toml_conf_content = """\
        TITLE OF BAD TOML
        [section]
        key = # BAD BECAUSE NO VALUE
        """
        os.makedirs(os.path.dirname(dummy_conf_path), exist_ok=True)

        with open(dummy_conf_path, "w") as dummy_conf_file:
            dummy_conf_file.write(bad_toml_conf_content)

        _ = Config.from_files()
        mock_getcwd.assert_called_once_with()
        mock_warning.assert_called_once_with(
            'Could not decode pyproject.toml: Invalid key "TITLE OF BAD TOML" at line 1 col 25'
        )
        # delete temporary toml config file
        os.remove(dummy_conf_path)

    @mock.patch("semantic_release.settings.getcwd", return_value=temp_dir)
    def test_toml_no_psr_section(self, mock_getcwd):
        # create temporary toml config file
        dummy_conf_path = os.path.join(temp_dir, "pyproject.toml")
        toml_conf_content = dedent(
            """
            [tool.foo]
            bar = "baz"
            """
        )
        os.makedirs(os.path.dirname(dummy_conf_path), exist_ok=True)

        with open(dummy_conf_path, "w") as dummy_conf_file:
            dummy_conf_file.write(toml_conf_content)

        config = Config.from_files()
        mock_getcwd.assert_called_once_with()
        self.assertEqual(config.hvcs, "github")
        # delete temporary toml config file
        os.remove(dummy_conf_path)

    def test_current_commit_parser_should_raise_error_if_parser_module_do_not_exist(
        self,
    ):
        with pytest.raises(ImproperConfigurationError):
            config = Config.from_files(commit_parser="nonexistent.parser")
            get_commit_parser(config)

    def test_current_commit_parser_should_raise_error_if_parser_do_not_exist(self):
        with pytest.raises(ImproperConfigurationError):
            config = Config.from_files(commit_parser="semantic_release.not_a_parser")
            get_commit_parser(config)

    @pytest.mark.xfail(
        reason="The commit parser needs rework, to no longer use lambdas"
    )
    def test_current_commit_parser_should_return_correct_parser(self):
        config = Config.from_files()
        self.assertEqual(get_commit_parser(config), parser_angular.parse_commit_message)
