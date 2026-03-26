"""
test_static_callcodecallcall_100_oogm_before

Ported from:
state_tests/stStaticCall/static_callcodecallcall_100_OOGMBeforeFiller.json
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
    "000000000000000000000000cc95c09a27cbe0199e6d898e64b4dc1774f164e1",
    "0000000000000000000000004670334e92c4d14771faadb3c90c987cb337acca",
]
TX_GAS = [172000]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_callcodecallcall_100_OOGMBeforeFiller.json"],
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
def test_static_callcodecallcall_100_oogm_before(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """test_static_callcodecallcall_100_oogm_before"""
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
        gas_limit=30000000,
    )

    # Source: lll
    # {  (MSTORE 0 (CALLDATALOAD 0)) [[ 0 ]] (DELEGATECALL 150000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) [[ 1 ]] 1  }
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
        + Op.SSTORE(key=0x0, value=Op.DELEGATECALL(gas=0x249f0, address=0x570b7a7eb7d0539d77442b6262127229b9b6c19f, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xb1dddce88104538f48811f8e62af99666e0c3a4e"),  # noqa: E501
    )
    # Source: lll
    # {  (STATICCALL 40080 (CALLDATALOAD 0) 0 64 0 64 ) (MSTORE 3 1) }
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.POP(Op.STATICCALL(gas=0x9c90, address=Op.CALLDATALOAD(offset=0x0), args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))
        + Op.MSTORE(offset=0x3, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x570b7a7eb7d0539d77442b6262127229b9b6c19f"),  # noqa: E501
    )
    # Source: lll
    # {  (def 'i 0x80) (for {} (< @i 50000) [i](+ @i 1) (EXTCODESIZE 1)) (STATICCALL 20020 <contract:0x1000000000000000000000000000000000000003> 0 64 0 64 ) }
    addr_0x1000000000000000000000000000000000000002 = pre.deploy_contract(
        code=Op.JUMPDEST
        + Op.JUMPI(pc=0x1c, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xc350)))
        + Op.POP(Op.EXTCODESIZE(address=0x1))
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x0) + Op.JUMPDEST
        + Op.STATICCALL(gas=0x4e34, address=0x335c5531b84765a7626e6e76688f18b81be5259c, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40)
        + Op.STOP,
        nonce=0,
        address=Address("0xcc95c09a27cbe0199e6d898e64b4dc1774f164e1"),  # noqa: E501
    )
    # Source: lll
    # {  (SSTORE 3 1) (STATICCALL 20020 <contract:0x1000000000000000000000000000000000000003> 0 64 0 64 ) (MSTORE 3 1) }
    addr_0x2000000000000000000000000000000000000002 = pre.deploy_contract(
        code=Op.SSTORE(key=0x3, value=0x1)
        + Op.POP(Op.STATICCALL(gas=0x4e34, address=0x335c5531b84765a7626e6e76688f18b81be5259c, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))
        + Op.MSTORE(offset=0x3, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x4670334e92c4d14771faadb3c90c987cb337acca"),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 3 1) }
    addr_0x1000000000000000000000000000000000000003 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x3, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x335c5531b84765a7626e6e76688f18b81be5259c"),  # noqa: E501
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
        nonce=0,
        gas_price=10,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
