"""Test suite for payload spilling in ``make_stateful_fixture``."""

import functools
import gc
import json
from io import StringIO
from typing import Any, Iterator, List, Tuple

import pytest

from execution_testing.base_types import Address, Bloom, Bytes, Hash
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
from execution_testing.fixtures.spill import PayloadBuffer
from execution_testing.forks import Amsterdam
from execution_testing.rpc.rpc_types import GetPayloadResponse
from execution_testing.test_types import (
    Alloc,
    Environment,
    TestPhase,
    Transaction,
)

from .. import blockchain as blockchain_module
from ..blockchain import Block, BlockchainTest, TestingBuildBlock

FORK = Amsterdam
START_BLOCK_NUMBER = 1
SETUP_BLOCKS = 2
EXECUTION_BLOCKS = 6
BAL_BYTES = 64 * 1024


def _header(number: int) -> FixtureHeader:
    """Build a minimal valid header for the test fork."""
    return FixtureHeader(
        fork=FORK,
        fee_recipient=Address(0),
        state_root=Hash(0),
        number=number,
        gas_limit=30_000_000,
        gas_used=21_000,
        timestamp=number * 12,
        extra_data=b"\x00",
        base_fee_per_gas=7,
        withdrawals_root=Hash(0),
        blob_gas_used=0,
        excess_blob_gas=0,
        parent_beacon_block_root=Hash(0),
        requests_hash=Hash(0),
        block_access_list_hash=Hash(0),
        slot_number=number,
    )


def _built_block(number: int) -> TestingBuildBlock:
    """Build a block whose access list only the filler can retain."""
    header = _header(number)
    payload = FixtureExecutionPayload.from_fixture_header(
        header=header,
        transactions=[],
        withdrawals=None,
    )
    payload.block_access_list = Bytes(
        (number % 251).to_bytes(1, "big") * BAL_BYTES
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
            receipts=[],
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
    threshold: int | None = None,
    execution_blocks: int = EXECUTION_BLOCKS,
) -> Tuple[BlockchainEngineStatefulFixture, int]:
    """
    Fill over setup and execution blocks, returning the fixture and the
    bytes still reachable afterwards.

    Only ``generate_block_data`` is stubbed, so a second holder of a
    payload anywhere else in the loop would show up in the figure.
    """
    tracemalloc = pytest.importorskip("tracemalloc")
    total = SETUP_BLOCKS + execution_blocks
    block_numbers: Iterator[int] = iter(
        range(START_BLOCK_NUMBER + 1, START_BLOCK_NUMBER + 1 + total)
    )

    def fake_generate_block_data(
        _self: BlockchainTest, **_kwargs: Any
    ) -> TestingBuildBlock:
        return _built_block(next(block_numbers))

    monkeypatch.setattr(
        BlockchainTest, "generate_block_data", fake_generate_block_data
    )
    if threshold is not None:
        monkeypatch.setattr(
            blockchain_module,
            "PayloadBuffer",
            functools.partial(PayloadBuffer, threshold=threshold),
        )

    blocks: List[Block] = []
    for phase, count in (
        (TestPhase.SETUP, SETUP_BLOCKS),
        (TestPhase.EXECUTION, execution_blocks),
    ):
        for _ in range(count):
            tx = Transaction()
            tx.test_phase = phase
            blocks.append(Block(txs=[tx]))
    test = BlockchainTest(
        fork=FORK,
        pre=Alloc(),
        post=Alloc(),
        blocks=blocks,
    )

    gc.collect()
    tracemalloc.start()
    baseline = tracemalloc.get_traced_memory()[0]
    result = test.make_stateful_fixture(client_backend)
    retained = tracemalloc.get_traced_memory()[0] - baseline
    tracemalloc.stop()

    fixture = result.fixture
    assert isinstance(fixture, BlockchainEngineStatefulFixture)
    return fixture, retained


def test_ordinary_fill_keeps_payloads_in_memory(
    monkeypatch: pytest.MonkeyPatch, client_backend: ClientBackend
) -> None:
    """Under the threshold the fixture carries the payloads as before."""
    fixture, _ = _fill_stateful(monkeypatch, client_backend)
    assert len(fixture.setup_payloads) == SETUP_BLOCKS
    assert len(fixture.payloads) == EXECUTION_BLOCKS


def test_spilled_fill_writes_every_payload(
    monkeypatch: pytest.MonkeyPatch, client_backend: ClientBackend
) -> None:
    """Spilled payloads splice back under the declared aliases."""
    fixture, _ = _fill_stateful(monkeypatch, client_backend, threshold=1)
    assert len(fixture.setup_payloads) == 0
    assert len(fixture.payloads) == 0

    out = StringIO()
    fixture.write_json(out)
    document = json.loads(out.getvalue())
    assert len(document["setupEngineNewPayloads"]) == SETUP_BLOCKS
    assert len(document["engineNewPayloads"]) == EXECUTION_BLOCKS


def test_spilled_fill_hashes_like_a_buffered_one(
    monkeypatch: pytest.MonkeyPatch, client_backend: ClientBackend
) -> None:
    """Spilling is invisible to the fixture's identity."""
    buffered, _ = _fill_stateful(monkeypatch, client_backend)
    spilled, _ = _fill_stateful(monkeypatch, client_backend, threshold=1)
    assert spilled.hash == buffered.hash


def test_buffered_retention_grows_with_the_block_count(
    monkeypatch: pytest.MonkeyPatch, client_backend: ClientBackend
) -> None:
    """Without spilling, every extra block stays reachable after the fill."""
    _, small = _fill_stateful(monkeypatch, client_backend, execution_blocks=4)
    _, large = _fill_stateful(monkeypatch, client_backend, execution_blocks=28)
    assert large - small > 24 * BAL_BYTES // 2


def test_spilled_retention_is_flat(
    monkeypatch: pytest.MonkeyPatch, client_backend: ClientBackend
) -> None:
    """Spilling leaves a fixed overhead rather than a per-block one."""
    _, small = _fill_stateful(
        monkeypatch, client_backend, threshold=1, execution_blocks=4
    )
    _, large = _fill_stateful(
        monkeypatch, client_backend, threshold=1, execution_blocks=28
    )
    assert large - small < BAL_BYTES
