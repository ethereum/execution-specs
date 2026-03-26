"""
test_static_call_bounds

Ported from:
state_tests/stMemoryStressTest/static_CALL_BoundsFiller.json
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
TX_GAS = [150000, 16777216]
TX_VALUE = [1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stMemoryStressTest/static_CALL_BoundsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
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
def test_static_call_bounds(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """test_static_call_bounds"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xef111bbdab3a1622936afdfc9bbec4b5bc05b4fa4b1ef0ce2a55cef552f7650e
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

    # Source: lll
    # {  (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0 0 0) (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0xfffffff 0 0xfffffff) (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0xffffffff 0 0xffffffff) (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0xfffffff 0 0xfffffff 0) (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0xffffffff 0 0xffffffff 0) (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0xffffffffffffffff 0 0xffffffffffffffff 0) (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0xffffffffffffffffffffffffffffffff 0 0xffffffffffffffffffffffffffffffff 0) (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0)  }
    target = pre.deploy_contract(
        code=Op.POP(Op.STATICCALL(gas=0x7ffffffffffffff, address=0xcc704d60c46b9c08aab4d15281184441ac7ed35c, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.POP(Op.STATICCALL(gas=0x7ffffffffffffff, address=0xcc704d60c46b9c08aab4d15281184441ac7ed35c, args_offset=0x0, args_size=0xfffffff, ret_offset=0x0, ret_size=0xfffffff))
        + Op.POP(Op.STATICCALL(gas=0x7ffffffffffffff, address=0xcc704d60c46b9c08aab4d15281184441ac7ed35c, args_offset=0x0, args_size=0xffffffff, ret_offset=0x0, ret_size=0xffffffff))
        + Op.POP(Op.STATICCALL(gas=0x7ffffffffffffff, address=0xcc704d60c46b9c08aab4d15281184441ac7ed35c, args_offset=0xfffffff, args_size=0x0, ret_offset=0xfffffff, ret_size=0x0))
        + Op.POP(Op.STATICCALL(gas=0x7ffffffffffffff, address=0xcc704d60c46b9c08aab4d15281184441ac7ed35c, args_offset=0xffffffff, args_size=0x0, ret_offset=0xffffffff, ret_size=0x0))
        + Op.POP(Op.STATICCALL(gas=0x7ffffffffffffff, address=0xcc704d60c46b9c08aab4d15281184441ac7ed35c, args_offset=0xffffffffffffffff, args_size=0x0, ret_offset=0xffffffffffffffff, ret_size=0x0))
        + Op.POP(Op.STATICCALL(gas=0x7ffffffffffffff, address=0xcc704d60c46b9c08aab4d15281184441ac7ed35c, args_offset=0xffffffffffffffffffffffffffffffff, args_size=0x0, ret_offset=0xffffffffffffffffffffffffffffffff, ret_size=0x0))
        + Op.STATICCALL(gas=0x7ffffffffffffff, address=0xcc704d60c46b9c08aab4d15281184441ac7ed35c, args_offset=0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff, args_size=0x0, ret_offset=0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff, ret_size=0x0)
        + Op.STOP,
        nonce=0,
        address=Address("0x7f91c742985ac295da40f3771a1be98f99f6a357"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0 (ADD 1 (SLOAD 0))) }
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.ADD(0x1, Op.SLOAD(key=0x0))) + Op.STOP,  # noqa: E501
        nonce=0,
        address=Address("0xcc704d60c46b9c08aab4d15281184441ac7ed35c"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xffffffffffffffffffffffffffffffffffffffffffffffffffffff)

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': -1, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        target: Account(balance=0),
        addr_0x1000000000000000000000000000000000000001: Account(storage={0: 0}),
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
