"""Simple transaction-send then post-check execution format."""

from itertools import groupby
from typing import ClassVar, Dict, List

import pytest
from pydantic import PrivateAttr
from pytest import FixtureRequest

from execution_testing.base_types import Address, Hash, HexNumber
from execution_testing.forks import Fork
from execution_testing.logging import get_logger
from execution_testing.rpc import (
    EngineRPC,
    EthRPC,
    SendTransactionExceptionError,
)
from execution_testing.test_types import (
    Alloc,
    Environment,
    NetworkWrappedTransaction,
    TestPhase,
    Transaction,
    TransactionTestMetadata,
)

from .base import BaseExecute, ExecuteResult

logger = get_logger(__name__)


class TransactionPost(BaseExecute):
    """
    Represents a simple transaction-send then post-check execution format.
    """

    blocks: List[List[Transaction]]
    post: Alloc
    estimate_gas: bool = False
    _estimate_indices: set[tuple[int, int]] = PrivateAttr(default_factory=set)

    format_name: ClassVar[str] = "transaction_post_test"
    description: ClassVar[str] = (
        "Simple transaction sending, then post-check after all transactions "
        "are included"
    )

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
        """Prepare transactions by setting their final gas properties."""
        for block_index, block in enumerate(self.blocks):
            max_tx_gas_limit = Transaction.calculate_max_gas_limit(
                txs=block,
                env_gas_limit=int(env.gas_limit),
                transaction_gas_limit_cap=fork.transaction_gas_limit_cap(),
                state_gas_reservoir_enabled=fork.state_gas_reservoir_enabled(),
                transaction_total_gas_limit_cap=(
                    fork.transaction_total_gas_limit_cap()
                ),
            )
            for tx_index, tx in enumerate(block):
                # Decide before `set_gas_limit` marks `gas_limit` as set.
                if self._should_estimate(tx):
                    self._estimate_indices.add((block_index, tx_index))
                tx.set_gas_limit(
                    max_gas_limit=max_tx_gas_limit,
                    transaction_gas_limit_cap=fork.transaction_gas_limit_cap(),
                    state_gas_reservoir_enabled=fork.state_gas_reservoir_enabled(),
                    transaction_total_gas_limit_cap=(
                        fork.transaction_total_gas_limit_cap()
                    ),
                )
                tx.set_gas_price(
                    gas_price=gas_price,
                    max_fee_per_gas=max_fee_per_gas,
                    max_priority_fee_per_gas=max_priority_fee_per_gas,
                    max_fee_per_blob_gas=max_fee_per_blob_gas,
                )

    def _should_estimate(self, tx: Transaction) -> bool:
        """Return whether the node decides the gas limit of the transaction."""
        if not self.estimate_gas or self.benchmark_mode:
            return False
        if "gas_limit" in tx.model_fields_set:
            return False  # the test pinned the gas limit
        if "state_gas_reservoir" in tx.model_fields_set:
            return False  # the test pinned the state gas reservoir
        if tx.error is not None:
            return False  # expected to be rejected by the mempool
        receipt = tx.expected_receipt
        if receipt is not None and receipt.status == 0:
            return False  # expected to fail during execution
        return True

    def get_required_sender_balances(
        self, *, fork: Fork
    ) -> Dict[Address, int]:
        """Get the required sender balances."""
        balances: Dict[Address, int] = {}
        for block in self.blocks:
            for tx in block:
                sender = tx.sender
                assert sender is not None, "Sender is None"
                if sender not in balances:
                    balances[sender] = 0
                balances[sender] += tx.signer_minimum_balance(fork=fork)
        return balances

    @staticmethod
    def _send_transactions(
        eth_rpc: EthRPC, signed_txs: List[Transaction]
    ) -> List[Hash]:
        """Send runs of valid transactions in batches and rejections alone."""
        sent: List[Hash] = []
        for expects_rejection, run in groupby(
            signed_txs, key=lambda tx: tx.error is not None
        ):
            txs = list(run)
            if not expects_rejection:
                eth_rpc.send_wait_transactions(txs)
                sent.extend(tx.hash for tx in txs)
                continue
            for tx in txs:
                logger.info(
                    f"Sending transaction expecting rejection "
                    f"(expected error: {tx.error})..."
                )
                with pytest.raises(SendTransactionExceptionError) as exc_info:
                    eth_rpc.send_transaction(tx)
                logger.info(
                    f"Transaction rejected as expected: {exc_info.value}"
                )
        return sent

    @staticmethod
    def _estimate_transaction(eth_rpc: EthRPC, tx: Transaction) -> None:
        """Set the transaction gas limit to the node's estimate."""
        # The node simulates an unsigned call: the secret key must never
        # leave this process and the signature does not exist yet.
        call = tx.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=True,
            exclude={"secret_key", "v", "r", "s"},
        )
        call["from"] = call.pop("sender")
        if tx.to is None:
            # The t8n serializer keeps `to: None` for contract creation; the
            # RPC omits `to` instead.
            del call["to"]
        # Authorizations serialize both `v` and `yParity` for fixtures; the
        # RPC only takes `yParity`.
        for authorization in call.get("authorizationList", []):
            for key in ("secretKey", "signer", "v"):
                authorization.pop(key, None)
        estimate = eth_rpc.estimate_gas(call, block_number="latest")
        assert 0 < estimate <= tx.gas_limit, (
            f"eth_estimateGas returned {estimate}, outside the funded "
            f"gas budget (1..{tx.gas_limit})"
        )
        logger.info(f"eth_estimateGas returned {estimate} for {tx.sender}")
        tx.gas_limit = HexNumber(estimate)

    def execute(
        self,
        fork: Fork,
        eth_rpc: EthRPC,
        engine_rpc: EngineRPC | None,
        request: FixtureRequest,
    ) -> ExecuteResult:
        """Execute the format."""
        del fork
        del engine_rpc

        for block in self.blocks:
            for tx in block:
                if not isinstance(tx, NetworkWrappedTransaction):
                    assert tx.ty != 3, (
                        "Unwrapped transaction type 3 is not supported in "
                        "execute mode."
                    )

        # Track transaction hashes for gas validation (benchmarking)
        last_block_tx_hashes: List[Hash] = []

        for block_index, block in enumerate(self.blocks):
            estimated = {
                tx_index
                for index, tx_index in self._estimate_indices
                if index == block_index
            }
            signed: List[Transaction] = []
            batch: List[Transaction] = []
            last_block_tx_hashes = []
            for tx_index, tx in enumerate(block):
                if tx_index in estimated:
                    # Include everything before it, so `latest` has its state.
                    last_block_tx_hashes += self._send_transactions(
                        eth_rpc, batch
                    )
                    batch = []
                    self._estimate_transaction(eth_rpc, tx)
                # Add metadata
                tx = tx.with_signature_and_sender()
                to_address = tx.to
                label = (
                    to_address.label
                    if isinstance(to_address, Address)
                    else None
                )
                phase = (
                    tx.test_phase
                    if tx.test_phase is not None
                    else TestPhase.EXECUTION
                )
                tx.metadata = TransactionTestMetadata(
                    test_id=request.node.nodeid,
                    phase=phase,
                    target=label,
                    tx_index=tx_index,
                )
                signed.append(tx)
                batch.append(tx)
            last_block_tx_hashes += self._send_transactions(eth_rpc, batch)
            for tx_index in sorted(estimated):
                tx = signed[tx_index]
                receipt = eth_rpc.get_transaction_receipt(tx.hash)
                assert receipt is not None, f"Missing receipt: {tx.hash}"
                assert int(HexNumber(receipt["status"])) == 1, (
                    f"Transaction {tx.hash} failed with eth_estimateGas "
                    f"limit {tx.gas_limit}"
                )

        # Fetch transaction receipts to get actual gas used
        benchmark_gas_used: int | None = None
        if self.benchmark_mode:
            benchmark_gas_used = 0
            for tx_hash in last_block_tx_hashes:
                receipt = eth_rpc.get_transaction_receipt(tx_hash)
                assert receipt is not None, (
                    f"Failed to get receipt for transaction {tx_hash}"
                )
                gas_used = int(receipt["gasUsed"], 16)
                benchmark_gas_used += gas_used

        actual_alloc = eth_rpc.get_alloc(self.post)
        for address, expected_account in self.post.root.items():
            actual_account = actual_alloc.root[address]
            assert actual_account is not None
            if expected_account is None:
                assert actual_account.balance == 0, (
                    f"Balance of {address} is "
                    f"{actual_account.balance}, expected 0."
                )
                assert actual_account.code == b"", (
                    f"Code of {address} is {actual_account.code}, expected 0x."
                )
                assert actual_account.nonce == 0, (
                    f"Nonce of {address} is "
                    f"{actual_account.nonce}, expected 0."
                )
            else:
                expected_account.check_alloc(address, actual_account)

        return ExecuteResult(
            benchmark_gas_used=benchmark_gas_used,
        )
