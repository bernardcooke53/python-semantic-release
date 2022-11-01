from __future__ import annotations

import logging
import os
import platform
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional, Tuple, Union

import twine.utils
from git import Repo
from jinja2 import Environment
from pydantic import BaseModel
from twine.exceptions import TwineException
from twine.settings import Settings as TwineSettings
from typing_extensions import Literal

from semantic_release.changelog import environment
from semantic_release.cli.masking_filter import MaskingFilter
from semantic_release.commit_parser import (
    AngularCommitParser,
    CommitParser,
    EmojiCommitParser,
    ScipyCommitParser,
    TagCommitParser,
)
from semantic_release.const import COMMIT_MESSAGE, SEMVER_REGEX
from semantic_release.errors import InvalidConfiguration, NotAReleaseBranch
from semantic_release.helpers import dynamic_import
from semantic_release.hvcs import Gitea, Github, Gitlab, HvcsBase
from semantic_release.version import VersionTranslator
from semantic_release.version.declaration import (
    PatternVersionDeclaration,
    TomlVersionDeclaration,
    VersionDeclarationABC,
)

log = logging.getLogger(__name__)


class HvcsClient(str, Enum):
    GITHUB = "github"
    GITLAB = "gitlab"
    GITEA = "gitea"


class EnvConfigVar(BaseModel):
    env: str
    default: Optional[str] = None
    default_env: Optional[str] = None

    def getvalue(self) -> Optional[str]:
        return os.getenv(self.env, os.getenv(self.default_env or "", self.default))


MaybeFromEnv = Union[EnvConfigVar, str]


class ChangelogEnvironmentConfig(BaseModel):
    block_start_string: str = "{%"
    block_end_string: str = "%}"
    variable_start_string: str = "{{"
    variable_end_string: str = "}}"
    comment_start_string: str = "{#"
    comment_end_string: str = "#}"
    line_statement_prefix: Optional[str] = None
    line_comment_prefix: Optional[str] = None
    trim_blocks: bool = False
    lstrip_blocks: bool = False
    newline_sequence: Literal["\n", "\r", "\r\n"] = "\n"
    keep_trailing_newline: bool = False
    extensions: Tuple[str, ...] = ()
    autoescape: Union[bool, str] = True


class ChangelogConfig(BaseModel):
    template_dir: str = "templates"
    default_output_file: str = "CHANGELOG.md"
    environment: ChangelogEnvironmentConfig = ChangelogEnvironmentConfig()


class BranchConfig(BaseModel):
    match: str = "(main|master)"
    prerelease_token = "rc"
    prerelease: bool = False


class RemoteConfig(BaseModel):
    name: str = "origin"
    token_var: Optional[str] = None
    url: Optional[MaybeFromEnv] = None
    type: HvcsClient = HvcsClient.GITHUB
    domain: Optional[str] = None
    api_domain: Optional[str] = None
    ignore_token_for_push: bool = False


class UploadConfig(BaseModel):
    dist_glob_patterns: Tuple[str, ...] = ("dist/*",)
    pypi_token: MaybeFromEnv = EnvConfigVar(env="PYPI_TOKEN")
    upload_to_repository: bool = True
    upload_to_release: bool = True
    # https://twine.readthedocs.io/en/stable/
    sign: bool = False
    sign_with: str = "gpg"
    identity: MaybeFromEnv = EnvConfigVar(env="GPG_IDENTITIY")
    # https://twine.readthedocs.io/en/stable/#environment-variables
    # NOTE: this is breaking, as it will no longer check PYPI_USERNAME
    username: MaybeFromEnv = EnvConfigVar(
        env="REPOSITORY_USERNAME", default_env="TWINE_USERNAME"
    )
    # NOTE: this is breaking, as it will no longer check PYPI_PASSWORD or PYPI_TOKEN
    password: MaybeFromEnv = EnvConfigVar(
        env="REPOSITORY_PASSWORD", default_env="TWINE_PASSWORD"
    )
    non_interactive: MaybeFromEnv = EnvConfigVar(
        env="TWINE_NON_INTERACTIVE", default="true"
    )
    comment: Optional[str] = None
    config_file: str = twine.utils.DEFAULT_CONFIG_FILE
    skip_existing: bool = False
    cacert: MaybeFromEnv = EnvConfigVar(env="TWINE_CERT")
    client_cert: MaybeFromEnv = EnvConfigVar(env="TWINE_CLIENT_CERT")
    repository_name: str = "pypi"
    repository_url: MaybeFromEnv = EnvConfigVar(
        env="REPOSITORY_URL", default_env="TWINE_REPOSITORY_URL"
    )
    verbose: bool = False
    disable_progress_bar: bool = False


_PY = "py" if platform.system() == "Windows" else "python"


class RawConfig(BaseModel):
    logging_use_named_masks: bool = False
    tag_format: str = "v{version}"
    commit_parser: str = "angular"
    commit_message: str = COMMIT_MESSAGE
    build_command: str = f"{_PY} setup.py sdist bdist_wheel"
    version_toml: Optional[Tuple[str, ...]] = None
    version_variables: Optional[Tuple[str, ...]] = None
    major_on_zero: bool = True
    assets: Tuple[str, ...] = ()
    # It's up to the parser_options() method to validate these
    commit_parser_options: Dict[str, Any] = {
        "allowed_tags": [
            "build",
            "chore",
            "ci",
            "docs",
            "feat",
            "fix",
            "perf",
            "style",
            "refactor",
            "test",
        ],
        "minor_tags": ["feat"],
        "patch_tags": ["fix", "perf"],
    }
    changelog: ChangelogConfig = ChangelogConfig()
    branches: Dict[str, BranchConfig] = {"main": BranchConfig()}
    remote: RemoteConfig = RemoteConfig()
    upload: UploadConfig = UploadConfig()


@dataclass
class GlobalCommandLineOptions:
    """
    A dataclass to hold all the command line options that
    should be set in the RuntimeContext
    """

    noop: bool = False


######
# RuntimeContext
######
# This is what we want to attach to `click.Context.obj`
# There are currently no defaults here - this is on purpose,
# the defaults should be specified and handled by `RawConfig`.
# When this is constructed we should know exactly what the user
# wants
def _recursive_getattr(obj: Any, path: str) -> Any:
    """
    Used to find nested parts of RuntimeContext which
    might contain sensitive data. Returns None if an attribute
    is missing
    """
    out = obj
    for part in path.split("."):
        out = getattr(out, part, None)
    return out


_known_commit_parsers = {
    "angular": AngularCommitParser,
    "emoji": EmojiCommitParser,
    "scipy": ScipyCommitParser,
    "tag": TagCommitParser,
}

_known_hvcs = {
    HvcsClient.GITHUB: Github,
    HvcsClient.GITLAB: Gitlab,
    HvcsClient.GITEA: Gitea,
}


@dataclass
class RuntimeContext:
    _mask_attrs_: ClassVar[List[str]] = [
        "hvcs_client.token",
        "twine_settings.password",
        "twine_settings.cacert",
        "twine_settings.client_cert",
    ]

    repo: Repo
    commit_parser: CommitParser
    version_translator: VersionTranslator
    major_on_zero: bool
    prerelease: bool
    assets: Tuple[str, ...]
    commit_message: str
    version_declarations: Tuple[VersionDeclarationABC, ...]
    hvcs_client: HvcsBase
    ignore_token_for_push: bool
    template_environment: Environment
    template_dir: str
    default_changelog_output_file: str
    build_command: str
    twine_settings: Optional[TwineSettings]
    dist_glob_patterns: Tuple[str, ...]
    upload_to_repository: bool
    upload_to_release: bool
    global_cli_options: GlobalCommandLineOptions
    # This way the filter can be passed around if needed, so that another function
    # can accept the filter as an argument and call
    masker: MaskingFilter

    @staticmethod
    def resolve_from_env(param: Optional[MaybeFromEnv]) -> Optional[str]:
        if isinstance(param, EnvConfigVar):
            return param.getvalue()
        return param

    @staticmethod
    def select_branch_options(
        choices: Dict[str, BranchConfig], active_branch: str
    ) -> BranchConfig:
        for group, options in choices.items():
            if re.match(options.match, active_branch):
                log.debug(
                    "Using group %r options, as %r matches %r",
                    group,
                    options.match,
                    active_branch,
                )
                return options
            log.debug(
                "Rejecting group %r as %r doesn't match %r",
                group,
                options.match,
                active_branch,
            )
        raise NotAReleaseBranch(
            f"branch {active_branch!r} isn't in any release groups; no release will be made"
        )

    @classmethod
    def make_twine_settings(cls, upload_config: UploadConfig) -> TwineSettings:
        settings = TwineSettings(
            sign=upload_config.sign,
            sign_with=upload_config.sign_with,
            identity=cls.resolve_from_env(upload_config.identity),
            username=cls.resolve_from_env(upload_config.username),
            password=cls.resolve_from_env(upload_config.password),
            non_interactive=cls.resolve_from_env(upload_config.non_interactive),
            comment=upload_config.comment,
            config_file=upload_config.config_file,
            skip_existing=upload_config.skip_existing,
            cacert=cls.resolve_from_env(upload_config.cacert),
            client_cert=cls.resolve_from_env(upload_config.client_cert),
            repository_name=upload_config.repository_name,
            repository_url=cls.resolve_from_env(upload_config.repository_url),
            verbose=(
                upload_config.verbose
                or logging.getLogger("semantic_release").getEffectiveLevel()
                <= logging.INFO
            ),
            disable_progress_bar=upload_config.disable_progress_bar,
        )
        try:
            # Twine settings are lazy, so we trigger validation errors now if there
            # are any
            settings.username
            settings.password
            settings.config_file
        except TwineException as err:
            log.warning(
                    "TwineException: uploading to repositories will be unavailable (message: %r)",
                str(err),
            )
            return None

    def apply_log_masking(self, masker: MaskingFilter) -> MaskingFilter:
        for attr in self._mask_attrs_:
            masker.add_mask_for(str(_recursive_getattr(self, attr)), f"context.{attr}")
            masker.add_mask_for(repr(_recursive_getattr(self, attr)), f"context.{attr}")
        return masker

    @classmethod
    def from_raw_config(
        cls, raw: RawConfig, repo: Repo, global_cli_options: GlobalCommandLineOptions
    ) -> RuntimeContext:
        ##
        # credentials masking for logging
        masker = MaskingFilter(_use_named_masks=raw.logging_use_named_masks)
        # branch-specific configuration
        branch_config = cls.select_branch_options(raw.branches, repo.active_branch.name)
        # commit_parser
        commit_parser_cls = (
            _known_commit_parsers[raw.commit_parser]
            if raw.commit_parser in _known_commit_parsers
            else dynamic_import(raw.commit_parser)
        )

        commit_parser = commit_parser_cls(
            options=commit_parser_cls.parser_options(  # type: ignore
                **raw.commit_parser_options
            )
        )
        version_declarations: List[VersionDeclarationABC] = []
        for decl in () if raw.version_toml is None else raw.version_toml:
            try:
                path, search_text = decl.split(":", maxsplit=1)
                # VersionDeclarationABC handles path existence check
                vd = TomlVersionDeclaration(path, search_text)
            except ValueError as exc:
                log.error("Invalid TOML declaration %r", decl, exc_info=True)
                raise InvalidConfiguration(
                    f"Invalid TOML declaration {decl!r}"
                ) from exc

            version_declarations.append(vd)

        for decl in () if raw.version_variables is None else raw.version_variables:
            try:
                path, variable = decl.split(":", maxsplit=1)
                # VersionDeclarationABC handles path existence check
                search_text = rf"(?x){variable}\s*(:=|[:=])\s*(?P<quote>['\"]){SEMVER_REGEX.pattern}(?P=quote)"
                pd = PatternVersionDeclaration(path, search_text)
            except ValueError as exc:
                log.error("Invalid variable declaration %r", decl, exc_info=True)
                raise InvalidConfiguration(
                    f"Invalid variable declaration {decl!r}"
                ) from exc

            version_declarations.append(pd)

        # TODO: raw.version_pattern - do we format in SEMVER_REGEX?

        # hvcs_client
        hvcs_client_cls = _known_hvcs[raw.remote.type]
        raw_remote_url = raw.remote.url
        resolved_remote_url = cls.resolve_from_env(raw_remote_url)
        remote_url = (
            resolved_remote_url
            if resolved_remote_url is not None
            else repo.remote(raw.remote.name).url
        )

        # TODO: maybe the env-handling here is duplicating
        # the one in hvcs client & could be removed
        hvcs_client = hvcs_client_cls(
            remote_url=remote_url,
            hvcs_domain=cls.resolve_from_env(raw.remote.domain),
            hvcs_api_domain=cls.resolve_from_env(raw.remote.api_domain),
            token_var=raw.remote.token_var or "",
        )

        template_environment = environment(
            template_dir=raw.changelog.template_dir, **raw.changelog.environment.dict()
        )

        # version_translator
        version_translator = VersionTranslator(
            tag_format=raw.tag_format, prerelease_token=branch_config.prerelease_token
        )

        try:
            twine_settings = cls.make_twine_settings(raw.upload)
        except TwineException as err:
            log.warning(str(err))
            log.warning("uploading to repositories will be unavailable", exc_info=True)

        self = cls(
            repo=repo,
            commit_parser=commit_parser,
            version_translator=version_translator,
            major_on_zero=raw.major_on_zero,
            build_command=raw.build_command,
            version_declarations=tuple(version_declarations),
            hvcs_client=hvcs_client,
            assets=raw.assets,
            commit_message=raw.commit_message,
            prerelease=branch_config.prerelease,
            ignore_token_for_push=raw.remote.ignore_token_for_push,
            template_dir=raw.changelog.template_dir,
            template_environment=template_environment,
            default_changelog_output_file=raw.changelog.default_output_file,
            twine_settings=twine_settings,
            dist_glob_patterns=raw.upload.dist_glob_patterns,
            upload_to_repository=raw.upload.upload_to_repository,
            upload_to_release=raw.upload.upload_to_release,
            global_cli_options=global_cli_options,
            masker=masker,
        )
        # credential masker
        self.apply_log_masking(self.masker)

        return self
