"""Tests for the `consume reorg` step runner."""

import hashlib
from typing import Callable, List, Sequence
from unittest.mock import MagicMock, patch

import pytest

from execution_testing.base_types import Bytes, Hash
from execution_testing.client_clis import TransitionTool
from execution_testing.fixtures.blockchain import PayloadStatusEnum
from execution_testing.fixtures.reorg import (
    AssertLogsStep,
    AssertStateStep,
    AssertTxStatusStep,
    BlockchainEngineReorgFixture,
    ForkchoiceUpdatedStep,
    GetPayloadStep,
    Outcome,
    PayloadAttributes,
    SendRawTransactionStep,
    TxRef,
)
from execution_testing.forks import Cancun
from execution_testing.rpc import EthRPC
from execution_testing.rpc.rpc_types import BlobsBundle, JSONRPCError
from execution_testing.specs.reorg import ReorgBlock, ReorgTest
from execution_testing.test_types import Alloc

from ..simulators.helpers.exceptions import LoggedError
from ..simulators.helpers.timing import TimingData
from ..simulators.simulator_logic import test_via_reorg as reorg_logic
from ..simulators.simulator_logic.test_via_reorg import (
    BoundPayload,
    StepRunner,
)

MakeRunner = Callable[..., StepRunner]


@pytest.fixture
def make_runner(default_t8n: TransitionTool) -> MakeRunner:
    """Build a `StepRunner` for a linear fixture with stubbed RPC."""

    def make(
        labels: Sequence[str] = ("a1",),
        eth: MagicMock | EthRPC | None = None,
        engine: MagicMock | None = None,
    ) -> StepRunner:
        test = ReorgTest(
            fork=Cancun,
            pre=Alloc().with_genesis_accounts(),
            blocks=[ReorgBlock(label=label) for label in labels],
            steps=[],
        )
        fixture = test.generate(
            t8n=default_t8n, fixture_format=BlockchainEngineReorgFixture
        ).fixture
        assert isinstance(fixture, BlockchainEngineReorgFixture)
        return StepRunner(
            fixture,
            eth if eth is not None else MagicMock(),
            engine if engine is not None else MagicMock(),
            TimingData("test"),
            0.0,
        )

    return make


def test_get_payload_computes_blob_versioned_hashes(
    make_runner: MakeRunner,
) -> None:
    """
    A built payload's blob commitments are converted to versioned hashes
    per EIP-4844 (PR3556-R0023), now via `BlobsBundle.blob_versioned_hashes`
    instead of a duplicated formula.
    """
    engine = MagicMock()
    step_runner = make_runner(engine=engine)
    step_runner.last_payload_id = Bytes(b"\x01" * 8)
    commitment = Bytes(b"\xaa" * 48)
    expected_hash = Hash(
        bytes([1]) + hashlib.sha256(bytes(commitment)).digest()[1:]
    )
    response = MagicMock()
    response.execution_payload = step_runner.fixture.blocks[
        "a1"
    ].payload.params[0]
    response.blobs_bundle = BlobsBundle(
        commitments=[commitment], proofs=[], blobs=[]
    )
    response.execution_requests = None
    engine.get_payload.return_value = response
    step_runner.get_payload(
        "gp", GetPayloadStep(bind="p1", parent="genesis", version=3)
    )
    assert step_runner.bound["p1"].versioned_hashes == [expected_hash]


@pytest.mark.parametrize(
    "prev_randao_offset,binds,error",
    [
        (1, ["p1"], "prevRandao"),
        (0, ["p1", "p2"], "the one bound to p1"),
    ],
    ids=["wrong_prev_randao", "duplicate_build"],
)
def test_get_payload_rejects_a_build_off_the_request(
    make_runner: MakeRunner,
    prev_randao_offset: int,
    binds: List[str],
    error: str,
) -> None:
    """A build must honor the requested attributes and be a new payload."""
    engine = MagicMock()
    step_runner = make_runner(engine=engine)
    payload = step_runner.fixture.blocks["a1"].payload.params[0]
    engine.get_payload.return_value = MagicMock(
        execution_payload=payload, blobs_bundle=None, execution_requests=None
    )
    step_runner.last_payload_id = Bytes(b"\x01" * 8)
    step_runner.last_payload_attributes = PayloadAttributes(
        timestamp=payload.timestamp,
        prev_randao=Hash(
            int.from_bytes(payload.prev_randao, "big") + prev_randao_offset
        ),
        suggested_fee_recipient=0x1234,
    )
    *earlier, last = binds
    for bind in earlier:
        step_runner.get_payload(
            "gp", GetPayloadStep(bind=bind, parent="genesis", version=3)
        )
    with pytest.raises(LoggedError, match=error):
        step_runner.get_payload(
            "gp", GetPayloadStep(bind=last, parent="genesis", version=3)
        )


@pytest.mark.parametrize(
    "latest,error",
    [
        ("genesis", None),
        ("a1", "matches none"),
        ("error", "-32603"),
        ("null", "returned no block"),
    ],
)
def test_head_moved_false_needs_an_observed_unmoved_head(
    make_runner: MakeRunner, latest: str, error: str | None
) -> None:
    """
    ``headMoved=False`` passes only when ``latest`` is observed to be
    another block; a failed or empty lookup fails the step.
    """
    eth = MagicMock()
    engine = MagicMock()
    step_runner = make_runner(eth=eth, engine=engine)
    if latest == "error":
        eth.get_block_by_number.side_effect = JSONRPCError(-32603, "boom")
    elif latest == "null":
        eth.get_block_by_number.return_value = None
    else:
        eth.get_block_by_number.return_value = {
            "hash": step_runner.resolve(latest)
        }
    response = MagicMock()
    response.payload_status.status = PayloadStatusEnum.SYNCING
    response.payload_status.latest_valid_hash = None
    response.payload_status.validation_error = None
    response.payload_id = None
    engine.forkchoice_updated.return_value = response
    step = ForkchoiceUpdatedStep(
        head="a1",
        version=3,
        expect=[
            Outcome(
                id="syncing",
                status="SYNCING",
                latest_valid_hash="null",
                head_moved=False,
            )
        ],
    )
    if error is None:
        step_runner.forkchoice_updated("fcu", step, 0)
        assert step_runner.matched[-1].endswith(":syncing")
    else:
        with pytest.raises(LoggedError, match=error):
            step_runner.forkchoice_updated("fcu", step, 0)


@pytest.mark.parametrize(
    "returned,expected,passes",
    [
        (["a2", "a1"], ["a1", "a2"], True),
        (["a1", "a1"], ["a1"], False),
        (["a1"], ["a1", "a1"], False),
        (["a2"], ["a1"], False),
    ],
    ids=["any_order", "extra_log", "missing_log", "wrong_block"],
)
def test_assert_logs_counts_logs_per_block(
    make_runner: MakeRunner,
    returned: List[str],
    expected: List[str],
    passes: bool,
) -> None:
    """`assertLogs` wants exactly one log per listed block, in any order."""
    eth = MagicMock()
    step_runner = make_runner(labels=("a1", "a2"), eth=eth)
    eth.get_logs.return_value = [
        {"blockHash": str(step_runner.fixture.resolve(label))}
        for label in returned
    ]
    step = AssertLogsStep(blocks=expected)
    if passes:
        step_runner.assert_logs("logs", step)
    else:
        with pytest.raises(LoggedError, match="eth_getLogs returned"):
            step_runner.assert_logs("logs", step)


def test_assert_logs_accepts_a_hash_bound_to_two_labels(
    make_runner: MakeRunner,
) -> None:
    """
    A label whose hash was later rebound to a second label must still match
    `assertLogs` (PR3556-R0021): the reverse `labels_by_hash` lookup only
    keeps the latest bind, but both labels identify the same block.
    """
    eth = MagicMock()
    step_runner = make_runner(eth=eth)
    payload = step_runner.fixture.blocks["a1"].payload.params[0]
    step_runner.bound["p"] = BoundPayload(
        payload=payload,
        versioned_hashes=[],
        parent_beacon_block_root=None,
        execution_requests=None,
    )
    step_runner.labels_by_hash[payload.block_hash] = "q"  # a later bind
    eth.get_logs.return_value = [{"blockHash": str(payload.block_hash)}]
    step_runner.assert_logs("logs", AssertLogsStep(blocks=["p"]))


@pytest.mark.parametrize(
    "expect,passes", [(["rejected"], True), (["accepted"], False)]
)
def test_send_raw_transaction_reports_a_client_rejection(
    make_runner: MakeRunner, expect: List[str], passes: bool
) -> None:
    """A JSON-RPC error from the client is the `rejected` result."""
    eth = EthRPC("http://localhost:8545")
    step_runner = make_runner(eth=eth)
    step_runner.tx_rlp = MagicMock(return_value=Bytes(b"\x01"))  # type: ignore[method-assign]
    reply = MagicMock()
    reply.json.return_value = {
        "jsonrpc": "2.0",
        "id": 1,
        "error": {"code": -32000, "message": "already known"},
    }
    step = SendRawTransactionStep(tx=TxRef(block="a1"), expect=expect)
    with patch.object(eth.session, "post", return_value=reply):
        if passes:
            step_runner.send_raw_transaction("send", step)
            assert step_runner.matched[-1] == "send:rejected"
        else:
            with pytest.raises(LoggedError, match="rejected .-32000"):
                step_runner.send_raw_transaction("send", step)


@pytest.mark.parametrize(
    "replies,timeout,status",
    [
        ([None, MagicMock(block_hash=None)], 5.0, "pending"),
        ([None], 0.0, "dropped"),
    ],
    ids=["waits_for_preferred", "accepts_later_at_deadline"],
)
def test_assert_tx_status_prefers_the_first_listed_status(
    make_runner: MakeRunner,
    replies: List[MagicMock | None],
    timeout: float,
    status: str,
) -> None:
    """A later-listed status passes only once the deadline has passed."""
    eth = MagicMock()
    eth.get_transaction_by_hash.side_effect = replies
    step_runner = make_runner(eth=eth)
    step_runner.tx_hash = MagicMock(return_value=Hash(1))  # type: ignore[method-assign]
    step = AssertTxStatusStep(
        tx=TxRef(block="a1"), expect=["pending", "dropped"]
    )
    with (
        patch.object(reorg_logic, "TX_STATUS_TIMEOUT", timeout),
        patch.object(reorg_logic, "TX_STATUS_POLL_INTERVAL", 0),
    ):
        step_runner.assert_tx_status("status", step)
    assert step_runner.matched[-1] == f"status:{status}"


def test_assert_state_rejects_noncanonical_block(
    make_runner: MakeRunner,
) -> None:
    """`assertState.at` fails when another block holds the label's height."""
    eth = MagicMock()
    eth.get_block_by_number.return_value = {"hash": Hash(0xDEAD)}
    step_runner = make_runner(eth=eth)
    with pytest.raises(LoggedError, match="expected a1"):
        step_runner.assert_state(
            "assertState", AssertStateStep(at="a1", accounts={})
        )
