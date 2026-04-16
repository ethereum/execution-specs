"""
Test_transaction_collision_to_empty_but_code.

Ported from:
state_tests/stCreateTest/TransactionCollisionToEmptyButCodeFiller.json
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
    ["state_tests/stCreateTest/TransactionCollisionToEmptyButCodeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="-g0-v0",
        ),
        pytest.param(
            0,
            0,
            1,
            id="-g0-v1",
        ),
        pytest.param(
            0,
            1,
            0,
            id="-g1-v0",
        ),
        pytest.param(
            0,
            1,
            1,
            id="-g1-v1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_transaction_collision_to_empty_but_code(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_transaction_collision_to_empty_but_code."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x6295EE1B4F6DD65047762F924ECD367C17EABF8F)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xE8D4A51000)
    # Source: raw
    # 0x1122334455
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=bytes.fromhex("1122334455"),
        nonce=0,
        address=Address(0x6295EE1B4F6DD65047762F924ECD367C17EABF8F),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_0: Account(
                    storage={1: 0},
                    code=bytes.fromhex("1122334455"),
                    nonce=0,
                ),
            },
        },
        {
            "indexes": {"data": -1, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_0: Account(
                    storage={},
                    code=bytes.fromhex("1122334455"),
                    nonce=0,
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Op.SSTORE(key=0x1, value=0x1),
    ]
    tx_gas = [600000, 54000]
    tx_value = [0, 1]

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
