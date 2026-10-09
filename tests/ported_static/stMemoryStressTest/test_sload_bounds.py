"""
Test_sload_bounds.

Ported from:
state_tests/stMemoryStressTest/SLOAD_BoundsFiller.json
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
    ["state_tests/stMemoryStressTest/SLOAD_BoundsFiller.json"],
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
def test_sload_bounds(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_sload_bounds."""
    sender = pre.fund_eoa(amount=0x7FFFFFFFFFFFFFFFFFF)

    # Source: lll
    # { (SLOAD 0) (SLOAD 0xffffffff) (SLOAD 0xffffffffffffffff) (SLOAD 0xffffffffffffffffffffffffffffffff) (SLOAD 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.POP(Op.SLOAD(key=0x0))
        + Op.POP(Op.SLOAD(key=0xFFFFFFFF))
        + Op.POP(Op.SLOAD(key=0xFFFFFFFFFFFFFFFF))
        + Op.POP(Op.SLOAD(key=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF))
        + Op.SLOAD(
            key=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
        )
        + Op.STOP,
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

    post = {target: Account(balance=1)}

    state_test(pre=pre, post=post, tx=tx)
