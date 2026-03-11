"""Shared pytest definitions for EIP-8025 witness tests."""

import pytest
from execution_testing import Bytes, Fork

# System contracts called every block (addresses as ints).
SYSTEM_CONTRACT_ADDRS = [
    0x000F3DF6D732807EF1319FB7B8BB8522D0BEAC02,  # beacon roots
    0x00000961EF480EB55E80D19AD83579A64C007002,  # withdrawal req
    0x0000BBDDC7CE488642FB579F8B00F3A590007251,  # consolidation req
    0x0000F90827F1C53A10CB7A02335B175320002935,  # history storage
]


@pytest.fixture
def system_codes(fork: Fork) -> list[Bytes]:
    """Collect system contract bytecodes from the fork pre-alloc."""
    alloc = fork.pre_allocation_blockchain()
    codes: list[Bytes] = []
    for addr in SYSTEM_CONTRACT_ADDRS:
        code = alloc[addr]["code"]
        if isinstance(code, str):
            code = bytes.fromhex(code.removeprefix("0x"))
        codes.append(Bytes(code))
    return codes
