"""
Test_call_the_contract_to_create_empty_contract.

Ported from:
state_tests/stInitCodeTest/CallTheContractToCreateEmptyContractFiller.json
"""

import pytest
from execution_testing import (
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
        "state_tests/stInitCodeTest/CallTheContractToCreateEmptyContractFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_the_contract_to_create_empty_contract(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_call_the_contract_to_create_empty_contract."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x095E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87)
    sender = pre.fund_eoa(amount=0x989680)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: lll
    # {(CREATE 0 0 32)}
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.CREATE(value=0x0, offset=0x0, size=0x20) + Op.STOP,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes("00"),
        gas_limit=100000,
        value=1,
    )

    post = {
        contract_0: Account(balance=1, nonce=1),
        sender: Account(nonce=1),
        compute_create_address(address=contract_0, nonce=0): Account(
            storage={}, code=b"", balance=0, nonce=1
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
