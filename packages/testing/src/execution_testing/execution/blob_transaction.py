"""Test execution format to get blobs from the execution client."""

from hashlib import sha256
from typing import ClassVar, Dict, List

from pytest import FixtureRequest

from execution_testing.base_types import Address, Hash
from execution_testing.base_types.base_types import Bytes
from execution_testing.forks import Fork
from execution_testing.logging import (
    get_logger,
)
from execution_testing.rpc import (
    BlobAndProofV1,
    BlobAndProofV2,
    BlobCellsAndProofsV1,
    EngineRPC,
    EthRPC,
)
from execution_testing.rpc.rpc_types import (
    ForkchoiceState,
    GetBlobsResponse,
    GetBlobsV4Response,
    JSONRPCError,
    PayloadStatusEnum,
)
from execution_testing.test_types import (
    Blob,
    Environment,
    NetworkWrappedTransaction,
    Transaction,
)
from execution_testing.test_types.transaction_types import (
    TransactionTestMetadata,
)

from .base import BaseExecute, ExecuteResult

logger = get_logger(__name__)

CUSTODY_COLUMNS_BYTE_LENGTH = 16
"""Byte length of a well-formed `custodyColumns` bitmap (EIP-8070)."""


def _interleave_hashes(a: List[Hash], b: List[Hash]) -> List[Hash]:
    """Interleave two hash lists, starting with `a`, appending leftovers."""
    interleaved: List[Hash] = []
    for x, y in zip(a, b, strict=False):
        interleaved.extend((x, y))
    shorter_length = min(len(a), len(b))
    interleaved.extend(a[shorter_length:])
    interleaved.extend(b[shorter_length:])
    return interleaved


def _validate_blob_and_proof(
    expected_blob: BlobAndProofV1 | BlobAndProofV2 | None,
    received_blob: BlobAndProofV1 | BlobAndProofV2 | None,
    index: int,
) -> None:
    """
    Validate that a received blob and proof match the expected values.

    When expected is None (non-existing blob hash), the received blob must
    also be None. When expected is not None, the received blob must match.
    Raise ValueError with a detailed message on mismatch.
    """
    if expected_blob is None:
        if received_blob is None:
            logger.info(
                f"Blob at index {index} correctly returned null "
                "(non-existing blob hash)"
            )
            return
        raise ValueError(
            f"Blob at index {index} should not exist but "
            f"client returned: {received_blob}"
        )
    if received_blob is None:
        raise ValueError(f"Received blob at index {index} is empty.")
    if isinstance(expected_blob, BlobAndProofV1):
        if not isinstance(received_blob, BlobAndProofV1):
            raise ValueError(
                f"Received blob at index {index} is not a BlobAndProofV1."
            )
        if expected_blob.blob != received_blob.blob:
            raise ValueError(f"Blob mismatch at index {index}.")
        if expected_blob.proof != received_blob.proof:
            raise ValueError(f"Proof mismatch at index {index}.")
    elif isinstance(expected_blob, BlobAndProofV2):
        if not isinstance(received_blob, BlobAndProofV2):
            raise ValueError(
                f"Received blob at index {index} is not a BlobAndProofV2."
            )
        if expected_blob.blob != received_blob.blob:
            raise ValueError(f"Blob mismatch at index {index}.")
        if expected_blob.proofs != received_blob.proofs:
            error_message = f"Proofs mismatch at index {index}."
            expected_len = len(expected_blob.proofs)
            received_len = len(received_blob.proofs)
            error_message += f"len(expected_blob.proofs) = {expected_len}, "
            error_message += f"len(received_blob.proofs) = {received_len}\n"
            if expected_len == received_len:
                for j, (expected_proof, received_proof) in enumerate(
                    zip(
                        expected_blob.proofs,
                        received_blob.proofs,
                        strict=False,
                    )
                ):
                    if len(expected_proof) != len(received_proof):
                        exp_len = len(expected_proof)
                        rcv_len = len(received_proof)
                        error_message += f"Proof length mismatch. index = {j},"
                        error_message += f"expected_proof length = {exp_len}, "
                        error_message += f"received_proof length = {rcv_len}\n"
                        continue
                    if expected_proof != received_proof:
                        exp_hash = sha256(expected_proof).hexdigest()
                        rcv_hash = sha256(received_proof).hexdigest()
                        error_message += f"Proof mismatch. index = {j},"
                        error_message += f"expected_proof hash = {exp_hash}, "
                        error_message += f"received_proof hash = {rcv_hash}\n"
            raise ValueError(error_message)
    else:
        raise ValueError(
            f"Unexpected blob type at index {index}: {type(expected_blob)}"
        )


def _validate_cells_and_proofs(
    expected_blob: Blob | None,
    received: BlobCellsAndProofsV1 | None,
    cell_mask: int,
    index: int,
) -> None:
    """
    Validate a received `engine_getBlobsV4` cell matrix against a local blob.

    The response is a compact matrix: for each existing blob the client
    returns only the cells selected by `cell_mask`, ordered by ascending
    cell index, so `blob_cells[k]` is the k-th requested cell. When
    `expected_blob` is `None` (a non-existing hash), the whole entry must be
    `null`.

    Per execution-apis `engine_getBlobsV4`, `cell_mask` is a little-endian
    16-byte bitmap where bit `i` selects cell `i` (see `EngineRPC.get_blobs`).
    Network-wrapped txs deliver the full blob, so the client holds every
    requested cell; a returned `null` means an unavailable cell and fails.
    """
    if expected_blob is None:
        if received is None:
            logger.info(
                f"Blob at index {index} correctly returned null "
                "(non-existing blob hash)"
            )
            return
        raise ValueError(
            f"Blob at index {index} should be null (non-existing hash), "
            f"but client returned a cell matrix."
        )
    if received is None:
        raise ValueError(f"Received cell matrix at index {index} is empty.")

    assert expected_blob.cells is not None, (
        "Local blob has no cells; getBlobsV4 requires a fork with cell proofs."
    )
    assert isinstance(expected_blob.proof, list), (
        "Local blob proof is not a cell-proof list."
    )
    # Compact matrix: the client returns only the requested cells, in
    # ascending cell-index order (bit `i` of the mask selects cell `i`).
    requested_indices = [
        i for i in range(len(expected_blob.cells)) if (cell_mask >> i) & 1
    ]
    if len(received.blob_cells) != len(requested_indices):
        raise ValueError(
            f"Cell matrix at index {index} has {len(received.blob_cells)} "
            f"cells, expected {len(requested_indices)}."
        )
    if len(received.proofs) != len(requested_indices):
        raise ValueError(
            f"Proof matrix at index {index} has {len(received.proofs)} "
            f"proofs, expected {len(requested_indices)}."
        )

    for pos, cell_index in enumerate(requested_indices):
        recv_cell = received.blob_cells[pos]
        recv_proof = received.proofs[pos]
        if recv_cell is None or recv_proof is None:
            raise ValueError(
                f"Requested cell {cell_index} at blob index {index} was "
                "returned as null."
            )
        if recv_cell != expected_blob.cells[cell_index]:
            raise ValueError(
                f"Cell mismatch at blob index {index}, cell {cell_index}."
            )
        if recv_proof != expected_blob.proof[cell_index]:
            raise ValueError(
                f"Cell proof mismatch at blob index {index}, "
                f"cell {cell_index}."
            )


def versioned_hashes_with_blobs_and_proofs(
    tx: NetworkWrappedTransaction,
) -> Dict[Hash, BlobAndProofV1 | BlobAndProofV2]:
    """
    Return a dictionary of versioned hashes with their corresponding blobs and
    proofs.
    """
    versioned_hashes: Dict[Hash, BlobAndProofV1 | BlobAndProofV2] = {}
    for blob in tx.blob_objects:
        if isinstance(blob.proof, Bytes):
            versioned_hashes[blob.versioned_hash] = BlobAndProofV1(
                blob=blob.data, proof=blob.proof
            )
        elif isinstance(blob.proof, list):
            versioned_hashes[blob.versioned_hash] = BlobAndProofV2(
                blob=blob.data, proofs=blob.proof
            )
        else:
            raise ValueError(
                f"Blob with versioned hash {blob.versioned_hash.hex()} "
                "requires a proof that is not None"
            )

    return versioned_hashes


class BlobTransaction(BaseExecute):
    """
    Represents a test execution format to send blob transactions to the client
    and then use `engine_getBlobsV*` end points to validate the proofs
    generated by the execution client.
    """

    format_name: ClassVar[str] = "blob_transaction_test"
    description: ClassVar[str] = (
        "Send blob transactions to the execution client and validate their "
        "availability via `engine_getBlobsV*`"
    )

    txs: List[NetworkWrappedTransaction | Transaction]
    nonexisting_blob_hashes: List[Hash] | None = None
    interleave_nonexisting_blob_hashes: bool = False
    get_blobs_version: int | None = None
    cell_mask: int | None = None
    custody_columns: bytes | None = None

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
        txs: List[Transaction] = []
        for tx in self.txs:
            if isinstance(tx, NetworkWrappedTransaction):
                txs.append(tx.tx)
            else:
                txs.append(tx)
        max_tx_gas_limit = Transaction.calculate_max_gas_limit(
            txs=txs,
            env_gas_limit=int(env.gas_limit),
            transaction_gas_limit_cap=fork.transaction_gas_limit_cap(),
            state_gas_reservoir_enabled=fork.state_gas_reservoir_enabled(),
        )
        for tx in txs:
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
        for tx in self.txs:
            sender = tx.sender
            assert sender is not None, "Sender is None"
            if sender not in balances:
                balances[sender] = 0
            balances[sender] += tx.signer_minimum_balance(fork=fork)
        return balances

    def _update_custody_columns(
        self,
        fork: Fork,
        eth_rpc: EthRPC,
        engine_rpc: EngineRPC,
    ) -> None:
        """
        Send a forkchoice update carrying the `custodyColumns` bitmap.

        A 16-byte bitmap must be accepted with a VALID payload status
        (custody set update errors must not affect the forkchoice flow,
        per `engine_forkchoiceUpdatedV4`); any other length must be
        rejected with `-32602: Invalid params`.
        """
        assert self.custody_columns is not None
        fcu_version = fork.engine_forkchoice_updated_version()
        assert fcu_version is not None and fcu_version >= 4, (
            "custodyColumns requires engine_forkchoiceUpdatedV4."
        )
        latest_block = eth_rpc.get_block_by_number("latest")
        assert latest_block is not None, "Failed to fetch the latest block."
        forkchoice_state = ForkchoiceState(
            head_block_hash=latest_block.hash,
        )
        valid_length = len(self.custody_columns) == CUSTODY_COLUMNS_BYTE_LENGTH
        try:
            response = engine_rpc.forkchoice_updated(
                forkchoice_state,
                None,
                version=fcu_version,
                custody_columns=self.custody_columns,
            )
        except JSONRPCError as e:
            if valid_length:
                raise
            if e.code != -32602:
                raise ValueError(
                    f"Expected error -32602 (Invalid params) for a "
                    f"{len(self.custody_columns)}-byte custodyColumns, "
                    f"got {e.code}: {e.message}"
                ) from e
            logger.info(
                f"Client correctly rejected a "
                f"{len(self.custody_columns)}-byte custodyColumns bitmap."
            )
            return
        if not valid_length:
            raise ValueError(
                f"Client accepted a {len(self.custody_columns)}-byte "
                "custodyColumns bitmap; expected -32602 (Invalid params)."
            )
        status = response.payload_status.status
        if status != PayloadStatusEnum.VALID:
            raise ValueError(
                f"forkchoiceUpdatedV{fcu_version} with custodyColumns "
                f"returned payload status {status}, expected VALID."
            )

    def execute(
        self,
        fork: Fork,
        eth_rpc: EthRPC,
        engine_rpc: EngineRPC | None,
        request: FixtureRequest,
    ) -> ExecuteResult:
        """Execute the format."""
        versioned_hashes: Dict[Hash, BlobAndProofV1 | BlobAndProofV2] = {}
        blobs_by_hash: Dict[Hash, Blob] = {}
        sent_txs: List[Transaction] = []
        for tx_index, tx in enumerate(self.txs):
            tx = tx.with_signature_and_sender()
            expected_hash = tx.hash
            to_address = tx.to
            if isinstance(tx, NetworkWrappedTransaction):
                sent_txs.append(tx.tx)
                versioned_hashes.update(
                    versioned_hashes_with_blobs_and_proofs(tx)
                )
                for blob in tx.blob_objects:
                    blobs_by_hash[blob.versioned_hash] = blob
            else:
                sent_txs.append(tx)
            label = (
                to_address.label if isinstance(to_address, Address) else None
            )
            metadata = TransactionTestMetadata(
                test_id=request.node.nodeid,
                phase="testing",
                target=label,
                tx_index=tx_index,
            )
            received_hash = eth_rpc.send_raw_transaction(
                tx.rlp(), request_id=metadata.to_json()
            )
            assert expected_hash == received_hash, (
                f"Expected hash {expected_hash} does not match "
                f"received hash {received_hash}."
            )

        if engine_rpc is None:
            logger.info(
                "Engine RPC is not available, skipping getBlobsV* validation."
            )
            return ExecuteResult(
                benchmark_gas_used=None,
            )

        # Use explicit version if provided, otherwise derive from fork
        if self.get_blobs_version is not None:
            version = self.get_blobs_version
        else:
            fork_version = fork.engine_get_blobs_version()
            assert fork_version is not None, (
                "Engine get blobs version is not supported by the fork."
            )
            version = fork_version

        list_versioned_hashes = list(versioned_hashes.keys())
        if self.nonexisting_blob_hashes is not None:
            if self.interleave_nonexisting_blob_hashes:
                assert version >= 4, (
                    "interleave_nonexisting_blob_hashes is only supported "
                    "with getBlobsV4."
                )
                list_versioned_hashes = _interleave_hashes(
                    self.nonexisting_blob_hashes, list_versioned_hashes
                )
            else:
                list_versioned_hashes.extend(self.nonexisting_blob_hashes)

        if self.custody_columns is not None:
            self._update_custody_columns(fork, eth_rpc, engine_rpc)

        indices_bitarray = self.cell_mask if version >= 4 else None
        blob_response: GetBlobsResponse | GetBlobsV4Response | None = (
            engine_rpc.get_blobs(
                list_versioned_hashes,
                version=version,
                indices_bitarray=indices_bitarray,
            )
        )

        if version <= 2:
            # V1/V2: all-or-nothing behavior
            if self.nonexisting_blob_hashes is not None:
                # Any missing blob must cause the entire response to be null
                if blob_response is not None:
                    raise ValueError(
                        "Non-existing blob hashes were requested and the "
                        f"client (using getBlobsV{version}) was expected "
                        "to respond with 'null', but instead it replied: "
                        f"{blob_response.root}"
                    )
                logger.info(
                    f"Test passed: getBlobsV{version} correctly returned "
                    "'null' (partial responses not allowed in V1/V2)"
                )
            else:
                # All blobs should be present and valid
                assert blob_response is not None, (
                    f"getBlobsV{version} returned 'null' but all "
                    "requested blobs should exist."
                )
                assert isinstance(blob_response, GetBlobsResponse)
                local_blobs_and_proofs = list(versioned_hashes.values())
                assert len(blob_response) == len(local_blobs_and_proofs), (
                    f"Expected {len(local_blobs_and_proofs)} blobs and "
                    f"proofs, got {len(blob_response)}."
                )
                for i, (expected_blob, received_blob) in enumerate(
                    zip(
                        local_blobs_and_proofs,
                        blob_response.root,
                        strict=True,
                    )
                ):
                    _validate_blob_and_proof(expected_blob, received_blob, i)
        elif version == 3:
            # V3: partial responses (null only for missing blobs)
            if blob_response is None:
                raise ValueError(
                    f"getBlobsV{version} returned 'null' for the entire "
                    "response, but V3 should always return an array "
                    "(with null entries for missing blobs)."
                )
            assert isinstance(blob_response, GetBlobsResponse)
            expected_blobs_and_proofs: List[
                BlobAndProofV1 | BlobAndProofV2 | None
            ] = list(versioned_hashes.values())
            if self.nonexisting_blob_hashes is not None:
                expected_blobs_and_proofs += [None] * len(
                    self.nonexisting_blob_hashes
                )
            if len(blob_response) != len(expected_blobs_and_proofs):
                raise ValueError(
                    f"Expected {len(expected_blobs_and_proofs)} blob "
                    f"responses, got {len(blob_response)}."
                )
            for i, (expected, received) in enumerate(
                zip(
                    expected_blobs_and_proofs,
                    blob_response.root,
                    strict=True,
                )
            ):
                _validate_blob_and_proof(expected, received, i)
            if self.nonexisting_blob_hashes is not None:
                existing_count = len(versioned_hashes)
                nonexisting_count = len(self.nonexisting_blob_hashes)
                logger.info(
                    f"Test passed: getBlobsV{version} correctly returned "
                    f"partial response with {existing_count} existing "
                    f"blobs and {nonexisting_count} null entries for "
                    "missing blobs"
                )
        elif version == 4:
            # V4 (EIP-8070): partial cell matrix, selected by cell_mask
            assert self.cell_mask is not None, (
                f"getBlobsV{version} requires a cell_mask."
            )
            if blob_response is None:
                raise ValueError(
                    f"getBlobsV{version} returned 'null' for the entire "
                    "response, but V4 should always return an array "
                    "(with null entries for missing blobs)."
                )
            assert isinstance(blob_response, GetBlobsV4Response)
            # `blobs_by_hash` only holds existing blobs, so non-existing
            # hashes map to `None` at their exact request positions.
            expected_blobs: List[Blob | None] = [
                blobs_by_hash.get(vh) for vh in list_versioned_hashes
            ]
            if len(blob_response) != len(expected_blobs):
                raise ValueError(
                    f"Expected {len(expected_blobs)} blob responses, "
                    f"got {len(blob_response)}."
                )
            for i, (expected_cells, received_cells) in enumerate(
                zip(expected_blobs, blob_response.root, strict=True)
            ):
                _validate_cells_and_proofs(
                    expected_cells, received_cells, self.cell_mask, i
                )
        else:
            raise NotImplementedError(
                f"getBlobsV{version} is not supported. "
                "Supported versions: V1, V2, V3, V4."
            )

        eth_rpc.wait_for_transactions(sent_txs)
        return ExecuteResult(
            benchmark_gas_used=None,
        )
