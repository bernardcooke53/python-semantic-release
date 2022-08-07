"""Build and manage distributions
"""
import logging
import shutil
from typing import Optional

from invoke import run

logger = logging.getLogger(__name__)


def should_build(
    upload_to_repository: bool,
    upload_to_pypi: bool,
    upload_to_release: bool,
    build_command: Optional[str],
) -> bool:
    upload_to_artifact_repository = upload_to_repository and upload_to_pypi
    build_command = (
        build_command if (build_command and build_command != "false") else False
    )
    return bool(build_command) and (upload_to_artifact_repository or upload_to_release)


def should_remove_dist(
    remove_dist: bool,
    upload_to_repository: bool,
    upload_to_pypi: bool,
    upload_to_release: bool,
    build_command: Optional[str],
) -> bool:
    return bool(
        remove_dist
        and should_build(
            upload_to_repository, upload_to_pypi, upload_to_release, build_command
        )
    )


def build_dists(build_command: Optional[str]) -> None:
    logger.info(f"Running {build_command}")
    run(build_command)


def remove_dists(path: str):
    logger.debug(f"Removing build folder: `{path}`")
    shutil.rmtree(path, ignore_errors=True)
