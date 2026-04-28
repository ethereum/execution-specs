"""
Test_static_ab_acalls3.

Ported from:
state_tests/stStaticCall/static_ABAcalls3Filler.json
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
    ["state_tests/stStaticCall/static_ABAcalls3Filler.json"],
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
def test_static_ab_acalls3(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_ab_acalls3."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000000,
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
    # {  [[ 0 ]] (ADD (SLOAD 0) 1) (STATICCALL (- (GAS) 100000) <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 0 0 0 0) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.STATICCALL(
            gas=Op.SUB(Op.GAS, 0x186A0),
            address=0xE278F8058BEF1396C2B1DF4D1DC4B65233133C57,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xFA3E8,
        nonce=0,
        address=Address(0x407DA20797D4E89C2F4E48C502385C1514D9FA52),  # noqa: E501
    )
    # Source: lll
    # { [[ 0 ]] (ADD (SLOAD 0) 1) (STATICCALL (- (GAS) 100000) <contract:0x095e7baea6a6c7c4c2dfeb977efac326af552d87> 0 0 0 0) }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.STATICCALL(
            gas=Op.SUB(Op.GAS, 0x186A0),
            address=0x407DA20797D4E89C2F4E48C502385C1514D9FA52,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        nonce=0,
        address=Address(0xE278F8058BEF1396C2B1DF4D1DC4B65233133C57),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 0 (ADD (SLOAD 0) 1)) (STATICCALL (- (GAS) 100000) <contract:0x245304eb96065b2a98b57a48a06ae28d285a71b5> 0 0 0 0) }  # noqa: E501
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.STATICCALL(
            gas=Op.SUB(Op.GAS, 0x186A0),
            address=0xB1F7380DB647F1D85565B28978BA83861B99965,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xFA3E8,
        nonce=0,
        address=Address(0xE40C059876E334B99A5D199693978C39BEDB690D),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0 (ADD (SLOAD 0) 1)) (STATICCALL (- (GAS) 100000) <contract:0x195e7baea6a6c7c4c2dfeb977efac326af552d87> 0 0 0 0) }  # noqa: E501
    addr_4 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.STATICCALL(
            gas=Op.SUB(Op.GAS, 0x186A0),
            address=0xE40C059876E334B99A5D199693978C39BEDB690D,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        nonce=0,
        address=Address(0x0B1F7380DB647F1D85565B28978BA83861B99965),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 1, 1: 1}),
                addr: Account(storage={0: 1}),
                addr_2: Account(storage={0: 0}),
            },
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 1, 1: 1}),
                addr_3: Account(storage={0: 0}),
                addr_4: Account(storage={0: 0}),
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
