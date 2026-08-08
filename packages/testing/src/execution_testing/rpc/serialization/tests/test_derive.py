"""Test enumeration of RPC expectations from a filled fixture."""

from typing import Any, Dict, List

import pytest

from execution_testing.base_types import Bytes, Hash
from execution_testing.exceptions import BlockException
from execution_testing.fixtures.blockchain import (
    BlockchainFixture,
    FixtureConfig,
    InvalidFixtureBlock,
)
from execution_testing.forks import Amsterdam
from execution_testing.rpc.serialization import derive as derive_module
from execution_testing.rpc.serialization import (
    derive_rpc_calls,
    validate_result,
)
from execution_testing.rpc.serialization.derive import ProjectionError

from .test_projection import (
    make_block,
    make_header,
    make_receipt,
    make_transaction,
)


def make_fixture(blocks: List[Any]) -> BlockchainFixture:
    """Return a fixture wrapping the given blocks."""
    genesis = make_header(number=0, gas_used=0)
    return BlockchainFixture(
        fork=Amsterdam,
        genesis=genesis,
        genesis_rlp=Bytes(b"\xc0"),
        blocks=blocks,
        last_block_hash=genesis.block_hash,
        pre={},
        post_state={},
        config=FixtureConfig(fork=Amsterdam, chain_id=1),
    )


@pytest.fixture
def single_block_fixture() -> BlockchainFixture:
    """Return a fixture holding one block with two transactions."""
    transactions = [make_transaction(nonce=0), make_transaction(nonce=1)]
    receipts = [
        make_receipt(21_000, transaction_hash=Hash(0xAA)),
        make_receipt(42_000, transaction_hash=Hash(0xBB)),
    ]
    return make_fixture([make_block(transactions, receipts)])


def methods(calls: List[Any]) -> List[str]:
    """Return the method name of each call, in order."""
    return [call.method for call in calls]


def test_each_block_is_queried_both_ways(
    single_block_fixture: BlockchainFixture,
) -> None:
    """A block is fetched by number and by hash, with the same result."""
    calls = derive_rpc_calls(single_block_fixture)

    by_number = next(c for c in calls if c.method == "eth_getBlockByNumber")
    by_hash = next(c for c in calls if c.method == "eth_getBlockByHash")

    assert by_number.result == by_hash.result
    assert by_number.params[0] == "0x1"


def test_every_transaction_gets_a_receipt_lookup(
    single_block_fixture: BlockchainFixture,
) -> None:
    """Each transaction contributes a receipt call keyed by its hash."""
    calls = derive_rpc_calls(single_block_fixture)
    receipts = [c for c in calls if c.method == "eth_getTransactionReceipt"]

    assert len(receipts) == 2
    assert [c.params[0] for c in receipts] == [
        str(Hash(0xAA)),
        str(Hash(0xBB)),
    ]


def test_parameters_come_from_the_chain(
    single_block_fixture: BlockchainFixture,
) -> None:
    """
    Every parameter is read off the fixture.

    Nothing is author-supplied, which is why the marker carries no
    parameter information.
    """
    calls = derive_rpc_calls(single_block_fixture)
    block = single_block_fixture.blocks[0]

    by_hash = next(c for c in calls if c.method == "eth_getBlockByHash")
    assert by_hash.params[0] == str(block.header.block_hash)  # type: ignore


def test_derived_results_conform_to_the_schema(
    single_block_fixture: BlockchainFixture,
) -> None:
    """Enumeration produces spec-conformant results, not just plausible."""
    for call in derive_rpc_calls(single_block_fixture):
        validate_result(call.method, call.result)


def test_invalid_blocks_are_skipped() -> None:
    """
    An invalid block contributes no expectations.

    It never joins the canonical chain, so a client is right to report
    nothing for it.
    """
    valid = make_block([make_transaction()], [make_receipt(21_000)])
    invalid = InvalidFixtureBlock(
        rlp=Bytes(b"\xc0"),
        expect_exception=BlockException.INCORRECT_BLOCK_FORMAT,
    )

    calls = derive_rpc_calls(make_fixture([valid, invalid]))

    # Two per canonical block: the hash form and the full-object form.
    assert methods(calls).count("eth_getBlockByNumber") == 2


def test_empty_block_yields_no_receipt_calls() -> None:
    """A block with no transactions still gets its block queries."""
    calls = derive_rpc_calls(make_fixture([make_block([], [])]))

    assert "eth_getTransactionReceipt" not in methods(calls)
    assert "eth_getTransactionByHash" not in methods(calls)
    assert methods(calls).count("eth_getBlockByNumber") == 2


def test_calls_serialize_into_the_fixture(
    single_block_fixture: BlockchainFixture,
) -> None:
    """The derived section round-trips through the fixture model."""
    single_block_fixture.rpc = derive_rpc_calls(single_block_fixture)

    dumped: Dict[str, Any] = single_block_fixture.model_dump(
        by_alias=True, mode="json"
    )

    assert len(dumped["rpc"]) == len(single_block_fixture.rpc)
    assert dumped["rpc"][0]["method"] == "eth_getBlockByNumber"


def test_absent_marker_leaves_the_section_unset(
    single_block_fixture: BlockchainFixture,
) -> None:
    """A fixture carries no `rpc` section unless one is derived."""
    assert single_block_fixture.rpc is None


def test_broken_projection_fails_at_derivation(
    single_block_fixture: BlockchainFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    A non-conformant projection is refused rather than written out.

    `FixtureRPCCall.result` is `Any`, so nothing downstream can tell a
    projected block from a bare string. Were this to reach a release it
    would surface as "your response is wrong" to a client team debugging
    an assertion that was never satisfiable.
    """
    good = derive_rpc_calls(single_block_fixture)[0].result
    monkeypatch.setattr(
        derive_module,
        "block_response",
        lambda _block, **_kwargs: _BadProjection(good),
    )

    with pytest.raises(ProjectionError, match="projection bug"):
        derive_rpc_calls(single_block_fixture)


def test_unknown_method_fails_at_derivation(
    single_block_fixture: BlockchainFixture,
) -> None:
    """A call the schema does not define is refused at derivation."""
    calls = derive_rpc_calls(single_block_fixture)
    calls[0].method = "eth_notAMethod"

    with pytest.raises(ProjectionError, match="does not define"):
        derive_module._reject_unsatisfiable(calls)


class _BadProjection:
    """
    Stand-in projection with a realistic defect.

    Structurally a block, but quantities are zero-padded the way the
    consensus types encode them. This is the exact regression the guard
    exists for: plausible enough to survive every downstream check, and
    unsatisfiable by any conforming client.
    """

    def __init__(self, good: Dict[str, Any]) -> None:
        self.payload = dict(good, number="0x01")

    def to_rpc(self) -> Dict[str, Any]:
        """Return the defective block object."""
        return self.payload


def test_blocks_can_be_supplied_directly(
    single_block_fixture: BlockchainFixture,
) -> None:
    """
    Derivation accepts a block list, not only a fixture.

    The engine formats carry payloads rather than blocks, so their blocks
    are assembled during generation and handed over directly.
    """
    from_fixture = derive_rpc_calls(single_block_fixture)
    from_blocks = derive_module.derive_rpc_calls_for_blocks(
        single_block_fixture.blocks
    )

    assert [c.method for c in from_blocks] == [c.method for c in from_fixture]
    assert [c.result for c in from_blocks] == [c.result for c in from_fixture]
