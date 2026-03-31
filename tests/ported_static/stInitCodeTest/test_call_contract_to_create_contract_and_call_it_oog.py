"""
Test_call_contract_to_create_contract_and_call_it_oog.

Ported from:
state_tests/stInitCodeTest/CallContractToCreateContractAndCallItOOGFiller.json
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
    Fork,
)
from execution_testing.vm import Op

from execution_testing.forks import Amsterdam

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stInitCodeTest/CallContractToCreateContractAndCallItOOGFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_contract_to_create_contract_and_call_it_oog(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
) -> None:
    """Test_call_contract_to_create_contract_and_call_it_oog."""
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
        gas_limit=100000000,
    )

    # Source: lll
    # {(MSTORE 0 0x600c60005566602060406000f060205260076039f3)[[0]](CREATE 1 11 21)(CALL 1000 (SLOAD 0) 0 0 0 0 0)}  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0, value=0x600C60005566602060406000F060205260076039F3
        )
        + Op.SSTORE(key=0x0, value=Op.CREATE(value=0x1, offset=0xB, size=0x15))
        + Op.CALL(
            gas=0x3E8,
            address=Op.SLOAD(key=0x0),
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=1000,
        nonce=0,
        address=Address(0x095E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87),  # noqa: E501
    )
    pre[sender] = Account(balance=0x5F5E100)

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes("00"),
        gas_limit=2203000 if fork >= Amsterdam else 203000,
    )

    post = {
        contract_0: Account(
            storage={0: 0xD2571607E241ECF590ED94B12D87C94BABE36DB6},
            nonce=1,
        ),
        sender: Account(nonce=1),
        compute_create_address(address=contract_0, nonce=0): Account(
            storage={0: 12}, balance=1, nonce=1
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
