"""Defines EIP-4844 specification constants and functions."""

import itertools
import math
from dataclasses import dataclass
from hashlib import sha256
from typing import List, Optional, Set, Tuple

import pytest
from execution_testing import Fork, ParameterSet, Transaction


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_4844 = ReferenceSpec(
    "EIPS/eip-4844.md", "de2e4a46ad93fc04e6fe3174dc6e90a3307bdb5f"
)


# Constants
@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-4844 specifications as defined at
    https://eips.ethereum.org/EIPS/eip-4844#parameters.

    If the parameter is not currently used within the tests, it is commented
    out.
    """

    BLOB_TX_TYPE = 0x03
    FIELD_ELEMENTS_PER_BLOB = 4096
    BLS_MODULUS = (
        0x73EDA753299D7D483339D80809A1D80553BDA402FFFE5BFEFFFFFFFF00000001
    )
    BLOB_COMMITMENT_VERSION_KZG = 1
    POINT_EVALUATION_PRECOMPILE_ADDRESS = 10
    POINT_EVALUATION_PRECOMPILE_GAS = 50_000
    # MAX_VERSIONED_HASHES_LIST_SIZE = 2**24
    # MAX_CALLDATA_SIZE = 2**24
    # MAX_ACCESS_LIST_SIZE = 2**24
    # MAX_ACCESS_LIST_STORAGE_KEYS = 2**24
    # MAX_TX_WRAP_COMMITMENTS = 2**12
    # LIMIT_BLOBS_PER_TX = 2**12
    HASH_OPCODE_BYTE = 0x49
    HASH_GAS_COST = 3
    GAS_PER_BLOB = 2**17

    @classmethod
    def kzg_to_versioned_hash(
        cls,
        kzg_commitment: bytes | int,  # 48 bytes
        blob_commitment_version_kzg: Optional[bytes | int] = None,
    ) -> bytes:
        """Calculate versioned hash for a given KZG commitment."""
        if blob_commitment_version_kzg is None:
            blob_commitment_version_kzg = cls.BLOB_COMMITMENT_VERSION_KZG
        if isinstance(kzg_commitment, int):
            kzg_commitment = kzg_commitment.to_bytes(48, "big")
        if isinstance(blob_commitment_version_kzg, int):
            blob_commitment_version_kzg = blob_commitment_version_kzg.to_bytes(
                1, "big"
            )
        return (
            blob_commitment_version_kzg + sha256(kzg_commitment).digest()[1:]
        )

    @classmethod
    def get_total_blob_gas(
        cls, *, tx: Transaction, blob_gas_per_blob: int
    ) -> int:
        """Calculate the total blob gas for a transaction."""
        if tx.blob_versioned_hashes is None:
            return 0
        return blob_gas_per_blob * len(tx.blob_versioned_hashes)


@dataclass(frozen=True)
class SpecHelpers:
    """
    Define parameters and helper functions that are tightly coupled to the 4844
    spec but not strictly part of it.
    """

    BYTES_PER_FIELD_ELEMENT = 32
    _EXHAUSTIVE_MAX_BLOBS_PER_BLOCK = (
        9  # Osaka max; exhaustive is tractable up to here
    )

    @classmethod
    def get_representative_blob_combinations(
        cls,
        blob_count: int,
        max_blobs_per_tx: int,
    ) -> List[Tuple[int, ...]]:
        """
        Get a bounded set of representative blob-per-tx partitions for a given
        blob count, instead of exhaustively enumerating all valid partitions.
        """
        n = blob_count
        if n < 1:
            return []
        m = max_blobs_per_tx
        seen: Set[Tuple[int, ...]] = set()
        result: List[Tuple[int, ...]] = []

        def add(combo: Tuple[int, ...]) -> None:
            if combo not in seen:
                seen.add(combo)
                result.append(combo)

        # 1. Single tx (if it fits)
        # e.g. n=5, m=6 → (5,)
        if n <= m:
            add((n,))

        # 2. All singles
        # e.g. n=10 → (1,1,1,1,1,1,1,1,1,1)
        if n > 1:
            add((1,) * n)

        # 3. Greedy pack: fill max-sized txs first
        # e.g. n=10, m=6 → (6,4)
        if n > m:
            q, r = divmod(n, m)
            greedy = (m,) * q + ((r,) if r else ())
            add(greedy)

            # 4. Reversed greedy
            # e.g. n=10, m=6 → (4,6)
            rev = tuple(reversed(greedy))
            add(rev)

        # 5. One big tx + singles for the rest (and reversed)
        # e.g. n=10, m=6 → (6,1,1,1,1) and (1,1,1,1,6)
        if n > 1:
            big = min(n - 1, m)
            rest = n - big
            combo = (big,) + (1,) * rest
            add(combo)
            add(tuple(reversed(combo)))

        # 6. Balanced split into two txs (and reversed)
        # e.g. n=10, m=6 → (5,5); n=9, m=6 → (5,4) and (4,5)
        if n > 1:
            half_hi = math.ceil(n / 2)
            half_lo = n - half_hi
            if half_hi <= m and half_lo >= 1:
                add((half_hi, half_lo))
                if half_hi != half_lo:
                    add((half_lo, half_hi))

        # 7. Uniform non-max: all txs same size, 1 < k < m
        # e.g. n=12, m=6 → (4,4,4); n=15, m=6 → (5,5,5)
        if n > 1:
            for k in range(m - 1, 1, -1):
                if n % k == 0 and n // k > 1:
                    add((k,) * (n // k))
                    break

        return result

    @classmethod
    def get_representative_invalid_blob_combinations(
        cls,
        fork: Fork,
    ) -> List[Tuple[int, ...]]:
        """
        Get a bounded set of representative invalid blob-per-tx partitions
        that exceed the block blob limit by exactly one.
        """
        max_blobs_per_block = fork.max_blobs_per_block()
        max_blobs_per_tx = fork.max_blobs_per_tx()
        total = max_blobs_per_block + 1
        m = max_blobs_per_tx
        seen: Set[Tuple[int, ...]] = set()
        result: List[Tuple[int, ...]] = []

        def add(combo: Tuple[int, ...]) -> None:
            if combo not in seen:
                seen.add(combo)
                result.append(combo)

        # 1. Single oversized tx — e.g. (16,)
        add((total,))

        # 2. Greedy pack of total — e.g. total=16, m=6 → (6,6,4)
        q, r = divmod(total, m)
        greedy = (m,) * q + ((r,) if r else ())
        add(greedy)

        # 3. All singles — e.g. (1,)*16
        add((1,) * total)

        # 4. One full tx + overflow — e.g. total=16, m=6 → (6,10)
        overflow = total - m
        if overflow >= 1:
            add((m, overflow))

        # 5. One blob + full block — e.g. (1,21)
        # Per-tx-oversized elements must be last: the test sends all txs from
        # one sender with sequential nonces, so a rejected non-last tx creates
        # a nonce gap that causes subsequent txs to fail with NONCE_MISMATCH,
        # not the expected blob error.
        add((1, max_blobs_per_block))

        # 6. Balanced all-valid: near-equal tx sizes, all within per-tx limit
        # e.g. total=16, m=6 → (6,5,5)
        num_txs = math.ceil(total / m)
        base, extra = divmod(total, num_txs)
        balanced = (base + 1,) * extra + (base,) * (num_txs - extra)
        if all(b <= m for b in balanced):
            add(balanced)

        return result

    @classmethod
    def get_min_excess_blob_gas_for_blob_gas_price(
        cls,
        *,
        fork: Fork,
        blob_gas_price: int,
    ) -> int:
        """
        Get the minimum required excess blob gas value to get a given blob gas
        cost in a block.
        """
        current_excess_blob_gas = 0
        current_blob_gas_price = 1
        get_blob_gas_price = fork.blob_gas_price_calculator()
        gas_per_blob = fork.blob_gas_per_blob()
        while current_blob_gas_price < blob_gas_price:
            current_excess_blob_gas += gas_per_blob
            current_blob_gas_price = get_blob_gas_price(
                excess_blob_gas=current_excess_blob_gas
            )
        return current_excess_blob_gas

    @classmethod
    def get_min_excess_blobs_for_blob_gas_price(
        cls,
        *,
        fork: Fork,
        blob_gas_price: int,
    ) -> int:
        """
        Get the minimum required excess blobs to get a given blob gas cost in a
        block.
        """
        gas_per_blob = fork.blob_gas_per_blob()
        return (
            cls.get_min_excess_blob_gas_for_blob_gas_price(
                fork=fork,
                blob_gas_price=blob_gas_price,
            )
            // gas_per_blob
        )

    @classmethod
    def get_blob_combinations(
        cls,
        blob_count: int,
        max_blobs_per_tx: int,
    ) -> List[Tuple[int, ...]]:
        """
        Get all possible combinations of blobs that result in a given blob
        count.
        """
        combinations = [
            seq
            for i in range(
                blob_count + 1, 0, -1
            )  # We can have from 1 to at most MAX_BLOBS_PER_BLOCK blobs per
            # block
            for seq in itertools.combinations_with_replacement(
                range(1, min(blob_count + 1, max_blobs_per_tx) + 1), i
            )  # We iterate through all possible combinations
            # And we only keep the ones that match the expected blob count
            if sum(seq) == blob_count
            and all(tx_blobs <= max_blobs_per_tx for tx_blobs in seq)
            # Validate each tx
        ]

        # We also add the reversed version of each combination, only if it's
        # not already in the list. E.g. (4, 1) is added from (1, 4) but not (1,
        # 1, 1, 1, 1) because its reversed version is identical.
        combinations += [
            tuple(reversed(x))
            for x in combinations
            if tuple(reversed(x)) not in combinations
        ]
        return combinations

    @classmethod
    def all_valid_blob_combinations(cls, fork: Fork) -> List[ParameterSet]:
        """
        Return all valid blob tx combinations for a given block, assuming the
        given MAX_BLOBS_PER_BLOCK, whilst respecting MAX_BLOBS_PER_TX.
        """
        max_blobs_per_block = fork.max_blobs_per_block()
        max_blobs_per_tx = fork.max_blobs_per_tx()
        exhaustive = max_blobs_per_block <= cls._EXHAUSTIVE_MAX_BLOBS_PER_BLOCK

        combinations: List[Tuple[int, ...]] = []
        for i in range(1, max_blobs_per_block + 1):
            if exhaustive:
                combinations += cls.get_blob_combinations(i, max_blobs_per_tx)
            else:
                combinations += cls.get_representative_blob_combinations(
                    i, max_blobs_per_tx
                )
        return [
            pytest.param(
                combination,
                id=f"blobs_per_tx_{repr(combination).replace(' ', '')}",
            )
            for combination in combinations
        ]

    @classmethod
    def invalid_blob_combinations(cls, fork: Fork) -> List[ParameterSet]:
        """
        Return invalid blob tx combinations for a given block that use up to
        MAX_BLOBS_PER_BLOCK+1 blobs.
        """
        max_blobs_per_block = fork.max_blobs_per_block()
        max_blobs_per_tx = fork.max_blobs_per_tx()

        invalid_combinations: List[Tuple[int, ...]] = []
        if max_blobs_per_block <= cls._EXHAUSTIVE_MAX_BLOBS_PER_BLOCK:
            invalid_combinations += cls.get_blob_combinations(
                max_blobs_per_block + 1,
                max_blobs_per_tx,
            )
            invalid_combinations.append((max_blobs_per_block + 1,))
        else:
            invalid_combinations = (
                cls.get_representative_invalid_blob_combinations(fork)
            )
        return [
            pytest.param(
                combination,
                id=f"blobs_per_tx_{repr(combination).replace(' ', '')}",
            )
            for combination in invalid_combinations
        ]
