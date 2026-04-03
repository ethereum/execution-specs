"""
Test_jumpi_bounds.

Ported from:
state_tests/stMemoryStressTest/JUMPI_BoundsFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
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
@pytest.mark.pre_alloc_mutable
def test_jumpi_bounds(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_jumpi_bounds."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x31B5AF02B012484AE954B3A43943242EDE546A2E76FC0A6ACC17435107C385EB
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    # Source: lll
    # { (JUMPI 0xffffffff 1) (JUMPI 0xffffffffffffffff 1) (JUMPI 0xffffffffffffffffffffffffffffffff 1) (JUMPI 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 1) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(pc=0xFFFFFFFF, condition=0x1)
        + Op.JUMPI(pc=0xFFFFFFFFFFFFFFFF, condition=0x1)
        + Op.JUMPI(pc=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, condition=0x1)
        + Op.JUMPI(
            pc=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
            condition=0x1,
        )
        + Op.STOP,
        nonce=0,
        address=Address(0x147F3300E29F2F09880E97B81F7B3EBCF78863E9),  # noqa: E501
    )
    pre[sender] = Account(balance=0x7FFFFFFFFFFFFFFF)

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
            code=bytes.fromhex(
                "600163ffffffff57600167ffffffffffffffff5760016fffffffffffffffffffffffffffffffff5760017fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff5700"  # noqa: E501
            ),
            balance=0,
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
