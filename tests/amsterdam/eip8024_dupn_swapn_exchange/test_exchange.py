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

from ethereum.forks.amsterdam.vm.stack import decode_pair, encode_pair

from .spec import ref_spec_8024

REFERENCE_SPEC_GIT_PATH = ref_spec_8024.git_path
REFERENCE_SPEC_VERSION = ref_spec_8024.version

pytestmark = pytest.mark.valid_from("Amsterdam")


@pytest.mark.parametrize(
    "n,m",
    [
        (1, 2),  # Swap positions 1 and 2
        (1, 16),  # Swap positions 1 and 16
        (1, 29),  # Swap positions 1 and 29 (n + m = 30)
        (5, 10),  # Swap positions 5 and 10
        (13, 17),  # Swap positions 13 and 17 (n + m = 30)
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

    # EXCHANGE swaps position n with position m
    stack_height = m  # Need at least m items
    value_at_n = 0xAAAA
    value_at_m = 0xBBBB

    # Build stack with known values at swap positions
    code = Bytecode()
    for i in range(stack_height):
        # Stack position is 1-indexed from top, so i=0 is bottom
        stack_pos = stack_height - i  # Position from top (1-indexed)
        if stack_pos == n:
            code += Op.PUSH2(value_at_n)
        elif stack_pos == m:
            code += Op.PUSH2(value_at_m)
        else:
            code += Op.PUSH2(0x1000 + i)

    # Encode the pair to get the immediate byte
    immediate = encode_pair(n, m)
    code += Op.EXCHANGE[immediate]

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
        if stack_pos == n:
            expected_storage[i] = value_at_m  # Now has value from m
        elif stack_pos == m:
            expected_storage[i] = value_at_n  # Now has value from n
        else:
            # Original value at this position
            original_i = stack_height - stack_pos
            expected_storage[i] = 0x1000 + original_i

    post = {contract_address: Account(storage=expected_storage)}

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


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
    n, m = decode_pair(immediate)
    stack_height = m  # Need at least m items
    value_at_n = 0xAAAA
    value_at_m = 0xBBBB

    # Build stack
    code = Bytecode()
    for i in range(stack_height):
        stack_pos = stack_height - i
        if stack_pos == n:
            code += Op.PUSH2(value_at_n)
        elif stack_pos == m:
            code += Op.PUSH2(value_at_m)
        else:
            code += Op.PUSH2(0x1000 + i)

    code += Op.EXCHANGE[immediate]

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
        if stack_pos == n:
            expected_storage[i] = value_at_m
        elif stack_pos == m:
            expected_storage[i] = value_at_n
        else:
            original_i = stack_height - stack_pos
            expected_storage[i] = 0x1000 + original_i

    post = {contract_address: Account(storage=expected_storage)}

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


def test_exchange_preserves_other_items(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """Test EXCHANGE only swaps specified items, leaving others unchanged."""
    sender = pre.fund_eoa()

    # Use n=1, m=5 - swaps positions 1 and 5
    n, m = 1, 5
    immediate = encode_pair(n, m)

    # Create a stack with 5 distinct values
    code = Bytecode()
    code += Op.PUSH2(0x1111)  # Position 5 from top (will be swapped)
    code += Op.PUSH2(0x2222)  # Position 4 from top
    code += Op.PUSH2(0x3333)  # Position 3 from top
    code += Op.PUSH2(0x4444)  # Position 2 from top
    code += Op.PUSH2(0x5555)  # Position 1 (top, will be swapped)

    # EXCHANGE swaps position 1 with position 5
    code += Op.EXCHANGE[immediate]

    # Store all values
    code += Op.PUSH1(0) + Op.SSTORE  # Position 1 (was 0x1111)
    code += Op.PUSH1(1) + Op.SSTORE  # Position 2 (0x4444, unchanged)
    code += Op.PUSH1(2) + Op.SSTORE  # Position 3 (0x3333, unchanged)
    code += Op.PUSH1(3) + Op.SSTORE  # Position 4 (0x2222, unchanged)
    code += Op.PUSH1(4) + Op.SSTORE  # Position 5 (was 0x5555)
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    post = {
        contract_address: Account(
            storage={
                0: 0x1111,  # Was at position 5, now at position 1
                1: 0x4444,  # Position 2 unchanged
                2: 0x3333,  # Position 3 unchanged
                3: 0x2222,  # Position 4 unchanged
                4: 0x5555,  # Was at position 1, now at position 5
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

    # Use n=1, m=5 which needs 5 items, but only push 4
    n, m = 1, 5
    immediate = encode_pair(n, m)

    code = Bytecode()
    for i in range(4):
        code += Op.PUSH1(i)
    code += Op.EXCHANGE[immediate]  # Needs 5 items, should fail
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    # Transaction should fail, contract storage unchanged
    post = {contract_address: Account(storage={})}

    state_test(env=Environment(), pre=pre, post=post, tx=tx)
