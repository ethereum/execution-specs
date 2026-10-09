"""
Check the PC after doing call to a contract.

Ported from:
state_tests/stCallCodes/callcode_checkPCFiller.json
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
    ["state_tests/stCallCodes/callcode_checkPCFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_callcode_check_pc(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Check the PC after doing call to a contract."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: lll
    # { [[0]] 1 }
    addr = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x1) + Op.STOP,
        balance=0x2540BE400,
    )
    # Source: lll
    # { (CALL 1000000 <contract:0x1000000000000000000000000000000000000001> 0 0 64 0 64 ) [[3]] (PC) }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.POP(
            Op.CALL(
                gas=0xF4240,
                address=addr,
                value=0x0,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.SSTORE(key=0x3, value=Op.PC)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=1100000,
    )

    post = {target: Account(storage={3: 37})}

    state_test(pre=pre, post=post, tx=tx)
