"""
SWAPN instruction tests.

Tests for SWAPN instruction in
[EIP-8024: Stack Access Instructions](https://eips.ethereum.org/EIPS/eip-8024).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    EIPChecklist,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
)

from .spec import Spec, decode_single, ref_spec_8024

REFERENCE_SPEC_GIT_PATH = ref_spec_8024.git_path
REFERENCE_SPEC_VERSION = ref_spec_8024.version

pytestmark = pytest.mark.valid_from("EIP8024")


@EIPChecklist.Opcode.Test.StackComplexOperations.StackHeights.Odd()
@EIPChecklist.Opcode.Test.StackComplexOperations.StackHeights.Even()
@EIPChecklist.Opcode.Test.StackComplexOperations.DataPortionVariables.Bottom()
@pytest.mark.parametrize(
    "stack_index",
    [17, 18, 32, 64, 107, 108, 200, 235],
    ids=lambda x: f"swapn_stack_{x}",
)
def test_swapn_basic(
    stack_index: int,
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """Test SWAPN with various stack indices (17-235)."""
    sender = pre.fund_eoa()

    # SWAPN with decoded value n swaps position 1 with position (n+1)
    # So we need stack_height = stack_index + 1 items
    stack_height = stack_index + 1
    top_value = 0xAAAA
    swap_target_value = 0xBBBB

    # Build stack with known values at top and swap position (n+1)
    code = Bytecode()

    # First push ends up at position (stack_index+1) from top
    code += Op.PUSH2(swap_target_value)

    # Pushes in-between
    for i in range(1, stack_height - 1):
        code += Op.PUSH2(0x1000 + i)

    # Last push ends up at top
    code += Op.PUSH2(top_value)

    # Pass stack index directly - encoder will handle encoding
    code += Op.SWAPN[stack_index]

    # Store both swapped values to verify
    code += Op.PUSH1(0) + Op.SSTORE  # New top (was swap_target_value)

    # Pop intermediate values to get to the swapped position
    for _ in range(stack_index - 1):
        code += Op.POP

    code += Op.PUSH1(1) + Op.SSTORE  # New position (was top_value)
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender)

    post = {
        contract_address: Account(
            storage={
                0: swap_target_value,  # Top now has the swapped value
                1: top_value,  # Position (stack_index+1) now has original top
            }
        )
    }

    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.Opcode.Test.DataPortion.AllZeros()
@EIPChecklist.Opcode.Test.DataPortion.MaxValue()
@pytest.mark.parametrize(
    "immediate",
    [0, 45, 90, 128, 200, 255],
    ids=lambda x: f"swapn_imm_{x}",
)
def test_swapn_valid_immediates(
    immediate: int,
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """Test SWAPN with valid immediate values (0-90 and 128-255)."""
    sender = pre.fund_eoa()

    # Decode the immediate to get the stack index
    # SWAPN with decoded value n swaps position 1 with position (n+1)
    stack_index = decode_single(immediate)
    stack_height = stack_index + 1
    top_value = 0xAAAA
    swap_target_value = 0xBBBB

    # Build stack
    code = Bytecode()

    # First push ends up at position (stack_index+1) from top
    code += Op.PUSH2(swap_target_value)

    # Pushes in-between
    for i in range(1, stack_height - 1):
        code += Op.PUSH2(0x1000 + i)

    # Last push ends up at top
    code += Op.PUSH2(top_value)

    # Pass immediate as bytes (raw immediate byte for testing)
    code += Op.SWAPN[immediate.to_bytes(1, "big")]

    # Store the new top value
    code += Op.PUSH1(0) + Op.SSTORE
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender)

    post = {
        contract_address: Account(
            storage={
                0: swap_target_value,  # Top now has the swapped value
            }
        )
    }

    state_test(pre=pre, post=post, tx=tx)


def test_swapn_preserves_other_stack_items(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """Test SWAPN only swaps the specified items, leaving others unchanged."""
    sender = pre.fund_eoa()

    # Use stack index 17 (smallest valid)
    # SWAPN with n=17 swaps position 1 with position 18, so need 18 items
    stack_index = 17
    stack_height = stack_index + 1  # Need 18 items

    # Create a stack with 18 distinct values
    code = Bytecode()
    for i in range(stack_height):
        code += Op.PUSH2(0x1000 + i)

    # SWAPN swaps top (position 1) with position 18
    # Pass stack index directly - encoder will handle encoding
    code += Op.SWAPN[stack_index]

    # Store all values to verify only the swapped ones changed
    for i in range(stack_height):
        code += Op.PUSH1(i) + Op.SSTORE

    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender)

    # After swap: position 1 and position 18 are swapped
    # Original stack (top to bottom): 0x1011, 0x1010, ..., 0x1001, 0x1000
    # After SWAPN[0]: 0x1000, 0x1010, ..., 0x1001, 0x1011
    expected_storage = {}
    for i in range(stack_height):
        if i == 0:
            expected_storage[i] = 0x1000  # Was at bottom, now at top
        elif i == stack_height - 1:
            expected_storage[i] = 0x1011  # Was at top, now at bottom
        else:
            expected_storage[i] = 0x1000 + (stack_height - 1 - i)

    post = {contract_address: Account(storage=expected_storage)}

    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.Opcode.Test.StackUnderflow()
def test_swapn_stack_underflow(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """Test SWAPN causes transaction failure on stack underflow."""
    sender = pre.fund_eoa()

    # SWAPN with immediate 0x80 (n=17) swaps position 1 with position 18
    # Need 18 items, so push only 17 to trigger underflow
    code = Bytecode()
    for i in range(17):
        code += Op.PUSH1(i)
    # Pass immediate as bytes (raw immediate byte for testing)
    # decode_single(0x80) = 17, needs 18 items but only 17
    code += Op.SWAPN[b"\x80"]
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender)

    # Transaction should fail, contract storage unchanged
    post = {contract_address: Account(storage={})}

    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.Opcode.Test.StackComplexOperations.StackHeights.Zero()
@EIPChecklist.Opcode.Test.StackUnderflow()
def test_swapn_empty_stack(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    Test SWAPN on an empty stack aborts with a stack underflow.
    """
    sender = pre.fund_eoa()

    code = Op.SSTORE(0, 1)  # leaves the stack empty
    code += Op.SWAPN[Spec.MIN_STACK_INDEX]
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender)

    # Transaction should fail, contract storage unchanged.
    post = {contract_address: Account(storage={0: 0})}

    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.Opcode.Test.GasUsage.Normal()
@EIPChecklist.Opcode.Test.GasUsage.OutOfGasExecution()
@EIPChecklist.Opcode.Test.GasUsage.ExtraGas()
@pytest.mark.parametrize("gas_cost_delta", [-2, -1, 0, 1, 2])
def test_swapn_gas_cost_boundary(
    gas_cost_delta: int,
    pre: Alloc,
    fork: Fork,
    state_test: StateTestFiller,
) -> None:
    """
    Test SWAPN at the gas cost boundary.

    SWAPN is invoked in a callee that receives exactly its execution cost
    plus `gas_cost_delta`. The caller records the CALL result: a negative
    delta starves SWAPN of its base gas (3) and the sub-call runs out of
    gas (result 0); a zero or positive delta succeeds (result 1).
    """
    # SWAPN with decoded value n swaps position 1 with position (n+1), so
    # it needs stack_index + 1 items on the stack.
    stack_index = Spec.MIN_STACK_INDEX  # 17

    code = Bytecode()
    for i in range(stack_index + 1):
        code += Op.PUSH1(i)
    code += Op.SWAPN[stack_index]

    contract_address = pre.deploy_contract(code=code)

    call_code = Op.SSTORE(
        0,
        Op.CALL(
            gas=code.gas_cost(fork) + gas_cost_delta,
            address=contract_address,
        ),
    )
    call_address = pre.deploy_contract(
        code=call_code,
        storage={0: 0xDEADBEEF},
    )

    tx = Transaction(to=call_address, sender=pre.fund_eoa())

    post = {call_address: Account(storage={0: 0 if gas_cost_delta < 0 else 1})}

    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.Opcode.Test.ExceptionalAbort()
@pytest.mark.parametrize(
    "invalid_immediate",
    list(range(91, 128)),  # 0x5b to 0x7f (JUMPDEST and PUSH opcodes)
    ids=lambda x: f"swapn_invalid_imm_0x{x:02x}",
)
def test_swapn_invalid_immediate_aborts(
    invalid_immediate: int,
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    Test SWAPN with invalid immediate values (90 < x < 128) aborts.

    Per EIP-8024, immediate values in range [91, 127] (0x5b-0x7f) are
    invalid because they correspond to JUMPDEST (0x5b) and PUSH opcodes
    (0x60-0x7f). Attempting to execute SWAPN with these immediates should
    abort.
    """
    sender = pre.fund_eoa()

    # Build a stack tall enough for any valid immediate (max decoded index
    # is 235, SWAPN needs index + 1 items) so the abort is caused by the
    # invalid immediate, never an underflow.
    code = Bytecode()
    for i in range(Spec.MAX_STACK_INDEX + 1):
        code += Op.PUSH1(i % 256)

    # Attempt SWAPN with invalid immediate - should abort.
    # Pass as bytes (raw immediate byte for testing invalid ranges).
    code += Op.SWAPN[invalid_immediate.to_bytes(1, "big")]

    # This should never execute.
    code += Op.PUSH1(0x42) + Op.PUSH1(0) + Op.SSTORE
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender)

    # Transaction should fail - invalid immediate causes abort.
    post = {contract_address: Account(storage={})}

    state_test(pre=pre, post=post, tx=tx)


def test_endofcode_behavior(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    Test SWAPN when the immediate byte is beyond the end of code.

    Per EIP-8024, code[pc + 1] evaluates to 0 if beyond the end of the code,
    matching PUSH behavior. With immediate = 0, decode_single(0) = 145, so
    SWAPN swaps position 1 with position 146.

    This test verifies the transaction succeeds (doesn't revert) when SWAPN
    is the last byte of the code with no immediate byte following it.
    """
    sender = pre.fund_eoa()

    # decode_single(0) = 145, which swaps position 1 with position 146
    # We need 146 items on the stack for this to succeed
    stack_height = 146
    marker_value = 0x42

    # Build code: store marker, push enough items, then SWAPN (no immediate)
    code = Bytecode()
    code += Op.PUSH1(marker_value) + Op.PUSH1(0) + Op.SSTORE  # Store marker

    # Push 146 items to stack so SWAPN with implicit imm=0 succeeds
    for i in range(stack_height):
        code += Op.PUSH1(i % 256)

    # Add just the SWAPN opcode without immediate byte
    # After SWAPN, pc += 2 goes beyond code, causing implicit STOP
    code += Op.SWAPN  # no immediate

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender)

    # If tx succeeds, storage[0] = marker_value
    # Bad implementation would revert and have empty storage
    post = {contract_address: Account(storage={0: marker_value})}

    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.Opcode.Test.DataPortion.Jump()
def test_swapn_jump_to_immediate_byte_0x5b_succeeds(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    Test that jumping to 0x5b after SWAPN succeeds (backward compat).

    Bytecode: PUSH1(4) JUMP SWAPN[0x5b]
    Hex: 6004 56 e7 5b
    Position 4 contains 0x5b which is an INVALID immediate for SWAPN.
    Per EIP-8024, 0x5b is preserved as valid JUMPDEST for compatibility.
    The SWAPN instruction is never executed due to the jump.
    """
    sender = pre.fund_eoa()

    # Build code that jumps to 0x5b after SWAPN opcode
    code = Bytecode()
    code += Op.PUSH1(4)  # Push jump target (position 4)
    code += Op.JUMP  # Jump to position 4
    # Pass as bytes (raw immediate byte for testing)
    code += Op.SWAPN[b"\x5b"]  # Position 3-4: SWAPN + 0x5b (invalid)

    # This SHOULD execute because 0x5b is a valid JUMPDEST
    code += Op.PUSH1(0x42) + Op.PUSH1(0) + Op.SSTORE
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender)

    # Transaction succeeds - 0x5b is preserved as valid JUMPDEST
    post = {contract_address: Account(storage={0: 0x42})}

    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.Opcode.Test.DataPortion.Jump()
def test_swapn_jump_to_valid_immediate_fails(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    Test jumping to a valid immediate byte fails.

    Bytecode: PUSH1(4) JUMP SWAPN[0x00]
    Hex: 6004 56 e7 00
    Position 4 contains 0x00 which is a VALID immediate for SWAPN.
    JUMPDEST analysis is unchanged by EIP-8024: position 4 holds 0x00,
    not 0x5b, so it is not a valid jump target and the jump fails.
    """
    sender = pre.fund_eoa()

    # Build code that tries to jump to a valid immediate
    code = Bytecode()
    code += Op.PUSH1(4)  # Push jump target (position 4)
    code += Op.JUMP  # Try to jump to position 4
    # Pass as bytes (raw immediate byte for testing)
    code += Op.SWAPN[b"\x00"]  # Position 3-4: SWAPN + 0x00 (valid)

    # This should never execute
    code += Op.PUSH1(0x42) + Op.PUSH1(0) + Op.SSTORE
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender)

    # Transaction fails - position 4 is a valid immediate, not JUMPDEST
    post = {contract_address: Account(storage={})}

    state_test(pre=pre, post=post, tx=tx)


def test_swapn_with_dup1_and_push(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    Test SWAPN swapping top and bottom after building stack with DUP1.

    Stack layout: PUSH1(1) PUSH1(0) DUP1*15 PUSH1(2) SWAPN[0x80]
    Before SWAPN: [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
    After SWAPN[0x80] (decode_single(0x80)=17, swaps pos 1 and 18):
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2]
    Result: 18 stack items, top=1, bottom=2, rest=0
    """
    sender = pre.fund_eoa()

    # Build the stack: PUSH1(1), PUSH1(0), 15x DUP1, PUSH1(2)
    code = Bytecode()
    code += Op.PUSH1(1)  # Position 18 after DUP1s and final PUSH1
    code += Op.PUSH1(0)
    for _ in range(15):
        code += Op.DUP1
    code += Op.PUSH1(2)  # Top of stack (position 1)

    # Stack: [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
    # SWAPN with immediate 0x80 (decode_single(0x80)=17) swaps pos 1 and 18
    # Pass as bytes (raw immediate byte for testing)
    code += Op.SWAPN[b"\x80"]

    # Store all stack values to verify
    for i in range(18):
        code += Op.PUSH1(i) + Op.SSTORE

    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender)

    # Expected: top (position 0) = 1, bottom (position 17) = 2, rest = 0
    expected_storage = {}
    for i in range(18):
        if i == 0:
            expected_storage[i] = 1  # Was at bottom, now at top
        elif i == 17:
            expected_storage[i] = 2  # Was at top, now at bottom
        else:
            expected_storage[i] = 0  # All middle values

    post = {contract_address: Account(storage=expected_storage)}

    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.Opcode.Test.StackComplexOperations.DataPortionVariables.Top()
@EIPChecklist.Opcode.Test.StackComplexOperations.DataPortionVariables.Middle()
@pytest.mark.parametrize(
    "stack_index",
    [17, 126, 235],
    ids=lambda x: f"swapn_full_stack_{x}",
)
def test_swapn_full_stack(
    stack_index: int,
    pre: Alloc,
    fork: Fork,
    state_test: StateTestFiller,
) -> None:
    """
    Test SWAPN succeeds on a completely full stack.

    SWAPN swaps in place without pushing, so it must work at the stack
    limit. The top marker is swapped down to position `stack_index + 1`;
    popping `stack_index` items then exposes it. If a faulty
    implementation had not swapped, the popped-to item would hold the
    planted deep marker instead, so either direction of failure is
    visible in storage.
    """
    sender = pre.fund_eoa()

    top_marker = 0xAAAA
    deep_marker = 0xBBBB

    # Full stack, top-down: the top marker at position 1, the deep
    # marker at the swap target, position stack_index + 1.
    stack = [0] * fork.max_stack_height()
    stack[0] = top_marker
    stack[stack_index] = deep_marker

    code = Bytecode()
    for value in reversed(stack):
        code += Op.PUSH2(value) if value else Op.PUSH0

    code += Op.SWAPN[stack_index]

    # Pop down to the swap target and store the item now there.
    code += Op.POP * stack_index
    code += Op.PUSH1(0) + Op.SSTORE
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code, storage={0: 0xBA5E})

    tx = Transaction(to=contract_address, sender=sender)

    post = {contract_address: Account(storage={0: top_marker})}

    state_test(pre=pre, post=post, tx=tx)
