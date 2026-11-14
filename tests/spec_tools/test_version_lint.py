"""Tests for the EELS version hygiene lint."""

import pytest

from ethereum_spec_tools.lint.lints.version_hygiene import VersionHygiene


@pytest.mark.parametrize(
    "version",
    [
        "1.15.0",
        "1.15.1",
        "2.16.0",
        "1.15.0rc1",
        "1.15.0rc1.post3",
        "1.15.0.dev7",
        "1.15.0rc5.dev7",
        "1.15.0rc5.post7.dev9",
    ],
)
def test_version_hygiene_accepts_documented_forms(version: str) -> None:
    """Accept documented EELS release-version forms."""
    assert VersionHygiene.check_version(version) == []


@pytest.mark.parametrize(
    "version",
    [
        "1.15",
        "v1.15.0",
        "1.15.0-rc1",
        "1.15.1rc1",
        "1.15.0rc0",
        "1.15.0rc1.post0",
        "1.15.0.dev0",
        "01.15.0",
        "1.015.0",
        "1.15.0+local",
    ],
)
def test_version_hygiene_rejects_other_forms(version: str) -> None:
    """Reject versions outside the documented EELS grammar."""
    diagnostics = VersionHygiene.check_version(version)
    assert len(diagnostics) == 1
    assert f"invalid EELS version `{version}`" in diagnostics[0].message
