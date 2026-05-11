"""
EIP-7251: Increase the MAX_EFFECTIVE_BALANCE.

Allow validators to consolidate via execution layer requests.

https://eips.ethereum.org/EIPS/eip-7251
"""

from os.path import realpath
from pathlib import Path
from typing import List, Mapping

from execution_testing.base_types import Address

from ....base_fork import BaseFork

BYTECODE_FILE = (
    Path(realpath(__file__)).parent / "contracts" / "consolidation_request.bin"
)
CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS = (
    0x0000BBDDC7CE488642FB579F8B00F3A590007251
)
CONSOLIDATION_REQUEST_PREDEPLOY_BYTECODE = BYTECODE_FILE.read_bytes()


class EIP7251(BaseFork):
    """EIP-7251 class."""

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
        } | super(EIP7251, cls).pre_allocation_blockchain()  # type: ignore
