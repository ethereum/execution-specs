"""
Test the RETURN data a caller receives.

The original tests were written by Ori Pomerantz.

Ported from:
state_tests/VMTests/vmIOandFlowOperations/returnFiller.yml

@manually-enhanced: Do not overwrite. Built from readable parameters.

A `caller` calls the `callee` whose address the transaction sends as
calldata, with every call opcode the fork has, stores the call's success
flag, and stores the two words of its 0x40-byte return buffer. The buffer
starts filled with `BUFFER_FILL`, so a client that writes past the
returned data, for example by zero-padding it to the buffer's size,
changes a word it must leave alone. `test_return` returns a range of the
callee's memory and derives the expected words from that range.
`test_return_memory_out_of_gas` returns a range whose memory expansion
cannot be paid for, so the call fails and nothing is returned.
`test_return_halts` returns from either branch of a JUMPI, with code
after each RETURN that would change the returned word if RETURN did not
halt.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op, Opcode

from tests.ported_static.helpers import Memory

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

SENTINEL = 0x0BAD
MAX_UINT = 2**256 - 1
WORD = 0x0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF
JUMPED = 0x600D
FELL_THROUGH = 0x60A7
NOT_HALTED = 0xDEAD
# Fills the caller's return buffer before the call: non-zero in every byte,
# and distinct from the storage sentinel and every returned word.
BUFFER_FILL = int.from_bytes(b"\xb0" * 32)

FIRST_WORD_SLOT = 0
SECOND_WORD_SLOT = 1
SUCCESS_SLOT = 2
RETURN_BUFFER_SIZE = 0x40
# Explicit, so the call does not ask for more gas than is left before
# EIP-150 lets it forward all but 1/64th.
CALLEE_GAS = 0x10000

pytestmark = [
    pytest.mark.ported_from(
        ["state_tests/VMTests/vmIOandFlowOperations/returnFiller.yml"],
    ),
    pytest.mark.valid_from("Frontier"),
    pytest.mark.with_all_call_opcodes(),
]


@pytest.fixture
def caller(pre: Alloc, call_opcode: Opcode) -> Address:
    """Deploy the caller of the callee address read from calldata."""
    return pre.deploy_contract(
        code=Op.MSTORE(0, BUFFER_FILL)
        + Op.MSTORE(0x20, BUFFER_FILL)
        + Op.SSTORE(
            SUCCESS_SLOT,
            call_opcode(
                gas=CALLEE_GAS,
                address=Op.CALLDATALOAD(0),
                ret_offset=0,
                ret_size=RETURN_BUFFER_SIZE,
            ),
        )
        + Op.SSTORE(FIRST_WORD_SLOT, Op.MLOAD(0))
        + Op.SSTORE(SECOND_WORD_SLOT, Op.MLOAD(0x20))
        + Op.STOP,
        storage=dict.fromkeys(
            (FIRST_WORD_SLOT, SECOND_WORD_SLOT, SUCCESS_SLOT), SENTINEL
        ),
    )


@pytest.fixture
def memory() -> Memory:
    """Return an empty model of the callee's memory."""
    return Memory()


def caller_storage(success: bool, return_data: bytes) -> dict[int, int]:
    """
    Return the caller's storage after receiving `return_data`, which
    overwrites only the start of the pre-filled return buffer.
    """
    buffer = bytearray(BUFFER_FILL.to_bytes(32, "big") * 2)
    returned = return_data[:RETURN_BUFFER_SIZE]
    buffer[: len(returned)] = returned
    return {
        FIRST_WORD_SLOT: int.from_bytes(buffer[:0x20]),
        SECOND_WORD_SLOT: int.from_bytes(buffer[0x20:]),
        SUCCESS_SLOT: int(success),
    }


@pytest.mark.parametrize(
    "offset, size",
    [
        pytest.param(0, RETURN_BUFFER_SIZE, id="fills_return_buffer"),
        # Larger than the return buffer, which keeps only its start.
        pytest.param(0, 0x1000, id="exceeds_return_buffer"),
        # Unaligned, and shorter than the return buffer, whose second
        # word keeps its fill.
        pytest.param(5, 0x20, id="unaligned_offset"),
        pytest.param(0, 0, id="empty"),
        # An empty range does not expand memory, whatever its offset.
        pytest.param(MAX_UINT, 0, id="empty_at_max_offset"),
    ],
)
def test_return(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    caller: Address,
    memory: Memory,
    offset: int,
    size: int,
) -> None:
    """Return `size` bytes of the callee's memory from `offset`."""
    callee = pre.deploy_contract(
        code=Op.MSTORE(0, WORD) + Op.RETURN(offset=offset, size=size)
    )
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller,
        data=Hash(callee, left_padding=True),
        protected=fork.supports_protected_txs(),
    )

    memory.store(0, WORD)
    return_data = memory.read(offset, size)
    post = {caller: Account(storage=caller_storage(True, return_data))}
    state_test(pre=pre, post=post, tx=tx)


def test_return_memory_out_of_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    caller: Address,
) -> None:
    """Fail the call when RETURN cannot pay for its memory expansion."""
    callee = pre.deploy_contract(
        code=Op.MSTORE(0, WORD) + Op.RETURN(offset=0, size=MAX_UINT)
    )
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller,
        data=Hash(callee, left_padding=True),
        protected=fork.supports_protected_txs(),
    )
    post = {caller: Account(storage=caller_storage(False, b""))}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "jump_taken", [True, False], ids=["jump_taken", "jump_not_taken"]
)
def test_return_halts(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    caller: Address,
    memory: Memory,
    jump_taken: bool,
) -> None:
    """Return from either JUMPI branch, skipping the code after RETURN."""
    # Returns `NOT_HALTED` instead if execution goes on past a RETURN.
    after_return = Op.MSTORE(0, NOT_HALTED) + Op.RETURN(0, 0x20)
    code: Bytecode = (
        Op.JUMPI(
            pc=Op.PUSH1(data_placeholder="jumped"), condition=int(jump_taken)
        )
        + Op.MSTORE(0, FELL_THROUGH)
        + Op.RETURN(0, 0x20)
        + after_return
    )
    code.substitute(jumped=len(code))
    code += (
        Op.JUMPDEST + Op.MSTORE(0, JUMPED) + Op.RETURN(0, 0x20) + after_return
    )
    callee = pre.deploy_contract(code=code)
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller,
        data=Hash(callee, left_padding=True),
        protected=fork.supports_protected_txs(),
    )

    memory.store(0, JUMPED if jump_taken else FELL_THROUGH)
    return_data = memory.read(0, 0x20)
    post = {caller: Account(storage=caller_storage(True, return_data))}
    state_test(pre=pre, post=post, tx=tx)
