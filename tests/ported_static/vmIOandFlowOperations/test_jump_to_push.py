"""
Test jumps around and into the data of PUSH1-PUSH32.

Ported from:
state_tests/VMTests/vmIOandFlowOperations/jumpToPushFiller.yml
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

SENTINEL = 0x0BAD

CASES = [
    pytest.param(size, target, id=f"push{size}-{target}")
    for size in range(1, 33)
    for target in ("after_data", "first_data_byte", "last_data_byte")
    if not (size == 1 and target == "last_data_byte")
]


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmIOandFlowOperations/jumpToPushFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("push_size, target", CASES)
def test_jump_to_push(
    state_test: StateTestFiller,
    pre: Alloc,
    push_size: int,
    target: str,
) -> None:
    """Jump past PUSHn data (succeeds) or into it (fails)."""
    prefix = Op.SSTORE(0, 1)
    push_offset = len(prefix) + len(Op.JUMP(0))
    if target == "after_data":
        dest = push_offset + 1 + push_size
    elif target == "first_data_byte":
        dest = push_offset + 1
    elif target == "last_data_byte":
        dest = push_offset + push_size
    else:
        raise ValueError(f"Unknown target: {target}")
    code = (
        prefix
        + Op.JUMP(dest)
        + getattr(Op, f"PUSH{push_size}")[b"\x5b" * push_size]
        + Op.JUMPDEST
    )
    assert bytes(code)[dest] == Op.JUMPDEST.int()
    contract = pre.deploy_contract(code=code, storage={0: SENTINEL})
    tx = Transaction(sender=pre.fund_eoa(), to=contract)
    expected = 1 if target == "after_data" else SENTINEL
    post = {contract: Account(storage={0: expected})}
    state_test(pre=pre, post=post, tx=tx)
