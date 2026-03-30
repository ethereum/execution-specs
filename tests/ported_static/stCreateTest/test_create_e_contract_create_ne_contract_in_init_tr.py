"""
Test_create_e_contract_create_ne_contract_in_init_tr.

Ported from:
state_tests/stCreateTest/CREATE_EContractCreateNEContractInInit_TrFiller.json
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
        "state_tests/stCreateTest/CREATE_EContractCreateNEContractInInit_TrFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_e_contract_create_ne_contract_in_init_tr(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_create_e_contract_create_ne_contract_in_init_tr."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0xC94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
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
    # {[[1]]12}
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0xC) + Op.STOP,
        balance=0xE8D4A51000,
        nonce=0,
        address=Address(0xC94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=None,
        data=Bytes(
            "6000600060006000600073c94f5374fce5edbc8e2a8697c15331677e6ebf0b61ea60f1506d64600c6000556000526005601bf3600052600e60126000f0"  # noqa: E501
        ),
        gas_limit=600000,
    )

    post = {
        contract_0: Account(storage={1: 12}),
        compute_create_address(address=sender, nonce=0): Account(nonce=2),
        Address(0x64E2EBD6405AF8CB348AEC519084D3FFF42EBBA6): Account(
            code=bytes.fromhex("600c600055")
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
