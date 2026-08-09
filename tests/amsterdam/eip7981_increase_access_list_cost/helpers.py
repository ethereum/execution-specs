"""Helpers for testing EIP-7981."""

from typing import List

from execution_testing import AccessList


def calculate_access_list_floor_tokens(access_list: List[AccessList]) -> int:
    """
    Calculate the number of floor tokens in an access list.

    According to EIP-7981 (aligned with EIP-7976), floor tokens are
    calculated from the raw access list byte length:
    floor_tokens = total_bytes * 4

    Where bytes come from:
    - 20 bytes per address
    - 32 bytes per storage key
    """
    total_bytes = 0

    for access in access_list:
        # Count bytes in address (20 bytes)
        total_bytes += len(access.address)

        # Count bytes in each storage key (32 bytes each)
        for slot in access.storage_keys:
            total_bytes += len(slot)

    return total_bytes * 4
