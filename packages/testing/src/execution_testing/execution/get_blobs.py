"""Mempool check reading the sent blobs back from the execution client."""

from hashlib import sha256
from typing import Dict, List, Sequence

from pydantic import model_validator
from typing_extensions import Self

from execution_testing.base_types import Hash
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
    MempoolTransaction,
    NetworkWrappedTransaction,
)

from .mempool import MempoolCheck

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


class GetBlobs(MempoolCheck):
    """
    Validate the blobs and proofs of the sent blob transactions via
    `engine_getBlobsV*`, while the blob pool still holds them.
    """

    version: int | None = None
    """The `engine_getBlobsV*` version, the fork's when unset."""
    nonexisting_blob_hashes: List[Hash] | None = None
    interleave_nonexisting_blob_hashes: bool = False
    cell_mask: int | None = None
    custody_columns_updates: List[bytes | None] | None = None
    """
    `custodyColumns` values to send in order, one
    `engine_forkchoiceUpdatedV4` each, before `engine_getBlobsV*`: a bitmap
    sends that value and `None` sends an explicit `null`. Leave unset to
    send no update.
    """

    @model_validator(mode="after")
    def _check_custody_columns_updates(self) -> Self:
        """Reject an empty update list, which would send nothing."""
        if self.custody_columns_updates is not None and not (
            self.custody_columns_updates
        ):
            raise ValueError(
                "custody_columns_updates must hold at least one update; "
                "leave it unset to send no custodyColumns update."
            )
        return self

    def _send_custody_columns_updates(
        self,
        fork: Fork,
        eth_rpc: EthRPC,
        engine_rpc: EngineRPC,
    ) -> None:
        """
        Send one forkchoice update per entry of `custody_columns_updates`.

        A 16-byte bitmap or an explicit `null` must be accepted with a
        VALID payload status (`null` and a bitmap identical to the current
        set are blobpool no-ops, and custody set update errors must not
        affect the forkchoice flow, per `engine_forkchoiceUpdatedV4`); any
        other length must be rejected with `-32602: Invalid params`.
        """
        assert self.custody_columns_updates, (
            "custody_columns_updates must hold at least one update."
        )
        fcu_version = fork.engine_forkchoice_updated_version()
        assert fcu_version is not None and fcu_version >= 4, (
            "custodyColumns requires engine_forkchoiceUpdatedV4."
        )
        latest_block = eth_rpc.get_block_by_number("latest")
        assert latest_block is not None, "Failed to fetch the latest block."
        forkchoice_state = ForkchoiceState(
            head_block_hash=Hash(latest_block["hash"]),
        )
        for custody_columns in self.custody_columns_updates:
            if custody_columns is None:
                response = engine_rpc.forkchoice_updated(
                    forkchoice_state,
                    None,
                    version=fcu_version,
                    custody_columns_null=True,
                )
                status = response.payload_status.status
                if status != PayloadStatusEnum.VALID:
                    raise ValueError(
                        f"forkchoiceUpdatedV{fcu_version} with a null "
                        f"custodyColumns returned payload status {status}, "
                        "expected VALID."
                    )
                continue
            valid_length = len(custody_columns) == CUSTODY_COLUMNS_BYTE_LENGTH
            try:
                response = engine_rpc.forkchoice_updated(
                    forkchoice_state,
                    None,
                    version=fcu_version,
                    custody_columns=custody_columns,
                )
            except JSONRPCError as e:
                if valid_length:
                    raise
                if e.code != -32602:
                    raise ValueError(
                        f"Expected error -32602 (Invalid params) for a "
                        f"{len(custody_columns)}-byte custodyColumns, "
                        f"got {e.code}: {e.message}"
                    ) from e
                logger.info(
                    f"Client correctly rejected a "
                    f"{len(custody_columns)}-byte custodyColumns bitmap."
                )
                continue
            if not valid_length:
                raise ValueError(
                    f"Client accepted a {len(custody_columns)}-byte "
                    "custodyColumns bitmap; expected -32602 (Invalid params)."
                )
            status = response.payload_status.status
            if status != PayloadStatusEnum.VALID:
                raise ValueError(
                    f"forkchoiceUpdatedV{fcu_version} with custodyColumns "
                    f"returned payload status {status}, expected VALID."
                )

    def check(
        self,
        *,
        fork: Fork,
        eth_rpc: EthRPC,
        engine_rpc: EngineRPC | None,
        txs: Sequence[MempoolTransaction],
    ) -> None:
        """
        Validate the sent blobs via `engine_getBlobsV*`.

        Runs before any block includes the transactions, so the blob pool
        still holds every blob they carry.
        """
        versioned_hashes: Dict[Hash, BlobAndProofV1 | BlobAndProofV2] = {}
        blobs_by_hash: Dict[Hash, Blob] = {}
        for entry in txs:
            if isinstance(entry.tx, NetworkWrappedTransaction):
                versioned_hashes.update(
                    versioned_hashes_with_blobs_and_proofs(entry.tx)
                )
                for blob in entry.tx.blob_objects:
                    blobs_by_hash[blob.versioned_hash] = blob

        if engine_rpc is None:
            logger.info(
                "Engine RPC is not available, skipping getBlobsV* validation."
            )
            return

        # Use explicit version if provided, otherwise derive from fork
        if self.version is not None:
            version = self.version
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

        if self.custody_columns_updates is not None:
            self._send_custody_columns_updates(fork, eth_rpc, engine_rpc)

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
