"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall
static_callcodecall_10_SuicideEnd2Filler.json
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
        "tests/static/state_tests/stStaticCall/static_callcodecall_10_SuicideEnd2Filler.json",  # noqa: E501
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
def test_static_callcodecall_10_suicide_end2(
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

    # Source: LLL
    # {  [[ 0 ]] (CALLCODE 150000 <contract:0x1000000000000000000000000000000000000001> (CALLVALUE) 0 64 0 64 ) [[ 1 ]] (GAS) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALLCODE(
                    gas=0x249F0,
                    address=0xB60789F240AC9F12FCDE1E4BBD5042A7F30932D4,
                    value=Op.CALLVALUE,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.GAS)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x44d09ddf088dd88c0e91fa7ef74973ff94ad7414"),  # noqa: E501
    )
    callee = pre.deploy_contract(
        code=(
            Op.POP(
                Op.STATICCALL(
                    gas=0xC350,
                    address=0xCFB5784A5E49924BECC2D5C5D2EE0A9B141E6216,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SELFDESTRUCT(
                address=0x44D09DDF088DD88C0E91FA7EF74973FF94AD7414
            )
            + Op.STOP
        ),
        balance=0x2540BE400,
        nonce=0,
        address=Address("0xb60789f240ac9f12fcde1e4bbd5042a7f30932d4"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x2, value=0x1) + Op.STOP,
        balance=0x2540BE400,
        nonce=0,
        address=Address("0xcfb5784a5e49924becc2d5c5d2ee0a9b141e6216"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1, 1: 0x2CF641},
                    code=bytes.fromhex(
                        "60406000604060003473b60789f240ac9f12fcde1e4bbd5042a7f30932d4620249f0f26000555a60015500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    code=bytes.fromhex(
                        "604060006040600073cfb5784a5e49924becc2d5c5d2ee0a9b141e621661c350fa507344d09ddf088dd88c0e91fa7ef74973ff94ad7414ff00"  # noqa: E501
                    )
                ),
                callee_1: Account(code=bytes.fromhex("600160025200")),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 1},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1, 1: 0x2CDC15},
                    code=bytes.fromhex(
                        "60406000604060003473b60789f240ac9f12fcde1e4bbd5042a7f30932d4620249f0f26000555a60015500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    code=bytes.fromhex(
                        "604060006040600073cfb5784a5e49924becc2d5c5d2ee0a9b141e621661c350fa507344d09ddf088dd88c0e91fa7ef74973ff94ad7414ff00"  # noqa: E501
                    )
                ),
                callee_1: Account(code=bytes.fromhex("600160025200")),
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
