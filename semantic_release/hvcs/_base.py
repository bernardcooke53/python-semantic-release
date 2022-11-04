"""
Common functionality and interface for interacting with Git remote VCS
"""
from __future__ import annotations

import logging
import os
import warnings
from functools import wraps
from typing import Any, Callable, Optional, Tuple

from semantic_release.helpers import parse_git_url
from semantic_release.hvcs.token_auth import TokenAuth
from semantic_release.hvcs.util import build_requests_session

logger = logging.getLogger(__name__)


def _not_supported(method: Callable[..., Any]) -> Callable[..., bool]:
    @wraps(method)
    def _methodwrapper(self: HvcsBase, *a: Any, **kw: Any) -> bool:
        warnings.warn(
            f"{method.__name__} is not supported by {type(self).__qualname__}",
            stacklevel=2,
        )
        warnings.warn
        return True

    return _methodwrapper


# pylint: disable=unused-argument
class HvcsBase:
    """
    Interface for subclasses interacting with a remote VCS

    Methods which have a base implementation are implemented here

    Methods which aren't mandatory but should indicate a lack of support gracefully
    (i.e. without raising an exception) are decorated with @_not_supported, and can
    be overridden to provide an implementation in subclasses.
    This is more straightforward than checking for NotImplemented around every method
    call.
    """

    def __init__(
        self,
        remote_url: str,
        hvcs_domain: Optional[str] = None,
        hvcs_api_domain: Optional[str] = None,
        token_var: str = "",
    ) -> None:
        self.hvcs_domain = hvcs_domain
        self.hvcs_api_domain = hvcs_api_domain
        self.token = os.getenv(token_var)
        auth = None if not self.token else TokenAuth(self.token)
        self._remote_url = remote_url
        self.session = build_requests_session(auth=auth)

    def _get_repository_owner_and_name(self) -> Tuple[str, str]:
        """
        Parse the repository's remote url to identify the repository
        owner and name
        """
        parsed_git_url = parse_git_url(self._remote_url)
        return parsed_git_url.namespace, parsed_git_url.repo_name

    @property
    def repo_name(self) -> str:
        _, _name = self._get_repository_owner_and_name()
        return _name

    @property
    def owner(self) -> str:
        _owner, _ = self._get_repository_owner_and_name()
        return _owner

    @_not_supported
    def compare_url(self, from_rev: str, to_rev: str) -> str:
        """
        Get the comparison link between two version tags.
        :param from_rev: The older version to compare. Can be a commit sha, tag or branch name.
        :param to_rev: The newer version to compare. Can be a commit sha, tag or branch name.
        :return: Link to view a comparison between the two versions.
        """

    @_not_supported
    def check_build_status(self, ref: str) -> bool:
        """
        Check the status of a build at `ref` in a remote VCS that reports build
        statuses, such as GitHub Actions or GitLab CI
        """

    @_not_supported
    def upload_dists(self, tag: str, dist_glob: str) -> int:
        """
        Upload built distributions to a release on a remote VCS that
        supports such uploads
        """

    @_not_supported
    def create_release(
        self, tag: str, changelog: str, prerelease: bool = False
    ) -> bool:
        """
        Create a release in a remote VCS, if supported
        """

    @_not_supported
    def get_release_id_by_tag(self, tag: str) -> Optional[int]:
        """
        Given a Git tag, return the ID (as the remote VCS defines it) of a corrsponding
        release in the remove VCS, if supported
        """

    @_not_supported
    def edit_release_changelog(self, release_id: int, changelog: str) -> bool:
        """
        Edit the changelog associated with a release, if supported
        """

    @_not_supported
    def create_or_update_release(
        self, tag: str, changelog: str, prerelease: bool = False
    ) -> bool:
        """
        Create or update a release for the given tag in a remote VCS, attaching the
        given changelog, if supported
        """

    @_not_supported
    def asset_upload_url(self, release_id: str) -> Optional[str]:
        """
        Return the URL to use to upload an asset to the given release id, if releases
        are supported by the remote VCS
        """

    @_not_supported
    def upload_asset(
        self, release_id: int, file: str, label: Optional[str] = None
    ) -> bool:
        """
        Upload an asset (file) to a release with the given release_id, if releases are
        supported by the remote VCS. Add a custom label if one is given in the "label"
        parameter and labels are supported by the remote VCS
        """

    @_not_supported
    def remote_url(self, use_token: bool) -> str:
        """
        Return the remote URL for the repository, including the token for
        authentication if requested by setting the `use_token` parameter to True,
        """

    @_not_supported
    def commit_hash_url(self, commit_hash: str) -> str:
        """
        Given a commit hash, return a web URL which links to this commit in the
        remote VCS.
        """

    @_not_supported
    def pull_request_url(self, pr_number: str) -> str:
        """
        Given a number for a PR/Merge request/equivalent, return a web URL that links
        to that PR in the remote VCS.
        """
