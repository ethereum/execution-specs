"""
Test LOGx opcodes.
"""

import pytest
from execution_testing import (
    Alloc,
    Environment,
    StateTestFiller,
)
from execution_testing.base_types.base_types import ZeroPaddedHexNumber
from execution_testing.forks.helpers import Fork
from execution_testing.vm import Opcodes as Op

from tests.unscheduled.eip7692_eof_v1.gas_test import gas_test

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


def log_gas(fork: Fork, topics: int, data_size: int) -> int:
    """
    Calculate gas cost for LOGx opcodes given the number of topics and data
    size.
    """
    return (
        fork.gas_costs().G_LOG
        + fork.gas_costs().G_LOG_TOPIC * topics
        + fork.gas_costs().G_LOG_DATA * data_size
    )


@pytest.mark.valid_from("Berlin")
@pytest.mark.parametrize(
    "opcode,topics",
    [(Op.LOG0, 0), (Op.LOG1, 1), (Op.LOG2, 2), (Op.LOG3, 3), (Op.LOG4, 4)],
)
@pytest.mark.parametrize(
    "data_size",
    [
        0,
        1,
        2,
        1023,
        1024,
    ],
)
def test_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
    topics: int,
    data_size: int,
    fork: Fork,
    env: Environment,
) -> None:
    """Test that LOGx gas works as expected."""
    warm_gas = log_gas(fork, topics, data_size)

    if cap := fork.transaction_gas_limit_cap():
        env.gas_limit = ZeroPaddedHexNumber(cap)
    print(hex(data_size))

    gas_test(
        fork,
        state_test,
        env,
        pre,
        setup_code=Op.MSTORE8(data_size, 0)
        + Op.PUSH1(0) * topics
        + Op.PUSH32(data_size)
        + Op.PUSH1(0),
        subject_code=opcode,
        tear_down_code=Op.STOP,
        cold_gas=warm_gas,
        warm_gas=warm_gas,
        eof=False,
    )
