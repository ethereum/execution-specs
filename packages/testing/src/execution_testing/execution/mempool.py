"""Test execution format to check a client's public mempool admission."""

from typing import Any, ClassVar, Dict, List, Sequence, Tuple

import pytest
from pytest import FixtureRequest

from execution_testing.base_types import Address, CamelModel, Hash
from execution_testing.forks import Fork
from execution_testing.logging import (
    get_logger,
)
from execution_testing.rpc import (
    EngineRPC,
    EthRPC,
    SendTransactionExceptionError,
)
from execution_testing.rpc.rpc_types import JSONRPCError
from execution_testing.test_types import (
    Environment,
    MempoolTransaction,
    TestPhase,
    Transaction,
)
from execution_testing.test_types.transaction_types import (
    TransactionTestMetadata,
)

from .base import BaseExecute, ExecuteResult

logger = get_logger(__name__)


VERIFY_FRAME_MODE = 1
"""Mode of a frame that runs before execution to grant approvals."""

APPROVE_PAYMENT = 0x1
"""Frame flag allowing the frame to approve the transaction's payment."""


def transaction_payer(tx: Transaction) -> Address:
    """
    Return the account a transaction charges: for a frame transaction,
    the target of the first `VERIFY` frame allowed to approve payment
    (the sender for a null target), otherwise the sender.
    """
    assert tx.sender is not None, "Sender is None"
    for frame in tx.frames or []:
        if int(frame.mode) != VERIFY_FRAME_MODE:
            continue
        if int(frame.flags) & APPROVE_PAYMENT:
            return frame.target if frame.target is not None else tx.sender
    return tx.sender


def frame_transaction_max_cost(tx: Transaction, fork: Fork) -> int:
    """
    Return the escrow a signed frame transaction collects from its payer
    when payment is approved: its derived gas limit at the maximum fee
    per gas, plus its blob gas at the maximum fee per blob gas.
    """
    assert tx.frames is not None and tx.signatures is not None
    max_gas = fork.frame_transaction_intrinsic_cost_calculator()(
        frames=tx.frames,
        signatures=tx.signatures,
        sender=tx.sender,
        nonce_keys=[int(key) for key in tx.nonce_keys or (0,)],
        nonce_seq=int(tx.nonce),
    )
    blob_gas = fork.blob_gas_per_blob() * len(tx.blob_versioned_hashes or [])
    return max_gas * int(tx.max_fee_per_gas or 0) + blob_gas * int(
        tx.max_fee_per_blob_gas or 0
    )


class AdmittedTransaction:
    """A transaction the client admitted, and whether it can land."""

    def __init__(self, tx_hash: Hash, tx: Transaction) -> None:
        """Record the admitted `tx` under the hash the client returned."""
        self.tx_hash = tx_hash
        self.tx = tx
        # A transaction invalid in a block never lands, so it is not
        # waited on even when the client wrongly admits it.
        self.lands = tx.error is None


class MempoolCheck(CamelModel):
    """
    A check of the client's mempool, run once every transaction is sent
    and before any block includes one.
    """

    def check(
        self,
        *,
        fork: Fork,
        eth_rpc: EthRPC,
        engine_rpc: EngineRPC | None,
        txs: Sequence[MempoolTransaction],
    ) -> None:
        """Check the mempool's state after `txs` were sent."""
        raise NotImplementedError(
            f"{self.__class__.__name__} does not implement `check`"
        )


class MempoolAdmission(BaseExecute):
    """
    Represents a test execution format that sends transactions in order
    to the client's public mempool via `eth_sendRawTransaction`, checks
    that each one is admitted or rejected as expected, then runs the
    mempool checks.
    """

    format_name: ClassVar[str] = "mempool_admission"
    description: ClassVar[str] = (
        "Send transactions to the execution client and check that its "
        "public mempool admits or rejects each one"
    )

    txs: List[MempoolTransaction]
    checks: List[MempoolCheck] = []

    def prepare_transactions(
        self,
        *,
        env: Environment,
        gas_price: int,
        max_fee_per_gas: int,
        max_priority_fee_per_gas: int,
        max_fee_per_blob_gas: int,
        fork: Fork,
    ) -> None:
        """
        Prepare transactions by setting their final gas properties.

        Gas limits and fees a test pins are kept, so tests depending on
        exact fees, such as replacements, stay exact. Frame transactions
        derive their gas limit from their frames, so only their fees are
        set.
        """
        txs = [entry.unwrapped for entry in self.txs]
        legacy_txs = [tx for tx in txs if tx.frames is None]
        for tx in txs:
            tx.set_gas_price(
                gas_price=gas_price,
                max_fee_per_gas=max_fee_per_gas,
                max_priority_fee_per_gas=max_priority_fee_per_gas,
                max_fee_per_blob_gas=max_fee_per_blob_gas,
            )
        if not legacy_txs:
            return
        max_tx_gas_limit = Transaction.calculate_max_gas_limit(
            txs=legacy_txs,
            env_gas_limit=int(env.gas_limit),
            transaction_gas_limit_cap=fork.transaction_gas_limit_cap(),
            state_gas_reservoir_enabled=fork.state_gas_reservoir_enabled(),
            transaction_total_gas_limit_cap=(
                fork.transaction_total_gas_limit_cap()
            ),
        )
        for tx in legacy_txs:
            tx.set_gas_limit(
                max_gas_limit=max_tx_gas_limit,
                transaction_gas_limit_cap=fork.transaction_gas_limit_cap(),
                state_gas_reservoir_enabled=fork.state_gas_reservoir_enabled(),
                transaction_total_gas_limit_cap=(
                    fork.transaction_total_gas_limit_cap()
                ),
            )

    def get_required_sender_balances(
        self, *, fork: Fork
    ) -> Dict[Address, int]:
        """
        Get the balances the payers need to cover every transaction.

        A frame transaction charges its payer the maximum cost and its
        sender the value its frames transfer. Authorization signers are
        listed with no balance, so a deferred EOA that only signs an
        authorization is created.
        """
        balances: Dict[Address, int] = {}
        for entry in self.txs:
            tx = entry.unwrapped
            payer = transaction_payer(tx)
            if tx.frames is None:
                balances[payer] = balances.get(
                    payer, 0
                ) + entry.tx.signer_minimum_balance(fork=fork)
            else:
                assert tx.sender is not None, "Sender is None"
                tx.sign()
                balances[payer] = balances.get(
                    payer, 0
                ) + frame_transaction_max_cost(tx, fork)
                balances[tx.sender] = balances.get(tx.sender, 0) + sum(
                    int(frame.value) for frame in tx.frames
                )
            for authorization in tx.authorization_list or []:
                if authorization.signer is not None:
                    balances.setdefault(authorization.signer, 0)
        return balances

    def execute(
        self,
        fork: Fork,
        eth_rpc: EthRPC,
        engine_rpc: EngineRPC | None,
        request: FixtureRequest,
    ) -> ExecuteResult:
        """
        Send each transaction and check the mempool's verdict.

        The block building lock is held while sending and checking so
        that no block includes an admitted transaction before a later one,
        which may depend on it being pending, is sent, or before the
        mempool checks see it. Admitted transactions are then waited on,
        so that none is still pending at teardown, and unexpected verdicts
        are reported together.
        """
        failures: List[str] = []
        inconclusive: List[str] = []
        admitted: Dict[Tuple, AdmittedTransaction] = {}
        receipts: List[Dict[str, Any]] = []
        try:
            with eth_rpc.transaction_polling_context:
                for tx_index, entry in enumerate(self.txs):
                    self._send(
                        entry,
                        tx_index,
                        eth_rpc=eth_rpc,
                        request=request,
                        admitted=admitted,
                        failures=failures,
                        inconclusive=inconclusive,
                    )
                # The checks run before any block includes an admitted
                # transaction, and only once every verdict matched.
                if not failures and not inconclusive:
                    for check in self.checks:
                        check.check(
                            fork=fork,
                            eth_rpc=eth_rpc,
                            engine_rpc=engine_rpc,
                            txs=self.txs,
                        )
        finally:
            landing = [a.tx_hash for a in admitted.values() if a.lands]
            try:
                receipts = eth_rpc.wait_for_receipts(landing)
            except Exception as e:
                failures.append(
                    f"admitted transactions were not included: {e}"
                )
        if failures:
            pytest.fail("\n".join(failures))
        if inconclusive:
            pytest.skip(
                "A block included an earlier transaction this verdict "
                "depends on before it was sent: " + "\n".join(inconclusive)
            )
        benchmark_gas_used = None
        if self.benchmark_mode:
            benchmark_gas_used = sum(
                int(receipt["gasUsed"], 16) for receipt in receipts
            )
        return ExecuteResult(benchmark_gas_used=benchmark_gas_used)

    def _send(
        self,
        entry: MempoolTransaction,
        tx_index: int,
        *,
        eth_rpc: EthRPC,
        request: FixtureRequest,
        admitted: Dict[Tuple, AdmittedTransaction],
        failures: List[str],
        inconclusive: List[str],
    ) -> None:
        """Send one transaction and record the mempool's verdict on it."""
        assert not (isinstance(entry.tx, Transaction) and entry.tx.ty == 3), (
            "Type-3 transaction must be wrapped in NetworkWrappedTransaction "
            "to be sent with its blobs"
        )
        signed = entry.tx.with_signature_and_sender()
        tx = entry.unwrapped
        label = f"tx {tx_index}" + (
            f" ({entry.reason})" if entry.reason else ""
        )
        metadata = TransactionTestMetadata(
            test_id=request.node.nodeid,
            phase=tx.test_phase or TestPhase.EXECUTION,
            target=tx.to.label if isinstance(tx.to, Address) else None,
            tx_index=tx_index,
        )
        verdict: str | None = None
        admitted_hash: Hash | None = None
        try:
            admitted_hash = eth_rpc.send_raw_transaction(
                signed.rlp(), request_id=metadata.to_json()
            )
        except SendTransactionExceptionError as e:
            if not isinstance(e.__cause__, JSONRPCError):
                raise
            known = eth_rpc.transaction_known(signed.hash)
            logger.info(f"{label} rejected: {e.__cause__}")
            if entry.accepted is not False and known:
                # A retried send of a delivered transaction is answered
                # as a duplicate.
                logger.warning(f"{label} rejected but known; admitted")
                admitted_hash = signed.hash
            elif entry.accepted:
                verdict = f"{label} was rejected: {e.__cause__}"
            elif entry.accepted is False and known:
                verdict = (
                    f"{label} was rejected with '{e.__cause__}' "
                    "but the client knows it"
                )
        else:
            logger.info(f"{label} admitted as {admitted_hash}")
            if admitted_hash != signed.hash:
                verdict = (
                    f"{label} was admitted as {admitted_hash}, "
                    f"expected {signed.hash}"
                )
            elif entry.accepted is False:
                verdict = f"{label} was admitted, expected rejection"
        if verdict is not None:
            if self._depends_on_included(tx, admitted, eth_rpc):
                inconclusive.append(verdict)
            else:
                failures.append(verdict)
        if admitted_hash is not None:
            admitted[entry.pool_key] = AdmittedTransaction(admitted_hash, tx)

    @staticmethod
    def _depends_on_included(
        tx: Transaction,
        admitted: Dict[Tuple, AdmittedTransaction],
        eth_rpc: EthRPC,
    ) -> bool:
        """
        Check whether a block already included an admitted transaction
        sharing the sender or payer of `tx`, whose pending state the
        mempool's verdict on `tx` may depend on.
        """
        related = [
            entry.tx_hash
            for entry in admitted.values()
            if entry.tx.sender == tx.sender
            or transaction_payer(entry.tx) == transaction_payer(tx)
        ]
        receipts = eth_rpc.get_transaction_receipts(related)
        return any(receipt is not None for receipt in receipts)
