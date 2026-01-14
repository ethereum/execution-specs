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
    "n,m",
    [
        (1, 1),  # Swap positions 2 and 3
        (1, 2),  # Swap positions 2 and 4
        (2, 1),  # Swap positions 3 and 4
        (1, 15),  # Swap positions 2 and 17
        (15, 1),  # Swap positions 16 and 17
        (8, 8),  # Swap positions 9 and 17
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

    # EXCHANGE swaps position (n+1) with position (n+m+1) (1-indexed from top)
    # We need n+m+1 items on the stack
    pos1 = n + 1  # First swap position (1-indexed)
    pos2 = n + m + 1  # Second swap position (1-indexed)
    stack_height = pos2  # Need at least pos2 items

    value_at_pos1 = 0xAAAA
    value_at_pos2 = 0xBBBB

    # Build stack with known values at swap positions
    code = Bytecode()
    for i in range(stack_height):
        # Stack position is 1-indexed from top, so i=0 is bottom
        stack_pos = stack_height - i  # Position from top (1-indexed)
        if stack_pos == pos1:
            code += Op.PUSH2(value_at_pos1)
        elif stack_pos == pos2:
            code += Op.PUSH2(value_at_pos2)
        else:
            code += Op.PUSH2(0x1000 + i)

    # EXCHANGE[n, m] swaps positions
    code += Op.EXCHANGE[pos1, pos2]

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
        if stack_pos == pos1:
            expected_storage[i] = value_at_pos2  # Now has value from pos2
        elif stack_pos == pos2:
            expected_storage[i] = value_at_pos1  # Now has value from pos1
        else:
            # Original value at this position
            original_i = stack_height - stack_pos
            expected_storage[i] = 0x1000 + original_i

    post = {contract_address: Account(storage=expected_storage)}

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


def test_exchange_preserves_top(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """Test EXCHANGE does not modify the top of stack."""
    sender = pre.fund_eoa()

    # Create a stack with known values
    code = Bytecode()
    code += Op.PUSH2(0x1111)  # Position 5 from top
    code += Op.PUSH2(0x2222)  # Position 4 from top (will be swapped)
    code += Op.PUSH2(0x3333)  # Position 3 from top
    code += Op.PUSH2(0x4444)  # Position 2 from top (will be swapped)
    code += Op.PUSH2(0x5555)  # Position 1 (top, should not be touched)

    # EXCHANGE[2, 4] swaps position 2 with position 4
    code += Op.EXCHANGE[2, 4]

    # Store all values
    code += Op.PUSH1(0) + Op.SSTORE  # Top
    code += Op.PUSH1(1) + Op.SSTORE  # Position 2 (swapped)
    code += Op.PUSH1(2) + Op.SSTORE  # Position 3
    code += Op.PUSH1(3) + Op.SSTORE  # Position 4 (swapped)
    code += Op.PUSH1(4) + Op.SSTORE  # Position 5
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    post = {
        contract_address: Account(
            storage={
                0: 0x5555,  # Top unchanged
                1: 0x2222,  # Was position 4, now at position 2
                2: 0x3333,  # Position 3 unchanged
                3: 0x4444,  # Was position 2, now at position 4
                4: 0x1111,  # Position 5 unchanged
            }
        )
    }

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


def test_exchange_stack_underflow(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """Test EXCHANGE causes transaction failure on stack underflow."""
    sender = pre.fund_eoa()

    # Push only 5 items but try EXCHANGE[2, 4] which needs 6 items
    code = Bytecode()
    for i in range(5):
        code += Op.PUSH1(i)
    code += Op.EXCHANGE[2, 4]  # Needs position 6, should fail
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    # Transaction should fail, contract storage unchanged
    post = {contract_address: Account(storage={})}

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "n,m",
    [
        (1, 1),
        (16, 16),
        (1, 16),
        (16, 1),
    ],
    ids=["min_min", "max_max", "min_max", "max_min"],
)
def test_exchange_immediate_encoding(
    n: int,
    m: int,
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """Test EXCHANGE with boundary immediate values (n and m from 1-16)."""
    sender = pre.fund_eoa()

    pos1 = n + 1
    pos2 = n + m + 1
    stack_height = pos2

    value_at_pos1 = 0xCAFE
    value_at_pos2 = 0xBEEF

    code = Bytecode()
    for i in range(stack_height):
        stack_pos = stack_height - i
        if stack_pos == pos1:
            code += Op.PUSH2(value_at_pos1)
        elif stack_pos == pos2:
            code += Op.PUSH2(value_at_pos2)
        else:
            code += Op.PUSH2(0x1000 + i)

    code += Op.EXCHANGE[pos1, pos2]

    # Just verify the two swapped positions
    # Pop items until we reach pos1
    for _ in range(pos1 - 1):
        code += Op.POP
    code += Op.PUSH1(0) + Op.SSTORE

    # Pop more items to reach pos2
    for _ in range(pos2 - pos1 - 1):
        code += Op.POP
    code += Op.PUSH1(1) + Op.SSTORE

    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    post = {
        contract_address: Account(
            storage={
                0: value_at_pos2,  # pos1 now has value from pos2
                1: value_at_pos1,  # pos2 now has value from pos1
            }
        )
    }

    state_test(env=Environment(), pre=pre, post=post, tx=tx)
