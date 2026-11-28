"""
Recursive STATICCALL bomb to the maximum call depth after a call to an
empty account.

Ported from:
state_tests/stStaticCall/static_CallRecursiveBombPreCallFiller.json
state_tests/stStaticCall/static_CallRecursiveBombPreCall2Filler.json

@manually-enhanced: Do not overwrite. Merged; the depth reached is stored.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    Op,
    StateTestFiller,
    Transaction,
)

from tests.ported_static.constants import HIGH_GAS_LIMIT

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

MAX_CALL_DEPTH = 1024
RETAINED_GAS = 224_000
BOMB_GAS = 0x7FFFFFFFFFFFFFF


@pytest.mark.ported_from(
    [
        "state_tests/stStaticCall/static_CallRecursiveBombPreCallFiller.json",
        "state_tests/stStaticCall/static_CallRecursiveBombPreCall2Filler.json",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.slow
@pytest.mark.parametrize("entry", [Op.DELEGATECALL, Op.STATICCALL])
def test_static_call_recursive_bomb_pre_call(
    state_test: StateTestFiller,
    pre: Alloc,
    entry: Op,
) -> None:
    """
    Verify a STATICCALL bomb entered by `entry` reaches the call depth
    limit.

    The bomb's address is passed as calldata, since in a DELEGATECALL
    frame ADDRESS is the caller's. Each bomb frame returns the number of
    bomb frames from itself down.
    """
    env = Environment(gas_limit=HIGH_GAS_LIMIT)

    bomb = pre.deploy_contract(
        code=Op.CALLDATACOPY(size=32)
        + Op.POP(
            Op.STATICCALL(
                gas=Op.SUB(Op.GAS, RETAINED_GAS),
                address=Op.CALLDATALOAD(0),
                args_size=32,
                ret_offset=32,
                ret_size=32,
            )
        )
        + Op.MSTORE(0, Op.ADD(Op.MLOAD(32), 1))
        + Op.RETURN(0, 32)
    )
    target = pre.deploy_contract(
        code=Op.POP(
            Op.STATICCALL(gas=100_000, address=pre.nonexistent_account())
        )
        + Op.MSTORE(0, bomb)
        + Op.SSTORE(
            0,
            entry(
                gas=BOMB_GAS,
                address=bomb,
                args_size=32,
                ret_offset=32,
                ret_size=32,
            ),
        )
        + Op.SSTORE(1, 1)
        + Op.SSTORE(2, Op.MLOAD(32))
        + Op.STOP
    )

    tx = Transaction(
        sender=pre.fund_eoa(), to=target, gas_limit=9214364837600034817
    )

    post = {target: Account(storage={0: 1, 1: 1, 2: MAX_CALL_DEPTH})}

    state_test(env=env, pre=pre, post=post, tx=tx)
