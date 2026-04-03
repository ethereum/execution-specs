"""
Test_create_high_nonce_minus1.

Ported from:
state_tests/stCreateTest/CREATE_HighNonceMinus1Filler.yml
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
    ["state_tests/stCreateTest/CREATE_HighNonceMinus1Filler.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_high_nonce_minus1(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_create_high_nonce_minus1."""
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
        gas_limit=89128960,
    )

    pre[sender] = Account(balance=0x3B9ACA00)
    # Source: yul
    # byzantium
    # {
    #   // initcode: { return(0, 1) }
    #   mstore(0, 0x60016000f3000000000000000000000000000000000000000000000000000000)  # noqa: E501
    #   sstore(0, create(0, 0, 5))
    #   sstore(1, 1)
    #
    #   let noOptimization := msize()
    # }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0x60016000F3000000000000000000000000000000000000000000000000000000,  # noqa: E501
        )
        + Op.SSTORE(
            key=0x0, value=Op.CREATE(value=Op.DUP1, offset=0x0, size=0x5)
        )
        + Op.SSTORE(key=Op.DUP1, value=0x1)
        + Op.STOP,
        nonce=18446744073709551614,
        address=Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=16777216,
    )

    post = {
        sender: Account(nonce=1),
        contract_0: Account(
            storage={
                0: 0xD061B08A84EBC70FE797F9BD62F4269EF8274A13,
                1: 1,
            },
            nonce=18446744073709551615,
        ),
        Address(0xD061B08A84EBC70FE797F9BD62F4269EF8274A13): Account(
            code=bytes.fromhex("00")
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
