"""Test replay of derived RPC expectations against a client."""

from typing import Any, List
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
    derive_rpc_calls,
)
from execution_testing.rpc.serialization.tests.test_projection import (
    make_block,
    make_header,
    make_log,
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


def results_of(fixture: BlockchainFixture) -> List[Any]:
    """
    Copy a fixture's expected results, ready to be perturbed.

    Not every result is an object: transaction counts are quantities and
    `eth_getBlockReceipts` is a list, so a blanket `dict()` would fail.
    """
    assert fixture.rpc is not None
    return [
        dict(call.result) if isinstance(call.result, dict) else call.result
        for call in fixture.rpc
    ]


def first_of(fixture: BlockchainFixture, method: str) -> int:
    """Return the index of the first call to the named method."""
    assert fixture.rpc is not None
    return next(
        i for i, call in enumerate(fixture.rpc) if call.method == method
    )


def rpc_returning(results: List[Any]) -> MagicMock:
    """Return a mock client whose batch call yields the given responses."""
    client = MagicMock()
    client.namespace = "eth"
    client.post_batch_request.return_value = [
        MagicMock(result=result, error=None) for result in results
    ]
    return client


def erroring_rpc(code: int, message: str = "boom") -> MagicMock:
    """Return a mock client whose batch call yields a JSON-RPC error."""
    client = MagicMock()
    client.namespace = "eth"
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


def test_namespace_is_stripped_before_sending(
    fixture: BlockchainFixture,
) -> None:
    """
    Sent methods are unqualified, because the client re-adds its namespace.

    Fixtures store the wire name, so passing it through unchanged produces
    `eth_eth_getBlockByNumber` and every call fails with -32601. A mock
    accepts anything, so only a real client exposes this.
    """
    assert fixture.rpc is not None
    client = rpc_returning([call.result for call in fixture.rpc])
    client.namespace = "eth"

    verify_rpc_expectations(client, fixture)

    sent = client.post_batch_request.call_args.kwargs["calls"]
    assert sent, "nothing was sent"
    assert not any(call.method.startswith("eth_") for call in sent)
    assert "getBlockByNumber" in {call.method for call in sent}


def test_foreign_namespace_is_rejected(fixture: BlockchainFixture) -> None:
    """
    A method outside the client's namespace fails loudly.

    `debug_getRawBlock` cannot go through an `eth` client, and silently
    mangling it into `eth_debug_getRawBlock` would report a spurious
    -32601 against the client instead of naming our own mistake.
    """
    fixture.rpc = [FixtureRPCCall(method="debug_getRawBlock", params=["0x1"])]
    client = rpc_returning([None])
    client.namespace = "eth"

    with pytest.raises(ValueError, match="debug"):
        verify_rpc_expectations(client, fixture)


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
    results = results_of(fixture)
    del results[first_of(fixture, "eth_getBlockByNumber")]["size"]

    with pytest.raises(AssertionError, match="size"):
        verify_rpc_expectations(rpc_returning(results), fixture)


def test_zero_padded_quantity_fails(fixture: BlockchainFixture) -> None:
    """
    A client returning `0x01` where the schema demands `0x1` fails.

    This is the most likely real-world divergence, since the consensus
    encoding pads and the RPC encoding does not.
    """
    assert fixture.rpc is not None
    results = results_of(fixture)
    results[first_of(fixture, "eth_getBlockByNumber")]["number"] = "0x01"

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
        result = call.result
        if isinstance(result, dict):
            result = {
                k: v
                for k, v in result.items()
                if k not in ("size", "logsBloom")
            }
        broken.append(result)

    with pytest.raises(AssertionError, match=r"\d+ of \d+ RPC expectations"):
        verify_rpc_expectations(rpc_returning(broken), built)


def test_wrong_value_of_right_shape_fails(
    fixture: BlockchainFixture,
) -> None:
    """
    A schema-valid but incorrect value is caught.

    This is the case schema validation alone cannot see, and the entire
    reason the expectation is stored rather than recomputed.
    """
    assert fixture.rpc is not None
    results = results_of(fixture)
    results[first_of(fixture, "eth_getBlockByNumber")]["gasUsed"] = "0x1234"

    with pytest.raises(AssertionError, match="gasUsed"):
        verify_rpc_expectations(rpc_returning(results), fixture)


def test_difference_names_the_path(fixture: BlockchainFixture) -> None:
    """A nested mismatch reports where it is, not just that it exists."""
    assert fixture.rpc is not None
    results = results_of(fixture)
    receipt = next(r for r in results if isinstance(r, dict) and "logs" in r)
    receipt["cumulativeGasUsed"] = "0xdead"

    with pytest.raises(AssertionError) as raised:
        verify_rpc_expectations(rpc_returning(results), fixture)

    assert "cumulativeGasUsed: expected" in str(raised.value)


def test_checksummed_addresses_are_accepted(
    fixture: BlockchainFixture,
) -> None:
    """
    A client returning EIP-55 addresses passes.

    The schema's address pattern permits mixed case, so byte-wise
    comparison would fail a conforming client.
    """
    assert fixture.rpc is not None

    def checksummed(value: Any) -> Any:
        if isinstance(value, str) and len(value) == 42:
            return value.upper().replace("0X", "0x")
        if isinstance(value, dict):
            return {k: checksummed(v) for k, v in value.items()}
        if isinstance(value, list):
            return [checksummed(v) for v in value]
        return value

    results = [checksummed(call.result) for call in fixture.rpc]

    verify_rpc_expectations(rpc_returning(results), fixture)


def test_unasserted_block_fields_are_ignored(
    fixture: BlockchainFixture,
) -> None:
    """
    A block field the projection does not model is not a client error.

    Geth returns `withdrawals`, which the projection omits; failing on it
    would report our own incompleteness as a client bug. The block schema
    permits additional properties, so this is legal for a client to do.
    """
    assert fixture.rpc is not None
    results = [
        dict(call.result, someUnmodelledField="0x1")
        if call.method in ("eth_getBlockByNumber", "eth_getBlockByHash")
        else call.result
        for call in fixture.rpc
    ]

    verify_rpc_expectations(rpc_returning(results), fixture)


def test_unknown_receipt_field_is_rejected(
    fixture: BlockchainFixture,
) -> None:
    """
    A receipt carrying an unmodelled field fails, unlike a block.

    The receipt schema sets `additionalProperties: false`, so the two are
    genuinely different and the schema layer is what draws the line.
    """
    assert fixture.rpc is not None
    results = [
        dict(call.result, someNonstandardField="0x1")
        if call.method == "eth_getTransactionReceipt"
        else call.result
        for call in fixture.rpc
    ]

    with pytest.raises(AssertionError, match="Additional properties"):
        verify_rpc_expectations(rpc_returning(results), fixture)


def test_missing_asserted_field_fails(fixture: BlockchainFixture) -> None:
    """
    Omitting a field we assert fails even when the schema allows its
    absence.

    `difficulty` is optional in the schema, so only the stored expectation
    can require it — exactly the gap exact comparison exists to close.
    """
    assert fixture.rpc is not None
    results = results_of(fixture)
    del results[first_of(fixture, "eth_getBlockByNumber")]["difficulty"]

    with pytest.raises(AssertionError, match="difficulty: missing"):
        verify_rpc_expectations(rpc_returning(results), fixture)


def test_dropped_log_entry_fails() -> None:
    """A response omitting a log is caught, by length before value."""
    genesis = make_header(number=0, gas_used=0)
    block = make_block(
        [make_transaction()],
        [make_receipt(21_000, logs=[make_log(1), make_log(2)])],
    )
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
    assert built.rpc is not None

    results = []
    for call in built.rpc:
        result = call.result
        if isinstance(result, dict) and result.get("logs"):
            result = dict(result, logs=result["logs"][:1])
        results.append(result)

    with pytest.raises(AssertionError, match="entries"):
        verify_rpc_expectations(rpc_returning(results), built)


def test_reported_differences_are_capped() -> None:
    """
    A badly wrong response reports a bounded number of differences.

    Without a cap, one broken call buries every other failure in the run.
    Each log's `data` is schema-valid here, so the schema layer passes and
    the differences all come from the value comparison.
    """
    genesis = make_header(number=0, gas_used=0)
    logs = [make_log(topic) for topic in range(15)]
    block = make_block([make_transaction()], [make_receipt(21_000, logs=logs)])
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
    assert built.rpc is not None

    results = []
    for call in built.rpc:
        result = call.result
        if isinstance(result, dict) and result.get("logs"):
            result = dict(
                result,
                logs=[dict(log, data="0xbeef") for log in result["logs"]],
            )
        results.append(result)

    with pytest.raises(AssertionError, match="and 5 more"):
        verify_rpc_expectations(rpc_returning(results), built)


def test_block_queried_by_number_and_hash_agree(
    fixture: BlockchainFixture,
) -> None:
    """The two block lookups assert the same object."""
    assert fixture.rpc is not None
    by_number = {
        call.params[1]: call.result
        for call in fixture.rpc
        if call.method == "eth_getBlockByNumber"
    }
    by_hash = {
        call.params[1]: call.result
        for call in fixture.rpc
        if call.method == "eth_getBlockByHash"
    }

    assert set(by_number) == {False, True}
    assert by_number == by_hash
