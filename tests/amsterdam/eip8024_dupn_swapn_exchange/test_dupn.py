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

from .spec import ref_spec_8024

REFERENCE_SPEC_GIT_PATH = ref_spec_8024.git_path
REFERENCE_SPEC_VERSION = ref_spec_8024.version

pytestmark = pytest.mark.valid_from("Amsterdam")


@pytest.mark.parametrize(
    "dupn_operand",
    [0, 1, 15, 16, 127, 255],
    ids=lambda x: f"dupn_{x}",
)
def test_dupn_basic(
    dupn_operand: int,
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """Test DUPN with various immediate operands."""
    sender = pre.fund_eoa()

    # Build stack with enough items, then use DUPN to duplicate the nth item
    # DUPN[n] duplicates the (n+1)th stack item (0-indexed from top)
    stack_height = dupn_operand + 1
    expected_value = 0xBEEF + dupn_operand

    # Push values onto stack: the value at position dupn_operand will be expected_value
    code = Bytecode()
    for i in range(stack_height):
        if i == 0:
            # The first push will end up at position dupn_operand from top
            code += Op.PUSH2(expected_value)
        else:
            code += Op.PUSH2(0x1000 + i)

    # DUPN[dupn_operand] should duplicate the (dupn_operand+1)th item
    code += Op.DUPN[dupn_operand]
    # Store the duplicated value
    code += Op.PUSH1(0) + Op.SSTORE
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    post = {contract_address: Account(storage={0: expected_value})}

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


def test_dupn_all_valid_immediates(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """Test DUPN with all valid immediate values (0-255)."""
    sender = pre.fund_eoa()
    n = 256  # All possible immediates

    # Push 256 values onto the stack
    code = Bytecode()
    for i in range(n):
        code += Op.PUSH2(0xD00 + i)

    # For each position, use DUPN to duplicate and store
    # We'll just test a subset to avoid huge storage
    test_positions = [0, 1, 127, 255]
    for idx, pos in enumerate(test_positions):
        code += Op.DUPN[pos]
        code += Op.PUSH1(idx) + Op.SSTORE

    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender, gas_limit=10_000_000)

    # The stack is: [0xD00, 0xD01, ..., 0xDFF] with 0xDFF at top
    # DUPN[0] duplicates top (0xDFF), DUPN[255] duplicates bottom (0xD00)
    expected_storage = {
        0: 0xD00 + n - 1,  # DUPN[0] = top = 0xDFF
        1: 0xD00 + n - 2,  # DUPN[1] = second from top = 0xDFE
        2: 0xD00 + n - 128,  # DUPN[127]
        3: 0xD00,  # DUPN[255] = bottom = 0xD00
    }

    post = {contract_address: Account(storage=expected_storage)}

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


def test_dupn_stack_underflow(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """Test DUPN causes transaction failure on stack underflow."""
    sender = pre.fund_eoa()

    # Push only 5 items but try to DUPN[5] (needs 6 items)
    code = Bytecode()
    for i in range(5):
        code += Op.PUSH1(i)
    code += Op.DUPN[5]  # Should fail - needs item at position 6
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    # Transaction should fail, contract storage unchanged
    post = {contract_address: Account(storage={})}

    state_test(env=Environment(), pre=pre, post=post, tx=tx)
