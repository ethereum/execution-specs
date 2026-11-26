"""
Test MLOAD, MSTORE, MSTORE8 and MSIZE.

The original tests were written by Ori Pomerantz.

Ported from:
state_tests/VMTests/vmIOandFlowOperations/mloadFiller.yml
state_tests/VMTests/vmIOandFlowOperations/mstoreFiller.yml
state_tests/VMTests/vmIOandFlowOperations/mstore8Filler.yml
state_tests/VMTests/vmIOandFlowOperations/msizeFiller.yml

@manually-enhanced: Do not overwrite. Built from readable parameters.

Every test reads its offsets and values from PUSH data (static) or
calldata (dynamic), and derives the expected storage from a byte-level
model of memory. `test_mstore` and `test_mstore8` write and read back a
word, `test_msize` records MSIZE after each write, and
`test_mload_out_of_gas` reads at offsets whose memory expansion the
transaction cannot pay for, next to an in-bounds read it can.
"""

from typing import NamedTuple

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op, Opcode

from tests.ported_static.helpers import Memory, Operands

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

pytestmark = [
    pytest.mark.ported_from(
        [
            "state_tests/VMTests/vmIOandFlowOperations/mloadFiller.yml",
            "state_tests/VMTests/vmIOandFlowOperations/mstoreFiller.yml",
            "state_tests/VMTests/vmIOandFlowOperations/mstore8Filler.yml",
            "state_tests/VMTests/vmIOandFlowOperations/msizeFiller.yml",
        ],
    ),
    pytest.mark.valid_from("Frontier"),
    pytest.mark.parametrize("operand_source", list(Operands.Source), ids=str),
]

RESULT_SLOT = 0

SENTINEL = 0x0BAD
MAX_UINT = 2**256 - 1
WORD_PATTERN = 0x111122223333444455556666777788889999AAAABBBBCCCCDDDDEEEEFFFF
BYTE_PATTERN = 0x112233445566778899AABBCCDDEEFF
# Far enough to exercise a large expansion, yet affordable under the
# transaction gas limit cap.
FAR_OFFSET = 0x200000


class Write(NamedTuple):
    """One memory write, by `Op.MSTORE` or `Op.MSTORE8`."""

    op: Opcode
    offset: int
    value: int

    def apply(self, memory: Memory) -> None:
        """Apply this write to the `memory` model."""
        if self.op == Op.MSTORE:
            memory.store(self.offset, self.value)
        elif self.op == Op.MSTORE8:
            memory.store8(self.offset, self.value)
        else:
            raise ValueError(f"Unknown store op: {self.op}")

    def code(self, operands: Operands) -> Bytecode:
        """Return the instruction performing this write."""
        return self.op(
            offset=operands(self.offset), value=operands(self.value)
        )


@pytest.fixture
def operands(operand_source: Operands.Source) -> Operands:
    """Return the operand supplier for the parametrized source."""
    return Operands(operand_source)


@pytest.fixture
def memory() -> Memory:
    """Return an empty memory model."""
    return Memory()


@pytest.mark.parametrize(
    "offset, value, load_offset",
    [
        pytest.param(0, WORD_PATTERN, 0, id="aligned"),
        pytest.param(1, MAX_UINT, 1, id="unaligned_all_ones"),
        pytest.param(1, 1, 1, id="unaligned_one"),
        # A word stored at offset 1 ends one byte past the word at 0.
        pytest.param(1, 0xFF, 0, id="low_byte_past_loaded_word"),
        pytest.param(1, 0xFF00, 0, id="second_byte_ends_loaded_word"),
    ],
)
def test_mstore(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    offset: int,
    value: int,
    load_offset: int,
    operands: Operands,
    memory: Memory,
) -> None:
    """Verify the word MLOAD reads back after an MSTORE."""
    write = Write(Op.MSTORE, offset, value)
    write.apply(memory)
    code = (
        write.code(operands)
        + Op.SSTORE(RESULT_SLOT, Op.MLOAD(offset=operands(load_offset)))
        + Op.STOP
    )

    contract = pre.deploy_contract(code=code, storage={RESULT_SLOT: SENTINEL})
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        data=operands.calldata,
        protected=fork.supports_protected_txs(),
    )
    post = {contract: Account(storage={RESULT_SLOT: memory.load(load_offset)})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "writes, load_offset",
    [
        pytest.param(
            [Write(Op.MSTORE8, 1, BYTE_PATTERN)], 1, id="low_byte_of_pattern"
        ),
        pytest.param(
            [Write(Op.MSTORE8, 1, MAX_UINT)], 1, id="low_byte_of_all_ones"
        ),
        pytest.param(
            [Write(Op.MSTORE8, 1, 0xFF), Write(Op.MSTORE8, 2, 0xEE)],
            0,
            id="two_bytes",
        ),
    ],
)
def test_mstore8(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    writes: list[Write],
    load_offset: int,
    operands: Operands,
    memory: Memory,
) -> None:
    """Verify MSTORE8 writes only the low byte of its value."""
    code = Bytecode()
    for write in writes:
        code += write.code(operands)
        write.apply(memory)
    code += Op.SSTORE(RESULT_SLOT, Op.MLOAD(offset=operands(load_offset)))
    code += Op.STOP

    contract = pre.deploy_contract(code=code, storage={RESULT_SLOT: SENTINEL})
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        data=operands.calldata,
        protected=fork.supports_protected_txs(),
    )
    post = {contract: Account(storage={RESULT_SLOT: memory.load(load_offset)})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "writes",
    [
        pytest.param(
            [Write(Op.MSTORE, 0, 0xFF)],
            id="one_word",
        ),
        pytest.param(
            [
                Write(Op.MSTORE, 0, 0xFFFFFFFFFF),
                Write(Op.MSTORE, 0x20, 0xEEEE),
            ],
            id="adjacent_words",
        ),
        pytest.param(
            [
                Write(Op.MSTORE, 0, 0xFFFFFFFFFF),
                # Covers 0x5A-0x79, rounded up to four words.
                Write(Op.MSTORE, 0x5A, 0xEEEE),
            ],
            id="unaligned_word",
        ),
        pytest.param(
            [
                # Last byte of the first word, then first byte of the
                # second, then zeroing that byte, which keeps the size.
                Write(Op.MSTORE8, 0x1F, 1),
                Write(Op.MSTORE8, 0x20, 1),
                Write(Op.MSTORE8, 0x20, 0),
            ],
            id="byte_chunks",
        ),
        pytest.param(
            [Write(Op.MSTORE8, FAR_OFFSET, 1)],
            id="far_byte",
        ),
    ],
)
def test_msize(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    writes: list[Write],
    operands: Operands,
    memory: Memory,
) -> None:
    """Verify MSIZE after each write grows in whole words."""
    code = Bytecode()
    storage: dict[int, int] = {}
    for slot, write in enumerate(writes):
        code += write.code(operands) + Op.SSTORE(slot, Op.MSIZE)
        write.apply(memory)
        storage[slot] = memory.size
    code += Op.STOP

    contract = pre.deploy_contract(
        code=code, storage=dict.fromkeys(storage, SENTINEL)
    )
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        data=operands.calldata,
        protected=fork.supports_protected_txs(),
    )
    state_test(pre=pre, post={contract: Account(storage=storage)}, tx=tx)


def mload_code(offset: int, operands: Operands) -> Bytecode:
    """Return code storing the word MLOAD reads at `offset`."""
    load = Op.MLOAD(offset=operands(offset), new_memory_size=offset + 32)
    return (
        Op.SSTORE(
            RESULT_SLOT,
            load,
            key_warm=False,
            original_value=SENTINEL,
            new_value=0,
        )
        + Op.STOP
    )


@pytest.mark.parametrize("offset", [0, 0x724825, 0xFFFFFFF], ids=hex)
def test_mload_out_of_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    offset: int,
    operands: Operands,
) -> None:
    """
    Revert the frame when MLOAD cannot pay for its memory expansion.

    The gas limit exactly funds the same code reading at offset 0, so the
    in-bounds read succeeds and the far reads run out of gas.
    """
    code = mload_code(offset, operands)
    in_bounds_code = mload_code(0, Operands(operands.source))
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()(
        calldata=operands.calldata
    )
    gas_limit = intrinsic_cost + in_bounds_code.gas_cost(fork)
    expected = 0
    if offset > 0:
        assert intrinsic_cost + code.gas_cost(fork) > gas_limit
        expected = SENTINEL

    contract = pre.deploy_contract(code=code, storage={RESULT_SLOT: SENTINEL})
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        data=operands.calldata,
        gas_limit=gas_limit,
        protected=fork.supports_protected_txs(),
    )
    post = {contract: Account(storage={RESULT_SLOT: expected})}
    state_test(pre=pre, post=post, tx=tx)
