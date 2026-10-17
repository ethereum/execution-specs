"""
EIP-12504 loads and stores.

CALLDATALOAD64, MLOAD64, and MSTORE64 are their twins reduced modulo
2**64: the same 32-byte window at the same offset, the offset read modulo
2**64, the same memory expansion, the same bytes.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Op,
    StateTestFiller,
    Transaction,
)

from .spec import ref_spec_12504

REFERENCE_SPEC_GIT_PATH = ref_spec_12504.git_path
REFERENCE_SPEC_VERSION = ref_spec_12504.version

pytestmark = pytest.mark.valid_from("EIP12504")

TX_GAS_LIMIT = 1_000_000

# The forty bytes 0x00..0x27, as calldata or as memory.
PATTERN = bytes(range(40))
WORD = int.from_bytes(PATTERN[:32], "big")
LOW_EIGHT_OF_WORD = 0x18191A1B1C1D1E1F
NEXT_EIGHT = 0x2021222324252627
GARBAGE_HIGH = 0x10000000000000005  # 2**64 + 5


@pytest.mark.parametrize(
    "offset,expected",
    [
        pytest.param(0, LOW_EIGHT_OF_WORD, id="offset_0"),
        pytest.param(8, NEXT_EIGHT, id="offset_8"),
        pytest.param(16, 0, id="offset_16_past_the_end"),
        pytest.param(2**64, LOW_EIGHT_OF_WORD, id="offset_2_64_reads_as_0"),
    ],
)
def test_calldataload64(
    state_test: StateTestFiller,
    pre: Alloc,
    offset: int,
    expected: int,
) -> None:
    """CALLDATALOAD64 reads the low eight bytes of the calldata word."""
    code = Op.SSTORE(0, Op.CALLDATALOAD64(offset)) + Op.STOP
    contract = pre.deploy_contract(code)
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        gas_limit=TX_GAS_LIMIT,
        data=PATTERN,
    )
    post = {contract: Account(storage={0: expected})}
    state_test(pre=pre, post=post, tx=tx)


def test_mload64_reads_what_mstore_stored(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    After MSTORE of the pattern word at 0, MLOAD64 of 0 is its low eight
    bytes, MLOAD64 of 2**64 reads the same word, and MLOAD64 of 8 is zero
    with memory extended to 40 bytes, which MSIZE rounds to 64.
    """
    code = (
        Op.MSTORE(0, WORD)
        + Op.SSTORE(0, Op.MLOAD64(0))
        + Op.SSTORE(1, Op.MLOAD64(2**64))
        + Op.SSTORE(2, Op.MLOAD64(8))
        + Op.SSTORE(3, Op.MSIZE)
        + Op.STOP
    )
    contract = pre.deploy_contract(code)
    tx = Transaction(
        sender=pre.fund_eoa(), to=contract, gas_limit=TX_GAS_LIMIT
    )
    post = {
        contract: Account(
            storage={
                0: LOW_EIGHT_OF_WORD,
                1: LOW_EIGHT_OF_WORD,
                2: 0,
                3: 64,
            }
        )
    }
    state_test(pre=pre, post=post, tx=tx)


def test_mstore64_stores_a_zero_extended_word(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    MSTORE64 of a value with garbage high bits at 0 leaves the word at 0
    reading as the low 64 bits under MLOAD and MLOAD64 alike; MSTORE64 at 8
    then extends memory to 40 bytes, which MSIZE rounds to 64, and leaves
    bytes 8..31 zero.
    """
    code = (
        Op.MSTORE(0, 2**256 - 1)
        + Op.MSTORE64(0, GARBAGE_HIGH)
        + Op.SSTORE(0, Op.MLOAD(0))
        + Op.SSTORE(1, Op.MLOAD64(0))
        + Op.MSTORE64(8, 2**64 - 1)
        + Op.SSTORE(2, Op.MSIZE)
        + Op.SSTORE(3, Op.MLOAD(8))
        + Op.STOP
    )
    contract = pre.deploy_contract(code)
    tx = Transaction(
        sender=pre.fund_eoa(), to=contract, gas_limit=TX_GAS_LIMIT
    )
    post = {
        contract: Account(
            storage={
                0: 5,
                1: 5,
                2: 64,
                3: 2**64 - 1,
            }
        )
    }
    state_test(pre=pre, post=post, tx=tx)
