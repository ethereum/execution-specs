"""
Test_mload32bit_bound_return.

Ported from:
state_tests/stMemoryStressTest/mload32bitBound_returnFiller.json
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
    ["state_tests/stMemoryStressTest/mload32bitBound_returnFiller.json"],
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
def test_mload32bit_bound_return(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_mload32bit_bound_return."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0x186A0C3B1E19A180)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=17592320524892,
    )

    # Source: lll
    # { (RETURN 0 4294967295) }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.RETURN(offset=0x0, size=0xFFFFFFFF) + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
    )

    tx_data = [
        Bytes(""),
    ]
    tx_gas = [150000, 16777216]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
    )

    post = {target: Account(storage={})}

    state_test(env=env, pre=pre, post=post, tx=tx)
