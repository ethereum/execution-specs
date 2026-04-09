"""
Test_static_callcallcode_01_2.

Ported from:
state_tests/stStaticCall/static_callcallcode_01_2Filler.json
"""

import pytest
from execution_testing import (
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
    ["state_tests/stStaticCall/static_callcallcode_01_2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
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
def test_static_callcallcode_01_2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_callcallcode_01_2."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    # Source: lll
    # {  [[ 0 ]] (CALLCODE (GAS) (CALLDATALOAD 0) 0 0 0 0 0) [[ 1 ]] 1 }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALLCODE(
                gas=Op.GAS,
                address=Op.CALLDATALOAD(offset=0x0),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
    )
    # Source: lll
    # {  (MSTORE 0 0x11223344) }
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0x11223344) + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # {  (MSTORE 0 0x11223344) }
    addr_6 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0x11223344) + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # {  (CALLCODE 250000 <contract:0x1000000000000000000000000000000000000002> 2 0 32 0 64 ) }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.CALLCODE(
            gas=0x3D090,
            address=addr_3,
            value=0x2,
            args_offset=0x0,
            args_size=0x20,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
    )
    # Source: lll
    # {  (MSTORE 0 (CALLDATALOAD 0)) (CALLCODE 250000 <contract:0x2000000000000000000000000000000000000002> 0 0 32 0 64 ) }  # noqa: E501
    addr_5 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
        + Op.CALLCODE(
            gas=0x3D090,
            address=addr_6,
            value=0x0,
            args_offset=0x0,
            args_size=0x20,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
    )
    # Source: lll
    # {  (STATICCALL 350000 <contract:0x1000000000000000000000000000000000000001> 0 32 0 64 ) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.STATICCALL(
            gas=0x55730,
            address=addr_2,
            args_offset=0x0,
            args_size=0x20,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
    )
    # Source: lll
    # {  (STATICCALL 350000 <contract:0x2000000000000000000000000000000000000001> 0 32 0 64 ) }  # noqa: E501
    addr_4 = pre.deploy_contract(  # noqa: F841
        code=Op.STATICCALL(
            gas=0x55730,
            address=addr_5,
            args_offset=0x0,
            args_size=0x20,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {target: Account(storage={0: 1, 1: 1})},
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {target: Account(storage={0: 1, 1: 1})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(addr, left_padding=True),
        Hash(addr_4, left_padding=True),
    ]
    tx_gas = [3000000]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
