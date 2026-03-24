"""
https://ropsten.etherscan.io/tx/0x8ec445380649f6c75a042a438ea9256c2fab2a6a34...

Ported from:
tests/static/state_tests/stAttackTest/CrashingTransactionFiller.json
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

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stAttackTest/CrashingTransactionFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_crashing_transaction(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Https://ropsten.etherscan.io/tx/0x8ec445380649f6c75a042a438ea9256c..."""
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
        gas_limit=4712388,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000, nonce=3270)

    tx = Transaction(
        sender=sender,
        to=None,
        data=bytes.fromhex(
            "60606040525b5b61c3505a1115602c576040516034806039833901809050604051809103"  # noqa: E501
            "906000f0506006565b5b600a80606d6000396000f360606040525b3373ffffffffffffff"  # noqa: E501
            "ffffffffffffffffffffffffff16ff5b600a80602a6000396000f360606040526008565b"  # noqa: E501
            "0060606040526008565b00"
        ),
        gas_limit=4657786,
        gas_price=11,
        nonce=3270,
        value=1,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
