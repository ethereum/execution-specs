"""Simple transaction-send then post-check execution format."""

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
            )
            for tx_index, tx in enumerate(block):
                if (
                    self.estimate_gas
                    and not self.benchmark_mode
                    and not tx.model_fields_set.intersection(
                        {"gas_limit", "state_gas_reservoir", "v", "r", "s"}
                    )
                    and tx.error is None
                    and (
                        tx.expected_receipt is None
                        or tx.expected_receipt.status != 0
                    )
                ):
                    self._estimate_indices.add((block_index, tx_index))
                tx.set_gas_limit(
                    max_gas_limit=max_tx_gas_limit,
                    transaction_gas_limit_cap=fork.transaction_gas_limit_cap(),
                    state_gas_reservoir_enabled=fork.state_gas_reservoir_enabled(),
                )
                tx.set_gas_price(
                    gas_price=gas_price,
                    max_fee_per_gas=max_fee_per_gas,
                    max_priority_fee_per_gas=max_priority_fee_per_gas,
                    max_fee_per_blob_gas=max_fee_per_blob_gas,
                )

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
        """Send a batch, checking any expected transaction rejections."""
        if not signed_txs:
            return []
        current_block_tx_hashes: List[Hash] = []
        if any(tx.error is not None for tx in signed_txs):
            tx_queue: List[Transaction] = []
            for transaction in signed_txs:
                if transaction.error is None:
                    tx_queue.append(transaction)
                else:
                    if tx_queue:
                        eth_rpc.send_wait_transactions(tx_queue)
                        current_block_tx_hashes.extend(
                            tx.hash for tx in tx_queue
                        )
                        tx_queue = []
                    logger.info(
                        f"Sending transaction expecting rejection "
                        f"(expected error: {transaction.error})..."
                    )
                    with pytest.raises(
                        SendTransactionExceptionError
                    ) as exc_info:
                        eth_rpc.send_transaction(transaction)
                    logger.info(
                        f"Transaction rejected as expected: {exc_info.value}"
                    )
            if tx_queue:
                eth_rpc.send_wait_transactions(tx_queue)
                current_block_tx_hashes.extend(tx.hash for tx in tx_queue)
        else:
            # Send transactions (batching is handled by eth_rpc internally)
            eth_rpc.send_wait_transactions(signed_txs)
            current_block_tx_hashes = [tx.hash for tx in signed_txs]
        return current_block_tx_hashes

    @staticmethod
    def _estimate_transaction(eth_rpc: EthRPC, tx: Transaction) -> None:
        """Estimate within the funded budget using only RPC fields."""
        assert tx.sender is not None, "Sender is None"
        # Only RPC transaction fields belong in the request. In particular,
        # never serialize secret_key, sender.key, metadata, or blob sidecars.
        transaction = tx.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=True,
            include={
                "ty",
                "chain_id",
                "nonce",
                "to",
                "value",
                "data",
                "gas_limit",
                "gas_price",
                "max_fee_per_gas",
                "max_priority_fee_per_gas",
                "access_list",
                "authorization_list",
                "max_fee_per_blob_gas",
                "blob_versioned_hashes",
            },
        )
        if tx.to is None:
            transaction.pop("to", None)
        if tx.authorization_list is not None:
            transaction["authorizationList"] = [
                {
                    key: value
                    for key, value in authorization.items()
                    if key
                    in {"chainId", "address", "nonce", "yParity", "r", "s"}
                }
                for authorization in transaction["authorizationList"]
            ]
        transaction["from"] = str(tx.sender)
        estimate = eth_rpc.estimate_gas(transaction, block_number="latest")
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
        all_tx_hashes: List[Hash] = []
        last_block_tx_hashes: List[Hash] = []

        for block_index, block in enumerate(self.blocks):
            signed_txs: List[Transaction] = []
            current_block_tx_hashes: List[Hash] = []
            for tx_index, tx in enumerate(block):
                estimate = (block_index, tx_index) in self._estimate_indices
                if estimate:
                    # Settle dependencies before estimating against latest.
                    current_block_tx_hashes.extend(
                        self._send_transactions(eth_rpc, signed_txs)
                    )
                    signed_txs = []
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
                if estimate:
                    current_block_tx_hashes.extend(
                        self._send_transactions(eth_rpc, [tx])
                    )
                    receipt = eth_rpc.get_transaction_receipt(tx.hash)
                    assert receipt is not None, f"Missing receipt: {tx.hash}"
                    assert int(HexNumber(receipt["status"])) == 1, (
                        f"Transaction {tx.hash} failed with eth_estimateGas "
                        f"limit {tx.gas_limit}"
                    )
                else:
                    signed_txs.append(tx)
            current_block_tx_hashes.extend(
                self._send_transactions(eth_rpc, signed_txs)
            )
            all_tx_hashes.extend(current_block_tx_hashes)
            last_block_tx_hashes = current_block_tx_hashes

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
