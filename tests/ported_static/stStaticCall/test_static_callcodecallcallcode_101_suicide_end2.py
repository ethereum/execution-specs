"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall
static_callcodecallcallcode_101_SuicideEnd2Filler.json
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
]

TX_GAS = [3000000]

TX_VALUE = [0, 1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stStaticCall/static_callcodecallcallcode_101_SuicideEnd2Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 0, 1, id="case1"),
    ],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_callcodecallcallcode_101_suicide_end2(
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
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    callee = pre.deploy_contract(
        code=Op.MSTORE(offset=0x3, value=0x1) + Op.STOP,
        balance=0x2540BE400,
        nonce=0,
        address=Address("0x48e2d4c0b593bfebe5ddb4f13aa355b8bd83ddd3"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x3, value=0x1)
            + Op.POP(
                Op.STATICCALL(
                    gas=0x186A0,
                    address=0x90E9B92C59A0E93D8AB0B7AFBC945D6999A50A9B,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.MSTORE(offset=0x20, value=0x1)
            + Op.STOP
        ),
        balance=0x2540BE400,
        nonce=0,
        address=Address("0x620b381d01cbd812ffb798ab35a1a316bde90ce6"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=(
            Op.POP(
                Op.CALLCODE(
                    gas=0xC350,
                    address=0x48E2D4C0B593BFEBE5DDB4F13AA355B8BD83DDD3,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SELFDESTRUCT(
                address=0x620B381D01CBD812FFB798AB35A1A316BDE90CE6
            )
            + Op.STOP
        ),
        balance=0x2540BE400,
        nonce=0,
        address=Address("0x90e9b92c59a0e93d8ab0b7afbc945d6999a50a9b"),  # noqa: E501
    )
    # Source: LLL
    # {  [[ 0 ]] (CALLCODE 150000 <contract:0x1000000000000000000000000000000000000001> (CALLVALUE) 0 64 0 64 ) [[ 1 ]] 1 }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALLCODE(
                    gas=0x249F0,
                    address=0x620B381D01CBD812FFB798AB35A1A316BDE90CE6,
                    value=Op.CALLVALUE,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x1)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xcc7b2c7c17e1dd7940b1aa2f4b3e55d7bd662608"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600160035200")),
                callee_1: Account(
                    code=bytes.fromhex(
                        "600160035260406000604060007390e9b92c59a0e93d8ab0b7afbc945d6999a50a9b620186a0fa50600160205200"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "604060006040600060007348e2d4c0b593bfebe5ddb4f13aa355b8bd83ddd361c350f25073620b381d01cbd812ffb798ab35a1a316bde90ce6ff00"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "60406000604060003473620b381d01cbd812ffb798ab35a1a316bde90ce6620249f0f2600055600160015500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 1},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600160035200")),
                callee_1: Account(
                    code=bytes.fromhex(
                        "600160035260406000604060007390e9b92c59a0e93d8ab0b7afbc945d6999a50a9b620186a0fa50600160205200"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "604060006040600060007348e2d4c0b593bfebe5ddb4f13aa355b8bd83ddd361c350f25073620b381d01cbd812ffb798ab35a1a316bde90ce6ff00"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "60406000604060003473620b381d01cbd812ffb798ab35a1a316bde90ce6620249f0f2600055600160015500"  # noqa: E501
                    ),
                ),
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
