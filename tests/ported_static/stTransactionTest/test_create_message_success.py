"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stTransactionTest/CreateMessageSuccessFiller.json
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
    [
        "tests/static/state_tests/stTransactionTest/CreateMessageSuccessFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_message_success(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
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
    # Source: LLL
    # {(MSTORE 0 0x600c600055) (CREATE 0 27 5)}
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=0x600C600055)
            + Op.CREATE(value=0x0, offset=0x1B, size=0x5)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=131882,
        value=100,
    )

    post = {
        Address("0xf1ecf98489fa9ed60a664fc4998db699cfa39d40"): Account(
            storage={0: 12},
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
