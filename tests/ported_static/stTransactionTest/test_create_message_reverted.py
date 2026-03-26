"""
test_create_message_reverted

Ported from:
state_tests/stTransactionTest/CreateMessageRevertedFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
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
    """test_create_message_reverted"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x2b75d0c814eb07c075fccbdd9a036faf651d9c46d7477d6c4f30772cfca90d38
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000000000,
    )

    pre[sender] = Account(balance=0x1c9c380)
    # Source: lll
    # {(MSTORE 0 0x600c600055) (CREATE 0 27 5)}
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x600c600055)
        + Op.CREATE(value=0x0, offset=0x1b, size=0x5) + Op.STOP,
        nonce=0,
        address=Address("0xc9b0ca064c8b73a1d845547cd28d4e97fe4ec8a0"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=21882,
        value=100,
        nonce=0,
        gas_price=10,
    )

    post = {
        sender: Account(nonce=1),
        target: Account(balance=0, nonce=0),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
