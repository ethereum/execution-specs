"""
create2 fails with not enough cash (endowment of a new account) + inside staticcall

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
from execution_testing.vm import Op
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "6000600060006000600073e2b35478fdd26477cc576dd906e6277761246a3c620249f0f100",
    "6000600060006000600173e2b35478fdd26477cc576dd906e6277761246a3c620249f0f100",
    "600060006000600073e2b35478fdd26477cc576dd906e6277761246a3c620249f0fa00",
]
TX_GAS = [400000]
TX_VALUE = [1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stCreate2/create2noCashFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="d0",
        ),
        pytest.param(
            1, 0, 0,
            id="d1",
        ),
        pytest.param(
            2, 0, 0,
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
    """create2 fails with not enough cash (endowment of a new account) + i..."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0xe2b35478fdd26477cc576dd906e6277761246a3c")
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
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0xde0b6b3a7640000)
    # Source: lll
    # { (CREATE2 101 0 0 0) }
    contract_0 = pre.deploy_contract(
        code=Op.CREATE2(value=0x65, offset=0x0, size=0x0, salt=0x0) + Op.STOP,
        balance=100,
        nonce=0,
        address=Address("0xe2b35478fdd26477cc576dd906e6277761246a3c"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': [0, 2], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        contract_0: Account(balance=100),
        Address("0x12aaefbc0350a026228076e5369e6ce148ce67be"): Account.NONEXISTENT,  # noqa: E501
        sender: Account(nonce=1),
    },
        },
        {
            "indexes": {'data': 1, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        contract_0: Account(balance=0),
        Address("0x12aaefbc0350a026228076e5369e6ce148ce67be"): Account(balance=101),  # noqa: E501
        sender: Account(nonce=1),
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
