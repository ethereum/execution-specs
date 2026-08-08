"""Test replay of derived RPC expectations against a client."""

from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest

from execution_testing.base_types import Bytes, Hash
from execution_testing.cli.pytest_commands.plugins.consume.simulators.helpers.rpc_expectations import (  # noqa: E501
    verify_rpc_expectations,
)
from execution_testing.fixtures.blockchain import (
    BlockchainFixture,
    FixtureConfig,
)
from execution_testing.fixtures.common import FixtureRPCCall
from execution_testing.forks import Amsterdam
from execution_testing.rpc.serialization import (
    block_response,
    derive_rpc_calls,
)
from execution_testing.rpc.serialization.tests.test_projection import (
    make_block,
    make_header,
    make_receipt,
    make_transaction,
)


@pytest.fixture
def fixture() -> BlockchainFixture:
    """Return a filled fixture carrying derived RPC expectations."""
    genesis = make_header(number=0, gas_used=0)
    block = make_block([make_transaction()], [make_receipt(21_000)])
    built = BlockchainFixture(
        fork=Amsterdam,
        genesis=genesis,
        genesis_rlp=Bytes(b"\xc0"),
        blocks=[block],
        last_block_hash=block.header.block_hash,
        pre={},
        post_state={},
        config=FixtureConfig(fork=Amsterdam, chain_id=1),
    )
    built.rpc = derive_rpc_calls(built)
    return built


def rpc_returning(results: List[Any]) -> MagicMock:
    """Return a mock client whose batch call yields the given responses."""
    client = MagicMock()
    client.post_batch_request.return_value = [
        MagicMock(result=result, error=None) for result in results
    ]
    return client


def erroring_rpc(code: int, message: str = "boom") -> MagicMock:
    """Return a mock client whose batch call yields a JSON-RPC error."""
    client = MagicMock()
    client.post_batch_request.return_value = [
        MagicMock(result=None, error=MagicMock(code=code, message=message))
    ]
    return client


def test_conforming_client_passes(fixture: BlockchainFixture) -> None:
    """A client echoing the stored expectations satisfies the check."""
    assert fixture.rpc is not None
    client = rpc_returning([call.result for call in fixture.rpc])

    verify_rpc_expectations(client, fixture)

    client.post_batch_request.assert_called_once()


def test_absent_section_makes_no_calls(
    fixture: BlockchainFixture,
) -> None:
    """
    An unmarked fixture is skipped without contacting the client.

    Most of the corpus is unmarked, so this must not cost a round trip.
    """
    fixture.rpc = None
    client = MagicMock()

    verify_rpc_expectations(client, fixture)

    client.post_batch_request.assert_not_called()


def test_missing_required_field_fails(fixture: BlockchainFixture) -> None:
    """A response missing a required field is rejected."""
    assert fixture.rpc is not None
    results: List[Dict[str, Any]] = [dict(call.result) for call in fixture.rpc]
    del results[0]["size"]

    with pytest.raises(AssertionError, match="size"):
        verify_rpc_expectations(rpc_returning(results), fixture)


def test_zero_padded_quantity_fails(fixture: BlockchainFixture) -> None:
    """
    A client returning `0x01` where the schema demands `0x1` fails.

    This is the most likely real-world divergence, since the consensus
    encoding pads and the RPC encoding does not.
    """
    assert fixture.rpc is not None
    results = [dict(call.result) for call in fixture.rpc]
    results[0]["number"] = "0x01"

    with pytest.raises(AssertionError, match="number"):
        verify_rpc_expectations(rpc_returning(results), fixture)


def test_unexpected_error_fails(fixture: BlockchainFixture) -> None:
    """An error where a result was expected is a failure."""
    fixture.rpc = [fixture.rpc[0]]  # type: ignore[index]

    with pytest.raises(AssertionError, match="expected a result"):
        verify_rpc_expectations(erroring_rpc(-32000), fixture)


def test_expected_error_code_matches(fixture: BlockchainFixture) -> None:
    """A call expecting an error passes when the code matches."""
    fixture.rpc = [
        FixtureRPCCall(
            method="eth_getBlockByNumber",
            params=["0x99", False],
            error_code=-32000,
        )
    ]

    verify_rpc_expectations(erroring_rpc(-32000), fixture)


def test_expected_error_code_mismatch_fails(
    fixture: BlockchainFixture,
) -> None:
    """A different error code is a failure, even though both are errors."""
    fixture.rpc = [
        FixtureRPCCall(
            method="eth_getBlockByNumber",
            params=["0x99", False],
            error_code=-32602,
        )
    ]

    with pytest.raises(AssertionError, match="-32602"):
        verify_rpc_expectations(erroring_rpc(-32000), fixture)


def test_error_message_wording_is_not_compared(
    fixture: BlockchainFixture,
) -> None:
    """
    Only the error code is compared, never the message.

    Wording is client-specific and unspecified, so matching on it would
    fail conforming clients.
    """
    fixture.rpc = [
        FixtureRPCCall(
            method="eth_getBlockByNumber",
            params=["0x99", False],
            error_code=-32000,
        )
    ]

    verify_rpc_expectations(
        erroring_rpc(-32000, "totally different wording"), fixture
    )


def test_all_failures_are_reported_together() -> None:
    """
    Every mismatch surfaces in one run.

    A client that gets a field wrong usually gets it wrong everywhere, and
    the hive feedback loop is too slow to fix them one at a time.
    """
    genesis = make_header(number=0, gas_used=0)
    blocks = [
        make_block([make_transaction()], [make_receipt(21_000)], number=1),
        make_block([make_transaction()], [make_receipt(21_000)], number=2),
    ]
    built = BlockchainFixture(
        fork=Amsterdam,
        genesis=genesis,
        genesis_rlp=Bytes(b"\xc0"),
        blocks=blocks,
        last_block_hash=Hash(0),
        pre={},
        post_state={},
        config=FixtureConfig(fork=Amsterdam, chain_id=1),
    )
    built.rpc = derive_rpc_calls(built)
    assert built.rpc is not None

    broken = []
    for call in built.rpc:
        result = dict(call.result)
        result.pop("size", None)
        result.pop("logsBloom", None)
        broken.append(result)

    with pytest.raises(AssertionError, match=r"\d+ of \d+ RPC expectations"):
        verify_rpc_expectations(rpc_returning(broken), built)


def test_block_queried_by_number_and_hash_agree(
    fixture: BlockchainFixture,
) -> None:
    """The two block lookups assert the same object."""
    assert fixture.rpc is not None
    block = fixture.blocks[0]
    expected = block_response(block).to_rpc()  # type: ignore[arg-type]

    for call in fixture.rpc:
        if call.method in ("eth_getBlockByNumber", "eth_getBlockByHash"):
            assert call.result == expected
