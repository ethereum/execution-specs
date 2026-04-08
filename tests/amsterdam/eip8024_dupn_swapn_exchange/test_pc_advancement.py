"""
Program Counter (PC) advancement tests for EIP-8024 opcodes.

Tests that verify DUPN, SWAPN, and EXCHANGE correctly advance the PC by 2 bytes
(opcode + immediate byte) as specified in
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


def test_dupn_pc_advances_by_2(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    Verify PC advances by 2 after DUPN (opcode + immediate byte).

    Tests that DUPN consumes the immediate byte and advances PC correctly.
    """
    sender = pre.fund_eoa()

    code = Bytecode()

    # Push 17 values so DUPN[17] will work
    for i in range(17):
        code += Op.PUSH1(i)

    # Capture PC before DUPN and store it
    code += Op.PC
    code += Op.PUSH1(1) + Op.SSTORE  # Store PC_before at key 1

    # Execute DUPN - should advance PC by 2 (opcode + immediate)
    code += Op.DUPN[17]

    # Capture PC after DUPN and store it
    code += Op.PC
    code += Op.PUSH1(2) + Op.SSTORE  # Store PC_after at key 2

    # Calculate difference: get both values and subtract
    code += Op.PUSH1(1) + Op.SLOAD  # Load PC_before
    code += Op.PUSH1(2) + Op.SLOAD  # Load PC_after
    code += Op.SUB  # PC_after - PC_before (SUB does: second - top)

    # Store the difference
    code += Op.PUSH1(0) + Op.SSTORE

    # Clean up intermediate storage
    code += Op.PUSH1(0) + Op.PUSH1(1) + Op.SSTORE  # Clear key 1
    code += Op.PUSH1(0) + Op.PUSH1(2) + Op.SSTORE  # Clear key 2

    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)
    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    # The difference should be:
    # PUSH1(2) + SSTORE(1) + DUPN(2) + PC(1) = 6
    # Note: Keys 1 and 2 are used for intermediate storage
    post = {
        contract_address: Account(
            storage={
                0: 6,  # PC_after - PC_before (the main result)
                # Keys 1 and 2 contain PC_before and PC_after for debugging
            }
        )
    }

    state_test(pre=pre, post=post, tx=tx)


def test_swapn_pc_advances_by_2(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    Verify PC advances by 2 after SWAPN (opcode + immediate byte).

    Tests that SWAPN consumes the immediate byte and advances PC correctly.
    """
    sender = pre.fund_eoa()

    code = Bytecode()

    # Push 18 values so SWAPN[17] will work (needs 18 items on stack)
    for i in range(18):
        code += Op.PUSH1(i)

    # Capture PC before SWAPN and store it
    code += Op.PC
    code += Op.PUSH1(1) + Op.SSTORE

    # Execute SWAPN - should advance PC by 2 (opcode + immediate)
    code += Op.SWAPN[17]

    # Capture PC after SWAPN and store it
    code += Op.PC
    code += Op.PUSH1(2) + Op.SSTORE

    # Calculate difference
    code += Op.PUSH1(1) + Op.SLOAD  # Load PC_before
    code += Op.PUSH1(2) + Op.SLOAD  # Load PC_after
    code += Op.SUB  # PC_after - PC_before

    # Store the difference
    code += Op.PUSH1(0) + Op.SSTORE

    # Clean up intermediate storage
    code += Op.PUSH1(0) + Op.PUSH1(1) + Op.SSTORE  # Clear key 1
    code += Op.PUSH1(0) + Op.PUSH1(2) + Op.SSTORE  # Clear key 2

    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)
    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    post = {
        contract_address: Account(
            storage={
                0: 6,  # PUSH1(2) + SSTORE(1) + SWAPN(2) + PC(1) = 6
            }
        )
    }

    state_test(pre=pre, post=post, tx=tx)


def test_exchange_pc_advances_by_2(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    Verify PC advances by 2 after EXCHANGE (opcode + immediate byte).

    Tests that EXCHANGE consumes the immediate byte and advances PC correctly.
    """
    sender = pre.fund_eoa()

    code = Bytecode()

    # Push 6 values so EXCHANGE[1, 5] will work (needs 6 items on stack)
    for i in range(6):
        code += Op.PUSH1(i)

    # Capture PC before EXCHANGE and store it
    code += Op.PC
    code += Op.PUSH1(1) + Op.SSTORE

    # Execute EXCHANGE - should advance PC by 2 (opcode + immediate)
    code += Op.EXCHANGE[1, 5]

    # Capture PC after EXCHANGE and store it
    code += Op.PC
    code += Op.PUSH1(2) + Op.SSTORE

    # Calculate difference
    code += Op.PUSH1(1) + Op.SLOAD  # Load PC_before
    code += Op.PUSH1(2) + Op.SLOAD  # Load PC_after
    code += Op.SUB  # PC_after - PC_before

    # Store the difference
    code += Op.PUSH1(0) + Op.SSTORE

    # Clean up intermediate storage
    code += Op.PUSH1(0) + Op.PUSH1(1) + Op.SSTORE  # Clear key 1
    code += Op.PUSH1(0) + Op.PUSH1(2) + Op.SSTORE  # Clear key 2

    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)
    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    post = {
        contract_address: Account(
            storage={
                0: 6,  # PUSH1(2) + SSTORE(1) + EXCHANGE(2) + PC(1) = 6
            }
        )
    }

    state_test(pre=pre, post=post, tx=tx)


def test_dupn_multiple_consecutive_pc_advancement(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    Verify PC advances correctly with multiple consecutive DUPN opcodes.

    Tests that each DUPN independently advances PC by 2 bytes.
    """
    sender = pre.fund_eoa()

    code = Bytecode()

    # Push enough values for multiple DUPNs
    for i in range(20):
        code += Op.PUSH1(i)

    # Capture initial PC
    code += Op.PC
    code += Op.PUSH1(1) + Op.SSTORE

    # Execute three consecutive DUPNs
    code += Op.DUPN[17]
    code += Op.DUPN[18]
    code += Op.DUPN[19]

    # Capture final PC
    code += Op.PC
    code += Op.PUSH1(2) + Op.SSTORE

    # Calculate difference
    code += Op.PUSH1(1) + Op.SLOAD  # Load PC_before
    code += Op.PUSH1(2) + Op.SLOAD  # Load PC_after
    code += Op.SUB  # PC_after - PC_before

    # Store the difference
    code += Op.PUSH1(0) + Op.SSTORE

    # Clean up intermediate storage
    code += Op.PUSH1(0) + Op.PUSH1(1) + Op.SSTORE  # Clear key 1
    code += Op.PUSH1(0) + Op.PUSH1(2) + Op.SSTORE  # Clear key 2

    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)
    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    post = {
        contract_address: Account(
            storage={
                0: 10,  # PUSH1(2) + SSTORE(1) + DUPN(2)*3 + PC(1) = 10
            }
        )
    }

    state_test(pre=pre, post=post, tx=tx)


def test_mixed_opcodes_pc_advancement(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    Verify PC advances correctly with mixed DUPN, SWAPN, and EXCHANGE opcodes.

    Tests that different EIP-8024 opcodes each correctly advance PC by 2 bytes.
    """
    sender = pre.fund_eoa()

    code = Bytecode()

    # Push enough values for all operations
    for i in range(30):
        code += Op.PUSH1(i)

    # Capture initial PC
    code += Op.PC
    code += Op.PUSH1(1) + Op.SSTORE

    # Execute one of each opcode
    code += Op.DUPN[17]
    code += Op.SWAPN[18]
    code += Op.EXCHANGE[1, 5]

    # Capture final PC
    code += Op.PC
    code += Op.PUSH1(2) + Op.SSTORE

    # Calculate difference
    code += Op.PUSH1(1) + Op.SLOAD  # Load PC_before
    code += Op.PUSH1(2) + Op.SLOAD  # Load PC_after
    code += Op.SUB  # PC_after - PC_before

    # Store the difference
    code += Op.PUSH1(0) + Op.SSTORE

    # Clean up intermediate storage
    code += Op.PUSH1(0) + Op.PUSH1(1) + Op.SSTORE  # Clear key 1
    code += Op.PUSH1(0) + Op.PUSH1(2) + Op.SSTORE  # Clear key 2

    code += Op.STOP

    contract_address = pre.deploy_contract(code=code)
    tx = Transaction(to=contract_address, sender=sender, gas_limit=1_000_000)

    post = {
        contract_address: Account(
            storage={
                # PUSH1(2) + SSTORE(1) + DUPN(2) + SWAPN(2)
                # + EXCHANGE(2) + PC(1) = 10
                0: 10,
            }
        )
    }

    state_test(pre=pre, post=post, tx=tx)
