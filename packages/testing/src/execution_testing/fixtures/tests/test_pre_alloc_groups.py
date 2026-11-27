"""Tests for pre-allocation group building."""

import ethereum.state as spec_state
from ethereum_types.bytes import Bytes20
from ethereum_types.numeric import U256, Uint

from execution_testing.base_types import Address, StateCommitment
from execution_testing.fixtures.blockchain import FixtureHeader
from execution_testing.fixtures.pre_alloc_groups import (
    GroupPreAlloc,
    PreAllocGroupBuilder,
)
from execution_testing.forks import get_forks
from execution_testing.test_types import (
    Account,
    Alloc,
    Environment,
)


def test_builder_genesis_carries_the_environment() -> None:
    """
    Every `Environment` field the genesis header shares reaches that header.

    A final `PreAllocGroup` does not carry the `Environment` it was grouped
    on, only the `genesis` header the builder derives from it, so this
    mapping is the whole of what a consumer ends up seeing.

    The fields to compare come from the two models, so one added to both is
    covered without touching this test. Fields left `None` are skipped, and
    the newest fork is used: `FixtureHeader.genesis` dumps the environment
    with `exclude_none=True` and derives the rest itself, gated on the fork
    (the empty block access list hash, for one).
    """
    fork = get_forks()[-1]
    environment = Environment(
        fee_recipient=0x1234,
        prev_randao=0x5678,
        extra_data=b"\x01\x02",
        number=0,
        timestamp=7,
        difficulty=0,
        gas_limit=0x123456,
        base_fee_per_gas=99,
        excess_blob_gas=0x20000,
        blob_gas_used=0x10000,
        parent_beacon_block_root=0xABC,
        slot_number=42,
    ).set_fork_requirements(fork)

    genesis = (
        PreAllocGroupBuilder(
            test_ids=["tests/a.py::test_a"],
            environment=environment,
            fork=fork,
            pre=Alloc(),
        )
        .build()
        .genesis
    )

    carried = sorted(
        field
        for field in set(Environment.model_fields)
        & set(FixtureHeader.model_fields)
        if getattr(environment, field) is not None
    )
    assert carried, "no environment field reaches the genesis header"
    for field in carried:
        assert getattr(genesis, field) == getattr(environment, field), (
            f"{field} did not reach the genesis header: "
            f"{getattr(environment, field)} != {getattr(genesis, field)}"
        )


def test_structural_copy_drops_group_caches() -> None:
    """
    A copy that executes blocks reports its own state root and dump, not the
    group's cached genesis ones.
    """
    address = Address(0x1234)
    group = GroupPreAlloc.model_validate({address: Account(balance=1)})
    group.migrate_state_commitment(StateCommitment.MPT)
    genesis_root = group.state_root()
    genesis_dump = group.model_dump(mode="json")
    group._cached_state_root = genesis_root

    copied = group.structural_copy()
    diff = spec_state.BlockDiff(
        account_changes={
            Bytes20(address): spec_state.Account(
                nonce=Uint(1),
                balance=U256(2),
                code_hash=spec_state.EMPTY_CODE_HASH,
            )
        }
    )
    copied.compute_state_root(diff)
    copied.apply_diff(diff)

    expected = Alloc.model_validate({address: Account(nonce=1, balance=2)})
    expected.migrate_state_commitment(StateCommitment.MPT)
    assert copied.state_root() == expected.state_root() != genesis_root
    assert copied.model_dump(mode="json") != genesis_dump
    assert group.state_root() == genesis_root
    assert group.model_dump(mode="json") == genesis_dump
