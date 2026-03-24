"""
Account attempts to send tx to create a contract on a non-empty address.

Ported from:
tests/static/state_tests/stEIP3607/initCollidingWithNonEmptyAccountFiller.yml
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
        "tests/static/state_tests/stEIP3607/initCollidingWithNonEmptyAccountFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "60206000f3",
        "6001600055600080808061271073d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d05af100",  # noqa: E501
        "60016000556000602081612710f500",
        "600160005560206000612710f000",
        "6001600055600080808073d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d05af400",
    ],
    ids=["case0", "case1", "case2", "case3", "case4"],
)
@pytest.mark.pre_alloc_mutable
def test_init_colliding_with_non_empty_account(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Account attempts to send tx to create a contract on a non-empty..."""
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
        gas_limit=71794957647893862,
    )

    pre[coinbase] = Account(balance=0, nonce=1)
    # Source: raw bytecode
    pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x0),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: raw bytecode
    pre.deploy_contract(
        code=bytes.fromhex("00"),
        nonce=0,
        address=Address("0xd0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0d0"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data,
        gas_limit=400000,
        value=100000,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
