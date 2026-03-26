"""
test_refund_suicide50procent_cap

Ported from:
state_tests/stRefundTest/refundSuicide50procentCapFiller.json
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
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stRefundTest/refundSuicide50procentCapFiller.json"],
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
def test_refund_suicide50procent_cap(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """test_refund_suicide50procent_cap"""
    coinbase = Address("0xeb201d2887816e041f6e807e804f64f3a7a226fe")
    sender = EOA(
        key=0xf79127a3004abde26a4cbd80c428cb10f829fa11b54d36e7b326f4f4a5927acf
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[coinbase] = Account(balance=0, nonce=1)
    # Source: lll
    # { [22] (GAS) [[ 10 ]] 1 [[ 11 ]] (CALL (CALLDATALOAD 0) <contract:0xaaae7baea6a6c7c4c2dfeb977efac326af552aaa> 0 0 0 0 0 ) [[ 1 ]] 0 [[ 2 ]] 0 [[ 3 ]] 0 [[ 4 ]] 0 [[ 5 ]] 0 [[ 6 ]] 0 [[ 7 ]] 0 [[ 8 ]] 0 [[ 23 ]] (SUB @22 (GAS)) }
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x16, value=Op.GAS) + Op.SSTORE(key=0xa, value=0x1)  # noqa: E501
        + Op.SSTORE(key=0xb, value=Op.CALL(gas=Op.CALLDATALOAD(offset=0x0), address=0x4ff65047ce9c85f968689e4369c10003026a41a9, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x1, value=0x0) + Op.SSTORE(key=0x2, value=0x0)
        + Op.SSTORE(key=0x3, value=0x0) + Op.SSTORE(key=0x4, value=0x0)
        + Op.SSTORE(key=0x5, value=0x0) + Op.SSTORE(key=0x6, value=0x0)
        + Op.SSTORE(key=0x7, value=0x0) + Op.SSTORE(key=0x8, value=0x0)
        + Op.SSTORE(key=0x17, value=Op.SUB(Op.MLOAD(offset=0x16), Op.GAS))
        + Op.STOP,
        storage={1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1},
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xa6cc2ca5611255d50118601aa8ece6f124fc4c45"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3b9aca00)
    # Source: lll
    # { (SELFDESTRUCT <contract:target:0x095e7baea6a6c7c4c2dfeb977efac326af552d87>) }
    addr_0xaaae7baea6a6c7c4c2dfeb977efac326af552aaa = pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=0xa6cc2ca5611255d50118601aa8ece6f124fc4c45)
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x4ff65047ce9c85f968689e4369c10003026a41a9"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': 0, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        target: Account(
                storage={10: 1, 11: 0, 23: 0x107a7},
                balance=0xde0b6b3a7640000,
            ),
        sender: Account(nonce=1),
    },
        },
        {
            "indexes": {'data': 1, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        target: Account(
                storage={10: 1, 11: 1, 23: 0x166fa},
                balance=0x1bc16d674ec80000,
            ),
        sender: Account(nonce=1),
    },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=target,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        nonce=0,
        gas_price=10,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
