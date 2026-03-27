"""
Change X -> 0.

Ported from:
state_tests/stSStoreTest/sstore_Xto0Filler.json
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
    "6000600060006000600073b000000000000000000000000000000000000000620493e0f1506000600060006000600073dea0000000000000000000000000000000000000620927c0f100",  # noqa: E501
    "6000600060006000600073b000000000000000000000000000000000000000620493e0f2506000600060006000600073dea0000000000000000000000000000000000000620927c0f100",  # noqa: E501
    "600060006000600073b000000000000000000000000000000000000000620493e0f4506000600060006000600073dea0000000000000000000000000000000000000620927c0f100",  # noqa: E501
    "600060006000600073c000000000000000000000000000000000000000620493e0fa506000600060006000600073dea0000000000000000000000000000000000000620927c0f100",  # noqa: E501
    "6000601080603860003960006000f5506000600060006000600073dea0000000000000000000000000000000000000620927c0f1500000fe60016000556000600055600160015500",  # noqa: E501
    "6000600060006000600073b000000000000000000000000000000000000000620493e0f1506000600060006000600073dea0000000000000000000000000000000000000620927c0f15060206000fd00",  # noqa: E501
    "6000600060006000600073b000000000000000000000000000000000000000620493e0f2506000600060006000600073dea0000000000000000000000000000000000000620927c0f15060206000fd00",  # noqa: E501
    "600060006000600073b000000000000000000000000000000000000000620493e0f4506000600060006000600073dea0000000000000000000000000000000000000620927c0f15060206000fd00",  # noqa: E501
    "600060006000600073c000000000000000000000000000000000000000620493e0fa506000600060006000600073dea0000000000000000000000000000000000000620927c0f15060206000fd00",  # noqa: E501
    "6000601080603d60003960006000f5506000600060006000600073dea0000000000000000000000000000000000000620927c0f15060206000fd0000fe60016000556000600055600160015500",  # noqa: E501
]
TX_GAS = [3000000, 400000]
TX_VALUE = [1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stSStoreTest/sstore_Xto0Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0-g0",
        ),
        pytest.param(
            0,
            1,
            0,
            id="d0-g1",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1-g0",
        ),
        pytest.param(
            1,
            1,
            0,
            id="d1-g1",
        ),
        pytest.param(
            2,
            0,
            0,
            id="d2-g0",
        ),
        pytest.param(
            2,
            1,
            0,
            id="d2-g1",
        ),
        pytest.param(
            3,
            0,
            0,
            id="d3-g0",
        ),
        pytest.param(
            3,
            1,
            0,
            id="d3-g1",
        ),
        pytest.param(
            4,
            0,
            0,
            id="d4-g0",
        ),
        pytest.param(
            4,
            1,
            0,
            id="d4-g1",
        ),
        pytest.param(
            5,
            0,
            0,
            id="d5-g0",
        ),
        pytest.param(
            5,
            1,
            0,
            id="d5-g1",
        ),
        pytest.param(
            6,
            0,
            0,
            id="d6-g0",
        ),
        pytest.param(
            6,
            1,
            0,
            id="d6-g1",
        ),
        pytest.param(
            7,
            0,
            0,
            id="d7-g0",
        ),
        pytest.param(
            7,
            1,
            0,
            id="d7-g1",
        ),
        pytest.param(
            8,
            0,
            0,
            id="d8-g0",
        ),
        pytest.param(
            8,
            1,
            0,
            id="d8-g1",
        ),
        pytest.param(
            9,
            0,
            0,
            id="d9-g0",
        ),
        pytest.param(
            9,
            1,
            0,
            id="d9-g1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_sstore_xto0(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Change X -> 0."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0xb000000000000000000000000000000000000000")
    contract_1 = Address("0xc000000000000000000000000000000000000000")
    contract_2 = Address("0xdea0000000000000000000000000000000000000")
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
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xE8D4A51000)
    # Source: lll
    # { [[1]] 0 }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x0) + Op.STOP,
        storage={1: 1},
        nonce=0,
        address=Address("0xb000000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: lll
    # { [[1]] 0 }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x0) + Op.STOP,
        storage={1: 1},
        nonce=0,
        address=Address("0xc000000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: lll
    # { [[1]] 1 [[1]] 0 [[2]] 1 [[2]] 0 [[3]] 1 [[3]] 0 [[4]] 1 [[4]] 0 [[5]] 1 [[5]] 0 [[6]] 1 [[6]] 0 [[7]] 1 [[7]] 0 [[8]] 1 [[8]] 0 [[9]] 1 [[9]] 0 [[10]] 1 [[10]] 0 [[11]] 1 [[11]] 0 [[12]] 1 [[12]] 0 [[13]] 1 [[13]] 0 [[14]] 1 [[14]] 0 [[15]] 1 [[15]] 0 [[16]] 1 [[16]] 0  [[1]] 1 }  # noqa: E501
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.SSTORE(key=0x1, value=0x0)
        + Op.SSTORE(key=0x2, value=0x1)
        + Op.SSTORE(key=0x2, value=0x0)
        + Op.SSTORE(key=0x3, value=0x1)
        + Op.SSTORE(key=0x3, value=0x0)
        + Op.SSTORE(key=0x4, value=0x1)
        + Op.SSTORE(key=0x4, value=0x0)
        + Op.SSTORE(key=0x5, value=0x1)
        + Op.SSTORE(key=0x5, value=0x0)
        + Op.SSTORE(key=0x6, value=0x1)
        + Op.SSTORE(key=0x6, value=0x0)
        + Op.SSTORE(key=0x7, value=0x1)
        + Op.SSTORE(key=0x7, value=0x0)
        + Op.SSTORE(key=0x8, value=0x1)
        + Op.SSTORE(key=0x8, value=0x0)
        + Op.SSTORE(key=0x9, value=0x1)
        + Op.SSTORE(key=0x9, value=0x0)
        + Op.SSTORE(key=0xA, value=0x1)
        + Op.SSTORE(key=0xA, value=0x0)
        + Op.SSTORE(key=0xB, value=0x1)
        + Op.SSTORE(key=0xB, value=0x0)
        + Op.SSTORE(key=0xC, value=0x1)
        + Op.SSTORE(key=0xC, value=0x0)
        + Op.SSTORE(key=0xD, value=0x1)
        + Op.SSTORE(key=0xD, value=0x0)
        + Op.SSTORE(key=0xE, value=0x1)
        + Op.SSTORE(key=0xE, value=0x0)
        + Op.SSTORE(key=0xF, value=0x1)
        + Op.SSTORE(key=0xF, value=0x0)
        + Op.SSTORE(key=0x10, value=0x1)
        + Op.SSTORE(key=0x10, value=0x0)
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.STOP,
        nonce=0,
        address=Address("0xdea0000000000000000000000000000000000000"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(storage={1: 0}),
                contract_2: Account(storage={1: 1}),
                Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"): Account(
                    storage={}, nonce=1
                ),
            },
        },
        {
            "indexes": {"data": [1, 2], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(storage={1: 1}),
                contract_2: Account(storage={1: 1}),
                Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"): Account(
                    storage={1: 0}, nonce=1
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_2: Account(storage={1: 1})},
        },
        {
            "indexes": {"data": 4, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address("0x7564c2d690ab324d8fa20707f2bbdcff4367bb92"): Account(
                    storage={0: 0, 1: 1}
                ),
                contract_2: Account(storage={1: 1}),
            },
        },
        {
            "indexes": {"data": -1, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_2: Account(storage={1: 0})},
        },
        {
            "indexes": {"data": [5, 6, 7, 8, 9], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_2: Account(storage={1: 0})},
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
