"""
Test_call_contract_to_create_contract_which_would_create_contract_in_ini...

Ported from:
state_tests/stInitCodeTest/CallContractToCreateContractWhichWouldCreateContractInInitCodeFiller.json
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
        "state_tests/stInitCodeTest/CallContractToCreateContractWhichWouldCreateContractInInitCodeFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_contract_to_create_contract_which_would_create_contract_in_init_code(  # noqa: E501
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_call_contract_to_create_contract_which_would_create_contract_i..."""  # noqa: E501
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x095E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000000,
    )

    # Source: lll
    # {(MSTORE 0 0x600c600055602060406000f0)(CREATE 0 20 12)}
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0x600C600055602060406000F0)
        + Op.CREATE(value=0x0, offset=0x14, size=0xC)
        + Op.STOP,
        balance=1,
        nonce=0,
        address=Address(0x095E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3B9ACA00)

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes("00"),
        gas_limit=200000,
    )

    post = {
        contract_0: Account(balance=1, nonce=1),
        Address(
            0x62C01474F089B07DAE603491675DC5B5748F7049
        ): Account.NONEXISTENT,
        sender: Account(nonce=1),
        compute_create_address(address=contract_0, nonce=0): Account(
            storage={0: 12}, nonce=2
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
