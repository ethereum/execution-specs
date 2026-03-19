"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall
static_refund_CallToSuicideTwiceFiller.json
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
        "tests/static/state_tests/stStaticCall/static_refund_CallToSuicideTwiceFiller.json",  # noqa: E501
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
def test_static_refund_call_to_suicide_twice(
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
        key=0x5B7B8EFB6D003CD481E408D8759A25ADC79955092F1A380D8F8B57346C1D1342
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: LLL
    # { [[ 0 ]] (STATICCALL (CALLDATALOAD 0) <contract:0xaaae7baea6a6c7c4c2dfeb977efac326af552aaa> 0 0 0 0 ) (CALL (CALLDATALOAD 0) <contract:0xaaae7baea6a6c7c4c2dfeb977efac326af552aaa> 0 0 0 0 0 )}  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.STATICCALL(
                    gas=Op.CALLDATALOAD(offset=0x0),
                    address=0x9DEA1AD5123F3D8B91CFC830B1C602597883E97C,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.CALL(
                gas=Op.CALLDATALOAD(offset=0x0),
                address=0x9DEA1AD5123F3D8B91CFC830B1C602597883E97C,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        storage={0x1: 0x1},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x75db2708826b7d5e8cd45002f9ae23c830c31efd"),  # noqa: E501
    )
    callee = pre.deploy_contract(
        code=(
            Op.SELFDESTRUCT(address=0x75DB2708826B7D5E8CD45002F9AE23C830C31EFD)
            + Op.STOP
        ),
        storage={0x1: 0x1},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x9dea1ad5123f3d8b91cfc830b1c602597883e97c"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x174876E800)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "6000600060006000739dea1ad5123f3d8b91cfc830b1c602597883e97c600035fa60005560006000600060006000739dea1ad5123f3d8b91cfc830b1c602597883e97c600035f100"  # noqa: E501
                    ),
                ),
                callee: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "7375db2708826b7d5e8cd45002f9ae23c830c31efdff00"
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "6000600060006000739dea1ad5123f3d8b91cfc830b1c602597883e97c600035fa60005560006000600060006000739dea1ad5123f3d8b91cfc830b1c602597883e97c600035f100"  # noqa: E501
                    ),
                ),
                callee: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "7375db2708826b7d5e8cd45002f9ae23c830c31efdff00"
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
