"""Test suite for receipt-status verification in ``make_stateful_fixture``."""

from typing import Any, Iterator, List

import pytest

from execution_testing.base_types import Address, Bloom, Hash
from execution_testing.client_clis import ClientBackend
from execution_testing.client_clis.cli_types import (
    EnginePayloadMetadata,
    LazyAllocJson,
    Result,
)
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
from execution_testing.test_types.receipt_types import TransactionReceipt

from ..base import FillResult
from ..blockchain import Block, BlockchainTest, TestingBuildBlock

FORK = Osaka
START_BLOCK_NUMBER = 1


def _header(number: int) -> FixtureHeader:
    """Build a minimal valid header for the test fork."""
    return FixtureHeader(
        fork=FORK,
        fee_recipient=Address(0),
        state_root=Hash(0),
        number=number,
        gas_limit=30_000_000,
        gas_used=21_000,
        bloom=0,
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


def _built_block(number: int, statuses: List[int]) -> TestingBuildBlock:
    """
    Build a ``TestingBuildBlock`` whose receipts carry ``statuses``,
    mimicking what ``ClientBackend.evaluate`` assembles from a live
    client's ``testing_buildBlockV1`` + ``eth_getTransactionReceipt``.
    """
    header = _header(number)
    payload = FixtureExecutionPayload.from_fixture_header(
        header=header,
        transactions=[],
        withdrawals=None,
    )
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
            receipts=[TransactionReceipt(status=s) for s in statuses],
            gas_used=21_000,
        ),
        fork=FORK,
        block_access_list=None,
        engine_payload=EnginePayloadMetadata(
            payload_response=GetPayloadResponse(execution_payload=payload),
            new_payload_version=new_payload_version,
            forkchoice_updated_version=forkchoice_updated_version,
            parent_beacon_block_root=Hash(0),
        ),
    )


@pytest.fixture
def client_backend() -> ClientBackend:
    """
    Stub ``ClientBackend`` with snapshot/start blocks pre-captured.
    """
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
    statuses_per_block: List[List[int]],
    phases: List[TestPhase],
    **kwargs: Any,
) -> FillResult:
    """
    Run ``make_stateful_fixture`` with one block per entry of ``phases``,
    stubbing ``generate_block_data`` to return receipts with the matching
    ``statuses_per_block`` entry.
    """
    assert len(statuses_per_block) == len(phases)
    calls: Iterator[List[int]] = iter(statuses_per_block)
    block_numbers = iter(
        range(START_BLOCK_NUMBER + 1, START_BLOCK_NUMBER + 1 + len(phases))
    )

    def fake_generate_block_data(
        _self: BlockchainTest, **_kwargs: Any
    ) -> TestingBuildBlock:
        return _built_block(next(block_numbers), next(calls))

    monkeypatch.setattr(
        BlockchainTest, "generate_block_data", fake_generate_block_data
    )
    test = BlockchainTest(
        fork=FORK,
        pre=Alloc(),
        post=Alloc(),
        blocks=[Block(txs=[_tx(phase)]) for phase in phases],
        **kwargs,
    )
    return test.make_stateful_fixture(client_backend)


def test_execution_status_mismatch_raises(
    monkeypatch: pytest.MonkeyPatch, client_backend: ClientBackend
) -> None:
    """A status-0 receipt with ``expected_receipt_status=1`` must throw."""
    with pytest.raises(Exception, match=r"receipt status 0, expected 1"):
        _fill_stateful(
            monkeypatch,
            client_backend,
            statuses_per_block=[[0]],
            phases=[TestPhase.EXECUTION],
            expected_receipt_status=1,
        )


def test_expected_failure_but_tx_succeeded_raises(
    monkeypatch: pytest.MonkeyPatch, client_backend: ClientBackend
) -> None:
    """A status-1 receipt with ``expected_receipt_status=0`` must throw."""
    with pytest.raises(Exception, match=r"receipt status 1, expected 0"):
        _fill_stateful(
            monkeypatch,
            client_backend,
            statuses_per_block=[[1]],
            phases=[TestPhase.EXECUTION],
            expected_receipt_status=0,
        )


def test_single_failed_receipt_in_block_raises(
    monkeypatch: pytest.MonkeyPatch, client_backend: ClientBackend
) -> None:
    """One bad receipt among good ones is enough to throw."""
    with pytest.raises(
        Exception,
        match=r"Transaction 2 in block \d+ has receipt status 0",
    ):
        _fill_stateful(
            monkeypatch,
            client_backend,
            statuses_per_block=[[1, 1, 0]],
            phases=[TestPhase.EXECUTION],
            expected_receipt_status=1,
        )


@pytest.mark.parametrize("status", [0, 1])
def test_matching_status_fills(
    monkeypatch: pytest.MonkeyPatch,
    client_backend: ClientBackend,
    status: int,
) -> None:
    """Receipts matching ``expected_receipt_status`` fill normally."""
    result = _fill_stateful(
        monkeypatch,
        client_backend,
        statuses_per_block=[[status, status]],
        phases=[TestPhase.EXECUTION],
        expected_receipt_status=status,
    )
    assert isinstance(result.fixture, BlockchainEngineStatefulFixture)


def test_setup_phase_blocks_are_exempt(
    monkeypatch: pytest.MonkeyPatch, client_backend: ClientBackend
) -> None:
    """
    ``expected_receipt_status`` describes the test's own transactions;
    a mismatching status in a SETUP-phase block must not throw.
    """
    result = _fill_stateful(
        monkeypatch,
        client_backend,
        statuses_per_block=[[0], [1]],
        phases=[TestPhase.SETUP, TestPhase.EXECUTION],
        expected_receipt_status=1,
    )
    assert isinstance(result.fixture, BlockchainEngineStatefulFixture)
    assert len(result.fixture.setup_payloads) == 1
    assert len(result.fixture.payloads) == 1


def test_unset_expected_status_skips_validation(
    monkeypatch: pytest.MonkeyPatch, client_backend: ClientBackend
) -> None:
    """Without ``expected_receipt_status``, any status fills normally."""
    result = _fill_stateful(
        monkeypatch,
        client_backend,
        statuses_per_block=[[0, 1]],
        phases=[TestPhase.EXECUTION],
    )
    assert isinstance(result.fixture, BlockchainEngineStatefulFixture)
