"""
Checks EIP-1706/EIP-2200 out of gas requirement for non-mutating SSTOREs.

Ported from:
tests/static/state_tests/stSStoreTest/sstore_gasLeftFiller.json
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
    "6000600060006000600073b0409d84ab61455cb8bec14b94f635146ab55613610901f115604b5760006000600060006000734092b3905cfea2485ea53222f41eb26e67587802617530f1505b00",  # noqa: E501
    "6000600060006000600073b0409d84ab61455cb8bec14b94f635146ab55613610902f115604b5760006000600060006000734092b3905cfea2485ea53222f41eb26e67587802617530f1505b00",  # noqa: E501
    "6000600060006000600073b0409d84ab61455cb8bec14b94f635146ab55613610903f115604b5760006000600060006000734092b3905cfea2485ea53222f41eb26e67587802617530f1505b00",  # noqa: E501
    "60016001556000600060006000600073b0409d84ab61455cb8bec14b94f635146ab55613610901f21560505760006000600060006000734092b3905cfea2485ea53222f41eb26e67587802617530f1505b00",  # noqa: E501
    "60016001556000600060006000600073b0409d84ab61455cb8bec14b94f635146ab55613610902f21560505760006000600060006000734092b3905cfea2485ea53222f41eb26e67587802617530f1505b00",  # noqa: E501
    "60016001556000600060006000600073b0409d84ab61455cb8bec14b94f635146ab55613610903f21560505760006000600060006000734092b3905cfea2485ea53222f41eb26e67587802617530f1505b00",  # noqa: E501
    "6001600155600060006000600073b0409d84ab61455cb8bec14b94f635146ab55613610901f415604e5760006000600060006000734092b3905cfea2485ea53222f41eb26e67587802617530f1505b00",  # noqa: E501
    "6001600155600060006000600073b0409d84ab61455cb8bec14b94f635146ab55613610902f415604e5760006000600060006000734092b3905cfea2485ea53222f41eb26e67587802617530f1505b00",  # noqa: E501
    "6001600155600060006000600073b0409d84ab61455cb8bec14b94f635146ab55613610903f415604e5760006000600060006000734092b3905cfea2485ea53222f41eb26e67587802617530f1505b00",  # noqa: E501
]

TX_GAS = [200000]

TX_VALUE = [1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/stSStoreTest/sstore_gasLeftFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 0, 0, id="case1"),
        pytest.param(2, 0, 0, id="case2"),
        pytest.param(3, 0, 0, id="case3"),
        pytest.param(4, 0, 0, id="case4"),
        pytest.param(5, 0, 0, id="case5"),
        pytest.param(6, 0, 0, id="case6"),
        pytest.param(7, 0, 0, id="case7"),
        pytest.param(8, 0, 0, id="case8"),
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
    """Checks EIP-1706/EIP-2200 out of gas requirement for non-mutating..."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    contract = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x4092b3905cfea2485ea53222f41eb26e67587802"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        storage={0x1: 0x1},
        nonce=0,
        address=Address("0xb0409d84ab61455cb8bec14b94f635146ab55613"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(code=bytes.fromhex("600160015500")),
                callee_1: Account(
                    storage={1: 1}, code=bytes.fromhex("600160015500")
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(code=bytes.fromhex("600160015500")),
                callee_1: Account(
                    storage={1: 1}, code=bytes.fromhex("600160015500")
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1}, code=bytes.fromhex("600160015500")
                ),
                callee_1: Account(
                    storage={1: 1}, code=bytes.fromhex("600160015500")
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                Address("0x21b8a1d7e6f995ece38f302d2981ac0793c37fbd"): Account(
                    storage={1: 1}
                ),
                contract: Account(code=bytes.fromhex("600160015500")),
                callee_1: Account(
                    storage={1: 1}, code=bytes.fromhex("600160015500")
                ),
            },
        },
        {
            "indexes": {"data": 4, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                Address("0x21b8a1d7e6f995ece38f302d2981ac0793c37fbd"): Account(
                    storage={1: 1}
                ),
                contract: Account(code=bytes.fromhex("600160015500")),
                callee_1: Account(
                    storage={1: 1}, code=bytes.fromhex("600160015500")
                ),
            },
        },
        {
            "indexes": {"data": 5, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                Address("0x21b8a1d7e6f995ece38f302d2981ac0793c37fbd"): Account(
                    storage={1: 1}
                ),
                contract: Account(
                    storage={1: 1}, code=bytes.fromhex("600160015500")
                ),
                callee_1: Account(
                    storage={1: 1}, code=bytes.fromhex("600160015500")
                ),
            },
        },
        {
            "indexes": {"data": 6, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                Address("0x21b8a1d7e6f995ece38f302d2981ac0793c37fbd"): Account(
                    storage={1: 1}
                ),
                contract: Account(code=bytes.fromhex("600160015500")),
                callee_1: Account(
                    storage={1: 1}, code=bytes.fromhex("600160015500")
                ),
            },
        },
        {
            "indexes": {"data": 7, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                Address("0x21b8a1d7e6f995ece38f302d2981ac0793c37fbd"): Account(
                    storage={1: 1}
                ),
                contract: Account(code=bytes.fromhex("600160015500")),
                callee_1: Account(
                    storage={1: 1}, code=bytes.fromhex("600160015500")
                ),
            },
        },
        {
            "indexes": {"data": 8, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                Address("0x21b8a1d7e6f995ece38f302d2981ac0793c37fbd"): Account(
                    storage={1: 1}
                ),
                contract: Account(
                    storage={1: 1}, code=bytes.fromhex("600160015500")
                ),
                callee_1: Account(
                    storage={1: 1}, code=bytes.fromhex("600160015500")
                ),
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
