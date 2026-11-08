"""
Test_jump_bounds2.

Ported from:
state_tests/stMemoryStressTest/JUMP_Bounds2Filler.json
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
    ["state_tests/stMemoryStressTest/JUMP_Bounds2Filler.json"],
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
def test_jump_bounds2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_jump_bounds2."""
    sender = pre.fund_eoa(amount=0x7FFFFFFFFFFFFFFF)

    # Source: raw
    # 0x63ffffffff5667ffffffffffffffff566fffffffffffffffffffffffffffffffff567fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff56  # noqa: E501
    target_code = (
        Op.JUMP(pc=0xFFFFFFFF)
        + Op.JUMP(pc=0xFFFFFFFFFFFFFFFF)
        + Op.JUMP(pc=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.JUMP(
            pc=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
        )
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
