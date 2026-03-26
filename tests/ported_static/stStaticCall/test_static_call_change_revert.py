"""
test_static_call_change_revert

Ported from:
state_tests/stStaticCall/static_callChangeRevertFiller.json
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
    "000000000000000000000000e6f1fdaa1c99007971c641e10af3a8fac0b641c8",
    "000000000000000000000000ea22ec955ac71d8e4380541212bd20818d704567",
    "0000000000000000000000002c004389edaae817e664b6d660f46735756b56d3",
]
TX_GAS = [1000000]
TX_VALUE = [100000]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_callChangeRevertFiller.json"],
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
    ],
)
@pytest.mark.pre_alloc_mutable
def test_static_call_change_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """test_static_call_change_revert"""
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
        gas_limit=10000000,
    )

    # Source: lll
    # {  (CALL 350000 (CALLDATALOAD 0) 0 0 0 0 0)  }
    target = pre.deploy_contract(
        code=Op.CALL(gas=0x55730, address=Op.CALLDATALOAD(offset=0x0), value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x492bb18adce7da2bed3592742fb4e3df9086fb4c"),  # noqa: E501
    )
    # Source: lll
    # {  [[ 0 ]] (CALL 100000 <contract:0x1000000000000000000000000000000000000001> 1 0 0 0 0) [[ 1 ]] (STATICCALL 100000 <contract:0x1000000000000000000000000000000000000001> 0 0 0 0) [[ 2 ]] (CALL 100000 <contract:0x1000000000000000000000000000000000000001> 1 0 0 0 0) }
    addr_0x1000000000000000000000000000000000000000 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALL(gas=0x186a0, address=0xc031fc0aa7b61a5d7d962afee8838dec6948abb7, value=0x1, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x1, value=Op.STATICCALL(gas=0x186a0, address=0xc031fc0aa7b61a5d7d962afee8838dec6948abb7, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x2, value=Op.CALL(gas=0x186a0, address=0xc031fc0aa7b61a5d7d962afee8838dec6948abb7, value=0x1, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xe6f1fdaa1c99007971c641e10af3a8fac0b641c8"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 1 1)  }
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x1, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0xc031fc0aa7b61a5d7d962afee8838dec6948abb7"),  # noqa: E501
    )
    # Source: lll
    # {  [[ 0 ]] (CALL 100000 <contract:0x1000000000000000000000000000000000000001> 1 0 0 0 0) [[ 1 ]] (STATICCALL 100000 <contract:0x1000000000000000000000000000000000000001> 0 0 0 0) [[ 2 ]] (CALL 100000 <contract:0x1000000000000000000000000000000000000001> 1 0 0 0 0) (def 'i 0x80) (for {} (< @i 50000) [i](+ @i 1) (EXTCODESIZE 1)) }
    addr_0x2000000000000000000000000000000000000000 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALL(gas=0x186a0, address=0xc031fc0aa7b61a5d7d962afee8838dec6948abb7, value=0x1, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x1, value=Op.STATICCALL(gas=0x186a0, address=0xc031fc0aa7b61a5d7d962afee8838dec6948abb7, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x2, value=Op.CALL(gas=0x186a0, address=0xc031fc0aa7b61a5d7d962afee8838dec6948abb7, value=0x1, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x8f, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xc350)))
        + Op.POP(Op.EXTCODESIZE(address=0x1))
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x73) + Op.JUMPDEST + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xea22ec955ac71d8e4380541212bd20818d704567"),  # noqa: E501
    )
    # Source: lll
    # {  [[ 0 ]] (CALL 100000 <contract:0x1000000000000000000000000000000000000002> 1 0 0 0 0) [[ 1 ]] (STATICCALL 100000 <contract:0x1000000000000000000000000000000000000002> 0 0 0 0) [[ 2 ]] (CALL 100000 <contract:0x1000000000000000000000000000000000000002> 1 0 0 0 0) }
    addr_0x3000000000000000000000000000000000000000 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALL(gas=0x186a0, address=0x47c4ed3d93429cb8304737e2327b522e8928c9f3, value=0x1, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x1, value=Op.STATICCALL(gas=0x186a0, address=0x47c4ed3d93429cb8304737e2327b522e8928c9f3, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x2, value=Op.CALL(gas=0x186a0, address=0x47c4ed3d93429cb8304737e2327b522e8928c9f3, value=0x1, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x2c004389edaae817e664b6d660f46735756b56d3"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 1 1) (SSTORE 1 (SLOAD 1)) }
    addr_0x1000000000000000000000000000000000000002 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x1, value=0x1)
        + Op.SSTORE(key=0x1, value=Op.SLOAD(key=0x1)) + Op.STOP,
        nonce=0,
        address=Address("0x47c4ed3d93429cb8304737e2327b522e8928c9f3"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': 0, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        addr_0x1000000000000000000000000000000000000000: Account(storage={0: 1, 1: 1, 2: 1}),
        addr_0x1000000000000000000000000000000000000001: Account(balance=2),
    },
        },
        {
            "indexes": {'data': 1, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        addr_0x2000000000000000000000000000000000000000: Account(storage={0: 0, 1: 0, 2: 0}),
        addr_0x1000000000000000000000000000000000000001: Account(balance=0),
    },
        },
        {
            "indexes": {'data': 2, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        addr_0x3000000000000000000000000000000000000000: Account(storage={0: 1, 1: 0, 2: 1}),
        addr_0x1000000000000000000000000000000000000002: Account(balance=2),
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
