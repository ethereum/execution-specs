"""
Test_static_raw_call_gas_ask.

Ported from:
state_tests/stStaticCall/static_RawCallGasAskFiller.json
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
    ["state_tests/stStaticCall/static_RawCallGasAskFiller.json"],
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
def test_static_raw_call_gas_ask(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_raw_call_gas_ask."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x094F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    contract_1 = Address(0x1000000000000000000000000000000000000000)
    contract_2 = Address(0x1000000000000000000000000000000000000001)
    contract_3 = Address(0x2000000000000000000000000000000000000001)
    contract_4 = Address(0x3000000000000000000000000000000000000001)
    contract_5 = Address(0x4000000000000000000000000000000000000001)
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: lll
    # { (MSTORE 0 (GAS)) }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.GAS) + Op.STOP,
        nonce=0,
        address=Address(0x094F5374FCE5EDBC8E2A8697C15331677E6EBF0B),  # noqa: E501
    )
    # Source: lll
    # { (CALL (GAS) (CALLDATALOAD 0) 0 0 0 0 0) }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.CALL(
            gas=Op.GAS,
            address=Op.CALLDATALOAD(offset=0x0),
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xE8D4A51000,
        nonce=0,
        address=Address(0x1000000000000000000000000000000000000000),  # noqa: E501
    )
    # Source: lll
    # { (STATICCALL 130000 0x094f5374fce5edbc8e2a8697c15331677e6ebf0b 0 0 0 0) [[1]] (GAS) }  # noqa: E501
    contract_3 = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.STATICCALL(
                gas=0x1FBD0,
                address=0x94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(key=0x1, value=Op.GAS)
        + Op.STOP,
        nonce=0,
        address=Address(0x2000000000000000000000000000000000000001),  # noqa: E501
    )
    # Source: lll
    # { (STATICCALL 130000 0x094f5374fce5edbc8e2a8697c15331677e6ebf0b 0 8000 0 8000) [[1]] (GAS) }  # noqa: E501
    contract_5 = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.STATICCALL(
                gas=0x1FBD0,
                address=0x94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                args_offset=0x0,
                args_size=0x1F40,
                ret_offset=0x0,
                ret_size=0x1F40,
            )
        )
        + Op.SSTORE(key=0x1, value=Op.GAS)
        + Op.STOP,
        nonce=0,
        address=Address(0x4000000000000000000000000000000000000001),  # noqa: E501
    )
    # Source: lll
    # { (STATICCALL 3000000 0x094f5374fce5edbc8e2a8697c15331677e6ebf0b 0 8000 0 8000) [[1]] (GAS) }  # noqa: E501
    contract_4 = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.STATICCALL(
                gas=0x2DC6C0,
                address=0x94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                args_offset=0x0,
                args_size=0x1F40,
                ret_offset=0x0,
                ret_size=0x1F40,
            )
        )
        + Op.SSTORE(key=0x1, value=Op.GAS)
        + Op.STOP,
        nonce=0,
        address=Address(0x3000000000000000000000000000000000000001),  # noqa: E501
    )
    # Source: lll
    # {  (STATICCALL 3000000 0x094f5374fce5edbc8e2a8697c15331677e6ebf0b 0 0 0 0) [[1]] (GAS) }  # noqa: E501
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.STATICCALL(
                gas=0x2DC6C0,
                address=0x94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(key=0x1, value=Op.GAS)
        + Op.STOP,
        nonce=0,
        address=Address(0x1000000000000000000000000000000000000001),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_2: Account(storage={1: 0xE9F83})},
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_3: Account(storage={1: 0xE9F83})},
        },
        {
            "indexes": {"data": 2, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_4: Account(storage={1: 0xE9C1B})},
        },
        {
            "indexes": {"data": 3, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_5: Account(storage={1: 0xE9C1B})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(contract_2, left_padding=True),
        Hash(contract_3, left_padding=True),
        Hash(contract_4, left_padding=True),
        Hash(contract_5, left_padding=True),
    ]
    tx_gas = [1000000]

    tx = Transaction(
        sender=sender,
        to=contract_1,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
