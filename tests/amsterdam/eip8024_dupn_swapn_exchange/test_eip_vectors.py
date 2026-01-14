"""
EIP-8024 Official Test Vectors.

Test vectors from the EIP-8024 specification:
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


def test_eip_vector_dupn_duplicate_bottom(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    EIP test vector: 60016000808080808080808080808080808080e600.

    Results in 18 stack items, top=1, bottom=1, rest=0.

    PUSH1 1, PUSH1 0, 15x DUP1, DUPN[0]
    - After 15 DUP1s: 17 items [0,0,0,...,0,1]
    - DUPN[0]: decode_single(0)=17, duplicate position 17 (value 1)
    - Result: 18 items, top=1, bottom=1
    """
    sender = pre.fund_eoa()

    # Build the exact bytecode from the EIP
    code = Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.DUP1 * 15 + Op.DUPN[0x0]

    # After DUPN: 18 items, top=1, bottom=1
    # Verify by storing top value at key 0
    code += Op.PUSH1(0) + Op.SSTORE  # Store top (should be 1) at key 0

    # Pop 16 items to get to bottom 2 items
    code += Op.POP * 16
    # Stack now has 1 item (bottom value = 1)

    # Store bottom value at key 1
    code += Op.PUSH1(1) + Op.SSTORE  # Store bottom (should be 1) at key 1
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)
    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    post = {
        contract_address: Account(
            storage={
                0: 1,  # top = 1 (from DUPN duplicating position 17)
                1: 1,  # bottom = 1 (original PUSH1 1)
            }
        )
    }

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


def test_eip_vector_swapn_swap_with_bottom(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    EIP test vector: 600160008080808080808080808080808080806002e700.

    Results in 18 stack items, top=1, bottom=2, rest=0.

    PUSH1 1, PUSH1 0, 15x DUP1, PUSH1 2, SWAPN[0]
    - After PUSH1 2: 18 items with top=2, bottom=1
    - SWAPN[0]: decode_single(0)=17, swap position 1 with position (17+1)=18
    - Result: 18 items, top=1, bottom=2
    """
    sender = pre.fund_eoa()

    # Build the exact bytecode from the EIP
    code = (
        Op.PUSH1[0x1]
        + Op.PUSH1[0x0]
        + Op.DUP1 * 15
        + Op.PUSH1[0x2]
        + Op.SWAPN[0x0]
    )

    # After SWAPN: 18 items, top=1, bottom=2
    # Verify by storing top value at key 0
    code += Op.PUSH1(0) + Op.SSTORE  # Store top (should be 1) at key 0

    # Pop 16 items to get to bottom 1 item
    code += Op.POP * 16
    # Stack now has 1 item (bottom value = 2)

    # Store bottom value at key 1
    code += Op.PUSH1(1) + Op.SSTORE  # Store bottom (should be 2) at key 1
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)
    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    post = {
        contract_address: Account(
            storage={
                0: 1,  # top = 1 (swapped from bottom)
                1: 2,  # bottom = 2 (swapped from top)
            }
        )
    }

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


def test_eip_vector_exchange_swap_positions(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    EIP test vector: 600060016002e801.

    Results in 3 stack items, from top to bottom: [2, 0, 1].

    PUSH1 0, PUSH1 1, PUSH1 2, EXCHANGE[1]
    - After pushes: [2, 1, 0] (top to bottom)
    - EXCHANGE[1]: decode_pair(1)=(1,2), swap positions 2 and 3
    - Result: [2, 0, 1]
    """
    sender = pre.fund_eoa()

    # Build the exact bytecode from the EIP
    code = Op.PUSH1[0x0] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EXCHANGE[0x1]

    # Store all 3 stack values
    code += Op.PUSH1(0) + Op.SSTORE  # Store position 1 / top (should be 2)
    code += Op.PUSH1(1) + Op.SSTORE  # Store position 2 (should be 0)
    code += Op.PUSH1(2) + Op.SSTORE  # Store position 3 / bottom (should be 1)
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)
    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    post = {
        contract_address: Account(
            storage={
                0: 2,  # top = 2 (unchanged)
                1: 0,  # position 2 = 0 (swapped from position 3)
                2: 1,  # bottom = 1 (swapped from position 2)
            }
        )
    }

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


def test_eip_vector_swapn_invalid_immediate_reverts(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    EIP test vector: e75b reverts.

    SWAPN with immediate 0x5b (91) is in the invalid range (90 < x < 128).
    This should cause an exceptional halt.
    """
    sender = pre.fund_eoa()

    # Build the exact bytecode from the EIP: SWAPN[0x5b]
    # 0x5b = 91 which is in the forbidden range
    # Use raw bytes with stack info (will fail during execution anyway)
    code = Bytecode(
        bytes.fromhex("e75b"),
        popped_stack_items=0,
        pushed_stack_items=0,
        terminating=True,
    )

    contract_address = pre.deploy_contract(code=code)
    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    # Transaction should fail, storage unchanged
    post = {contract_address: Account(storage={})}

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


def test_eip_vector_jump_over_invalid_dupn(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    EIP test vector: 600456e65b executes successfully.

    PUSH1 04, JUMP, DUPN[0x5b]
    - The DUPN at position 2 has immediate 0x5b which would be invalid
    - But we JUMP to position 4 (the 0x5b byte), which is a valid JUMPDEST
    - The DUPN instruction is never executed
    """
    sender = pre.fund_eoa()

    # Build the exact bytecode: PUSH1 04, JUMP, DUPN[0x5b]
    # Position 0: PUSH1 (0x60)
    # Position 1: 0x04
    # Position 2: JUMP (0x56)
    # Position 3: DUPN (0xe6)
    # Position 4: 0x5b (JUMPDEST when executed as opcode)
    code = Bytecode(
        bytes.fromhex("600456e65b"),
        popped_stack_items=0,
        pushed_stack_items=0,
    )

    # After jumping to JUMPDEST, mark success
    code += Op.PUSH1(1) + Op.PUSH1(0) + Op.SSTORE
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)
    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    # Transaction should succeed
    post = {contract_address: Account(storage={0: 1})}

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


def test_eip_vector_exchange_with_iszero(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    EIP test vector: 600060006000e80115.

    Results in 3 stack items, top=1, rest=0.

    PUSH1 0, PUSH1 0, PUSH1 0, EXCHANGE[1], ISZERO
    - After pushes: [0, 0, 0]
    - EXCHANGE[1]: swap positions 2 and 3 (both 0, no visible change)
    - ISZERO: pop 0, push 1
    - Result: [1, 0, 0]
    """
    sender = pre.fund_eoa()

    # Build the exact bytecode from the EIP
    code = (
        Op.PUSH1[0x0]
        + Op.PUSH1[0x0]
        + Op.PUSH1[0x0]
        + Op.EXCHANGE[0x1]
        + Op.ISZERO
    )

    # Store all 3 stack values
    code += Op.PUSH1(0) + Op.SSTORE  # Store top (should be 1)
    code += Op.PUSH1(1) + Op.SSTORE  # Store position 2 (should be 0)
    code += Op.PUSH1(2) + Op.SSTORE  # Store position 3 (should be 0)
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)
    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    post = {
        contract_address: Account(
            storage={
                0: 1,  # top = 1 (from ISZERO)
                1: 0,  # position 2 = 0
                2: 0,  # bottom = 0
            }
        )
    }

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


def test_eip_vector_dupn_stack_underflow(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    EIP test vector: 6000808080808080808080808080808080e600.

    Results in exceptional halt (stack underflow).

    PUSH1 0, 15x DUP1, DUPN[0]
    - After 15 DUP1s: 16 items
    - DUPN[0]: decode_single(0)=17, needs position 17 but only 16 items
    - Result: exceptional halt
    """
    sender = pre.fund_eoa()

    # Build the exact bytecode from the EIP
    code = Op.PUSH1[0x0] + Op.DUP1 * 15 + Op.DUPN[0x0]

    # This should not execute due to stack underflow
    code += Op.PUSH1(1) + Op.PUSH1(0) + Op.SSTORE
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)
    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    # Transaction should fail, storage unchanged
    post = {contract_address: Account(storage={})}

    state_test(env=Environment(), pre=pre, post=post, tx=tx)
