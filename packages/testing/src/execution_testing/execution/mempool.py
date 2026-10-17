"""Test execution format to check a client's public mempool admission."""

from typing import ClassVar, Dict, List, Tuple

import pytest
from pytest import FixtureRequest

from execution_testing.base_types import Address, Hash
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


class MempoolAdmission(BaseExecute):
    """
    Represents a test execution format that sends transactions in order
    to the client's public mempool via `eth_sendRawTransaction` and
    checks that each one is admitted or rejected as expected.
    """

    format_name: ClassVar[str] = "mempool_test"
    description: ClassVar[str] = (
        "Send transactions to the execution client and check that its "
        "public mempool admits or rejects each one"
    )

    txs: List[MempoolTransaction]

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

        Fees a test pins are kept, so replacement and payer exposure
        tests stay exact. Frame transactions derive their gas limit from
        their frames, so only their fees are set.
        """
        txs = [entry.tx for entry in self.txs]
        legacy_txs = [tx for tx in txs if tx.frames is None]
        if legacy_txs:
            max_tx_gas_limit = Transaction.calculate_max_gas_limit(
                txs=legacy_txs,
                env_gas_limit=int(env.gas_limit),
                transaction_gas_limit_cap=fork.transaction_gas_limit_cap(),
                state_gas_reservoir_enabled=(
                    fork.state_gas_reservoir_enabled()
                ),
                transaction_total_gas_limit_cap=(
                    fork.transaction_total_gas_limit_cap()
                ),
            )
            for tx in legacy_txs:
                tx.set_gas_limit(
                    max_gas_limit=max_tx_gas_limit,
                    transaction_gas_limit_cap=fork.transaction_gas_limit_cap(),
                    state_gas_reservoir_enabled=(
                        fork.state_gas_reservoir_enabled()
                    ),
                    transaction_total_gas_limit_cap=(
                        fork.transaction_total_gas_limit_cap()
                    ),
                )
        for tx in txs:
            tx.set_gas_price(
                gas_price=gas_price,
                max_fee_per_gas=max_fee_per_gas,
                max_priority_fee_per_gas=max_priority_fee_per_gas,
                max_fee_per_blob_gas=max_fee_per_blob_gas,
            )

    def get_required_sender_balances(
        self, *, fork: Fork
    ) -> Dict[Address, int]:
        """
        Get the balances the payers need to cover every transaction.

        A frame transaction charges its payer the maximum cost and its
        sender the value its frames transfer.
        """
        balances: Dict[Address, int] = {}
        for entry in self.txs:
            tx = entry.tx
            assert tx.sender is not None, "Sender is None"
            if tx.frames is None:
                balances[tx.sender] = balances.get(
                    tx.sender, 0
                ) + tx.signer_minimum_balance(fork=fork)
                continue
            tx.sign()
            payer = transaction_payer(tx)
            balances[payer] = balances.get(
                payer, 0
            ) + frame_transaction_max_cost(tx, fork)
            balances[tx.sender] = balances.get(tx.sender, 0) + sum(
                int(frame.value) for frame in tx.frames
            )
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

        The block building lock is held while sending so that no block
        includes an admitted transaction before a later one, which may
        depend on it being pending, is sent. Admitted transactions are
        then waited on, so that none is still pending at teardown, and
        unexpected verdicts are reported together.
        """
        del fork, engine_rpc
        failures: List[str] = []
        inconclusive: List[str] = []
        admitted: Dict[Tuple, Tuple[Hash, Transaction]] = {}
        with eth_rpc.transaction_polling_context:
            for tx_index, entry in enumerate(self.txs):
                tx = entry.tx.with_signature_and_sender()
                label = f"tx {tx_index}" + (
                    f" ({entry.reason})" if entry.reason else ""
                )
                metadata = TransactionTestMetadata(
                    test_id=request.node.nodeid,
                    phase="testing",
                    tx_index=tx_index,
                )
                verdict: str | None = None
                admitted_hash: Hash | None = None
                try:
                    tx_hash = eth_rpc.send_raw_transaction(
                        tx.rlp(), request_id=metadata.to_json()
                    )
                except SendTransactionExceptionError as e:
                    if not isinstance(e.__cause__, JSONRPCError):
                        raise
                    logger.info(f"{label} rejected: {e.__cause__}")
                    if entry.accepted:
                        verdict = f"{label} was rejected: {e.__cause__}"
                    elif eth_rpc.transaction_known(tx.hash):
                        verdict = (
                            f"{label} was rejected with '{e.__cause__}' "
                            "but the client knows it"
                        )
                else:
                    logger.info(f"{label} admitted as {tx_hash}")
                    admitted_hash = tx_hash
                    if tx_hash != tx.hash:
                        verdict = (
                            f"{label} was admitted as {tx_hash}, "
                            f"expected {tx.hash}"
                        )
                    elif not entry.accepted:
                        verdict = f"{label} was admitted, expected rejection"
                if verdict is not None:
                    if self._depends_on_included(tx, admitted, eth_rpc):
                        inconclusive.append(verdict)
                    else:
                        failures.append(verdict)
                if admitted_hash is not None:
                    admitted[entry.pool_key] = (admitted_hash, tx)
        try:
            eth_rpc.wait_for_receipts(
                [tx_hash for tx_hash, _ in admitted.values()]
            )
        except Exception as e:
            failures.append(f"admitted transactions were not included: {e}")
        if failures:
            pytest.fail("\n".join(failures))
        if inconclusive:
            pytest.skip(
                "A block included an earlier transaction this verdict "
                "depends on before it was sent: " + "\n".join(inconclusive)
            )
        return ExecuteResult(benchmark_gas_used=None)

    @staticmethod
    def _depends_on_included(
        tx: Transaction,
        admitted: Dict[Tuple, Tuple[Hash, Transaction]],
        eth_rpc: EthRPC,
    ) -> bool:
        """
        Check whether a block already included an admitted transaction
        sharing the sender or payer of `tx`, whose pending state the
        mempool's verdict on `tx` may depend on.
        """
        related = [
            tx_hash
            for tx_hash, other in admitted.values()
            if other.sender == tx.sender
            or transaction_payer(other) == transaction_payer(tx)
        ]
        receipts = eth_rpc.get_transaction_receipts(related)
        return any(receipt is not None for receipt in receipts)
