"""
EIP-7999: Unified multidimensional fee market.

Each transaction carries one `max_fee` budget for every resource it
reserves. The block header carries per-resource gas limits, gas used, and
a normalized excess gas vector from which each resource's base fee
derives. Calldata becomes the first resource beside EVM and blob gas.

https://eips.ethereum.org/EIPS/eip-7999
"""

from typing import Callable, Dict, List

from execution_testing.base_types import AccessList
from execution_testing.base_types.conversions import BytesConvertible
from execution_testing.vm import OpcodeBase, Opcodes

from .....recipient_type import RecipientType
from ....base_fork import (
    BaseFeePerGasCalculator,
    BaseFeesCalculator,
    BaseFork,
    BlobGasPriceCalculator,
    BlockGasLimitsCalculator,
    ExcessBlobGasCalculator,
    ExcessGasCalculator,
    GenesisExcessGasCalculator,
    InitialExcessGasCalculator,
    TransactionDataFloorCostCalculator,
)
from ...helpers import fake_exponential

EVM_GAS_RESOURCE = 0
BLOB_GAS_RESOURCE = 1
CALLDATA_GAS_RESOURCE = 2
RESOURCE_COUNT = 3

EVM_LIMIT_TARGET_RATIO = 2
CALLDATA_GAS_LIMIT_RATIO = 4
CALLDATA_LIMIT_TARGET_RATIO = 4
GAS_RESERVE_FACTOR = (0, 16, 12)
GAS_RESERVE_INDEX = (0, 0, 1)
MIN_BASE_FEE_PER_GAS = 1
GAS_NORMALIZATION_FACTOR = 10**9
BASE_FEE_UPDATE_FRACTION = 4_245_093_508

MULTIDIM_TX_TYPE = 5

NOMINAL_EVM_GAS_LIMIT = 30_000_000
"""EVM gas limit used when only the blob dimension's update is wanted."""


class EIP7999(
    BaseFork,
    # The header and payload change shape: gas limits, gas used, and excess
    # gas become per-resource vectors.
    engine_new_payload_version_bump=True,
    engine_get_payload_version_bump=True,
    engine_forkchoice_updated_version_bump=True,
):
    """EIP-7999 class."""

    @classmethod
    def header_gas_vectors_required(cls) -> bool:
        """Per-resource gas vectors replace the scalar gas fields."""
        return True

    @classmethod
    def tx_types(cls) -> List[int]:
        """Multidimensional transactions are introduced."""
        return [MULTIDIM_TX_TYPE] + super(EIP7999, cls).tx_types()

    @classmethod
    def contract_creating_tx_types(cls) -> List[int]:
        """A multidimensional transaction without blobs can create."""
        return [MULTIDIM_TX_TYPE] + super(
            EIP7999, cls
        ).contract_creating_tx_types()

    @classmethod
    def transaction_data_floor_cost_calculator(
        cls,
    ) -> TransactionDataFloorCostCalculator:
        """
        Retire the EIP-7623 floor: calldata is priced by its own resource.
        """

        def fn(
            *,
            data: BytesConvertible,
            access_list: List[AccessList] | None = None,
            contract_creation: bool = False,
            sends_value: bool = False,
            recipient_type: RecipientType = RecipientType.CONTRACT,
        ) -> int:
            del data, access_list
            del contract_creation, sends_value, recipient_type
            return 0

        return fn

    @classmethod
    def block_gas_limits_calculator(cls) -> BlockGasLimitsCalculator:
        """
        Return a callable that derives a block's per-resource gas limits
        from its EVM gas limit.
        """
        max_blob_gas = cls.max_blobs_per_block() * cls.blob_gas_per_blob()

        def fn(*, gas_limit: int) -> List[int]:
            return [
                gas_limit,
                max_blob_gas,
                gas_limit // CALLDATA_GAS_LIMIT_RATIO,
            ]

        return fn

    @classmethod
    def _gas_targets(cls, gas_limits: List[int]) -> List[int]:
        """Return the per-resource gas targets for the given limits."""
        blob_target_gas = (
            cls.target_blobs_per_block() * cls.blob_gas_per_blob()
        )
        return [
            gas_limits[EVM_GAS_RESOURCE] // EVM_LIMIT_TARGET_RATIO,
            blob_target_gas,
            gas_limits[CALLDATA_GAS_RESOURCE] // CALLDATA_LIMIT_TARGET_RATIO,
        ]

    @staticmethod
    def _resource_base_fee(excess_gas: int) -> int:
        """Price a resource from its normalized excess gas."""
        return fake_exponential(
            MIN_BASE_FEE_PER_GAS, excess_gas, BASE_FEE_UPDATE_FRACTION
        )

    @classmethod
    def _invert_base_fee(cls, base_fee_per_gas: int) -> int:
        """
        Return the smallest excess gas pricing at or above
        `base_fee_per_gas`.
        """
        low, high = 0, 1
        while cls._resource_base_fee(high) < base_fee_per_gas:
            high *= 2
        while low < high:
            mid = (low + high) // 2
            if cls._resource_base_fee(mid) < base_fee_per_gas:
                low = mid + 1
            else:
                high = mid
        return low

    @classmethod
    def _normalized_blob_excess(cls, excess_blob_gas: int) -> int:
        """Scale an EIP-4844 excess blob gas to the normalized units."""
        max_blob_gas = cls.max_blobs_per_block() * cls.blob_gas_per_blob()
        return excess_blob_gas * GAS_NORMALIZATION_FACTOR // max_blob_gas

    @classmethod
    def _denormalized_blob_excess(cls, excess_gas: int) -> int:
        """Scale a normalized blob excess back to EIP-4844 units."""
        max_blob_gas = cls.max_blobs_per_block() * cls.blob_gas_per_blob()
        return excess_gas * max_blob_gas // GAS_NORMALIZATION_FACTOR

    @classmethod
    def base_fees_calculator(cls) -> BaseFeesCalculator:
        """Return a callable that prices every resource from excess gas."""

        def fn(*, excess_gas: List[int]) -> List[int]:
            return [cls._resource_base_fee(excess) for excess in excess_gas]

        return fn

    @classmethod
    def initial_excess_gas_calculator(cls) -> InitialExcessGasCalculator:
        """
        Return a callable that builds the excess gas pricing a given base
        fee and EIP-4844 excess blob gas, for a block without a
        multidimensional parent.
        """

        def fn(*, base_fee_per_gas: int, excess_blob_gas: int) -> List[int]:
            return [
                cls._invert_base_fee(base_fee_per_gas),
                cls._normalized_blob_excess(excess_blob_gas),
                0,
            ]

        return fn

    @classmethod
    def genesis_excess_gas_calculator(cls) -> GenesisExcessGasCalculator:
        """
        Return a callable that builds a genesis excess gas such that the
        empty genesis block leaves its child priced exactly at the given
        base fee and EIP-4844 excess blob gas.
        """
        blob_target_gas = (
            cls.target_blobs_per_block() * cls.blob_gas_per_blob()
        )

        def fn(
            *, base_fee_per_gas: int, excess_blob_gas: int, gas_limit: int
        ) -> List[int]:
            gas_limits = cls.block_gas_limits_calculator()(gas_limit=gas_limit)
            evm_target = cls._gas_targets(gas_limits)[EVM_GAS_RESOURCE]
            evm_excess = cls._invert_base_fee(base_fee_per_gas) + (
                evm_target
                * GAS_NORMALIZATION_FACTOR
                // gas_limits[EVM_GAS_RESOURCE]
            )
            blob_excess = cls._normalized_blob_excess(
                excess_blob_gas + blob_target_gas
            )
            return [evm_excess, blob_excess, 0]

        return fn

    @classmethod
    def excess_gas_calculator(cls) -> ExcessGasCalculator:
        """
        Return a callable that computes a block's excess gas from its
        parent's vectors, `calc_excess_gas` in EIP-7999.
        """

        def fn(
            *,
            parent_excess_gas: List[int],
            parent_gas_used: List[int],
            parent_gas_limits: List[int],
        ) -> List[int]:
            base_fees = cls.base_fees_calculator()(
                excess_gas=parent_excess_gas
            )
            targets = cls._gas_targets(parent_gas_limits)
            excess_gas = []
            for i in range(RESOURCE_COUNT):
                excess = parent_excess_gas[i]
                limit = parent_gas_limits[i]
                used = parent_gas_used[i]
                target = targets[i]
                reserve_factor = GAS_RESERVE_FACTOR[i]
                anchor_base_fee = base_fees[GAS_RESERVE_INDEX[i]]
                if (
                    reserve_factor > 0
                    and base_fees[i] * reserve_factor < anchor_base_fee
                ):
                    delta = used * (limit - target) // limit
                    excess += delta * GAS_NORMALIZATION_FACTOR // limit
                elif used >= target:
                    delta = used - target
                    excess += delta * GAS_NORMALIZATION_FACTOR // limit
                else:
                    normalized_delta = (
                        (target - used) * GAS_NORMALIZATION_FACTOR // limit
                    )
                    excess = max(0, excess - normalized_delta)
                excess_gas.append(excess)
            return excess_gas

        return fn

    @classmethod
    def base_fee_per_gas_calculator(cls) -> BaseFeePerGasCalculator:
        """
        Return a callable that computes the EVM base fee from the parent's
        scalar fields.

        The parent's price is inverted into an excess gas before the
        update, which drops the fraction of excess the parent's header
        carried, so the result is exact only when that excess was itself
        an inversion, as in a test chain started from a genesis base fee.
        """

        def fn(
            *,
            parent_base_fee_per_gas: int,
            parent_gas_used: int,
            parent_gas_limit: int,
        ) -> int:
            gas_limits = cls.block_gas_limits_calculator()(
                gas_limit=parent_gas_limit
            )
            excess_gas = cls.excess_gas_calculator()(
                parent_excess_gas=[
                    cls._invert_base_fee(parent_base_fee_per_gas),
                    0,
                    0,
                ],
                parent_gas_used=[parent_gas_used, 0, 0],
                parent_gas_limits=gas_limits,
            )
            return cls._resource_base_fee(excess_gas[EVM_GAS_RESOURCE])

        return fn

    @classmethod
    def blob_gas_price_calculator(cls) -> BlobGasPriceCalculator:
        """
        Return a callable that prices blob gas from an EIP-4844 excess blob
        gas, the units the header's `excess_blob_gas` mirror keeps.
        """

        def fn(*, excess_blob_gas: int) -> int:
            return cls._resource_base_fee(
                cls._normalized_blob_excess(excess_blob_gas)
            )

        return fn

    @classmethod
    def excess_blob_gas_calculator(cls) -> ExcessBlobGasCalculator:
        """
        Return a callable that computes a block's blob excess from its
        parent in EIP-4844 units, the units the header's `excess_blob_gas`
        mirror keeps. The EIP-7999 update runs in normalized units and the
        result is scaled back.
        """
        blob_gas_per_blob = cls.blob_gas_per_blob()

        def fn(
            *,
            parent_excess_blob_gas: int | None = None,
            parent_excess_blobs: int | None = None,
            parent_blob_gas_used: int | None = None,
            parent_blob_count: int | None = None,
            parent_base_fee_per_gas: int,
        ) -> int:
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
            gas_limits = cls.block_gas_limits_calculator()(
                gas_limit=NOMINAL_EVM_GAS_LIMIT
            )
            excess_gas = cls.excess_gas_calculator()(
                parent_excess_gas=[
                    cls._invert_base_fee(parent_base_fee_per_gas),
                    cls._normalized_blob_excess(parent_excess_blob_gas),
                    0,
                ],
                parent_gas_used=[0, parent_blob_gas_used, 0],
                parent_gas_limits=gas_limits,
            )
            return cls._denormalized_blob_excess(excess_gas[BLOB_GAS_RESOURCE])

        return fn

    @classmethod
    def opcode_gas_map(
        cls,
    ) -> Dict[OpcodeBase, int | Callable[[OpcodeBase], int]]:
        """Add CALLDATABASEFEE opcode gas cost."""
        gas_costs = cls.gas_costs()
        base_map = super(EIP7999, cls).opcode_gas_map()
        return {
            **base_map,
            Opcodes.CALLDATABASEFEE: gas_costs.BASE,
        }

    @classmethod
    def valid_opcodes(cls) -> List[Opcodes]:
        """Add CALLDATABASEFEE opcode."""
        return [Opcodes.CALLDATABASEFEE] + super(EIP7999, cls).valid_opcodes()
