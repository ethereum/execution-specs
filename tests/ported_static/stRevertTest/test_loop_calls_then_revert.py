"""
Test_loop_calls_then_revert.

Ported from:
state_tests/stRevertTest/LoopCallsThenRevertFiller.json
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
    ["state_tests/stRevertTest/LoopCallsThenRevertFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_loop_calls_then_revert(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_loop_calls_then_revert."""
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    # Source: lll
    # { [[0]] (ADD 1 (SLOAD 0)) }
    addr = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.ADD(0x1, Op.SLOAD(key=0x0)))
        + Op.STOP,
    )
    # Source: raw
    # 0x5b6001600054036000556000600060006000600073<contract:0xb000000000000000000000000000000000000000>61c350f150600054600057  # noqa: E501
    target = pre.deploy_contract(
        code=Op.JUMPDEST
        + Op.SSTORE(key=0x0, value=Op.SUB(Op.SLOAD(key=0x0), 0x1))
        + Op.POP(
            Op.CALL(
                gas=0xC350,
                address=Op.PUSH20[addr],
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.JUMPI(pc=0x0, condition=Op.SLOAD(key=0x0)),
        storage={0: 850},
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
    )

    post = {
        target: Account(storage={0: 0}),
        addr: Account(storage={0: 850}),
    }

    state_test(pre=pre, post=post, tx=tx)
