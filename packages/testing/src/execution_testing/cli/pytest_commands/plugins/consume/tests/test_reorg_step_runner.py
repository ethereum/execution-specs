"""Tests for the `consume reorg` step runner."""

import hashlib
import logging
from typing import Callable, List, Sequence
from unittest.mock import MagicMock, patch

import pytest

from execution_testing.base_types import Bytes, Hash
from execution_testing.client_clis import TransitionTool
from execution_testing.devp2p.rlpx import RLPxError
from execution_testing.fixtures.blockchain import PayloadStatusEnum
from execution_testing.fixtures.reorg import (
    AssertLogsStep,
    AssertReceiptStep,
    AssertStateStep,
    AssertTxStatusStep,
    AwaitHeadStep,
    BlockchainEngineReorgFixture,
    ForkchoiceUpdatedStep,
    GetPayloadStep,
    Outcome,
    PayloadAttributes,
    SendRawTransactionStep,
    ServePeerStep,
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
    per EIP-4844.
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
    `assertLogs`: the reverse `labels_by_hash` lookup only keeps the latest
    bind, but both labels identify the same block.
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


INDEXING = JSONRPCError(-32000, reorg_logic.TX_INDEXING_IN_PROGRESS)


@pytest.mark.parametrize(
    "replies,timeout,passes",
    [
        ([INDEXING, None], 5.0, True),
        ([INDEXING], 0.0, False),
        ([JSONRPCError(-32000, "header not found"), None], 5.0, False),
    ],
    ids=[
        "retries_while_indexing",
        "fails_at_deadline",
        "fails_on_other_errors",
    ],
)
def test_assert_receipt_waits_for_the_transaction_index(
    make_runner: MakeRunner,
    replies: List[JSONRPCError | None],
    timeout: float,
    passes: bool,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """
    A lookup the client cannot answer while indexing is retried until the
    deadline, and each retry is logged; any other error fails at once.
    """
    eth = MagicMock()
    eth.get_transaction_receipt.side_effect = replies
    step_runner = make_runner(eth=eth)
    step_runner.tx_hash = MagicMock(return_value=Hash(1))  # type: ignore[method-assign]
    step = AssertReceiptStep(tx=TxRef(block="a1"), block=None)
    with (
        patch.object(reorg_logic, "TX_STATUS_TIMEOUT", timeout),
        patch.object(reorg_logic, "TX_STATUS_POLL_INTERVAL", 0),
        caplog.at_level(logging.INFO),
    ):
        if passes:
            step_runner.assert_receipt("receipt", step)
            assert "receipt: client is still indexing" in caplog.text
        else:
            with pytest.raises(JSONRPCError):
                step_runner.assert_receipt("receipt", step)


@pytest.mark.parametrize(
    "replies,timeout,passes",
    [
        ([INDEXING, MagicMock(block_hash=None)], 5.0, True),
        ([INDEXING], 0.0, False),
    ],
    ids=["retries_while_indexing", "fails_at_deadline"],
)
def test_assert_tx_status_waits_for_the_transaction_index(
    make_runner: MakeRunner,
    replies: List[JSONRPCError | MagicMock],
    timeout: float,
    passes: bool,
) -> None:
    """
    A lookup the client cannot answer while indexing is retried until the
    deadline, and is never read as a status.
    """
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
        if passes:
            step_runner.assert_tx_status("status", step)
            assert step_runner.matched[-1] == "status:pending"
        else:
            with pytest.raises(JSONRPCError):
                step_runner.assert_tx_status("status", step)


def test_assert_tx_status_retries_within_its_own_deadline(
    make_runner: MakeRunner,
) -> None:
    """
    Retries of a lookup the client cannot answer while indexing end at the
    deadline of the status poll, and do not start a new one.
    """

    class Clock:
        """A clock that only moves when the code under test sleeps."""

        now = 0.0

        def monotonic(self) -> float:
            return self.now

        def sleep(self, seconds: float) -> None:
            self.now += seconds

    # Three polls see a status that is not the preferred one, then the
    # client answers that it is indexing for the rest of the poll.
    eth = MagicMock()
    eth.get_transaction_by_hash.side_effect = [None] * 3 + [INDEXING] * 20
    step_runner = make_runner(eth=eth)
    step_runner.tx_hash = MagicMock(return_value=Hash(1))  # type: ignore[method-assign]
    step = AssertTxStatusStep(
        tx=TxRef(block="a1"), expect=["pending", "dropped"]
    )
    timeout, interval = 5.0, 1.0
    with (
        patch.object(reorg_logic, "time", Clock()),
        patch.object(reorg_logic, "TX_STATUS_TIMEOUT", timeout),
        patch.object(reorg_logic, "TX_STATUS_POLL_INTERVAL", interval),
        pytest.raises(JSONRPCError),
    ):
        step_runner.assert_tx_status("status", step)
    # One lookup per interval from the start up to and including the deadline.
    assert eth.get_transaction_by_hash.call_count == timeout / interval + 1


def awaiting(
    make_runner: MakeRunner, polls: int = 2
) -> tuple[StepRunner, MagicMock, MagicMock]:
    """
    A runner on a1..a2 whose client reports genesis for ``polls`` polls and
    then a2, with a ``forkchoiceUpdated`` sent to a2 and a later one to a1.
    """
    eth = MagicMock()
    engine = MagicMock()
    step_runner = make_runner(labels=("a1", "a2"), eth=eth, engine=engine)
    behind = {"hash": step_runner.resolve("genesis")}
    synced = {"hash": step_runner.resolve("a2")}
    eth.get_block_by_number.side_effect = [behind] * polls + [synced]
    awaited = MagicMock()
    step_runner.forkchoice_sent = {"a2": (awaited, 3), "a1": (MagicMock(), 3)}
    return step_runner, engine, awaited


def test_await_head_announces_the_awaited_head_until_it_is_synced(
    make_runner: MakeRunner,
) -> None:
    """
    While ``latest`` is another block, the newPayload of the awaited head and
    the forkchoiceUpdated sent to it are sent again, whatever was sent
    since; the step passes once ``latest`` is the awaited head.
    """
    step_runner, engine, awaited = awaiting(make_runner)
    params, version = step_runner._new_payload_params("a2")
    with (
        patch.object(reorg_logic, "FIRST_REANNOUNCE_DELAY", 0),
        patch.object(reorg_logic, "REANNOUNCE_INTERVAL", 0),
        patch.object(reorg_logic, "SYNC_POLL_INTERVAL", 0),
    ):
        step_runner.await_head("await", AwaitHeadStep(latest="a2"))
    assert engine.new_payload.call_count == 2
    engine.new_payload.assert_called_with(*params, version=version)
    assert engine.forkchoice_updated.call_count == 2
    engine.forkchoice_updated.assert_called_with(
        forkchoice_state=awaited, payload_attributes=None, version=3
    )


def test_await_head_announces_the_update_answered_syncing(
    make_runner: MakeRunner,
) -> None:
    """
    A later forkchoiceUpdated to the awaited head that errors is not the one
    announced again.
    """
    eth = MagicMock()
    engine = MagicMock()
    step_runner = make_runner(labels=("a1", "a2"), eth=eth, engine=engine)
    syncing = MagicMock()
    syncing.payload_status.status = PayloadStatusEnum.SYNCING
    syncing.payload_status.latest_valid_hash = None
    syncing.payload_status.validation_error = None
    syncing.payload_id = None
    engine.forkchoice_updated.side_effect = [
        syncing,
        JSONRPCError(-38002, "Invalid forkchoice state"),
        syncing,
    ]
    for safe, outcome in (
        ("zero", Outcome(id="syncing", status="SYNCING")),
        ("a1", Outcome(id="refused", error_code=-38002)),
    ):
        step = ForkchoiceUpdatedStep(
            head="a2", safe=safe, version=3, expect=[outcome]
        )
        step_runner.forkchoice_updated("fcu", step, 0)
    eth.get_block_by_number.side_effect = [
        {"hash": step_runner.resolve("genesis")},
        {"hash": step_runner.resolve("a2")},
    ]
    with (
        patch.object(reorg_logic, "FIRST_REANNOUNCE_DELAY", 0),
        patch.object(reorg_logic, "SYNC_POLL_INTERVAL", 0),
    ):
        step_runner.await_head("await", AwaitHeadStep(latest="a2"))
    first, _, announced = engine.forkchoice_updated.call_args_list
    assert (
        announced.kwargs["forkchoice_state"]
        == first.kwargs["forkchoice_state"]
    )


def test_await_head_announces_early_once_then_at_the_interval(
    make_runner: MakeRunner,
) -> None:
    """
    The first announcement comes after ``FIRST_REANNOUNCE_DELAY``, the next
    ones every ``REANNOUNCE_INTERVAL``.
    """

    class Clock:
        """A clock that only moves when the code under test sleeps."""

        now = 0.0

        def monotonic(self) -> float:
            return self.now

        def sleep(self, seconds: float) -> None:
            self.now += seconds

    # Polls at 0, 1, .. 8 s see genesis: announcements at 1, 5 and 9 s.
    step_runner, engine, _ = awaiting(make_runner, polls=10)
    with (
        patch.object(reorg_logic, "time", Clock()),
        patch.object(reorg_logic, "FIRST_REANNOUNCE_DELAY", 1.0),
        patch.object(reorg_logic, "REANNOUNCE_INTERVAL", 4.0),
        patch.object(reorg_logic, "SYNC_POLL_INTERVAL", 1.0),
    ):
        step_runner.await_head("await", AwaitHeadStep(latest="a2"))
    assert engine.new_payload.call_count == 3


def test_await_head_fails_at_once_when_the_client_rejects_the_head(
    make_runner: MakeRunner,
) -> None:
    """An INVALID answer to an announcement does not wait for the timeout."""
    step_runner, engine, _ = awaiting(make_runner, polls=5)
    engine.new_payload.return_value = MagicMock(
        status=PayloadStatusEnum.INVALID, validation_error="bad block"
    )
    step_runner.peer = MagicMock(alive=True)
    step_runner.peer.statistics.transcript = ["GetBlockHeaders"]
    with (
        patch.object(reorg_logic, "FIRST_REANNOUNCE_DELAY", 0),
        patch.object(reorg_logic, "SYNC_POLL_INTERVAL", 0),
        pytest.raises(LoggedError, match="rejected a2.*GetBlockHeaders"),
    ):
        step_runner.await_head("await", AwaitHeadStep(latest="a2"))
    assert engine.new_payload.call_count == 1


def test_await_head_redials_a_dropped_peer_and_reports_it_on_timeout(
    make_runner: MakeRunner,
) -> None:
    """
    A peer the client dropped is redialed before each announcement, and the
    timeout message says so and carries the peer's transcript.
    """
    step_runner, _, _ = awaiting(make_runner, polls=5)
    peer = MagicMock(alive=False, disconnect_reason=4)
    peer.statistics.transcript = ["eth/69 negotiated"]
    peer.reconnect.side_effect = OSError("refused")
    step_runner.peer = peer
    step_runner.served_chain = MagicMock()

    def timeout_after_two_polls() -> float:
        return 0.0 if peer.reconnect.call_count < 2 else 1.0

    clock = MagicMock(monotonic=timeout_after_two_polls)
    with (
        patch.object(reorg_logic, "time", clock),
        patch.object(reorg_logic, "FIRST_REANNOUNCE_DELAY", 0),
        patch.object(reorg_logic, "REANNOUNCE_INTERVAL", 0),
        patch.object(reorg_logic, "SYNC_TIMEOUT", 1.0),
        pytest.raises(
            LoggedError,
            match="dropped .Disconnect reason 4.*eth/69 negotiated",
        ),
    ):
        step_runner.await_head("await", AwaitHeadStep(latest="a2"))
    peer.reconnect.assert_called_with(step_runner.served_chain)
    assert peer.reconnect.call_count == 2


def test_await_head_needs_a_forkchoice_update_to_the_head(
    make_runner: MakeRunner,
) -> None:
    """Without one there is nothing to announce again."""
    with pytest.raises(LoggedError, match="no forkchoiceUpdated to a1"):
        make_runner().await_head("await", AwaitHeadStep(latest="a1"))


@pytest.mark.parametrize(
    "error", [OSError("connection refused"), RLPxError("no shared eth")]
)
def test_serve_peer_reports_a_failed_dial(
    make_runner: MakeRunner, error: Exception
) -> None:
    """A refused connection or handshake is reported with its cause."""
    step_runner = make_runner()
    step_runner.dial_peer = MagicMock(side_effect=error)
    with pytest.raises(LoggedError, match=f"could not connect.*{error}"):
        step_runner.serve_peer("serve", ServePeerStep(head="a1"))


def test_serve_peer_dials_once_then_switches_or_redials(
    make_runner: MakeRunner,
) -> None:
    """
    The first step dials the peer; a later one switches the served chain,
    or redials when the client has dropped the peer.
    """
    step_runner = make_runner(labels=("a1", "a2"))
    with pytest.raises(LoggedError, match="no peer can be dialed"):
        step_runner.serve_peer("serve", ServePeerStep(head="a1"))
    peer = MagicMock(alive=True)
    step_runner.dial_peer = MagicMock(return_value=peer)
    step_runner.serve_peer("serve", ServePeerStep(head="a1"))
    step_runner.serve_peer("serve", ServePeerStep(head="a2"))
    assert step_runner.dial_peer.call_count == 1
    peer.set_chain.assert_called_once_with(step_runner.served_chain)
    peer.alive = False
    step_runner.serve_peer("serve", ServePeerStep(head="a1"))
    peer.reconnect.assert_called_once_with(step_runner.served_chain)


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
