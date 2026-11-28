"""
DIV/SDIV/MOD/SMOD by zero tests.

Ported from:
state_tests/stSolidityTest/ByZeroFiller.json
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
    ["state_tests/stSolidityTest/ByZeroFiller.json"],
)
@pytest.mark.valid_from("Cancun")
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
        pytest.param(
            2,
            0,
            0,
            id="d2",
        ),
        pytest.param(
            3,
            0,
            0,
            id="d3",
        ),
    ],
)
def test_by_zero(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """DIV/SDIV/MOD/SMOD by zero tests."""
    sender = pre.fund_eoa(amount=0x8AC7230489E80000)

    tx_data = [
        Op.SSTORE(key=Op.DIV(0x1, 0x0), value=0x1) + Op.STOP,
        Op.SSTORE(key=Op.SDIV(0x1, 0x0), value=0x1) + Op.STOP,
        Op.SSTORE(key=Op.MOD(0x1, 0x0), value=0x1) + Op.STOP,
        Op.SSTORE(key=Op.SMOD(0x1, 0x0), value=0x1) + Op.STOP,
    ]
    tx_gas = [400000]

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data[d],
        gas_limit=tx_gas[g],
    )

    post = {
        compute_create_address(address=sender, nonce=0): Account(
            storage={0: 1}, code=b"", balance=0
        ),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(pre=pre, post=post, tx=tx)
