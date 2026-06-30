"""
EIP-7251: Increase the MAX_EFFECTIVE_BALANCE.

Allow validators to consolidate via execution layer requests.

https://eips.ethereum.org/EIPS/eip-7251
"""

from typing import List, Mapping

from execution_testing.base_types import Address

from ....base_fork import BaseFork
from ....bytecode import load_contract_bytecode

CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS = (
    0x0000BBDDC7CE488642FB579F8B00F3A590007251
)
CONSOLIDATION_REQUEST_PREDEPLOY_BYTECODE = load_contract_bytecode(
    __name__, "consolidation_request.bin"
)


class EIP7251(BaseFork):
    """EIP-7251 class."""

    @classmethod
    def empty_block_bal_item_count(cls) -> int:
        """Add block-level access list elements for an empty block."""
        # Consolidations contract: 1 address + 4 reads = 5
        return super(EIP7251, cls).empty_block_bal_item_count() + 5

    @classmethod
    def system_contracts(cls) -> List[Address]:
        """Add the consolidation request predeploy contract."""
        return [
            Address(
                CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS,
                label="CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS",
            ),
        ] + super(EIP7251, cls).system_contracts()

    @classmethod
    def pre_allocation_blockchain(cls) -> Mapping:
        """Pre-allocate the consolidation request contract."""
        return {
            CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS: {
                "nonce": 1,
                "code": CONSOLIDATION_REQUEST_PREDEPLOY_BYTECODE,
            },
            **super(EIP7251, cls).pre_allocation_blockchain(),
        }
