"""
EIP-1559: Fee market change for ETH 1.0 chain.

A transaction pricing mechanism that includes fixed-per-block network fee
that is burned and dynamically expands/contracts block sizes to deal with
transient congestion.

https://eips.ethereum.org/EIPS/eip-1559
"""

from typing import List

from ....base_fork import (
    BaseFeeChangeCalculator,
    BaseFeePerGasCalculator,
    BaseFork,
)


class EIP1559(BaseFork):
    """EIP-1559 class."""

    @classmethod
    def header_base_fee_required(cls) -> bool:
        """Header must contain the base fee."""
        return True

    @classmethod
    def tx_types(cls) -> List[int]:
        """Dynamic fee transactions are introduced."""
        return [2] + super(EIP1559, cls).tx_types()

    @classmethod
    def contract_creating_tx_types(cls) -> List[int]:
        """Dynamic fee transactions can create contracts."""
        return [2] + super(EIP1559, cls).contract_creating_tx_types()

    @classmethod
    def base_fee_max_change_denominator(cls) -> int:
        """Return the base fee max change denominator."""
        return 8

    @classmethod
    def base_fee_elasticity_multiplier(cls) -> int:
        """Return the base fee elasticity multiplier."""
        return 2

    @classmethod
    def base_fee_per_gas_calculator(cls) -> BaseFeePerGasCalculator:
        """
        Return a callable that calculates the base fee per gas.

        EIP-1559 block validation pseudo code:

        if INITIAL_FORK_BLOCK_NUMBER == block.number:
            expected_base_fee_per_gas = INITIAL_BASE_FEE
        elif parent_gas_used == parent_gas_target:
            expected_base_fee_per_gas = parent_base_fee_per_gas
        elif parent_gas_used > parent_gas_target:
            gas_used_delta = parent_gas_used - parent_gas_target
            base_fee_per_gas_delta = max( parent_base_fee_per_gas
                                  * gas_used_delta // parent_gas_target //
                                  BASE_FEE_MAX_CHANGE_DENOMINATOR, 1, )
            expected_base_fee_per_gas = parent_base_fee_per_gas +
                                       base_fee_per_gas_delta
        else:
            gas_used_delta = parent_gas_target - parent_gas_used
            base_fee_per_gas_delta = (
                              parent_base_fee_per_gas * gas_used_delta //
                              parent_gas_target //
                              BASE_FEE_MAX_CHANGE_DENOMINATOR
                              )
            expected_base_fee_per_gas = parent_base_fee_per_gas -
                                        base_fee_per_gas_delta
        """
        base_fee_max_change_denominator = cls.base_fee_max_change_denominator()
        elasticity_multiplier = cls.base_fee_elasticity_multiplier()

        def fn(
            *,
            parent_base_fee_per_gas: int,
            parent_gas_used: int,
            parent_gas_limit: int,
        ) -> int:
            parent_gas_target = parent_gas_limit // elasticity_multiplier
            if parent_gas_used == parent_gas_target:
                return parent_base_fee_per_gas
            elif parent_gas_used > parent_gas_target:
                gas_used_delta = parent_gas_used - parent_gas_target
                base_fee_per_gas_delta = max(
                    parent_base_fee_per_gas
                    * gas_used_delta
                    // parent_gas_target
                    // base_fee_max_change_denominator,
                    1,
                )
                return parent_base_fee_per_gas + base_fee_per_gas_delta
            else:
                gas_used_delta = parent_gas_target - parent_gas_used
                base_fee_per_gas_delta = (
                    parent_base_fee_per_gas
                    * gas_used_delta
                    // parent_gas_target
                    // base_fee_max_change_denominator
                )
                return parent_base_fee_per_gas - base_fee_per_gas_delta

        return fn

    @classmethod
    def base_fee_change_calculator(cls) -> BaseFeeChangeCalculator:
        """
        Return a callable that calculates the gas that needs to be used
        to change the base fee.
        """
        base_fee_max_change_denominator = cls.base_fee_max_change_denominator()
        elasticity_multiplier = cls.base_fee_elasticity_multiplier()
        base_fee_per_gas_calculator = cls.base_fee_per_gas_calculator()

        def fn(
            *,
            parent_base_fee_per_gas: int,
            parent_gas_limit: int,
            required_base_fee_per_gas: int,
        ) -> int:
            parent_gas_target = parent_gas_limit // elasticity_multiplier

            if parent_base_fee_per_gas == required_base_fee_per_gas:
                return parent_gas_target
            elif required_base_fee_per_gas > parent_base_fee_per_gas:
                base_fee_per_gas_delta = (
                    required_base_fee_per_gas - parent_base_fee_per_gas
                )
                parent_gas_used = (
                    (
                        base_fee_per_gas_delta
                        * base_fee_max_change_denominator
                        * parent_gas_target
                    )
                    // parent_base_fee_per_gas
                ) + parent_gas_target
            elif required_base_fee_per_gas < parent_base_fee_per_gas:
                base_fee_per_gas_delta = (
                    parent_base_fee_per_gas - required_base_fee_per_gas
                )

                parent_gas_used = (
                    parent_gas_target
                    - (
                        (
                            base_fee_per_gas_delta
                            * base_fee_max_change_denominator
                            * parent_gas_target
                        )
                        // parent_base_fee_per_gas
                    )
                    - 1
                )

            assert (
                base_fee_per_gas_calculator(
                    parent_base_fee_per_gas=parent_base_fee_per_gas,
                    parent_gas_used=parent_gas_used,
                    parent_gas_limit=parent_gas_limit,
                )
                == required_base_fee_per_gas
            )

            return parent_gas_used

        return fn
