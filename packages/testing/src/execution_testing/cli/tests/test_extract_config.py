"""Tests for the extract_config CLI helpers."""

from pathlib import Path

import pytest

from execution_testing.base_types import Alloc
from execution_testing.cli.extract_config import GenesisState
from execution_testing.fixtures.blockchain import FixtureHeader
from execution_testing.fixtures.pre_alloc_groups import PreAllocGroup
from execution_testing.forks import (
    Fork,
    Prague,
    forks_from_until,
    get_deployed_forks,
)
from execution_testing.test_types import Environment


def forks_from_prague_onward() -> list[Fork]:
    """Return deployed forks from Prague onward."""
    all_forks = get_deployed_forks()
    return list(forks_from_until(Prague, all_forks[-1]))


@pytest.mark.parametrize("fork", forks_from_prague_onward())
def test_genesis_state_from_pre_alloc_group_uses_stored_chain_id(
    tmp_path: Path,
    fork: Fork,
) -> None:
    """Pre-alloc group files should preserve the configured chain ID."""
    builder = PreAllocGroup(
        test_ids=["test_id"],
        environment=Environment()
        .set_fork_requirements(fork)
        .model_dump(mode="json", exclude={"parent_hash"}),
        fork=fork.name(),
        chain_id=12345,
        genesis=FixtureHeader(
            parent_hash=0,
            ommers_hash=1,
            fee_recipient=2,
            state_root=3,
            transactions_trie=4,
            receipts_root=5,
            logs_bloom=6,
            difficulty=7,
            number=8,
            gas_limit=9,
            gas_used=10,
            timestamp=11,
            extra_data=b"",
            prev_randao=13,
            nonce=14,
        ),
        pre=Alloc().model_dump(mode="json"),
        group_hash=1,
        pre_account_count=1,
        test_count=1,
    )
    fixture_path = tmp_path / "pre_alloc.json"
    fixture_path.write_text(
        builder.model_dump_json(by_alias=True, exclude_none=True, indent=2)
    )

    genesis_state = GenesisState.from_fixture(fixture_path)

    assert genesis_state.chain_id == 12345
    assert genesis_state.get_client_environment()["HIVE_CHAIN_ID"] == "12345"


@pytest.mark.parametrize("fork", forks_from_prague_onward())
def test_genesis_state_from_legacy_pre_alloc_group_defaults_chain_id(
    tmp_path: Path,
    fork: Fork,
) -> None:
    """Legacy pre-alloc groups without chain ID should still default to 1."""
    builder = PreAllocGroup(
        test_ids=["test_id"],
        environment=Environment()
        .set_fork_requirements(fork)
        .model_dump(mode="json", exclude={"parent_hash"}),
        fork=fork.name(),
        genesis=FixtureHeader(
            parent_hash=0,
            ommers_hash=1,
            fee_recipient=2,
            state_root=3,
            transactions_trie=4,
            receipts_root=5,
            logs_bloom=6,
            difficulty=7,
            number=8,
            gas_limit=9,
            gas_used=10,
            timestamp=11,
            extra_data=b"",
            prev_randao=13,
            nonce=14,
        ),
        pre=Alloc().model_dump(mode="json"),
        group_hash=1,
        pre_account_count=1,
        test_count=1,
    )
    fixture_path = tmp_path / "legacy_pre_alloc.json"
    fixture_path.write_text(builder.model_dump_json(exclude={"chain_id"}))

    genesis_state = GenesisState.from_fixture(fixture_path)

    assert genesis_state.chain_id == 1
    assert genesis_state.get_client_environment()["HIVE_CHAIN_ID"] == "1"
