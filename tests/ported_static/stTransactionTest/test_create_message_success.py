"""
Test_create_message_success.

Ported from:
state_tests/stTransactionTest/CreateMessageSuccessFiller.json
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
    ["state_tests/stTransactionTest/CreateMessageSuccessFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_message_success(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
) -> None:
    """Test_create_message_success."""
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
        gas_limit=1000000000000,
    )

    pre[sender] = Account(balance=0x17D78400)
    # Source: lll
    # {(MSTORE 0 0x600c600055) (CREATE 0 27 5)}
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0x600C600055)
        + Op.CREATE(value=0x0, offset=0x1B, size=0x5)
        + Op.STOP,
        nonce=0,
        address=Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=2131882 if fork >= Amsterdam else 131882,
        value=100,
    )

    post = {
        contract_0: Account(balance=100, nonce=1),
        compute_create_address(address=contract_0, nonce=0): Account(
            storage={0: 12}
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
