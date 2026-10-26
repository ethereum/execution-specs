"""
Test_suicide_non_const.

Ported from:
state_tests/stArgsZeroOneBalance/suicideNonConstFiller.yml
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stArgsZeroOneBalance/suicideNonConstFiller.yml"],
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
def test_suicide_non_const(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_suicide_non_const."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: lll
    # { (SELFDESTRUCT (BALANCE 0x095e7baea6a6c7c4c2dfeb977efac326af552d87)) }
    contract_0_code = (
        Op.SELFDESTRUCT(address=Op.BALANCE(address=Op.ADDRESS)) + Op.STOP
    )
    contract_0 = pre.deploy_contract(
        code=contract_0_code,
    )

    tx_data = [
        Bytes(""),
    ]
    tx_gas = [400000]
    tx_value = [0, 1]

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
    )

    post = {
        contract_0: Account(
            storage={},
            code=contract_0_code,
            balance=0,
            nonce=1,
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
