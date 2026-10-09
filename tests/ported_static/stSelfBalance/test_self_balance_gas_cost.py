"""
Test_self_balance_gas_cost.

Ported from:
state_tests/stSelfBalance/selfBalanceGasCostFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stSelfBalance/selfBalanceGasCostFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_self_balance_gas_cost(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_self_balance_gas_cost."""
    sender = pre.fund_eoa(amount=0x3635C9ADC5DEA00000)

    # Source: lll
    # (asm GAS SELFBALANCE GAS SWAP1 POP SWAP1 SUB 2 SWAP1 SUB 0x01 SSTORE)
    target = pre.deploy_contract(
        code=Op.GAS
        + Op.SELFBALANCE
        + Op.GAS
        + Op.SWAP1
        + Op.POP
        + Op.SWAP1
        + Op.SUB
        + Op.PUSH1[0x2]
        + Op.SWAP1
        + Op.SSTORE(key=0x1, value=Op.SUB)
        + Op.STOP,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
    )

    post = {target: Account(storage={1: 5})}

    state_test(pre=pre, post=post, tx=tx)
