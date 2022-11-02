import logging
import mimetypes
import os
from typing import Optional, Tuple, Union
from urllib.parse import urlsplit

import gitlab

from semantic_release.helpers import logged_function
from semantic_release.hvcs._base import HvcsBase
from semantic_release.hvcs.token_auth import TokenAuth
from semantic_release.hvcs.util import build_requests_session

logger = logging.getLogger(__name__)

# Add a mime type for wheels
# Fix incorrect entries in the `mimetypes` registry.
# On Windows, the Python standard library's `mimetypes` reads in
# mappings from file extension to MIME type from the Windows
# registry. Other applications can and do write incorrect values
# to this registry, which causes `mimetypes.guess_type` to return
# incorrect values, which causes TensorBoard to fail to render on
# the frontend.
# This method hard-codes the correct mappings for certain MIME
# types that are known to be either used by python-semantic-release or
# problematic in general.
mimetypes.add_type("application/octet-stream", ".whl")
mimetypes.add_type("text/markdown", ".md")


class Gitlab(HvcsBase):
    """
    Gitlab helper class
    Note Gitlab doesn't really have the concept of a separate
    API domain
    """

    DEFAULT_DOMAIN = "gitlab.com"

    # pylint: disable=super-init-not-called
    def __init__(
        self,
        remote_url: str,
        hvcs_domain: Optional[str] = None,
        hvcs_api_domain: Optional[str] = None,
        token_var: str = "GL_TOKEN",
    ) -> None:
        self._remote_url = remote_url
        self.hvcs_domain = (
            hvcs_domain or self._domain_from_environment() or self.DEFAULT_DOMAIN
        )
        self.hvcs_api_domain = hvcs_api_domain or self.hvcs_domain.replace(
            "https://", ""
        )
        self.api_url = os.getenv("CI_SERVER_URL", f"https://{self.hvcs_api_domain}")

        self.token = os.getenv(token_var)
        auth = None if not self.token else TokenAuth(self.token)
        self.session = build_requests_session(auth=auth)

    @staticmethod
    def _domain_from_environment() -> Optional[str]:
        """
        Use Gitlab-CI environment vars if available
        """
        if "CI_SERVER_URL" in os.environ:
            url = urlsplit(os.environ["CI_SERVER_URL"])
            return f"{url.netloc}{url.path}".rstrip("/")
        return os.getenv("CI_SERVER_HOST")

    def _get_repository_owner_and_name(self) -> Tuple[str, str]:
        # Gitlab-CI context
        if "CI_PROJECT_NAMESPACE" in os.environ and "CI_PROJECT_NAME" in os.environ:
            return os.environ["CI_PROJECT_NAMESPACE"], os.environ["CI_PROJECT_NAME"]
        return super()._get_repository_owner_and_name()

    @logged_function(logger)
    def check_build_status(self, ref: str) -> bool:
        """Check last build status
        :param owner: The owner namespace of the repository. It includes all groups and subgroups.
        :param repo: The repository name
        :param ref: The sha1 hash of the commit ref
        :return: the status of the pipeline (False if a job failed)
        """
        client = gitlab.Gitlab(self.api_url, private_token=self.token)
        client.auth()
        jobs = (
            client.projects.get(f"{self.owner}/{self.repo_name}")
            .commits.get(ref)
            .statuses.list()
        )
        for job in jobs:
            # "success" and "skipped" aren't considered
            if job["status"] == "pending":  # type: ignore[index]
                logger.debug(
                    "check_build_status: job %s is still in pending status",
                    job["name"],  # type: ignore[index]
                )
                return False
            if job["status"] == "failed" and not job["allow_failure"]:  # type: ignore[index]
                logger.debug("check_build_status: job %s failed", job["name"])  # type: ignore[index]
                return False
        return True

    @logged_function(logger)
    def create_release(self, tag: str, changelog: str) -> bool:
        """Post release changelog
        :param owner: The owner namespace of the repository
        :param repo: The repository name
        :param tag: Tag to create release for
        :param changelog: The release notes for this version
        :return: The status of the request
        """
        client = gitlab.Gitlab(self.api_url, private_token=self.token)
        client.auth()
        try:
            logger.debug("Before release create call")
            client.projects.get(self.owner + "/" + self.repo_name).releases.create(
                {
                    "name": "Release " + tag,
                    "tag_name": tag,
                    "description": changelog,
                }
            )
            return True
        except gitlab.GitlabCreateError:
            logger.debug(
                "Release %s could not be created for project %s/%s",
                tag,
                self.owner,
                self.repo_name,
            )
            return False

    def remote_url(self, use_token: bool = True) -> str:
        if not (self.token and use_token):
            return self._remote_url
        return f"https://gitlab-ci-token:{self.token}@{self.hvcs_domain}/{self.owner}/{self.repo_name}.git"

    def commit_hash_url(self, commit_hash: str) -> str:
        return f"https://{self.hvcs_domain}/{self.owner}/{self.repo_name}/-/commit/{commit_hash}"

    def pull_request_url(self, pr_number: Union[str, int]) -> str:
        return f"https://{self.hvcs_domain}/{self.owner}/{self.repo_name}/-/issues/{pr_number}"
