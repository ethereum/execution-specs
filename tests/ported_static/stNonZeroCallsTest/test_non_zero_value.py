"""
Gas cost of CALL / CALLCODE / DELEGATECALL carrying non-zero value to targets
in various pre-states, measured with CodeGasMeasure.

Ported from:
state_tests/stNonZeroCallsTest/NonZeroValue_CALLFiller.json
state_tests/stNonZeroCallsTest/NonZeroValue_CALL_ToEmpty_ParisFiller.json
state_tests/stNonZeroCallsTest/NonZeroValue_CALL_ToOneStorageKey_ParisFiller.json
state_tests/stNonZeroCallsTest/NonZeroValue_CALLCODEFiller.json
state_tests/stNonZeroCallsTest/NonZeroValue_CALLCODE_ToEmpty_ParisFiller.json
state_tests/stNonZeroCallsTest/NonZeroValue_CALLCODE_ToOneStorageKey_ParisFiller.json
state_tests/stNonZeroCallsTest/NonZeroValue_DELEGATECALLFiller.json
state_tests/stNonZeroCallsTest/NonZeroValue_DELEGATECALL_ToEmpty_ParisFiller.json
state_tests/stNonZeroCallsTest/NonZeroValue_DELEGATECALL_ToOneStorageKey_ParisFiller.json
state_tests/stNonZeroCallsTest/NonZeroValue_DELEGATECALL_ToNonNonZeroBalanceFiller.json

@manually-enhanced: Do not overwrite. Call gas via CodeGasMeasure.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    CodeGasMeasure,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

CONTRACT_BALANCE = 100
CALL_VALUE = 1
EXISTING_BALANCE = 10
NONZERO_BALANCE = 100


@pytest.mark.ported_from(
    [
        "state_tests/stNonZeroCallsTest/NonZeroValue_CALLFiller.json",
        "state_tests/stNonZeroCallsTest/NonZeroValue_CALL_ToEmpty_ParisFiller.json",  # noqa: E501
        "state_tests/stNonZeroCallsTest/NonZeroValue_CALL_ToOneStorageKey_ParisFiller.json",  # noqa: E501
        "state_tests/stNonZeroCallsTest/NonZeroValue_CALLCODEFiller.json",
        "state_tests/stNonZeroCallsTest/NonZeroValue_CALLCODE_ToEmpty_ParisFiller.json",  # noqa: E501
        "state_tests/stNonZeroCallsTest/NonZeroValue_CALLCODE_ToOneStorageKey_ParisFiller.json",  # noqa: E501
        "state_tests/stNonZeroCallsTest/NonZeroValue_DELEGATECALLFiller.json",
        "state_tests/stNonZeroCallsTest/NonZeroValue_DELEGATECALL_ToEmpty_ParisFiller.json",  # noqa: E501
        "state_tests/stNonZeroCallsTest/NonZeroValue_DELEGATECALL_ToOneStorageKey_ParisFiller.json",  # noqa: E501
        "state_tests/stNonZeroCallsTest/NonZeroValue_DELEGATECALL_ToNonNonZeroBalanceFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Berlin")
@pytest.mark.parametrize(
    "opcode, target_kind",
    [
        pytest.param(Op.CALL, "nonexistent", id="call"),
        pytest.param(Op.CALL, "empty", id="call_to_empty"),
        pytest.param(Op.CALL, "one_storage_key", id="call_to_one_storage_key"),
        pytest.param(Op.CALLCODE, "nonexistent", id="callcode"),
        pytest.param(Op.CALLCODE, "empty", id="callcode_to_empty"),
        pytest.param(
            Op.CALLCODE, "one_storage_key", id="callcode_to_one_storage_key"
        ),
        pytest.param(Op.DELEGATECALL, "nonexistent", id="delegatecall"),
        pytest.param(Op.DELEGATECALL, "empty", id="delegatecall_to_empty"),
        pytest.param(
            Op.DELEGATECALL,
            "one_storage_key",
            id="delegatecall_to_one_storage_key",
        ),
        pytest.param(
            Op.DELEGATECALL,
            "nonzero_balance",
            id="delegatecall_to_nonzero_balance",
        ),
    ],
)
def test_non_zero_value(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    target_kind: str,
) -> None:
    """Measure call-family gas to a cold target of each pre-state."""
    transfers_value = opcode != Op.DELEGATECALL

    # Set up the target account in the requested pre-state.
    if target_kind == "nonexistent":
        call_target = pre.nonexistent_account()
        target_balance = 0
        target_storage: dict = {}
    elif target_kind == "one_storage_key":
        target_balance = EXISTING_BALANCE
        target_storage = {0x0: 0x1}
        call_target = pre.deploy_contract(
            code=b"", balance=target_balance, storage=target_storage
        )
    else:
        target_balance = (
            NONZERO_BALANCE
            if target_kind == "nonzero_balance"
            else EXISTING_BALANCE
        )
        target_storage = {}
        call_target = pre.fund_eoa(amount=target_balance)

    # Only a plain CALL forwards value to the target (and can create it);
    # CALLCODE keeps value in the caller's context, DELEGATECALL has no value.
    account_new = opcode == Op.CALL and target_kind == "nonexistent"
    received = CALL_VALUE if opcode == Op.CALL else 0

    if opcode == Op.DELEGATECALL:
        call_code = Op.DELEGATECALL(
            gas=0xEA60,
            address=call_target,
            address_warm=False,
        )
    else:
        call_code = opcode(
            gas=0xEA60,
            address=call_target,
            value=CALL_VALUE,
            address_warm=False,
            value_transfer=True,
            account_new=account_new,
        )

    contract = pre.deploy_contract(
        code=CodeGasMeasure(
            code=call_code,
            extra_stack_items=1,
            sstore_key=0x64,
        ),
        balance=CONTRACT_BALANCE,
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        state_gas_reservoir=0,
    )

    # A value-bearing call whose callee consumes nothing returns the stipend.
    measured = call_code.gas_cost(fork)
    if transfers_value:
        measured -= fork.gas_costs().CALL_STIPEND

    if target_kind == "nonexistent":
        target_account = (
            Account(balance=CALL_VALUE) if account_new else Account.NONEXISTENT
        )
    else:
        target_account = Account(
            balance=target_balance + received, storage=target_storage
        )

    post = {
        contract: Account(
            storage={0x64: measured},
            balance=CONTRACT_BALANCE - received,
        ),
        call_target: target_account,
    }

    state_test(pre=pre, post=post, tx=tx)
