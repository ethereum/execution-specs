"""
Call a Solidity method that never terminates.

`testInfiniteLoop()` loops until out of gas; `testRecursiveMethods()`
and `testRecursiveMethods2()` call each other until the stack overflows.
Both runs fail and roll back the value sent with the call.

Ported from:
state_tests/stSolidityTest/CallInfiniteLoopFiller.json
state_tests/stSolidityTest/CallRecursiveMethodsFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Bytes,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

# Source: raw
# 0x60003560e060020a90048063296df0df1460295780634893d88a146035578063981a316514604157005b602f604d565b60006000f35b603b6062565b60006000f35b6047605a565b60006000f35b5b600115605857604e565b565b60606062565b565b6068605a565b56  # noqa: E501
INFINITE_LOOP_BUILD = (
    Op.CALLDATALOAD(offset=0x0)
    + Op.EXP(0x2, 0xE0)
    + Op.SWAP1
    + Op.DIV
    + Op.JUMPI(pc=0x29, condition=Op.EQ(0x296DF0DF, Op.DUP1))
    + Op.JUMPI(pc=0x35, condition=Op.EQ(0x4893D88A, Op.DUP1))
    + Op.JUMPI(pc=0x41, condition=Op.EQ(0x981A3165, Op.DUP1))
    + Op.STOP
    + Op.JUMPDEST
    + Op.PUSH1[0x2F]
    + Op.JUMP(pc=0x4D)
    + Op.JUMPDEST
    + Op.RETURN(offset=0x0, size=0x0)
    + Op.JUMPDEST
    + Op.PUSH1[0x3B]
    + Op.JUMP(pc=0x62)
    + Op.JUMPDEST
    + Op.RETURN(offset=0x0, size=0x0)
    + Op.JUMPDEST
    + Op.PUSH1[0x47]
    + Op.JUMP(pc=0x5A)
    + Op.JUMPDEST
    + Op.RETURN(offset=0x0, size=0x0)
    + Op.JUMPDEST * 2
    + Op.JUMPI(pc=0x58, condition=Op.ISZERO(0x1))
    + Op.JUMP(pc=0x4E)
    + Op.JUMPDEST
    + Op.JUMP
    + Op.JUMPDEST
    + Op.PUSH1[0x60]
    + Op.JUMP(pc=0x62)
    + Op.JUMPDEST
    + Op.JUMP
    + Op.JUMPDEST
    + Op.PUSH1[0x68]
    + Op.JUMP(pc=0x5A)
    + Op.JUMPDEST
    + Op.JUMP
)

# Source: raw
# 0x7c01000000000000000000000000000000000000000000000000000000006000350463296df0df811460415780634893d88a14604d578063981a316514605957005b60476065565b60006000f35b6053607a565b60006000f35b605f6072565b60006000f35b5b6001156070576066565b565b6078607a565b565b60806072565b56  # noqa: E501
RECURSIVE_METHODS_BUILD = (
    Op.DIV(
        Op.CALLDATALOAD(offset=0x0),
        0x100000000000000000000000000000000000000000000000000000000,
    )
    + Op.JUMPI(pc=0x41, condition=Op.EQ(Op.DUP2, 0x296DF0DF))
    + Op.JUMPI(pc=0x4D, condition=Op.EQ(0x4893D88A, Op.DUP1))
    + Op.JUMPI(pc=0x59, condition=Op.EQ(0x981A3165, Op.DUP1))
    + Op.STOP
    + Op.JUMPDEST
    + Op.PUSH1[0x47]
    + Op.JUMP(pc=0x65)
    + Op.JUMPDEST
    + Op.RETURN(offset=0x0, size=0x0)
    + Op.JUMPDEST
    + Op.PUSH1[0x53]
    + Op.JUMP(pc=0x7A)
    + Op.JUMPDEST
    + Op.RETURN(offset=0x0, size=0x0)
    + Op.JUMPDEST
    + Op.PUSH1[0x5F]
    + Op.JUMP(pc=0x72)
    + Op.JUMPDEST
    + Op.RETURN(offset=0x0, size=0x0)
    + Op.JUMPDEST * 2
    + Op.JUMPI(pc=0x70, condition=Op.ISZERO(0x1))
    + Op.JUMP(pc=0x66)
    + Op.JUMPDEST
    + Op.JUMP
    + Op.JUMPDEST
    + Op.PUSH1[0x78]
    + Op.JUMP(pc=0x7A)
    + Op.JUMPDEST
    + Op.JUMP
    + Op.JUMPDEST
    + Op.PUSH1[0x80]
    + Op.JUMP(pc=0x72)
    + Op.JUMPDEST
    + Op.JUMP
)


@pytest.mark.ported_from(
    [
        "state_tests/stSolidityTest/CallInfiniteLoopFiller.json",
        "state_tests/stSolidityTest/CallRecursiveMethodsFiller.json",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "code, selector, gas_limit",
    [
        pytest.param(
            INFINITE_LOOP_BUILD,
            "296df0df",
            300_000,
            id="call_infinite_loop",
        ),
        pytest.param(
            RECURSIVE_METHODS_BUILD,
            "981a3165",
            60_000,
            id="call_recursive_methods",
        ),
    ],
)
def test_call_non_terminating_method(
    state_test: StateTestFiller,
    pre: Alloc,
    code: Bytecode,
    selector: str,
    gas_limit: int,
) -> None:
    """Call the method with value; the failure keeps the value out."""
    sender = pre.fund_eoa()
    target = pre.deploy_contract(code=code)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(selector),
        gas_limit=gas_limit,
        value=1,
    )

    post = {
        target: Account(balance=0),
        sender: Account(nonce=1),
    }

    state_test(pre=pre, post=post, tx=tx)
