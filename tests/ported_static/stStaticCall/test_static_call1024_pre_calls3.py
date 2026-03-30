"""
Test_static_call1024_pre_calls3.

Ported from:
state_tests/stStaticCall/static_Call1024PreCalls3Filler.json
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
    ["state_tests/stStaticCall/static_Call1024PreCalls3Filler.json"],
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
def test_static_call1024_pre_calls3(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_call1024_pre_calls3."""
    coinbase = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    addr = Address(0xD9B97C712EBCE43F3C19179BBEF44B550F9E8BC0)
    sender = EOA(
        key=0xCC381C83857B17CA629268ED418E2915A0287B84EFE9CF2204C020302E83CDA0
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
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
    pre[addr] = Account(balance=7000)
    # Source: lll
    # { [[ 2 ]] (STATICCALL 0xffff <eoa:0xaaaf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0) [[ 3 ]] (STATICCALL 0xffff <eoa:0xaaaf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0)  [[ 0 ]] (ADD @@0 1) [[ 1 ]] (STATICCALL 0xfffffffffff <contract:0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0) }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x2,
            value=Op.STATICCALL(
                gas=0xFFFF,
                address=0xD9B97C712EBCE43F3C19179BBEF44B550F9E8BC0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0x3,
            value=Op.STATICCALL(
                gas=0xFFFF,
                address=0xD9B97C712EBCE43F3C19179BBEF44B550F9E8BC0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.SSTORE(
            key=0x1,
            value=Op.STATICCALL(
                gas=0xFFFFFFFFFFF,
                address=0x2806E7553F3585D821F91D679A254ABBF002F6F2,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        balance=2024,
        nonce=0,
        address=Address(0x2806E7553F3585D821F91D679A254ABBF002F6F2),  # noqa: E501
    )
    # Source: lll
    # { (STATICCALL 0xffff <eoa:0xaaaf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0) (STATICCALL 0xffff <eoa:0xaaaf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0)  (MSTORE 0 (ADD (MLOAD 0) 1)) (STATICCALL 0xfffffffffff <contract:0xcbbf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0) }  # noqa: E501
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.STATICCALL(
                gas=0xFFFF,
                address=0xD9B97C712EBCE43F3C19179BBEF44B550F9E8BC0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        * 2
        + Op.MSTORE(offset=0x0, value=Op.ADD(Op.MLOAD(offset=0x0), 0x1))
        + Op.STATICCALL(
            gas=0xFFFFFFFFFFF,
            address=0x7C546B69D5BDA111C03C8D7B51B41A8D55B843CA,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=2024,
        nonce=0,
        address=Address(0x7C546B69D5BDA111C03C8D7B51B41A8D55B843CA),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                addr_2: Account(storage={0: 1, 1: 0, 2: 1, 3: 1}),
                target: Account(storage={0: 1, 1: 1}),
            },
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                addr_3: Account(storage={0: 0, 1: 0, 2: 0, 3: 0}),
                target: Account(storage={0: 1, 1: 1}),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(addr_2, left_padding=True),
        Hash(addr_3, left_padding=True),
    ]
    tx_gas = [9214364837600034817]
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
