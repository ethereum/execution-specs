"""
Test_static_ab_acalls_suicide0.

Ported from:
state_tests/stStaticCall/static_ABAcallsSuicide0Filler.json
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
    ["state_tests/stStaticCall/static_ABAcallsSuicide0Filler.json"],
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
def test_static_ab_acalls_suicide0(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_ab_acalls_suicide0."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

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
    # {  [[ (PC) ]] (STATICCALL 100000 <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 0 0 0 0) (SELFDESTRUCT <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>)  }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=Op.PC,
            value=Op.STATICCALL(
                gas=0x186A0,
                address=0xC20B4779ED25A1CCF1848F1CBCC84433FCB9D083,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SELFDESTRUCT(address=0xC20B4779ED25A1CCF1848F1CBCC84433FCB9D083)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x195198C66C5E31767D41365FF8003C5FE4387110),  # noqa: E501
    )
    # Source: lll
    # { [[ (PC) ]] (ADD 1 (STATICCALL 50000 <contract:0x095e7baea6a6c7c4c2dfeb977efac326af552d87> 0 0 0 0)) }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=Op.PC,
            value=Op.ADD(
                0x1,
                Op.STATICCALL(
                    gas=0xC350,
                    address=0x195198C66C5E31767D41365FF8003C5FE4387110,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            ),
        )
        + Op.STOP,
        balance=23,
        nonce=0,
        address=Address(0xC20B4779ED25A1CCF1848F1CBCC84433FCB9D083),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE (PC)  (STATICCALL 100000 <contract:0x245304eb96065b2a98b57a48a06ae28d285a71b5> 0 0 0 0)) (SELFDESTRUCT <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>)  }  # noqa: E501
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=Op.PC,
            value=Op.STATICCALL(
                gas=0x186A0,
                address=0x644AC2B24A9316ED4C55001E5EDA02D77F729C7B,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SELFDESTRUCT(address=0xC20B4779ED25A1CCF1848F1CBCC84433FCB9D083)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x15631F76B02193E5716CBD4B4D696F2F7A39F0A4),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE (PC) (ADD 1 (STATICCALL 50000 <contract:0x195e7baea6a6c7c4c2dfeb977efac326af552d87> 0 0 0 0)) ) }  # noqa: E501
    addr_4 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=Op.PC,
            value=Op.ADD(
                0x1,
                Op.STATICCALL(
                    gas=0xC350,
                    address=0x15631F76B02193E5716CBD4B4D696F2F7A39F0A4,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            ),
        )
        + Op.STOP,
        balance=23,
        nonce=0,
        address=Address(0x644AC2B24A9316ED4C55001E5EDA02D77F729C7B),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_2: Account(storage={38: 0}),
                target: Account(storage={0: 1, 1: 1}),
            },
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 1, 1: 1}),
                addr_2: Account(storage={38: 0}),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(addr, left_padding=True),
        Hash(addr_3, left_padding=True),
    ]
    tx_gas = [10000000]
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
