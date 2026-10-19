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
        Couple the new account charge to a value transfer, per the dead
        account rules. The charge itself applies from Frontier.
        """
        metadata = opcode.metadata
        if "value_transfer" in metadata:
            if metadata["account_new"] and not metadata["value_transfer"]:
                raise ValueError("Account new requires value transfer")

        return super(EIP161, cls)._calculate_call_gas(opcode, gas_costs)
