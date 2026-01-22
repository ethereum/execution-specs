"""
EXCHANGE instruction tests.

Tests for EXCHANGE instruction in
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

from .spec import decode_pair, ref_spec_8024

REFERENCE_SPEC_GIT_PATH = ref_spec_8024.git_path
REFERENCE_SPEC_VERSION = ref_spec_8024.version

pytestmark = pytest.mark.valid_from("Amsterdam")


@pytest.mark.parametrize(
    "n,m",
    [
        (1, 2),  # Swap positions 2 and 3
        (1, 16),  # Swap positions 2 and 17
        (1, 29),  # Swap positions 2 and 30 (n + m = 30)
        (5, 10),  # Swap positions 6 and 11
        (13, 17),  # Swap positions 14 and 18 (n + m = 30)
    ],
    ids=lambda x: f"{x}",
)
def test_exchange_basic(
    n: int,
    m: int,
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """Test EXCHANGE with various n and m values."""
    sender = pre.fund_eoa()

    # EXCHANGE with decoded (n, m) swaps position (n+1) with position (m+1)
    stack_height = m + 1  # Need at least m+1 items
    value_at_n_plus_1 = 0xAAAA
    value_at_m_plus_1 = 0xBBBB

    # Build stack with known values at swap positions (n+1) and (m+1)
    code = Bytecode()
    for i in range(stack_height):
        # Stack position is 1-indexed from top, so i=0 is bottom
        stack_pos = stack_height - i  # Position from top (1-indexed)
        if stack_pos == n + 1:
            code += Op.PUSH2(value_at_n_plus_1)
        elif stack_pos == m + 1:
            code += Op.PUSH2(value_at_m_plus_1)
        else:
            code += Op.PUSH2(0x1000 + i)

    # Pass n and m directly - encoder will handle encoding
    code += Op.EXCHANGE[n, m]

    # Store all stack values to verify the swap
    for i in range(stack_height):
        code += Op.PUSH1(i) + Op.SSTORE

    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    # Build expected storage
    expected_storage = {}
    for i in range(stack_height):
        stack_pos = i + 1  # Position from top (1-indexed)
        if stack_pos == n + 1:
            expected_storage[i] = value_at_m_plus_1  # Now has value from m+1
        elif stack_pos == m + 1:
            expected_storage[i] = value_at_n_plus_1  # Now has value from n+1
        else:
            # Original value at this position
            original_i = stack_height - stack_pos
            expected_storage[i] = 0x1000 + original_i

    post = {contract_address: Account(storage=expected_storage)}

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "immediate",
    [0, 1, 15, 79, 128, 200, 255],
    ids=lambda x: f"exchange_imm_{x}",
)
def test_exchange_valid_immediates(
    immediate: int,
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """Test EXCHANGE with valid immediate values (0-79 and 128-255)."""
    sender = pre.fund_eoa()

    # Decode the immediate to get the stack indices
    # EXCHANGE with decoded (n, m) swaps position (n+1) with position (m+1)
    n, m = decode_pair(immediate)
    stack_height = m + 1  # Need at least m+1 items
    value_at_n_plus_1 = 0xAAAA
    value_at_m_plus_1 = 0xBBBB

    # Build stack
    code = Bytecode()
    for i in range(stack_height):
        stack_pos = stack_height - i
        if stack_pos == n + 1:
            code += Op.PUSH2(value_at_n_plus_1)
        elif stack_pos == m + 1:
            code += Op.PUSH2(value_at_m_plus_1)
        else:
            code += Op.PUSH2(0x1000 + i)

    # Pass immediate as bytes (raw immediate byte for testing)
    code += Op.EXCHANGE[immediate.to_bytes(1, "big")]

    # Store the swapped values
    for i in range(stack_height):
        code += Op.PUSH1(i) + Op.SSTORE

    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender, gas_limit=10_000_000)

    # Build expected storage
    expected_storage = {}
    for i in range(stack_height):
        stack_pos = i + 1
        if stack_pos == n + 1:
            expected_storage[i] = value_at_m_plus_1
        elif stack_pos == m + 1:
            expected_storage[i] = value_at_n_plus_1
        else:
            original_i = stack_height - stack_pos
            expected_storage[i] = 0x1000 + original_i

    post = {contract_address: Account(storage=expected_storage)}

    state_test(pre=pre, post=post, tx=tx)


def test_exchange_preserves_other_items(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """Test EXCHANGE only swaps specified items, leaving others unchanged."""
    sender = pre.fund_eoa()

    # Use n=1, m=5 - EXCHANGE swaps positions (n+1)=2 and (m+1)=6
    n, m = 1, 5

    # Create a stack with 6 distinct values
    code = Bytecode()
    code += Op.PUSH2(0x1111)  # Position 6 from top (will be swapped)
    code += Op.PUSH2(0x2222)  # Position 5 from top
    code += Op.PUSH2(0x3333)  # Position 4 from top
    code += Op.PUSH2(0x4444)  # Position 3 from top
    code += Op.PUSH2(0x5555)  # Position 2 from top (will be swapped)
    code += Op.PUSH2(0x6666)  # Position 1 (top)

    # EXCHANGE swaps position 2 with position 6
    # Pass n and m directly - encoder will handle encoding
    code += Op.EXCHANGE[n, m]

    # Store all values
    code += Op.PUSH1(0) + Op.SSTORE  # Position 1 (0x6666, unchanged)
    code += Op.PUSH1(1) + Op.SSTORE  # Position 2 (was 0x1111, swapped from 6)
    code += Op.PUSH1(2) + Op.SSTORE  # Position 3 (0x4444, unchanged)
    code += Op.PUSH1(3) + Op.SSTORE  # Position 4 (0x3333, unchanged)
    code += Op.PUSH1(4) + Op.SSTORE  # Position 5 (0x2222, unchanged)
    code += Op.PUSH1(5) + Op.SSTORE  # Position 6 (was 0x5555, swapped from 2)
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    post = {
        contract_address: Account(
            storage={
                0: 0x6666,  # Position 1 unchanged
                1: 0x1111,  # Was at position 6, now at position 2
                2: 0x4444,  # Position 3 unchanged
                3: 0x3333,  # Position 4 unchanged
                4: 0x2222,  # Position 5 unchanged
                5: 0x5555,  # Was at position 2, now at position 6
            }
        )
    }

    state_test(pre=pre, post=post, tx=tx)


def test_exchange_stack_underflow(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """Test EXCHANGE causes transaction failure on stack underflow."""
    sender = pre.fund_eoa()

    # Use n=1, m=5 - EXCHANGE swaps positions 2 and 6, so needs 6 items
    # Push only 5 to trigger underflow
    n, m = 1, 5

    code = Bytecode()
    for i in range(5):
        code += Op.PUSH1(i)
    # Pass n and m directly - encoder will handle encoding
    # Needs 6 items, should fail
    code += Op.EXCHANGE[n, m]
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    # Transaction should fail, contract storage unchanged
    post = {contract_address: Account(storage={})}

    state_test(pre=pre, post=post, tx=tx)


def test_endofcode_behavior(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    Test EXCHANGE when the immediate byte is beyond the end of code.

    Per EIP-8024, code[pc + 1] evaluates to 0 if beyond the end of the code,
    matching PUSH behavior. With immediate = 0, decode_pair(0) = (1, 29), so
    EXCHANGE swaps positions 2 and 30.

    This test verifies the transaction succeeds (doesn't revert) when EXCHANGE
    is the last byte of the code with no immediate byte following it.
    """
    sender = pre.fund_eoa()

    # decode_pair(0) = (1, 29), which swaps positions 2 and 30
    # We need 30 items on the stack for this to succeed
    stack_height = 30
    marker_value = 0x42

    # Build code: store marker, push enough items, then EXCHANGE (no immediate)
    code = Bytecode()
    code += Op.PUSH1(marker_value) + Op.PUSH1(0) + Op.SSTORE  # Store marker

    # Push 30 items to stack so EXCHANGE with implicit imm=0 succeeds
    for i in range(stack_height):
        code += Op.PUSH1(i)

    # Add just the EXCHANGE opcode without immediate byte
    # After EXCHANGE, pc += 2 goes beyond code, causing implicit STOP
    code += Op.EXCHANGE  # no immediate

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    # If tx succeeds, storage[0] = marker_value
    # Bad implementation would revert and have empty storage
    post = {contract_address: Account(storage={0: marker_value})}

    state_test(pre=pre, post=post, tx=tx)


def test_exchange_jump_to_immediate_byte_0x5b_succeeds(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    Test that jumping to 0x5b after EXCHANGE succeeds (backward compat).

    Bytecode: PUSH1(4) JUMP EXCHANGE[0x5b]
    Hex: 6004 56 e8 5b
    Position 4 contains 0x5b which is an INVALID immediate for EXCHANGE.
    Per EIP-8024, 0x5b is preserved as valid JUMPDEST for compatibility.
    The EXCHANGE instruction is never executed due to the jump.
    """
    sender = pre.fund_eoa()

    # Build code that jumps to 0x5b after EXCHANGE opcode
    code = Bytecode()
    code += Op.PUSH1(4)  # Push jump target (position 4)
    code += Op.JUMP  # Jump to position 4
    # Pass as bytes (raw immediate byte for testing)
    code += Op.EXCHANGE[b"\x5b"]  # Position 3-4: EXCHANGE + 0x5b (invalid)

    # This SHOULD execute because 0x5b is a valid JUMPDEST
    code += Op.PUSH1(0x42) + Op.PUSH1(0) + Op.SSTORE
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    # Transaction succeeds - 0x5b is preserved as valid JUMPDEST
    post = {contract_address: Account(storage={0: 0x42})}

    state_test(pre=pre, post=post, tx=tx)


def test_exchange_jump_to_valid_immediate_fails(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    Test jumping to a valid immediate byte fails.

    Bytecode: PUSH1(4) JUMP EXCHANGE[0x00]
    Hex: 6004 56 e8 00
    Position 4 contains 0x00 which is a VALID immediate for EXCHANGE.
    Valid immediates are skipped in JUMPDEST analysis, so jump fails.
    """
    sender = pre.fund_eoa()

    # Build code that tries to jump to a valid immediate
    code = Bytecode()
    code += Op.PUSH1(4)  # Push jump target (position 4)
    code += Op.JUMP  # Try to jump to position 4
    # Pass as bytes (raw immediate byte for testing)
    code += Op.EXCHANGE[b"\x00"]  # Position 3-4: EXCHANGE + 0x00 (valid)

    # This should never execute
    code += Op.PUSH1(0x42) + Op.PUSH1(0) + Op.SSTORE
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    # Transaction fails - position 4 is a valid immediate, not JUMPDEST
    post = {contract_address: Account(storage={})}

    state_test(pre=pre, post=post, tx=tx)


def test_exchange_with_push_sequence(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    Test EXCHANGE swapping positions 2 and 30 with a push sequence.

    Stack layout: 28x PUSH1(0) PUSH1(1) PUSH1(2) EXCHANGE[0]
    Before EXCHANGE (30 items, top to bottom):
    [2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
     0, 0, 0, 0, 0, 0, 0, 0]
    After EXCHANGE[0] (decode_pair(0)=(1,29), swaps positions 2 and 30):
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
     0, 0, 0, 0, 0, 0, 0, 1]
    Result: 30 stack items, top=2, bottom=1, rest=0
    """
    sender = pre.fund_eoa()

    # Build the stack: 28x PUSH1(0), PUSH1(1), PUSH1(2)
    code = Bytecode()
    for _ in range(28):
        code += Op.PUSH1(0)
    code += Op.PUSH1(1)  # Position 2 from top after final push
    code += Op.PUSH1(2)  # Position 1 (top)

    # Stack has 30 items:
    # [2, 1, 0, 0, ..., 0, 0] (28 zeros in the middle)
    # EXCHANGE with immediate 0 (decode_pair(0) = (1, 29))
    # swaps pos 2 and 30
    # Pass as bytes (raw immediate byte for testing)
    code += Op.EXCHANGE[b"\x00"]

    # Store all stack values to verify
    for i in range(30):
        code += Op.PUSH1(i) + Op.SSTORE

    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    # Expected: top (position 0) = 2, position 1 = 0 (swapped from 30),
    # bottom (position 29) = 1 (swapped from position 2), rest = 0
    expected_storage = {}
    for i in range(30):
        if i == 0:
            expected_storage[i] = 2  # Top unchanged
        elif i == 1:
            expected_storage[i] = 0  # Was at bottom (pos 30), now at pos 2
        elif i == 29:
            expected_storage[i] = 1  # Was at pos 2, now at bottom (pos 30)
        else:
            expected_storage[i] = 0  # All other values

    post = {contract_address: Account(storage=expected_storage)}

    state_test(pre=pre, post=post, tx=tx)
