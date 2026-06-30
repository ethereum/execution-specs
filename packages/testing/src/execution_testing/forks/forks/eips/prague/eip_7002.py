"""
EIP-7002: Execution layer triggerable withdrawals.

Allow validators to trigger exits and partial withdrawals via their execution
layer (0x01) withdrawal credentials.

https://eips.ethereum.org/EIPS/eip-7002
"""

from typing import List, Mapping

from execution_testing.base_types import Address

from ....base_fork import BaseFork
from ....bytecode import load_contract_bytecode

WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS = (
    0x00000961EF480EB55E80D19AD83579A64C007002
)
WITHDRAWAL_REQUEST_PREDEPLOY_BYTECODE = load_contract_bytecode(
    __name__, "withdrawal_request.bin"
)


class EIP7002(BaseFork):
    """EIP-7002 class."""

    @classmethod
    def empty_block_bal_item_count(cls) -> int:
        """Add block-level access list elements for an empty block."""
        # Withdrawals contract: 1 address + 4 reads = 5
        return super(EIP7002, cls).empty_block_bal_item_count() + 5

    @classmethod
    def system_contracts(cls) -> List[Address]:
        """Add the withdrawal request predeploy contract."""
        return [
            Address(
                WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS,
                label="WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS",
            ),
        ] + super(EIP7002, cls).system_contracts()

    @classmethod
    def pre_allocation_blockchain(cls) -> Mapping:
        """Pre-allocate the withdrawal request contract."""
        return {
            WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS: {
                "nonce": 1,
                "code": WITHDRAWAL_REQUEST_PREDEPLOY_BYTECODE,
            },
            **super(EIP7002, cls).pre_allocation_blockchain(),
        }
