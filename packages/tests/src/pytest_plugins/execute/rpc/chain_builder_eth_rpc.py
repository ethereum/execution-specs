"""
Chain builder Ethereum RPC that can drive the chain when new transactions are
submitted.
"""

import time
from pathlib import Path
from typing import Any, Dict, Iterator, List

from filelock import FileLock
from pydantic import RootModel
from typing_extensions import Self

from ethereum_test_base_types import HexNumber
from ethereum_test_forks import Fork
from ethereum_test_rpc import EngineRPC
from ethereum_test_rpc import EthRPC as BaseEthRPC
from ethereum_test_rpc.rpc_types import (
    ForkchoiceState,
    PayloadAttributes,
    PayloadStatusEnum,
    TransactionByHashResponse,
)
from ethereum_test_tools import (
    Address,
    Hash,
    Transaction,
)
from ethereum_test_types.trie import keccak256


class HashList(RootModel[List[Hash]]):
    """Hash list class."""

    root: List[Hash]

    def append(self, item: Hash) -> None:
        """Append an item to the list."""
        self.root.append(item)

    def clear(self) -> None:
        """Clear the list."""
        self.root.clear()

    def remove(self, item: Hash) -> None:
        """Remove an item from the list."""
        self.root.remove(item)

    def __contains__(self, item: Hash) -> bool:
        """Check if an item is in the list."""
        return item in self.root

    def __len__(self) -> int:
        """Get the length of the list."""
        return len(self.root)

    def __iter__(self) -> Iterator[Hash]:  # type: ignore
        """Iterate over the list."""
        return iter(self.root)


class AddressList(RootModel[List[Address]]):
    """Address list class."""

    root: List[Address]

    def append(self, item: Address) -> None:
        """Append an item to the list."""
        self.root.append(item)

    def clear(self) -> None:
        """Clear the list."""
        self.root.clear()

    def remove(self, item: Address) -> None:
        """Remove an item from the list."""
        self.root.remove(item)

    def __contains__(self, item: Address) -> bool:
        """Check if an item is in the list."""
        return item in self.root

    def __len__(self) -> int:
        """Get the length of the list."""
        return len(self.root)

    def __iter__(self) -> Iterator[Address]:  # type: ignore
        """Iterate over the list."""
        return iter(self.root)


class PendingTxHashes:
    """
    A class to manage the pending transaction hashes in a multi-process
    environment.

    It uses a lock file to ensure that only one process can access the pending
    hashes file at a time.
    """

    pending_hashes_file: Path
    pending_hashes_lock: Path
    pending_tx_hashes: HashList | None
    lock: FileLock | None

    def __init__(self, temp_folder: Path):
        """Initialize the pending transaction hashes manager."""
        self.pending_hashes_file = temp_folder / "pending_tx_hashes"
        self.pending_hashes_lock = temp_folder / "pending_tx_hashes.lock"
        self.pending_tx_hashes = None
        self.lock = None

    def __enter__(self) -> Self:
        """Lock the pending hashes file and load it."""
        assert self.lock is None, "Lock already acquired"
        self.lock = FileLock(self.pending_hashes_lock, timeout=-1)
        self.lock.acquire()
        assert self.pending_tx_hashes is None, (
            "Pending transaction hashes already loaded"
        )
        if self.pending_hashes_file.exists():
            with open(self.pending_hashes_file, "r") as f:
                self.pending_tx_hashes = HashList.model_validate_json(f.read())
        else:
            self.pending_tx_hashes = HashList([])
        return self

    def __exit__(
        self, exc_type: object, exc_value: object, traceback: object
    ) -> None:
        """Flush the pending hashes to the file and release the lock."""
        assert self.lock is not None, "Lock not acquired"
        assert self.pending_tx_hashes is not None, (
            "Pending transaction hashes not loaded"
        )
        with open(self.pending_hashes_file, "w") as f:
            f.write(self.pending_tx_hashes.model_dump_json())
        self.lock.release()
        self.lock = None
        self.pending_tx_hashes = None

    def append(self, tx_hash: Hash) -> None:
        """Add a transaction hash to the pending list."""
        assert self.lock is not None, "Lock not acquired"
        assert self.pending_tx_hashes is not None, (
            "Pending transaction hashes not loaded"
        )
        self.pending_tx_hashes.append(tx_hash)

    def clear(self) -> None:
        """Remove a transaction hash from the pending list."""
        assert self.lock is not None, "Lock not acquired"
        assert self.pending_tx_hashes is not None
        self.pending_tx_hashes.clear()

    def remove(self, tx_hash: Hash) -> None:
        """Remove a transaction hash from the pending list."""
        assert self.lock is not None, "Lock not acquired"
        assert self.pending_tx_hashes is not None, (
            "Pending transaction hashes not loaded"
        )
        self.pending_tx_hashes.remove(tx_hash)

    def __contains__(self, tx_hash: Hash) -> bool:
        """Check if a transaction hash is in the pending list."""
        assert self.lock is not None, "Lock not acquired"
        assert self.pending_tx_hashes is not None, (
            "Pending transaction hashes not loaded"
        )
        return tx_hash in self.pending_tx_hashes

    def __len__(self) -> int:
        """Get the number of pending transaction hashes."""
        assert self.lock is not None, "Lock not acquired"
        assert self.pending_tx_hashes is not None, (
            "Pending transaction hashes not loaded"
        )
        return len(self.pending_tx_hashes)

    def __iter__(self) -> Iterator[Hash]:
        """Iterate over the pending transaction hashes."""
        assert self.lock is not None, "Lock not acquired"
        assert self.pending_tx_hashes is not None, (
            "Pending transaction hashes not loaded"
        )
        return iter(self.pending_tx_hashes)


class ChainBuilderEthRPC(BaseEthRPC, namespace="eth"):
    """
    Special type of Ethereum RPC client that also has access to the Engine API
    and automatically coordinates block generation based on the number of
    pending transactions or a block generation interval.
    """

    fork: Fork
    engine_rpc: EngineRPC
    transactions_per_block: int
    get_payload_wait_time: float
    pending_tx_hashes: PendingTxHashes

    def __init__(
        self,
        *,
        rpc_endpoint: str,
        fork: Fork,
        engine_rpc: EngineRPC,
        transactions_per_block: int,
        session_temp_folder: Path,
        get_payload_wait_time: float,
        initial_forkchoice_update_retries: int = 5,
        transaction_wait_timeout: int = 60,
    ):
        """Initialize the Ethereum RPC client for the hive simulator."""
        super().__init__(
            rpc_endpoint,
            transaction_wait_timeout=transaction_wait_timeout,
        )
        self.fork = fork
        self.engine_rpc = engine_rpc
        self.transactions_per_block = transactions_per_block
        self.pending_tx_hashes = PendingTxHashes(session_temp_folder)
        self.get_payload_wait_time = get_payload_wait_time

        # Send initial forkchoice updated only if we are the first worker
        base_name = "eth_rpc_forkchoice_updated"
        base_file = session_temp_folder / base_name
        base_error_file = session_temp_folder / f"{base_name}.err"
        base_lock_file = session_temp_folder / f"{base_name}.lock"

        with FileLock(base_lock_file):
            if base_error_file.exists():
                raise Exception(
                    "Error occurred during initial forkchoice_updated"
                )
            if not base_file.exists():
                base_error_file.touch()  # Assume error
                # Get the head block hash
                head_block = self.get_block_by_number("latest")
                assert head_block is not None
                # Send initial forkchoice updated
                forkchoice_state = ForkchoiceState(
                    head_block_hash=head_block["hash"],
                )
                forkchoice_version = (
                    self.fork.engine_forkchoice_updated_version()
                )
                assert forkchoice_version is not None, (
                    "Fork does not support engine forkchoice_updated"
                )
                for _ in range(initial_forkchoice_update_retries):
                    response = self.engine_rpc.forkchoice_updated(
                        forkchoice_state,
                        None,
                        version=forkchoice_version,
                    )
                    if (
                        response.payload_status.status
                        == PayloadStatusEnum.VALID
                    ):
                        break
                    time.sleep(0.5)
                else:
                    raise Exception("Initial forkchoice_updated was invalid")
                base_error_file.unlink()  # Success
                base_file.touch()

    def generate_block(self: "ChainBuilderEthRPC") -> None:
        """Generate a block using the Engine API."""
        # Get the head block hash
        head_block = self.get_block_by_number("latest")
        assert head_block is not None

        forkchoice_state = ForkchoiceState(
            head_block_hash=head_block["hash"],
        )
        parent_beacon_block_root = (
            Hash(0)
            if self.fork.header_beacon_root_required(
                block_number=0, timestamp=0
            )
            else None
        )
        payload_attributes = PayloadAttributes(
            timestamp=HexNumber(head_block["timestamp"]) + 1,
            prev_randao=Hash(0),
            suggested_fee_recipient=Address(0),
            withdrawals=[]
            if self.fork.header_withdrawals_required()
            else None,
            parent_beacon_block_root=parent_beacon_block_root,
            target_blobs_per_block=(
                self.fork.target_blobs_per_block(block_number=0, timestamp=0)
                if self.fork.engine_payload_attribute_target_blobs_per_block(
                    block_number=0, timestamp=0
                )
                else None
            ),
            max_blobs_per_block=(
                self.fork.max_blobs_per_block(block_number=0, timestamp=0)
                if self.fork.engine_payload_attribute_max_blobs_per_block(
                    block_number=0, timestamp=0
                )
                else None
            ),
        )
        forkchoice_updated_version = (
            self.fork.engine_forkchoice_updated_version()
        )
        assert forkchoice_updated_version is not None, (
            "Fork does not support engine forkchoice_updated"
        )
        response = self.engine_rpc.forkchoice_updated(
            forkchoice_state,
            payload_attributes,
            version=forkchoice_updated_version,
        )
        assert response.payload_status.status == PayloadStatusEnum.VALID, (
            "Payload was invalid"
        )
        assert response.payload_id is not None, (
            "payload_id was not returned by the client"
        )
        time.sleep(self.get_payload_wait_time)
        get_payload_version = self.fork.engine_get_payload_version()
        assert get_payload_version is not None, (
            "Fork does not support engine get_payload"
        )
        new_payload = self.engine_rpc.get_payload(
            response.payload_id,
            version=get_payload_version,
        )
        new_payload_args: List[Any] = [new_payload.execution_payload]
        if new_payload.blobs_bundle is not None:
            new_payload_args.append(
                new_payload.blobs_bundle.blob_versioned_hashes()
            )
        if parent_beacon_block_root is not None:
            new_payload_args.append(parent_beacon_block_root)
        if new_payload.execution_requests is not None:
            new_payload_args.append(new_payload.execution_requests)
        new_payload_version = self.fork.engine_new_payload_version()
        assert new_payload_version is not None, (
            "Fork does not support engine new_payload"
        )
        new_payload_response = self.engine_rpc.new_payload(
            *new_payload_args, version=new_payload_version
        )
        assert new_payload_response.status == PayloadStatusEnum.VALID, (
            "Payload was invalid"
        )

        new_forkchoice_state = ForkchoiceState(
            head_block_hash=new_payload.execution_payload.block_hash,
        )
        response = self.engine_rpc.forkchoice_updated(
            new_forkchoice_state,
            None,
            version=forkchoice_updated_version,
        )
        assert response.payload_status.status == PayloadStatusEnum.VALID, (
            "Payload was invalid"
        )
        for tx in new_payload.execution_payload.transactions:
            tx_hash = Hash(keccak256(tx))
            if tx_hash in self.pending_tx_hashes:
                self.pending_tx_hashes.remove(tx_hash)

    def send_transaction(self, transaction: Transaction) -> Hash:
        """`eth_sendRawTransaction`: Send a transaction to the client."""
        returned_hash = super().send_transaction(transaction)
        with self.pending_tx_hashes:
            self.pending_tx_hashes.append(transaction.hash)
            if len(self.pending_tx_hashes) >= self.transactions_per_block:
                self.generate_block()
        return returned_hash

    def wait_for_transaction(
        self, transaction: Transaction
    ) -> TransactionByHashResponse:
        """
        Wait for a specific transaction to be included in a block.

        Waits for a specific transaction to be included in a block by polling
        `eth_getTransactionByHash` until it is confirmed or a timeout occurs.

        Args:
            transaction: The transaction to track.

        Returns:
            The transaction details after it is included in a block.

        """
        return self.wait_for_transactions([transaction])[0]

    def wait_for_transactions(
        self, transactions: List[Transaction]
    ) -> List[TransactionByHashResponse]:
        """
        Wait for all transactions in the provided list to be included in a
        block.

        Waits for all transactions in the provided list to be included in a
        block by polling `eth_getTransactionByHash` until they are confirmed or
        a timeout occurs.

        Args:
            transactions: A list of transactions to track.

        Returns:
            A list of transaction details after they are included in a block.

        Raises:
            Exception: If one or more transactions are not included in a block
                within the timeout period.

        """
        tx_hashes = [tx.hash for tx in transactions]
        responses: List[TransactionByHashResponse] = []
        pending_responses: Dict[Hash, TransactionByHashResponse] = {}

        start_time = time.time()
        pending_transactions_handler = PendingTransactionHandler(self)
        while True:
            tx_id = 0
            pending_responses = {}
            while tx_id < len(tx_hashes):
                tx_hash = tx_hashes[tx_id]
                tx = self.get_transaction_by_hash(tx_hash)
                assert tx is not None, f"Transaction {tx_hash} not found"
                if tx.block_number is not None:
                    responses.append(tx)
                    tx_hashes.pop(tx_id)
                else:
                    pending_responses[tx_hash] = tx
                    tx_id += 1

            if not tx_hashes:
                return responses

            pending_transactions_handler.handle()

            if (time.time() - start_time) > self.transaction_wait_timeout:
                break
            time.sleep(0.1)

        missing_txs_strings = [
            f"{tx.hash} ({tx.model_dump_json()})"
            for tx in transactions
            if tx.hash in tx_hashes
        ]

        pending_tx_responses_string = "\n".join(
            [
                f"{tx_hash}: {tx.model_dump_json()}"
                for tx_hash, tx in pending_responses.items()
            ]
        )
        raise Exception(
            f"Transactions {', '.join(missing_txs_strings)} were not included in a block "
            f"within {self.transaction_wait_timeout} seconds:\n"
            f"{pending_tx_responses_string}"
        )


class PendingTransactionHandler:
    """
    Manages block generation based on the number of pending transactions or a
    block generation interval.

    Attributes:
        block_generation_interval: The number of iterations after which a block
            is generated if no new transactions are added (default: 10).

    """

    chain_builder_eth_rpc: ChainBuilderEthRPC
    block_generation_interval: int
    last_pending_tx_hashes_count: int | None = None
    i: int = 0

    def __init__(
        self,
        chain_builder_eth_rpc: ChainBuilderEthRPC,
        block_generation_interval: int = 10,
    ):
        """Initialize the pending transaction handler."""
        self.chain_builder_eth_rpc = chain_builder_eth_rpc
        self.block_generation_interval = block_generation_interval

    def handle(self) -> None:
        """
        Handle pending transactions and generate blocks if necessary.

        If the number of pending transactions reaches the limit, a block is
        generated.

        If no new transactions have been added to the pending list and the
        block generation interval has been reached, a block is generated to
        avoid potential deadlock.
        """
        with self.chain_builder_eth_rpc.pending_tx_hashes:
            if (
                len(self.chain_builder_eth_rpc.pending_tx_hashes)
                >= self.chain_builder_eth_rpc.transactions_per_block
            ):
                self.chain_builder_eth_rpc.generate_block()
            else:
                if (
                    self.last_pending_tx_hashes_count is not None
                    and len(self.chain_builder_eth_rpc.pending_tx_hashes)
                    == self.last_pending_tx_hashes_count
                    and self.i % self.block_generation_interval == 0
                ):
                    # If no new transactions have been added to the pending
                    # list, generate a block to avoid potential deadlock.
                    self.chain_builder_eth_rpc.generate_block()
            self.last_pending_tx_hashes_count = len(
                self.chain_builder_eth_rpc.pending_tx_hashes
            )
            self.i += 1
