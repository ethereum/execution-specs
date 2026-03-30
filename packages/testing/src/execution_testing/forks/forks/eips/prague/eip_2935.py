"""
EIP-2935: Serve historical block hashes from state.

Store and serve last 8191 block hashes as storage slots of a system contract
to allow for stateless execution.

https://eips.ethereum.org/EIPS/eip-2935
"""

from os.path import realpath
from pathlib import Path
from typing import List, Mapping

from execution_testing.base_types import Address

from ....base_fork import BaseFork

BYTECODE_FILE = (
    Path(realpath(__file__)).parent / "contracts" / "history_contract.bin"
)
HISTORY_STORAGE_ADDRESS = 0x0000F90827F1C53A10CB7A02335B175320002935
HISTORY_STORAGE_BYTECODE = BYTECODE_FILE.read_bytes()


class EIP2935(BaseFork):
    """EIP-2935 class."""

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
    def pre_allocation_blockchain(cls) -> Mapping:
        """Pre-allocate the history storage contract."""
        return {
            HISTORY_STORAGE_ADDRESS: {
                "nonce": 1,
                "code": HISTORY_STORAGE_BYTECODE,
            }
        } | super(EIP2935, cls).pre_allocation_blockchain()  # type: ignore
