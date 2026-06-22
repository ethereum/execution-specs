"""Test CALL return data buffer behavior on pre-check failure."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Op,
    StateTestFiller,
    Transaction,
)

from .spec import ref_spec_211

REFERENCE_SPEC_GIT_PATH = ref_spec_211.git_path
REFERENCE_SPEC_VERSION = ref_spec_211.version


@pytest.mark.valid_from("Byzantium")
def test_call_clears_return_data_on_insufficient_balance(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    Test that a CALL clears the return-data buffer even when the call fails the
    insufficient-balance pre-check and the callee is never entered.

    A CALL whose value exceeds the caller's balance is a "light" failure: it
    pushes 0 and never executes the callee, but per EIP-211 it must still reset
    the return-data buffer. A client that skips the reset on this early-return
    path would leave stale return data from a preceding CALL observable via
    RETURNDATASIZE/RETURNDATACOPY.

    (The other CALL pre-check -- the 1024 call-stack depth limit -- is not
    exercised here: since EIP-150's 63/64 gas-forwarding rule, a call chain
    runs out of gas long before reaching depth 1024, so that branch is
    effectively unreachable.)

    Storage layout:
      slot 0 = RETURNDATASIZE after the funded CALL    (expected 32)
      slot 1 = RETURNDATASIZE after the failing CALL   (expected 0)
      slot 2 = the failing CALL result                 (expected 0, failure)
    """
    slot_rds_after_call = 0
    slot_rds_after_failed_call = 1
    slot_failed_call_result = 2

    # Callee returns 32 bytes, so the caller's return-data buffer is 32 bytes.
    callee = pre.deploy_contract(
        code=Op.MSTORE(0, 0x11223344) + Op.RETURN(0, 32),
    )

    # Caller has balance 1, so a CALL with value 2 fails the balance pre-check
    # before entering the callee.
    caller = pre.deploy_contract(
        balance=1,
        code=(
            Op.CALL(Op.GAS, callee, 0, 0, 0, 0, 32)
            + Op.SSTORE(slot_rds_after_call, Op.RETURNDATASIZE)
            + Op.SSTORE(
                slot_failed_call_result,
                Op.CALL(Op.GAS, callee, 2, 0, 0, 0, 0),
            )
            + Op.SSTORE(slot_rds_after_failed_call, Op.RETURNDATASIZE)
            + Op.STOP
        ),
        storage={
            slot_rds_after_call: 0xFF,
            slot_rds_after_failed_call: 0xFF,
            slot_failed_call_result: 0xFF,
        },
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller,
        gas_limit=1_000_000,
    )

    state_test(
        pre=pre,
        post={
            caller: Account(
                storage={
                    slot_rds_after_call: 32,
                    slot_rds_after_failed_call: 0,
                    slot_failed_call_result: 0,
                }
            )
        },
        tx=tx,
    )
