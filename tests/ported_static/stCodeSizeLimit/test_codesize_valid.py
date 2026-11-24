"""
Test_codesize_valid.

Ported from:
state_tests/stCodeSizeLimit/codesizeValidFiller.json

@manually-enhanced: Do not overwrite. Explicit gas values removed. Runs
from Frontier.
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
        "state_tests/stCodeSizeLimit/codesizeValidFiller.json",
        f"{LEGACY_URL}/codesizeValidFiller.json",
    ],
)
@pytest.mark.valid_from("Frontier")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1",
        ),
    ],
)
def test_codesize_valid(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_codesize_valid."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    env = Environment.for_fork(
        fork,
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=45000000,
    )

    tx_data = [
        Op.CODECOPY(dest_offset=0x0, offset=0xD, size=0x5ED5)
        + Op.RETURN(offset=0x0, size=0x5ED5),
        Op.CODECOPY(dest_offset=0x0, offset=0xD, size=0x6000)
        + Op.RETURN(offset=0x0, size=0x6000),
    ]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data[d],
        value=tx_value[v],
        protected=fork.supports_protected_txs(),
    )

    post = {
        compute_create_address(address=sender, nonce=0): Account(balance=1)
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
