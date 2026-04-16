"""
Create2 fails with not enough cash (endowment of a new account) +...

Ported from:
state_tests/stCreate2/create2noCashFiller.json
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
)
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stCreate2/create2noCashFiller.json"],
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
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create2no_cash(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Create2 fails with not enough cash (endowment of a new account) +..."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0xE2B35478FDD26477CC576DD906E6277761246A3C)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: lll
    # { (CREATE2 101 0 0 0) }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.CREATE2(value=0x65, offset=0x0, size=0x0, salt=0x0) + Op.STOP,
        balance=100,
        nonce=0,
        address=Address(0xE2B35478FDD26477CC576DD906E6277761246A3C),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0, 2], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(balance=100),
                Address(
                    0x12AAEFBC0350A026228076E5369E6CE148CE67BE
                ): Account.NONEXISTENT,
                sender: Account(nonce=1),
            },
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(balance=0),
                Address(0x12AAEFBC0350A026228076E5369E6CE148CE67BE): Account(
                    balance=101
                ),
                sender: Account(nonce=1),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Op.CALL(
            gas=0x249F0,
            address=contract_0,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.CALL(
            gas=0x249F0,
            address=contract_0,
            value=0x1,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.STATICCALL(
            gas=0x249F0,
            address=contract_0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
    ]
    tx_gas = [400000]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
