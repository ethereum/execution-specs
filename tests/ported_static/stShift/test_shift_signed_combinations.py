"""
Test SHL, SHR and SAR over combinations of large shifts and signed values.

Ported from:
state_tests/stShift/shiftSignedCombinationsFiller.yml
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

WORD_MODULUS = 2**256
INITIAL_VALUE = 0xDEADBEEF

SHIFTS = [5, 2**7, 2**15, 2**31, 2**63, 2**127, 2**255]
VALUES = [
    0,
    1,
    2,
    5,
    0xFE,
    0xFF,
    0x100,
    0x101,
    2**256 - 1,
    2**256 - 2,
    2**255,
    0xA << 252,
    int("55" * 32, 16),
    int("AA" * 32, 16),
]


def shift_result(opcode: Op, shift: int, value: int) -> int:
    """Return the expected result of a shift opcode."""
    if opcode == Op.SHL:
        return (value << shift) % WORD_MODULUS if shift < 256 else 0
    if opcode == Op.SHR:
        return value >> shift if shift < 256 else 0
    if opcode == Op.SAR:
        signed = value - WORD_MODULUS if value >= 2**255 else value
        return (signed >> min(shift, 256)) % WORD_MODULUS
    raise ValueError(f"Unsupported opcode: {opcode}")


@pytest.mark.ported_from(
    ["state_tests/stShift/shiftSignedCombinationsFiller.yml"],
)
@pytest.mark.valid_from("Constantinople")
@pytest.mark.parametrize(
    "opcode",
    [
        pytest.param(Op.SAR, id="sar"),
        pytest.param(Op.SHL, id="shl"),
        pytest.param(Op.SHR, id="shr"),
    ],
)
@pytest.mark.parametrize("shift", SHIFTS, ids=[hex(s) for s in SHIFTS])
def test_shift_signed_combinations(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    shift: int,
) -> None:
    """Store the result of a shift by `shift` for every value in VALUES."""
    sender = pre.fund_eoa()

    code = Bytecode()
    for slot, value in enumerate(VALUES):
        code += Op.SSTORE(key=slot, value=opcode(shift, value))
    target = pre.deploy_contract(
        code=code + Op.STOP,
        storage=dict.fromkeys(range(len(VALUES)), INITIAL_VALUE),
    )

    tx = Transaction(
        sender=sender,
        to=target,
        protected=fork.supports_protected_txs(),
    )

    post = {
        target: Account(
            storage={
                slot: shift_result(opcode, shift, value)
                for slot, value in enumerate(VALUES)
            },
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
