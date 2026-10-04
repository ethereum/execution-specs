"""Reference spec for [EIP-8198: Quick Slots](https://eips.ethereum.org/EIPS/eip-8198)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


ref_spec_8198 = ReferenceSpec(
    git_path="EIPS/eip-8198.md",
    version="e256c0d5ef51182f42488b5d1da2eb57228b8dd8",
)


@dataclass(frozen=True)
class Spec:
    """
    Parameters and reference arithmetic from the EIP-8198 execution layer
    changes.

    The arithmetic is restated here, independently of the framework's fork
    classes, so that the tests check the values the EIP specifies.
    """

    FORK_TIMESTAMP = 15_000

    BASE_FEE_MAX_CHANGE_NUMERATOR = 5
    BASE_FEE_MAX_CHANGE_DENOMINATOR = 48
    ELASTICITY_MULTIPLIER = 2
    GAS_LIMIT_ADJUSTMENT_FACTOR = 1024

    # Provisional blob schedule, pending a joint decision with the consensus
    # layer.
    TARGET_BLOBS_PER_BLOCK = 12
    MAX_BLOBS_PER_BLOCK = 18
    BLOB_BASE_FEE_UPDATE_FRACTION = 12018519

    GAS_PER_BLOB = 2**17
    BLOB_BASE_COST = 2**13
    MIN_BLOB_BASE_FEE = 1
    BLOB_TX_TYPE = 3
    BLOB_COMMITMENT_VERSION_KZG = 1

    @staticmethod
    def next_base_fee(
        *,
        parent_base_fee_per_gas: int,
        parent_gas_used: int,
        parent_gas_limit: int,
        numerator: int,
        denominator: int,
    ) -> int:
        """
        Return the base fee of a block from its parent, for a maximum
        per-block change of `numerator / denominator`, multiplying before
        dividing.
        """
        parent_gas_target = parent_gas_limit // Spec.ELASTICITY_MULTIPLIER
        if parent_gas_used == parent_gas_target:
            return parent_base_fee_per_gas
        gas_used_delta = abs(parent_gas_used - parent_gas_target)
        target_fee_gas_delta = (
            parent_base_fee_per_gas * gas_used_delta // parent_gas_target
        )
        base_fee_per_gas_delta = (
            target_fee_gas_delta * numerator // denominator
        )
        if parent_gas_used > parent_gas_target:
            return parent_base_fee_per_gas + max(base_fee_per_gas_delta, 1)
        return parent_base_fee_per_gas - base_fee_per_gas_delta

    @staticmethod
    def fake_exponential(factor: int, numerator: int, denominator: int) -> int:
        """Approximate `factor * e ** (numerator / denominator)`."""
        i = 1
        output = 0
        numerator_accumulator = factor * denominator
        while numerator_accumulator > 0:
            output += numerator_accumulator
            numerator_accumulator = (numerator_accumulator * numerator) // (
                denominator * i
            )
            i += 1
        return output // denominator

    @staticmethod
    def blob_base_fee(*, excess_blob_gas: int, update_fraction: int) -> int:
        """Return the blob base fee for the given excess blob gas."""
        return Spec.fake_exponential(
            Spec.MIN_BLOB_BASE_FEE, excess_blob_gas, update_fraction
        )

    @staticmethod
    def next_excess_blob_gas(
        *,
        parent_excess_blob_gas: int,
        parent_blob_gas_used: int,
        parent_base_fee_per_gas: int,
        target_blobs_per_block: int,
        max_blobs_per_block: int,
        update_fraction: int,
    ) -> int:
        """
        Return the excess blob gas of a block from its parent, including the
        blob base fee reserve price.
        """
        target_blob_gas = target_blobs_per_block * Spec.GAS_PER_BLOB
        if parent_excess_blob_gas + parent_blob_gas_used < target_blob_gas:
            return 0
        reserve_price = Spec.BLOB_BASE_COST * parent_base_fee_per_gas
        target_blob_gas_price = Spec.GAS_PER_BLOB * Spec.blob_base_fee(
            excess_blob_gas=parent_excess_blob_gas,
            update_fraction=update_fraction,
        )
        if reserve_price > target_blob_gas_price:
            return (
                parent_excess_blob_gas
                + parent_blob_gas_used
                * (max_blobs_per_block - target_blobs_per_block)
                // max_blobs_per_block
            )
        return parent_excess_blob_gas + parent_blob_gas_used - target_blob_gas
