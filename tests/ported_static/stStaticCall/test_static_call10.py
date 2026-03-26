"""
test_static_call10

Ported from:
state_tests/stStaticCall/static_Call10Filler.json
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
    "000000000000000000000000ba3d56e16f62d1c74689f260f80faeb7181fcf8f",
    "000000000000000000000000689ef931c00f3b00de5dd2cf0e06f5409b0f26a4",
]
TX_GAS = [200000]
TX_VALUE = [10]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_Call10Filler.json"],
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
def test_static_call10(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """test_static_call10"""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    addr_0xaaaf5374fce5edbc8e2a8697c15331677e6ebf0b = Address("0xd9b97c712ebce43f3c19179bbef44b550f9e8bc0")  # noqa: E501
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
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(balance=0xffffffffffffffffffffffffffffffff)
    pre[addr_0xaaaf5374fce5edbc8e2a8697c15331677e6ebf0b] = Account(balance=7000)
    # Source: lll
    # {  [[ 0 ]] (CALL (GAS) (CALLDATALOAD 0) (CALLVALUE) 0 0 0 0) [[ 1 ]] 1 }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALL(gas=Op.GAS, address=Op.CALLDATALOAD(offset=0x0), value=Op.CALLVALUE, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0xc0e4183389eb57f779a986d8c878f89b9401dc8e"),  # noqa: E501
    )
    # Source: lll
    # { (def 'i 0x80) (for {} (< @i 10) [i](+ @i 1) [[ 0 ]](STATICCALL 0xfffffffffff <eoa:0xaaaf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 50000 0 0) ) [[ 1 ]] @i}
    addr_0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(
        code=Op.JUMPDEST
        + Op.JUMPI(pc=0x40, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xa)))
        + Op.SSTORE(key=0x0, value=Op.STATICCALL(gas=0xfffffffffff, address=0xd9b97c712ebce43f3c19179bbef44b550f9e8bc0, args_offset=0x0, args_size=0xc350, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x0) + Op.JUMPDEST
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x80)) + Op.STOP,
        balance=1000,
        nonce=0,
        address=Address("0xba3d56e16f62d1c74689f260f80faeb7181fcf8f"),  # noqa: E501
    )
    # Source: lll
    # { (def 'i 0x80) (for {} (< @i 10) [i](+ @i 1) (MSTORE 0 (STATICCALL 0xfffffffffff <eoa:0xaaaf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 50000 0 0)) ) (MSTORE 32 @i)}
    addr_0xcbbf5374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(
        code=Op.JUMPDEST
        + Op.JUMPI(pc=0x40, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xa)))
        + Op.MSTORE(offset=0x0, value=Op.STATICCALL(gas=0xfffffffffff, address=0xd9b97c712ebce43f3c19179bbef44b550f9e8bc0, args_offset=0x0, args_size=0xc350, ret_offset=0x0, ret_size=0x0))
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x0) + Op.JUMPDEST
        + Op.MSTORE(offset=0x20, value=Op.MLOAD(offset=0x80)) + Op.STOP,
        balance=1000,
        nonce=0,
        address=Address("0x689ef931c00f3b00de5dd2cf0e06f5409b0f26a4"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': 0, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        addr_0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b: Account(storage={0: 1, 1: 10}),
        target: Account(storage={0: 1, 1: 1}),
    },
        },
        {
            "indexes": {'data': 1, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        addr_0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b: Account(storage={0: 0, 1: 0}),
        target: Account(storage={0: 1, 1: 1}),
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
