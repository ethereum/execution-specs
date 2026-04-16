"""
Test_static_call_basic.

Ported from:
state_tests/stStaticCall/static_callBasicFiller.json
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
    ["state_tests/stStaticCall/static_callBasicFiller.json"],
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
        pytest.param(
            2,
            0,
            0,
            id="d2",
        ),
        pytest.param(
            3,
            0,
            0,
            id="d3",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_static_call_basic(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_call_basic."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: lll
    # {  [[ 0 ]] (STATICCALL 100000 (CALLDATALOAD 0) 0 0 0 0) [[ 1 ]] 1 }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0x186A0,
                address=Op.CALLDATALOAD(offset=0x0),
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
        address=Address(0x13670D6BD41ACD42D75E7C4C25DF7384A6FBD752),  # noqa: E501
    )
    # Source: lll
    # { [[ 1 ]] 1 }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        storage={1: 1},
        balance=23,
        nonce=0,
        address=Address(0xD3C0847CA0222F22DCFB4A433A378FF58AD6A881),  # noqa: E501
    )
    # Source: lll
    # { [[ 1 ]] 0 }
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x0) + Op.STOP,
        storage={1: 0},
        balance=23,
        nonce=0,
        address=Address(0xEAD198F480FB91A5FBEDCF5EB28CD369EE4C6CF2),  # noqa: E501
    )
    # Source: lll
    # { (LOG0 1 10) (MSTORE 1 1) }
    addr_4 = pre.deploy_contract(  # noqa: F841
        code=Op.LOG0(offset=0x1, size=0xA)
        + Op.MSTORE(offset=0x1, value=0x1)
        + Op.STOP,
        balance=23,
        nonce=0,
        address=Address(0x2E0DD8ABE4E68C5B602F3C65051F4B30C6D018DA),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 1 1) }
    addr_6 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x1, value=0x1) + Op.STOP,
        balance=23,
        nonce=0,
        address=Address(0xC93C7A588B13699E562B3933E8F2B1C15E610781),  # noqa: E501
    )
    # Source: lll
    # { (CALL 40000 <contract:0x2000000000000000000000000000000000000003> 0 0 0 0 0) (MSTORE 1 1) }  # noqa: E501
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.CALL(
                gas=0x9C40,
                address=0x2E0DD8ABE4E68C5B602F3C65051F4B30C6D018DA,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x1, value=0x1)
        + Op.STOP,
        balance=23,
        nonce=0,
        address=Address(0xEB015F637A39C63F8B6DB67505F5C02C613DEFC1),  # noqa: E501
    )
    # Source: lll
    # { (CALLCODE 40000 <contract:0x3000000000000000000000000000000000000003> 1 0 0 0 0) (MSTORE 1 1) }  # noqa: E501
    addr_5 = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.CALLCODE(
                gas=0x9C40,
                address=0xC93C7A588B13699E562B3933E8F2B1C15E610781,
                value=0x1,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x1, value=0x1)
        + Op.STOP,
        balance=23,
        nonce=0,
        address=Address(0xD5B64FA2CA1E471B45B639A5E9C259CA24C28ACE),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0, 1], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {target: Account(storage={0: 0, 1: 1})},
        },
        {
            "indexes": {"data": [2], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {target: Account(storage={0: 1, 1: 1})},
        },
        {
            "indexes": {"data": [3], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 1, 1: 1}),
                addr_6: Account(balance=23),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(addr, left_padding=True),
        Hash(addr_2, left_padding=True),
        Hash(addr_3, left_padding=True),
        Hash(addr_5, left_padding=True),
    ]
    tx_gas = [1000000]
    tx_value = [100000]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
