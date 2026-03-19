"""
create2 fails with not enough cash (endowment of a new account) + inside...

Ported from:
tests/static/state_tests/stCreate2/create2noCashFiller.json
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

TX_DATA = [
    "6000600060006000600073e2b35478fdd26477cc576dd906e6277761246a3c620249f0f100",  # noqa: E501
    "6000600060006000600173e2b35478fdd26477cc576dd906e6277761246a3c620249f0f100",  # noqa: E501
    "600060006000600073e2b35478fdd26477cc576dd906e6277761246a3c620249f0fa00",
]

TX_GAS = [400000]

TX_VALUE = [1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/stCreate2/create2noCashFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 0, 0, id="case1"),
        pytest.param(2, 0, 0, id="case2"),
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
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
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
    # Source: LLL
    # { (CREATE2 101 0 0 0) }
    contract = pre.deploy_contract(
        code=Op.CREATE2(value=0x65, offset=0x0, size=0x0, salt=0x0) + Op.STOP,
        balance=100,
        nonce=0,
        address=Address("0xe2b35478fdd26477cc576dd906e6277761246a3c"),  # noqa: E501
    )

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": [0, 2], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address(
                    "0x12aaefbc0350a026228076e5369e6ce148ce67be"
                ): Account.NONEXISTENT,
                sender: Account(nonce=1),
                contract: Account(balance=100),
            },
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address("0x12aaefbc0350a026228076e5369e6ce148ce67be"): Account(
                    balance=101
                ),
                sender: Account(nonce=1),
                contract: Account(balance=0),
            },
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=None,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
