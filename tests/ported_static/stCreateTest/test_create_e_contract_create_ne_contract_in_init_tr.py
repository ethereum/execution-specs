"""
Test_create_e_contract_create_ne_contract_in_init_tr.

Ported from:
state_tests/stCreateTest/CREATE_EContractCreateNEContractInInit_TrFiller.json
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
        balance=0xE8D4A51000,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=None,
        data=Op.POP(
            Op.CALL(
                gas=0xEA60,
                address=contract_0,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x0, value=0x64600C6000556000526005601BF3)
        + Op.CREATE(value=0x0, offset=0x12, size=0xE),
        gas_limit=600000,
    )

    post = {
        contract_0: Account(storage={1: 12}),
        compute_create_address(address=sender, nonce=0): Account(nonce=2),
        compute_create_address(
            address=compute_create_address(address=sender, nonce=0), nonce=1
        ): Account(code=bytes.fromhex("600c600055")),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
