"""
EIP-7997: Deterministic Factory Predeploy.

Predeploy a minimal `CREATE2` factory at address `0x12` so deterministic
deployments are available across chains without bootstrapping transactions.

https://eips.ethereum.org/EIPS/eip-7997
"""

from typing import Mapping

from execution_testing.base_types import Address

from ....base_fork import BaseFork

DETERMINISTIC_FACTORY_PREDEPLOY_ADDRESS = 0x12
DETERMINISTIC_FACTORY_PREDEPLOY_BYTECODE = bytes.fromhex(
    "60203610602f57"
    "60003560203603806020600037600034f5"
    "806026573d600060003e3d6000fd"
    "5b60005260206000f3"
    "5b60006000fd"
)


class EIP7997(BaseFork):
    """EIP-7997 class."""

    @classmethod
    def deterministic_factory_predeploy_address(cls) -> Address | None:
        """Return the EIP-7997 deterministic factory predeploy address."""
        return Address(
            DETERMINISTIC_FACTORY_PREDEPLOY_ADDRESS,
            label="DETERMINISTIC_FACTORY_PREDEPLOY_ADDRESS",
        )

    @classmethod
    def pre_allocation(cls) -> Mapping:
        """Pre-allocate the deterministic factory predeploy."""
        return {
            DETERMINISTIC_FACTORY_PREDEPLOY_ADDRESS: {
                "nonce": 1,
                "code": DETERMINISTIC_FACTORY_PREDEPLOY_BYTECODE,
            }
        } | super(EIP7997, cls).pre_allocation()  # type: ignore

    @classmethod
    def pre_allocation_blockchain(cls) -> Mapping:
        """Pre-allocate the deterministic factory predeploy."""
        return {
            DETERMINISTIC_FACTORY_PREDEPLOY_ADDRESS: {
                "nonce": 1,
                "code": DETERMINISTIC_FACTORY_PREDEPLOY_BYTECODE,
            }
        } | super(EIP7997, cls).pre_allocation_blockchain()  # type: ignore
