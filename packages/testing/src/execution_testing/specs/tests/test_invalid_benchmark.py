"""Test suite for invalid blocks in ``fill-stateful`` benchmarks."""

from typing import Any

import pytest

from execution_testing.base_types import Address, Bloom, Bytes, Hash
from execution_testing.client_clis.cli_types import (
    EnginePayloadMetadata,
    LazyAllocJson,
    Result,
)
from execution_testing.exceptions import BlockException
from execution_testing.fixtures.blockchain import (
    FixtureExecutionPayload,
    FixtureHeader,
)
from execution_testing.forks import Osaka
from execution_testing.rpc.rpc_types import GetPayloadResponse
from execution_testing.test_types import (
    BlockAccessListExpectation,
    Environment,
    TestPhase,
    Transaction,
)

from ..blockchain import (
    Block,
    Header,
    TestingBuildBlock,
    validate_stateful_blocks,
)

FORK = Osaka
BLOCK_NUMBER = 2
CLIENT_GAS_LIMIT = 30_000_000
ENV_GAS_LIMIT = 36_000_000
GAS_USED = 21_000


def _sealed_header(**overrides: Any) -> FixtureHeader:
    """Build the header the client seals for the test block."""
    header = FixtureHeader(
        fork=FORK,
        fee_recipient=Address(0),
        state_root=Hash(0),
        number=BLOCK_NUMBER,
        gas_limit=CLIENT_GAS_LIMIT,
        gas_used=GAS_USED,
        timestamp=BLOCK_NUMBER * 12,
        extra_data=b"\x00",
        base_fee_per_gas=7,
        withdrawals_root=Hash(0),
        blob_gas_used=0,
        excess_blob_gas=0,
        parent_beacon_block_root=Hash(0),
        requests_hash=Hash(0),
    )
    return header.copy(**overrides) if overrides else header


def _tx(phase: TestPhase) -> Transaction:
    """Build a transaction tagged with ``phase``."""
    return Transaction(test_phase=phase)


def _invalid_block(**modifier_fields: Any) -> Block:
    """Build an execution block whose header understates ``gas_used``."""
    return Block(
        txs=[_tx(TestPhase.EXECUTION)],
        rlp_modifier=Header(gas_used=GAS_USED - 1, **modifier_fields),
        exception=BlockException.INVALID_GAS_USED,
    )


def _built_block(
    block: Block, **fill_header_changes: Any
) -> TestingBuildBlock:
    """
    Build what the client backend hands back for ``block``.

    The engine payload is the block the client sealed; ``header`` is
    fill's own view of it, which takes ``gas_limit`` from the test
    environment and already carries ``rlp_modifier``.
    """
    sealed = _sealed_header()
    header = sealed.copy(gas_limit=ENV_GAS_LIMIT, **fill_header_changes)
    if block.rlp_modifier is not None:
        header = block.rlp_modifier.apply(header)
    new_payload_version = FORK.engine_new_payload_version()
    forkchoice_updated_version = FORK.engine_forkchoice_updated_version()
    assert new_payload_version is not None
    assert forkchoice_updated_version is not None
    return TestingBuildBlock(
        header=header,
        env=Environment(number=BLOCK_NUMBER, timestamp=BLOCK_NUMBER * 12),
        alloc=LazyAllocJson(raw={}, _state_root=Hash(0)),
        state_root=Hash(0),
        txs=[],
        ommers=[],
        withdrawals=None,
        requests=None,
        result=Result(
            state_root=Hash(0),
            transactions_trie=Hash(0),
            receipts_root=Hash(0),
            logs_hash=Hash(0),
            logs_bloom=Bloom(0),
            receipts=[],
            gas_used=GAS_USED,
        ),
        fork=FORK,
        block_access_list=None,
        expected_exception=block.exception,
        rlp_modifier=block.rlp_modifier,
        engine_payload=EnginePayloadMetadata(
            payload_response=GetPayloadResponse(
                execution_payload=(
                    FixtureExecutionPayload.from_fixture_header(
                        header=sealed, transactions=[], withdrawals=None
                    )
                )
            ),
            new_payload_version=new_payload_version,
            forkchoice_updated_version=forkchoice_updated_version,
            parent_beacon_block_root=Hash(0),
        ),
    )


def test_corruption_only_touches_the_modified_field() -> None:
    """The rest of the payload stays as the client sealed it."""
    built = _built_block(_invalid_block())
    sealed = built.engine_payload.payload_response.execution_payload

    payload = built.corrupted_execution_payload()

    untouched = {"gas_used", "block_hash"}
    assert payload.gas_used == GAS_USED - 1
    assert payload.gas_limit == CLIENT_GAS_LIMIT
    assert payload.model_dump(
        mode="json", by_alias=True, exclude=untouched
    ) == sealed.model_dump(mode="json", by_alias=True, exclude=untouched)


def test_corrupted_payload_hashes_to_the_corrupted_block() -> None:
    """
    The payload hashes to the client's block with the field rewritten, so
    a client has to reach the corrupted field to reject it.
    """
    built = _built_block(_invalid_block())
    sealed = built.engine_payload.payload_response.execution_payload

    payload = built.corrupted_execution_payload()

    assert (
        payload.block_hash == _sealed_header(gas_used=GAS_USED - 1).block_hash
    )
    assert payload.block_hash != sealed.block_hash


def test_header_field_outside_the_payload_must_match_the_client() -> None:
    """Refuse a payload whose hash would not describe the sealed block."""
    built = _built_block(_invalid_block(), parent_beacon_block_root=Hash(1))

    with pytest.raises(ValueError, match="hashes to"):
        built.corrupted_execution_payload()


def test_valid_block_forwards_what_the_client_sealed() -> None:
    """A block with no expected exception is handed over untouched."""
    built = _built_block(Block(txs=[_tx(TestPhase.EXECUTION)]))

    payload = built.get_fixture_engine_new_payload()

    assert (
        payload.params[0]
        is built.engine_payload.payload_response.execution_payload
    )
    assert payload.validation_error is None


def test_corruption_leaves_the_other_engine_params_alone() -> None:
    """Only the execution payload differs from the valid block's call."""
    invalid = _built_block(_invalid_block()).get_fixture_engine_new_payload()
    valid = _built_block(
        Block(txs=[_tx(TestPhase.EXECUTION)])
    ).get_fixture_engine_new_payload()

    assert invalid.params[1:] == valid.params[1:]
    assert invalid.new_payload_version == valid.new_payload_version
    assert (
        invalid.forkchoice_updated_version == valid.forkchoice_updated_version
    )


def test_expected_exception_reaches_the_fixture() -> None:
    """The fixture payload names the exception and the test phase."""
    built = _built_block(_invalid_block())

    payload = built.get_fixture_engine_new_payload(phase=TestPhase.EXECUTION)

    assert payload.validation_error == BlockException.INVALID_GAS_USED
    assert payload.phase == TestPhase.EXECUTION
    assert (
        payload.model_dump(mode="json", by_alias=True)["validationError"]
        == "BlockException.INVALID_GAS_USED"
    )


@pytest.mark.parametrize(
    "block,evaluated",
    [
        pytest.param(Block(txs=[_tx(TestPhase.EXECUTION)]), True, id="valid"),
        pytest.param(_invalid_block(), False, id="invalid"),
    ],
)
def test_only_an_imported_block_has_transactions_to_verify(
    block: Block, evaluated: bool
) -> None:
    """A block the client never imports leaves no receipts behind."""
    assert _built_block(block).transactions_evaluated is evaluated


@pytest.mark.parametrize(
    "block,reason",
    [
        pytest.param(
            Block(
                txs=[_tx(TestPhase.EXECUTION)],
                exception=BlockException.INVALID_GAS_USED,
            ),
            "no `rlp_modifier`",
            id="exception_without_modifier",
        ),
        pytest.param(
            Block(
                txs=[_tx(TestPhase.EXECUTION)],
                rlp_modifier=Header(gas_used=GAS_USED - 1),
            ),
            "no `exception`",
            id="modifier_without_exception",
        ),
        pytest.param(
            _invalid_block(withdrawals_root=Hash(1)),
            "withdrawals_root",
            id="field_outside_the_payload",
        ),
        pytest.param(
            _invalid_block(blob_gas_used=Header.REMOVE_FIELD),
            "removes",
            id="removed_field",
        ),
        pytest.param(
            _invalid_block().copy(requests=[Bytes(b"\x00")]),
            "overrides `requests`",
            id="requests_override",
        ),
        pytest.param(
            _invalid_block().copy(engine_new_payload_slot_number=1),
            "engine_new_payload_slot_number",
            id="payload_only_override",
        ),
        pytest.param(
            _invalid_block().copy(
                expected_block_access_list=(
                    BlockAccessListExpectation().modify(lambda bal: bal)
                )
            ),
            "block access list",
            id="block_access_list_modifier",
        ),
        pytest.param(
            Block(
                txs=[_tx(TestPhase.SETUP)],
                rlp_modifier=Header(gas_used=GAS_USED - 1),
                exception=BlockException.INVALID_GAS_USED,
            ),
            "setup-phase",
            id="setup_phase_block",
        ),
    ],
)
def test_unfillable_block_is_refused(block: Block, reason: str) -> None:
    """An invalid block the client cannot help produce is refused."""
    with pytest.raises(NotImplementedError, match=reason):
        validate_stateful_blocks([block])


def test_refusal_names_the_block_it_cannot_fill() -> None:
    """The refusal points at the offending block."""
    blocks = [
        Block(txs=[_tx(TestPhase.SETUP)]),
        Block(
            txs=[_tx(TestPhase.EXECUTION)],
            exception=BlockException.INVALID_GAS_USED,
        ),
    ]

    with pytest.raises(NotImplementedError, match="block 1"):
        validate_stateful_blocks(blocks)


def test_fillable_blocks_pass_the_gate() -> None:
    """A header-corrupted invalid block is fillable."""
    validate_stateful_blocks(
        [Block(txs=[_tx(TestPhase.SETUP)]), _invalid_block()]
    )
