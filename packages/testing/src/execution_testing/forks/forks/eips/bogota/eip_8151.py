"""
EIP-8151: Account Code Restricted ecRecover.

The ecrecover precompile reads the recovered account and withholds the
address when the account holds code other than a delegation designation.
Reading the account is priced as an account access plus a code read.

https://eips.ethereum.org/EIPS/eip-8151
"""

from ....base_fork import BaseFork


class EIP8151(BaseFork):
    """EIP-8151 class."""

    @classmethod
    def ecrecover_gas(cls, *, recovered: bool, address_warm: bool) -> int:
        """
        A recovered address is charged a warm or cold account access and a
        code read on top of the base fee; a failed recovery reads no account.
        """
        base_gas = super(EIP8151, cls).ecrecover_gas(
            recovered=recovered, address_warm=address_warm
        )
        if not recovered:
            return base_gas
        gas_costs = cls.gas_costs()
        if address_warm:
            access_gas = gas_costs.WARM_ACCESS
        else:
            access_gas = gas_costs.COLD_ACCOUNT_ACCESS
        code_read_gas = gas_costs.WARM_ACCESS
        return base_gas + access_gas + code_read_gas
