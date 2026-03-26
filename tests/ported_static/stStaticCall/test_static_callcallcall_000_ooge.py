"""
test_static_callcallcall_000_ooge

Ported from:
state_tests/stStaticCall/static_callcallcall_000_OOGEFiller.json
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
    "000000000000000000000000071587c3e5f2ebf88b2a5b048733778605addb28",
    "0000000000000000000000009b0cb3cb3655d3173ff7c2cd51319aaf2cca3cad",
]
TX_GAS = [1720000]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_callcallcall_000_OOGEFiller.json"],
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
def test_static_callcallcall_000_ooge(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """test_static_callcallcall_000_ooge"""
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
    # {  [[ 0 ]] (CALL (GAS) (CALLDATALOAD 0) (CALLVALUE) 0 0 0 0) [[ 1 ]] 1 }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALL(gas=Op.GAS, address=Op.CALLDATALOAD(offset=0x0), value=Op.CALLVALUE, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0xc0e4183389eb57f779a986d8c878f89b9401dc8e"),  # noqa: E501
    )
    # Source: lll
    # {  [[ 0 ]] (STATICCALL 500000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) }
    addr_0x1000000000000000000000000000000000000000 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.STATICCALL(gas=0x7a120, address=0xa69f4d8056bb192982bf07d59ad0ff96a15b41d9, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x071587c3e5f2ebf88b2a5b048733778605addb28"),  # noqa: E501
    )
    # Source: lll
    # {   (MSTORE 3 1) (STATICCALL 300000 <contract:0x1000000000000000000000000000000000000002> 0 64 0 64 ) (MSTORE 32 1) }
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x3, value=0x1)
        + Op.POP(Op.STATICCALL(gas=0x493e0, address=0xcd0bd482baeeb001e6f3ffd36bceb34d32169c93, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))
        + Op.MSTORE(offset=0x20, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0xa69f4d8056bb192982bf07d59ad0ff96a15b41d9"),  # noqa: E501
    )
    # Source: lll
    # {   (MSTORE 3 1) (STATICCALL 120020 <contract:0x1000000000000000000000000000000000000003> 0 64 0 64 ) (MSTORE 32 1) }
    addr_0x1000000000000000000000000000000000000002 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x3, value=0x1)
        + Op.POP(Op.STATICCALL(gas=0x1d4d4, address=0x9d41ca9233d19d3202befcef33f16af7201f0eaa, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))
        + Op.MSTORE(offset=0x20, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0xcd0bd482baeeb001e6f3ffd36bceb34d32169c93"),  # noqa: E501
    )
    # Source: lll
    # {  (SSTORE 3 1) (MSTORE 3 1)}
    addr_0x1000000000000000000000000000000000000003 = pre.deploy_contract(
        code=Op.SSTORE(key=0x3, value=0x1) + Op.MSTORE(offset=0x3, value=0x1)
        + Op.STOP,
        nonce=0,
        address=Address("0x9d41ca9233d19d3202befcef33f16af7201f0eaa"),  # noqa: E501
    )
    # Source: lll
    # {  [[ 0 ]] (STATICCALL 600000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) }
    addr_0x2000000000000000000000000000000000000000 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.STATICCALL(gas=0x927c0, address=0xa69f4d8056bb192982bf07d59ad0ff96a15b41d9, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x9b0cb3cb3655d3173ff7c2cd51319aaf2cca3cad"),  # noqa: E501
    )
    # Source: lll
    # {   (MSTORE 3 1) (STATICCALL 300000 <contract:0x2000000000000000000000000000000000000002> 0 64 0 64 )(MSTORE 32 1) }
    addr_0x2000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x3, value=0x1)
        + Op.POP(Op.STATICCALL(gas=0x493e0, address=0xac6bf72c47193c6fefc55efcc14674f8023f39f9, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))
        + Op.MSTORE(offset=0x20, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0xa76ce2de971ea2b78bc19ba706cb135f4fff2cc2"),  # noqa: E501
    )
    # Source: lll
    # {   (MSTORE 3 1) (STATICCALL 120020 <contract:0x2000000000000000000000000000000000000003> 0 64 0 64 )(MSTORE 32 1) }
    addr_0x2000000000000000000000000000000000000002 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x3, value=0x1)
        + Op.POP(Op.STATICCALL(gas=0x1d4d4, address=0xf31e5b020afccf373bfa588c4d3a199c4f7a46a4, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))
        + Op.MSTORE(offset=0x20, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0xac6bf72c47193c6fefc55efcc14674f8023f39f9"),  # noqa: E501
    )
    # Source: lll
    # { (def 'i 0x80) (for {} (< @i 50000) [i](+ @i 1) (EXTCODESIZE 1)  ) }
    addr_0x2000000000000000000000000000000000000003 = pre.deploy_contract(
        code=Op.JUMPDEST
        + Op.JUMPI(pc=0x1c, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xc350)))
        + Op.POP(Op.EXTCODESIZE(address=0x1))
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x0) + Op.JUMPDEST + Op.STOP,
        nonce=0,
        address=Address("0xf31e5b020afccf373bfa588c4d3a199c4f7a46a4"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': 0, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        addr_0x1000000000000000000000000000000000000000: Account(storage={0: 1, 1: 0, 2: 0, 3: 0}),
        addr_0x1000000000000000000000000000000000000001: Account(storage={1: 0, 2: 0, 3: 0}),
        addr_0x1000000000000000000000000000000000000002: Account(storage={2: 0, 3: 0}),
        addr_0x1000000000000000000000000000000000000003: Account(storage={3: 0}),
        target: Account(storage={0: 1, 1: 1}),
    },
        },
        {
            "indexes": {'data': 1, 'gas': -1, 'value': -1},
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
