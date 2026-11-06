"""
Test SHL, SHR and SAR on boundary shift amounts and operand values.

Ported from:
state_tests/stShift/shl01Filler.json
state_tests/stShift/shl01-0100Filler.json
state_tests/stShift/shl01-0101Filler.json
state_tests/stShift/shl01-ffFiller.json
state_tests/stShift/shl10Filler.json
state_tests/stShift/shl11Filler.json
state_tests/stShift/shl_2^255-1_1Filler.json
state_tests/stShift/shl_-1_0Filler.json
state_tests/stShift/shl_-1_1Filler.json
state_tests/stShift/shl_-1_255Filler.json
state_tests/stShift/shl_-1_256Filler.json
state_tests/stShift/shr01Filler.json
state_tests/stShift/shr10Filler.json
state_tests/stShift/shr11Filler.json
state_tests/stShift/shr_2^255_1Filler.json
state_tests/stShift/shr_2^255_255Filler.json
state_tests/stShift/shr_2^255_256Filler.json
state_tests/stShift/shr_2^255_257Filler.json
state_tests/stShift/shr_-1_0Filler.json
state_tests/stShift/shr_-1_1Filler.json
state_tests/stShift/shr_-1_255Filler.json
state_tests/stShift/shr_-1_256Filler.json
state_tests/stShift/sar00Filler.json
state_tests/stShift/sar01Filler.json
state_tests/stShift/sar10Filler.json
state_tests/stShift/sar11Filler.json
state_tests/stShift/sar_0_256-1Filler.json
state_tests/stShift/sar_2^254_254Filler.json
state_tests/stShift/sar_2^255_1Filler.json
state_tests/stShift/sar_2^255_255Filler.json
state_tests/stShift/sar_2^255_256Filler.json
state_tests/stShift/sar_2^255_257Filler.json
state_tests/stShift/sar_2^255-1_248Filler.json
state_tests/stShift/sar_2^255-1_254Filler.json
state_tests/stShift/sar_2^255-1_255Filler.json
state_tests/stShift/sar_2^255-1_256Filler.json
state_tests/stShift/sar_2^256-1_0Filler.json
state_tests/stShift/sar_2^256-1_1Filler.json
state_tests/stShift/sar_2^256-1_255Filler.json
state_tests/stShift/sar_2^256-1_256Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

WORD_MODULUS = 2**256
INITIAL_VALUE = 0xDEADBEEF


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
    [
        "state_tests/stShift/shl01Filler.json",
        "state_tests/stShift/shl01-0100Filler.json",
        "state_tests/stShift/shl01-0101Filler.json",
        "state_tests/stShift/shl01-ffFiller.json",
        "state_tests/stShift/shl10Filler.json",
        "state_tests/stShift/shl11Filler.json",
        "state_tests/stShift/shl_2^255-1_1Filler.json",
        "state_tests/stShift/shl_-1_0Filler.json",
        "state_tests/stShift/shl_-1_1Filler.json",
        "state_tests/stShift/shl_-1_255Filler.json",
        "state_tests/stShift/shl_-1_256Filler.json",
        "state_tests/stShift/shr01Filler.json",
        "state_tests/stShift/shr10Filler.json",
        "state_tests/stShift/shr11Filler.json",
        "state_tests/stShift/shr_2^255_1Filler.json",
        "state_tests/stShift/shr_2^255_255Filler.json",
        "state_tests/stShift/shr_2^255_256Filler.json",
        "state_tests/stShift/shr_2^255_257Filler.json",
        "state_tests/stShift/shr_-1_0Filler.json",
        "state_tests/stShift/shr_-1_1Filler.json",
        "state_tests/stShift/shr_-1_255Filler.json",
        "state_tests/stShift/shr_-1_256Filler.json",
        "state_tests/stShift/sar00Filler.json",
        "state_tests/stShift/sar01Filler.json",
        "state_tests/stShift/sar10Filler.json",
        "state_tests/stShift/sar11Filler.json",
        "state_tests/stShift/sar_0_256-1Filler.json",
        "state_tests/stShift/sar_2^254_254Filler.json",
        "state_tests/stShift/sar_2^255_1Filler.json",
        "state_tests/stShift/sar_2^255_255Filler.json",
        "state_tests/stShift/sar_2^255_256Filler.json",
        "state_tests/stShift/sar_2^255_257Filler.json",
        "state_tests/stShift/sar_2^255-1_248Filler.json",
        "state_tests/stShift/sar_2^255-1_254Filler.json",
        "state_tests/stShift/sar_2^255-1_255Filler.json",
        "state_tests/stShift/sar_2^255-1_256Filler.json",
        "state_tests/stShift/sar_2^256-1_0Filler.json",
        "state_tests/stShift/sar_2^256-1_1Filler.json",
        "state_tests/stShift/sar_2^256-1_255Filler.json",
        "state_tests/stShift/sar_2^256-1_256Filler.json",
    ],
)
@pytest.mark.valid_from("Constantinople")
@pytest.mark.parametrize(
    "opcode, shift, value",
    [
        pytest.param(Op.SHL, 1, 0, id="shl01"),
        pytest.param(Op.SHL, 256, 1, id="shl01_minus_0100"),
        pytest.param(Op.SHL, 257, 1, id="shl01_minus_0101"),
        pytest.param(Op.SHL, 255, 1, id="shl01_minus_ff"),
        pytest.param(Op.SHL, 0, 1, id="shl10"),
        pytest.param(Op.SHL, 1, 1, id="shl11"),
        pytest.param(Op.SHL, 1, 2**255 - 1, id="shl_2_255_minus_1_1"),
        pytest.param(Op.SHL, 0, 2**256 - 1, id="shl_minus_1_0"),
        pytest.param(Op.SHL, 1, 2**256 - 1, id="shl_minus_1_1"),
        pytest.param(Op.SHL, 255, 2**256 - 1, id="shl_minus_1_255"),
        pytest.param(Op.SHL, 256, 2**256 - 1, id="shl_minus_1_256"),
        pytest.param(Op.SHR, 1, 0, id="shr01"),
        pytest.param(Op.SHR, 0, 1, id="shr10"),
        pytest.param(Op.SHR, 1, 1, id="shr11"),
        pytest.param(Op.SHR, 1, 2**255, id="shr_2_255_1"),
        pytest.param(Op.SHR, 255, 2**255, id="shr_2_255_255"),
        pytest.param(Op.SHR, 256, 2**255, id="shr_2_255_256"),
        pytest.param(Op.SHR, 257, 2**255, id="shr_2_255_257"),
        pytest.param(Op.SHR, 0, 2**256 - 1, id="shr_minus_1_0"),
        pytest.param(Op.SHR, 1, 2**256 - 1, id="shr_minus_1_1"),
        pytest.param(Op.SHR, 255, 2**256 - 1, id="shr_minus_1_255"),
        pytest.param(Op.SHR, 256, 2**256 - 1, id="shr_minus_1_256"),
        pytest.param(Op.SAR, 0, 0, id="sar00"),
        pytest.param(Op.SAR, 1, 0, id="sar01"),
        pytest.param(Op.SAR, 0, 1, id="sar10"),
        pytest.param(Op.SAR, 1, 1, id="sar11"),
        pytest.param(Op.SAR, 0, 2**256 - 1, id="sar_0_256_minus_1"),
        pytest.param(Op.SAR, 254, 2**254, id="sar_2_254_254"),
        pytest.param(Op.SAR, 1, 2**255, id="sar_2_255_1"),
        pytest.param(Op.SAR, 255, 2**255, id="sar_2_255_255"),
        pytest.param(Op.SAR, 256, 2**255, id="sar_2_255_256"),
        pytest.param(Op.SAR, 257, 2**255, id="sar_2_255_257"),
        pytest.param(Op.SAR, 248, 2**255 - 1, id="sar_2_255_minus_1_248"),
        pytest.param(Op.SAR, 254, 2**255 - 1, id="sar_2_255_minus_1_254"),
        pytest.param(Op.SAR, 255, 2**255 - 1, id="sar_2_255_minus_1_255"),
        pytest.param(Op.SAR, 256, 2**255 - 1, id="sar_2_255_minus_1_256"),
        pytest.param(Op.SAR, 2**256 - 1, 0, id="sar_2_256_minus_1_0"),
        pytest.param(Op.SAR, 1, 2**256 - 1, id="sar_2_256_minus_1_1"),
        pytest.param(Op.SAR, 255, 2**256 - 1, id="sar_2_256_minus_1_255"),
        pytest.param(Op.SAR, 256, 2**256 - 1, id="sar_2_256_minus_1_256"),
    ],
)
def test_shift(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    shift: int,
    value: int,
) -> None:
    """Store the result of a shift over the given operands."""
    sender = pre.fund_eoa()
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0, value=opcode(shift, value)) + Op.STOP,
        storage={0: INITIAL_VALUE},
    )

    tx = Transaction(
        sender=sender,
        to=target,
        protected=fork.supports_protected_txs(),
    )

    post = {
        target: Account(storage={0: shift_result(opcode, shift, value)}),
    }

    state_test(pre=pre, post=post, tx=tx)
