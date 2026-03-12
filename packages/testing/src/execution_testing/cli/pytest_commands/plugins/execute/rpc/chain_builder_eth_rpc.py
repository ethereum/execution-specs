"""
Chain builder Ethereum RPC that can drive the chain when new transactions are
submitted.
"""

import time
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any, List, Sequence
from urllib.parse import urlparse

from filelock import FileLock

from execution_testing.base_types import (
    Address,
    Bytes,
    Hash,
    HexNumber,
)
from execution_testing.forks import Fork, TransitionFork
from execution_testing.rpc import EngineRPC, TestingRPC
from execution_testing.rpc import EthRPC as BaseEthRPC
from execution_testing.rpc.rpc_types import (
    ForkchoiceState,
    GetPayloadResponse,
    PayloadAttributes,
    PayloadStatusEnum,
    TransactionProtocol,
)


class ChainBuilderEthRPC(BaseEthRPC, namespace="eth"):
    """
    Special type of Ethereum RPC client that also has access to the Engine API
    and automatically coordinates block generation based on the number of
    pending transactions or a block generation interval.
    """

    fork: Fork | TransitionFork
    engine_rpc: EngineRPC
    get_payload_wait_time: float
    block_building_lock: FileLock
    testing_rpc: TestingRPC | None

    def __init__(
        self,
        *,
        rpc_endpoint: str,
        fork: Fork | TransitionFork,
        engine_rpc: EngineRPC,
        session_temp_folder: Path,
        get_payload_wait_time: float,
        initial_forkchoice_update_retries: int = 5,
        transaction_wait_timeout: int = 60,
        max_transactions_per_batch: int | None = None,
        testing_rpc: TestingRPC | None = None,
    ):
        """Initialize the Ethereum RPC client for the hive simulator."""
        super().__init__(
            rpc_endpoint,
            transaction_wait_timeout=transaction_wait_timeout,
            max_transactions_per_batch=max_transactions_per_batch,
        )
        self.fork = fork
        self.engine_rpc = engine_rpc
        parsed = urlparse(rpc_endpoint)
        self.block_building_lock = FileLock(
            session_temp_folder / f"chain_builder_fcu_{parsed.hostname}.lock"
        )
        self.get_payload_wait_time = get_payload_wait_time
        self.testing_rpc = testing_rpc

        # Send initial forkchoice updated only if we are the first worker
        base_name = f"eth_rpc_forkchoice_updated_{parsed.hostname}"
        base_file = session_temp_folder / base_name
        base_error_file = session_temp_folder / f"{base_name}.err"

        with self.block_building_lock:
            if base_error_file.exists():
                raise Exception(
                    "Error occurred during initial forkchoice_updated"
                )
            if not base_file.exists():
                base_error_file.touch()  # Assume error
                # Get the head block hash
                head_block = self.get_block_by_number("latest")
                assert head_block is not None
                block_number = HexNumber(head_block["number"])
                timestamp = HexNumber(head_block["timestamp"])
                head_fork = self.fork.fork_at(
                    block_number=block_number, timestamp=timestamp
                )
                # Send initial forkchoice updated
                forkchoice_state = ForkchoiceState(
                    head_block_hash=head_block["hash"],
                )
                forkchoice_version = (
                    head_fork.engine_forkchoice_updated_version()
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

    @property
    def transaction_polling_context(self) -> AbstractContextManager:
        """
        Return the block building lock as context manager so it's acquired
        during transaction polling.

        Reasoning is that the lock gets acquired once while all processes
        wait for transactions, only one of them produces a new block.
        """
        return self.block_building_lock

    def _payload_attributes(
        self, *, next_block_number: int, next_timestamp: int
    ) -> PayloadAttributes:
        """Build payload attributes from the current head block."""
        next_fork = self.fork.fork_at(
            block_number=next_block_number, timestamp=next_timestamp
        )
        parent_beacon_block_root = (
            Hash(0) if next_fork.header_beacon_root_required() else None
        )
        return PayloadAttributes(
            timestamp=next_timestamp,
            prev_randao=Hash(0),
            suggested_fee_recipient=Address(0),
            withdrawals=[]
            if next_fork.header_withdrawals_required()
            else None,
            parent_beacon_block_root=parent_beacon_block_root,
            target_blobs_per_block=(
                next_fork.target_blobs_per_block()
                if next_fork.engine_payload_attribute_target_blobs_per_block()
                else None
            ),
            max_blobs_per_block=(
                next_fork.max_blobs_per_block()
                if next_fork.engine_payload_attribute_max_blobs_per_block()
                else None
            ),
        )

    def _finalize_payload(
        self,
        payload: GetPayloadResponse,
        parent_beacon_block_root: Hash | None,
    ) -> None:
        """
        Execute *payload* via ``engine_newPayload`` and set it as
        the canonical head via ``engine_forkchoiceUpdated``.
        """
        new_payload_args: List[Any] = [
            payload.execution_payload,
        ]
        if payload.blobs_bundle is not None:
            new_payload_args.append(
                payload.blobs_bundle.blob_versioned_hashes()
            )
        if parent_beacon_block_root is not None:
            new_payload_args.append(parent_beacon_block_root)
        if payload.execution_requests is not None:
            new_payload_args.append(payload.execution_requests)
        payload_fork = self.fork.fork_at(
            block_number=payload.execution_payload.number,
            timestamp=payload.execution_payload.timestamp,
        )
        new_payload_version = payload_fork.engine_new_payload_version()
        assert new_payload_version is not None, (
            "Fork does not support engine new_payload"
        )
        new_payload_response = self.engine_rpc.new_payload(
            *new_payload_args, version=new_payload_version
        )
        assert new_payload_response.status == PayloadStatusEnum.VALID, (
            "Payload was invalid"
        )

        fcu_version = payload_fork.engine_forkchoice_updated_version()
        assert fcu_version is not None, (
            "Fork does not support engine forkchoice_updated"
        )
        new_forkchoice_state = ForkchoiceState(
            head_block_hash=(payload.execution_payload.block_hash),
        )
        response = self.engine_rpc.forkchoice_updated(
            new_forkchoice_state,
            None,
            version=fcu_version,
        )
        assert response.payload_status.status == PayloadStatusEnum.VALID, (
            "Payload was invalid"
        )

    def generate_block(self: "ChainBuilderEthRPC") -> None:
        """Generate a block using the Engine API."""
        head_block = self.get_block_by_number("latest")
        assert head_block is not None

        forkchoice_state = ForkchoiceState(
            head_block_hash=head_block["hash"],
        )
        next_block_number = int(HexNumber(head_block["number"]) + 1)
        next_timestamp = int(HexNumber(head_block["timestamp"]) + 1)
        next_fork = self.fork.fork_at(
            block_number=next_block_number, timestamp=next_timestamp
        )
        payload_attributes = self._payload_attributes(
            next_block_number=next_block_number, next_timestamp=next_timestamp
        )
        forkchoice_updated_version = (
            next_fork.engine_forkchoice_updated_version()
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
        get_payload_version = next_fork.engine_get_payload_version()
        assert get_payload_version is not None, (
            "Fork does not support engine get_payload"
        )
        new_payload = self.engine_rpc.get_payload(
            response.payload_id,
            version=get_payload_version,
        )
        self._finalize_payload(
            new_payload,
            payload_attributes.parent_beacon_block_root,
        )

    def pending_transactions_handler(self) -> None:
        """
        Called inside the transaction inclusion wait-loop.

        This class triggers the block building process if it's still
        waiting for transactions to be included.
        """
        self.generate_block()

    def send_transactions(
        self,
        transactions: Sequence[TransactionProtocol],
    ) -> List[Hash]:
        """
        Send transactions to the execution client.

        When ``testing_rpc`` is configured, build and finalize a
        block containing *transactions* via
        ``testing_buildBlockV1`` instead of sending them to the
        mempool with ``eth_sendRawTransaction``.
        """
        if self.testing_rpc is None:
            return super().send_transactions(transactions)
        if not transactions:
            return []

        with self.block_building_lock:
            head_block = self.get_block_by_number("latest")
            assert head_block is not None
            next_block_number = int(HexNumber(head_block["number"]) + 1)
            next_timestamp = int(HexNumber(head_block["timestamp"]) + 1)
            payload_attributes = self._payload_attributes(
                next_block_number=next_block_number,
                next_timestamp=next_timestamp,
            )
            new_payload = self.testing_rpc.build_block(
                parent_block_hash=Hash(head_block["hash"]),
                payload_attributes=payload_attributes,
                transactions=transactions,
                extra_data=Bytes(b""),  # TODO: This is marked as optional
            )
            self._finalize_payload(
                new_payload,
                payload_attributes.parent_beacon_block_root,
            )

        return [tx.hash for tx in transactions]
