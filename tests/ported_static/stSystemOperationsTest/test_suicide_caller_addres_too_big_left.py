"""
Test_suicide_caller_addres_too_big_left.

Ported from:
state_tests/stSystemOperationsTest/suicideCallerAddresTooBigLeftFiller.json
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
        "state_tests/stSystemOperationsTest/suicideCallerAddresTooBigLeftFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_suicide_caller_addres_too_big_left(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_suicide_caller_addres_too_big_left."""
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
        gas_limit=10000000,
    )

    # Source: lll
    # { [[0]] (CALLER) (SELFDESTRUCT 0xaaa94f5374fce5edbc8e2a8697c15331677e6ebf0b)}  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.CALLER)
        + Op.SELFDESTRUCT(address=0xAAA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x095E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=1000000,
        value=0x186A0,
    )

    post = {
        sender: Account(nonce=1),
        contract_0: Account(
            storage={0: 0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B},
            balance=0,
            nonce=0,
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
