"""
Common constants, classes & functions local to EIP-4788 tests.
"""

from ethereum_test_tools import BeaconRoot, Storage

REF_SPEC_4788_GIT_PATH = "EIPS/eip-4788.md"
REF_SPEC_4788_VERSION = "f0eb6a364aaf5ccb43516fa2c269a54fb881ecfd"

BEACON_ROOT_CONTRACT_ADDRESS = 0x0B  # HISTORY_STORE_ADDRESS
BEACON_ROOT_CONTRACT_CALL_GAS = 100_000
HISTORICAL_ROOTS_MODULUS = 98_304
SYSTEM_ADDRESS = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE

FORK_TIMESTAMP = 15_000  # ShanghaiToCancun timestamp
DEFAULT_BEACON_ROOT_HASH = BeaconRoot


def timestamp_index(timestamp: int) -> int:
    """
    Derive the timestamp index into the timestamp ring buffer.
    """
    return timestamp % HISTORICAL_ROOTS_MODULUS


def root_index(timestamp: int) -> int:
    """
    Derive the root index into the root ring buffer.
    """
    return timestamp_index(timestamp) + HISTORICAL_ROOTS_MODULUS


def expected_storage(
    *,
    beacon_root: bytes,
    valid_call: bool,
    valid_input: bool,
) -> Storage:
    """
    Derives the expected storage for a given beacon root precompile call
    dependent on:
    - success or failure of the call
    - validity of the timestamp input used within the call
    """
    # By default assume the call is unsuccessful and all keys are zero
    storage = Storage({k: 0 for k in range(4)})
    if valid_call and valid_input:
        # beacon root precompile call is successful
        storage[0] = 1
        storage[1] = beacon_root
        storage[2] = 32
        storage[3] = beacon_root

    return storage
