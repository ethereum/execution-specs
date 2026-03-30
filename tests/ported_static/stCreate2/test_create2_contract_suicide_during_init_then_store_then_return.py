"""
Test_create2_contract_suicide_during_init_then_store_then_return.

Ported from:
state_tests/stCreate2/CREATE2_ContractSuicideDuringInit_ThenStoreThenReturnFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stCreate2/CREATE2_ContractSuicideDuringInit_ThenStoreThenReturnFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create2_contract_suicide_during_init_then_store_then_return(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_create2_contract_suicide_during_init_then_store_then_return."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    contract_1 = Address(0xC94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xE8D4A51000)
    # Source: lll
    # { (CALL 150000 0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b 1 0 0 0 32) (SSTORE 1 (MLOAD 0)) }  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.CALL(
                gas=0x249F0,
                address=0xC94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                value=0x1,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x20,
            )
        )
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        balance=0xE8D4A51000,
        nonce=0,
        address=Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0 0x6d64600c6000556000526005601bf36000526001ff) (CREATE2 1 11 21 0) [[0]] 11 (RETURN 18 14) }  # noqa: E501
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0, value=0x6D64600C6000556000526005601BF36000526001FF
        )
        + Op.POP(Op.CREATE2(value=0x1, offset=0xB, size=0x15, salt=0x0))
        + Op.SSTORE(key=0x0, value=0xB)
        + Op.RETURN(offset=0x12, size=0xE)
        + Op.STOP,
        balance=0xE8D4A51000,
        nonce=0,
        address=Address(0xC94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=600000,
        value=10,
    )

    post = {
        Address(0x0000000000000000000000000000000000000001): Account(
            balance=1
        ),
        contract_0: Account(
            storage={
                1: 0x6000526005601BF36000526001FF000000000000000000000000000000000000,  # noqa: E501
            },
        ),
        contract_1: Account(storage={0: 11}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
