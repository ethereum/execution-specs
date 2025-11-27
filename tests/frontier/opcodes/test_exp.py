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


def exp_gas(fork: Fork, exponent: int) -> int:
    """Calculate gas cost for EXP opcode given the exponent."""
    gas_costs = fork.gas_costs()
    byte_len = (exponent.bit_length() + 7) // 8
    return gas_costs.G_EXP + gas_costs.G_EXP_BYTE * byte_len


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
    gas_cost = exp_gas(fork, exponent)

    gas_test(
        fork=fork,
        state_test=state_test,
        pre=pre,
        setup_code=Op.PUSH32(exponent) + Op.PUSH32(a),
        subject_code=Op.EXP,
        cold_gas=gas_cost,
        warm_gas=gas_cost,
    )
