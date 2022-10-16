"""Legacy commit parser from Python Semantic Release 1.0"""
import logging
import re
from dataclasses import dataclass

from git import Commit

from semantic_release.commit_parser._base import CommitParser, ParserOptions
from semantic_release.commit_parser.token import ParsedCommit, ParseError, ParseResult
from semantic_release.commit_parser.util import breaking_re, parse_paragraphs
from semantic_release.enums import LevelBump

logger = logging.getLogger(__name__)

re_parser = re.compile(r"(?P<subject>[^\n]+)" + r"(:?\n\n(?P<text>.+))?", re.DOTALL)


@dataclass
class TagParserOptions(ParserOptions):
    minor_tag: str = ":sparkles:"
    patch_tag: str = ":nut_and_bolt:"


class TagCommitParser(CommitParser[ParseResult[ParsedCommit, ParseError]]):
    """
    Parse a commit message according to the 1.0 version of python-semantic-release.
    It expects a tag of some sort in the commit message and will use the rest of the first line
    as changelog content.
    :param message: A string of a commit message.
    :raises UnknownCommitMessageStyleError: If it does not recognise the commit style
    :return: A tuple of (level to bump, type of change, scope of change, a tuple with descriptions)
    """

    parser_options = TagParserOptions

    def parse(self, commit: Commit) -> ParseResult[ParsedCommit, ParseError]:
        message = commit.message

        # Attempt to parse the commit message with a regular expression
        parsed = re_parser.match(message)
        if not parsed:
            return ParseError(
                commit, error=f"Unable to parse the given commit message: {message!r}"
            )

        subject = parsed.group("subject")

        # Check tags for minor or patch
        if self.options.minor_tag in message:
            level = "feature"
            level_bump = LevelBump.MINOR
            if subject:
                subject = subject.replace(self.options.minor_tag, "")

        elif self.options.patch_tag in message:
            level = "fix"
            level_bump = LevelBump.PATCH
            if subject:
                subject = subject.replace(self.options.patch_tag, "")

        else:
            # We did not find any tags in the commit message
            return ParseError(
                commit, error=f"Unable to parse the given commit message: {message!r}"
            )

        if parsed.group("text"):
            descriptions = parse_paragraphs(parsed.group("text"))
        else:
            descriptions = []
        descriptions.insert(0, subject.strip())

        # Look for descriptions of breaking changes
        breaking_descriptions = [
            match.group(1)
            for match in (breaking_re.match(p) for p in descriptions[1:])
            if match
        ]
        if breaking_descriptions:
            level = "breaking"
            level_bump = LevelBump.MAJOR

        return ParsedCommit(
            bump=level_bump,
            type=level,
            scope=None,
            descriptions=descriptions,
            breaking_descriptions=breaking_descriptions,
            commit=commit,
        )
