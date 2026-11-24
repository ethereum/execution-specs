"""
Test_codesize_init.

Ported from:
state_tests/stCodeSizeLimit/codesizeInitFiller.json

@manually-enhanced: Do not overwrite. Runs from Frontier.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

LEGACY_URL = (
    "https://github.com/ethereum/legacytests/blob/master/src/LegacyTests"
    "/Constantinople/GeneralStateTestsFiller/stCodeSizeLimit"
)


@pytest.mark.ported_from(
    [
        "state_tests/stCodeSizeLimit/codesizeInitFiller.json",
        f"{LEGACY_URL}/codesizeInitFiller.json",
    ],
)
@pytest.mark.valid_from("Frontier")
def test_codesize_init(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test_codesize_init."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    env = Environment.for_fork(
        fork,
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=20000000,
    )

    tx = Transaction(
        sender=sender,
        to=None,
        data=Op.SSTORE(key=0x1, value=Op.CODESIZE)
        + Op.SSTORE(key=0x2, value=Op.EXTCODESIZE(address=Op.ADDRESS))
        + Op.STOP,
        gas_limit=15000000,
        protected=fork.supports_protected_txs(),
    )

    post = {
        compute_create_address(address=sender, nonce=0): Account(
            storage={1: 10, 2: 0}, balance=0
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
