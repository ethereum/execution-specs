"""
test_delegatecall_bounds

Ported from:
state_tests/stMemoryStressTest/DELEGATECALL_BoundsFiller.json
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
    ["state_tests/stMemoryStressTest/DELEGATECALL_BoundsFiller.json"],
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
def test_delegatecall_bounds(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """test_delegatecall_bounds"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x50eadfb1030587ab3a993a6ecc073041fc3b45e119daa31a13d78c7e209631a5
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
    # {(DELEGATECALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0 0 0) (DELEGATECALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0xfffffff 0 0xfffffff) (DELEGATECALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0xffffffff 0 0xffffffff) (DELEGATECALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0xfffffff 0 0xfffffff 0) (DELEGATECALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0xffffffff 0 0xffffffff 0)  (DELEGATECALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0xffffffffffffffff 0 0xffffffffffffffff 0) (DELEGATECALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0xffffffffffffffffffffffffffffffff 0 0xffffffffffffffffffffffffffffffff 0) (DELEGATECALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0) (DELEGATECALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0xfffffff 0xfffffff 0xfffffff 0xfffffff)  }
    target = pre.deploy_contract(
        code=Op.POP(Op.DELEGATECALL(gas=0x7ffffffffffffff, address=0x849f53126ade5f72469029537296f2b6644d4d41, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.POP(Op.DELEGATECALL(gas=0x7ffffffffffffff, address=0x849f53126ade5f72469029537296f2b6644d4d41, args_offset=0x0, args_size=0xfffffff, ret_offset=0x0, ret_size=0xfffffff))
        + Op.POP(Op.DELEGATECALL(gas=0x7ffffffffffffff, address=0x849f53126ade5f72469029537296f2b6644d4d41, args_offset=0x0, args_size=0xffffffff, ret_offset=0x0, ret_size=0xffffffff))
        + Op.POP(Op.DELEGATECALL(gas=0x7ffffffffffffff, address=0x849f53126ade5f72469029537296f2b6644d4d41, args_offset=0xfffffff, args_size=0x0, ret_offset=0xfffffff, ret_size=0x0))
        + Op.POP(Op.DELEGATECALL(gas=0x7ffffffffffffff, address=0x849f53126ade5f72469029537296f2b6644d4d41, args_offset=0xffffffff, args_size=0x0, ret_offset=0xffffffff, ret_size=0x0))
        + Op.POP(Op.DELEGATECALL(gas=0x7ffffffffffffff, address=0x849f53126ade5f72469029537296f2b6644d4d41, args_offset=0xffffffffffffffff, args_size=0x0, ret_offset=0xffffffffffffffff, ret_size=0x0))
        + Op.POP(Op.DELEGATECALL(gas=0x7ffffffffffffff, address=0x849f53126ade5f72469029537296f2b6644d4d41, args_offset=0xffffffffffffffffffffffffffffffff, args_size=0x0, ret_offset=0xffffffffffffffffffffffffffffffff, ret_size=0x0))
        + Op.POP(Op.DELEGATECALL(gas=0x7ffffffffffffff, address=0x849f53126ade5f72469029537296f2b6644d4d41, args_offset=0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff, args_size=0x0, ret_offset=0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff, ret_size=0x0))
        + Op.DELEGATECALL(gas=0x7ffffffffffffff, address=0x849f53126ade5f72469029537296f2b6644d4d41, args_offset=0xfffffff, args_size=0xfffffff, ret_offset=0xfffffff, ret_size=0xfffffff)
        + Op.STOP,
        nonce=0,
        address=Address("0x75bc6dcef9bdda4e2eb511e92ed4815699f32b4f"),  # noqa: E501
    )
    # Source: lll
    # { (SSTORE 0 (ADD 1 (SLOAD 0))) }
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.ADD(0x1, Op.SLOAD(key=0x0))) + Op.STOP,  # noqa: E501
        nonce=0,
        address=Address("0x849f53126ade5f72469029537296f2b6644d4d41"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': -1, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {target: Account(storage={0: 0}, balance=0)},
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
