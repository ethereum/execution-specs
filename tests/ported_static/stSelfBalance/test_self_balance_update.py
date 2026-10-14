"""
Test_self_balance_update.

Ported from:
state_tests/stSelfBalance/selfBalanceUpdateFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Amsterdam
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stSelfBalance/selfBalanceUpdateFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_self_balance_update(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
) -> None:
    """Test_self_balance_update."""
    sender = pre.fund_eoa(amount=0x3635C9ADC5DEA00000)

    # Source: lll
    # (asm SELFBALANCE DUP1 1 SSTORE 0 0 0 0 1 0 0 CALL POP SELFBALANCE DUP1 2 SSTORE SWAP1 SUB 3 SSTORE)  # noqa: E501
    target = pre.deploy_contract(
        code=Op.SELFBALANCE
        + Op.SSTORE(key=0x1, value=Op.DUP1)
        + Op.POP(
            Op.CALL(
                gas=0x0,
                address=0x0,
                value=0x1,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SELFBALANCE
        + Op.SSTORE(key=0x2, value=Op.DUP1)
        + Op.SWAP1
        + Op.SSTORE(key=0x3, value=Op.SUB)
        + Op.STOP,
        balance=500,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=2200000 if fork >= Amsterdam else 200000,
    )

    post = {target: Account(storage={1: 500, 2: 499, 3: 1})}

    state_test(pre=pre, post=post, tx=tx)
