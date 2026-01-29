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
    code = Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.DUP1 * 15 + Op.DUPN[17]

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

    state_test(pre=pre, post=post, tx=tx)


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
        + Op.SWAPN[17]
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

    state_test(pre=pre, post=post, tx=tx)


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
    code = Op.PUSH1[0x0] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EXCHANGE[b"\x01"]

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

    state_test(pre=pre, post=post, tx=tx)


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
    code = Bytecode(
        Op.SWAPN[b"\x5b"],
        popped_stack_items=0,
        pushed_stack_items=0,
        terminating=True,
    )

    contract_address = pre.deploy_contract(code=code)
    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    # Transaction should fail, storage unchanged
    post = {contract_address: Account(storage={})}

    state_test(pre=pre, post=post, tx=tx)


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
        Op.PUSH1[0x4] + Op.JUMP + Op.DUPN[b"\x5b"],
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

    state_test(pre=pre, post=post, tx=tx)


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
        + Op.EXCHANGE[b"\x01"]
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

    state_test(pre=pre, post=post, tx=tx)


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
    code = Op.PUSH1[0x0] + Op.DUP1 * 15 + Op.DUPN[b"\x00"]

    # This should not execute due to stack underflow
    code += Op.PUSH1(1) + Op.PUSH1(0) + Op.SSTORE
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)
    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    # Transaction should fail, storage unchanged
    post = {contract_address: Account(storage={})}

    state_test(pre=pre, post=post, tx=tx)


def test_vector_dupn_followed_by_jumpdest(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    Test vector: e6005b [DUPN 17, JUMPDEST].

    Verifies that DUPN with immediate 0x00 correctly consumes the immediate
    byte. The 0x5b following the DUPN is a separate JUMPDEST instruction,
    not part of DUPN. decode_single(0x00) = 17, so DUPN duplicates the 17th
    stack item.
    """
    sender = pre.fund_eoa()

    # Push 17 items so DUPN[0x00] (which duplicates position 17) succeeds
    marker_value = 0xBEEF
    code = Bytecode()
    code += Op.PUSH2(marker_value)  # This will be at position 17
    for i in range(16):
        code += Op.PUSH1(i)

    # DUPN with immediate 0x00 followed by JUMPDEST
    # Hex: e6 00 5b
    code += Op.DUPN[17] + Op.JUMPDEST

    # Store the duplicated value (should be marker_value)
    code += Op.PUSH1(0) + Op.SSTORE
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)
    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    # DUPN should duplicate position 17 (marker_value)
    post = {contract_address: Account(storage={0: marker_value})}

    state_test(pre=pre, post=post, tx=tx)


def test_vector_dupn_invalid_0x60(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    Test vector: e6605b [INVALID_DUPN, PUSH1 0x5b].

    DUPN with immediate 0x60 (96) is in the invalid range (91-127).
    Execution should abort with exceptional halt.
    """
    sender = pre.fund_eoa()

    # Push enough items on stack for any potential operation
    code = Bytecode()
    for i in range(235):
        code += Op.PUSH1(i % 256)

    # DUPN with invalid immediate 0x60 - should abort
    # Hex: e6 60 5b
    code += Op.DUPN[b"\x60"]

    # This should never execute due to invalid immediate
    code += Op.PUSH1(0x5B)  # Would be PUSH1 0x5b if we got here
    code += Op.PUSH1(0x42) + Op.PUSH1(0) + Op.SSTORE
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)
    tx = Transaction(to=contract_address, sender=sender, gas_limit=10_000_000)

    # Transaction should fail, storage unchanged
    post = {contract_address: Account(storage={})}

    state_test(pre=pre, post=post, tx=tx)


def test_vector_swapn_invalid_0x61(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    Test vector: e7610000 [INVALID_SWAPN, PUSH2 0x0000].

    SWAPN with immediate 0x61 (97) is in the invalid range (91-127).
    Execution should abort with exceptional halt.
    """
    sender = pre.fund_eoa()

    # Push enough items on stack for any potential operation
    code = Bytecode()
    for i in range(236):
        code += Op.PUSH1(i % 256)

    # SWAPN with invalid immediate 0x61 - should abort
    # Hex: e7 61 00 00
    code += Op.SWAPN[b"\x61"]

    # These bytes would be PUSH2 0x0000 if we got here
    code += Op.PUSH2(0x0000)
    code += Op.PUSH1(0x42) + Op.PUSH1(0) + Op.SSTORE
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)
    tx = Transaction(to=contract_address, sender=sender, gas_limit=10_000_000)

    # Transaction should fail, storage unchanged
    post = {contract_address: Account(storage={})}

    state_test(pre=pre, post=post, tx=tx)


def test_vector_dupn_invalid_0x5f(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    Test vector: e65f [INVALID_DUPN, PUSH0].

    DUPN with immediate 0x5f (95) is in the invalid range (91-127).
    Execution should abort with exceptional halt.
    """
    sender = pre.fund_eoa()

    # Push enough items on stack for any potential operation
    code = Bytecode()
    for i in range(235):
        code += Op.PUSH1(i % 256)

    # DUPN with invalid immediate 0x5f - should abort
    # Hex: e6 5f
    code += Op.DUPN[b"\x5f"]

    # This should never execute
    code += Op.PUSH1(0x42) + Op.PUSH1(0) + Op.SSTORE
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)
    tx = Transaction(to=contract_address, sender=sender, gas_limit=10_000_000)

    # Transaction should fail, storage unchanged
    post = {contract_address: Account(storage={})}

    state_test(pre=pre, post=post, tx=tx)


def test_vector_exchange_0x12(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    Test vector: e812 [EXCHANGE 2 3].

    EXCHANGE with immediate 0x12 (18 decimal).
    decode_pair(18) = (2, 3), swaps positions 3 and 4.
    """
    sender = pre.fund_eoa()

    # Build stack with 4 items: positions 1, 2, 3, 4 from top
    # Values: [top=0x1111, pos2=0x2222, pos3=0x3333, pos4=0x4444]
    code = Bytecode()
    code += Op.PUSH2(0x4444)  # Position 4 (will be swapped)
    code += Op.PUSH2(0x3333)  # Position 3 (will be swapped)
    code += Op.PUSH2(0x2222)  # Position 2
    code += Op.PUSH2(0x1111)  # Position 1 (top)

    # EXCHANGE with immediate 0x12 - swaps positions 3 and 4
    # Hex: e8 12
    code += Op.EXCHANGE[b"\x12"]

    # Store all values to verify the swap
    code += Op.PUSH1(0) + Op.SSTORE  # Position 1 (top)
    code += Op.PUSH1(1) + Op.SSTORE  # Position 2
    code += Op.PUSH1(2) + Op.SSTORE  # Position 3 (was 4)
    code += Op.PUSH1(3) + Op.SSTORE  # Position 4 (was 3)
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)
    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    # After EXCHANGE[0x12]: positions 3 and 4 are swapped
    post = {
        contract_address: Account(
            storage={
                0: 0x1111,  # Position 1 unchanged
                1: 0x2222,  # Position 2 unchanged
                2: 0x4444,  # Position 3 now has value from position 4
                3: 0x3333,  # Position 4 now has value from position 3
            }
        )
    }

    state_test(pre=pre, post=post, tx=tx)


def test_vector_exchange_0xd0(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    Test vector: e8d0 [EXCHANGE 1 19].

    EXCHANGE with immediate 0xd0 (208 decimal).
    decode_pair(208) = (1, 19), swaps positions 2 and 20.
    """
    sender = pre.fund_eoa()

    # Build stack with 20 items
    # Position 2 and position 20 will be swapped
    code = Bytecode()
    code += Op.PUSH2(0xBBBB)  # Position 20 (bottom, will be swapped)
    for i in range(17):
        code += Op.PUSH2(0x1000 + i)  # Positions 3-19
    code += Op.PUSH2(0xAAAA)  # Position 2 (will be swapped)
    code += Op.PUSH2(0x1111)  # Position 1 (top)

    # EXCHANGE with immediate 0xd0 - swaps positions 2 and 20
    # Hex: e8 d0
    code += Op.EXCHANGE[b"\xd0"]

    # Store position 1, 2, and 20 to verify
    code += Op.PUSH1(0) + Op.SSTORE  # Position 1 (top, unchanged)
    code += Op.PUSH1(1) + Op.SSTORE  # Position 2 (was 0xBBBB from pos 20)

    # Pop to get to position 20
    for _ in range(17):
        code += Op.POP

    code += Op.PUSH1(2) + Op.SSTORE  # Position 20 (was 0xAAAA from pos 2)
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)
    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    # After EXCHANGE[0xd0]: positions 2 and 20 are swapped
    post = {
        contract_address: Account(
            storage={
                0: 0x1111,  # Position 1 unchanged
                1: 0xBBBB,  # Position 2 now has value from position 20
                2: 0xAAAA,  # Position 20 now has value from position 2
            }
        )
    }

    state_test(pre=pre, post=post, tx=tx)


def test_vector_exchange_invalid_0x50(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    Test vector: e850 [INVALID_EXCHANGE, POP].

    EXCHANGE with immediate 0x50 (80 decimal) is in the invalid range (80-127).
    Execution should abort with exceptional halt.
    """
    sender = pre.fund_eoa()

    # Push enough items on stack for any potential operation
    code = Bytecode()
    for i in range(30):
        code += Op.PUSH1(i)

    # EXCHANGE with invalid immediate 0x50 - should abort
    # Hex: e8 50
    code += Op.EXCHANGE[b"\x50"]

    # This would be POP if we got here (0x50 = POP opcode)
    code += Op.POP
    code += Op.PUSH1(0x42) + Op.PUSH1(0) + Op.SSTORE
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)
    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    # Transaction should fail, storage unchanged
    post = {contract_address: Account(storage={})}

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "eip8024_opcode,stack_items",
    [
        pytest.param(Op.DUPN, 17, id="dupn"),
        pytest.param(Op.SWAPN, 18, id="swapn"),
        pytest.param(Op.EXCHANGE, 30, id="exchange"),
    ],
)
def test_eip_vector_end_of_code(
    pre: Alloc,
    state_test: StateTestFiller,
    eip8024_opcode: Op,
    stack_items: int,
) -> None:
    """
    Test EIP-8024 opcodes at end of code (no immediate byte).

    When an opcode appears at end of code, code[pc+1] = 0 beyond end of code.
    - DUPN: decode_single(0) = 17, needs 17 items on stack
    - SWAPN: decode_single(0) = 17, needs 18 items on stack
    - EXCHANGE: decode_pair(0) = (1, 29), needs 30 items on stack

    Store a marker before the opcode to verify the transaction succeeded,
    since adding any opcode after would make that opcode byte the immediate.
    """
    sender = pre.fund_eoa()
    marker_value = 0x42

    code = (
        # store marker for verification
        Op.SSTORE(0, marker_value)
        # push minimum required stack items for the opcode
        + Op.PUSH0 * stack_items
        # end-of-code EIP-8024 opcode
        + eip8024_opcode
    )
    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    # verify marker was stored (tx succeeded)
    post = {contract_address: Account(storage={0: marker_value})}
    state_test(pre=pre, post=post, tx=tx)
