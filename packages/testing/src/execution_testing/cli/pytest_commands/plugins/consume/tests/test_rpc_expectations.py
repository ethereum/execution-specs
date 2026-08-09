"""Test replay of derived RPC expectations against a client."""

from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest

from execution_testing.base_types import Bytes, Hash
from execution_testing.cli.pytest_commands.plugins.consume.simulators.helpers.rpc_expectations import (  # noqa: E501
    verify_rpc_expectations,
)
from execution_testing.fixtures.blockchain import (
    BlockchainEngineXFixture,
    BlockchainFixture,
    FixtureConfig,
)
from execution_testing.fixtures.common import (
    FixtureForkchoiceState,
    FixtureRPCCall,
)
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


SHAPE_ONLY_ANSWERS = {
    "eth_gasPrice": "0x3b9aca00",
    "eth_maxPriorityFeePerGas": "0x0",
    "eth_syncing": False,
    "eth_getStorageValues": {},
}
"""
A schema-conformant answer for each method asserted on shape alone.

Those calls store no result — that is what makes them schema-only — so a
plausible client answer has to be supplied here instead. The values are
arbitrary on purpose: any of them satisfies the assertion, which is the
honest measure of how much it asserts.
"""


def capabilities_answer(number: str, block_hash: str) -> Dict[str, Any]:
    """
    Return a complete `eth_capabilities` response naming the given head.

    A partial expectation stores only `head`, but a *response* is still
    held to the whole schema, so the other six resources have to be here.
    Their values are a node's own configuration and nothing asserts them;
    these are what go-ethereum v1.17.6 answered under hive.
    """
    served = {"disabled": False, "oldestBlock": "0x0"}
    return {
        "head": {"number": number, "hash": block_hash},
        "state": served,
        "tx": served,
        "logs": served,
        "receipts": served,
        "blocks": served,
        "stateproofs": served,
    }


def fee_history_answer(oldest: str) -> Dict[str, Any]:
    """Return a complete `eth_feeHistory` response for a one-block range."""
    return {
        "oldestBlock": oldest,
        "baseFeePerGas": ["0x7", "0x7"],
        "gasUsedRatio": [0.0],
    }


PARTIAL_ANSWERS = {
    "eth_capabilities": lambda call: capabilities_answer(
        call.result["head"]["number"], call.result["head"]["hash"]
    ),
    "eth_feeHistory": lambda call: fee_history_answer(
        call.result["oldestBlock"]
    ),
}
"""
A complete response agreeing with each partial expectation.

Echoing the stored subset back would fail, and rightly: weakening what is
*asserted* never weakens what a conforming client must *return*. The
response is validated against the full result schema either way.
"""


def conforming_results(fixture: BlockchainFixture) -> List[Any]:
    """
    Return what a correct client would answer for each stored call.

    A digest-asserted call stores no result, so its preimage is supplied
    instead. Every such call in these fixtures reads the code of an
    account that does not exist, which is empty.
    """
    assert fixture.rpc is not None
    answers = []
    for call in fixture.rpc:
        if call.assertion == "schema":
            answers.append(SHAPE_ONLY_ANSWERS[call.method])
        elif call.assertion == "partial":
            answers.append(PARTIAL_ANSWERS[call.method](call))
        elif call.result_keccak is not None:
            answers.append("0x")
        else:
            answers.append(call.result)
    return answers


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
    client = rpc_returning(conforming_results(fixture))

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
    client = rpc_returning(conforming_results(fixture))
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

    results = [checksummed(result) for result in conforming_results(fixture)]

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
        dict(result, someUnmodelledField="0x1")
        if call.method in ("eth_getBlockByNumber", "eth_getBlockByHash")
        and isinstance(result, dict)
        else result
        for call, result in zip(
            fixture.rpc, conforming_results(fixture), strict=True
        )
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
        dict(result, someNonstandardField="0x1")
        if call.method == "eth_getTransactionReceipt"
        and isinstance(result, dict)
        else result
        for call, result in zip(
            fixture.rpc, conforming_results(fixture), strict=True
        )
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
        and str(call.params[0]).startswith("0x")
    }
    by_hash = {
        call.params[1]: call.result
        for call in fixture.rpc
        if call.method == "eth_getBlockByHash" and call.result is not None
    }

    assert set(by_number) == {False, True}
    assert by_number == by_hash


def test_expected_null_fails_when_something_is_returned(
    fixture: BlockchainFixture,
) -> None:
    """
    A lookup that should find nothing must actually find nothing.

    The zero hash names no block, so a client answering with one is
    reporting a block that does not exist.
    """
    assert fixture.rpc is not None
    nothing = str(Hash(0))
    index = next(
        i
        for i, call in enumerate(fixture.rpc)
        if call.method == "eth_getBlockByHash" and call.params[0] == nothing
    )
    results = conforming_results(fixture)
    results[index] = results[first_of(fixture, "eth_getBlockByNumber")]

    with pytest.raises(AssertionError, match="expected None"):
        verify_rpc_expectations(rpc_returning(results), fixture)


def test_expected_error_fails_when_the_call_succeeds() -> None:
    """
    A malformed request that a client accepts is a failure.

    Only the code is asserted, but its absence is asserted too: a client
    silently truncating an over-long storage key would otherwise pass.
    """
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
    built.rpc = [
        FixtureRPCCall(
            method="eth_getStorageAt",
            params=[str(make_transaction().to), "0xasdf", "0x1"],
            error_code=-32602,
        )
    ]

    with pytest.raises(AssertionError, match="got a successful response"):
        verify_rpc_expectations(rpc_returning([str(Hash(0))]), built)


def engine_fixture(
    calls: List[FixtureRPCCall],
    forkchoice: FixtureForkchoiceState | None,
) -> BlockchainEngineXFixture:
    """
    Return an engine fixture carrying the given calls and declaration.

    Payloads are irrelevant here: replay reads only the stored calls and
    the forkchoice declaration, and an empty chain keeps the fixture to
    what the assertion is about.
    """
    built = BlockchainEngineXFixture(
        fork=Amsterdam,
        last_block_hash=Hash(0),
        config=FixtureConfig(fork=Amsterdam, chain_id=1),
        pre_hash="",
        payloads=[],
    )
    built.rpc = calls
    built.rpc_forkchoice = forkchoice
    return built


def tagged_call(tag: str) -> FixtureRPCCall:
    """Return a round-trip expectation for one forkchoice tag."""
    return FixtureRPCCall(
        method="eth_getBlockTransactionCountByNumber",
        params=[tag],
        result="0x0",
        round_trip=True,
    )


DECLARATION = FixtureForkchoiceState(
    head_block_hash=Hash(3),
    safe_block_hash=Hash(2),
    finalized_block_hash=Hash(1),
)


def test_round_trip_calls_are_replayed_when_declared() -> None:
    """
    A consumer that made the declaration asserts what it implies.

    The engine simulator sends the triple in its final
    `engine_forkchoiceUpdated`, so the client has been told which blocks
    these tags name and is obliged to answer.
    """
    built = engine_fixture(
        [tagged_call("safe"), tagged_call("finalized")],
        DECLARATION,
    )
    client = rpc_returning(["0x0", "0x0"])

    verify_rpc_expectations(client, built)

    sent = client.post_batch_request.call_args.kwargs["calls"]
    assert [call.params[0] for call in sent] == ["safe", "finalized"]


def test_round_trip_calls_are_skipped_without_a_declaration() -> None:
    """
    A consumer that cannot declare the triple must not assert it.

    `consume rlp` never opens the engine port, so a client it drives has no
    safe or finalized block and answering `safe block not found` is
    correct. Sending the call anyway would fail a conforming client.
    """
    built = engine_fixture(
        [tagged_call("safe"), tagged_call("finalized")],
        None,
    )

    client = rpc_returning([])
    verify_rpc_expectations(client, built)

    client.post_batch_request.assert_not_called()


def test_derived_calls_survive_the_skip() -> None:
    """Dropping the round trips leaves everything else replayed."""
    derived = FixtureRPCCall(method="eth_blockNumber", params=[], result="0x3")
    built = engine_fixture([derived, tagged_call("safe")], None)
    client = rpc_returning(["0x3"])

    verify_rpc_expectations(client, built)

    sent = client.post_batch_request.call_args.kwargs["calls"]
    assert [call.method for call in sent] == ["blockNumber"]


def test_a_wrong_tag_answer_says_where_the_value_came_from() -> None:
    """
    A round-trip failure is labelled, not blurred in with the rest.

    Every other expectation here means "the spec says so". This one means
    "you were told so", and a client team debugging it is owed the
    difference — the answer is only correct relative to a forkchoice
    update this harness sent.
    """
    built = engine_fixture([tagged_call("safe")], DECLARATION)

    with pytest.raises(AssertionError, match="round trip") as failure:
        verify_rpc_expectations(rpc_returning(["0x1"]), built)

    assert "declared by the harness" in str(failure.value)


def shape_only_call(method: str = "eth_gasPrice") -> FixtureRPCCall:
    """Return an expectation that pins only the response's shape."""
    return FixtureRPCCall(method=method, params=[], assertion="schema")


def test_any_conformant_value_satisfies_a_schema_only_call() -> None:
    """
    The value is genuinely unasserted, not asserted against a default.

    Two clients answering different gas prices must both pass, because
    neither is wrong: the oracle is a heuristic and the spec has no
    opinion. If this ever started failing, the tier would be quietly
    asserting a value nobody derived.
    """
    built = engine_fixture([shape_only_call()], None)

    for answer in ("0x1", "0x3b9aca00", "0x0"):
        verify_rpc_expectations(rpc_returning([answer]), built)


@pytest.mark.parametrize(
    "answer",
    [
        pytest.param("0x01", id="zero_padded_quantity"),
        pytest.param(1_000_000_000, id="quantity_as_integer"),
        pytest.param("1000000000", id="missing_prefix"),
        pytest.param(None, id="null"),
    ],
)
def test_a_malformed_shape_still_fails(answer: Any) -> None:
    """
    The negative control for the weakest tier in the suite.

    A check that cannot fail is worse than no check, because it inflates
    the apparent coverage of a run. `eth_gasPrice` buys about as little as
    a schema-only assertion can — the result schema is one quantity
    pattern — so these four are the entire set of defects it can catch,
    and they are worth knowing it does catch.
    """
    built = engine_fixture([shape_only_call()], None)

    with pytest.raises(AssertionError, match="schema only") as failure:
        verify_rpc_expectations(rpc_returning([answer]), built)

    assert "eth_gasPrice" in str(failure.value)


def test_a_schema_only_failure_says_what_was_not_checked() -> None:
    """
    The label reaches the failure, not only the fixture.

    A client team told "your response is wrong" is owed the fact that only
    its shape was ever examined, so they do not go hunting for a value
    disagreement that was never asserted.
    """
    built = engine_fixture([shape_only_call()], None)

    with pytest.raises(AssertionError) as failure:
        verify_rpc_expectations(rpc_returning(["0x01"]), built)

    assert "no spec-derived value exists" in str(failure.value)


def test_a_missing_method_fails_a_schema_only_call() -> None:
    """
    An unimplemented method is a failure, not a vacuous pass.

    This is the other half of the negative control: the tier asserts the
    client answers *and* answers well-formed, so a `-32601` has to be
    caught even though no value is being compared.
    """
    built = engine_fixture([shape_only_call()], None)

    with pytest.raises(AssertionError, match="expected a result, got error"):
        verify_rpc_expectations(erroring_rpc(-32601, "no such method"), built)


HEAD_HASH = "0x" + "ab" * 32


def partial_call() -> FixtureRPCCall:
    """Return an expectation naming one field of a larger response."""
    return FixtureRPCCall(
        method="eth_capabilities",
        params=[],
        result={"head": {"number": "0x2", "hash": HEAD_HASH}},
        assertion="partial",
    )


def test_a_partial_call_ignores_the_fields_it_does_not_name() -> None:
    """
    The rest of the response is genuinely unasserted.

    A node's retention windows are its own configuration, so a client
    reporting whatever it likes for them must still pass, however far it
    strays from what any other client would say.
    """
    built = engine_fixture([partial_call()], None)
    answered = capabilities_answer("0x2", HEAD_HASH)
    answered["logs"] = {"disabled": True}
    answered["tx"]["deleteStrategy"] = {
        "type": "window",
        "retentionBlocks": "0x1",
    }

    verify_rpc_expectations(rpc_returning([answered]), built)


def test_a_partial_call_still_fails_on_a_field_it_names() -> None:
    """
    The negative control for the middle tier.

    Naming fewer fields must not weaken the ones named, or a partial
    expectation would be a schema-only one wearing a stored value.
    """
    built = engine_fixture([partial_call()], None)

    with pytest.raises(AssertionError, match="partial value") as failure:
        verify_rpc_expectations(
            rpc_returning([capabilities_answer("0x3", HEAD_HASH)]), built
        )

    assert "head/number: expected '0x2', got '0x3'" in str(failure.value)


def test_a_partial_call_still_holds_the_whole_response_to_the_schema() -> None:
    """
    Weakening what is asserted does not weaken what must be returned.

    A partial expectation says the spec cannot compute the other fields,
    not that a client may omit them. Dropping a required one is still a
    shape violation.
    """
    built = engine_fixture([partial_call()], None)
    answered = capabilities_answer("0x2", HEAD_HASH)
    del answered["blocks"]

    with pytest.raises(AssertionError, match="'blocks' is a required"):
        verify_rpc_expectations(rpc_returning([answered]), built)


def test_a_partial_call_fails_when_its_field_is_absent() -> None:
    """A field we assert must be present, not merely not contradicted."""
    built = engine_fixture([partial_call()], None)
    answered = capabilities_answer("0x2", HEAD_HASH)
    del answered["head"]["number"]

    with pytest.raises(AssertionError, match="required|missing"):
        verify_rpc_expectations(rpc_returning([answered]), built)
