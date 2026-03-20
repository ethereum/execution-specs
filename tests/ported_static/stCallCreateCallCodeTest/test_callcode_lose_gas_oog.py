"""
recursive call.

Ported from:
tests/static/state_tests/stCallCreateCallCodeTest/CallcodeLoseGasOOGFiller.json
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
    "",
    "",
    "",
]

TX_GAS = [166262, 156262, 170000]

TX_VALUE = [10]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stCallCreateCallCodeTest/CallcodeLoseGasOOGFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 1, 0, id="case1"),
        pytest.param(2, 2, 0, id="case2"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_callcode_lose_gas_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Recursive call."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = EOA(
        key=0xE7C72B378297589ACEE4E0BA3272841BCFC5E220F86DE253F890274CFEE9E474
    )
    callee = Address("0xd9b97c712ebce43f3c19179bbef44b550f9e8bc0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
    # Source: LLL
    # { [[ 0 ]] (ADD @@0 1) [[ 1 ]] (CALLCODE (ADD 1(MUL @@0 100000)) <contract:target:0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[ 2 ]] (ADD 1(MUL @@0 1000)) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
            + Op.SSTORE(
                key=0x1,
                value=Op.CALLCODE(
                    gas=Op.ADD(0x1, Op.MUL(Op.SLOAD(key=0x0), 0x186A0)),
                    address=0xB0FAFBE5AA1D6F184EB4BCB79B292E4D3238F4CA,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(
                key=0x2,
                value=Op.ADD(0x1, Op.MUL(Op.SLOAD(key=0x0), 0x3E8)),
            )
            + Op.STOP
        ),
        balance=1024,
        nonce=0,
        address=Address("0xb0fafbe5aa1d6f184eb4bcb79b292e4d3238f4ca"),  # noqa: E501
    )
    pre[callee] = Account(balance=7000, nonce=0)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "6001600054016000556000600060006000600073b0fafbe5aa1d6f184eb4bcb79b292e4d3238f4ca620186a060005402600101f26001556103e86000540260010160025500"  # noqa: E501
                    )
                )
            },
        },
        {
            "indexes": {"data": 1, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "6001600054016000556000600060006000600073b0fafbe5aa1d6f184eb4bcb79b292e4d3238f4ca620186a060005402600101f26001556103e86000540260010160025500"  # noqa: E501
                    )
                )
            },
        },
        {
            "indexes": {"data": 2, "gas": 2, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1, 2: 1001},
                    code=bytes.fromhex(
                        "6001600054016000556000600060006000600073b0fafbe5aa1d6f184eb4bcb79b292e4d3238f4ca620186a060005402600101f26001556103e86000540260010160025500"  # noqa: E501
                    ),
                )
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
