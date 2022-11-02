from __future__ import annotations

import logging
from queue import Queue
from typing import Iterable, List, Optional, Set, Tuple, Union

from git.objects.blob import Blob
from git.objects.commit import Commit
from git.objects.tag import TagObject
from git.objects.tree import Tree
from git.refs.tag import Tag
from git.repo.base import Repo

from semantic_release.commit_parser import (
    CommitParser,
    ParsedCommit,
    ParseResult,
    ParserOptions,
)
from semantic_release.enums import LevelBump
from semantic_release.version.translator import VersionTranslator
from semantic_release.version.version import Version

log = logging.getLogger(__name__)


def tags_and_versions(
    tags: Iterable[Tag], translator: VersionTranslator
) -> List[Tuple[Tag, Version]]:
    """
    Return a list of 2-tuples, where each element is a tuple (tag, version)
    from the tags in the Git repo and their corresponding `Version` according
    to `Version.from_tag`. The returned list is sorted according to semver
    ordering rules
    """
    return sorted(
        [(t, translator.from_tag(t.name)) for t in tags],
        reverse=True,
        key=lambda v: v[1],
    )


def _bfs_for_latest_version_in_history(
    merge_base: Union[Commit, TagObject, Blob, Tree],
    full_release_tags_and_versions: List[Tuple[Tag, Version]],
) -> Optional[Version]:
    """
    Run a breadth-first search through the given `merge_base`'s parents,
    looking for the most recent version corresponding to a commit in the
    `merge_base`'s parents' history. If no commits in the history correspond
    to a released version, return None
    """
    # Step 3. Latest full release version within the history of the current branch
    # Breadth-first search the merge-base and its parent commits for one which matches
    # the tag of the latest full release tag in history
    def bfs(visited: Set[Commit], q: "Queue[Commit]") -> Optional[Version]:
        if q.empty():
            return None

        node = q.get()
        if node in visited:
            return None

        for tag, version in full_release_tags_and_versions:
            log.debug(
                "checking if tag %r (%s) matches commit %s",
                tag.name,
                tag.commit.hexsha,
                node.hexsha,
            )
            if tag.commit == node:
                log.info(
                    "found latest version in branch history: %r (%s)",
                    str(version),
                    node.hexsha[:7],
                )
                return version
            log.debug("commit %s doesn't match any tags", node.hexsha)

        visited.add(node)
        for parent in node.parents:
            q.put(parent)

        return bfs(visited, q)

    q: Queue[Commit] = Queue()
    q.put(merge_base)
    return bfs(set(), q)


def _increment_version(
    latest_version: Version,
    latest_full_version: Version,
    latest_full_version_in_history: Version,
    level_bump: LevelBump,
    prerelease: bool,
    prerelease_token: str,
    major_on_zero: bool,
) -> Version:
    """
    Using the given versions, along with a given `level_bump`, increment to
    the next version according to whether or not this is a prerelease.

    `latest_version`, `latest_full_version` and `latest_full_version_in_history`
    can be the same, but aren't necessarily.

    `latest_version` is the most recent version released from this branch's history.
    `latest_full_version` is the most recent full release (i.e. not a prerelease)
    anywhere in the repository's history, including commits which aren't present on
    this branch.
    `latest_full_version_in_history`, correspondingly, is the latest full release which
    is in this branch's history.
    """

    log.debug(
        "_increment_version: %s", ", ".join(f"{k} = {v}" for k, v in locals().items())
    )
    if not major_on_zero and latest_version.major == 0:
        # if we are a 0.x.y release and have set `major_on_zero`,
        # breaking changes should increment the minor di
        # Correspondingly, we reduce the level that we increment the
        # version by.
        log.debug(
            "reducing version increment due to 0. version and major_on_zero=False"
        )

        level_bump = min(level_bump, LevelBump.MINOR)

    if prerelease:
        target_final_version = latest_full_version.finalize_version()
        diff_with_last_released_version = (
            latest_version - latest_full_version_in_history
        )
        log.debug(
            "diff_with_last_released_version: %s", diff_with_last_released_version
        )
        # 6a i) if the level_bump > the level bump introduced by any prerelease tag before
        # e.g. 1.2.4-rc.3 -> 1.3.0-rc.1
        if level_bump > diff_with_last_released_version:
            return target_final_version.bump(level_bump).to_prerelease(
                token=prerelease_token
            )

        # 6a ii) if level_bump <= the level bump introduced by prerelease tag
        return latest_version.to_prerelease(
            token=prerelease_token,
            revision=(
                1
                if latest_version.prerelease_token != prerelease_token
                else (latest_version.prerelease_revision or 0) + 1
            ),
        )

    # 6b. if not prerelease
    # NOTE: These can actually be condensed down to the single line
    # 6b. i) if there's been a prerelease
    if latest_version.is_prerelease:
        diff_with_last_released_version = (
            latest_version - latest_full_version_in_history
        )
        log.debug(
            "diff_with_last_released_version: %s", diff_with_last_released_version
        )
        if level_bump > diff_with_last_released_version:
            return latest_version.bump(level_bump).finalize_version()
        return latest_version.finalize_version()

    # 6b. ii) If there's been no prerelease
    return latest_version.bump(level_bump)


def next_version(
    repo: Repo,
    translator: VersionTranslator,
    commit_parser: CommitParser[ParseResult, ParserOptions],
    prerelease: bool = False,
    major_on_zero: bool = True,
) -> Version:
    # Step 1. All tags, sorted descending by semver ordering rules
    all_git_tags_as_versions = tags_and_versions(repo.tags, translator)
    all_full_release_tags_and_versions = [
        (t, v) for t, v in all_git_tags_as_versions if not v.is_prerelease
    ]
    log.debug("Found %s previous tags", len(all_git_tags_as_versions))

    # Default initial version of 0.0.0
    latest_full_release_tag, latest_full_release_version = next(
        iter(all_full_release_tags_and_versions),
        (None, translator.from_string("0.0.0")),
    )
    if latest_full_release_tag is None:
        # Workaround - we can safely scan the extra commits on this
        # branch if it's never been released, but we have no other
        # guarantees that other branches exist
        log.info("No full releases have been made yet")
        merge_bases = repo.merge_base(repo.active_branch, repo.active_branch)
    else:
        # Note the merge_base might be on our current branch, it's not
        # necessarily the merge base of the current branch with `main`
        log.info(
            "The last full release was %s, tagged as %r",
            latest_full_release_version,
            latest_full_release_tag,
        )
        merge_bases = repo.merge_base(latest_full_release_tag.name, repo.active_branch)
    if len(merge_bases) > 1:
        raise NotImplementedError(
            "This branch has more than one merge-base with the "
            "latest version, which is not yet supported"
        )
    merge_base = merge_bases[0]
    if merge_base is None:
        str_tag_name = (
            "None" if latest_full_release_tag is None else latest_full_release_tag.name
        )
        raise ValueError(
            f"The merge_base found by merge_base({str_tag_name}, {repo.active_branch}) is None"
        )

    latest_full_version_in_history = _bfs_for_latest_version_in_history(
        merge_base=merge_base,
        full_release_tags_and_versions=all_full_release_tags_and_versions,
    )
    log.info(
        "The last full version in this branch's history was %s",
        latest_full_version_in_history,
    )

    commits_since_last_full_release = (
        repo.iter_commits()
        if latest_full_version_in_history is None
        else repo.iter_commits(f"{latest_full_version_in_history.as_tag()}...")
    )

    # Step 4. Parse each commit since the last release and find any tags that have
    # been added since then.
    parsed_levels: Set[LevelBump] = set()
    latest_version = latest_full_version_in_history or Version(
        0, 0, 0, prerelease_token=translator.prerelease_token
    )

    # N.B. these should be sorted so long as we iterate the commits in reverse order
    for commit in commits_since_last_full_release:
        parse_result = commit_parser.parse(commit)
        if isinstance(parse_result, ParsedCommit):
            log.debug(
                "adding %s to the levels identified in commits_since_last_full_release",
                parse_result.bump,
            )
            parsed_levels.add(parse_result.bump)

        # We only include pre-releases here if doing a prerelease.
        # If it's not a prerelease, we need to include commits back
        # to the last full version in consideration for what kind of
        # bump to produce. However if we're doing a prerelease, we can
        # include prereleases here to potentially consider a smaller portion
        # of history (from a prerelease since the last full release, onwards)

        # Note that a side-effect of this is, if at some point the configuration
        # for a particular branch pattern changes w.r.t. prerelease=True/False,
        # the new kind of version will be produced from the commits already
        # included in a prerelease since the last full release on the branch
        for tag, version in (
            (tag, version)
            for tag, version in all_git_tags_as_versions
            if prerelease or not version.is_prerelease
        ):
            log.debug(
                "testing if tag %r (%s) matches commit %s",
                tag.name,
                tag.commit.hexsha,
                commit.hexsha,
            )
            if tag.commit == commit:
                latest_version = version
                log.debug(
                    "tag %r (%s) matches commit %s. the latest version is %s",
                    tag.name,
                    tag.commit.hexsha,
                    commit.hexsha,
                    latest_version,
                )
                break
        else:
            # If we haven't found the latest prerelease on the branch,
            # keep the outer loop going to look for it
            log.debug("no tags correspond to commit %s", commit.hexsha)
            continue
        # If we found it in the inner loop, break the outer loop too
        break

    log.debug(
        "parsed the following distinct levels from the commits since the last release: %s",
        parsed_levels,
    )
    level_bump = max(parsed_levels, default=LevelBump.NO_RELEASE)
    log.info("The type of release triggered is: %s", level_bump)
    if level_bump is LevelBump.NO_RELEASE:
        log.info("No release will be made")
        return latest_version

    return _increment_version(
        latest_version=latest_version,
        latest_full_version=latest_full_release_version,
        latest_full_version_in_history=(
            latest_full_version_in_history
            or Version.parse("0.0.0", prerelease_token=translator.prerelease_token)
        ),
        level_bump=level_bump,
        prerelease=prerelease,
        prerelease_token=translator.prerelease_token,
        major_on_zero=major_on_zero,
    )
