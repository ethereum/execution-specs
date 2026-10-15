"""Test the mempool admission execute format against a fake client."""

from contextlib import AbstractContextManager, nullcontext
from types import SimpleNamespace
from typing import Any, Dict, List, Sequence, Set

import pytest

from execution_testing.base_types import Hash
from execution_testing.forks import Bogota
from execution_testing.rpc import SendTransactionExceptionError
from execution_testing.rpc.rpc_types import JSONRPCError
from execution_testing.test_types import EOA, MempoolTransaction, Transaction

from ..mempool import MempoolAdmission

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
        self.waited: List[Hash] = []

    @property
    def transaction_polling_context(self) -> AbstractContextManager:
        """Return a no-op lock."""
        return nullcontext()

    def send_raw_transaction(
        self, transaction_rlp: Any, request_id: Any = None
    ) -> Hash:
        """Admit the transaction, or fail as `eth_rpc` would."""
        del request_id
        tx_hash = transaction_rlp.keccak256()
        if tx_hash in self.dropped:
            error: Exception = ConnectionError("connection dropped")
        elif tx_hash in self.rejected:
            error = JSONRPCError(code=-32000, message="rejected")
        else:
            return tx_hash
        raise SendTransactionExceptionError(str(error)) from error

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
        return [{} for _ in transaction_hashes]


def signed(sender: EOA, nonce: int, gas_price: int = 10) -> Transaction:
    """Return a signed transfer from `sender` at `nonce`."""
    return Transaction(
        sender=sender, nonce=nonce, gas_limit=21_000, gas_price=gas_price
    ).with_signature_and_sender()


def run(rpc: FakeEthRPC, entries: List[MempoolTransaction]) -> None:
    """Execute the format against `rpc`."""
    MempoolAdmission(txs=entries).execute(
        fork=Bogota,
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


def test_wrongly_rejected_tx_fails() -> None:
    """Test that a rejected admission case fails."""
    tx = signed(ALICE, 0)
    rpc = FakeEthRPC(rejected={tx.hash})
    with pytest.raises(pytest.fail.Exception, match="was rejected"):
        run(rpc, [MempoolTransaction(tx=tx, accepted=True)])


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
