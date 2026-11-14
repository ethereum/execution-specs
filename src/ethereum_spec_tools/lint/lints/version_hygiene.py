"""
EELS Version Hygiene Lint.

Ensures the package version follows the release grammar documented in
``docs/specs/spec_releases.md``.
"""

import re
from typing import List, Sequence

from ethereum import __version__
from ethereum_spec_tools.forks import Hardfork
from ethereum_spec_tools.lint import Diagnostic, Lint

_VERSION_RE = re.compile(
    r"""
    ^
    (?:0|[1-9][0-9]*)                  # COMPAT
    \.
    (?:0|[1-9][0-9]*)                  # HARDFORK
    \.
    (?:
        (?:0|[1-9][0-9]*)              # PATCH
        |
        0rc[1-9][0-9]*                 # DEVNET
        (?:\.post[1-9][0-9]*)?         # optional devnet PATCH
    )
    (?:\.dev[1-9][0-9]*)?              # optional preview number
    $
    """,
    re.VERBOSE,
)


class VersionHygiene(Lint):
    """Ensure the EELS package version follows the documented grammar."""

    @staticmethod
    def check_version(version: str) -> Sequence[Diagnostic]:
        """Return a diagnostic when ``version`` is not a legal EELS version."""
        if _VERSION_RE.fullmatch(version):
            return []

        return [
            Diagnostic(
                message=(
                    f"invalid EELS version `{version}`; expected "
                    "COMPAT.HARDFORK.PATCH or "
                    "COMPAT.HARDFORK.0rcDEVNET[.postPATCH], "
                    "optionally followed by .devDEV"
                )
            )
        ]

    def lint(
        self, forks: List[Hardfork], position: int
    ) -> Sequence[Diagnostic]:
        """
        Check the package version once.

        ``ethereum-spec-lint`` invokes every lint once per hardfork. Version
        validity is repository-wide, so only the first invocation performs
        the check.
        """
        del forks
        if position != 0:
            return []
        return self.check_version(__version__)
