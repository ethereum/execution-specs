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
    Fork,
    Op,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
)

from .spec import ref_spec_8163

REFERENCE_SPEC_GIT_PATH = ref_spec_8163.git_path
REFERENCE_SPEC_VERSION = ref_spec_8163.version

pytestmark = pytest.mark.valid_from("EIP8163")

slot_code_worked = 1
value_code_worked = 0x1234
value_code_untouched = 0xBA5E


@pytest.mark.parametrize(
    "opcode,success,all_gas_consumed",
    [
        pytest.param(Op.EXTENSION, False, True),
        pytest.param(Op.INVALID, False, True),
        pytest.param(Op.REVERT(0, 0), False, False, id="REVERT"),
        pytest.param(Op.JUMPDEST, True, False),
    ],
)
def test_top_level_call(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Bytecode,
    success: bool,
    all_gas_consumed: bool,
) -> None:
    """
    Call a contract whose whole code is the single tested byte.

    EXTENSION behaves as INVALID, JUMPDEST as sanity check.
    """
    contract_address = pre.deploy_contract(code=opcode)

    # One gas more than the code needs, so a normal halt refunds exactly
    # that gas while an exceptional halt consumes it with the rest.
    execution_gas = (
        fork.transaction_intrinsic_cost_calculator()() + opcode.gas_cost(fork)
    )
    gas_limit = execution_gas + 1
    tx = Transaction(
        gas_limit=gas_limit,
        to=contract_address,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(
            status=int(success),
            cumulative_gas_used=(
                gas_limit if all_gas_consumed else execution_gas
            ),
        ),
    )

    state_test(pre=pre, post={}, tx=tx)


@pytest.mark.parametrize(
    "target,valid_jump",
    [
        pytest.param(Op.JUMPDEST, True),
        pytest.param(Op.PUSH1(0x5B), False, id="push_data_0x5b"),
    ],
)
@pytest.mark.parametrize(
    "following",
    [
        pytest.param(Bytecode(), id="nothing"),
        Op.STOP,
        Op.ADD,
        Op.JUMPDEST,
        pytest.param(Op.PUSH1(0), id="PUSH1"),
        pytest.param(Op.PUSH32(0), id="PUSH32"),
        Op.EXTENSION,
        Op.SELFDESTRUCT,
    ],
)
def test_jumpdest_analysis_neutrality(
    state_test: StateTestFiller,
    pre: Alloc,
    following: Bytecode,
    target: Bytecode,
    valid_jump: bool,
) -> None:
    """
    Jump over an EXTENSION byte to a destination right behind it.

    JUMPDEST analysis ignores EXTENSION: a JUMPDEST behind EXTENSION
    is a valid destination and a 0x5b held as PUSH1 data behind
    EXTENSION is not. EXTENSION is never executed. Only JUMPDEST, the
    PUSH opcodes and EXTENSION itself matter to the analysis of the
    byte behind EXTENSION; every other byte is data to it.
    """
    code = (
        Op.SSTORE(slot_code_worked, value_code_worked)
        + Op.JUMP(pc=Op.PUSH2(data_placeholder="destination"))
        + Op.EXTENSION
        + following
        + target
    )
    code.substitute(destination=len(code) - 1)

    contract_address = pre.deploy_contract(
        code=code,
        storage={slot_code_worked: value_code_untouched},
    )

    tx = Transaction(to=contract_address, sender=pre.fund_eoa())

    value = value_code_worked if valid_jump else value_code_untouched
    state_test(
        pre=pre,
        post={contract_address: Account(storage={slot_code_worked: value})},
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
@pytest.mark.parametrize(
    "following",
    [
        pytest.param(bytes([b]), id=f"0x{b:02x}")
        for b in [0x5B, *range(0x60, 0x80)]
    ]
    + [pytest.param(b"", id="nothing")],
)
def test_solo_extension_bytes(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
    success: bool,
    following: bytes,
) -> None:
    """
    Execute the tested byte followed by a solo 0x5b or 0x60..0x7f
    byte (or nothing), expect it to halt exceptionally always.

    EIP-8163 rules these out as single-byte extension immediates.
    The stack is filled first, so the halt is known not to require an
    empty stack.

    EXTENSION behaves as INVALID, JUMPDEST as sanity check.
    """
    code = (
        Op.SSTORE(slot_code_worked, value_code_worked)
        + Op.PUSH1(1) * 256
        + opcode
        + following
    )
    contract_address = pre.deploy_contract(
        code=code,
        storage={slot_code_worked: value_code_untouched},
    )

    tx = Transaction(to=contract_address, sender=pre.fund_eoa())

    value = value_code_worked if success else value_code_untouched
    state_test(
        pre=pre,
        post={contract_address: Account(storage={slot_code_worked: value})},
        tx=tx,
    )
