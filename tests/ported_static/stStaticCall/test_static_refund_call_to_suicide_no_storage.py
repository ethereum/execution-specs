"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall
static_refund_CallToSuicideNoStorageFiller.json
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
    "00000000000000000000000000000000000000000000000000000000000001f4",
    "0000000000000000000000000000000000000000000000000000000000010000",
]

TX_GAS = [10000000]

TX_VALUE = [10]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stStaticCall/static_refund_CallToSuicideNoStorageFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 0, 0, id="case1"),
    ],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_refund_call_to_suicide_no_storage(
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
        key=0x6F0117D3E9C684C7D6E1E6B79DC3880DA2BEBE77C765B171C062FDFFD38A673F
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000000,
    )

    callee = pre.deploy_contract(
        code=(
            Op.SELFDESTRUCT(address=0xA2A10D67C0F0864B703D90D9C36296AD8A547AE6)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x4ff65047ce9c85f968689e4369c10003026a41a9"),  # noqa: E501
    )
    # Source: LLL
    # { [[ 0 ]] (STATICCALL (CALLDATALOAD 0) <contract:0xaaae7baea6a6c7c4c2dfeb977efac326af552aaa> 0 0 0 0 ) [[ 2 ]] 1 }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.STATICCALL(
                    gas=Op.CALLDATALOAD(offset=0x0),
                    address=0x4FF65047CE9C85F968689E4369C10003026A41A9,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x2, value=0x1)
            + Op.STOP
        ),
        storage={0x1: 0x1},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xa2a10d67c0f0864b703d90d9c36296ad8a547ae6"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x2540BE400)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "73a2a10d67c0f0864b703d90d9c36296ad8a547ae6ff00"
                    )
                ),
                contract: Account(
                    storage={1: 1, 2: 1},
                    code=bytes.fromhex(
                        "6000600060006000734ff65047ce9c85f968689e4369c10003026a41a9600035fa600055600160025500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "73a2a10d67c0f0864b703d90d9c36296ad8a547ae6ff00"
                    )
                ),
                contract: Account(
                    storage={1: 1, 2: 1},
                    code=bytes.fromhex(
                        "6000600060006000734ff65047ce9c85f968689e4369c10003026a41a9600035fa600055600160025500"  # noqa: E501
                    ),
                ),
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
