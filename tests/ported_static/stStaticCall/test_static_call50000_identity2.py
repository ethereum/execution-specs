"""
Test_static_call50000_identity2.

Ported from:
state_tests/stStaticCall/static_Call50000_identity2Filler.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_Call50000_identity2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.slow
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_static_call50000_identity2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_call50000_identity2."""
    coinbase = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    sender = EOA(
        key=0xE7C72B378297589ACEE4E0BA3272841BCFC5E220F86DE253F890274CFEE9E474
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=8925000000,
    )

    pre[sender] = Account(balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
    # Source: lll
    # {  [[ 0 ]] (CALL (GAS) (CALLDATALOAD 0) (CALLVALUE) 0 0 0 0) [[ 1 ]] 1 }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=Op.GAS,
                address=Op.CALLDATALOAD(offset=0x0),
                value=Op.CALLVALUE,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.STOP,
        nonce=0,
        address=Address(0xC0E4183389EB57F779A986D8C878F89B9401DC8E),  # noqa: E501
    )
    # Source: lll
    # { (def 'i 0x80) [ 1 ] 42 (for {} (< @i 50000) [i](+ @i 1) [[ 0 ]] (STATICCALL 1564 4 0 50000 1 50000) ) [[ 1 ]] @i [[ 2 ]] @1 }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x1, value=0x2A)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x30, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350))
        )
        + Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0x61C,
                address=0x4,
                args_offset=0x0,
                args_size=0xC350,
                ret_offset=0x1,
                ret_size=0xC350,
            ),
        )
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x5)
        + Op.JUMPDEST
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x80))
        + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x1))
        + Op.STOP,
        balance=0xFFFFFFFFFFFFF,
        nonce=0,
        address=Address(0xCFB4C99D22928822FEFFA77A1A6DE64042E48DD3),  # noqa: E501
    )
    # Source: lll
    # { (def 'i 0x80) [ 1 ] 42 (for {} (< @i 50000) [i](+ @i 1) (MSTORE 0 (STATICCALL 1564 4 0 50000 1 50000)) ) (MSTORE 32 @i) (MSTORE 64 @1 ) }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x1, value=0x2A)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x30, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350))
        )
        + Op.MSTORE(
            offset=0x0,
            value=Op.STATICCALL(
                gas=0x61C,
                address=0x4,
                args_offset=0x0,
                args_size=0xC350,
                ret_offset=0x1,
                ret_size=0xC350,
            ),
        )
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x5)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x20, value=Op.MLOAD(offset=0x80))
        + Op.MSTORE(offset=0x40, value=Op.MLOAD(offset=0x1))
        + Op.STOP,
        balance=0xFFFFFFFFFFFFF,
        nonce=0,
        address=Address(0xB02BD8691A1A4F5FD4432B5B17C68DDE3013FC35),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                sender: Account(storage={}, code=b"", nonce=1),
                addr: Account(storage={1: 50000, 2: 42}, nonce=0),
                target: Account(storage={0: 1, 1: 1}),
            },
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                sender: Account(storage={}, code=b"", nonce=1),
                addr: Account(storage={}, nonce=0),
                target: Account(storage={0: 1, 1: 1}),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(addr, left_padding=True),
        Hash(addr_2, left_padding=True),
    ]
    tx_gas = [882500000]
    tx_value = [10]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
