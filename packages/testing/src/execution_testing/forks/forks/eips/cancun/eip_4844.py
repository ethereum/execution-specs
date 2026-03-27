"""
EIP-4844: Shard Blob Transactions.

Shard Blob Transactions scale data-availability of Ethereum in a simple,
forwards-compatible manner.

https://eips.ethereum.org/EIPS/eip-4844
"""

from dataclasses import replace
from typing import Callable, Dict, List

from execution_testing.base_types import (
    Address,
    BlobSchedule,
    ForkBlobSchedule,
)
from execution_testing.vm import (
    OpcodeBase,
    Opcodes,
)

from ....base_fork import (
    BaseFork,
    BlobGasPriceCalculator,
    ExcessBlobGasCalculator,
)
from ....gas_costs import GasCosts
from ...helpers import fake_exponential


class EIP4844(
    BaseFork,
    update_blob_constants={
        "FIELD_ELEMENTS_PER_BLOB": 4096,
        "BYTES_PER_FIELD_ELEMENT": 32,
        "CELL_LENGTH": 2048,
        # EIP-2537: Main subgroup order = q, due to this BLS_MODULUS
        # every blob byte (uint256) must be smaller than 116
        "BLS_MODULUS": (
            0x73EDA753299D7D483339D80809A1D80553BDA402FFFE5BFEFFFFFFFF00000001
        ),
        # https://github.com/ethereum/consensus-specs/blob/
        # cc6996c22692d70e41b7a453d925172ee4b719ad/specs/deneb/
        # polynomial-commitments.md?plain=1#L78
        "BYTES_PER_PROOF": 48,
        "BYTES_PER_COMMITMENT": 48,
        "AMOUNT_CELL_PROOFS": 0,
        "BLOB_GAS_PER_BLOB": 2**17,
        "MAX_BLOBS_PER_BLOCK": 6,
        "TARGET_BLOBS_PER_BLOCK": 3,
        "BLOB_BASE_FEE_UPDATE_FRACTION": 3338477,
        "MIN_BASE_FEE_PER_BLOB_GAS": 1,
    },
    # Engine API method version bumps
    engine_new_payload_version_bump=True,
    engine_forkchoice_updated_version_bump=True,
    engine_get_payload_version_bump=True,
    engine_get_blobs_version_bump=True,
):
    """EIP-4844 class."""

    @classmethod
    def header_excess_blob_gas_required(cls) -> bool:
        """Excess blob gas is required starting from Cancun."""
        return True

    @classmethod
    def header_blob_gas_used_required(cls) -> bool:
        """Blob gas used is required starting from Cancun."""
        return True

    @classmethod
    def blob_gas_price_calculator(cls) -> BlobGasPriceCalculator:
        """Return a callable that calculates the blob gas price at Cancun."""
        min_base_fee_per_blob_gas = cls.min_base_fee_per_blob_gas()
        blob_base_fee_update_fraction = cls.blob_base_fee_update_fraction()

        def fn(*, excess_blob_gas: int) -> int:
            return fake_exponential(
                min_base_fee_per_blob_gas,
                excess_blob_gas,
                blob_base_fee_update_fraction,
            )

        return fn

    @classmethod
    def excess_blob_gas_calculator(cls) -> ExcessBlobGasCalculator:
        """
        Return a callable that calculates the excess blob gas for a block at
        Cancun.
        """
        target_blobs_per_block = cls.target_blobs_per_block()
        blob_gas_per_blob = cls.blob_gas_per_blob()
        blob_target_gas_per_block = target_blobs_per_block * blob_gas_per_blob

        def fn(
            *,
            parent_excess_blob_gas: int | None = None,
            parent_excess_blobs: int | None = None,
            parent_blob_gas_used: int | None = None,
            parent_blob_count: int | None = None,
            # Required for Osaka as using this as base
            parent_base_fee_per_gas: int,
        ) -> int:
            del parent_base_fee_per_gas

            if parent_excess_blob_gas is None:
                assert parent_excess_blobs is not None, (
                    "Parent excess blobs are required"
                )
                parent_excess_blob_gas = (
                    parent_excess_blobs * blob_gas_per_blob
                )
            if parent_blob_gas_used is None:
                assert parent_blob_count is not None, (
                    "Parent blob count is required"
                )
                parent_blob_gas_used = parent_blob_count * blob_gas_per_blob
            if (
                parent_excess_blob_gas + parent_blob_gas_used
                < blob_target_gas_per_block
            ):
                return 0
            else:
                return (
                    parent_excess_blob_gas
                    + parent_blob_gas_used
                    - blob_target_gas_per_block
                )

        return fn

    @classmethod
    def supports_blobs(cls) -> bool:
        """At Cancun, blobs support is enabled."""
        return True

    @classmethod
    def blob_reserve_price_active(cls) -> bool:
        """Blob reserve price is not supported in Cancun."""
        return False

    @classmethod
    def full_blob_tx_wrapper_version(cls) -> int | None:
        """
        Pre-Osaka forks don't use tx wrapper versions for full blob
        transactions.
        """
        return None

    @classmethod
    def blob_schedule(cls) -> BlobSchedule | None:
        """
        At Cancun, the fork object runs this routine to get the updated blob
        schedule.
        """
        parent_fork = cls.parent()
        assert parent_fork is not None, "Parent fork must be defined"
        blob_schedule = parent_fork.blob_schedule() or BlobSchedule()
        current_blob_schedule = ForkBlobSchedule(
            target_blobs_per_block=cls.target_blobs_per_block(),
            max_blobs_per_block=cls.max_blobs_per_block(),
            base_fee_update_fraction=cls.blob_base_fee_update_fraction(),
        )
        blob_schedule.append(fork=cls.name(), schedule=current_blob_schedule)
        return blob_schedule

    @classmethod
    def tx_types(cls) -> List[int]:
        """At Cancun, blob type transactions are introduced."""
        return [3] + super(EIP4844, cls).tx_types()

    @classmethod
    def precompiles(cls) -> List[Address]:
        """At Cancun, a precompile for kzg point evaluation is introduced."""
        return [
            Address(10, label="KZG_POINT_EVALUATION"),
        ] + super(EIP4844, cls).precompiles()

    @classmethod
    def engine_new_payload_blob_hashes(cls) -> bool:
        """From Cancun, payloads must have blob hashes."""
        return True

    @classmethod
    def gas_costs(cls) -> GasCosts:
        """On Cancun, the point evaluation precompile gas cost is set."""
        return replace(
            super(EIP4844, cls).gas_costs(),
            GAS_PRECOMPILE_POINT_EVALUATION=50_000,
        )

    @classmethod
    def opcode_gas_map(
        cls,
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """
        Return a mapping of opcodes to their gas costs for Cancun.

        Adds Cancun-specific opcodes: BLOBHASH, BLOBBASEFEE, TLOAD, TSTORE,
        MCOPY.
        """
        gas_costs = cls.gas_costs()

        # Get parent fork's opcode gas map
        base_map = super(EIP4844, cls).opcode_gas_map()

        # Add Cancun-specific opcodes
        return {**base_map, Opcodes.BLOBHASH: gas_costs.GAS_VERY_LOW}

    @classmethod
    def valid_opcodes(cls) -> List[Opcodes]:
        """Return list of Opcodes that are valid to work on this fork."""
        return [Opcodes.BLOBHASH] + super(EIP4844, cls).valid_opcodes()
