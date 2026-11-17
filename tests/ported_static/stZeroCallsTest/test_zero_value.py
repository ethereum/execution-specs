"""
Measure the gas of a zero-value CALL / CALLCODE / DELEGATECALL to different
kinds of recipient, using CodeGasMeasure.

Ported from:
state_tests/stZeroCallsTest/ZeroValue_CALLFiller.json
state_tests/stZeroCallsTest/ZeroValue_CALL_ToEmpty_ParisFiller.json
state_tests/stZeroCallsTest/ZeroValue_CALL_ToNonZeroBalanceFiller.json
state_tests/stZeroCallsTest/ZeroValue_CALL_ToOneStorageKey_ParisFiller.json
state_tests/stZeroCallsTest/ZeroValue_CALLCODEFiller.json
state_tests/stZeroCallsTest/ZeroValue_CALLCODE_ToEmpty_ParisFiller.json
state_tests/stZeroCallsTest/ZeroValue_CALLCODE_ToNonZeroBalanceFiller.json
state_tests/stZeroCallsTest/ZeroValue_CALLCODE_ToOneStorageKey_ParisFiller.json
state_tests/stZeroCallsTest/ZeroValue_DELEGATECALLFiller.json
state_tests/stZeroCallsTest/ZeroValue_DELEGATECALL_ToEmpty_ParisFiller.json
state_tests/stZeroCallsTest/ZeroValue_DELEGATECALL_ToNonZeroBalanceFiller.json
state_tests/stZeroCallsTest/ZeroValue_DELEGATECALL_ToOneStorageKey_ParisFiller.json

@manually-enhanced: Do not overwrite. Twelve fillers parametrized by opcode
and recipient. The fillers stored `GAS` before the call, which only pinned
the intrinsic gas; the call's gas is now measured with CodeGasMeasure, and
the call success flag is stored inside the measured window (a wrongly
failed call is gas-identical to a successful one into an empty callee).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    CodeGasMeasure,
    Fork,
    StateTestFiller,
    Storage,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

FORWARDED_GAS = 0xEA60
GAS_SLOT = 0x64
SUCCESS_SLOT = 0x1


@pytest.mark.ported_from(
    [
        "state_tests/stZeroCallsTest/ZeroValue_CALLFiller.json",
        "state_tests/stZeroCallsTest/ZeroValue_CALL_ToEmpty_ParisFiller.json",
        "state_tests/stZeroCallsTest/ZeroValue_CALL_ToNonZeroBalanceFiller.json",  # noqa: E501
        "state_tests/stZeroCallsTest/ZeroValue_CALL_ToOneStorageKey_ParisFiller.json",  # noqa: E501
        "state_tests/stZeroCallsTest/ZeroValue_CALLCODEFiller.json",
        "state_tests/stZeroCallsTest/ZeroValue_CALLCODE_ToEmpty_ParisFiller.json",  # noqa: E501
        "state_tests/stZeroCallsTest/ZeroValue_CALLCODE_ToNonZeroBalanceFiller.json",  # noqa: E501
        "state_tests/stZeroCallsTest/ZeroValue_CALLCODE_ToOneStorageKey_ParisFiller.json",  # noqa: E501
        "state_tests/stZeroCallsTest/ZeroValue_DELEGATECALLFiller.json",
        "state_tests/stZeroCallsTest/ZeroValue_DELEGATECALL_ToEmpty_ParisFiller.json",  # noqa: E501
        "state_tests/stZeroCallsTest/ZeroValue_DELEGATECALL_ToNonZeroBalanceFiller.json",  # noqa: E501
        "state_tests/stZeroCallsTest/ZeroValue_DELEGATECALL_ToOneStorageKey_ParisFiller.json",  # noqa: E501
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
def test_zero_value(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    recipient: str,
) -> None:
    """Make a zero-value `opcode` call to `recipient`."""
    sender = pre.fund_eoa()
    storage = Storage()

    if recipient == "nonexistent":
        callee = pre.nonexistent_account()
        expected = Account.NONEXISTENT
    elif recipient == "funded_eoa":
        callee = pre.fund_eoa()
        expected = Account(balance_change=0)
    else:
        storage[0] = 1
        callee = pre.fund_eoa(storage=storage)
        expected = Account(storage=storage, balance_change=0)

    # Source: lll
    # { [[0]](GAS) [[1]] (CALL 60000 0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b 0 0 0 0 0) [[100]] 1 }  # noqa: E501
    store_code = Op.SSTORE(
        SUCCESS_SLOT,
        opcode(gas=FORWARDED_GAS, address=callee),
        key_warm=False,
        original_value=0,
        new_value=1,
    )
    target = pre.deploy_contract(
        code=CodeGasMeasure(code=store_code, sstore_key=GAS_SLOT),
    )

    tx = Transaction(
        sender=sender,
        to=target,
        state_gas_reservoir=0,
    )

    post = {
        callee: expected,
        target: Account(
            storage={
                GAS_SLOT: store_code.gas_cost(fork),
                SUCCESS_SLOT: 1,
            }
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
