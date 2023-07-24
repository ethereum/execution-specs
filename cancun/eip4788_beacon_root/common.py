"""
Common constants, classes & functions local to EIP-4788 tests.
"""

from ethereum_test_tools import BeaconRoot, Storage

REF_SPEC_4788_GIT_PATH = "EIPS/eip-4788.md"
REF_SPEC_4788_VERSION = "f0eb6a364aaf5ccb43516fa2c269a54fb881ecfd"

BEACON_ROOT_PRECOMPILE_ADDRESS = 0x0B  # HISTORY_STORE_ADDRESS
BEACON_ROOT_PRECOMPILE_GAS = 4_200  # G_BEACON_ROOT
HISTORICAL_ROOTS_MODULUS = 98_304

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
    beacon_root: bytes,
    timestamp: int,
    valid_call: bool,
    valid_input: bool,
) -> Storage:
    """
    Derives the expected storage for a given beacon root precompile call
    dependent on:
    - success or failure of the call
    - validity of the timestamp input used within the call
    """
    storage: Storage.StorageDictType = dict()
    # beacon root precompile call is successful
    if valid_call:
        storage[0] = 1
        storage[2] = 32
        # timestamp precompile input is valid
        if valid_input:
            storage[1] = beacon_root
        else:
            storage[1] = 0
        storage[3] = storage[1]

    # beacon root precompile call failed
    else:
        storage[0] = 0
        storage[1] = timestamp  # due to failure, input is not overwritten
        storage[2] = 0
        storage[3] = storage[1]

    return storage
