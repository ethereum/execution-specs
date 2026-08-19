"""
Tests for appended sync-payload eligibility, leaves and physical guards.

The filler appends one framework-built empty block above each authored
leaf, stored out-of-chain in the fixture's ``syncPayloads`` list. These
tests pin which tests can carry targets, how rejected attempts split the
payload graph into leaves, and which heads the filler declines to build
above. The payloads themselves are built against a real backend and are
covered by the filler plugin's pytester tests.
"""

from typing import Any, Dict, List

import pytest

from execution_testing.base_types import Address, Hash
from execution_testing.exceptions import BlockException, EngineAPIError
from execution_testing.fixtures.blockchain import FixtureHeader
from execution_testing.forks import (
    BPO2ToAmsterdamAtTime15k,
    Cancun,
    Fork,
    TransitionFork,
)
from execution_testing.specs.benchmark import BenchmarkTest
from execution_testing.specs.blockchain import (
    Block,
    BlockchainTest,
    sync_block_context_unavailable,
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
    fork: Fork | TransitionFork = Cancun,
) -> BlockchainTest:
    """Create a blockchain test over the given blocks."""
    return BlockchainTest(
        fork=fork,
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
    Every non-empty chain can carry sync payloads unless one of its
    authored payloads asserts an Engine API error code.

    Expected-invalid blocks are eligible: the appended block is what
    puts them on the wire. A block whose ``engine_api_error_code``
    expects the announcement itself to be refused is not - a block
    appended above it would be announced instead, and the refusal the
    test asserts would never happen.
    """
    assert make_test(blocks=blocks).sync_payload_eligible() is eligible


@pytest.mark.parametrize(
    "blocks,leaves",
    [
        pytest.param([VALID], [0], id="valid_singleton"),
        pytest.param(
            [VALID, Block(timestamp=2_000)],
            [1],
            id="valid_chain_has_one_leaf",
        ),
        pytest.param([INVALID], [0], id="invalid_singleton"),
        pytest.param(
            [VALID, Block(timestamp=2_000, exception=INVALID.exception)],
            [1],
            id="terminal_invalid_covers_valid_ancestor",
        ),
        pytest.param(
            [INVALID, Block(timestamp=2_000)],
            [0, 1],
            id="invalid_then_valid_siblings",
        ),
        pytest.param(
            [
                INVALID,
                Block(timestamp=2_000),
                Block(timestamp=3_000, exception=INVALID.exception),
                Block(timestamp=4_000),
            ],
            [0, 2, 3],
            id="two_rejected_leaves_and_final_valid_leaf",
        ),
        pytest.param([REFUSED], [], id="engine_refused"),
        pytest.param([], [], id="empty"),
    ],
)
def test_sync_payload_leaf_indices(
    blocks: List[Block], leaves: List[int]
) -> None:
    """Every authored payload is below at least one selected leaf."""
    assert make_test(blocks=blocks).sync_payload_leaf_indices() == leaves


def test_sync_block_disabled() -> None:
    """Without the option no chain takes the extra block."""
    test = make_test(blocks=[VALID], sync_block=False)
    assert not test.sync_payload_eligible()


def head_with(**fields: Any) -> FixtureHeader:
    """Build a Cancun-shaped header pinning the given fields."""
    defaults: Dict[str, Any] = dict(
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
        blob_gas_used=0,
        excess_blob_gas=0,
        parent_beacon_block_root=Hash(0),
    )
    return FixtureHeader(**{**defaults, **fields})


@pytest.mark.parametrize(
    "head_number,available",
    [
        pytest.param(2**64 - 2, True, id="child_fits_exactly"),
        pytest.param(2**64 - 1, False, id="max"),
        pytest.param(2**64, False, id="already_overflowing"),
    ],
)
def test_block_number_ceiling(head_number: int, available: bool) -> None:
    """The appended block's number must have a uint64 representation."""
    reason = sync_block_context_unavailable(
        head_with(number=head_number), Cancun
    )
    assert (reason is None) is available


@pytest.mark.parametrize(
    "gas_limit,available",
    [
        pytest.param(2**64 - 1, True, id="max"),
        pytest.param(2**64, False, id="one_over_max"),
    ],
)
def test_gas_limit_ceiling(gas_limit: int, available: bool) -> None:
    """The appended block's inherited gas limit must fit uint64."""
    reason = sync_block_context_unavailable(
        head_with(gas_limit=gas_limit), Cancun
    )
    assert (reason is None) is available


@pytest.mark.parametrize(
    "head_timestamp,available",
    [
        pytest.param(2**64 - 1, False, id="max"),
        pytest.param(
            2**64 - Cancun.block_time(),
            False,
            id="one_short_of_room",
        ),
        pytest.param(
            2**64 - 1 - Cancun.block_time(),
            True,
            id="exactly_enough_room",
        ),
    ],
)
def test_timestamp_ceiling(head_timestamp: int, available: bool) -> None:
    """
    A head pinned so close to the uint64 ceiling that no child
    timestamp fits carries no sync block: nothing downstream notices
    the overflow, and no client can parse the resulting payload.
    """
    reason = sync_block_context_unavailable(
        head_with(timestamp=head_timestamp), Cancun
    )
    assert (reason is None) is available


@pytest.mark.parametrize(
    "slot_number,available",
    [
        pytest.param(2**64 - 1, False, id="max_slot"),
        pytest.param(2**64 - 2, True, id="one_below_max"),
        pytest.param(None, True, id="no_slot_field"),
    ],
)
def test_slot_ceiling(slot_number: int | None, available: bool) -> None:
    """
    The appended block's slot number is its parent's plus one, so the
    maximum uint64 slot number admits no child.
    """
    reason = sync_block_context_unavailable(
        head_with(slot_number=slot_number), Cancun
    )
    assert (reason is None) is available


@pytest.mark.parametrize(
    "excess_blob_gas,blob_gas_used,available",
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
            id="blob_gas_fields_overflow_uint64",
        ),
        pytest.param(
            2**64 - 2 * Cancun.blob_gas_per_blob(),
            0,
            False,
            id="price_needs_unbounded_taylor_steps",
        ),
    ],
)
def test_blob_fields_the_fork_cannot_build_above(
    excess_blob_gas: int, blob_gas_used: int, available: bool
) -> None:
    """
    A head pinning blob fields whose child fee context cannot be
    derived - the fields do not sum within uint64, or the price's
    Taylor series would run for astronomically many steps - carries no
    sync block, while a legitimately expensive fee market still does.
    """
    reason = sync_block_context_unavailable(
        head_with(
            excess_blob_gas=excess_blob_gas, blob_gas_used=blob_gas_used
        ),
        Cancun,
    )
    assert (reason is None) is available


@pytest.mark.parametrize(
    "gas_limit,available",
    [
        pytest.param(Cancun.minimum_block_gas_limit(), True, id="minimum"),
        pytest.param(
            Cancun.minimum_block_gas_limit() - 1, False, id="one_below"
        ),
        pytest.param(0, False, id="zero"),
    ],
)
def test_gas_limit_the_fork_cannot_build_above(
    gas_limit: int, available: bool
) -> None:
    """
    The appended block inherits its parent's gas limit, so a head below
    the fork's minimum carries no sync block. The floor is fork
    arithmetic - from Amsterdam on it is the budget an empty block's
    own access list needs - which is why the filler decides this rather
    than the test author.
    """
    reason = sync_block_context_unavailable(
        head_with(gas_limit=gas_limit), Cancun
    )
    assert (reason is None) is available


@pytest.mark.parametrize(
    "head_timestamp,available",
    [
        pytest.param(14_000, True, id="appended_block_lands_before_the_fork"),
        pytest.param(15_000, False, id="appended_block_lands_after_the_fork"),
    ],
)
def test_head_is_judged_under_the_appended_block_s_own_fork(
    head_timestamp: int, available: bool
) -> None:
    """
    A transition chain's head is judged against the fork the appended
    block itself lands in, not the chain's final fork.

    The gas limit here is legal before Amsterdam and below the floor
    Amsterdam raises it to, so the two forks disagree about this head.
    Judging by the chain's final fork would refuse the appended block
    on a chain that never reaches that fork.
    """
    reason = sync_block_context_unavailable(
        head_with(gas_limit=10_000, timestamp=head_timestamp),
        BPO2ToAmsterdamAtTime15k,
    )
    assert (reason is None) is available


def test_benchmark_chains_take_sync_payloads() -> None:
    """
    A benchmark chain carries the appended block like any other: the
    benchmark's gas and opcode values are recorded before the block is
    built, and the block is what makes a mostly single-block benchmark
    chain servable by a sync-based consumer at all. The conversion to
    a blockchain test propagates the fill context unchanged, so
    ``--no-sync-block`` remains the release-level opt-out.
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
    assert blockchain_test.sync_block
    assert blockchain_test.sync_payload_eligible()
