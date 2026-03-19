"""
Account attempts to send tx to create a contract on a non-empty address.

Ported from:
tests/static/state_tests/stEIP3607/initCollidingWithNonEmptyAccountFiller.yml
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
    "60206000f3",
    "6001600055600080808061271073d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d05af100",  # noqa: E501
    "60016000556000602081612710f500",
    "600160005560206000612710f000",
    "6001600055600080808073d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d05af400",
]

TX_GAS = [400000]

TX_VALUE = [100000]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stEIP3607/initCollidingWithNonEmptyAccountFiller.yml",  # noqa: E501
    ],
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
    """Account attempts to send tx to create a contract on a non-empty..."""
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
        gas_limit=71794957647893862,
    )

    pre[coinbase] = Account(balance=0, nonce=1)
    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x0),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: raw bytecode
    callee_1 = pre.deploy_contract(
        code=bytes.fromhex("00"),
        nonce=0,
        address=Address("0xd0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0"),  # noqa: E501
    )

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(code=bytes.fromhex("6000600155")),
                callee_1: Account(code=bytes.fromhex("00")),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(code=bytes.fromhex("6000600155")),
                callee_1: Account(code=bytes.fromhex("00")),
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(code=bytes.fromhex("6000600155")),
                callee_1: Account(code=bytes.fromhex("00")),
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(code=bytes.fromhex("6000600155")),
                callee_1: Account(code=bytes.fromhex("00")),
            },
        },
        {
            "indexes": {"data": 4, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(code=bytes.fromhex("6000600155")),
                callee_1: Account(code=bytes.fromhex("00")),
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
