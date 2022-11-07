from __future__ import annotations

from typing import NamedTuple, NoReturn, TypeVar, Union

from git.objects.commit import Commit

from semantic_release.enums import LevelBump
from semantic_release.errors import CommitParseError


class ParsedCommit(NamedTuple):
    bump: LevelBump
    type: str
    scope: str
    descriptions: list[str]
    breaking_descriptions: list[str]
    commit: Commit


class ParseError(NamedTuple):
    commit: Commit
    error: str

    def raise_error(self) -> NoReturn:
        raise CommitParseError(self.error)


_T = TypeVar("_T", bound=ParsedCommit)
_E = TypeVar("_E", bound=ParseError)

# For extensions, this type can be used to build an alias
# e.g. CustomParseResult = ParseResultType[CustomParsedCommit, ParseError]
ParseResultType = Union[_T, _E]
ParseResult = ParseResultType[ParsedCommit, ParseError]
