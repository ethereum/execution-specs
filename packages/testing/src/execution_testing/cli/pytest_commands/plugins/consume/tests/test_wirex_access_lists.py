"""
Tests for the access list modes `consume wirex --wirex-access-lists both`
runs a fixture under.

Only blocks from Amsterdam onward carry an access list, so only those
fixtures run twice; an earlier fixture would sync identically in both
modes.
"""

from pathlib import Path
from typing import Any

import pytest

from execution_testing.cli.pytest_commands.plugins.consume.simulators.wirex.conftest import (  # noqa: E501
    ACCESS_LISTS_SERVED,
    ACCESS_LISTS_WITHHELD,
    access_list_variants,
)
from execution_testing.fixtures import BlockchainEngineXFixture
from execution_testing.fixtures.consume import TestCaseIndexFile
from execution_testing.forks import (
    Amsterdam,
    BPO2ToAmsterdamAtTime15k,
    Osaka,
    OsakaToBPO1AtTime15k,
)


def _case(fork: Any) -> TestCaseIndexFile:
    """Return an EngineX test case of `fork`."""
    return TestCaseIndexFile(
        id="test",
        fixture_hash="0x" + "11" * 32,
        format=BlockchainEngineXFixture,
        fork=fork,
        json_path=Path("test.json"),
    )


@pytest.mark.parametrize("fork", [Amsterdam, BPO2ToAmsterdamAtTime15k])
def test_access_list_forks_run_in_both_modes(fork: Any) -> None:
    """A fork whose blocks carry access lists runs withheld and served."""
    assert access_list_variants(_case(fork)) == (
        ACCESS_LISTS_WITHHELD,
        ACCESS_LISTS_SERVED,
    )


@pytest.mark.parametrize("fork", [Osaka, OsakaToBPO1AtTime15k, None])
def test_earlier_forks_run_once(fork: Any) -> None:
    """A fork without access lists keeps one unsuffixed test."""
    assert access_list_variants(_case(fork)) == ("",)
