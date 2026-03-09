"""
create fails because init code has stack size >1024.

Ported from:
tests/static/state_tests/stCallCreateCallCodeTest
createInitFailStackSizeLargerThan1024Filler.json
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
        "tests/static/state_tests/stCallCreateCallCodeTest/createInitFailStackSizeLargerThan1024Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_init_fail_stack_size_larger_than1024(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Create fails because init code has stack size >1024."""
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
        gas_limit=1000000000,
    )

    # Source: LLL
    # {(MSTORE 0 0x6103ff6000525b7f0102030405060708090a0102030405060708090a01020304) (MSTORE 32 0x05060708090a0102600160005103600052600051600657000000000000000000 ) (SELFDESTRUCT (CREATE 1 0 64)) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0x6103FF6000525B7F0102030405060708090A0102030405060708090A01020304,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0x5060708090A0102600160005103600052600051600657000000000000000000,  # noqa: E501
            )
            + Op.SELFDESTRUCT(
                address=Op.CREATE(value=0x1, offset=0x0, size=0x40)
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x0ee6db8c4a76cab3bb0584e06916cea75d307db0"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=2200000,
        value=100000,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
