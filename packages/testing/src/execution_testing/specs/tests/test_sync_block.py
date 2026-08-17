"""
Tests for the appended sync block's eligibility.

The filler appends one framework-built empty block above every
engine_x chain, stored out-of-chain in the fixture's ``syncPayload``,
so a sync-based consumer can announce it and every test-authored block
must travel devp2p as ancestry. These tests pin which chains take the
block; the block itself is built against a real backend and is covered
by the filler plugin's pytester tests.
"""

from typing import List

import pytest

from execution_testing.exceptions import BlockException, EngineAPIError
from execution_testing.forks import Cancun, Fork, TransitionFork
from execution_testing.specs.benchmark import BenchmarkTest
from execution_testing.specs.blockchain import Block, BlockchainTest
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
