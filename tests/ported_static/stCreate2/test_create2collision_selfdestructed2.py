"""
A contract which performs SUICIDE, and is then attempted to be recreated (different code, same init-code) during the same transaction. This ought to fail, since the code is not cleaned out until after the transaction is ended.

Ported from:
state_tests/stCreate2/create2collisionSelfdestructed2Filler.json
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
    "6000600060006000600073fce41d047b4a1d4450382dcc29ec7e5fedc5f9a361c350f1506b620102036000526003601df36000526000600c60146000f500",
    "6000600060006000600073cff64f4c5df8f436c4f2c1af4b2e3f9e3004c77961c350f1506b626010ff6000526003601df36000526000600c60146000f500",
]
TX_GAS = [400000]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stCreate2/create2collisionSelfdestructed2Filler.json"],
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
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create2collision_selfdestructed2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """A contract which performs SUICIDE, and is then attempted to be recr..."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0xfce41d047b4a1d4450382dcc29ec7e5fedc5f9a3")
    contract_1 = Address("0xcff64f4c5df8f436c4f2c1af4b2e3f9e3004c779")
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
    # { (SELFDESTRUCT 0x10) }
    contract_0 = pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=0x10) + Op.STOP,
        balance=1,
        nonce=0,
        address=Address("0xfce41d047b4a1d4450382dcc29ec7e5fedc5f9a3"),  # noqa: E501
    )
    # Source: raw
    # 0x6010ff
    contract_1 = pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=0x10),
        balance=1,
        nonce=1,
        address=Address("0xcff64f4c5df8f436c4f2c1af4b2e3f9e3004c779"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': 0, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        contract_0: Account(
                storage={},
                code=bytes.fromhex("6010ff00"),
                balance=0,
                nonce=0,
            ),
        Address("0x0000000000000000000000000000000000000010"): Account(balance=1),  # noqa: E501
        sender: Account(nonce=1),
    },
        },
        {
            "indexes": {'data': 1, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        contract_1: Account(balance=0, nonce=1),
        Address("0x0000000000000000000000000000000000000010"): Account(balance=1),  # noqa: E501
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
        nonce=0,
        gas_price=10,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
