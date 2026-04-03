"""
Test_mload_bounds.

Ported from:
state_tests/stMemoryStressTest/MLOAD_BoundsFiller.json
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
    ["state_tests/stMemoryStressTest/MLOAD_BoundsFiller.json"],
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
def test_mload_bounds(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_mload_bounds."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xFE5BE118AD5955E30E0FFC4E1F1BBDCAA7F5A67CB1426C4AC19E32C80ECCDC06
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
    # { (MLOAD 0) (MLOAD 0xffffffff) }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.POP(Op.MLOAD(offset=0x0))
        + Op.MLOAD(offset=0xFFFFFFFF)
        + Op.STOP,
        nonce=0,
        address=Address(0x8B0647E983082E6923F7B20E38972690FCE91E9B),  # noqa: E501
    )
    pre[sender] = Account(balance=0x7FFFFFFFFFFFFFFFFFF)

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

    post = {target: Account(balance=0)}

    state_test(env=env, pre=pre, post=post, tx=tx)
