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
    Environment,
    Op,
    StateTestFiller,
    Transaction,
)

from ethereum.forks.amsterdam.vm.stack import decode_single, encode_single

from .spec import ref_spec_8024

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

    # Encode the stack index to the immediate byte
    immediate = encode_single(stack_index)
    code += Op.DUPN[immediate]
    # Store the duplicated value
    code += Op.PUSH1(0) + Op.SSTORE
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    post = {contract_address: Account(storage={0: expected_value})}

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


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

    code += Op.DUPN[immediate]
    code += Op.PUSH1(0) + Op.SSTORE
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender, gas_limit=10_000_000)

    post = {contract_address: Account(storage={0: expected_value})}

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


def test_dupn_stack_underflow(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """Test DUPN causes transaction failure on stack underflow."""
    sender = pre.fund_eoa()

    # DUPN with immediate 0 needs stack index 17, so push only 16 items
    code = Bytecode()
    for i in range(16):
        code += Op.PUSH1(i)
    code += Op.DUPN[0]  # decode_single(0) = 17, but only 16 items on stack
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    # Transaction should fail, contract storage unchanged
    post = {contract_address: Account(storage={})}

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


def test_endofcode_behavior(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    Test DUPN when the immediate byte is beyond the end of code.

    Per EIP-8024, code[pc + 1] evaluates to 0 if beyond the end of the code,
    matching PUSH behavior. With immediate = 0, decode_single(0) = 17, so
    DUPN duplicates the 17th stack item.

    This test verifies the transaction succeeds (doesn't revert) when DUPN
    is the last byte of the code with no immediate byte following it.
    """
    sender = pre.fund_eoa()

    # decode_single(0) = 17, which duplicates the 17th item from top
    # We need 17 items on the stack for this to succeed
    stack_height = 17
    marker_value = 0x42
    # The value at position 17 (first pushed) will be duplicated
    dup_target_value = 0xBEEF

    # Build code: store marker, push enough items, then DUPN (no immediate)
    code = Bytecode()
    code += Op.PUSH1(marker_value) + Op.PUSH1(0) + Op.SSTORE  # Store marker

    # Push 17 items to stack so DUPN with implicit imm=0 succeeds
    for i in range(stack_height):
        if i == 0:
            code += Op.PUSH2(dup_target_value)  # This will be at position 17
        else:
            code += Op.PUSH1(i)

    # Add just the DUPN opcode without immediate byte
    # After DUPN, pc += 2 goes beyond code, causing implicit STOP
    code += bytes([0xE6])  # DUPN opcode only, no immediate

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    # If tx succeeds, storage[0] = marker_value
    # Bad implementation would revert and have empty storage
    post = {contract_address: Account(storage={0: marker_value})}

    state_test(env=Environment(), pre=pre, post=post, tx=tx)
