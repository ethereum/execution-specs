"""
test_revert_precompiled_touch_paris

Ported from:
state_tests/stRevertTest/RevertPrecompiledTouch_ParisFiller.json
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
    "00000000000000000000000087aaeb9e422487283b0b008ef445e32acb9dd1ae",
    "00000000000000000000000031f52a66cf9d94c60f089a2ca9c4e784261c57fa",
    "000000000000000000000000de1200b7ecaea2d15b57d0f331ad5ade8e924255",
    "00000000000000000000000010ef6d6218ada53728683cec4d5160c8c72159bd",
]
TX_GAS = [100000]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stRevertTest/RevertPrecompiledTouch_ParisFiller.json"],
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
        pytest.param(
            2, 0, 0,
            id="d2",
        ),
        pytest.param(
            3, 0, 0,
            id="d3",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_revert_precompiled_touch_paris(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """test_revert_precompiled_touch_paris"""
    coinbase = Address("0x68795c4aa09d6f4ed3e5deddf8c2ad3049a601da")
    addr_0x0000000000000000000000000000000000000001 = Address("0x6eb9afcb5d985b12549b7ac2e65c093f7113a0c7")  # noqa: E501
    addr_0x0000000000000000000000000000000000000002 = Address("0xf07a794e0f8aab4242b86368503d3c1de15481f8")  # noqa: E501
    addr_0x0000000000000000000000000000000000000003 = Address("0x9e6c35deced6e05eb21d3465b5bbbb57b9cd57d6")  # noqa: E501
    addr_0x0000000000000000000000000000000000000004 = Address("0x1688023d9ae9e25ea02a2447a77b9cc9d22ce57b")  # noqa: E501
    addr_0x0000000000000000000000000000000000000005 = Address("0xd085ab47bc36d1238fc092679b21b10792746640")  # noqa: E501
    addr_0x0000000000000000000000000000000000000006 = Address("0xad3df2901b7c6642e397c35e0e9f3dea5d098238")  # noqa: E501
    addr_0x0000000000000000000000000000000000000007 = Address("0xbe44b82021b08cfecc33a2e57ff5adcb7fe3b049")  # noqa: E501
    addr_0x0000000000000000000000000000000000000008 = Address("0x85fdde91fd0ce22a2968e1f1b2ebb9f9e5a180ba")  # noqa: E501
    sender = EOA(
        key=0xff8d58222f34f6890ddaa468c023b77d6691ed7d3c4dcddae38336212faf54b
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=4012015,
    )

    # Source: lll
    # {  (CALLCODE (GAS) (CALLDATALOAD 0) 0 0 0 0 0) }
    target = pre.deploy_contract(
        code=Op.CALLCODE(gas=Op.GAS, address=Op.CALLDATALOAD(offset=0x0), value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.STOP,
        nonce=0,
        address=Address("0xe7c596de24ccc387daa5c017066aeb25ea8d2f3f"),  # noqa: E501
    )
    # Source: lll
    # { (CALL 50000 1 0 0 0 0 0) (CALL 50000 2 0 0 0 0 0) (CALL 50000 3 0 0 0 0 0) (CALL 50000 4 0 0 0 0 0) (CALL 50000 5 0 0 0 0 0) (CALL 50000 6 0 0 0 0 0) (CALL 50000 7 0 0 0 0 0) (CALL 50000 8 0 0 0 0 0) [[1]] (GAS) [[2]] (GAS) [[3]] (GAS) }
    addr_0x1000000000000000000000000000000000000000 = pre.deploy_contract(
        code=Op.POP(Op.CALL(gas=0xc350, address=0x1, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.POP(Op.CALL(gas=0xc350, address=0x2, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.POP(Op.CALL(gas=0xc350, address=0x3, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.POP(Op.CALL(gas=0xc350, address=0x4, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.POP(Op.CALL(gas=0xc350, address=0x5, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.POP(Op.CALL(gas=0xc350, address=0x6, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.POP(Op.CALL(gas=0xc350, address=0x7, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.POP(Op.CALL(gas=0xc350, address=0x8, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.SSTORE(key=0x1, value=Op.GAS) + Op.SSTORE(key=0x2, value=Op.GAS)
        + Op.SSTORE(key=0x3, value=Op.GAS) + Op.STOP,
        nonce=0,
        address=Address("0x87aaeb9e422487283b0b008ef445e32acb9dd1ae"),  # noqa: E501
    )
    # Source: lll
    # { (DELEGATECALL 50000 1 0 0 0 0) (DELEGATECALL 50000 2 0 0 0 0) (DELEGATECALL 50000 3 0 0 0 0) (DELEGATECALL 50000 4 0 0 0 0) (DELEGATECALL 50000 5 0 0 0 0) (DELEGATECALL 50000 6 0 0 0 0) (DELEGATECALL 50000 7 0 0 0 0) (DELEGATECALL 50000 8 0 0 0 0) [[1]] (GAS) [[2]] (GAS) [[3]] (GAS) }
    addr_0x2000000000000000000000000000000000000000 = pre.deploy_contract(
        code=Op.POP(Op.DELEGATECALL(gas=0xc350, address=0x1, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.POP(Op.DELEGATECALL(gas=0xc350, address=0x2, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.POP(Op.DELEGATECALL(gas=0xc350, address=0x3, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.POP(Op.DELEGATECALL(gas=0xc350, address=0x4, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.POP(Op.DELEGATECALL(gas=0xc350, address=0x5, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.POP(Op.DELEGATECALL(gas=0xc350, address=0x6, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.POP(Op.DELEGATECALL(gas=0xc350, address=0x7, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.POP(Op.DELEGATECALL(gas=0xc350, address=0x8, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.SSTORE(key=0x1, value=Op.GAS) + Op.SSTORE(key=0x2, value=Op.GAS)
        + Op.SSTORE(key=0x3, value=Op.GAS) + Op.STOP,
        nonce=0,
        address=Address("0x31f52a66cf9d94c60f089a2ca9c4e784261c57fa"),  # noqa: E501
    )
    # Source: lll
    # { (CALLCODE 50000 1 0 0 0 0 0) (CALLCODE 50000 2 0 0 0 0 0) (CALLCODE 50000 3 0 0 0 0 0) (CALLCODE 50000 4 0 0 0 0 0) (CALLCODE 50000 5 0 0 0 0 0) (CALLCODE 50000 6 0 0 0 0 0) (CALLCODE 50000 7 0 0 0 0 0) (CALLCODE 50000 8 0 0 0 0 0) [[1]] (GAS) [[2]] (GAS) [[3]] (GAS) }
    addr_0x3000000000000000000000000000000000000000 = pre.deploy_contract(
        code=Op.POP(Op.CALLCODE(gas=0xc350, address=0x1, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.POP(Op.CALLCODE(gas=0xc350, address=0x2, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.POP(Op.CALLCODE(gas=0xc350, address=0x3, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.POP(Op.CALLCODE(gas=0xc350, address=0x4, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.POP(Op.CALLCODE(gas=0xc350, address=0x5, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.POP(Op.CALLCODE(gas=0xc350, address=0x6, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.POP(Op.CALLCODE(gas=0xc350, address=0x7, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.POP(Op.CALLCODE(gas=0xc350, address=0x8, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.SSTORE(key=0x1, value=Op.GAS) + Op.SSTORE(key=0x2, value=Op.GAS)
        + Op.SSTORE(key=0x3, value=Op.GAS) + Op.STOP,
        nonce=0,
        address=Address("0xde1200b7ecaea2d15b57d0f331ad5ade8e924255"),  # noqa: E501
    )
    # Source: lll
    # { (STATICCALL 50000 1 0 0 0 0) (STATICCALL 50000 2 0 0 0 0) (STATICCALL 50000 3 0 0 0 0) (STATICCALL 50000 4 0 0 0 0) (STATICCALL 50000 5 0 0 0 0) (STATICCALL 50000 6 0 0 0 0) (STATICCALL 50000 7 0 0 0 0) (STATICCALL 50000 8 0 0 0 0) [[1]] (GAS) [[2]] (GAS) [[3]] (GAS) }
    addr_0x4000000000000000000000000000000000000000 = pre.deploy_contract(
        code=Op.POP(Op.STATICCALL(gas=0xc350, address=0x1, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.POP(Op.STATICCALL(gas=0xc350, address=0x2, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.POP(Op.STATICCALL(gas=0xc350, address=0x3, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.POP(Op.STATICCALL(gas=0xc350, address=0x4, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.POP(Op.STATICCALL(gas=0xc350, address=0x5, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.POP(Op.STATICCALL(gas=0xc350, address=0x6, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.POP(Op.STATICCALL(gas=0xc350, address=0x7, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.POP(Op.STATICCALL(gas=0xc350, address=0x8, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.SSTORE(key=0x1, value=Op.GAS) + Op.SSTORE(key=0x2, value=Op.GAS)
        + Op.SSTORE(key=0x3, value=Op.GAS) + Op.STOP,
        nonce=0,
        address=Address("0x10ef6d6218ada53728683cec4d5160c8c72159bd"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=1)
    pre[addr_0x0000000000000000000000000000000000000001] = Account(balance=1)
    pre[addr_0x0000000000000000000000000000000000000002] = Account(balance=1)
    pre[addr_0x0000000000000000000000000000000000000003] = Account(balance=1)
    pre[addr_0x0000000000000000000000000000000000000004] = Account(balance=1)
    pre[addr_0x0000000000000000000000000000000000000005] = Account(balance=1)
    pre[addr_0x0000000000000000000000000000000000000006] = Account(balance=1)
    pre[addr_0x0000000000000000000000000000000000000007] = Account(balance=1)
    pre[addr_0x0000000000000000000000000000000000000008] = Account(balance=1)

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': [0, 3], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        addr_0x0000000000000000000000000000000000000001: Account(nonce=0),
        addr_0x0000000000000000000000000000000000000002: Account(nonce=0),
        addr_0x0000000000000000000000000000000000000003: Account(nonce=0),
        addr_0x0000000000000000000000000000000000000004: Account(nonce=0),
        addr_0x0000000000000000000000000000000000000005: Account(nonce=0),
        addr_0x0000000000000000000000000000000000000006: Account(nonce=0),
        addr_0x0000000000000000000000000000000000000007: Account(nonce=0),
        addr_0x0000000000000000000000000000000000000008: Account(nonce=0),
    },
        },
        {
            "indexes": {'data': [1, 2], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        addr_0x0000000000000000000000000000000000000001: Account(nonce=0),
        addr_0x0000000000000000000000000000000000000002: Account(nonce=0),
        addr_0x0000000000000000000000000000000000000003: Account(nonce=0),
        addr_0x0000000000000000000000000000000000000004: Account(nonce=0),
        addr_0x0000000000000000000000000000000000000005: Account(nonce=0),
        addr_0x0000000000000000000000000000000000000006: Account(nonce=0),
        addr_0x0000000000000000000000000000000000000007: Account(nonce=0),
        addr_0x0000000000000000000000000000000000000008: Account(nonce=0),
    },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=target,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        nonce=1,
        gas_price=10,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
