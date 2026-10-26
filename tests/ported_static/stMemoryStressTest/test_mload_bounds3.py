"""
Test_mload_bounds3.

Ported from:
state_tests/stMemoryStressTest/MLOAD_Bounds3Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

from tests.ported_static.constants import HIGH_GAS_LIMIT

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stMemoryStressTest/MLOAD_Bounds3Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
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
def test_mload_bounds3(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_mload_bounds3."""
    sender = pre.fund_eoa(amount=0x7FFFFFFFFFFFFFFFFFF)

    # Source: lll
    # {  (MLOAD 0x400000) }
    target = pre.deploy_contract(
        code=Op.MLOAD(offset=0x400000) + Op.STOP,
    )

    tx_data = [
        Bytes(""),
    ]
    tx_gas = [35000000, 250000000]
    tx_value = [1]

    env = Environment(gas_limit=HIGH_GAS_LIMIT)

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
    )

    post = {target: Account(balance=1)}

    state_test(env=env, pre=pre, post=post, tx=tx)
