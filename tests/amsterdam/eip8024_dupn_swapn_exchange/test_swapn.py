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

from .spec import ref_spec_8024

REFERENCE_SPEC_GIT_PATH = ref_spec_8024.git_path
REFERENCE_SPEC_VERSION = ref_spec_8024.version

pytestmark = pytest.mark.valid_from("Amsterdam")


@pytest.mark.parametrize(
    "swapn_operand",
    [0, 1, 15, 16, 127, 255],
    ids=lambda x: f"swapn_{x}",
)
def test_swapn_basic(
    swapn_operand: int,
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """Test SWAPN with various immediate operands."""
    sender = pre.fund_eoa()

    # SWAPN[n] swaps position 1 (top) with position n+2 (like SWAP{n+1})
    stack_height = swapn_operand + 2  # Need n+2 items for SWAPN[n]
    top_value = 0xAAAA
    swap_target_value = 0xBBBB

    # Build stack with known values at top and swap position
    code = Bytecode()
    for i in range(stack_height):
        if i == 0:
            # First push ends up at position (n+2) from top
            code += Op.PUSH2(swap_target_value)
        elif i == stack_height - 1:
            # Last push ends up at top
            code += Op.PUSH2(top_value)
        else:
            code += Op.PUSH2(0x1000 + i)

    # SWAPN[n] swaps top with (n+2)th item
    code += Op.SWAPN[swapn_operand]

    # Store both swapped values to verify
    code += Op.PUSH1(0) + Op.SSTORE  # New top (was swap_target_value)

    # Pop intermediate values to get to the swapped position
    for _ in range(swapn_operand):
        code += Op.POP

    code += Op.PUSH1(1) + Op.SSTORE  # New (n+2)th position (was top_value)
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    post = {
        contract_address: Account(
            storage={
                0: swap_target_value,  # Top now has the swapped value
                1: top_value,  # Position n+2 now has original top
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

    # Create a stack with 5 distinct values
    # SWAPN[n] swaps position 1 (top) with position n+2
    code = Bytecode()
    code += Op.PUSH2(0x1111)  # Position 5 from top
    code += Op.PUSH2(0x2222)  # Position 4 from top (will be swapped)
    code += Op.PUSH2(0x3333)  # Position 3 from top
    code += Op.PUSH2(0x4444)  # Position 2 from top
    code += Op.PUSH2(0x5555)  # Position 1 (top, will be swapped)

    # SWAPN[2] swaps position 1 with position 4 (like SWAP3)
    code += Op.SWAPN[2]

    # Store all values to verify
    # After swap: top=0x2222, pos2=0x4444, pos3=0x3333,
    # pos4=0x5555, pos5=0x1111
    code += Op.PUSH1(0) + Op.SSTORE  # Slot 0 = new top
    code += Op.PUSH1(1) + Op.SSTORE  # Slot 1 = position 2 (0x4444, unchanged)
    code += Op.PUSH1(2) + Op.SSTORE  # Slot 2 = position 3 (0x3333, unchanged)
    code += Op.PUSH1(3) + Op.SSTORE  # Slot 3 = position 4 (0x5555, swapped)
    code += Op.PUSH1(4) + Op.SSTORE  # Slot 4 = position 5 (0x1111, unchanged)
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    post = {
        contract_address: Account(
            storage={
                0: 0x2222,  # Swapped from position 4 to top
                1: 0x4444,  # Unchanged
                2: 0x3333,  # Unchanged
                3: 0x5555,  # Swapped from top to position 4
                4: 0x1111,  # Unchanged
            }
        )
    }

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


def test_swapn_stack_underflow(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """Test SWAPN causes transaction failure on stack underflow."""
    sender = pre.fund_eoa()

    # Push only 5 items but try to SWAPN[5] (needs 7 items: top + 6 more)
    code = Bytecode()
    for i in range(5):
        code += Op.PUSH1(i)
    code += Op.SWAPN[5]  # Should fail - needs 7 items total
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    # Transaction should fail, contract storage unchanged
    post = {contract_address: Account(storage={})}

    state_test(env=Environment(), pre=pre, post=post, tx=tx)
