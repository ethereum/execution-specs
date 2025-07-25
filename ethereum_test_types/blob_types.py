"""Blob-related types for Ethereum tests."""

import random
from enum import Enum
from hashlib import sha256
from os.path import realpath
from pathlib import Path
from typing import Any, ClassVar, List, Literal, cast

import ckzg  # type: ignore
import platformdirs
from filelock import FileLock

from ethereum_test_base_types.base_types import Bytes, Hash
from ethereum_test_base_types.pydantic import CamelModel
from ethereum_test_forks import Fork
from pytest_plugins.logging import get_logger

CACHED_BLOBS_DIRECTORY: Path = (
    Path(platformdirs.user_cache_dir("ethereum-execution-spec-tests")) / "cached_blobs"
)
logger = get_logger(__name__)


def clear_blob_cache(cached_blobs_folder_path: Path):
    """Delete all cached blobs."""
    if not cached_blobs_folder_path.is_dir():
        return

    json_files = list(cached_blobs_folder_path.glob("*.json"))

    for f in json_files:
        lock_file_path = f.with_suffix(".lock")

        try:
            # get file lock for what you want to delete
            with FileLock(lock_file_path):
                f.unlink()
        except Exception as e:
            print(
                f"Error while trying to delete file {f}:{e}. "
                "Aborting clearing of blob cache folder."
            )
            return


class Blob(CamelModel):
    """Class representing a full blob."""

    data: Bytes
    commitment: Bytes
    proof: List[Bytes] | Bytes  # Bytes < Osaka, List[Bytes] >= Osaka
    cells: List[Bytes] | None  # None (in json: null) < Osaka, List[Bytes] >= Osaka

    versioned_hash: Hash
    name: str
    fork: Fork
    seed: int
    timestamp: int  # fork transitions require timestamp >= 15000 to occur

    _trusted_setup: ClassVar[Any | None] = None

    @classmethod
    def trusted_setup(cls):
        """Set trusted setup if it is not already set."""
        if cls._trusted_setup is None:
            trusted_setup_path = Path(realpath(__file__)).parent / "kzg_trusted_setup.txt"
            trusted_setup = ckzg.load_trusted_setup(str(trusted_setup_path), 0)
            cls._trusted_setup = trusted_setup

        return cls._trusted_setup

    @staticmethod
    def get_filename(fork: Fork, seed: int) -> str:
        """Return filename this blob would have as string (with .json extension)."""
        amount_cell_proofs: int = cast(int, fork.get_blob_constant("AMOUNT_CELL_PROOFS"))
        return "blob_" + str(seed) + "_cell_proofs_" + str(amount_cell_proofs) + ".json"

    @staticmethod
    def get_filepath(fork: Fork, seed: int):
        """Return the Path to the blob that would be created with these parameters."""
        # determine amount of cell proofs for this fork (0 or 128)
        would_be_filename: str = Blob.get_filename(fork, seed)

        # return path to blob
        return CACHED_BLOBS_DIRECTORY / would_be_filename

    @staticmethod
    def from_fork(fork: Fork, seed: int = 0, timestamp: int = 0) -> "Blob":
        """Construct Blob instances. Fork logic is encapsulated within nested functions."""

        def generate_blob_data(rng_seed: int = 0) -> Bytes:
            """Calculate blob data deterministically via provided seed."""
            # create local (independent) RNG object seeded with rng_seed
            rng = random.Random(rng_seed)

            # generate blob
            ints: list[int] = [
                rng.randrange(cast(int, fork.get_blob_constant("BLS_MODULUS")))
                for _ in range(cast(int, fork.get_blob_constant("FIELD_ELEMENTS_PER_BLOB")))
            ]

            encoded: list[bytes] = [
                i.to_bytes(
                    cast(int, fork.get_blob_constant("BYTES_PER_FIELD_ELEMENT")),
                    cast(Literal["big"], fork.get_blob_constant("KZG_ENDIANNESS")),
                )
                for i in ints
            ]
            blob: bytes = b"".join(encoded)  # without 0x

            return Bytes(blob)

        def get_versioned_hash(commitment: Bytes, version: int = 1) -> Hash:
            """Calculate versioned hash for a given blob."""
            return Hash(bytes([version]) + sha256(commitment).digest()[1:])

        def get_commitment(data: Bytes) -> Bytes:
            """
            Take a blob and returns a cryptographic commitment to it.

            Note: Each cell holds the exact same copy of this commitment.
            """
            # sanity check
            field_elements: int = cast(int, fork.get_blob_constant("FIELD_ELEMENTS_PER_BLOB"))
            bytes_per_field: int = cast(int, fork.get_blob_constant("BYTES_PER_FIELD_ELEMENT"))
            assert len(data) == field_elements * bytes_per_field, (
                f"Expected blob of length "
                f"{field_elements * bytes_per_field} but got blob of length {len(data)}"
            )

            # calculate commitment
            commitment = ckzg.blob_to_kzg_commitment(data, Blob.trusted_setup())
            assert len(commitment) == fork.get_blob_constant("BYTES_PER_COMMITMENT"), (
                f"Expected {fork.get_blob_constant('BYTES_PER_COMMITMENT')} "
                f"resulting commitments but got {len(commitment)} commitments"
            )

            return commitment

        def get_proof(fork: Fork, data: Bytes) -> List[Bytes] | Bytes:
            # determine whether this fork is <osaka or >= osaka by looking at amount of cell_proofs
            amount_cell_proofs = fork.get_blob_constant("AMOUNT_CELL_PROOFS")

            # cancun, prague
            if amount_cell_proofs == 0:
                z = 2  # 2 is one of many possible valid field elements z (https://github.com/ethereum/consensus-specs/blob/ad884507f7a1d5962cd3dfb5f7b3e41aab728c55/tests/core/pyspec/eth2spec/test/utils/kzg_tests.py#L58-L66)
                z_valid_size: bytes = z.to_bytes(
                    cast(int, fork.get_blob_constant("BYTES_PER_FIELD_ELEMENT")), byteorder="big"
                )
                proof, _ = ckzg.compute_kzg_proof(data, z_valid_size, Blob.trusted_setup())
                return proof

            # >=osaka
            if amount_cell_proofs == 128:
                _, proofs = ckzg.compute_cells_and_kzg_proofs(
                    data, Blob.trusted_setup()
                )  # returns List[byte] of length 128
                return proofs

            raise AssertionError(
                f"get_proof() has not been implemented yet for fork: {fork.name()}."
                f"Got amount of cell proofs {amount_cell_proofs} but expected 128."
            )

        def get_cells(fork: Fork, data: Bytes) -> List[Bytes] | None:
            # determine whether this fork is <osaka or >= osaka by looking at amount of cell_proofs
            amount_cell_proofs = fork.get_blob_constant("AMOUNT_CELL_PROOFS")

            # cancun, prague
            if amount_cell_proofs == 0:
                return None

            # >=osaka
            if amount_cell_proofs == 128:
                cells, _ = ckzg.compute_cells_and_kzg_proofs(
                    data, Blob.trusted_setup()
                )  # returns List[byte] of length 128
                return cells  # List[bytes]

            raise AssertionError(
                f"get_cells() has not been implemented yet for fork: {fork.name()}. Got amount of "
                f"cell proofs {amount_cell_proofs} but expected 128."
            )

        # first, create cached blobs dir if necessary
        if not CACHED_BLOBS_DIRECTORY.exists():
            CACHED_BLOBS_DIRECTORY.mkdir(
                parents=True, exist_ok=True
            )  # create all necessary dirs on the way

        # handle transition forks
        # (blob related constants are needed and only available for normal forks)
        fork = fork.fork_at(timestamp=timestamp)

        # if this blob already exists then load from file. use lock
        blob_location: Path = Blob.get_filepath(fork, seed)

        # use lock to avoid race conditions
        lock_file_path = blob_location.with_suffix(".lock")
        with FileLock(lock_file_path):
            if blob_location.exists():
                logger.debug(f"Blob exists already, reading it from file {blob_location}")
                return Blob.from_file(Blob.get_filename(fork, seed))

        assert fork.supports_blobs(), f"Provided fork {fork.name()} does not support blobs!"

        # get data for blob parameters
        data: Bytes = generate_blob_data(seed)
        commitment: Bytes = get_commitment(data)
        proof: List[Bytes] | Bytes = get_proof(fork, data)
        cells: List[Bytes] | None = get_cells(fork, data)
        versioned_hash: Hash = get_versioned_hash(commitment)
        name: str = Blob.get_filename(fork, seed)

        blob = Blob(
            data=data,
            commitment=commitment,
            proof=proof,
            cells=cells,
            versioned_hash=versioned_hash,
            name=name,
            fork=fork,
            seed=seed,
            timestamp=timestamp,
        )
        # for most effective caching temporarily persist every blob that is created in cache
        blob.write_to_file()

        return blob

    @staticmethod
    def from_file(file_name: str) -> "Blob":
        """
        Read a .json file and reconstruct object it represents.

        You can load a blob only via its filename (with or without .json extension).
        """
        # ensure filename was passed
        assert file_name.startswith("blob_"), (
            f"You provided an invalid blob filename. Expected it to start with 'blob_' "
            f"but got: {file_name}"
        )

        if ".json" not in file_name:
            file_name = file_name + ".json"

        # determine path where this blob would be stored if it existed
        blob_file_location = CACHED_BLOBS_DIRECTORY / file_name

        # check whether blob exists
        assert blob_file_location.exists(), (
            f"Tried to load blob from file but {blob_file_location} does not exist"
        )

        # read blob from file
        with open(blob_file_location, "r", encoding="utf-8") as f:
            json_str: str = f.read()

        # reconstruct and return blob object
        return Blob.model_validate_json(json_str)

    def write_to_file(self):
        """Take a blob object, serialize it and write it to disk as json."""
        json_str = self.model_dump_json()
        output_location = Blob.get_filepath(self.fork, self.seed)

        # use lock to avoid race conditions
        lock_file_path = output_location.with_suffix(".lock")
        with FileLock(lock_file_path):
            # warn if existing static_blob gets overwritten
            if output_location.exists():
                logger.debug(f"Blob {output_location} already exists. It will be overwritten.")

            with open(output_location, "w", encoding="utf-8") as f:  # overwrite existing
                f.write(json_str)

    def verify_cell_kzg_proof_batch(self, cell_indices: list) -> bool:
        """Check whether all cell proofs are valid and returns True only if that is the case."""
        amount_cell_proofs: int = cast(int, self.fork.get_blob_constant("AMOUNT_CELL_PROOFS"))

        assert amount_cell_proofs > 0, (
            f"verify_cell_kzg_proof_batch() is not available for your fork: {self.fork.name()}."
        )

        assert self.cells is not None, "self.cells is None, critical error."

        assert len(cell_indices) == len(self.cells), (
            f"Cell Indices list (detected length {len(cell_indices)}) and Cell list "
            f"(detected length {len(self.cells)}) should have same length."
        )

        # each cell refers to the same commitment
        commitments: list[bytes] = [self.commitment] * len(cell_indices)

        is_valid = ckzg.verify_cell_kzg_proof_batch(
            commitments, cell_indices, self.cells, self.proof, Blob.trusted_setup()
        )

        return is_valid

    def delete_cells_then_recover_them(self, deletion_indices: list[int]):
        """
        Simulate the cell recovery process in user-specified scenario.

        Note: Requirement for successful reconstruction is having at least N of the 2N cells.

        Theoretical Usage: You pass a cell list with to 128 elements to this function
        along with a list of deletion indices. These cells will be deleted and then
        the ckzg recovery mechanism is used to repair the missing cells.
        If no assertion is triggered the reconstruction was successful.
        """
        amount_cell_proofs: int = cast(int, self.fork.get_blob_constant("AMOUNT_CELL_PROOFS"))

        assert amount_cell_proofs > 0, (
            f"delete_cells_then_recover_them() is not available for fork: {self.fork.name()}"
        )

        assert self.cells is not None, "self.cells is None, critical problem."

        assert isinstance(self.proof, list), (
            "This function only works when self.proof is a list, but it seems to be "
            " of type bytes (not a list)"
        )

        assert len(self.cells) == 128, (
            f"You are supposed to pass a full cell list with 128 elements to this function, "
            f"but got list of length {len(self.cells)}"
        )

        assert len(deletion_indices) < 129, (
            f"You can't delete more than every cell (max len of deletion indices list is 128), "
            f"but you passed a deletion indices list of length {len(deletion_indices)}"
        )
        for i in deletion_indices:
            assert 0 <= i <= 127, f"Expected integers in range [0, 127], but got: {i}"

        # delete cells
        all_cell_indices: list[int] = list(range(128))
        remaining_indices: list[int] = [i for i in all_cell_indices if i not in deletion_indices]
        remaining_cells = [c for i, c in enumerate(self.cells) if i not in deletion_indices]

        recovered_cells, recovered_proofs = ckzg.recover_cells_and_kzg_proofs(
            remaining_indices, remaining_cells, Blob.trusted_setup()
        )  # on success returns two lists of len 128

        # determine success/failure
        assert len(recovered_cells) == len(self.cells), (
            f"Failed to recover cell list. Original cell list had length {len(self.cells)} but "
            f"recovered cell list has length {len(recovered_cells)}"
        )
        assert len(recovered_proofs) == len(self.proof), (
            f"Failed to recover proofs list. Original proofs list had length {len(self.proof)} "
            f"but recovered proofs list has length {len(recovered_proofs)}"
        )

        for i in range(len(recovered_cells)):
            assert self.cells[i] == recovered_cells[i], (
                f"Failed to correctly restore missing cells. At index {i} original cell was "
                f"0x{self.cells[i].hex()} but reconstructed cell does not match: "
                f"0x{recovered_cells[i].hex()}"
            )
            assert self.proof[i] == recovered_proofs[i], (
                f"Failed to correctly restore missing proofs. At index {i} original proof was "
                f"0x{self.proof[i].hex()} but reconstructed proof does not match: "
                f"0x{recovered_proofs[i].hex()}"
            )

    class ProofCorruptionMode(Enum):
        """
        Define what the proof corruption modes do.

        For Osaka and later each Bytes object in the list is manipulated this way.
        """

        CORRUPT_FIRST_BYTE = 1  # corrupts a single byte (index 0)
        CORRUPT_LAST_BYTE = 2  # corrupts a single byte (last valid index)
        CORRUPT_TO_ALL_ZEROES = 3  # sets all proof bytes to 0
        CORRUPT_ALL_BYTES = 4  # corrupts all bytes

    def corrupt_proof(self, mode: ProofCorruptionMode):
        """Corrupt the proof field, supports different corruption modes."""

        def corrupt_byte(b: bytes) -> Bytes:
            """Bit-flip all bits of provided byte using XOR to guarantee change."""
            if len(b) != 1:
                raise ValueError("Input must be a single byte")
            return Bytes(bytes([b[0] ^ 0xFF]))

        # >=osaka
        amount_cell_proofs: int = cast(int, self.fork.get_blob_constant("AMOUNT_CELL_PROOFS"))
        if amount_cell_proofs > 0:
            assert isinstance(self.proof, list), "proof was expected to be a list but it isn't"

            if mode == self.ProofCorruptionMode.CORRUPT_FIRST_BYTE:
                for i in range(len(self.proof)):
                    b: Bytes = self.proof[i]
                    corrupted: Bytes = Bytes(corrupt_byte(b[:1]) + b[1:])
                    self.proof[i] = corrupted
            elif mode == self.ProofCorruptionMode.CORRUPT_LAST_BYTE:
                for i in range(len(self.proof)):
                    b = self.proof[i]
                    corrupted = Bytes(b[:-1] + corrupt_byte(b[-1:]))
                    self.proof[i] = corrupted
            elif mode == self.ProofCorruptionMode.CORRUPT_TO_ALL_ZEROES:
                for i in range(len(self.proof)):
                    self.proof[i] = Bytes(bytes(len(self.proof[i])))
            elif mode == self.ProofCorruptionMode.CORRUPT_ALL_BYTES:
                for i in range(len(self.proof)):
                    b = self.proof[i]
                    corrupted_bytes = Bytes(b"".join(corrupt_byte(bytes([byte])) for byte in b))
                    self.proof[i] = corrupted_bytes
            return

        # pre-osaka (cancun and prague)
        assert amount_cell_proofs == 0, (
            f"You need to adjust corrupt_proof to handle fork {self.fork.name()}"
        )
        assert isinstance(self.proof, Bytes), "proof was expected to be Bytes but it isn't"

        if mode == self.ProofCorruptionMode.CORRUPT_FIRST_BYTE:
            self.proof = Bytes(corrupt_byte(self.proof[:1]) + self.proof[1:])
        elif mode == self.ProofCorruptionMode.CORRUPT_LAST_BYTE:
            self.proof = Bytes(self.proof[:-1] + corrupt_byte(self.proof[-1:]))
        elif mode == self.ProofCorruptionMode.CORRUPT_TO_ALL_ZEROES:
            self.proof = Bytes(bytes(len(self.proof)))
        elif mode == self.ProofCorruptionMode.CORRUPT_ALL_BYTES:
            self.proof = Bytes(b"".join(corrupt_byte(bytes([byte])) for byte in self.proof))
