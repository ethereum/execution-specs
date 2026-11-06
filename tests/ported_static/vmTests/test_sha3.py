"""
Test SHA3 over zeroed memory ranges.

Ported from:
state_tests/VMTests/vmTests/sha3Filler.yml
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Op,
    StateTestFiller,
    Transaction,
    keccak256,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

SENTINEL = 0x0BAD
MAX_UINT = 2**256 - 1


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmTests/sha3Filler.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "offset, size, out_of_gas",
    [
        pytest.param(0, 0, False, id="sha3_nodata"),
        pytest.param(4, 5, False, id="sha3_five_0s"),
        pytest.param(10, 10, False, id="sha3_ten_0s"),
        pytest.param(1000, 0xFFFFF, False, id="sha3_0xFFFFF_0s"),
        pytest.param(0xFFFFFFFFF, 100, True, id="sha3_highmem"),
        pytest.param(10000, 0xFFFFFFFFF, True, id="sha3_huge_buffer"),
        pytest.param(MAX_UINT, MAX_UINT, True, id="sha3_neg1_neg1"),
        pytest.param(MAX_UINT, 2, True, id="sha3_neg1_2"),
        pytest.param(0x1000000, 2, True, id="sha3_0x1000000_2"),
        pytest.param(960, 1, False, id="sha3_960_1"),
        pytest.param(992, 1, False, id="sha3_992_1"),
        pytest.param(1024, 1, False, id="sha3_1024_1"),
        pytest.param(1984, 1, False, id="sha3_1984_1"),
        pytest.param(2016, 1, False, id="sha3_2016_1"),
        pytest.param(2016, 32, False, id="sha3_2016_32"),
        pytest.param(2048, 1, False, id="sha3_2048_1"),
        pytest.param(1024, 0, False, id="sha3_1024_0"),
    ],
)
def test_sha3(
    state_test: StateTestFiller,
    pre: Alloc,
    offset: int,
    size: int,
    out_of_gas: bool,
) -> None:
    """Store SHA3 of a zeroed memory range, or keep the sentinel on OOG."""
    contract = pre.deploy_contract(
        code=Op.SSTORE(0, Op.SHA3(offset=offset, size=size)) + Op.STOP,
        storage={0: SENTINEL},
    )
    tx = Transaction(sender=pre.fund_eoa(), to=contract)
    expected = SENTINEL if out_of_gas else keccak256(bytes(size))
    post = {contract: Account(storage={0: expected})}
    state_test(pre=pre, post=post, tx=tx)
