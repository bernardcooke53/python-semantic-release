from __future__ import annotations
import semver

from semantic_release.enums import LevelBump


class Version(semver.VersionInfo):

    def bump(self, level: LevelBump, prerelease: bool = False, prerelease_token: str = "beta") -> Version:
        # If already a prerelease, bump revision and return
        if level is LevelBump.NO_RELEASE:
            # Return a copy rather than the same instance for consistency
            return Version(*self.to_tuple())

        if self.prerelease and prerelease:
            return self.bump_prerelease()

        version = self
        if level is LevelBump.MAJOR:
            version = self.bump_major()
        elif level is LevelBump.MINOR:
            version = self.bump_minor()
        elif level is LevelBump.PATCH:
            version = self.bump_patch()

        if prerelease:
            version = version.bump_prerelease(token=prerelease_token)
        return version
