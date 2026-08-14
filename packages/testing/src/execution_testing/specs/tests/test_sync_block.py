"""
Tests for the appended sync block's eligibility and physical guards.

The filler appends one framework-built empty block above every
engine_x chain, stored out-of-chain in the fixture's ``syncPayload``,
so a sync-based consumer can announce it and every test-authored block
must travel devp2p as ancestry. These tests pin which chains take the
block and the uint64 headroom the append needs; the block itself is
built against a real backend and is covered by the filler plugin's
pytester tests.
"""

from typing import List

import pytest

from execution_testing.base_types import Address, Hash
from execution_testing.exceptions import BlockException, EngineAPIError
from execution_testing.fixtures.blockchain import FixtureHeader
from execution_testing.forks import Cancun
from execution_testing.specs.benchmark import BenchmarkTest
from execution_testing.specs.blockchain import (
    DEFAULT_TIMESTAMP_INCREMENT,
    Block,
    BlockchainTest,
    sync_block_blob_context_derivable,
    verify_sync_block_timestamp_headroom,
)
from execution_testing.test_types import Alloc, Environment

SALT = "tests/cancun/test_x.py::test_y[fork_Cancun]"

VALID = Block(timestamp=1_000)
INVALID = Block(
    timestamp=1_000, exception=BlockException.INCORRECT_BLOCK_FORMAT
)
REFUSED = Block(
    timestamp=1_000, engine_api_error_code=EngineAPIError.InvalidParams
)


def make_test(
    *,
    blocks: List[Block],
    sync_block: bool = True,
) -> BlockchainTest:
    """Create a Cancun blockchain test over the given blocks."""
    return BlockchainTest(
        fork=Cancun,
        pre=Alloc(),
        post=Alloc(),
        blocks=blocks,
        sync_block=sync_block,
        sync_block_salt=SALT,
    )


@pytest.mark.parametrize(
    "blocks,eligible",
    [
        pytest.param([VALID], True, id="valid_singleton"),
        pytest.param(
            [VALID, Block(timestamp=2_000)], True, id="valid_multi_block"
        ),
        pytest.param([INVALID], True, id="invalid_singleton"),
        pytest.param(
            [
                VALID,
                Block(
                    timestamp=2_000,
                    exception=BlockException.INCORRECT_BLOCK_FORMAT,
                ),
            ],
            True,
            id="invalid_multi_block",
        ),
        pytest.param(
            [INVALID, Block(timestamp=2_000)],
            True,
            id="mid_chain_invalid_block",
        ),
        pytest.param([REFUSED], False, id="engine_refused_singleton"),
        pytest.param(
            [
                VALID,
                Block(
                    timestamp=2_000,
                    engine_api_error_code=EngineAPIError.InvalidParams,
                ),
            ],
            False,
            id="engine_refused_multi_block_head",
        ),
        pytest.param([REFUSED, VALID], False, id="engine_refused_ancestor"),
        pytest.param([], False, id="empty_chain"),
    ],
)
def test_sync_payload_eligibility(blocks: List[Block], eligible: bool) -> None:
    """
    Every chain with blocks takes the appended sync block, except one
    asserting an Engine API error code.

    Expected-invalid blocks are eligible: the appended block is what
    puts them on the wire. A block whose ``engine_api_error_code``
    expects the announcement itself to be refused is not - a block
    appended above it would be announced instead, and the refusal the
    test asserts would never happen.
    """
    assert make_test(blocks=blocks).sync_payload_eligible() is eligible


def test_sync_block_disabled() -> None:
    """Without the option no chain takes the extra block."""
    test = make_test(blocks=[VALID], sync_block=False)
    assert not test.sync_payload_eligible()


def test_benchmark_chains_never_take_the_sync_block() -> None:
    """
    A benchmark chain must not carry the appended block: it would
    distort the per-block gas and timing benchmarks measure. The
    conversion to a blockchain test opts out explicitly, overriding
    whatever the fill context set on the benchmark spec.
    """
    benchmark_test = BenchmarkTest(
        fork=Cancun,
        pre=Alloc(),
        post=Alloc(),
        env=Environment(),
        gas_benchmark_value=1_000_000,
        blocks=[Block()],
        sync_block=True,
        sync_block_salt=SALT,
    )
    blockchain_test = benchmark_test.generate_blockchain_test()
    assert not blockchain_test.sync_block
    assert not blockchain_test.sync_payload_eligible()


@pytest.mark.parametrize(
    "head_timestamp",
    [2**64 - 1, 2**64 - DEFAULT_TIMESTAMP_INCREMENT],
    ids=["max", "one_short_of_room"],
)
def test_head_without_timestamp_headroom_is_refused(
    head_timestamp: int,
) -> None:
    """
    A head pinned so close to the uint64 ceiling that no block fits
    above it fails the fill loudly: nothing downstream notices the
    overflow, and no client can parse the resulting payload.
    """
    with pytest.raises(ValueError, match="no uint64 headroom"):
        verify_sync_block_timestamp_headroom(head_timestamp)


def test_head_with_exactly_enough_headroom_is_accepted() -> None:
    """The largest head the appended block still fits above passes."""
    verify_sync_block_timestamp_headroom(
        2**64 - 1 - DEFAULT_TIMESTAMP_INCREMENT
    )


def blob_head(excess_blob_gas: int, blob_gas_used: int) -> FixtureHeader:
    """Build a Cancun header pinning the given blob fields."""
    return FixtureHeader(
        fork=Cancun,
        fee_recipient=Address(0),
        state_root=Hash(0),
        number=1,
        gas_limit=30_000_000,
        gas_used=0,
        timestamp=12,
        extra_data=b"\x00",
        base_fee_per_gas=7,
        withdrawals_root=Hash(0),
        blob_gas_used=blob_gas_used,
        excess_blob_gas=excess_blob_gas,
        parent_beacon_block_root=Hash(0),
    )


@pytest.mark.parametrize(
    "excess_blob_gas,blob_gas_used,derivable",
    [
        pytest.param(0, 0, True, id="empty_head"),
        pytest.param(
            60 * Cancun.blob_base_fee_update_fraction(),
            Cancun.blob_gas_per_blob(),
            True,
            id="expensive_but_representable_price",
        ),
        pytest.param(
            2**64 - Cancun.blob_gas_per_blob(),
            Cancun.blob_gas_per_blob(),
            False,
            id="parent_blob_gas_overflows_uint64",
        ),
        pytest.param(
            2**64 - 2 * Cancun.blob_gas_per_blob(),
            0,
            False,
            id="price_needs_unbounded_taylor_steps",
        ),
    ],
)
def test_sync_block_blob_context_derivable(
    excess_blob_gas: int, blob_gas_used: int, derivable: bool
) -> None:
    """
    A head pinning blob fields whose child fee context cannot be
    derived - the sum overflows uint64, or the price's Taylor series
    would run for astronomically many steps - carries no sync block,
    while a legitimately expensive fee market still does.
    """
    head = blob_head(excess_blob_gas, blob_gas_used)
    assert sync_block_blob_context_derivable(head, Cancun) is derivable
