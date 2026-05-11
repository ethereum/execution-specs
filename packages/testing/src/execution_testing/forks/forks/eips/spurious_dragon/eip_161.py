"""
EIP-161: State trie clearing (invariant-preserving alternative).

https://eips.ethereum.org/EIPS/eip-161
"""

from execution_testing.vm import OpcodeBase

from ....base_fork import BaseFork, GasCosts


class EIP161(BaseFork):
    """EIP-161 class."""

    @classmethod
    def _calculate_call_gas(
        cls, opcode: OpcodeBase, gas_costs: GasCosts
    ) -> int:
        """
        The call gas cost needs to take the value transfer
        and account new into account.
        """
        base_cost = super(EIP161, cls)._calculate_call_gas(opcode, gas_costs)

        # Additional costs for value transfer, does not apply to STATICCALL
        metadata = opcode.metadata
        if "value_transfer" in metadata:
            if metadata["value_transfer"]:
                base_cost += gas_costs.CALL_VALUE
                if metadata["account_new"]:
                    base_cost += gas_costs.NEW_ACCOUNT
            elif metadata["account_new"]:
                raise ValueError("Account new requires value transfer")

        return base_cost
