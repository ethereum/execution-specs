"""
EIP-8282: Builder Execution Requests.

Predeploy builder deposit and exit request contracts for EIP-7732 builders on
the EIP-7685 request bus.

https://eips.ethereum.org/EIPS/eip-8282
"""

from typing import List, Mapping

from execution_testing.base_types import Address

from ....base_fork import BaseFork
from ....bytecode import load_contract_bytecode

BUILDER_DEPOSIT_CONTRACT_ADDRESS = 0x0000BFF46984E3725691FA540A8C7589300D8282
BUILDER_DEPOSIT_CONTRACT_BYTECODE = load_contract_bytecode(
    __name__, "builder_deposit_request.bin"
)

BUILDER_EXIT_CONTRACT_ADDRESS = 0x000064D678505AD48F8CCB093BC65613800E8282
BUILDER_EXIT_CONTRACT_BYTECODE = load_contract_bytecode(
    __name__, "builder_exit_request.bin"
)


class EIP8282(BaseFork):
    """EIP-8282 class."""

    @classmethod
    def max_request_type(cls) -> int:
        """
        Two request types are introduced: builder deposit requests (0x03)
        and builder exit requests (0x04).
        """
        return super(EIP8282, cls).max_request_type() + 2

    @classmethod
    def empty_block_bal_item_count(cls) -> int:
        """Add block-level access list elements for an empty block."""
        # Builder contracts: 2 addresses + 8 reads = 10
        return super(EIP8282, cls).empty_block_bal_item_count() + 10

    @classmethod
    def system_contracts(cls) -> List[Address]:
        """Add the builder deposit and exit request predeploy contracts."""
        return [
            Address(
                BUILDER_DEPOSIT_CONTRACT_ADDRESS,
                label="BUILDER_DEPOSIT_CONTRACT_ADDRESS",
            ),
            Address(
                BUILDER_EXIT_CONTRACT_ADDRESS,
                label="BUILDER_EXIT_CONTRACT_ADDRESS",
            ),
        ] + super(EIP8282, cls).system_contracts()

    @classmethod
    def pre_allocation_blockchain(cls) -> Mapping:
        """Pre-allocate the builder deposit and exit request contracts."""
        return {
            BUILDER_DEPOSIT_CONTRACT_ADDRESS: {
                "nonce": 1,
                "code": BUILDER_DEPOSIT_CONTRACT_BYTECODE,
            },
            BUILDER_EXIT_CONTRACT_ADDRESS: {
                "nonce": 1,
                "code": BUILDER_EXIT_CONTRACT_BYTECODE,
            },
            **super(EIP8282, cls).pre_allocation_blockchain(),
        }
