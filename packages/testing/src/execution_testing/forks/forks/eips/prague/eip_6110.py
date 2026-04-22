"""
EIP-6110: Supply validator deposits on chain.

Provides validator deposits as a list of deposit operations added to the
Execution Layer block.

https://eips.ethereum.org/EIPS/eip-6110
"""

from hashlib import sha256
from os.path import realpath
from pathlib import Path
from typing import List, Mapping

from execution_testing.base_types import Address

from ....base_fork import BaseFork

BYTECODE_FILE = (
    Path(realpath(__file__)).parent / "contracts" / "deposit_contract.bin"
)
DEPOSIT_CONTRACT_ADDRESS = 0x00000000219AB540356CBB839CBE05303D7705FA
DEPOSIT_CONTRACT_BYTECODE = BYTECODE_FILE.read_bytes()


class EIP6110(BaseFork):
    """EIP-6110 class."""

    @classmethod
    def system_contracts(cls) -> List[Address]:
        """Add the beacon chain deposit contract."""
        return [
            Address(
                DEPOSIT_CONTRACT_ADDRESS,
                label="DEPOSIT_CONTRACT_ADDRESS",
            ),
        ] + super(EIP6110, cls).system_contracts()

    @classmethod
    def pre_allocation_blockchain(cls) -> Mapping:
        """Pre-allocate the beacon chain deposit contract."""
        deposit_contract_tree_depth = 32
        storage = {}
        next_hash = sha256(b"\x00" * 64).digest()
        for i in range(
            deposit_contract_tree_depth + 2,
            deposit_contract_tree_depth * 2 + 1,
        ):
            storage[i] = next_hash
            next_hash = sha256(next_hash + next_hash).digest()

        return {
            DEPOSIT_CONTRACT_ADDRESS: {
                "nonce": 1,
                "code": DEPOSIT_CONTRACT_BYTECODE,
                "storage": storage,
            }
        } | super(EIP6110, cls).pre_allocation_blockchain()  # type: ignore
