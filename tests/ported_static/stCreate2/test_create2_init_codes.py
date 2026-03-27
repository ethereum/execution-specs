"""
Testing different byte opcodes inside create2 init code.

Ported from:
state_tests/stCreate2/create2InitCodesFiller.json
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
    "60006000536000600160006000f560005500",
    "60566000536000600160006000f560005500",
    "60016000536000600160006000f560005500",
    "60f46000536000600160006000f560005500",
    "6a60016001556001546002556000526000600b60156000f560005500",
    "626001ff60005260006003601d6000f560005500",
    "626001ff60005260006003601d6001f560005500",
    "60006003601d6000f560005500",
    "6160a960005260006002601e6001f560005500",
]
TX_GAS = [800000]
TX_VALUE = [1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stCreate2/create2InitCodesFiller.json"],
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
        pytest.param(
            4,
            0,
            0,
            id="d4",
        ),
        pytest.param(
            5,
            0,
            0,
            id="d5",
        ),
        pytest.param(
            6,
            0,
            0,
            id="d6",
        ),
        pytest.param(
            7,
            0,
            0,
            id="d7",
        ),
        pytest.param(
            8,
            0,
            0,
            id="d8",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create2_init_codes(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Testing different byte opcodes inside create2 init code."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
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

    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address("0x9ccb06046c674d1a423c968d7998235bc33d40c1"): Account(
                    nonce=1
                ),
                sender: Account(nonce=1),
                Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"): Account(
                    storage={0: 0x9CCB06046C674D1A423C968D7998235BC33D40C1},
                ),
            },
        },
        {
            "indexes": {"data": [1, 2, 3], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"): Account(
                    balance=1, nonce=2
                ),
                sender: Account(nonce=1),
            },
        },
        {
            "indexes": {"data": [4], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address("0xd46f8d2a93844fb23d8a2803a615f3d00849b8ab"): Account(
                    storage={1: 1, 2: 1}
                ),
                sender: Account(nonce=1),
            },
        },
        {
            "indexes": {"data": [5], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address(
                    "0xadf52aafb61364f699f9b15ee605ef82dca7f53d"
                ): Account.NONEXISTENT,
                sender: Account(nonce=1),
                Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"): Account(
                    storage={0: 0xADF52AAFB61364F699F9B15EE605EF82DCA7F53D},
                ),
            },
        },
        {
            "indexes": {"data": [6], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address(
                    "0xadf52aafb61364f699f9b15ee605ef82dca7f53d"
                ): Account.NONEXISTENT,
                Address("0x0000000000000000000000000000000000000001"): Account(
                    balance=1
                ),
                sender: Account(nonce=1),
                Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"): Account(
                    storage={0: 0xADF52AAFB61364F699F9B15EE605EF82DCA7F53D},
                ),
            },
        },
        {
            "indexes": {"data": [7], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address("0x52b620d9a3fd03486496061138825a08b4da501f"): Account(
                    nonce=1
                ),
                sender: Account(nonce=1),
                Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"): Account(
                    storage={0: 0x52B620D9A3FD03486496061138825A08B4DA501F},
                ),
            },
        },
        {
            "indexes": {"data": [8], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address("0x5210981ae8161a02a1b7e37452ae142aedc66ea3"): Account(
                    balance=1, nonce=1
                ),
                sender: Account(nonce=1),
                Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"): Account(
                    storage={0: 0x5210981AE8161A02A1B7E37452AE142AEDC66EA3},
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
