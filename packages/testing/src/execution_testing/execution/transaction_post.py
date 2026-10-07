"""Simple transaction-send then post-check execution format."""

from typing import Any, ClassVar, Dict, List

import pytest
from pytest import FixtureRequest

from execution_testing.base_types import Address, Hash
from execution_testing.forks import Fork
from execution_testing.logging import get_logger
from execution_testing.rpc import (
    EngineRPC,
    EthRPC,
    SendTransactionExceptionError,
)
from execution_testing.test_types import (
    Account,
    Alloc,
    Environment,
    NetworkWrappedTransaction,
    PostStateContext,
    TestPhase,
    Transaction,
    TransactionTestMetadata,
)
from execution_testing.test_types.balance_expectations import (
    TransactionKey,
    TransactionLanding,
    transaction_key,
)

from .base import BaseExecute, ExecuteResult

logger = get_logger(__name__)


class RPCTransactionLanding(TransactionLanding):
    """
    Landing of a transaction on a live network, fetched piece by piece.

    The receipt is requested the first time any value is needed; the block
    is requested only for the base fee or the fee recipient, so a sender's
    `GasFee` costs a single receipt request.
    """

    _context: "RPCPostStateContext"
    _tx_hash: Hash
    _receipt: Dict[str, Any] | None

    def __init__(
        self, *, context: "RPCPostStateContext", tx_hash: Hash
    ) -> None:
        """Track the transaction `tx_hash`, without fetching anything yet."""
        self._context = context
        self._tx_hash = tx_hash
        self._receipt = None

    def receipt(self) -> Dict[str, Any]:
        """Return the transaction receipt, fetching it on first use."""
        if self._receipt is None:
            receipt = self._context.eth_rpc.get_transaction_receipt(
                self._tx_hash
            )
            assert receipt is not None, f"missing receipt for {self._tx_hash}"
            self._receipt = receipt
        return self._receipt

    def block(self) -> Dict[str, Any]:
        """Return the block the transaction landed in."""
        return self._context.block(Hash(self.receipt()["blockHash"]))

    def effective_gas_price(self) -> int:
        """Return the price per gas the transaction paid."""
        return int(self.receipt()["effectiveGasPrice"], 16)

    def base_fee_per_gas(self) -> int:
        """Return the block base fee, or zero before the London fork."""
        base_fee = self.block().get("baseFeePerGas")
        return int(base_fee, 16) if base_fee else 0

    def blob_gas_price(self) -> int | None:
        """Return the blob gas price the transaction paid, if any."""
        blob_gas_price = self.receipt().get("blobGasPrice")
        return int(blob_gas_price, 16) if blob_gas_price else None

    def fee_recipient(self) -> Address:
        """Return the block fee recipient."""
        return Address(self.block()["miner"])


class RPCPostStateContext(PostStateContext):
    """
    Context for execute, where transactions land on a live network.

    Nothing is fetched up front: each landing requests its receipt and block
    only when an expectation needs them, and each block is fetched at most
    once however many of the transactions landed in it.
    """

    eth_rpc: EthRPC
    _landings: Dict[TransactionKey, RPCTransactionLanding]
    _blocks: Dict[Hash, Dict[str, Any]]

    def __init__(self, *, eth_rpc: EthRPC, txs: List[Transaction]) -> None:
        """Track the sent `txs`, without fetching anything yet."""
        self.eth_rpc = eth_rpc
        self._landings = {
            transaction_key(tx): RPCTransactionLanding(
                context=self, tx_hash=tx.hash
            )
            for tx in txs
        }
        self._blocks = {}

    def block(self, block_hash: Hash) -> Dict[str, Any]:
        """Return the block `block_hash`, fetching it on first use."""
        if block_hash not in self._blocks:
            block = self.eth_rpc.get_block_by_hash(block_hash, full_txs=False)
            assert block is not None, f"block {block_hash} not found"
            self._blocks[block_hash] = block
        return self._blocks[block_hash]

    def landing(self, key: TransactionKey) -> TransactionLanding:
        """Return the landing of the transaction `key`."""
        if key not in self._landings:
            raise PostStateContext.TransactionNotLandedError(key)
        return self._landings[key]


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
        for block in self.blocks:
            max_tx_gas_limit = Transaction.calculate_max_gas_limit(
                txs=block,
                env_gas_limit=int(env.gas_limit),
                transaction_gas_limit_cap=fork.transaction_gas_limit_cap(),
                state_gas_reservoir_enabled=fork.state_gas_reservoir_enabled(),
                transaction_total_gas_limit_cap=(
                    fork.transaction_total_gas_limit_cap()
                ),
            )
            for tx in block:
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

    def snapshot_pre_state(self, eth_rpc: EthRPC) -> Alloc:
        """
        Fetch the live state of the post accounts that expect changes.

        The test's `pre` is not authoritative on a live network: senders are
        topped up to cover their transactions, and accounts the test did not
        create (fee recipients, precompiles, system contracts) may already
        hold a balance.
        """
        relative_fields = {"balance_change", "nonce_change"}
        relative = Alloc(
            {
                address: Account()
                for address, account in self.post.root.items()
                if account is not None
                and relative_fields & account.model_fields_set
            }
        )
        return eth_rpc.get_alloc(relative, skip_code=True)

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

        pre_state = self.snapshot_pre_state(eth_rpc)

        # Track transaction hashes for gas validation (benchmarking)
        all_tx_hashes: List[Hash] = []
        landed_txs: List[Transaction] = []
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
            landed_txs.extend(
                tx.tx if isinstance(tx, NetworkWrappedTransaction) else tx
                for tx in signed_txs
                if tx.error is None
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
        context = RPCPostStateContext(eth_rpc=eth_rpc, txs=landed_txs)
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
                expected_account.check_alloc(
                    address=address,
                    pre_account=pre_state.root.get(address),
                    account=actual_account,
                    context=context,
                )

        return ExecuteResult(
            benchmark_gas_used=benchmark_gas_used,
        )
