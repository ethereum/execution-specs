"""
Test_call_contract_to_create_contract_oog.

Ported from:
state_tests/stInitCodeTest/CallContractToCreateContractOOGFiller.json
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
    ["state_tests/stInitCodeTest/CallContractToCreateContractOOGFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_contract_to_create_contract_oog(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_call_contract_to_create_contract_oog."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xF79127A3004ABDE26A4CBD80C428CB10F829FA11B54D36E7B326F4F4A5927ACF
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
    # {(MSTORE 0 0x600c60005566602060406000f060205260076039f3)[[0]](CREATE 1 11 21)(CALL 0 (SLOAD 0) 0 0 0 0 0)}  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0, value=0x600C60005566602060406000F060205260076039F3
        )
        + Op.SSTORE(key=0x0, value=Op.CREATE(value=0x1, offset=0xB, size=0x15))
        + Op.CALL(
            gas=0x0,
            address=Op.SLOAD(key=0x0),
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        nonce=0,
        address=Address(0x1BC6342E077E772B0F4CC48116BC171F9A35D09E),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3B9ACA00)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes("00"),
        gas_limit=100000,
    )

    post = {
        target: Account(nonce=0),
        sender: Account(nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
