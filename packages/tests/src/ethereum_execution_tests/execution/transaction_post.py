"""Simple transaction-send then post-check execution format."""

from typing import ClassVar, List

import pytest
from pytest import FixtureRequest

from ethereum_test_base_types import Address, Alloc, Hash
from ethereum_test_forks import Fork
from ethereum_test_rpc import EngineRPC, EthRPC, SendTransactionExceptionError
from ethereum_test_types import Transaction, TransactionTestMetadata

from .base import BaseExecute


class TransactionPost(BaseExecute):
    """
    Represents a simple transaction-send then post-check execution format.
    """

    blocks: List[List[Transaction]]
    post: Alloc
    # Gas validation fields for benchmark tests
    expected_benchmark_gas_used: int | None = (
        None  # Expected total gas to be consumed
    )
    skip_gas_used_validation: bool = (
        False  # Skip gas validation even if expected is set
    )

    format_name: ClassVar[str] = "transaction_post_test"
    description: ClassVar[str] = (
        "Simple transaction sending, then post-check after all transactions are included"
    )

    def execute(
        self,
        fork: Fork,
        eth_rpc: EthRPC,
        engine_rpc: EngineRPC | None,
        request: FixtureRequest,
    ) -> None:
        """Execute the format."""
        del fork
        del engine_rpc
        assert not any(tx.ty == 3 for block in self.blocks for tx in block), (
            "Transaction type 3 is not supported in execute mode."
        )

        # Track transaction hashes for gas validation (benchmarking)
        all_tx_hashes = []

        for block in self.blocks:
            signed_txs = []
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
                    "testing"
                    if (tx.test_phase == "execution" or tx.test_phase is None)
                    else "setup"
                )
                tx.metadata = TransactionTestMetadata(
                    test_id=request.node.nodeid,
                    phase=phase,
                    target=label,
                    tx_index=tx_index,
                )
                signed_txs.append(tx)
            if any(tx.error is not None for tx in signed_txs):
                for transaction in signed_txs:
                    if transaction.error is None:
                        eth_rpc.send_wait_transaction(transaction)
                        all_tx_hashes.append(transaction.hash)
                    else:
                        with pytest.raises(SendTransactionExceptionError):
                            eth_rpc.send_transaction(transaction)
            else:
                eth_rpc.send_wait_transactions(signed_txs)
                all_tx_hashes.extend([tx.hash for tx in signed_txs])

        # Perform gas validation if required for benchmarking
        # Ensures benchmark tests consume exactly the expected gas
        if (
            not self.skip_gas_used_validation
            and self.expected_benchmark_gas_used is not None
        ):
            total_gas_used = 0
            # Fetch transaction receipts to get actual gas used
            for tx_hash in all_tx_hashes:
                receipt = eth_rpc.get_transaction_receipt(tx_hash)
                assert receipt is not None, (
                    f"Failed to get receipt for transaction {tx_hash}"
                )
                gas_used = int(receipt["gasUsed"], 16)
                total_gas_used += gas_used

            # Verify that the total gas consumed matches expectations
            assert total_gas_used == self.expected_benchmark_gas_used, (
                f"Total gas used ({total_gas_used}) does not match "
                f"expected benchmark gas ({self.expected_benchmark_gas_used}), "
                f"difference: {total_gas_used - self.expected_benchmark_gas_used}"
            )

        for address, account in self.post.root.items():
            balance = eth_rpc.get_balance(address)
            code = eth_rpc.get_code(address)
            nonce = eth_rpc.get_transaction_count(address)
            if account is None:
                assert balance == 0, (
                    f"Balance of {address} is {balance}, expected 0."
                )
                assert code == b"", (
                    f"Code of {address} is {code}, expected 0x."
                )
                assert nonce == 0, (
                    f"Nonce of {address} is {nonce}, expected 0."
                )
            else:
                if "balance" in account.model_fields_set:
                    assert balance == account.balance, (
                        f"Balance of {address} is {balance}, expected {account.balance}."
                    )
                if "code" in account.model_fields_set:
                    assert code == account.code, (
                        f"Code of {address} is {code}, expected {account.code}."
                    )
                if "nonce" in account.model_fields_set:
                    assert nonce == account.nonce, (
                        f"Nonce of {address} is {nonce}, expected {account.nonce}."
                    )
                if "storage" in account.model_fields_set:
                    for key, value in account.storage.items():
                        storage_value = eth_rpc.get_storage_at(
                            address, Hash(key)
                        )
                        assert storage_value == value, (
                            f"Storage value at {key} of {address} is {storage_value},"
                            f"expected {value}."
                        )
