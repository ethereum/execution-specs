"""
Defines EIP-7999 specification constants and functions.

The fee helpers mirror the EIP's `get_gas_limits`, `get_max_fee`,
`get_required_max_fee` and `get_priority_fee`, so tests can state the
exact wei a transaction pays and refunds.
"""

from dataclasses import dataclass
from typing import List, Sequence

from execution_testing import Fork, Transaction


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_7999 = ReferenceSpec(
    "EIPS/eip-7999.md", "6eae017eeae28e5f3c157885cbb689117c91008b"
)


@dataclass(frozen=True)
class FeeSettlement:
    """The wei a transaction pays at inclusion and keeps at settlement."""

    fee_to_deduct: int
    """Wei taken from the sender at inclusion."""

    base_fee_paid: int
    """Wei burned for the gas consumed in every resource."""

    priority_fee_paid: int
    """Wei paid to the block producer."""

    @property
    def total_paid(self) -> int:
        """Wei the sender does not get back."""
        return self.base_fee_paid + self.priority_fee_paid

    @property
    def refund(self) -> int:
        """Wei returned to the sender at settlement."""
        return self.fee_to_deduct - self.total_paid


@dataclass(frozen=True)
class Spec:
    """Constants and fee functions of the EIP-7999 specification."""

    MULTIDIM_TX_TYPE = 5

    EVM_GAS = 0
    BLOB_GAS = 1
    CALLDATA_GAS = 2
    RESOURCE_COUNT = 3
    TIPPED_RESOURCES = (EVM_GAS, CALLDATA_GAS)

    EVM_LIMIT_TARGET_RATIO = 2
    CALLDATA_GAS_LIMIT_RATIO = 4
    CALLDATA_LIMIT_TARGET_RATIO = 4
    GAS_RESERVE_FACTOR = (0, 16, 12)
    GAS_RESERVE_INDEX = (0, 0, 1)
    MIN_BASE_FEE_PER_GAS = 1
    GAS_NORMALIZATION_FACTOR = 10**9
    BASE_FEE_UPDATE_FRACTION = 4_245_093_508

    MAX_FEE_LIMIT = 2**128 - 1
    MAX_PRIORITY_FEE_PER_GAS_LIMIT = 2**64 - 1

    # The EIP assigns 0x4B, which Amsterdam gave to SLOTNUM (EIP-7843).
    CALLDATABASEFEE_OPCODE = 0x4C

    @staticmethod
    def calldata_gas(fork: Fork, tx: Transaction) -> int:
        """Return the gas the calldata resource charges for the data."""
        return fork.calldata_gas_calculator()(data=tx.data)

    @staticmethod
    def blob_gas(fork: Fork, tx: Transaction) -> int:
        """Return the blob gas of the transaction."""
        return fork.blob_gas_per_blob() * len(tx.blob_versioned_hashes or [])

    @classmethod
    def resource_gas_limits(cls, fork: Fork, tx: Transaction) -> List[int]:
        """
        Return the gas reserved in each resource, `get_gas_limits` in the
        EIP: an older transaction's gas limit is split into EVM gas and
        calldata gas, a multidimensional transaction lists its EVM gas.
        """
        calldata_gas = cls.calldata_gas(fork, tx)
        evm_gas = int(tx.gas_limit)
        if int(tx.ty) != cls.MULTIDIM_TX_TYPE:
            evm_gas -= calldata_gas
        return [evm_gas, cls.blob_gas(fork, tx), calldata_gas]

    @classmethod
    def max_fee(cls, fork: Fork, tx: Transaction) -> int:
        """
        Return the transaction's fee budget, `get_max_fee` in the EIP: an
        older transaction's fee caps per gas over its gas limit and blob
        gas.
        """
        if int(tx.ty) == cls.MULTIDIM_TX_TYPE:
            assert tx.max_fee is not None
            return int(tx.max_fee)
        if tx.gas_price is not None:
            return int(tx.gas_price) * int(tx.gas_limit)
        assert tx.max_fee_per_gas is not None
        budget = int(tx.max_fee_per_gas) * int(tx.gas_limit)
        if tx.max_fee_per_blob_gas is not None:
            budget += int(tx.max_fee_per_blob_gas) * cls.blob_gas(fork, tx)
        return budget

    @staticmethod
    def resource_fees(base_fees: Sequence[int], gas: Sequence[int]) -> int:
        """Price gas amounts at their resources' base fees and sum them."""
        return sum(
            base_fee * amount
            for base_fee, amount in zip(base_fees, gas, strict=True)
        )

    @classmethod
    def priority_fee(
        cls,
        tx: Transaction,
        gas: Sequence[int],
        base_fees: Sequence[int],
        remaining_fee: int,
    ) -> int:
        """
        Return the priority fee on the given gas amounts, `get_priority_fee`
        in the EIP. Blob gas carries no tip under a single cap; a cap per
        resource tips every resource's gas, blobs included.
        """
        tipped_gas = sum(gas[i] for i in cls.TIPPED_RESOURCES)
        tipped_base_fee = sum(
            gas[i] * base_fees[i] for i in cls.TIPPED_RESOURCES
        )
        if int(tx.ty) == cls.MULTIDIM_TX_TYPE:
            assert tx.max_fee is not None
            assert tx.max_priority_fees_per_gas is not None
            caps = [int(cap) for cap in tx.max_priority_fees_per_gas]
            if len(caps) == 1:
                tipped_max_fee = (
                    int(tx.max_fee)
                    - gas[cls.BLOB_GAS] * base_fees[cls.BLOB_GAS]
                )
                tipped_priority_fee = max(0, tipped_max_fee - tipped_base_fee)
                max_priority_fee = min(
                    caps[0] * tipped_gas, tipped_priority_fee
                )
            else:
                max_priority_fee = sum(
                    cap * amount for cap, amount in zip(caps, gas, strict=True)
                )
            return min(max_priority_fee, remaining_fee)
        if tx.gas_price is not None:
            return max(0, int(tx.gas_price) * tipped_gas - tipped_base_fee)
        assert tx.max_fee_per_gas is not None
        assert tx.max_priority_fee_per_gas is not None
        tipped_max_fee = int(tx.max_fee_per_gas) * tipped_gas
        tipped_priority_fee = max(0, tipped_max_fee - tipped_base_fee)
        max_priority_fee = min(
            int(tx.max_priority_fee_per_gas) * tipped_gas, tipped_priority_fee
        )
        if tx.max_fee_per_blob_gas is not None:
            return min(max_priority_fee, remaining_fee)
        return max_priority_fee

    @classmethod
    def settle(
        cls,
        fork: Fork,
        tx: Transaction,
        base_fees: Sequence[int],
        evm_gas_used: int,
    ) -> FeeSettlement:
        """
        Settle a transaction that consumed `evm_gas_used` EVM gas and all
        of its blob and calldata gas.
        """
        gas_limits = cls.resource_gas_limits(fork, tx)
        max_fee = cls.max_fee(fork, tx)
        required_max_fee = cls.resource_fees(base_fees, gas_limits)
        assert required_max_fee <= max_fee, "test correctness: budget short"
        fee_to_deduct = required_max_fee + cls.priority_fee(
            tx, gas_limits, base_fees, max_fee - required_max_fee
        )
        gas_consumed = [
            evm_gas_used,
            gas_limits[cls.BLOB_GAS],
            gas_limits[cls.CALLDATA_GAS],
        ]
        base_fee_paid = cls.resource_fees(base_fees, gas_consumed)
        priority_fee_paid = cls.priority_fee(
            tx, gas_consumed, base_fees, fee_to_deduct - base_fee_paid
        )
        return FeeSettlement(fee_to_deduct, base_fee_paid, priority_fee_paid)

    @classmethod
    def effective_gas_price(
        cls, fork: Fork, tx: Transaction, base_fees: Sequence[int]
    ) -> int:
        """
        Return what GASPRICE reports: the EVM base fee plus the priority fee
        admitted with the transaction, spread over its tipped gas. The EIP
        leaves GASPRICE unspecified; this is the prototype's definition.
        """
        gas_limits = cls.resource_gas_limits(fork, tx)
        max_fee = cls.max_fee(fork, tx)
        required_max_fee = cls.resource_fees(base_fees, gas_limits)
        priority_fee = cls.priority_fee(
            tx, gas_limits, base_fees, max_fee - required_max_fee
        )
        tipped_gas = sum(gas_limits[i] for i in cls.TIPPED_RESOURCES)
        return base_fees[cls.EVM_GAS] + priority_fee // tipped_gas
