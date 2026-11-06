"""
Test a CREATE whose init code CREATEs again near the call depth limit.

Ported from:
state_tests/stRevertTest/LoopCallsDepthThenRevert2Filler.json
state_tests/stRevertTest/LoopCallsDepthThenRevert3Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Conditional,
    Environment,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

MAX_CALL_DEPTH = 1024


@pytest.mark.ported_from(
    [
        "state_tests/stRevertTest/LoopCallsDepthThenRevert2Filler.json",
        "state_tests/stRevertTest/LoopCallsDepthThenRevert3Filler.json",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "create_depth",
    [
        pytest.param(1023, id="loop_calls_depth_then_revert2"),
        pytest.param(1022, id="loop_calls_depth_then_revert3"),
    ],
)
def test_loop_calls_depth_then_revert2(
    state_test: StateTestFiller,
    pre: Alloc,
    create_depth: int,
) -> None:
    """
    Self-call down to `create_depth`, then CREATE a contract there.

    The child's init code CREATEs a grandchild, which only succeeds
    when the child runs below the maximum call depth.
    """
    env = Environment(gas_limit=0x7FFFFFFFFFFFFFFF)
    sender = pre.fund_eoa(amount=0x13426172C74D822B878FE800000000)

    # Init code: CREATE(value=2, offset=0, size=0)
    create = Op.MSTORE(offset=0x0, value=0x600060006002F0) + Op.POP(
        Op.CREATE(value=0x3, offset=0x19, size=0x7)
    )
    # Source: raw
    # 0x6103ff60005414603f576001600054016000556000600060006000600073a0000000000000000000000000000000000000005af15061041a600054106053575b66600060006002f0600052600760196003f0505b  # noqa: E501
    contract = pre.deploy_contract(
        code=Conditional(
            condition=Op.EQ(Op.SLOAD(key=0x0), create_depth),
            if_true=create,
            if_false=Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
            + Op.POP(Op.CALL(address=Op.ADDRESS))
            + Conditional(
                condition=Op.LT(Op.SLOAD(key=0x0), 0x41A),
                if_false=create,
            ),
        ),
        balance=10,
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=9214364837600034817,
    )

    child = compute_create_address(address=contract, nonce=1)
    grandchild = compute_create_address(address=child, nonce=1)
    post: dict = {}
    if create_depth + 1 < MAX_CALL_DEPTH:
        post |= {
            child: Account(balance=1, nonce=2),
            grandchild: Account(balance=2, nonce=1),
        }
    else:
        post |= {
            child: Account(balance=3, nonce=1),
            grandchild: Account.NONEXISTENT,
        }
    post[contract] = Account(storage={0: create_depth}, balance=7)

    state_test(env=env, pre=pre, post=post, tx=tx)
