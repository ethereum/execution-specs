"""
https://ropsten.etherscan.io/tx/0x8ec445380649f6c75a042a438ea9256c2fab2a6a3437904c9e5a712fcbf8a54a

Ported from:
state_tests/stAttackTest/CrashingTransactionFiller.json
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
    ["state_tests/stAttackTest/CrashingTransactionFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_crashing_transaction(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """https://ropsten."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=4712388,
    )

    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=3270)


    tx = Transaction(
        sender=sender,
        to=None,
        data=bytes.fromhex("60606040525b5b61c3505a1115602c576040516034806039833901809050604051809103906000f0506006565b5b600a80606d6000396000f360606040525b3373ffffffffffffffffffffffffffffffffffffffff16ff5b600a80602a6000396000f360606040526008565b0060606040526008565b00"),  # noqa: E501
        gas_limit=4657786,
        value=1,
        nonce=3270,
        gas_price=11,
    )

    post = {
        sender: Account(nonce=3271),
        Address("0xecbf9aa676d9e0bbba7e517d1350c1b64f8c6779"): Account(
                code=bytes.fromhex("60606040526008565b00"),
                balance=1,
                nonce=124,
            ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
