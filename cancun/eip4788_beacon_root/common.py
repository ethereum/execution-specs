"""
Common constants, classes & functions local to EIP-4788 tests.
"""

from ethereum_test_tools import Storage

REF_SPEC_4788_GIT_PATH = "EIPS/eip-4788.md"
REF_SPEC_4788_VERSION = "e7608fe8ac8a60934ca874f5aab7d5c1f4ff7782"

BEACON_ROOT_CONTRACT_ADDRESS = 0xBEAC00DDB15F3B6D645C48263DC93862413A222D
BEACON_ROOT_CONTRACT_CALL_GAS = 100_000
HISTORY_BUFFER_LENGTH = 98_304
SYSTEM_ADDRESS = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE

FORK_TIMESTAMP = 15_000  # ShanghaiToCancun timestamp


def timestamp_index(timestamp: int) -> int:
    """
    Derive the timestamp index into the timestamp ring buffer.
    """
    return timestamp % HISTORY_BUFFER_LENGTH


def root_index(timestamp: int) -> int:
    """
    Derive the root index into the root ring buffer.
    """
    return timestamp_index(timestamp) + HISTORY_BUFFER_LENGTH


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
