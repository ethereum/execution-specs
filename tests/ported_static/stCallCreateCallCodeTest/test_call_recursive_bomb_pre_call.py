"""
Recursive call.

Ported from:
state_tests/stCallCreateCallCodeTest/CallRecursiveBombPreCallFiller.json
state_tests/stDelegatecallTestHomestead/CallRecursiveBombPreCallFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

from tests.ported_static.constants import HIGH_GAS_LIMIT

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

MAX_CALL_DEPTH = 1024


@pytest.mark.ported_from(
    [
        "state_tests/stCallCreateCallCodeTest/CallRecursiveBombPreCallFiller.json",  # noqa: E501
        "state_tests/stDelegatecallTestHomestead/CallRecursiveBombPreCallFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize("opcode", [Op.CALL, Op.DELEGATECALL])
def test_call_recursive_bomb_pre_call(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
) -> None:
    """
    Send value to an empty account, then enter a recursive call bomb.

    The bomb recurses into the address passed in calldata until the
    call depth limit. Entered by DELEGATECALL, its first frame counts in
    the target's storage and recursion starts one level deeper.
    """
    env = Environment(gas_limit=HIGH_GAS_LIMIT)
    sender = pre.fund_eoa(amount=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)

    # Source: lll
    # { [[ 0 ]] (+ (SLOAD 0) 1) [[ 1 ]] (CALL (- (GAS) 224000) (ADDRESS) 0 0 0 0 0) }  # noqa: E501
    bomb = pre.deploy_contract(
        code=Op.SSTORE(0, Op.ADD(Op.SLOAD(0), 1))
        + Op.CALLDATACOPY(dest_offset=0, offset=0, size=0x20)
        + Op.SSTORE(
            1,
            Op.CALL(
                gas=Op.SUB(Op.GAS, 224000),
                address=Op.CALLDATALOAD(0),
                args_size=0x20,
            ),
        ),
        balance=0xDE0B6B3A7640000,
    )
    # Source: lll
    # { (CALL 100000 0xbad304eb96065b2a98b57a48a06ae28d285a71b5 23 0 0 0 0)  (CALL 0x7ffffffffffffff <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 23 0 0 0 0)  }  # noqa: E501
    if opcode == Op.CALL:
        enter_bomb = Op.CALL(
            gas=0x7FFFFFFFFFFFFFF, address=bomb, value=23, args_size=0x20
        )
    else:
        enter_bomb = Op.DELEGATECALL(
            gas=0x7FFFFFFFFFFFFFF, address=bomb, args_size=0x20
        )
    target = pre.deploy_contract(
        code=Op.POP(
            Op.CALL(gas=100000, address=pre.nonexistent_account(), value=23)
        )
        + Op.MSTORE(0, bomb)
        + enter_bomb,
        balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        gas_limit=9214364837600034817,
    )

    if opcode == Op.CALL:
        post = {
            target: Account(storage={}),
            bomb: Account(storage={0: MAX_CALL_DEPTH, 1: 1}),
        }
    else:
        post = {
            target: Account(storage={0: 1, 1: 1}),
            bomb: Account(storage={0: MAX_CALL_DEPTH - 1, 1: 1}),
        }

    state_test(env=env, pre=pre, post=post, tx=tx)
