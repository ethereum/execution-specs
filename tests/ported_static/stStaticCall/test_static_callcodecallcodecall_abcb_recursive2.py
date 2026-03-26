"""
test_static_callcodecallcodecall_abcb_recursive2

Ported from:
state_tests/stStaticCall/static_callcodecallcodecall_ABCB_RECURSIVE2Filler.json
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
TX_GAS = [600000]
TX_VALUE = [0, 1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_callcodecallcodecall_ABCB_RECURSIVE2Filler.json"],
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
def test_static_callcodecallcodecall_abcb_recursive2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """test_static_callcodecallcodecall_abcb_recursive2"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=3000000000,
    )

    # Source: lll
    # {  [[ 0 ]] (CALLCODE 25000000 <contract:0x1000000000000000000000000000000000000001> (CALLVALUE) 0 64 0 64 ) [[ 1 ]] 1 }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALLCODE(gas=0x17d7840, address=0x9ef1d089354c245c0c8a08590f55e76008ac54cd, value=Op.CALLVALUE, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x3da1f9d4153096bd467629a1fdb678437acd810b"),  # noqa: E501
    )
    # Source: lll
    # {  (CALLCODE 1000000 <contract:0x1000000000000000000000000000000000000002> 0 0 64 0 64 ) }
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.CALLCODE(gas=0xf4240, address=0x1e2229d0f325b81b81b8b14f2d239ff9742683c0, value=0x0, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40)
        + Op.STOP,
        balance=0x2540be400,
        nonce=0,
        address=Address("0x9ef1d089354c245c0c8a08590f55e76008ac54cd"),  # noqa: E501
    )
    # Source: lll
    # {  (STATICCALL 500000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) }
    addr_0x1000000000000000000000000000000000000002 = pre.deploy_contract(
        code=Op.STATICCALL(gas=0x7a120, address=0x9ef1d089354c245c0c8a08590f55e76008ac54cd, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40)
        + Op.STOP,
        balance=0x2540be400,
        nonce=0,
        address=Address("0x1e2229d0f325b81b81b8b14f2d239ff9742683c0"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': -1, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {target: Account(storage={0: 1, 1: 1})},
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
