"""
create2 generates an account that already exists and has not empty code.

Ported from:
tests/static/state_tests/stCreate2/create2collisionCodeFiller.json
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
    "6000600060006000f500",
    "64600160015560005260006005601b6000f500",
    "6d6460016001556000526005601bf36000526000600e60126000f500",
]

TX_GAS = [400000]

TX_VALUE = [1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/stCreate2/create2collisionCodeFiller.json"],
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
def test_create2collision_code(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Create2 generates an account that already exists and has not..."""
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
    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=Op.SUB(Op.MUL, Op.ADD),
        nonce=0,
        address=Address("0xaf3ecba2fe09a4f6c19f16a9d119e44e08c2da01"),  # noqa: E501
    )
    # Source: raw bytecode
    callee_1 = pre.deploy_contract(
        code=Op.SUB(Op.MUL, Op.ADD),
        nonce=0,
        address=Address("0xe2b35478fdd26477cc576dd906e6277761246a3c"),  # noqa: E501
    )
    # Source: raw bytecode
    callee_2 = pre.deploy_contract(
        code=Op.SUB(Op.MUL, Op.ADD),
        nonce=0,
        address=Address("0xec2c6832d00680ece8ff9254f81fdab0a5a2ac50"),  # noqa: E501
    )

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": -1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"): Account(
                    nonce=2, balance=1, code=b""
                ),
                sender: Account(nonce=1),
                contract: Account(
                    storage={},
                    nonce=0,
                    balance=0,
                    code=bytes.fromhex("010203"),
                ),
                callee_1: Account(
                    storage={},
                    nonce=0,
                    balance=0,
                    code=bytes.fromhex("010203"),
                ),
                callee_2: Account(
                    storage={},
                    nonce=0,
                    balance=0,
                    code=bytes.fromhex("010203"),
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
