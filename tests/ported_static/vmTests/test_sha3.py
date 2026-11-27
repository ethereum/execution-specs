"""
Test SHA3 over memory ranges.

The original tests were written by Ori Pomerantz.

Ported from:
state_tests/VMTests/vmTests/sha3Filler.yml

@manually-enhanced: Do not overwrite. Built from readable parameters.

The contract fills the first `PATTERN_WORDS` memory words with distinct
values before hashing, so the hash depends on where the range starts and
not only on its size, and the expected hash comes from a model of that
memory. The offset and size reach the stack from PUSH data (static) or
calldata (dynamic). `test_sha3` hashes ranges the transaction can pay for,
including single bytes around word boundaries and a range running far
past the pattern into zeros. `test_sha3_out_of_gas` hashes ranges whose
memory expansion cannot be paid for, so the frame reverts and the
sentinel stays.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Environment,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
    keccak256,
)

from tests.ported_static.helpers import Memory, Operands

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

pytestmark = [
    pytest.mark.ported_from(
        ["state_tests/VMTests/vmTests/sha3Filler.yml"],
    ),
    pytest.mark.valid_from("Frontier"),
    pytest.mark.parametrize("operand_source", list(Operands.Source), ids=str),
]

RESULT_SLOT = 0
SENTINEL = 0x0BAD
MAX_UINT = 2**256 - 1
# Covers every range of `test_sha3` except the one running past it.
PATTERN_WORDS = 0x41


def pattern_word(index: int) -> int:
    """Return the distinct value stored in memory word `index`."""
    return int.from_bytes(keccak256(index.to_bytes(32, "big")))


@pytest.fixture
def operands(operand_source: Operands.Source) -> Operands:
    """Return the operand supplier for the parametrized source."""
    return Operands(operand_source)


@pytest.fixture
def memory() -> Memory:
    """Return a memory model holding the pattern the contract stores."""
    memory = Memory()
    for index in range(PATTERN_WORDS):
        memory.store(index * 32, pattern_word(index))
    return memory


@pytest.fixture
def fill_memory() -> Bytecode:
    """Return the code writing the pattern to memory."""
    code = Bytecode()
    for index in range(PATTERN_WORDS):
        code += Op.MSTORE(index * 32, pattern_word(index))
    return code


@pytest.mark.parametrize(
    "offset, size",
    [
        pytest.param(0, 0, id="empty"),
        pytest.param(4, 5, id="five_bytes"),
        pytest.param(10, 10, id="ten_bytes"),
        # Runs far past the pattern, into memory that reads as zero.
        pytest.param(1000, 0xFFFFF, id="offset_1000_size_0xfffff"),
        # Single bytes at the first byte of words 30, 31, 32, 62, 63 and
        # 64, around memory sizes of 1024 and 2048 bytes.
        pytest.param(960, 1, id="offset_960_size_1"),
        pytest.param(992, 1, id="offset_992_size_1"),
        pytest.param(1024, 1, id="offset_1024_size_1"),
        pytest.param(1984, 1, id="offset_1984_size_1"),
        pytest.param(2016, 1, id="offset_2016_size_1"),
        pytest.param(2016, 32, id="offset_2016_size_32"),
        pytest.param(2048, 1, id="offset_2048_size_1"),
        pytest.param(1024, 0, id="offset_1024_size_0"),
    ],
)
def test_sha3(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    offset: int,
    size: int,
    operands: Operands,
    memory: Memory,
    fill_memory: Bytecode,
) -> None:
    """Store the SHA3 of a range of the patterned memory."""
    code = (
        fill_memory
        + Op.SSTORE(
            RESULT_SLOT,
            Op.SHA3(offset=operands(offset), size=operands(size)),
        )
        + Op.STOP
    )
    contract = pre.deploy_contract(code=code, storage={RESULT_SLOT: SENTINEL})
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        data=operands.calldata,
        protected=fork.supports_protected_txs(),
    )
    expected = keccak256(memory.read(offset, size))
    post = {contract: Account(storage={RESULT_SLOT: expected})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "offset, size",
    [
        pytest.param(0xFFFFFFFFF, 100, id="offset_0xfffffffff_size_100"),
        pytest.param(10000, 0xFFFFFFFFF, id="offset_10000_size_0xfffffffff"),
        pytest.param(MAX_UINT, MAX_UINT, id="offset_max_size_max"),
        pytest.param(MAX_UINT, 2, id="offset_max_size_2"),
        pytest.param(0x1000000, 2, id="offset_0x1000000_size_2"),
    ],
)
def test_sha3_out_of_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    offset: int,
    size: int,
    operands: Operands,
    fill_memory: Bytecode,
) -> None:
    """Revert the frame when SHA3 cannot pay for its memory expansion."""
    sha3 = Op.SHA3(
        offset=operands(offset),
        size=operands(size),
        data_size=size,
        new_memory_size=offset + size,
    )
    code = fill_memory + Op.SSTORE(RESULT_SLOT, sha3) + Op.STOP
    contract = pre.deploy_contract(code=code, storage={RESULT_SLOT: SENTINEL})
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        data=operands.calldata,
        protected=fork.supports_protected_txs(),
    )
    # No transaction gets more gas than the block's gas limit.
    assert sha3.gas_cost(fork) > Environment().gas_limit
    post = {contract: Account(storage={RESULT_SLOT: SENTINEL})}
    state_test(pre=pre, post=post, tx=tx)
