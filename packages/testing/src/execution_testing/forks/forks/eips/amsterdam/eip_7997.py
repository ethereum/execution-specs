"""
EIP-7997: Deterministic Factory Predeploy.

Predeploy the Arachnid `CREATE2` factory at
`0x4e59b44847b379578588920ca78fbf26c0b4956c` so deterministic
deployments are available across chains without bootstrapping
transactions.

https://eips.ethereum.org/EIPS/eip-7997
"""

from typing import Mapping

from execution_testing.base_types import Address

from ....base_fork import BaseFork

DETERMINISTIC_FACTORY_PREDEPLOY_ADDRESS = (
    0x4E59B44847B379578588920CA78FBF26C0B4956C
)
DETERMINISTIC_FACTORY_PREDEPLOY_BYTECODE = bytes.fromhex(
    "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0"
    "3601600081602082378035828234f58015156039578182fd"
    "5b8082525050506014600cf3"
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
