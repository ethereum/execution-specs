"""
Test_create_e_contract_then_call_to_non_existent_acc.

Ported from:
state_tests/stCreateTest/CREATE_EContract_ThenCALLToNonExistentAccFiller.json
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
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stCreateTest/CREATE_EContract_ThenCALLToNonExistentAccFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_e_contract_then_call_to_non_existent_acc(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_create_e_contract_then_call_to_non_existent_acc."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
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
    # { [[0]](GAS) [[1]] (CREATE 0 0 32) [[2]](GAS) [[3]] (CALL 60000 0xe1ecf98489fa9ed60a664fc4998db699cfa39d40 0 0 0 0 0) [[100]] (GAS) }  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.GAS)
        + Op.SSTORE(key=0x1, value=Op.CREATE(value=0x0, offset=0x0, size=0x20))
        + Op.SSTORE(key=0x2, value=Op.GAS)
        + Op.SSTORE(
            key=0x3,
            value=Op.CALL(
                gas=0xEA60,
                address=0xE1ECF98489FA9ED60A664FC4998DB699CFA39D40,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x64, value=Op.GAS)
        + Op.STOP,
        nonce=0,
        address=Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=600000,
    )

    post = {
        contract_0: Account(
            storage={
                0: 0x8D5B6,
                1: compute_create_address(address=contract_0, nonce=0),
                2: 0x7ABF8,
                3: 1,
                100: 0x6F50B,
            },
        ),
        compute_create_address(address=contract_0, nonce=0): Account(nonce=1),
        Address(
            0xE1ECF98489FA9ED60A664FC4998DB699CFA39D40
        ): Account.NONEXISTENT,
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
