"""
EIP-4788: Beacon block root in the EVM.

Expose beacon chain roots in the EVM.

https://eips.ethereum.org/EIPS/eip-4788
"""

from typing import List, Mapping

from execution_testing.base_types import Address

from ....base_fork import BaseFork, SystemCallPhase

BEACON_ROOTS_ADDRESS = 0x000F3DF6D732807EF1319FB7B8BB8522D0BEAC02


class EIP4788(BaseFork):
    """EIP-4788 class."""

    @classmethod
    def empty_block_bal_item_count(cls) -> int:
        """Add block-level access list elements for an empty block."""
        # Beacon roots contract: 1 address + 1 write + 1 read = 3
        return super(EIP4788, cls).empty_block_bal_item_count() + 3

    @classmethod
    def header_beacon_root_required(cls) -> bool:
        """Parent beacon block root is required."""
        return True

    @classmethod
    def system_call_gas_limit(cls) -> int:
        """Gas budget for the system-call mechanism (30M)."""
        return 30_000_000

    @classmethod
    def system_contracts(cls) -> List[Address]:
        """Add the beacon roots system contract."""
        return [Address(BEACON_ROOTS_ADDRESS, label="BEACON_ROOTS_ADDRESS")]

    @classmethod
    def system_contract_call_phases(cls) -> Mapping[Address, SystemCallPhase]:
        """Call the beacon roots contract before the transactions."""
        return {
            Address(
                BEACON_ROOTS_ADDRESS, label="BEACON_ROOTS_ADDRESS"
            ): SystemCallPhase.BEFORE_TRANSACTIONS,
            **super(EIP4788, cls).system_contract_call_phases(),
        }

    @classmethod
    def pre_allocation_blockchain(cls) -> Mapping:
        """Pre-allocate the beacon root contract."""
        return {
            BEACON_ROOTS_ADDRESS: {
                "nonce": 1,
                "code": "0x3373fffffffffffffffffffffffffffffffffffffffe14604d"
                "57602036146024575f5ffd5b5f35801560495762001fff810690"
                "815414603c575f5ffd5b62001fff01545f5260205ff35b5f5ffd"
                "5b62001fff42064281555f359062001fff015500",
            },
            **super(EIP4788, cls).pre_allocation_blockchain(),
        }

    @classmethod
    def engine_new_payload_beacon_root(cls) -> bool:
        """Payloads must have a parent beacon block root."""
        return True
