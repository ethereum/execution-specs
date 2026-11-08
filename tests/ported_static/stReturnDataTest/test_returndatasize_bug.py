"""
RETURNDATASIZE after a failing CALL (due to insufficient balance)...

Ported from:
state_tests/stReturnDataTest/returndatasize_bugFiller.json
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
    ["state_tests/stReturnDataTest/returndatasize_bugFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_returndatasize_bug(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """RETURNDATASIZE after a failing CALL (due to insufficient balance)..."""
    sender = pre.fund_eoa(amount=0x6400000000)

    # Source: lll
    # { (CALL 10 1 50000 0 0 0 0) (SSTORE 1 1) }
    addr = pre.deploy_contract(
        code=Op.POP(
            Op.CALL(
                gas=0xA,
                address=0x1,
                value=0xC350,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.STOP,
    )
    # Source: lll
    # { (CALL 1 <contract:0x1f572e5295c57f15886f9b263e2f6d2d6c7b5ec6> 50000 0 0 0 0) (SSTORE 0 (RETURNDATASIZE)) }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.POP(
            Op.CALL(
                gas=0x1,
                address=addr,
                value=0xC350,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
        + Op.STOP,
        storage={0: 1},
        balance=0xDE0B6B3A7640000,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=100000,
    )

    post = {
        target: Account(storage={0: 0}),
        addr: Account(storage={1: 0}),
    }

    state_test(pre=pre, post=post, tx=tx)
