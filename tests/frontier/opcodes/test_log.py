"""
Test LOGx opcodes.
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
) -> None:
    """Test that LOGx gas works as expected."""
    gas_test(
        fork=fork,
        state_test=state_test,
        pre=pre,
        setup_code=Op.MSTORE8(data_size, 0)
        + Op.PUSH1(0) * topics
        + Op.PUSH32(data_size)
        + Op.PUSH1(0),
        subject_code=opcode(data_size=data_size),
    )
