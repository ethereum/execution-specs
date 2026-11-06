"""
Test execution environment opcodes in a called frame.

Ported from:
state_tests/VMTests/vmTests/envInfoFiller.yml
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Op,
    StateTestFiller,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

SENTINEL = 0x0BAD
CALL_VALUE = 0x10
GAS_PRICE = 4660
MAX_UINT = 2**256 - 1


def store_copied_code(offset: int, size: int) -> Bytecode:
    """Copy code to memory and store the first memory word."""
    return (
        Op.CODECOPY(dest_offset=0, offset=offset, size=size)
        + Op.SSTORE(0, Op.MLOAD(0))
        + Op.STOP
    )


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmTests/envInfoFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "case",
    [
        "address",
        "codecopy",
        "codecopy_len0",
        "codecopy_neg_offset",
        "caller",
        "callvalue",
        "codesize",
        "gasprice",
        "origin",
        "calldatasize",
    ],
)
def test_env_info(
    state_test: StateTestFiller,
    pre: Alloc,
    case: str,
) -> None:
    """Store an environment value observed by a contract called with value."""
    sender = pre.fund_eoa()
    code: Bytecode
    if case == "codecopy":
        code = store_copied_code(offset=0, size=7)
    elif case == "codecopy_len0":
        code = store_copied_code(offset=0, size=0)
    elif case == "codecopy_neg_offset":
        code = store_copied_code(offset=MAX_UINT - 5, size=8)
    else:
        opcode = {
            "address": Op.ADDRESS,
            "caller": Op.CALLER,
            "callvalue": Op.CALLVALUE,
            "codesize": Op.CODESIZE,
            "gasprice": Op.GASPRICE,
            "origin": Op.ORIGIN,
            "calldatasize": Op.CALLDATASIZE,
        }[case]
        code = Op.SSTORE(0, opcode) + Op.STOP
    contract = pre.deploy_contract(code=code, storage={0: SENTINEL})
    caller = pre.deploy_contract(
        code=Op.CALL(address=contract, value=CALL_VALUE) + Op.STOP,
        balance=CALL_VALUE,
    )

    expected: int | bytes
    if case == "address":
        expected = contract
    elif case == "codecopy":
        expected = bytes(code)[:7].ljust(32, b"\0")
    elif case == "caller":
        expected = caller
    elif case == "callvalue":
        expected = CALL_VALUE
    elif case == "codesize":
        expected = len(code)
    elif case == "gasprice":
        expected = GAS_PRICE
    elif case == "origin":
        expected = sender
    elif case in ("codecopy_len0", "codecopy_neg_offset", "calldatasize"):
        expected = 0
    else:
        raise ValueError(f"Unknown case: {case}")

    tx = Transaction(sender=sender, to=caller, gas_price=GAS_PRICE)
    post = {contract: Account(storage={0: expected})}
    state_test(pre=pre, post=post, tx=tx)
