"""
A REVERT with a big output should not be confused with a big code...

Ported from:
tests/static/state_tests/stRevertTest
RevertOpcodeWithBigOutputInInitFiller.json
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
    [
        "tests/static/state_tests/stRevertTest/RevertOpcodeWithBigOutputInInitFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_value",
    [
        0,
        10,
    ],
    ids=["case0", "case1"],
)
@pytest.mark.pre_alloc_mutable
def test_revert_opcode_with_big_output_in_init(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_value: int,
) -> None:
    """A REVERT with a big output should not be confused with a big code..."""
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
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xE8D4A51000)

    tx = Transaction(
        sender=sender,
        to=None,
        data=bytes.fromhex("600160005560016000fd6011600155"),
        gas_limit=1600000,
        value=tx_value,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
