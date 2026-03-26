"""
Account attempts to send tx to create a contract on a non-empty address

Ported from:
state_tests/stEIP3607/initCollidingWithNonEmptyAccountFiller.yml
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
    "60206000f3",
    "6001600055600080808061271073d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d05af100",
    "60016000556000602081612710f500",
    "600160005560206000612710f000",
    "6001600055600080808073d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d05af400",
]
TX_GAS = [400000]
TX_VALUE = [100000]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stEIP3607/initCollidingWithNonEmptyAccountFiller.yml"],
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
        pytest.param(
            3, 0, 0,
            id="d3",
        ),
        pytest.param(
            4, 0, 0,
            id="d4",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_init_colliding_with_non_empty_account(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Account attempts to send tx to create a contract on a non-empty add..."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f")
    contract_1 = Address("0xd0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0")
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
        gas_limit=71794957647893862,
    )

    pre[coinbase] = Account(balance=0, nonce=1)
    pre[sender] = Account(balance=0xde0b6b3a7640000)
    # Source: raw
    # 0x6000600155
    contract_0 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x0),
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"),  # noqa: E501
    )
    # Source: raw
    # 0x00
    contract_1 = pre.deploy_contract(
        code=Op.STOP,
        nonce=0,
        address=Address("0xd0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': -1, 'gas': 0, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        contract_0: Account(
                storage={},
                code=bytes.fromhex("6000600155"),
                balance=0xde0b6b3a7640000,
                nonce=0,
            ),
        contract_1: Account(balance=0),
        Address("0x05cd8493115c3299094a269e839e2f5f25691785"): Account.NONEXISTENT,  # noqa: E501
        Address("0xa42676447b7cedfa5fde894d1d3df24aab362701"): Account.NONEXISTENT,  # noqa: E501
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
