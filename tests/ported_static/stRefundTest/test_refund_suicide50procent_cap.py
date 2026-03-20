"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRefundTest/refundSuicide50procentCapFiller.json
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

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stRefundTest/refundSuicide50procentCapFiller.json",  # noqa: E501
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
def test_refund_suicide50procent_cap(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xeb201d2887816e041f6e807e804f64f3a7a226fe")
    sender = EOA(
        key=0xF79127A3004ABDE26A4CBD80C428CB10F829FA11B54D36E7B326F4F4A5927ACF
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    callee = pre.deploy_contract(
        code=(
            Op.SELFDESTRUCT(address=0xA6CC2CA5611255D50118601AA8ECE6F124FC4C45)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x4ff65047ce9c85f968689e4369c10003026a41a9"),  # noqa: E501
    )
    # Source: LLL
    # { [22] (GAS) [[ 10 ]] 1 [[ 11 ]] (CALL (CALLDATALOAD 0) <contract:0xaaae7baea6a6c7c4c2dfeb977efac326af552aaa> 0 0 0 0 0 ) [[ 1 ]] 0 [[ 2 ]] 0 [[ 3 ]] 0 [[ 4 ]] 0 [[ 5 ]] 0 [[ 6 ]] 0 [[ 7 ]] 0 [[ 8 ]] 0 [[ 23 ]] (SUB @22 (GAS)) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x16, value=Op.GAS)
            + Op.SSTORE(key=0xA, value=0x1)
            + Op.SSTORE(
                key=0xB,
                value=Op.CALL(
                    gas=Op.CALLDATALOAD(offset=0x0),
                    address=0x4FF65047CE9C85F968689E4369C10003026A41A9,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x0)
            + Op.SSTORE(key=0x2, value=0x0)
            + Op.SSTORE(key=0x3, value=0x0)
            + Op.SSTORE(key=0x4, value=0x0)
            + Op.SSTORE(key=0x5, value=0x0)
            + Op.SSTORE(key=0x6, value=0x0)
            + Op.SSTORE(key=0x7, value=0x0)
            + Op.SSTORE(key=0x8, value=0x0)
            + Op.SSTORE(key=0x17, value=Op.SUB(Op.MLOAD(offset=0x16), Op.GAS))
            + Op.STOP
        ),
        storage={
            0x1: 0x1,
            0x2: 0x1,
            0x3: 0x1,
            0x4: 0x1,
            0x5: 0x1,
            0x6: 0x1,
            0x7: 0x1,
            0x8: 0x1,
        },
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xa6cc2ca5611255d50118601aa8ece6f124fc4c45"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3B9ACA00)
    pre[coinbase] = Account(balance=0, nonce=1)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "73a6cc2ca5611255d50118601aa8ece6f124fc4c45ff00"
                    )
                ),
                contract: Account(
                    storage={10: 1, 23: 0x107A7},
                    code=bytes.fromhex(
                        "5a6016526001600a5560006000600060006000734ff65047ce9c85f968689e4369c10003026a41a9600035f1600b55600060015560006002556000600355600060045560006005556000600655600060075560006008555a6016510360175500"  # noqa: E501
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
                        "73a6cc2ca5611255d50118601aa8ece6f124fc4c45ff00"
                    )
                ),
                contract: Account(
                    storage={10: 1, 11: 1, 23: 0x166FA},
                    code=bytes.fromhex(
                        "5a6016526001600a5560006000600060006000734ff65047ce9c85f968689e4369c10003026a41a9600035f1600b55600060015560006002556000600355600060045560006005556000600655600060075560006008555a6016510360175500"  # noqa: E501
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
