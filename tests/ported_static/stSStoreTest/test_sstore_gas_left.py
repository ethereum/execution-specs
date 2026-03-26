"""
Checks EIP-1706/EIP-2200 out of gas requirement for non-mutating SSTOREs.

Ported from:
state_tests/stSStoreTest/sstore_gasLeftFiller.json
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
    "6000600060006000600073b0409d84ab61455cb8bec14b94f635146ab55613610901f115604b5760006000600060006000734092b3905cfea2485ea53222f41eb26e67587802617530f1505b00",
    "6000600060006000600073b0409d84ab61455cb8bec14b94f635146ab55613610902f115604b5760006000600060006000734092b3905cfea2485ea53222f41eb26e67587802617530f1505b00",
    "6000600060006000600073b0409d84ab61455cb8bec14b94f635146ab55613610903f115604b5760006000600060006000734092b3905cfea2485ea53222f41eb26e67587802617530f1505b00",
    "60016001556000600060006000600073b0409d84ab61455cb8bec14b94f635146ab55613610901f21560505760006000600060006000734092b3905cfea2485ea53222f41eb26e67587802617530f1505b00",
    "60016001556000600060006000600073b0409d84ab61455cb8bec14b94f635146ab55613610902f21560505760006000600060006000734092b3905cfea2485ea53222f41eb26e67587802617530f1505b00",
    "60016001556000600060006000600073b0409d84ab61455cb8bec14b94f635146ab55613610903f21560505760006000600060006000734092b3905cfea2485ea53222f41eb26e67587802617530f1505b00",
    "6001600155600060006000600073b0409d84ab61455cb8bec14b94f635146ab55613610901f415604e5760006000600060006000734092b3905cfea2485ea53222f41eb26e67587802617530f1505b00",
    "6001600155600060006000600073b0409d84ab61455cb8bec14b94f635146ab55613610902f415604e5760006000600060006000734092b3905cfea2485ea53222f41eb26e67587802617530f1505b00",
    "6001600155600060006000600073b0409d84ab61455cb8bec14b94f635146ab55613610903f415604e5760006000600060006000734092b3905cfea2485ea53222f41eb26e67587802617530f1505b00",
]
TX_GAS = [200000]
TX_VALUE = [1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stSStoreTest/sstore_gasLeftFiller.json"],
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
        pytest.param(
            5, 0, 0,
            id="d5",
        ),
        pytest.param(
            6, 0, 0,
            id="d6",
        ),
        pytest.param(
            7, 0, 0,
            id="d7",
        ),
        pytest.param(
            8, 0, 0,
            id="d8",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_sstore_gas_left(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Checks EIP-1706/EIP-2200 out of gas requirement for non-mutating SS..."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52
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
    # Source: lll
    # { [[1]] 1 }
    addr_0xb000000000000000000000000000000000000000 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        storage={1: 1},
        nonce=0,
        address=Address("0xb0409d84ab61455cb8bec14b94f635146ab55613"),  # noqa: E501
    )
    # Source: lll
    # { [[1]] 1 }
    addr_0xc000000000000000000000000000000000000000 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x4092b3905cfea2485ea53222f41eb26e67587802"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': [0, 1, 3, 4, 6, 7], 'gas': 0, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        addr_0xc000000000000000000000000000000000000000: Account(storage={1: 0}),
    },
        },
        {
            "indexes": {'data': [8, 2, 5], 'gas': 0, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        addr_0xc000000000000000000000000000000000000000: Account(storage={1: 1}),
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
