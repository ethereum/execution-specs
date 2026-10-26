"""
Test_jumpi_bounds.

Ported from:
state_tests/stMemoryStressTest/JUMPI_BoundsFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stMemoryStressTest/JUMPI_BoundsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="-g0",
        ),
        pytest.param(
            0,
            1,
            0,
            id="-g1",
        ),
    ],
)
def test_jumpi_bounds(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_jumpi_bounds."""
    sender = pre.fund_eoa(amount=0x7FFFFFFFFFFFFFFF)

    # Source: lll
    # { (JUMPI 0xffffffff 1) (JUMPI 0xffffffffffffffff 1) (JUMPI 0xffffffffffffffffffffffffffffffff 1) (JUMPI 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 1) }  # noqa: E501
    target_code = (
        Op.JUMPI(pc=0xFFFFFFFF, condition=0x1)
        + Op.JUMPI(pc=0xFFFFFFFFFFFFFFFF, condition=0x1)
        + Op.JUMPI(pc=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, condition=0x1)
        + Op.JUMPI(
            pc=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
            condition=0x1,
        )
        + Op.STOP
    )
    target = pre.deploy_contract(
        code=target_code,
    )

    tx_data = [
        Bytes(""),
    ]
    tx_gas = [150000, 16777216]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
    )

    post = {
        target: Account(
            code=target_code,
            balance=0,
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
