"""
Test_static_create_contract_suicide_during_init_then_store_then_return.

Ported from:
state_tests/stStaticCall/static_CREATE_ContractSuicideDuringInit_ThenStoreThenReturnFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stStaticCall/static_CREATE_ContractSuicideDuringInit_ThenStoreThenReturnFiller.json"  # noqa: E501
    ],
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
def test_static_create_contract_suicide_during_init_then_store_then_return(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_create_contract_suicide_during_init_then_store_then_return."""  # noqa: E501
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0xC94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    contract_1 = Address(0xD94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    contract_2 = Address(0x094F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    contract_3 = Address(0x194F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
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
    # {[[1]]12}
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0xC) + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # {[[1]]12}
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0xC) + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # { (MSTORE 1 1) }
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x1, value=0x1) + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # {(MSTORE 1 1) }
    contract_3 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x1, value=0x1) + Op.STOP,
        nonce=0,
    )

    tx_data = [
        Op.POP(
            Op.STATICCALL(
                gas=0xEA60,
                address=contract_0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x0, value=0x64600C6000556000526005601BF3)
        + Op.SELFDESTRUCT(address=contract_1)
        + Op.POP(
            Op.STATICCALL(
                gas=0xEA60,
                address=contract_1,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(key=0x0, value=0xB)
        + Op.RETURN(offset=0x12, size=0xE),
        Op.POP(
            Op.STATICCALL(
                gas=0xEA60,
                address=contract_2,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x0, value=0x64600C6000556000526005601BF3)
        + Op.SELFDESTRUCT(address=contract_1)
        + Op.POP(
            Op.STATICCALL(
                gas=0xEA60,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(key=0x0, value=0xB)
        + Op.RETURN(offset=0x12, size=0xE),
    ]
    tx_gas = [600000]
    tx_value = [10]

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
    )

    post = {
        compute_create_address(address=sender, nonce=0): Account.NONEXISTENT,
        contract_0: Account(storage={1: 0}, balance=0),
        contract_1: Account(storage={1: 0}, balance=10),
        contract_2: Account(storage={1: 0}, balance=0),
        contract_3: Account(storage={1: 0}, balance=0),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
