"""Helpers for testing EIP-7981."""

from typing import List

from execution_testing import AccessList


def calculate_access_list_tokens(access_list: List[AccessList]) -> int:
    """
    Calculate the number of tokens in an access list.

    According to EIP-7981, tokens are calculated as:
    tokens = zero_bytes + nonzero_bytes * 4

    Where bytes come from:
    - 20 bytes per address
    - 32 bytes per storage key
    """
    zero_bytes = 0
    nonzero_bytes = 0

    for access in access_list:
        # Count bytes in address (20 bytes)
        for byte in access.address:
            if byte == 0:
                zero_bytes += 1
            else:
                nonzero_bytes += 1

        # Count bytes in each storage key (32 bytes each)
        for slot in access.storage_keys:
            for byte in slot:
                if byte == 0:
                    zero_bytes += 1
                else:
                    nonzero_bytes += 1

    return zero_bytes + nonzero_bytes * 4
