"""
Test_call_ecrecover0_0input.

Ported from:
state_tests/stPreCompiledContracts2/CallEcrecover0_0inputFiller.json
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
    ["state_tests/stPreCompiledContracts2/CallEcrecover0_0inputFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_call_ecrecover0_0input(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_call_ecrecover0_0input."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: lll
    # { [[ 2 ]] (CALL 300000 1 0 0 128 128 32) [[ 0 ]] (MOD (MLOAD 128) (EXP 2 160)) }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x2,
            value=Op.CALL(
                gas=0x493E0,
                address=0x1,
                value=0x0,
                args_offset=0x0,
                args_size=0x80,
                ret_offset=0x80,
                ret_size=0x20,
            ),
        )
        + Op.SSTORE(
            key=0x0, value=Op.MOD(Op.MLOAD(offset=0x80), Op.EXP(0x2, 0xA0))
        )
        + Op.STOP,
        balance=0x1312D00,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=3652240,
        value=0x186A0,
    )

    post = {target: Account(storage={2: 1})}

    state_test(pre=pre, post=post, tx=tx)
