"""
Tests for [EIP-8163: Reserve EXTENSION (0xae) opcode](https://eips.ethereum.org/EIPS/eip-8163).

EXTENSION behaves exactly like INVALID on chains with no extensions
defined for it, Ethereum L1 included, and the byte is neutral to
JUMPDEST analysis everywhere. All assertions here hold on any
EIP-8163-conformant EVM, including chains that define extensions.

These tests do not assert the non-existence of extensions that would
be conformant but are undefined today: there is no way to
forward-guess under what conditions such an extension would succeed,
and no point in testing it.
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

from .spec import ref_spec_8163

REFERENCE_SPEC_GIT_PATH = ref_spec_8163.git_path
REFERENCE_SPEC_VERSION = ref_spec_8163.version

pytestmark = pytest.mark.valid_from("Bogota")

slot_code_worked = 1
value_code_worked = 0x1234


@pytest.mark.parametrize(
    "opcode,success",
    [
        pytest.param(Op.EXTENSION, False),
        pytest.param(Op.INVALID, False),
        pytest.param(Op.JUMPDEST, True),
    ],
)
def test_top_level_call(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
    success: bool,
) -> None:
    """
    Call a contract whose whole code is the single tested byte.

    EXTENSION behaves as INVALID, JUMPDEST as sanity check.
    """
    contract_address = pre.deploy_contract(code=opcode)

    tx = Transaction(
        to=contract_address,
        sender=pre.fund_eoa(),
    )

    state_test(
        pre=pre,
        post={},
        tx=tx,
        expected_receipt_status=int(success),
    )


@pytest.mark.parametrize(
    "opcode,success",
    [
        pytest.param(Op.EXTENSION, False),
        pytest.param(Op.INVALID, False),
        pytest.param(Op.JUMPDEST, True),
    ],
)
@pytest.mark.parametrize("stack_item", [0, 1])
def test_execute_with_stack(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
    success: bool,
    stack_item: int,
) -> None:
    """
    Execute the tested byte with 256 items of value 0 or 1 on the
    stack.

    EXTENSION behaves as INVALID, JUMPDEST as sanity check.
    """
    push = Op.PUSH0 if stack_item == 0 else Op.PUSH1(stack_item)
    code = Op.SSTORE(slot_code_worked, value_code_worked) + push * 256 + opcode
    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=pre.fund_eoa())

    storage = {slot_code_worked: value_code_worked} if success else {}
    state_test(
        pre=pre,
        post={contract_address: Account(storage=storage)},
        tx=tx,
    )


@pytest.mark.parametrize("valid_jump", [True, False])
@pytest.mark.parametrize("following_byte", [None, *range(256)])
def test_jumpdest_analysis_neutrality(
    state_test: StateTestFiller,
    pre: Alloc,
    valid_jump: bool,
    following_byte: int | None,
) -> None:
    """
    Jump over an EXTENSION byte to a destination right behind it.

    JUMPDEST analysis ignores EXTENSION: a JUMPDEST behind EXTENSION
    is a valid destination and a 0x5b held as PUSH1 data behind
    EXTENSION is not. EXTENSION is never executed. The optional byte
    between EXTENSION and the
    destination covers all values, PUSH opcodes with non-truncated
    data, to show none of them acts as an EXTENSION immediate during
    the analysis.
    """
    following = b""
    if following_byte is not None:
        following = bytes([following_byte])
        if 0x60 <= following_byte <= 0x7F:
            push_data_size = following_byte - 0x5F
            following += b"\x00" * push_data_size

    sentinel = Op.SSTORE(slot_code_worked, value_code_worked)
    destination = len(
        sentinel + Op.PUSH2(0) + Op.JUMP + Op.EXTENSION + following
    )
    target: Bytecode
    if valid_jump:
        target = Op.JUMPDEST
    else:
        # point at the 0x5b held as PUSH1 data
        destination += 1
        target = Op.PUSH1(0x5B)
    code = (
        sentinel
        + Op.PUSH2(destination)
        + Op.JUMP
        + Op.EXTENSION
        + following
        + target
    )
    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=pre.fund_eoa())

    storage = {slot_code_worked: value_code_worked} if valid_jump else {}
    state_test(
        pre=pre,
        post={contract_address: Account(storage=storage)},
        tx=tx,
    )


@pytest.mark.parametrize(
    "opcode,success",
    [
        pytest.param(Op.EXTENSION, False),
        pytest.param(Op.INVALID, False),
        pytest.param(Op.JUMPDEST, True),
    ],
)
@pytest.mark.parametrize("stack_item", [0, 1])
@pytest.mark.parametrize(
    "following_byte",
    [pytest.param(b, id=f"0x{b:02x}") for b in [0x5B, *range(0x60, 0x80)]],
)
def test_solo_extension_bytes(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
    success: bool,
    stack_item: int,
    following_byte: int,
) -> None:
    """
    Execute the tested byte followed by a solo 0x5b or 0x60..0x7f
    byte.

    EIP-8163 rules these out as single-byte extension immediates: the
    0x5b stays a valid jump destination.

    EXTENSION behaves as INVALID, JUMPDEST as sanity check.
    """
    push = Op.PUSH0 if stack_item == 0 else Op.PUSH1(stack_item)
    code = (
        Op.SSTORE(slot_code_worked, value_code_worked)
        + push * 256
        + opcode
        + bytes([following_byte])
    )
    contract_address = pre.deploy_contract(code=code)

    tx = Transaction(to=contract_address, sender=pre.fund_eoa())

    storage = {slot_code_worked: value_code_worked} if success else {}
    state_test(
        pre=pre,
        post={contract_address: Account(storage=storage)},
        tx=tx,
    )
