"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stCodeSizeLimit/create2CodeSizeLimitFiller.yml
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
    "6160006000f3",
    "6160016000f3",
]

TX_GAS = [15000000]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stCodeSizeLimit/create2CodeSizeLimitFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(1, 0, 0, id="case0"),
        pytest.param(0, 0, 0, id="case1"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create2_code_size_limit(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test ported from static filler."""
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
        gas_limit=20000000,
    )

    pre[sender] = Account(balance=0xBEBC200)
    # Source: Yul
    # {
    #   mstore(0, calldataload(0))
    #   sstore(0, create2(0, 0, calldatasize(), 0))
    #   sstore(1, 1)
    # }
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
            + Op.SSTORE(
                key=0x0,
                value=Op.CREATE2(
                    value=Op.DUP1,
                    offset=Op.DUP2,
                    size=Op.CALLDATASIZE,
                    salt=0x0,
                ),
            )
            + Op.SSTORE(key=Op.DUP1, value=0x1)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": [0], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address("0x81c305016ab9ca56033a07cc37e7a30fc3e079ac"): Account(
                    storage={}, nonce=1, balance=0
                ),
                sender: Account(nonce=1),
                contract: Account(storage={0: 0, 1: 1}),
            },
        },
        {
            "indexes": {"data": [1], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address(
                    "0x81c305016ab9ca56033a07cc37e7a30fc3e079ac"
                ): Account.NONEXISTENT,
                sender: Account(nonce=1),
                contract: Account(storage={0: 0, 1: 1}),
            },
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
