"""
test_call1_mb1024_calldepth

Ported from:
state_tests/stQuadraticComplexityTest/Call1MB1024CalldepthFiller.json
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
    ["state_tests/stQuadraticComplexityTest/Call1MB1024CalldepthFiller.json"],
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
def test_call1_mb1024_calldepth(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """test_call1_mb1024_calldepth"""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    addr_0xaaa50000fce5edbc8e2a8697c15331677e6ebf0b = Address("0x2ab8257767339461506c0c67824cf17bc77b52ca")  # noqa: E501
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
        gas_limit=882500000000,
    )

    pre[sender] = Account(balance=0xffffffffffffffffffffffffffffffff)
    pre[addr_0xaaa50000fce5edbc8e2a8697c15331677e6ebf0b] = Account(balance=0xfffffffffffff)
    # Source: lll
    # { (def 'i 0x80) [[ 0 ]] (+ @@0 1) (if (LT @@0 1024) [[ 1 ]] (CALL (- (GAS) 1005000) <contract:target:0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 1000000 0 0) [[ 2 ]] 1 )  }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.JUMPI(pc=0x1b, condition=Op.LT(Op.SLOAD(key=0x0), 0x400))
        + Op.SSTORE(key=0x2, value=0x1) + Op.JUMP(pc=0x47) + Op.JUMPDEST
        + Op.SSTORE(key=0x1, value=Op.CALL(gas=Op.SUB(Op.GAS, 0xf55c8), address=0x9d15232f6851f9f3a88f88a3b358ed1579977a5a, value=0x0, args_offset=0x0, args_size=0xf4240, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.JUMPDEST + Op.STOP,
        balance=0xfffffffffffff,
        nonce=0,
        address=Address("0x9d15232f6851f9f3a88f88a3b358ed1579977a5a"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': -1, 'gas': 1, 'value': -1},
            "network": ['>=Cancun<Osaka'],
            "result": {
        sender: Account(storage={}, code=b"", nonce=1),
        addr_0xaaa50000fce5edbc8e2a8697c15331677e6ebf0b: Account(storage={}, code=b"", nonce=0),
        target: Account(storage={0: 69, 1: 1}, nonce=0),
    },
        },
        {
            "indexes": {'data': -1, 'gas': 0, 'value': -1},
            "network": ['>=Cancun<Osaka'],
            "result": {
        sender: Account(storage={}, code=b"", nonce=1),
        addr_0xaaa50000fce5edbc8e2a8697c15331677e6ebf0b: Account(storage={}, code=b"", nonce=0),
        target: Account(storage={}, nonce=0),
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
