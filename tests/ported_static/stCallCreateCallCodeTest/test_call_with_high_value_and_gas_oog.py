"""
call with value. call takes more gas then tx has, and more value than account has. check returndata.

Ported from:
state_tests/stCallCreateCallCodeTest/callWithHighValueAndGasOOGFiller.json
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
    "",
]
TX_GAS = [6000000]
TX_VALUE = [100000, 100000000000000000000]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stCallCreateCallCodeTest/callWithHighValueAndGasOOGFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="-v0",
        ),
        pytest.param(
            0, 0, 1,
            id="-v1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_call_with_high_value_and_gas_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """call with value."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x897b12d02d588d8a4fe16ff831cbd4459c6f62f8c845b0ccdd31caf068c84a26
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    # Source: lll
    # { (MSTORE 0 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) (MSTORE 32 0xaaffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffaa ) [[ 0 ]] (CALL 0xffffffffffffffffffffffff <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 100000000000000000000 0 64 0 2 ) [[1]] (MLOAD 0)}
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)
        + Op.MSTORE(offset=0x20, value=0xaaffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffaa)
        + Op.SSTORE(key=0x0, value=Op.CALL(gas=0xffffffffffffffffffffffff, address=0x896f13e800125c0ccec44f3c434335f0a97bc1b, value=0x56bc75e2d63100000, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x2))  # noqa: E501
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0)) + Op.STOP,
        storage={0: 5},
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xdfad372452688759edd82c422bf3976eafc89c2b"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155603760005360026000f3
    addr_0x945304eb96065b2a98b57a48a06ae28d285a71b5 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x1) + Op.MSTORE8(offset=0x0, value=0x37)
        + Op.RETURN(offset=0x0, size=0x2),
        balance=23,
        nonce=0,
        address=Address("0x0896f13e800125c0ccec44f3c434335f0a97bc1b"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3635c9adc5dea00000)

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': -1, 'gas': -1, 'value': 0},
            "network": ['>=Cancun'],
            "result": {
        target: Account(
                storage={
            1: 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff,
        },
            ),
    },
        },
        {
            "indexes": {'data': -1, 'gas': -1, 'value': 1},
            "network": ['>=Cancun'],
            "result": {
        target: Account(
                storage={
            0: 1,
            1: 0x3700ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff,
        },
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
