"""
test_static_refund_call_to_suicide_no_storage

Ported from:
state_tests/stStaticCall/static_refund_CallToSuicideNoStorageFiller.json
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
from execution_testing.vm import Op
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)

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
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_refund_CallToSuicideNoStorageFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="d0",
        ),
        pytest.param(
            1, 0, 0,
            id="d1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_static_refund_call_to_suicide_no_storage(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """test_static_refund_call_to_suicide_no_storage"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x6f0117d3e9c684c7d6e1e6b79dc3880da2bebe77c765b171c062fdffd38a673f
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000000,
    )

    # Source: lll
    # { [[ 0 ]] (STATICCALL (CALLDATALOAD 0) <contract:0xaaae7baea6a6c7c4c2dfeb977efac326af552aaa> 0 0 0 0 ) [[ 2 ]] 1 }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.STATICCALL(gas=Op.CALLDATALOAD(offset=0x0), address=0x4ff65047ce9c85f968689e4369c10003026a41a9, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x2, value=0x1) + Op.STOP,
        storage={1: 1},
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xa2a10d67c0f0864b703d90d9c36296ad8a547ae6"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x2540be400)
    # Source: lll
    # { (SELFDESTRUCT <contract:target:0x095e7baea6a6c7c4c2dfeb977efac326af552d87>) }
    addr_0xaaae7baea6a6c7c4c2dfeb977efac326af552aaa = pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=0xa2a10d67c0f0864b703d90d9c36296ad8a547ae6)
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x4ff65047ce9c85f968689e4369c10003026a41a9"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': -1, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        target: Account(
                storage={0: 0, 1: 1, 2: 1},
                balance=0xde0b6b3a764000a,
            ),
    },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=target,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        nonce=0,
        gas_price=10,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
