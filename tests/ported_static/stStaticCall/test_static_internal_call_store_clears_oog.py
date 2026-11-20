"""
STATICCALL a contract that clears its storage.

Ported from:
state_tests/stStaticCall/static_InternalCallStoreClearsOOGFiller.json

@manually-enhanced: Do not overwrite. Callee is no longer address 0.
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

CLEARED_SLOTS = range(10)
RESULT_SLOT = 1
RESULT_SENTINEL = 0xFF


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_InternalCallStoreClearsOOGFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_static_internal_call_store_clears_oog(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Verify the callee's storage clears fail and are not applied."""
    callee_storage: dict = dict.fromkeys(CLEARED_SLOTS, 12)
    callee = pre.deploy_contract(
        code=sum((Op.SSTORE(slot, 0) for slot in CLEARED_SLOTS), Bytecode())
        + Op.STOP,
        storage=callee_storage,
    )
    caller = pre.deploy_contract(
        code=Op.SSTORE(RESULT_SLOT, Op.STATICCALL(address=callee)) + Op.STOP,
        storage={RESULT_SLOT: RESULT_SENTINEL},
    )

    tx = Transaction(sender=pre.fund_eoa(), to=caller)

    post = {
        callee: Account(storage=callee_storage),
        caller: Account(storage={RESULT_SLOT: 0}),
    }

    state_test(pre=pre, post=post, tx=tx)
