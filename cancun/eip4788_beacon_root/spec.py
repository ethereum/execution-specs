"""
Defines EIP-4788 specification constants and functions.
"""
from dataclasses import dataclass

from ethereum_test_tools import Storage


@dataclass(frozen=True)
class ReferenceSpec:
    """
    Defines the reference spec version and git path.
    """

    git_path: str
    version: str


ref_spec_4788 = ReferenceSpec("EIPS/eip-4788.md", "e7608fe8ac8a60934ca874f5aab7d5c1f4ff7782")


# Constants
@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-4788 specifications as defined at
    https://eips.ethereum.org/EIPS/eip-4788#specification
    """

    BEACON_ROOTS_ADDRESS = 0x000F3DF6D732807EF1319FB7B8BB8522D0BEAC02
    BEACON_ROOTS_CALL_GAS = 100_000
    BEACON_ROOTS_DEPLOYER_ADDRESS = 0x0B799C86A49DEEB90402691F1041AA3AF2D3C875
    HISTORY_BUFFER_LENGTH = 8_191
    SYSTEM_ADDRESS = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
    FORK_TIMESTAMP = 15_000  # ShanghaiToCancun timestamp


@dataclass(frozen=True)
class SpecHelpers:
    """
    Helper functions closely related to the EIP-4788 specification.
    """

    def timestamp_index(self, timestamp: int) -> int:
        """
        Derive the timestamp index into the timestamp ring buffer.
        """
        return timestamp % Spec.HISTORY_BUFFER_LENGTH

    def root_index(self, timestamp: int) -> int:
        """
        Derive the root index into the root ring buffer.
        """
        return self.timestamp_index(timestamp) + Spec.HISTORY_BUFFER_LENGTH

    @staticmethod
    def expected_storage(
        *,
        beacon_root: bytes,
        valid_call: bool,
        valid_input: bool,
    ) -> Storage:
        """
        Derives the expected storage for a given beacon root contract call
        dependent on:
        - success or failure of the call
        - validity of the timestamp input used within the call
        """
        # By default assume the call is unsuccessful and all keys are zero
        storage = Storage({k: 0 for k in range(4)})
        if valid_call and valid_input:
            # beacon root contract call is successful
            storage[0] = 1
            storage[1] = beacon_root
            storage[2] = 32
            storage[3] = beacon_root

        return storage
