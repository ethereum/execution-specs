"""
Create fails because we try to send more wei to it that we have.

Ported from:
state_tests/stCallCreateCallCodeTest/createFailBalanceTooLowFiller.json
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
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stCallCreateCallCodeTest/createFailBalanceTooLowFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="-v0",
        ),
        pytest.param(
            0,
            0,
            1,
            id="-v1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create_fail_balance_too_low(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Create fails because we try to send more wei to it that we have."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x095E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: lll
    # {(MSTORE 0 0x6001600255 ) (SELFDESTRUCT (CREATE 1000000000000000024 27 5)) }  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0x6001600255)
        + Op.SELFDESTRUCT(
            address=Op.CREATE(value=0xDE0B6B3A7640018, offset=0x1B, size=0x5)
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x095E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": -1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                Address(0x0000000000000000000000000000000000000000): Account(
                    storage={}
                ),
                compute_create_address(
                    address=contract_0, nonce=0
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": -1, "gas": -1, "value": 1},
            "network": [">=Cancun"],
            "result": {
                Address(
                    0x0000000000000000000000000000000000000000
                ): Account.NONEXISTENT,
                compute_create_address(address=contract_0, nonce=0): Account(
                    storage={2: 1}
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes(""),
    ]
    tx_gas = [253021]
    tx_value = [23, 24]

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
