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
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address(0x9CCB06046C674D1A423C968D7998235BC33D40C1): Account(
                    nonce=1
                ),
                sender: Account(nonce=1),
                compute_create_address(address=sender, nonce=0): Account(
                    storage={0: 0x9CCB06046C674D1A423C968D7998235BC33D40C1},
                ),
            },
        },
        {
            "indexes": {"data": [1, 2, 3], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                compute_create_address(address=sender, nonce=0): Account(
                    balance=1, nonce=2
                ),
                sender: Account(nonce=1),
            },
        },
        {
            "indexes": {"data": [4], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address(0xD46F8D2A93844FB23D8A2803A615F3D00849B8AB): Account(
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
                    0xADF52AAFB61364F699F9B15EE605EF82DCA7F53D
                ): Account.NONEXISTENT,
                sender: Account(nonce=1),
                compute_create_address(address=sender, nonce=0): Account(
                    storage={0: 0xADF52AAFB61364F699F9B15EE605EF82DCA7F53D},
                ),
            },
        },
        {
            "indexes": {"data": [6], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address(
                    0xADF52AAFB61364F699F9B15EE605EF82DCA7F53D
                ): Account.NONEXISTENT,
                Address(0x0000000000000000000000000000000000000001): Account(
                    balance=1
                ),
                sender: Account(nonce=1),
                compute_create_address(address=sender, nonce=0): Account(
                    storage={0: 0xADF52AAFB61364F699F9B15EE605EF82DCA7F53D},
                ),
            },
        },
        {
            "indexes": {"data": [7], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address(0x52B620D9A3FD03486496061138825A08B4DA501F): Account(
                    nonce=1
                ),
                sender: Account(nonce=1),
                compute_create_address(address=sender, nonce=0): Account(
                    storage={0: 0x52B620D9A3FD03486496061138825A08B4DA501F},
                ),
            },
        },
        {
            "indexes": {"data": [8], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address(0x5210981AE8161A02A1B7E37452AE142AEDC66EA3): Account(
                    balance=1, nonce=1
                ),
                sender: Account(nonce=1),
                compute_create_address(address=sender, nonce=0): Account(
                    storage={0: 0x5210981AE8161A02A1B7E37452AE142AEDC66EA3},
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Op.MSTORE8(offset=0x0, value=0x0)
        + Op.SSTORE(
            key=0x0,
            value=Op.CREATE2(value=0x0, offset=0x0, size=0x1, salt=0x0),
        )
        + Op.STOP,
        Op.MSTORE8(offset=0x0, value=0x56)
        + Op.SSTORE(
            key=0x0,
            value=Op.CREATE2(value=0x0, offset=0x0, size=0x1, salt=0x0),
        )
        + Op.STOP,
        Op.MSTORE8(offset=0x0, value=0x1)
        + Op.SSTORE(
            key=0x0,
            value=Op.CREATE2(value=0x0, offset=0x0, size=0x1, salt=0x0),
        )
        + Op.STOP,
        Op.MSTORE8(offset=0x0, value=0xF4)
        + Op.SSTORE(
            key=0x0,
            value=Op.CREATE2(value=0x0, offset=0x0, size=0x1, salt=0x0),
        )
        + Op.STOP,
        Op.MSTORE(offset=0x0, value=0x6001600155600154600255)
        + Op.SSTORE(
            key=0x0,
            value=Op.CREATE2(value=0x0, offset=0x15, size=0xB, salt=0x0),
        )
        + Op.STOP,
        Op.MSTORE(offset=0x0, value=0x6001FF)
        + Op.SSTORE(
            key=0x0,
            value=Op.CREATE2(value=0x0, offset=0x1D, size=0x3, salt=0x0),
        )
        + Op.STOP,
        Op.MSTORE(offset=0x0, value=0x6001FF)
        + Op.SSTORE(
            key=0x0,
            value=Op.CREATE2(value=0x1, offset=0x1D, size=0x3, salt=0x0),
        )
        + Op.STOP,
        Op.SSTORE(
            key=0x0,
            value=Op.CREATE2(value=0x0, offset=0x1D, size=0x3, salt=0x0),
        )
        + Op.STOP,
        Op.MSTORE(offset=0x0, value=0x60A9)
        + Op.SSTORE(
            key=0x0,
            value=Op.CREATE2(value=0x1, offset=0x1E, size=0x2, salt=0x0),
        )
        + Op.STOP,
    ]
    tx_gas = [800000]
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
