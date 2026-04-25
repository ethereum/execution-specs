"""
Test_static_call_bounds2.

Ported from:
state_tests/stMemoryStressTest/static_CALL_Bounds2Filler.json
"""

import pytest
from execution_testing import (
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
    ["state_tests/stMemoryStressTest/static_CALL_Bounds2Filler.json"],
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
def test_static_call_bounds2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_call_bounds2."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(
        amount=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
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
    # { (SSTORE 0 (ADD 1 (SLOAD 0))) }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADD(0x1, Op.SLOAD(key=0x0)))
        + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # {   (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0xfffffff 0xfffffff 0xfffffff 0xfffffff)   }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.STATICCALL(
            gas=0x7FFFFFFFFFFFFFF,
            address=addr,
            args_offset=0xFFFFFFF,
            args_size=0xFFFFFFF,
            ret_offset=0xFFFFFFF,
            ret_size=0xFFFFFFF,
        )
        + Op.STOP,
        nonce=0,
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
        target: Account(balance=0),
        addr: Account(storage={0: 0}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
