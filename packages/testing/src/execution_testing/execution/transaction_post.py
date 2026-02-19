"""Simple transaction-send then post-check execution format."""

from typing import ClassVar, Dict, List

import pytest
from pytest import FixtureRequest

from execution_testing.base_types import Address, Alloc, Hash
from execution_testing.forks import Fork
from execution_testing.logging import get_logger
from execution_testing.rpc import (
    EngineRPC,
    EthRPC,
    SendTransactionExceptionError,
)
from execution_testing.test_types import (
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

    format_name: ClassVar[str] = "transaction_post_test"
    description: ClassVar[str] = (
        "Simple transaction sending, then post-check after all transactions "
        "are included"
    )

    def get_required_sender_balances(
        self,
        *,
        gas_price: int,
        max_fee_per_gas: int,
        max_priority_fee_per_gas: int,
        max_fee_per_blob_gas: int,
        fork: Fork,
    ) -> Dict[Address, int]:
        """Get the required sender balances."""
        balances: Dict[Address, int] = {}
        for block in self.blocks:
            for tx in block:
                sender = tx.sender
                assert sender is not None, "Sender is None"
                tx.set_gas_price(
                    gas_price=gas_price,
                    max_fee_per_gas=max_fee_per_gas,
                    max_priority_fee_per_gas=max_priority_fee_per_gas,
                    max_fee_per_blob_gas=max_fee_per_blob_gas,
                )
                if sender not in balances:
                    balances[sender] = 0
                balances[sender] += tx.signer_minimum_balance(fork=fork)
        return balances

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

        for block in self.blocks:
            signed_txs: List[Transaction] = []
            for tx_index, tx in enumerate(block):
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
                signed_txs.append(tx)
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
                            "Transaction rejected as expected: "
                            f"{exc_info.value}"
                        )
                if tx_queue:
                    eth_rpc.send_wait_transactions(tx_queue)
                    current_block_tx_hashes.extend(tx.hash for tx in tx_queue)
            else:
                # Send transactions (batching is handled by eth_rpc internally)
                eth_rpc.send_wait_transactions(signed_txs)
                current_block_tx_hashes = [tx.hash for tx in signed_txs]
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
