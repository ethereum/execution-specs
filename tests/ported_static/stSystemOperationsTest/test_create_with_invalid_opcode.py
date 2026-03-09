"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stSystemOperationsTest
createWithInvalidOpcodeFiller.json
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
        "tests/static/state_tests/stSystemOperationsTest/createWithInvalidOpcodeFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_with_invalid_opcode(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.PREVRANDAO
            + Op.TIMESTAMP
            + Op.TIMESTAMP
            + Op.TIMESTAMP
            + Op.TIMESTAMP
            + Op.GASLIMIT
            + Op.MSTORE8(offset=Op.TIMESTAMP, value=Op.NUMBER)
            + Op.CREATE
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xcc73f3508071f505fb5a5c6108b9444fe05fdd4d"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=300000,
        value=100000,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
