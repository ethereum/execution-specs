"""
Test EXP opcode.
"""

import pytest
from execution_testing import (
    Alloc,
    Fork,
    Op,
    StateTestFiller,
    gas_test,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.valid_from("Berlin")
@pytest.mark.parametrize(
    "a", [0, 1, pytest.param(2**256 - 1, id="a2to256minus1")]
)
@pytest.mark.parametrize(
    "exponent",
    [
        0,
        1,
        2,
        1023,
        1024,
        pytest.param(2**255, id="exponent2to255"),
        pytest.param(2**256 - 1, id="exponent2to256minus1"),
    ],
)
def test_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    a: int,
    exponent: int,
    fork: Fork,
) -> None:
    """Test that EXP gas works as expected."""
    gas_test(
        fork=fork,
        state_test=state_test,
        pre=pre,
        setup_code=Op.PUSH32(exponent) + Op.PUSH32(a),
        subject_code=Op.EXP(exponent=exponent),
    )
