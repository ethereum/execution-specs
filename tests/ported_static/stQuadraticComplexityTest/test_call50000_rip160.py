"""
test_call50000_rip160

Ported from:
state_tests/stQuadraticComplexityTest/Call50000_rip160Filler.json
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
TX_GAS = [150000, 250000000]
TX_VALUE = [10]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stQuadraticComplexityTest/Call50000_rip160Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="-g0",
        ),
        pytest.param(
            0, 1, 0,
            id="-g1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_call50000_rip160(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """test_call50000_rip160"""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = EOA(
        key=0xe7c72b378297589acee4e0ba3272841bcfc5e220f86de253f890274cfee9e474
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=3925000000,
    )

    pre[sender] = Account(balance=0xffffffffffffffffffffffffffffffff)
    # Source: lll
    # { (def 'i 0x80) (for {} (< @i 50000) [i](+ @i 1) [[ 0 ]] (CALL 78200 3 1 0 50000 0 0) ) [[ 1 ]] @i}
    target = pre.deploy_contract(
        code=Op.JUMPDEST
        + Op.JUMPI(pc=0x2d, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xc350)))
        + Op.SSTORE(key=0x0, value=Op.CALL(gas=0x13178, address=0x3, value=0x1, args_offset=0x0, args_size=0xc350, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x0) + Op.JUMPDEST
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x80)) + Op.STOP,
        balance=0xfffffffffffff,
        nonce=0,
        address=Address("0xc10d84baa3a4bb4e45c856ebe1ef386bfed327db"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': -1, 'gas': 1, 'value': -1},
            "network": ['>=Cancun<Osaka'],
            "result": {
        sender: Account(storage={}, code=b"", nonce=1),
        target: Account(
                storage={},
                code=bytes.fromhex("5b61c3506080511015602d576000600061c35060006001600362013178f16000556001608051016080526000565b60805160015500"),  # noqa: E501
                nonce=0,
            ),
    },
        },
        {
            "indexes": {'data': -1, 'gas': 0, 'value': -1},
            "network": ['>=Cancun<Osaka'],
            "result": {
        sender: Account(storage={}, code=b"", nonce=1),
        target: Account(
                storage={},
                code=bytes.fromhex("5b61c3506080511015602d576000600061c35060006001600362013178f16000556001608051016080526000565b60805160015500"),  # noqa: E501
                nonce=0,
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
