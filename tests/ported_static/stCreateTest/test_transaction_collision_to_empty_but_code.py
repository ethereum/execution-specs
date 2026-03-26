"""
test_transaction_collision_to_empty_but_code

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

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "6001600155",
]
TX_GAS = [600000, 54000]
TX_VALUE = [0, 1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stCreateTest/TransactionCollisionToEmptyButCodeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="-g0-v0",
        ),
        pytest.param(
            0, 0, 1,
            id="-g0-v1",
        ),
        pytest.param(
            0, 1, 0,
            id="-g1-v0",
        ),
        pytest.param(
            0, 1, 1,
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
    """test_transaction_collision_to_empty_but_code"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f")
    sender = EOA(
        key=0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xe8d4a51000)
    # Source: raw
    # 0x1122334455
    contract_0 = pre.deploy_contract(
        code=bytes.fromhex("1122334455"),
        nonce=0,
        address=Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': -1, 'gas': 0, 'value': -1},
            "network": ['>=Cancun'],
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
            "indexes": {'data': -1, 'gas': 1, 'value': -1},
            "network": ['>=Cancun'],
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

    tx = Transaction(
        sender=sender,
        to=None,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        nonce=0,
        gas_price=10,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
