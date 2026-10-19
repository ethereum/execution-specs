"""Test suite for invalid blocks in ``make_stateful_fixture``."""

from types import SimpleNamespace
from typing import Any, Dict, Iterator, List

import pytest

from execution_testing.base_types import Address, Bloom, Hash
from execution_testing.client_clis import ClientBackend, TransitionTool
from execution_testing.client_clis.cli_types import (
    EnginePayloadMetadata,
    LazyAllocJson,
    Result,
)
from execution_testing.client_clis.client_backend import (
    ClientBackendExceptionMapper,
)
from execution_testing.exceptions import BlockException
from execution_testing.fixtures.blockchain import (
    BlockchainEngineStatefulFixture,
    FixtureExecutionPayload,
    FixtureHeader,
)
from execution_testing.forks import Osaka
from execution_testing.rpc.rpc_types import GetPayloadResponse
from execution_testing.test_types import (
    Alloc,
    Environment,
    TestPhase,
    Transaction,
)

from ..blockchain import (
    Block,
    BlockchainTest,
    Header,
    TestingBuildBlock,
    validate_stateful_blocks,
)

FORK = Osaka
START_BLOCK_NUMBER = 1
CLIENT_GAS_LIMIT = 30_000_000
ENV_GAS_LIMIT = 36_000_000
GAS_USED = 21_000


def _header(number: int) -> FixtureHeader:
    """Build the header the client seals for block ``number``."""
    return FixtureHeader(
        fork=FORK,
        fee_recipient=Address(0),
        state_root=Hash(0),
        number=number,
        gas_limit=CLIENT_GAS_LIMIT,
        gas_used=GAS_USED,
        timestamp=number * 12,
        extra_data=b"\x00",
        base_fee_per_gas=7,
        withdrawals_root=Hash(0),
        blob_gas_used=0,
        excess_blob_gas=0,
        parent_beacon_block_root=Hash(0),
        requests_hash=Hash(0),
    )


def _tx(phase: TestPhase) -> Transaction:
    """Build a Transaction tagged with the given test phase."""
    tx = Transaction()
    tx.test_phase = phase
    return tx


def _built_block(
    number: int, block: Block, **header_changes: Any
) -> TestingBuildBlock:
    """
    Build the ``TestingBuildBlock`` that ``generate_block_data`` returns.

    The payload is what the client sealed. The header is fill's own: it
    takes ``gas_limit`` from the test environment, so it differs from the
    client's, and it already has ``rlp_modifier`` applied.
    """
    client_header = _header(number)
    payload = FixtureExecutionPayload.from_fixture_header(
        header=client_header,
        transactions=[],
        withdrawals=None,
    )
    header = client_header.copy(gas_limit=ENV_GAS_LIMIT, **header_changes)
    if block.rlp_modifier is not None:
        header = block.rlp_modifier.apply(header)
    new_payload_version = FORK.engine_new_payload_version()
    forkchoice_updated_version = FORK.engine_forkchoice_updated_version()
    assert new_payload_version is not None
    assert forkchoice_updated_version is not None
    return TestingBuildBlock(
        header=header,
        env=Environment(number=number, timestamp=number * 12),
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
            payload_response=GetPayloadResponse(execution_payload=payload),
            new_payload_version=new_payload_version,
            forkchoice_updated_version=forkchoice_updated_version,
            parent_beacon_block_root=Hash(0),
        ),
    )


def _invalid_block(**modifier: Any) -> Block:
    """Build an execution block whose header understates ``gas_used``."""
    return Block(
        txs=[_tx(TestPhase.EXECUTION)],
        rlp_modifier=Header(gas_used=GAS_USED - 1, **modifier),
        exception=BlockException.INVALID_GAS_USED,
    )


@pytest.fixture
def client_backend() -> ClientBackend:
    """Stub ``ClientBackend`` with snapshot/start blocks pre-captured."""
    # ``__new__`` skips ``__init__``: no live RPC endpoints are needed
    # because ``generate_block_data`` is monkeypatched below.
    backend = ClientBackend.__new__(ClientBackend)
    start_header = _header(START_BLOCK_NUMBER)
    block_dict = start_header.model_dump(
        by_alias=True, mode="json", exclude_none=True
    )
    block_dict["hash"] = str(start_header.block_hash)
    backend.fork = FORK
    backend.snapshot_block = block_dict
    backend.start_block = block_dict
    backend.extract_opcode_count = False
    backend.debug_rpc = None
    return backend


def _fill_stateful(
    monkeypatch: pytest.MonkeyPatch,
    client_backend: ClientBackend,
    blocks: List[Block],
) -> BlockchainEngineStatefulFixture:
    """Run ``make_stateful_fixture`` over ``blocks`` with a stub client."""
    block_numbers: Iterator[int] = iter(
        range(START_BLOCK_NUMBER + 1, START_BLOCK_NUMBER + 1 + len(blocks))
    )

    def fake_generate_block_data(
        _self: BlockchainTest, *, block: Block, **_kwargs: Any
    ) -> TestingBuildBlock:
        return _built_block(next(block_numbers), block)

    monkeypatch.setattr(
        BlockchainTest, "generate_block_data", fake_generate_block_data
    )
    test = BlockchainTest(fork=FORK, pre=Alloc(), post=Alloc(), blocks=blocks)
    fixture = test.make_stateful_fixture(client_backend).fixture
    assert isinstance(fixture, BlockchainEngineStatefulFixture)
    return fixture


def test_invalid_payload_has_modified_header_and_valid_hash() -> None:
    """
    The payload carries the modified field and a ``block_hash`` over the
    client's sealed header, not over fill's diverging one.
    """
    block = _invalid_block()
    built_block = _built_block(START_BLOCK_NUMBER + 1, block)

    payload = built_block.get_fixture_engine_new_payload(
        phase=TestPhase.EXECUTION
    )

    execution_payload = payload.params[0]
    expected_header = _header(START_BLOCK_NUMBER + 1).copy(
        gas_used=GAS_USED - 1
    )
    assert execution_payload.gas_used == GAS_USED - 1
    assert execution_payload.gas_limit == CLIENT_GAS_LIMIT
    assert execution_payload.block_hash == expected_header.block_hash
    assert payload.validation_error == BlockException.INVALID_GAS_USED
    assert payload.phase == TestPhase.EXECUTION


def test_invalid_payload_serializes_validation_error() -> None:
    """The fixture JSON names the expected exception on the payload."""
    block = _invalid_block()
    payload = _built_block(
        START_BLOCK_NUMBER + 1, block
    ).get_fixture_engine_new_payload()

    data: Dict[str, Any] = payload.model_dump(mode="json", by_alias=True)

    assert data["validationError"] == "BlockException.INVALID_GAS_USED"


def test_header_mismatch_outside_payload_raises() -> None:
    """
    A header field the payload does not carry must match the client's,
    or the recomputed hash would not describe the block it sealed.
    """
    block = _invalid_block()
    built_block = _built_block(
        START_BLOCK_NUMBER + 1, block, parent_beacon_block_root=Hash(1)
    )

    with pytest.raises(ValueError, match="hashes to"):
        built_block.get_fixture_engine_new_payload()


def test_invalid_block_keeps_head_on_last_valid_block(
    monkeypatch: pytest.MonkeyPatch, client_backend: ClientBackend
) -> None:
    """
    The invalid block lands in ``engineNewPayloads``, but
    ``lastblockhash`` stays on the last block the client accepts.
    """
    fixture = _fill_stateful(
        monkeypatch,
        client_backend,
        blocks=[Block(txs=[_tx(TestPhase.SETUP)]), _invalid_block()],
    )

    assert len(fixture.setup_payloads) == 1
    assert len(fixture.payloads) == 1
    setup_hash = fixture.setup_payloads[0].params[0].block_hash
    assert fixture.last_block_hash == setup_hash
    assert (
        fixture.payloads[0].validation_error == BlockException.INVALID_GAS_USED
    )


def test_block_after_invalid_block_builds_on_last_valid_block(
    monkeypatch: pytest.MonkeyPatch, client_backend: ClientBackend
) -> None:
    """A block after a rejected one gets the rejected block's parent."""
    parent_envs: List[Environment] = []
    block_numbers = iter(range(START_BLOCK_NUMBER + 1, START_BLOCK_NUMBER + 4))

    def fake_generate_block_data(
        _self: BlockchainTest,
        *,
        block: Block,
        previous_env: Environment,
        **_kwargs: Any,
    ) -> TestingBuildBlock:
        parent_envs.append(previous_env)
        return _built_block(next(block_numbers), block)

    monkeypatch.setattr(
        BlockchainTest, "generate_block_data", fake_generate_block_data
    )
    test = BlockchainTest(
        fork=FORK,
        pre=Alloc(),
        post=Alloc(),
        blocks=[
            Block(txs=[_tx(TestPhase.SETUP)]),
            _invalid_block(),
            Block(txs=[_tx(TestPhase.EXECUTION)]),
        ],
    )

    fixture = test.make_stateful_fixture(client_backend).fixture

    assert isinstance(fixture, BlockchainEngineStatefulFixture)
    assert parent_envs[2] is parent_envs[1]
    assert fixture.last_block_hash == fixture.payloads[1].params[0].block_hash


@pytest.mark.parametrize(
    "block,reason",
    [
        pytest.param(
            Block(
                txs=[_tx(TestPhase.EXECUTION)],
                exception=BlockException.INVALID_GAS_USED,
            ),
            "no `rlp_modifier`",
            id="no_rlp_modifier",
        ),
        pytest.param(
            _invalid_block(withdrawals_root=Hash(1)),
            "withdrawals_root",
            id="field_not_in_payload",
        ),
        pytest.param(
            _invalid_block(blob_gas_used=Header.REMOVE_FIELD),
            "removes",
            id="removed_field",
        ),
        pytest.param(
            Block(
                txs=[_tx(TestPhase.SETUP)],
                rlp_modifier=Header(gas_used=1),
                exception=BlockException.INVALID_GAS_USED,
            ),
            "setup-phase",
            id="setup_phase",
        ),
        pytest.param(
            Block(
                txs=[_tx(TestPhase.EXECUTION)],
                rlp_modifier=Header(gas_used=1),
            ),
            "no `exception`",
            id="modifier_without_exception",
        ),
    ],
)
def test_unsupported_invalid_block_raises(block: Block, reason: str) -> None:
    """An invalid block the client cannot help produce is refused."""
    with pytest.raises(NotImplementedError, match=reason):
        validate_stateful_blocks([block])


def test_unsupported_invalid_block_raises_before_any_build(
    monkeypatch: pytest.MonkeyPatch, client_backend: ClientBackend
) -> None:
    """No block reaches the client when a later block is unsupported."""
    built: List[Block] = []

    def fake_generate_block_data(
        _self: BlockchainTest, *, block: Block, **_kwargs: Any
    ) -> TestingBuildBlock:
        built.append(block)
        return _built_block(START_BLOCK_NUMBER + len(built), block)

    monkeypatch.setattr(
        BlockchainTest, "generate_block_data", fake_generate_block_data
    )
    test = BlockchainTest(
        fork=FORK,
        pre=Alloc(),
        post=Alloc(),
        blocks=[
            Block(txs=[_tx(TestPhase.SETUP)]),
            Block(
                txs=[_tx(TestPhase.EXECUTION)],
                exception=BlockException.INVALID_GAS_USED,
            ),
        ],
    )

    with pytest.raises(NotImplementedError):
        test.make_stateful_fixture(client_backend)
    assert built == []


@pytest.mark.parametrize("expect_invalid", [False, True])
def test_client_backend_imports_only_valid_blocks(
    monkeypatch: pytest.MonkeyPatch,
    client_backend: ClientBackend,
    expect_invalid: bool,
) -> None:
    """
    ``evaluate`` imports a built block (and reads its receipts) unless
    the test expects that block to be invalid.
    """
    header = _header(START_BLOCK_NUMBER + 1)
    payload = FixtureExecutionPayload.from_fixture_header(
        header=header, transactions=[], withdrawals=None
    )
    calls: List[str] = []

    def fake_fetch_receipts(*_args: Any) -> List[Any]:
        calls.append("receipts")
        return []

    client_backend.testing_rpc = SimpleNamespace(  # type: ignore[assignment]
        build_block=lambda **_kwargs: GetPayloadResponse(
            execution_payload=payload
        )
    )
    monkeypatch.setattr(
        client_backend,
        "_payload_attributes",
        lambda *_args: SimpleNamespace(parent_beacon_block_root=Hash(0)),
    )
    monkeypatch.setattr(
        client_backend,
        "_finalize",
        lambda *_args, **_kwargs: calls.append("finalize"),
    )
    monkeypatch.setattr(client_backend, "_fetch_receipts", fake_fetch_receipts)

    output = client_backend.evaluate(
        transition_tool_data=TransitionTool.TransitionToolData(
            alloc=Alloc(),
            txs=[],
            env=Environment(number=START_BLOCK_NUMBER + 1),
            fork=FORK,
            chain_id=1,
            reward=0,
            blob_schedule=None,
            expect_invalid=expect_invalid,
        ),
    )

    assert calls == ([] if expect_invalid else ["finalize", "receipts"])
    assert output.result.gas_used == GAS_USED


def test_generate_block_data_accepts_invalid_block_without_receipts(
    monkeypatch: pytest.MonkeyPatch,
    client_backend: ClientBackend,
) -> None:
    """
    An expected-invalid block that the client built has no receipts, so
    ``generate_block_data`` must not check its transactions against them.
    """
    header = _header(START_BLOCK_NUMBER + 1)
    payload = FixtureExecutionPayload.from_fixture_header(
        header=header, transactions=[], withdrawals=None
    )
    client_backend.exception_mapper = ClientBackendExceptionMapper()
    client_backend.testing_rpc = SimpleNamespace(  # type: ignore[assignment]
        build_block=lambda **_kwargs: GetPayloadResponse(
            execution_payload=payload
        )
    )
    monkeypatch.setattr(
        client_backend,
        "_payload_attributes",
        lambda *_args: SimpleNamespace(parent_beacon_block_root=Hash(0)),
    )
    block = Block(
        txs=[Transaction(to=Address(1), gas_limit=GAS_USED)],
        rlp_modifier=Header(gas_used=GAS_USED - 1),
        exception=BlockException.INVALID_GAS_USED,
    )
    parent = _header(START_BLOCK_NUMBER)
    test = BlockchainTest(fork=FORK, pre=Alloc(), post=Alloc(), blocks=[block])

    built_block = test.generate_block_data(
        t8n=client_backend,
        block=block,
        previous_env=Environment(
            parent_timestamp=parent.timestamp,
            parent_base_fee_per_gas=parent.base_fee_per_gas,
            parent_blob_gas_used=parent.blob_gas_used,
            parent_excess_blob_gas=parent.excess_blob_gas,
            parent_gas_used=parent.gas_used,
            parent_gas_limit=parent.gas_limit,
            block_hashes={START_BLOCK_NUMBER: parent.block_hash},
        ),
        previous_alloc=Alloc(),
    )

    assert isinstance(built_block, TestingBuildBlock)
    assert built_block.result.receipts == []
