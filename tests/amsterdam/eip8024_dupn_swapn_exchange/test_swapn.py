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
    ids=lambda x: f"swapn_stack_{x}",
)
def test_swapn_basic(
    stack_index: int,
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """Test SWAPN with various stack indices (17-235)."""
    sender = pre.fund_eoa()

    # SWAPN with immediate x swaps top with the decode_single(x)th stack item
    stack_height = stack_index
    top_value = 0xAAAA
    swap_target_value = 0xBBBB

    # Build stack with known values at top and swap position
    code = Bytecode()
    for i in range(stack_height):
        if i == 0:
            # First push ends up at position stack_index from top
            code += Op.PUSH2(swap_target_value)
        elif i == stack_height - 1:
            # Last push ends up at top
            code += Op.PUSH2(top_value)
        else:
            code += Op.PUSH2(0x1000 + i)

    # Encode the stack index to the immediate byte
    immediate = encode_single(stack_index)
    code += Op.SWAPN[immediate]

    # Store both swapped values to verify
    code += Op.PUSH1(0) + Op.SSTORE  # New top (was swap_target_value)

    # Pop intermediate values to get to the swapped position
    for _ in range(stack_index - 2):
        code += Op.POP

    code += Op.PUSH1(1) + Op.SSTORE  # New position (was top_value)
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    post = {
        contract_address: Account(
            storage={
                0: swap_target_value,  # Top now has the swapped value
                1: top_value,  # Position stack_index now has original top
            }
        )
    }

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


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
    stack_index = decode_single(immediate)
    stack_height = stack_index
    top_value = 0xAAAA
    swap_target_value = 0xBBBB

    # Build stack
    code = Bytecode()
    for i in range(stack_height):
        if i == 0:
            code += Op.PUSH2(swap_target_value)
        elif i == stack_height - 1:
            code += Op.PUSH2(top_value)
        else:
            code += Op.PUSH2(0x1000 + i)

    code += Op.SWAPN[immediate]

    # Store the new top value
    code += Op.PUSH1(0) + Op.SSTORE
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender, gas_limit=10_000_000)

    post = {
        contract_address: Account(
            storage={
                0: swap_target_value,  # Top now has the swapped value
            }
        )
    }

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


def test_swapn_preserves_other_stack_items(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """Test SWAPN only swaps the specified items, leaving others unchanged."""
    sender = pre.fund_eoa()

    # Use stack index 17 (smallest valid), needs 17 items
    stack_index = 17
    immediate = encode_single(stack_index)

    # Create a stack with 17 distinct values
    code = Bytecode()
    for i in range(stack_index):
        code += Op.PUSH2(0x1000 + i)

    # SWAPN swaps top (position 1) with position 17
    code += Op.SWAPN[immediate]

    # Store all values to verify only the swapped ones changed
    for i in range(stack_index):
        code += Op.PUSH1(i) + Op.SSTORE

    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    # After swap: position 1 and position 17 are swapped
    # Original stack (top to bottom): 0x1010, 0x100F, ..., 0x1001, 0x1000
    # After SWAPN[0]: 0x1000, 0x100F, ..., 0x1001, 0x1010
    expected_storage = {}
    for i in range(stack_index):
        if i == 0:
            expected_storage[i] = 0x1000  # Was at bottom, now at top
        elif i == stack_index - 1:
            expected_storage[i] = 0x1010  # Was at top, now at bottom
        else:
            expected_storage[i] = 0x1000 + (stack_index - 1 - i)

    post = {contract_address: Account(storage=expected_storage)}

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


def test_swapn_stack_underflow(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """Test SWAPN causes transaction failure on stack underflow."""
    sender = pre.fund_eoa()

    # SWAPN with immediate 0 needs stack index 17, so push only 16 items
    code = Bytecode()
    for i in range(16):
        code += Op.PUSH1(i)
    code += Op.SWAPN[0]  # decode_single(0) = 17, but only 16 items on stack
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    # Transaction should fail, contract storage unchanged
    post = {contract_address: Account(storage={})}

    state_test(env=Environment(), pre=pre, post=post, tx=tx)
