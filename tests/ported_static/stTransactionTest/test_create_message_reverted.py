"""
Test_create_message_reverted.

Ported from:
state_tests/stTransactionTest/CreateMessageRevertedFiller.json
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
    ["state_tests/stTransactionTest/CreateMessageRevertedFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_message_reverted(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_create_message_reverted."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x2B75D0C814EB07C075FCCBDD9A036FAF651D9C46D7477D6C4F30772CFCA90D38
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000000000,
    )

    pre[sender] = Account(balance=0x1C9C380)
    # Source: lll
    # {(MSTORE 0 0x600c600055) (CREATE 0 27 5)}
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0x600C600055)
        + Op.CREATE(value=0x0, offset=0x1B, size=0x5)
        + Op.STOP,
        nonce=0,
        address=Address(0xC9B0CA064C8B73A1D845547CD28D4E97FE4EC8A0),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=21882,
        value=100,
    )

    post = {
        sender: Account(nonce=1),
        target: Account(balance=0, nonce=0),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
