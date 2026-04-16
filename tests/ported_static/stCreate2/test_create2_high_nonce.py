"""
Test_create2_high_nonce.

Ported from:
state_tests/stCreate2/CREATE2_HighNonceFiller.yml
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
    ["state_tests/stCreate2/CREATE2_HighNonceFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create2_high_nonce(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_create2_high_nonce."""
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
    # berlin
    # {
    #   // initcode: { return(0, 1) }
    #   mstore(0, 0x60016000f3000000000000000000000000000000000000000000000000000000)  # noqa: E501
    #   sstore(0, create2(0, 0, 5, 0))
    #   sstore(1, 1)
    # }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SHL(0xD8, 0x60016000F3)
        + Op.PUSH1[0x0]
        + Op.SWAP1
        + Op.DUP2
        + Op.MSTORE
        + Op.PUSH1[0x5]
        + Op.DUP2
        + Op.DUP1
        + Op.SSTORE(key=0x0, value=Op.CREATE2)
        + Op.SSTORE(key=Op.DUP1, value=0x1)
        + Op.STOP,
        nonce=18446744073709551615,
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
        contract_0: Account(storage={0: 0, 1: 1}, nonce=18446744073709551615),
        Address(
            0x77DD5D2A2B742CA01EE2CFFF306445E3741EF744
        ): Account.NONEXISTENT,
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
