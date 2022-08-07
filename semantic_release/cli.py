"""CLI
"""
import logging
import os
import sys
from functools import update_wrapper
from pathlib import Path
from typing import Optional

import click
import click_log
from invoke import run

from semantic_release import ci_checks
from semantic_release.errors import GitError, ImproperConfigurationError

from .changelog import markdown_changelog
from .dist import build_dists, remove_dists, should_build, should_remove_dist
from .history import (
    evaluate_version_bump,
    get_current_release_version,
    get_current_version,
    get_new_version,
    get_previous_release_version,
    get_previous_version,
    set_new_version,
)
from .history.logs import generate_changelog
from .hvcs import (
    check_build_status as do_check_build_status,
    check_token,
    get_domain,
    get_token,
    post_changelog,
    upload_to_release as do_upload_to_release,
)
from .repository import ArtifactRepo
from .settings import Config, get_commit_parser
from .vcs_helpers import (
    checkout,
    commit_new_version,
    get_current_head_hash,
    get_repository_owner_and_name,
    push_new_version,
    tag_new_version,
    update_additional_files,
    update_changelog_file,
)

logger = logging.getLogger("semantic_release")
logger.setLevel(logging.DEBUG)

TOKEN_VARS = [
    "github_token_var",
    "gitlab_token_var",
    "pypi_pass_var",
    "pypi_token_var",
    "pypi_user_var",
    "repository_user_var",
    "repository_pass_var",
]

COMMON_OPTIONS = [
    click_log.simple_verbosity_option(logger),
    click.option(
        "--major", "force_level", flag_value="major", help="Force major version."
    ),
    click.option(
        "--minor", "force_level", flag_value="minor", help="Force minor version."
    ),
    click.option(
        "--patch", "force_level", flag_value="patch", help="Force patch version."
    ),
    click.option("--prerelease", is_flag=True, help="Creates a prerelease version."),
    click.option(
        "--prerelease-patch/--no-prerelease-patch",
        "prerelease_patch",
        default=True,
        show_default=True,
        help="whether or not prerelease always gets at least a patch-level bump",
    ),
    click.option("--post", is_flag=True, help="Post changelog."),
    click.option("--retry", is_flag=True, help="Retry the same release, do not bump."),
    click.option(
        "--noop",
        is_flag=True,
        help="No-operations mode, finds the new version number without changing it.",
    ),
    click.option(
        "--define",
        "-D",
        multiple=True,
        help='setting="value", override a configuration value.',
    ),
]


def common_options(func):
    """
    Decorator that adds all the options in COMMON_OPTIONS
    """
    original_func = func
    for option in reversed(COMMON_OPTIONS):
        func = option(func)
    return update_wrapper(wrapper=func, wrapped=original_func)


def print_version(
    config: Config,
    *,
    current=False,
    force_level=None,
    prerelease=False,
    prerelease_patch=True,
    # version_source: str = "commit",
    # patch_without_tag: bool = False,
    # major_on_zero: bool = True,
    # check_build_status: bool = False,
    **kwargs,
):
    """
    Print the current or new version to standard output.
    """
    try:
        current_version = get_current_version(
            config.prerelease_tag,
            config.version_source,
            config.version_variable,
            config.version_pattern,
            config.version_toml,
        )
        current_release_version = get_current_release_version(
            config.version_source,
            config.prerelease_tag,
            config.tag_format,
            config.commit_subject,
        )
        logger.info(
            f"Current version: {current_version}, Current release version: {current_release_version}"
        )
    except GitError as e:
        print(str(e), file=sys.stderr)
        return False
    if current:
        print(current_version, end="")
        return True

    # Find what the new version number should be
    level_bump = evaluate_version_bump(
        current_version,
        config.tag_format,
        config.patch_without_tag,
        config.major_on_zero,
        force_level,
    )
    new_version = get_new_version(
        current_version,
        current_release_version,
        level_bump,
        prerelease,
        prerelease_patch,
    )
    if should_bump_version(
        current_version=current_version,
        new_version=new_version,
        current_release_version=current_release_version,
        prerelease=prerelease,
        check_build_status=config.check_build_status,
    ):
        print(new_version, end="")
        return True

    print("No release will be made.", file=sys.stderr)
    return False


def version(
    config: Config,
    *,
    # version_source: str = "commit",
    retry=False,
    noop=False,
    force_level=None,
    # patch_without_tag: bool = False,
    # major_on_zero: bool = True,
    # check_build_status: bool = False,
    prerelease=False,
    prerelease_patch=True,
    # tag_commit: bool = True,
    # TODO: Revisit default for this
    # commit_version_number: bool = True,
    **kwargs,
) -> bool:
    """
    Detect the new version according to git log and semver.

    Write the new version number and commit it, unless the noop option is True.
    """
    if retry:
        logger.info("Retrying publication of the same version")
    else:
        logger.info("Creating new version")

    # Get the current version number
    try:
        current_version = get_current_version(
            config.prerelease_tag,
            config.version_source,
            config.version_variable,
            config.version_pattern,
            config.version_toml,
        )
        current_release_version = get_current_release_version(
            config.version_source,
            config.prerelease_tag,
            config.tag_format,
            config.commit_subject,
        )
        logger.info(
            f"Current version: {current_version}, Current release version: {current_release_version}"
        )
    except GitError as e:
        logger.error(str(e))
        return False

    commit_parser = get_commit_parser(config)
    # Find what the new version number should be
    level_bump = evaluate_version_bump(
        commit_parser,
        current_version,
        config.tag_format,
        config.patch_without_tag,
        config.major_on_zero,
        force_level,
    )
    new_version = get_new_version(
        current_version,
        current_release_version,
        level_bump,
        prerelease,
        prerelease_patch,
    )
    if not should_bump_version(
        current_version=current_version,
        new_version=new_version,
        current_release_version=current_release_version,
        prerelease=prerelease,
        check_build_status=config.check_build_status,
        hvcs=config.hvcs,
        noop=noop
    ):
        return False

    if retry:
        # No need to make changes to the repo, we're just retrying.
        return True

    # Bump the version
    bump_version(
        new_version,
        level_bump,
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
    return True


def should_bump_version(
    *,
    current_version,
    current_release_version,
    new_version,
    prerelease,
    hvcs,
    check_build_status: bool = False,
    retry=False,
    noop=False,
):
    match_version = current_version if prerelease else current_release_version

    """Test whether the version should be bumped."""
    if new_version == match_version and not retry:
        logger.info("No release will be made.")
        return False

    if noop:
        logger.warning(
            "No operation mode. Should have bumped "
            f"from {current_version} to {new_version}"
        )
        return False

    if check_build_status:
        logger.info("Checking build status...")
        owner, name = get_repository_owner_and_name()
        if not do_check_build_status(hvcs, owner, name, get_current_head_hash()):
            logger.warning("The build failed, cancelling the release")
            return False
        logger.info("The build was a success, continuing the release")

    return True


def bump_version(
    new_version: str,
    level_bump: str,
    prerelease_tag: str,
    commit_subject: str,
    commit_message: str,
    version_variable: Optional[str],
    version_pattern: Optional[str],
    version_toml: Optional[str],
    tag_format: str,
    commit_author: Optional[str] = None,
    tag_commit: bool = True,
    commit_version_number: Optional[bool] = None,
    version_source: Optional[str] = None,
):
    """
    Set the version to the given `new_version`.

    Edit in the source code, commit and create a git tag.
    """
    logger.info(f"Bumping with a {level_bump} version to {new_version}")
    if version_source == "tag_only":
        tag_new_version(tag_format, new_version)

        # we are done, no need for file changes if we are using
        # tags as version source
        return

    set_new_version(
        new_version, version_variable, version_pattern, version_toml, prerelease_tag
    )
    if commit_version_number or version_source == "commit":
        commit_new_version(
            new_version,
            version_variable,
            version_pattern,
            version_toml,
            prerelease_tag,
            commit_subject,
            commit_message,
            commit_author,
        )
    if version_source == "tag" or tag_commit:
        tag_new_version(tag_format, new_version)


def changelog(
    config: Config,
    *,
    unreleased: bool = False,
    noop: bool = False,
    post: bool = False,
    prerelease: bool = False,
    **kwargs,
):
    """
    Generate the changelog since the last release.

    :raises ImproperConfigurationError: if there is no current version
    """
    current_version = get_current_version(
        config.prerelease_tag,
        config.version_source,
        config.version_variable,
        config.version_pattern,
        config.version_toml,
    )
    if current_version is None:
        raise ImproperConfigurationError(
            "Unable to get the current version. "
            "Make sure semantic_release.version_variable "
            "is setup correctly"
        )

    previous_version = get_previous_version(
        current_version, config.prerelease_tag, config.tag_format
    )

    commit_parser = get_commit_parser(config)
    # Generate the changelog
    if unreleased:
        changelog = generate_changelog(commit_parser, current_version, None)
    else:
        changelog = generate_changelog(commit_parser, previous_version, current_version)

    owner, name = get_repository_owner_and_name()
    # print is used to keep the changelog on stdout, separate from log messages
    print(
        markdown_changelog(
            owner,
            name,
            current_version,
            changelog,
            config.changelog_sections,
            config.changelog_components,
            config.hvcs,
            config.hvcs_domain,
            header=False,
        )
    )

    # Post changelog to HVCS if enabled
    if not noop and post:
        # TODO: This is also a hack
        if config.hvcs == "github":
            token_var = config.github_token_var
        elif config.hvcs == "gitlab":
            token_var = config.gitlab_token_var
        elif config.hvcs == "gitea":
            token_var = config.gitea_token_var

        if check_token(config.hvcs, token_var):
            logger.info("Posting changelog to HVCS")
            # TODO: This is now broken for all but Github
            post_changelog(
                config.hvcs,
                owner,
                name,
                config.tag_format,
                current_version,
                markdown_changelog(
                    owner,
                    name,
                    current_version,
                    changelog,
                    config.changelog_sections,
                    config.changelog_components,
                    config.hvcs,
                    config.hvcs_domain,
                    header=False,
                ),
                token_var,
                hvcs_domain=config.hvcs_domain,
                hvcs_api_domain=config.hvcs_api_domain,
            )
        else:
            logger.error("Missing token: cannot post changelog to HVCS")


def publish(
    config: Config,
    *,
    retry: bool = False,
    noop: bool = False,
    prerelease: bool = False,
    prerelease_patch: bool = True,
    force_level: str = None,
    # branch: str = "master",
    # dist_path: str = "dist",
    # build_command: str = "python setup.py sdist bdist_wheel",
    # upload_to_release: bool = True,
    # patch_without_tag: bool = False,
    # version_source: str = "commit",
    # changelog_sections: str = "feature,fix,breaking,documentation,performance,:boom:,:sparkles:,:children_crossing:,:lipstick:,:iphone:,:egg:,:chart_with_upwards_trend:,:ambulance:,:lock:,:bug:,:zap:,:goal_net:,:alien:,:wheelchair:,:speech_balloon:,:mag:,:apple:,:penguin:,:checkered_flag:,:robot:,:green_apple:,Other",
    # pre_commit_command: Optional[str] = None,
    # changelog_file: str = "CHANGELOG.md",
    # changelog_placeholder: str = "<!--next-version-placeholder-->",
    # include_additional_files: str = "",
    # tag_commit: bool = True,
    # # TODO: revisit default for this
    # commit_version_number: bool = True,
    # major_on_zero: bool = True,
    # upload_to_repository: bool = True,
    # upload_to_pypi: bool = True,
    # remove_dist: bool = True,
    # repository: str = "pypi",
    # repository_url: Optional[str] = "None",
    # repository_user_var: str = "REPOSITORY_USERNAME",
    # repository_pass_var: str = "REPOSITORY_PASSWORD",
    # repository_url_var: str = "REPOSITORY_URL",
    # pypi_user_var: str = "PYPI_USERNAME",
    # pypi_pass_var: str = "PYPI_PASSWORD",
    # pypi_token_var: str = "PYPI_TOKEN",
    # dist_glob_patterns: str = "*",
    # upload_to_pypi_glob_patterns: str = "*",
    **kwargs,
):
    """Run the version task, then push to git and upload to an artifact repository / GitHub Releases."""
    current_version = get_current_version(
        config.prerelease_tag,
        config.version_source,
        config.version_variable,
        config.version_pattern,
        config.version_toml,
    )
    current_release_version = get_current_release_version(
        config.version_source,
        config.prerelease_tag,
        config.tag_format,
        config.commit_subject,
    )
    logger.info(
        f"Current version: {current_version}, Current release version: {current_release_version}"
    )

    # TODO: remove
    commit_parser = get_commit_parser(config)
    verbose = logger.isEnabledFor(logging.DEBUG)
    if retry:
        logger.info("Retry is on")
        # The "new" version will actually be the current version, and the
        # "current" version will be the previous version.
        level_bump = None
        new_version = current_version
        current_version = get_previous_release_version(
            current_version, config.prerelease_tag, config.commit_subject
        )
    else:
        # Calculate the new version
        level_bump = evaluate_version_bump(
            commit_parser,
            current_release_version,
            config.tag_format,
            patch_without_tag=config.patch_without_tag,
            major_on_zero=config.major_on_zero,
            force=force_level,
        )
        new_version = get_new_version(
            current_version,
            current_release_version,
            level_bump,
            config.prerelease_tag,
            prerelease,
            prerelease_patch,
        )

    owner, name = get_repository_owner_and_name()

    logger.debug(f"Running publish on branch {config.branch}")
    ci_checks.check(config.branch)
    checkout(config.branch)

    if should_bump_version(
        current_version=current_version,
        new_version=new_version,
        current_release_version=current_release_version,
        prerelease=prerelease,
        hvcs=config.hvcs,
        check_build_status=config.check_build_status,
        retry=retry,
        noop=noop,
    ):
        changelog = generate_changelog(commit_parser, current_version)
        changelog_md = markdown_changelog(
            owner,
            name,
            new_version,
            changelog,
            changelog_sections=config.changelog_sections,
            changelog_components=config.changelog_components,
            hvcs=config.hvcs,
            hvcs_domain=config.hvcs_domain,
            header=False,
            previous_version=current_version,
        )

        if config.pre_commit_command:
            logger.info("Running pre-commit command")
            logger.debug(f"Running {config.pre_commit_command}")
            run(config.pre_commit_command)

        if not retry:
            update_changelog_file(
                new_version,
                changelog_md,
                config.changelog_file,
                config.changelog_placeholder,
            )
            update_additional_files(config.include_additional_files)
            bump_version(
                new_version,
                level_bump,
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
        # A new version was released
        logger.info("Pushing new version")
        # TODO: This is also a hack
        if config.hvcs == "github":
            token_var = config.github_token_var
        elif config.hvcs == "gitlab":
            token_var = config.gitlab_token_var
        elif config.hvcs == "gitea":
            token_var = config.gitea_token_var

        push_new_version(
            config.hvcs,
            config.ignore_token_for_push,
            auth_token=get_token(config.hvcs, token_var),
            owner=owner,
            name=name,
            branch=config.branch,
            domain=get_domain(config.hvcs, config.hvcs_domain),
        )

        if should_build(
            config.upload_to_repository,
            config.upload_to_pypi,
            config.upload_to_release,
            config.build_command,
        ):
            # We need to run the command to build wheels for releasing
            logger.info("Building distributions")
            if config.remove_dist:
                # Remove old distributions before building
                remove_dists(config.dist_path)
            build_dists(config.build_command)

        # TODO: handle ~/.pypirc here - currently still in class
        if ArtifactRepo.upload_enabled(
            config.upload_to_repository, config.upload_to_pypi
        ):
            logger.info("Uploading to artifact Repository")
            ArtifactRepo(
                dist_path=Path(config.dist_path),
                repository_name=config.repository,
                repository_url=(
                    os.getenv(config.repository_url_var) or config.repository_url
                ),
                username=(
                    os.getenv(config.repository_user_var)
                    or os.getenv(config.pypi_user_var)
                ),
                password=(
                    os.getenv(config.repository_pass_var)
                    or os.getenv(config.pypi_pass_var)
                    or os.getenv(config.pypi_token_var)
                ),
                dist_glob_patterns=config.dist_glob_patterns
                or config.upload_to_pypi_glob_patterns,
            ).upload(noop=noop, verbose=verbose, skip_existing=retry)

        token_checked = check_token(config.hvcs, token_var)
        if token_checked:
            # Update changelog on HVCS
            logger.info("Posting changelog to HVCS")
            try:
                post_changelog(
                    config.hvcs,
                    owner,
                    name,
                    config.tag_format,
                    current_version,
                    changelog_md,
                    token_var,
                    hvcs_domain=config.hvcs_domain,
                    hvcs_api_domain=config.hvcs_api_domain,
                )
            except GitError:
                logger.error("Posting changelog failed")
        else:
            logger.warning("Missing token: cannot post changelog to HVCS")

        # Upload to GitHub Releases
        if config.upload_to_release:
            if token_checked:
                logger.info("Uploading to HVCS release")
                do_upload_to_release(
                    config.hvcs,
                    owner,
                    name,
                    config.tag_format,
                    new_version,
                    config.dist_path,
                    token_var,
                    config.hvcs_api_domain,
                )
                logger.info("Upload to HVCS is complete")
            else:
                logger.warning("Missing token: cannot upload to HVCS")

        # Remove distribution files as they are no longer needed
        if should_remove_dist(
            config.remove_dist,
            config.upload_to_repository,
            config.upload_to_pypi,
            config.upload_to_release,
            config.build_command,
        ):
            logger.info("Removing distribution files")
            remove_dists(config.dist_path)

        logger.info("Publish has finished")

    # else: Since version shows a message on failure, we do not need to print another.


def filter_output_for_secrets(config: Config, message: str):
    """Remove secrets from cli output."""
    output = message
    for token_var in TOKEN_VARS:
        secret_name = getattr(config, token_var)
        secret = os.environ.get(secret_name)
        if secret:
            output = output.replace(secret, f"${secret_name}")

    return output


def entry():
    # Move flags to after the command
    ARGS = sorted(sys.argv[1:], key=lambda x: 1 if x.startswith("--") else -1)

    if ARGS and not ARGS[0].startswith("print-"):
        # print-* command output should not be polluted with logging.
        click_log.basic_config()

    main(args=ARGS)


#
# Making the CLI commands.
# We have a level of indirection to the logical commands
# so we can successfully mock them during testing
#


@click.group()
@common_options
def main(**kwargs):
    logger.debug(f"Main args: {kwargs}")
    config, kwargs = Config.with_additional_kwargs(**kwargs)
    message = ""
    for token_var in TOKEN_VARS:
        secret_name = getattr(config, token_var)
        message += f'{secret_name}="{os.environ.get(secret_name)}",'
    logger.debug(f"Environment: {filter_output_for_secrets(config, message)}")

    obj = {
        key: getattr(config, key, kwargs.get(key))
        for key in (
            "check_build_status",
            "commit_subject",
            "commit_message",
            "commit_parser",
            "patch_without_tag",
            "major_on_zero",
            "upload_to_pypi",
            "upload_to_repository",
            "version_source",
            "no_git_tag",
        )
    }
    logger.debug(f"Main config: {obj}")


@main.command(name="publish", help=publish.__doc__)
@common_options
def cmd_publish(**kwargs):
    try:
        config, kwargs = Config.with_additional_kwargs(**kwargs)
        return publish(config, **kwargs)
    except Exception as error:
        logger.error(filter_output_for_secrets(config, str(error)))
        exit(1)


@main.command(name="changelog", help=changelog.__doc__)
@common_options
@click.option(
    "--unreleased/--released",
    help="Decides whether to show the released or unreleased changelog.",
)
def cmd_changelog(**kwargs):
    try:
        config, kwargs = Config.with_additional_kwargs(**kwargs)
        return changelog(config, **kwargs)
    except Exception as error:
        logger.error(filter_output_for_secrets(config, str(error)))
        exit(1)


@main.command(name="version", help=version.__doc__)
@common_options
def cmd_version(**kwargs):
    try:
        config, kwargs = Config.with_additional_kwargs(**kwargs)
        return version(config, **kwargs)
    except Exception as error:
        logger.error(filter_output_for_secrets(config, str(error)))
        exit(1)


@main.command(name="print-version", help=print_version.__doc__)
@common_options
@click.option(
    "--current/--next",
    default=False,
    help="Choose to output next version (default) or current one.",
)
def cmd_print_version(**kwargs):
    try:
        config, kwargs = Config.with_additional_kwargs(**kwargs)
        return print_version(config, **kwargs)
    except Exception as error:
        print(filter_output_for_secrets(config, str(error)), file=sys.stderr)
        exit(1)
