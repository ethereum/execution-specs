"""
DUPN instruction tests.

Tests for DUPN instruction in
[EIP-8024: Stack Access Instructions](https://eips.ethereum.org/EIPS/eip-8024).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Op,
    StateTestFiller,
    Transaction,
)

from .spec import decode_single, ref_spec_8024

REFERENCE_SPEC_GIT_PATH = ref_spec_8024.git_path
REFERENCE_SPEC_VERSION = ref_spec_8024.version

pytestmark = pytest.mark.valid_from("Amsterdam")


@pytest.mark.parametrize(
    "stack_index",
    [17, 18, 32, 64, 107, 108, 200, 235],
    ids=lambda x: f"dupn_stack_{x}",
)
def test_dupn_basic(
    stack_index: int,
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """Test DUPN with various stack indices (17-235)."""
    sender = pre.fund_eoa()

    # Build stack with enough items, then use DUPN to duplicate the nth item
    # DUPN with immediate x duplicates the decode_single(x)th stack item
    stack_height = stack_index
    expected_value = 0xBEEF + stack_index

    # Push values onto stack: the value at the target position will
    # be expected_value
    code = Bytecode()
    for i in range(stack_height):
        if i == 0:
            # The first push will end up at position stack_index from top
            code += Op.PUSH2(expected_value)
        else:
            code += Op.PUSH2(0x1000 + i)

    # Pass stack index directly - encoder will handle encoding
    code += Op.DUPN[stack_index]
    # Store the duplicated value
    code += Op.PUSH1(0) + Op.SSTORE
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    post = {contract_address: Account(storage={0: expected_value})}

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "immediate",
    [0, 45, 90, 128, 200, 255],
    ids=lambda x: f"dupn_imm_{x}",
)
def test_dupn_valid_immediates(
    immediate: int,
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """Test DUPN with valid immediate values (0-90 and 128-255)."""
    sender = pre.fund_eoa()

    # Decode the immediate to get the stack index
    stack_index = decode_single(immediate)
    stack_height = stack_index
    expected_value = 0xCAFE + immediate

    # Push values onto stack
    code = Bytecode()
    for i in range(stack_height):
        if i == 0:
            code += Op.PUSH2(expected_value)
        else:
            code += Op.PUSH2(0x1000 + i)

    # Pass immediate as bytes (raw immediate byte for testing)
    code += Op.DUPN[immediate.to_bytes(1, "big")]
    code += Op.PUSH1(0) + Op.SSTORE
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender, gas_limit=10_000_000)

    post = {contract_address: Account(storage={0: expected_value})}

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "immediate",
    [0, 45, 90, 128, 200, 255],
    ids=lambda x: f"dupn_underflow_imm_{x}",
)
def test_dupn_stack_underflow(
    immediate: int,
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """Test DUPN causes transaction failure on stack underflow."""
    sender = pre.fund_eoa()

    # Decode the immediate to get the stack index
    stack_index = decode_single(immediate)
    # Push one less than required to trigger underflow
    insufficient_items = stack_index - 1

    code = Op.SSTORE(0, 1)
    for i in range(insufficient_items):
        code += Op.PUSH1(i)
    # Pass immediate as bytes (raw immediate byte for testing)
    # Needs stack_index items, underflow
    code += Op.DUPN[immediate.to_bytes(1, "big")]
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    # Transaction should fail, contract storage unchanged
    post = {contract_address: Account(storage={0: 0})}

    state_test(pre=pre, post=post, tx=tx)


def test_endofcode_behavior(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    Test DUPN when the immediate byte is beyond the end of code.

    Per EIP-8024, code[pc + 1] evaluates to 0 if beyond the end of the code,
    matching PUSH behavior. With immediate = 0, decode_single(0) = 145, so
    DUPN duplicates the 145th stack item.

    This test verifies the transaction succeeds (doesn't revert) when DUPN
    is the last byte of the code with no immediate byte following it.
    """
    sender = pre.fund_eoa()

    # decode_single(0) = 145, which duplicates the 145th item from top
    # We need 145 items on the stack for this to succeed
    stack_height = 145
    marker_value = 0x42

    # Build code: store marker, push enough items, then DUPN (no immediate)
    code = Bytecode()
    code += Op.SSTORE(0, marker_value)  # Store marker

    # Push 145 items to stack so DUPN with implicit imm=0 succeeds
    for i in range(stack_height):
        code += Op.PUSH1(i % 256)

    # Add just the DUPN opcode without immediate byte
    # After DUPN, pc += 2 goes beyond code, causing implicit STOP
    code += Op.DUPN  # no immediate

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    # If tx succeeds, storage[0] = marker_value
    # Bad implementation would revert and have empty storage
    post = {contract_address: Account(storage={0: marker_value})}

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "invalid_immediate",
    list(range(91, 128)),  # 0x5b to 0x7f (JUMPDEST and PUSH opcodes)
    ids=lambda x: f"dupn_invalid_imm_0x{x:02x}",
)
def test_dupn_invalid_immediate_aborts(
    invalid_immediate: int,
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    Test DUPN with invalid immediate values (90 < x < 128) aborts execution.

    Per EIP-8024, immediate values in range [91, 127] (0x5b-0x7f) are invalid
    because they correspond to JUMPDEST (0x5b) and PUSH opcodes (0x60-0x7f).
    Attempting to execute DUPN with these immediates should abort.
    """
    sender = pre.fund_eoa()

    # Build stack with enough items for any valid immediate
    # Maximum stack index is 235, so push 235 items
    code = Bytecode()
    for i in range(235):
        code += Op.PUSH1(i % 256)

    # Attempt DUPN with invalid immediate - should abort
    # Pass as bytes (raw immediate byte for testing invalid ranges)
    code += Op.DUPN[invalid_immediate.to_bytes(1, "big")]

    # This should never execute
    code += Op.PUSH1(0x42) + Op.PUSH1(0) + Op.SSTORE
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender, gas_limit=10_000_000)

    # Transaction should fail - invalid immediate causes abort
    post = {contract_address: Account(storage={})}

    state_test(pre=pre, post=post, tx=tx)


def test_dupn_jump_to_immediate_byte_0x5b_succeeds(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    Test that jumping to 0x5b after DUPN succeeds (backward compatibility).

    Bytecode: PUSH1(4) JUMP DUPN[0x5b]
    Hex: 6004 56 e6 5b
    Position 4 contains 0x5b which is an INVALID immediate for DUPN.
    Per EIP-8024, 0x5b is preserved as valid JUMPDEST for compatibility.
    The DUPN instruction is never executed due to the jump.
    """
    sender = pre.fund_eoa()

    # Build code that jumps to 0x5b after DUPN opcode
    code = Bytecode()
    code += Op.PUSH1(4)  # Push jump target (position 4)
    code += Op.JUMP  # Jump to position 4
    # Pass as bytes (raw immediate byte for testing)
    code += Op.DUPN[b"\x5b"]  # Position 3-4: DUPN + 0x5b (invalid immediate)

    # This SHOULD execute because 0x5b is a valid JUMPDEST
    code += Op.SSTORE(0, 0x42)
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    # Transaction succeeds - 0x5b is preserved as valid JUMPDEST
    post = {contract_address: Account(storage={0: 0x42})}

    state_test(pre=pre, post=post, tx=tx)


def test_dupn_jump_to_valid_immediate_fails(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    Test jumping to a valid immediate byte fails.

    Bytecode: PUSH1(4) JUMP DUPN[0x00]
    Hex: 6004 56 e6 00
    Position 4 contains 0x00 which is a VALID immediate for DUPN.
    Valid immediates are skipped in JUMPDEST analysis, so jump fails.
    """
    sender = pre.fund_eoa()

    # Build code that tries to jump to a valid immediate
    code = Bytecode()
    code += Op.PUSH1(4)  # Push jump target (position 4)
    code += Op.JUMP  # Try to jump to position 4
    # Pass as bytes (raw immediate byte for testing)
    code += Op.DUPN[b"\x00"]  # Position 3-4: DUPN + 0x00 (valid immediate)

    # This should never execute
    code += Op.SSTORE(0, 0x42)
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    # Transaction fails - position 4 is a valid immediate, not JUMPDEST
    post = {contract_address: Account(storage={})}

    state_test(pre=pre, post=post, tx=tx)


def test_dupn_with_dup1_sequence(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    Test DUPN duplicating the bottom item after building stack with DUP1.

    Stack layout: PUSH1(1) PUSH1(0) DUP1*15 DUPN[0x80]
    Before DUPN: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
    After DUPN[0x80] (decode_single(0x80)=17): [1, 0, 0, ..., 0, 1]
    Result: 18 stack items, top=1, bottom=1, rest=0
    """
    sender = pre.fund_eoa()

    # Build the stack: PUSH1(1), PUSH1(0), 15x DUP1
    code = Bytecode()
    code += Op.PUSH1(1)  # Bottom of stack (position 17 after DUP1s)
    code += Op.PUSH1(0)
    for _ in range(15):
        code += Op.DUP1

    # Stack now has 17 items:
    # [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
    # DUPN with immediate 0x80 (decode_single(0x80) = 17) duplicates pos 17
    # Pass as bytes (raw immediate byte for testing)
    code += Op.DUPN[b"\x80"]

    # Store all stack values to verify
    for i in range(18):
        code += Op.PUSH1(i) + Op.SSTORE

    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    # Expected: top (position 0) = 1, bottom (position 17) = 1, all others = 0
    expected_storage = {}
    for i in range(18):
        if i == 0:
            expected_storage[i] = 1  # Top of stack after DUPN
        elif i == 17:
            expected_storage[i] = 1  # Bottom of stack
        else:
            expected_storage[i] = 0  # All middle values

    post = {contract_address: Account(storage=expected_storage)}

    state_test(pre=pre, post=post, tx=tx)
