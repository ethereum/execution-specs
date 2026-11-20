"""
A REVERT with a big output should not be confused with a big code...

Ported from:
state_tests/stRevertTest/RevertOpcodeWithBigOutputInInitFiller.json

@manually-enhanced: Do not overwrite. Environment overrides dropped.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRevertTest/RevertOpcodeWithBigOutputInInitFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="-v0",
        ),
        pytest.param(
            0,
            0,
            1,
            id="-v1",
        ),
    ],
)
def test_revert_opcode_with_big_output_in_init(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """A REVERT with a big output should not be confused with a big code..."""
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    tx_data = [
        Op.SSTORE(key=0x0, value=0x1)
        + Op.REVERT(offset=0x0, size=0x1)
        + Op.SSTORE(key=0x1, value=0x11),
    ]
    tx_gas = [1600000]
    tx_value = [0, 10]

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
    )

    post = {
        compute_create_address(address=sender, nonce=0): Account.NONEXISTENT,
        sender: Account(nonce=1),
    }

    state_test(pre=pre, post=post, tx=tx)
