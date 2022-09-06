import pytest

from semantic_release.enums import LevelBump
from semantic_release.version.version import Version


@pytest.mark.parametrize(
    "version_str, bump, is_prerelease, new_version_str",
    [
        ("1.0.0", LevelBump.MAJOR, False, "2.0.0"),
        ("1.0.0", LevelBump.MINOR, False, "1.1.0"),
        ("1.0.0", LevelBump.PATCH, False, "1.0.1"),
        ("1.0.0", LevelBump.NO_RELEASE, False, "1.0.0"),
        ("1.0.0", LevelBump.MAJOR, True, "2.0.0-rc.1"),
        ("1.0.0", LevelBump.MINOR, True, "1.1.0-rc.1"),
        ("1.0.0", LevelBump.PATCH, True, "1.0.1-rc.1"),
        ("1.0.0", LevelBump.NO_RELEASE, True, "1.0.0"),
        ("1.0.0-rc.1", LevelBump.MAJOR, False, "2.0.0"),
        ("1.0.0-rc.1", LevelBump.MINOR, False, "1.1.0"),
        ("1.0.0-rc.1", LevelBump.PATCH, False, "1.0.1"),
        ("1.0.0-rc.1", LevelBump.NO_RELEASE, False, "1.0.0-rc.1"),
        ("1.0.0-rc.1", LevelBump.MAJOR, True, "1.0.0-rc.2"),
        ("1.0.0-rc.1", LevelBump.MINOR, True, "1.0.0-rc.2"),
        ("1.0.0-rc.1", LevelBump.PATCH, True, "1.0.0-rc.2"),
        ("1.0.0-rc.1", LevelBump.NO_RELEASE, True, "1.0.0-rc.1"),
        # Note: currently build metadata isn't supported, this just
        # documents expected behaviour
        ("1.0.0+build.12345", LevelBump.MAJOR, False, "2.0.0"),
        ("1.0.0+build.12345", LevelBump.MINOR, False, "1.1.0"),
        ("1.0.0+build.12345", LevelBump.PATCH, False, "1.0.1"),
        ("1.0.0+build.12345", LevelBump.NO_RELEASE, False, "1.0.0+build.12345"),
        ("1.0.0+build.12345", LevelBump.MAJOR, True, "2.0.0-rc.1"),
        ("1.0.0+build.12345", LevelBump.MINOR, True, "1.1.0-rc.1"),
        ("1.0.0+build.12345", LevelBump.PATCH, True, "1.0.1-rc.1"),
        ("1.0.0+build.12345", LevelBump.NO_RELEASE, True, "1.0.0+build.12345"),
    ]
)
def test_version_bump(version_str, bump, is_prerelease, new_version_str):
    version = Version.parse(version_str)
    new_version = version.bump(bump, prerelease=is_prerelease, prerelease_token="rc")
    assert version is not new_version, "Version.bump should return a new Version instance"
    assert str(new_version) == new_version_str
