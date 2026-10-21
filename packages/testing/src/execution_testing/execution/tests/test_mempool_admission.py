"""Test the mempool admission execute format against a fake client."""

from contextlib import contextmanager
from types import SimpleNamespace
from typing import Any, ClassVar, Dict, Iterator, List, Sequence, Set

import pytest

from execution_testing.base_types import Hash
from execution_testing.exceptions import TransactionException
from execution_testing.forks import Cancun, Prague
from execution_testing.rpc import SendTransactionExceptionError
from execution_testing.rpc.rpc_types import JSONRPCError
from execution_testing.test_types import (
    EOA,
    Blob,
    MempoolTransaction,
    NetworkWrappedTransaction,
    Transaction,
)

from ..get_blobs import GetBlobs
from ..mempool import MempoolAdmission, MempoolCheck

ALICE = EOA(key=1)
BOB = EOA(key=2)
REQUEST = SimpleNamespace(node=SimpleNamespace(nodeid="test_mempool"))


class FakeEthRPC:
    """Admit, reject or drop each transaction by hash."""

    def __init__(
        self,
        *,
        rejected: Set[Hash] | None = None,
        dropped: Set[Hash] | None = None,
        known: Set[Hash] | None = None,
        included: Set[Hash] | None = None,
    ) -> None:
        """Answer every send by admission unless listed otherwise."""
        self.rejected = rejected or set()
        self.dropped = dropped or set()
        self.known = known or set()
        self.included = included or set()
        self.sent: List[Hash] = []
        self.waited: List[Hash] = []
        self.locked = False

    @property
    def transaction_polling_context(self) -> Any:
        """Return a lock recording whether it is held."""

        @contextmanager
        def lock() -> Iterator[None]:
            self.locked = True
            try:
                yield
            finally:
                self.locked = False

        return lock()

    def send_raw_transaction(
        self, transaction_rlp: Any, request_id: Any = None
    ) -> Hash:
        """Admit the transaction, or fail as `eth_rpc` would."""
        del request_id
        tx_hash = self.hash_of(transaction_rlp)
        self.sent.append(tx_hash)
        if tx_hash in self.dropped:
            error: Exception = ConnectionError("connection dropped")
        elif tx_hash in self.rejected:
            error = JSONRPCError(code=-32000, message="rejected")
        else:
            return tx_hash
        raise SendTransactionExceptionError(str(error)) from error

    hashes_by_rlp: Dict[bytes, Hash] = {}

    def hash_of(self, transaction_rlp: Any) -> Hash:
        """Return the hash a wrapper's or a payload's encoding names."""
        return self.hashes_by_rlp.get(
            bytes(transaction_rlp), transaction_rlp.keccak256()
        )

    def transaction_known(self, transaction_hash: Hash) -> bool:
        """Return whether the client holds the transaction."""
        return transaction_hash in self.known

    def get_transaction_receipts(
        self, transaction_hashes: Sequence[Hash]
    ) -> List[Dict[str, Any] | None]:
        """Return a receipt for the transactions already included."""
        return [
            {} if tx_hash in self.included else None
            for tx_hash in transaction_hashes
        ]

    def wait_for_receipts(
        self, transaction_hashes: Sequence[Hash]
    ) -> List[Dict[str, Any]]:
        """Record the transactions waited on."""
        self.waited.extend(transaction_hashes)
        return [{"gasUsed": hex(21_000)} for _ in transaction_hashes]


def signed(sender: EOA, nonce: int, gas_price: int = 10) -> Transaction:
    """Return a signed transfer from `sender` at `nonce`."""
    return Transaction(
        sender=sender, nonce=nonce, gas_limit=21_000, gas_price=gas_price
    ).with_signature_and_sender()


def run(
    rpc: FakeEthRPC,
    entries: List[MempoolTransaction],
    **kwargs: Any,
) -> None:
    """Execute the format against `rpc`."""
    MempoolAdmission(txs=entries, **kwargs).execute(
        fork=Prague,
        eth_rpc=rpc,  # type: ignore[arg-type]
        engine_rpc=None,
        request=REQUEST,  # type: ignore[arg-type]
    )


def test_expected_verdicts_pass_and_admitted_txs_are_waited_on() -> None:
    """Test that matching verdicts pass and admissions are mined."""
    admitted = signed(ALICE, 0)
    rejected = signed(BOB, 0)
    rpc = FakeEthRPC(rejected={rejected.hash})
    run(
        rpc,
        [
            MempoolTransaction(tx=admitted, accepted=True),
            MempoolTransaction(tx=rejected, accepted=False),
        ],
    )
    assert rpc.waited == [admitted.hash]


def test_transport_errors_are_not_rejections() -> None:
    """Test that a failed delivery is an error, not a rejection."""
    tx = signed(ALICE, 0)
    rpc = FakeEthRPC(dropped={tx.hash})
    with pytest.raises(SendTransactionExceptionError):
        run(rpc, [MempoolTransaction(tx=tx, accepted=False)])


def test_wrongly_admitted_tx_fails_after_inclusion() -> None:
    """Test that an admitted rejection case fails once it is mined."""
    tx = signed(ALICE, 0)
    rpc = FakeEthRPC()
    with pytest.raises(pytest.fail.Exception, match="expected rejection"):
        run(rpc, [MempoolTransaction(tx=tx, accepted=False)])
    assert rpc.waited == [tx.hash]


def test_wrongly_admitted_invalid_tx_is_not_waited_on() -> None:
    """Test that a wrongly admitted tx invalid in a block is not mined."""
    tx = signed(ALICE, 0).with_error(TransactionException.NONCE_IS_MAX)
    rpc = FakeEthRPC()
    with pytest.raises(pytest.fail.Exception, match="expected rejection"):
        run(rpc, [MempoolTransaction(tx=tx, accepted=False)])
    assert rpc.waited == []


def test_wrongly_rejected_tx_fails() -> None:
    """Test that a rejected admission case fails."""
    tx = signed(ALICE, 0)
    rpc = FakeEthRPC(rejected={tx.hash})
    with pytest.raises(pytest.fail.Exception, match="was rejected"):
        run(rpc, [MempoolTransaction(tx=tx, accepted=True)])


def test_duplicate_of_a_delivered_tx_counts_as_admitted() -> None:
    """Test that a retried send answered as a duplicate is admitted."""
    tx = signed(ALICE, 0)
    rpc = FakeEthRPC(rejected={tx.hash}, known={tx.hash})
    run(rpc, [MempoolTransaction(tx=tx, accepted=True)])
    assert rpc.waited == [tx.hash]


def test_rejected_tx_the_client_holds_fails() -> None:
    """Test that a rejection is void if the client still holds the tx."""
    tx = signed(ALICE, 0)
    rpc = FakeEthRPC(rejected={tx.hash}, known={tx.hash})
    with pytest.raises(pytest.fail.Exception, match="client knows it"):
        run(rpc, [MempoolTransaction(tx=tx, accepted=False)])


def test_only_the_surviving_replacement_is_waited_on() -> None:
    """Test that a replaced admission is not waited on."""
    original = signed(ALICE, 0, gas_price=10)
    replacement = signed(ALICE, 0, gas_price=11)
    rpc = FakeEthRPC()
    run(
        rpc,
        [
            MempoolTransaction(tx=original, accepted=True),
            MempoolTransaction(tx=replacement, accepted=True),
        ],
    )
    assert rpc.waited == [replacement.hash]


def test_verdict_after_a_related_inclusion_is_inconclusive() -> None:
    """
    Test that a wrong verdict is skipped when a block already included
    an admitted transaction of the same sender before it was sent.
    """
    original = signed(ALICE, 0, gas_price=100)
    underpriced = signed(ALICE, 0, gas_price=101)
    unrelated = signed(BOB, 0)
    rpc = FakeEthRPC(included={original.hash})
    with pytest.raises(pytest.skip.Exception, match="earlier transaction"):
        run(
            rpc,
            [
                MempoolTransaction(tx=original, accepted=True),
                MempoolTransaction(tx=unrelated, accepted=True),
                MempoolTransaction(tx=underpriced, accepted=False),
            ],
        )


class RecordingCheck(MempoolCheck):
    """Record whether the check ran with the lock held."""

    calls: ClassVar[List[bool]] = []
    raises: bool = False

    def check(
        self, *, fork: Any, eth_rpc: Any, engine_rpc: Any, txs: Any
    ) -> None:
        """Record the lock state, raising if asked to."""
        del fork, engine_rpc, txs
        RecordingCheck.calls.append(eth_rpc.locked)
        if self.raises:
            raise AssertionError("mempool state mismatch")


def test_checks_run_under_the_lock() -> None:
    """Test that a check sees the mempool before any block is built."""
    RecordingCheck.calls = []
    tx = signed(ALICE, 0)
    rpc = FakeEthRPC()
    run(
        rpc,
        [MempoolTransaction(tx=tx, accepted=True)],
        checks=[RecordingCheck()],
    )
    assert RecordingCheck.calls == [True]
    assert rpc.waited == [tx.hash]


def test_checks_are_skipped_on_a_wrong_verdict() -> None:
    """Test that the checks do not run once a verdict is wrong."""
    RecordingCheck.calls = []
    tx = signed(ALICE, 0)
    rpc = FakeEthRPC(rejected={tx.hash})
    with pytest.raises(pytest.fail.Exception):
        run(
            rpc,
            [MempoolTransaction(tx=tx, accepted=True)],
            checks=[RecordingCheck()],
        )
    assert RecordingCheck.calls == []


def test_admitted_txs_are_waited_on_when_a_check_fails() -> None:
    """Test that admitted txs are mined even if a check fails."""
    RecordingCheck.calls = []
    tx = signed(ALICE, 0)
    rpc = FakeEthRPC()
    with pytest.raises(AssertionError, match="mempool state mismatch"):
        run(
            rpc,
            [MempoolTransaction(tx=tx, accepted=True)],
            checks=[RecordingCheck(raises=True)],
        )
    assert rpc.waited == [tx.hash]


def test_wrapped_tx_is_sent_wrapped_and_waited_on_by_payload_hash() -> None:
    """Test that a blob tx is sent with its sidecar, keyed by its hash."""
    payload = Transaction(
        ty=3,
        sender=ALICE,
        nonce=0,
        gas_limit=21_000,
        max_fee_per_blob_gas=10,
        blob_versioned_hashes=[Blob.from_fork(Cancun).versioned_hash],
    )
    wrapped = NetworkWrappedTransaction(
        tx=payload, blob_objects=[Blob.from_fork(Cancun)]
    ).with_signature_and_sender()
    rpc = FakeEthRPC()
    rpc.hashes_by_rlp = {bytes(wrapped.rlp()): wrapped.hash}
    run(rpc, [MempoolTransaction(tx=wrapped, accepted=True)])
    assert rpc.sent == [wrapped.hash]
    assert rpc.waited == [wrapped.tx.hash]


def test_unwrapped_blob_tx_is_refused() -> None:
    """Test that a blob tx without its sidecar is never sent."""
    tx = Transaction(
        ty=3,
        sender=ALICE,
        nonce=0,
        gas_limit=21_000,
        max_fee_per_blob_gas=10,
        blob_versioned_hashes=[Blob.from_fork(Cancun).versioned_hash],
    )
    with pytest.raises(AssertionError, match="NetworkWrappedTransaction"):
        run(FakeEthRPC(), [MempoolTransaction(tx=tx, accepted=True)])


def test_benchmark_gas_sums_the_admitted_receipts() -> None:
    """Test that benchmark mode reports the gas the admitted txs used."""
    rpc = FakeEthRPC()
    result = MempoolAdmission(
        txs=[
            MempoolTransaction(tx=signed(ALICE, 0), accepted=True),
            MempoolTransaction(tx=signed(BOB, 0), accepted=True),
        ],
        benchmark_mode=True,
    ).execute(
        fork=Prague,
        eth_rpc=rpc,  # type: ignore[arg-type]
        engine_rpc=None,
        request=REQUEST,  # type: ignore[arg-type]
    )
    assert result.benchmark_gas_used == 2 * 21_000


def test_mempool_admission_mark() -> None:
    """Test that the format carries the mark selecting mempool tests."""
    assert [m.name for m in MempoolAdmission.marks()] == ["mempool_admission"]


def test_get_blobs_rejects_empty_custody_columns_updates() -> None:
    """
    Test that a getBlobs check accepts any non-empty sequence of
    `custodyColumns` updates, with `None` for an explicit `null`, and
    rejects an empty one, which would send nothing.
    """
    bitmap = b"\xff" * 16
    for updates in ([bitmap], [None], [bitmap, None], [bitmap, bitmap]):
        GetBlobs(custody_columns_updates=updates)
    with pytest.raises(ValueError, match="custody_columns_updates"):
        GetBlobs(custody_columns_updates=[])
