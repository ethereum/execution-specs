"""
STATICCALL with input and output areas over the caller's memory.

Ported from:
state_tests/stStaticCall/static_callOutput1Filler.json
state_tests/stStaticCall/static_callOutput2Filler.json
state_tests/stStaticCall/static_callOutput3Filler.json
state_tests/stStaticCall/static_callOutput3FailFiller.json
state_tests/stStaticCall/static_callOutput3partialFiller.json
state_tests/stStaticCall/static_callOutput3partialFailFiller.json

@manually-enhanced: Do not overwrite. Merged; added a returning callee.
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

MEMORY_WORD = (
    0x5E20A0453CECD065EA59C37AC63E079EE08998B6045136A8CE6635C7912EC0B6
)
RETURNED_WORD = 2**256 - 1
OUTPUT_SLOT = 0
SUCCESS_SLOT = 1
SUCCESS_SENTINEL = 0xFF


@pytest.mark.ported_from(
    [
        "state_tests/stStaticCall/static_callOutput1Filler.json",
        "state_tests/stStaticCall/static_callOutput2Filler.json",
        "state_tests/stStaticCall/static_callOutput3Filler.json",
        "state_tests/stStaticCall/static_callOutput3FailFiller.json",
        "state_tests/stStaticCall/static_callOutput3partialFiller.json",
        "state_tests/stStaticCall/static_callOutput3partialFailFiller.json",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "args_size, ret_size",
    [
        pytest.param(0, 0, id="output1"),
        pytest.param(32, 0, id="output2"),
        pytest.param(0, 32, id="output3"),
        pytest.param(0, 10, id="output3partial"),
    ],
)
@pytest.mark.parametrize("callee_kind", ["sstore", "underflow", "returns"])
def test_static_call_output(
    state_test: StateTestFiller,
    pre: Alloc,
    args_size: int,
    ret_size: int,
    callee_kind: str,
) -> None:
    """
    Verify the caller's memory after a STATICCALL whose output area
    overlaps its input.

    A callee that writes storage or underflows the stack fails and leaves
    the memory alone; one that returns a word copies its first `ret_size`
    bytes over the memory.
    """
    callee_code: Bytecode
    if callee_kind == "sstore":
        callee_code = Op.SSTORE(0, Op.ADD(1, 1))
    elif callee_kind == "underflow":
        callee_code = Op.ADD + Op.SSTORE(0, Op.ADD(1, 1))
    elif callee_kind == "returns":
        callee_code = Op.MSTORE(0, RETURNED_WORD) + Op.RETURN(0, 32)
    else:
        raise ValueError(f"Unknown callee kind: {callee_kind}")
    callee = pre.deploy_contract(code=callee_code)
    caller = pre.deploy_contract(
        code=Op.MSTORE(0, MEMORY_WORD)
        + Op.SSTORE(
            SUCCESS_SLOT,
            Op.STATICCALL(
                address=callee, args_size=args_size, ret_size=ret_size
            ),
        )
        + Op.SSTORE(OUTPUT_SLOT, Op.MLOAD(0))
        + Op.STOP,
        storage={SUCCESS_SLOT: SUCCESS_SENTINEL},
    )

    tx = Transaction(sender=pre.fund_eoa(), to=caller)

    succeeds = callee_kind == "returns"
    memory = bytearray(MEMORY_WORD.to_bytes(32, "big"))
    if succeeds:
        memory[:ret_size] = RETURNED_WORD.to_bytes(32, "big")[:ret_size]
    post = {
        caller: Account(
            storage={
                OUTPUT_SLOT: int.from_bytes(memory, "big"),
                SUCCESS_SLOT: int(succeeds),
            }
        )
    }

    state_test(pre=pre, post=post, tx=tx)
