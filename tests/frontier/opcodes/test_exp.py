"""
Test EXP opcode.
"""

import pytest
from execution_testing import (
    Alloc,
    Environment,
    Fork,
    Op,
    StateTestFiller,
    gas_test,
)
from execution_testing.base_types.base_types import ZeroPaddedHexNumber

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


def exp_gas(fork: Fork, exponent: int) -> int:
    """Calculate gas cost for EXP opcode given the exponent."""
    byte_len = (exponent.bit_length() + 7) // 8
    return fork.gas_costs().G_EXP + fork.gas_costs().G_EXP_BYTE * byte_len


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
    env: Environment,
) -> None:
    """Test that EXP gas works as expected."""
    warm_gas = exp_gas(fork, exponent)

    if cap := fork.transaction_gas_limit_cap():
        env.gas_limit = ZeroPaddedHexNumber(cap)

    gas_test(
        fork=fork,
        state_test=state_test,
        env=env,
        pre=pre,
        setup_code=Op.PUSH32(exponent) + Op.PUSH32(a),
        subject_code=Op.EXP,
        tear_down_code=Op.STOP,
        cold_gas=warm_gas,
        warm_gas=warm_gas,
    )
