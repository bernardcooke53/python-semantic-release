from dataclasses import dataclass
from typing import Any, Callable, Tuple

from jinja2 import Environment

from semantic_release.changelog.release_history import ReleaseHistory
from semantic_release.hvcs._base import HvcsBase

# from semantic_release.version.version import Version


@dataclass
class ChangelogContext:
    repo_name: str
    repo_owner: str
    # version: Version
    history: ReleaseHistory
    functions: Tuple[Callable[..., Any], ...] = ()

    def bind_to_environment(self, env: Environment) -> Environment:
        env.globals["context"] = self
        for f in self.functions:
            env.filters[f.__name__] = f
        return env


def make_changelog_context(
    hvcs_client: HvcsBase,
    # version: Version,
    release_history: ReleaseHistory
    # All changes in branch's history
) -> ChangelogContext:
    return ChangelogContext(
        repo_name=hvcs_client.repo_name,
        repo_owner=hvcs_client.owner,
        # version=version,
        history=release_history,
        functions=(hvcs_client.pull_request_url, hvcs_client.commit_hash_url),
    )
