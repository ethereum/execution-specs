"""
EIP-2935: Serve historical block hashes from state.

Store and serve last 8191 block hashes as storage slots of a system contract
to allow for stateless execution.

https://eips.ethereum.org/EIPS/eip-2935
"""

from typing import List, Mapping

from execution_testing.base_types import Address

from ....base_fork import BaseFork, SystemCallPhase
from ....bytecode import load_contract_bytecode

HISTORY_STORAGE_ADDRESS = 0x0000F90827F1C53A10CB7A02335B175320002935
HISTORY_STORAGE_BYTECODE = load_contract_bytecode(
    __name__, "history_contract.bin"
)


class EIP2935(BaseFork):
    """EIP-2935 class."""

    @classmethod
    def empty_block_bal_item_count(cls) -> int:
        """Add block-level access list elements for an empty block."""
        # History contract: 1 address + 1 write = 2
        return super(EIP2935, cls).empty_block_bal_item_count() + 2

    @classmethod
    def system_contracts(cls) -> List[Address]:
        """Add the history storage contract."""
        return [
            Address(
                HISTORY_STORAGE_ADDRESS,
                label="HISTORY_STORAGE_ADDRESS",
            ),
        ] + super(EIP2935, cls).system_contracts()

    @classmethod
    def system_contract_call_phases(cls) -> Mapping[Address, SystemCallPhase]:
        """Call the history storage contract before the transactions."""
        return {
            Address(
                HISTORY_STORAGE_ADDRESS, label="HISTORY_STORAGE_ADDRESS"
            ): SystemCallPhase.BEFORE_TRANSACTIONS,
            **super(EIP2935, cls).system_contract_call_phases(),
        }

    @classmethod
    def pre_allocation_blockchain(cls) -> Mapping:
        """Pre-allocate the history storage contract."""
        return {
            HISTORY_STORAGE_ADDRESS: {
                "nonce": 1,
                "code": HISTORY_STORAGE_BYTECODE,
            },
            **super(EIP2935, cls).pre_allocation_blockchain(),
        }
