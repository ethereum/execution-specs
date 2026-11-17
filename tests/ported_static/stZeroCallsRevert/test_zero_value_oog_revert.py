"""
Zero-value CALL / CALLCODE / DELEGATECALL in a transaction that runs out of
gas, to different kinds of recipient.

Ported from:
state_tests/stZeroCallsRevert/ZeroValue_CALL_OOGRevertFiller.json
state_tests/stZeroCallsRevert/ZeroValue_CALL_ToEmpty_OOGRevert_ParisFiller.json
state_tests/stZeroCallsRevert/ZeroValue_CALL_ToNonZeroBalance_OOGRevertFiller.json
state_tests/stZeroCallsRevert/ZeroValue_CALL_ToOneStorageKey_OOGRevert_ParisFiller.json
state_tests/stZeroCallsRevert/ZeroValue_CALLCODE_OOGRevertFiller.json
state_tests/stZeroCallsRevert/ZeroValue_CALLCODE_ToEmpty_OOGRevert_ParisFiller.json
state_tests/stZeroCallsRevert/ZeroValue_CALLCODE_ToNonZeroBalance_OOGRevertFiller.json
state_tests/stZeroCallsRevert/ZeroValue_CALLCODE_ToOneStorageKey_OOGRevert_ParisFiller.json
state_tests/stZeroCallsRevert/ZeroValue_DELEGATECALL_OOGRevertFiller.json
state_tests/stZeroCallsRevert/ZeroValue_DELEGATECALL_ToEmpty_OOGRevert_ParisFiller.json
state_tests/stZeroCallsRevert/ZeroValue_DELEGATECALL_ToNonZeroBalance_OOGRevertFiller.json
state_tests/stZeroCallsRevert/ZeroValue_DELEGATECALL_ToOneStorageKey_OOGRevert_ParisFiller.json

@manually-enhanced: Do not overwrite. Twelve fillers parametrized by opcode
and recipient.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    StateTestFiller,
    Storage,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stZeroCallsRevert/ZeroValue_CALL_OOGRevertFiller.json",
        "state_tests/stZeroCallsRevert/ZeroValue_CALL_ToEmpty_OOGRevert_ParisFiller.json",  # noqa: E501
        "state_tests/stZeroCallsRevert/ZeroValue_CALL_ToNonZeroBalance_OOGRevertFiller.json",  # noqa: E501
        "state_tests/stZeroCallsRevert/ZeroValue_CALL_ToOneStorageKey_OOGRevert_ParisFiller.json",  # noqa: E501
        "state_tests/stZeroCallsRevert/ZeroValue_CALLCODE_OOGRevertFiller.json",  # noqa: E501
        "state_tests/stZeroCallsRevert/ZeroValue_CALLCODE_ToEmpty_OOGRevert_ParisFiller.json",  # noqa: E501
        "state_tests/stZeroCallsRevert/ZeroValue_CALLCODE_ToNonZeroBalance_OOGRevertFiller.json",  # noqa: E501
        "state_tests/stZeroCallsRevert/ZeroValue_CALLCODE_ToOneStorageKey_OOGRevert_ParisFiller.json",  # noqa: E501
        "state_tests/stZeroCallsRevert/ZeroValue_DELEGATECALL_OOGRevertFiller.json",  # noqa: E501
        "state_tests/stZeroCallsRevert/ZeroValue_DELEGATECALL_ToEmpty_OOGRevert_ParisFiller.json",  # noqa: E501
        "state_tests/stZeroCallsRevert/ZeroValue_DELEGATECALL_ToNonZeroBalance_OOGRevertFiller.json",  # noqa: E501
        "state_tests/stZeroCallsRevert/ZeroValue_DELEGATECALL_ToOneStorageKey_OOGRevert_ParisFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "recipient",
    [
        "nonexistent",
        "funded_eoa",
        "eoa_with_storage",
    ],
)
@pytest.mark.parametrize(
    "opcode",
    [
        pytest.param(Op.CALL, id="call"),
        pytest.param(Op.CALLCODE, id="callcode"),
        pytest.param(Op.DELEGATECALL, id="delegatecall"),
    ],
)
def test_zero_value_oog_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
    recipient: str,
) -> None:
    """Make a zero-value `opcode` call to `recipient`, then run out of gas."""
    sender = pre.fund_eoa()
    storage = Storage()

    if recipient == "nonexistent":
        callee = pre.nonexistent_account()
        expected = Account.NONEXISTENT
    elif recipient == "funded_eoa":
        callee = pre.fund_eoa()
        expected = Account(storage={}, balance_change=0)
    else:
        storage[0] = 1
        callee = pre.fund_eoa(storage=storage)
        expected = Account(storage=storage, balance_change=0)

    # Source: lll
    # { [[0]](GAS) [[1]] (CALL 60000 <eoa:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[2]]12 [[3]]12 [[4]]12 [[100]] (GAS) }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.GAS)
        + Op.SSTORE(key=0x1, value=opcode(gas=0xEA60, address=callee))
        + Op.SSTORE(key=0x2, value=0xC)
        + Op.SSTORE(key=0x3, value=0xC)
        + Op.SSTORE(key=0x4, value=0xC)
        + Op.SSTORE(key=0x64, value=Op.GAS)
        + Op.STOP,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        gas_limit=135000,
    )

    post = {
        sender: Account(nonce=1),
        callee: expected,
        target: Account(storage={0: 0, 1: 0, 100: 0}),
    }

    state_test(pre=pre, post=post, tx=tx)
