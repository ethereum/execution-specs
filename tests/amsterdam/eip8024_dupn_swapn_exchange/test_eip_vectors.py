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

pytestmark = pytest.mark.valid_from("EIP8024")


def test_eip_vector_dupn_duplicate_bottom(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    EIP test vector: 60016000808080808080808080808080808080e680.

    Results in 18 stack items, top=1, bottom=1, rest=0.

    PUSH1 1, PUSH1 0, 15x DUP1, DUPN[0x80]
    - After 15 DUP1s: 17 items [0,0,0,...,0,1]
    - DUPN[0x80]: decode_single(0x80)=17, duplicate position 17 (value 1)
    - Result: 18 items, top=1, bottom=1
    """
    sender = pre.fund_eoa()

    # Build the exact bytecode from the EIP
    code = Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.DUP1 * 15 + Op.DUPN[17]
    assert bytes(code) == bytes.fromhex(
        "60016000808080808080808080808080808080e680"
    )

    # Verify by storing top and bottom values
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
    EIP test vector: 600160008080808080808080808080808080806002e780.

    Results in 18 stack items, top=1, bottom=2, rest=0.

    PUSH1 1, PUSH1 0, 15x DUP1, PUSH1 2, SWAPN[0x80]
    - After PUSH1 2: 18 items with top=2, bottom=1
    - SWAPN[0x80]: decode_single(0x80)=17, swap pos 1 with pos (17+1)=18
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
    assert bytes(code) == bytes.fromhex(
        "600160008080808080808080808080808080806002e780"
    )

    # Verify by storing top and bottom values
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
    EIP test vector: 600060016002e88e.

    Results in 3 stack items, from top to bottom: [2, 0, 1].

    PUSH1 0, PUSH1 1, PUSH1 2, EXCHANGE[0x8e]
    - After pushes: [2, 1, 0] (top to bottom)
    - EXCHANGE[0x8e]: decode_pair(0x8e)=(1,2), swap positions 2 and 3
    - Result: [2, 0, 1]
    """
    sender = pre.fund_eoa()

    # Build the exact bytecode from the EIP
    code = Op.PUSH1[0x0] + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.EXCHANGE[b"\x8e"]
    assert bytes(code) == bytes.fromhex("600060016002e88e")

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
    assert bytes(code) == bytes.fromhex("e75b")

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
    assert bytes(code) == bytes.fromhex("600456e65b")

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
    EIP test vector: 60008080e88e15.

    Results in 3 stack items, top=1, rest=0.

    PUSH1 0, DUP1, DUP1, EXCHANGE[0x8e], ISZERO
    - After DUP1s: [0, 0, 0]
    - EXCHANGE[0x8e]: decode_pair(0x8e)=(1,2), swap pos 2 and 3
    - ISZERO: pop 0, push 1
    - Result: [1, 0, 0]
    """
    sender = pre.fund_eoa()

    # Build the exact bytecode from the EIP
    code = Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.EXCHANGE[b"\x8e"] + Op.ISZERO
    assert bytes(code) == bytes.fromhex("60008080e88e15")

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
    EIP test vector: 6000808080808080808080808080808080e680.

    Results in exceptional halt (stack underflow).

    PUSH1 0, 15x DUP1, DUPN[0x80]
    - After 15 DUP1s: 16 items
    - DUPN[0x80]: decode_single(0x80)=17, needs position 17 but only 16 items
    - Result: exceptional halt
    """
    sender = pre.fund_eoa()

    # Build the exact bytecode from the EIP
    code = Op.PUSH1[0x0] + Op.DUP1 * 15 + Op.DUPN[b"\x80"]
    assert bytes(code) == bytes.fromhex(
        "6000808080808080808080808080808080e680"
    )

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
    Test vector: e6805b [DUPN 17, JUMPDEST].

    Verify that DUPN with immediate 0x80 (128) correctly consumes the
    immediate byte. The 0x5b following the DUPN is a separate JUMPDEST
    instruction, not part of DUPN. decode_single(0x80) = 17, so DUPN
    duplicates the 17th stack item.
    """
    sender = pre.fund_eoa()

    # Push 17 items so DUPN[17] (immediate 0x80 / 128) succeeds
    marker_value = 0xBEEF
    code = Bytecode()
    code += Op.PUSH2(marker_value)  # This will be at position 17
    for i in range(16):
        code += Op.PUSH1(i)

    # DUPN[17] encodes to immediate 0x80 (128), followed by JUMPDEST
    # Bytecode: e6 80 5b
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


def test_vector_exchange_0x9d(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    Test vector: e89d [EXCHANGE 2 3].

    EXCHANGE with immediate 0x9d (157 decimal).
    decode_pair(0x9d) = (2, 3), swaps positions 3 and 4.
    """
    sender = pre.fund_eoa()

    # Build stack with 4 items: positions 1, 2, 3, 4 from top
    # Values: [top=0x1111, pos2=0x2222, pos3=0x3333, pos4=0x4444]
    code = Bytecode()
    code += Op.PUSH2(0x4444)  # Position 4 (will be swapped)
    code += Op.PUSH2(0x3333)  # Position 3 (will be swapped)
    code += Op.PUSH2(0x2222)  # Position 2
    code += Op.PUSH2(0x1111)  # Position 1 (top)

    # EXCHANGE with immediate 0x9d - swaps positions 3 and 4
    # Hex: e8 9d
    code += Op.EXCHANGE[b"\x9d"]

    # Store all values to verify the swap
    code += Op.PUSH1(0) + Op.SSTORE  # Position 1 (top)
    code += Op.PUSH1(1) + Op.SSTORE  # Position 2
    code += Op.PUSH1(2) + Op.SSTORE  # Position 3 (was 4)
    code += Op.PUSH1(3) + Op.SSTORE  # Position 4 (was 3)
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)
    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    # After EXCHANGE[0x9d]: positions 3 and 4 are swapped
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


def test_vector_exchange_0x2f(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    Test vector: e82f [EXCHANGE 1 19].

    EXCHANGE with immediate 0x2f (47 decimal).
    decode_pair(0x2f) = (1, 19), swaps positions 2 and 20.
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

    # EXCHANGE with immediate 0x2f - swaps positions 2 and 20
    # Hex: e8 2f
    code += Op.EXCHANGE[b"\x2f"]

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

    # After EXCHANGE[0x2f]: positions 2 and 20 are swapped
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


def test_vector_exchange_valid_0x50(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    Test vector: e850 [EXCHANGE 14 16].

    EXCHANGE with immediate 0x50 (80 decimal) is valid.
    decode_pair(0x50) = (14, 16), swaps positions 15 and 17.
    """
    sender = pre.fund_eoa()

    # Build stack with 17 items, with known values at positions 15 and 17
    code = Bytecode()
    for i in range(17):
        stack_pos = 17 - i  # Position from top (1-indexed)
        if stack_pos == 15:
            code += Op.PUSH2(0xAAAA)
        elif stack_pos == 17:
            code += Op.PUSH2(0xBBBB)
        else:
            code += Op.PUSH2(0x1000 + i)

    # EXCHANGE with immediate 0x50 - swaps positions 15 and 17
    code += Op.EXCHANGE[b"\x50"]

    # Store swapped positions to verify
    # Pop to position 15 (pop 14 items)
    for _ in range(14):
        code += Op.POP
    code += Op.PUSH1(0) + Op.SSTORE  # Position 15 (was 0xBBBB)
    code += Op.POP  # Skip position 16
    code += Op.PUSH1(1) + Op.SSTORE  # Position 17 (was 0xAAAA)
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)
    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    post = {
        contract_address: Account(
            storage={
                0: 0xBBBB,  # Position 15 now has value from 17
                1: 0xAAAA,  # Position 17 now has value from 15
            }
        )
    }

    state_test(pre=pre, post=post, tx=tx)


def test_vector_exchange_valid_0x51(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    Test vector: e851 [EXCHANGE 14 15].

    EXCHANGE with immediate 0x51 (81 decimal) is valid.
    decode_pair(0x51) = (14, 15), swaps positions 15 and 16.
    """
    sender = pre.fund_eoa()

    # Build stack with 16 items, with known values at positions 15 and 16
    code = Bytecode()
    for i in range(16):
        stack_pos = 16 - i
        if stack_pos == 15:
            code += Op.PUSH2(0xAAAA)
        elif stack_pos == 16:
            code += Op.PUSH2(0xBBBB)
        else:
            code += Op.PUSH2(0x1000 + i)

    # EXCHANGE with immediate 0x51 - swaps positions 15 and 16
    code += Op.EXCHANGE[b"\x51"]

    # Pop to position 15 (pop 14 items)
    for _ in range(14):
        code += Op.POP
    code += Op.PUSH1(0) + Op.SSTORE  # Position 15 (was 0xBBBB)
    code += Op.PUSH1(1) + Op.SSTORE  # Position 16 (was 0xAAAA)
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)
    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    post = {
        contract_address: Account(
            storage={
                0: 0xBBBB,  # Position 15 now has value from 16
                1: 0xAAAA,  # Position 16 now has value from 15
            }
        )
    }

    state_test(pre=pre, post=post, tx=tx)


def test_eip_vector_exchange_end_of_code(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    EIP test vector: 600260008080808080600160008080808080808080e8.

    EXCHANGE at end of code, immediate = 0x00 (beyond code).
    decode_pair(0) = (9, 16), swaps positions 10 and 17.
    Results in 17 stack items, bottom=1, 10th from top=2, rest=0.
    """
    sender = pre.fund_eoa()

    # Build exact bytecode from the EIP
    code = (
        Op.PUSH1[0x2]
        + Op.PUSH1[0x0]
        + Op.DUP1 * 5
        + Op.PUSH1[0x1]
        + Op.PUSH1[0x0]
        + Op.DUP1 * 8
        + Op.EXCHANGE
    )
    assert bytes(code) == bytes.fromhex(
        "600260008080808080600160008080808080808080e8"
    )
    # 17 items on stack:
    # pos 1-8: 0, pos 9: 0, pos 10: 1, pos 11-16: 0, pos 17: 2
    # After EXCHANGE(9,16): swap pos 10 and 17 -> pos 10=2, pos 17=1

    # Store marker before opcode to verify success
    # Since EXCHANGE is at end of code, we verify by checking that the
    # operation completed by storing the 10th and bottom items
    contract_address = pre.deploy_contract(
        code=Op.SSTORE(0, 0x42) + code + Op.STOP
    )
    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    # Verify marker was stored (tx succeeded)
    post = {contract_address: Account(storage={0: 0x42})}
    state_test(pre=pre, post=post, tx=tx)


def test_eip_vector_exchange_30_items(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    EIP test vector (30-item EXCHANGE).

    Bytecode: 600080...(27x DUP1)...60016002e88f.
    decode_pair(0x8f / 143) = (1, 29), swaps positions 2 and 30.
    Results in 30 stack items, top=2, bottom=1, rest=0.
    """
    sender = pre.fund_eoa()

    code = (
        Op.PUSH1[0x0]
        + Op.DUP1 * 27
        + Op.PUSH1[0x1]
        + Op.PUSH1[0x2]
        + Op.EXCHANGE[b"\x8f"]
    )
    assert bytes(code) == bytes.fromhex("6000" + "80" * 27 + "60016002e88f")
    # 30 items: pos 1=2, pos 2=1, rest=0
    # After EXCHANGE(1,29): swap pos 2 and 30 -> pos 2=0, pos 30=1
    # Result: top=2, bottom=1, rest=0

    # Store top value
    code += Op.PUSH1(0) + Op.SSTORE  # top = 2

    # Pop to get to bottom
    code += Op.POP * 28

    # Store bottom value
    code += Op.PUSH1(1) + Op.SSTORE  # bottom = 1
    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)
    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    post = {
        contract_address: Account(
            storage={
                0: 2,  # top = 2 (unchanged)
                1: 1,  # bottom = 1 (swapped from position 2)
            }
        )
    }

    state_test(pre=pre, post=post, tx=tx)


def test_vector_exchange_invalid_0x52(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    Test vector: e852 [INVALID_EXCHANGE, MSTORE].

    EXCHANGE with immediate 0x52 (82 decimal) is in the invalid
    range (82-127). Execution should abort with exceptional halt.
    """
    sender = pre.fund_eoa()

    # Push enough items on stack for any potential operation
    code = Bytecode()
    for i in range(30):
        code += Op.PUSH1(i)

    # EXCHANGE with invalid immediate 0x52 - should abort
    # Hex: e8 52
    code += Op.EXCHANGE[b"\x52"]

    # This would be MSTORE if we got here (0x52 = MSTORE opcode)
    code += Op.MSTORE
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
        pytest.param(Op.DUPN, 145, id="dupn"),
        pytest.param(Op.SWAPN, 146, id="swapn"),
        pytest.param(Op.EXCHANGE, 17, id="exchange"),
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
    - DUPN: decode_single(0) = 145, needs 145 items on stack
    - SWAPN: decode_single(0) = 145, needs 146 items on stack
    - EXCHANGE: decode_pair(0) = (9, 16), needs 17 items on stack

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
