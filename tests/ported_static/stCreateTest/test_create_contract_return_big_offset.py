"""
Test_create_contract_return_big_offset.

Ported from:
state_tests/stCreateTest/CREATE_ContractRETURNBigOffsetFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stCreateTest/CREATE_ContractRETURNBigOffsetFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1",
        ),
        pytest.param(
            2,
            0,
            0,
            id="d2",
        ),
        pytest.param(
            3,
            0,
            0,
            id="d3",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create_contract_return_big_offset(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_create_contract_return_big_offset."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=89128960,
    )

    pre[sender] = Account(balance=0x9184E72A000)

    tx_data = [
        Op.RETURN(offset=0x74AC2, size=0x10000),
        Op.RETURN(offset=0x74AC2, size=0x51EB8),
        Op.RETURN(offset=0x74AC2, size=0x51EB9),
        Op.RETURN(offset=0x74AC2, size=0xD15BC),
    ]
    tx_gas = [16777216]

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data[d],
        gas_limit=tx_gas[g],
    )

    post = {
        sender: Account(nonce=1),
        compute_create_address(address=sender, nonce=0): Account.NONEXISTENT,
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
