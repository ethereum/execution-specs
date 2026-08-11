"""
Verify a contract-creation transaction targeting an address that holds
only a balance: the prefund is not a collision, so creation proceeds and
the budget alone decides whether the init code completes.

Ported from:
state_tests/stCreateTest/TransactionCollisionToEmpty2Filler.json

@manually-enhanced: Do not overwrite. Budgets are derived from the fork
(intrinsic + init code cost, success arm exact), pinning that a prefunded
create target incurs no EIP-8037 top-frame new-account state gas.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

PREFUND = 10


@pytest.mark.ported_from(
    ["state_tests/stCreateTest/TransactionCollisionToEmpty2Filler.json"],
)
@pytest.mark.valid_from("Berlin")
@pytest.mark.parametrize("oog", [False, True], ids=["enough-gas", "oog"])
@pytest.mark.parametrize("tx_value", [0, 1], ids=["v0", "v1"])
def test_transaction_collision_to_empty2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    oog: bool,
    tx_value: int,
) -> None:
    """Prefunded create target is no collision; budget decides the rest."""
    # Init code: one cold zero->non-zero store, deploys nothing.
    initcode = Op.SSTORE(
        key=0x1,
        value=0x1,
        key_warm=False,
        original_value=0,
        new_value=1,
    )

    success_gas = fork.transaction_intrinsic_cost_calculator()(
        calldata=initcode,
        contract_creation=True,
        sends_value=tx_value > 0,
        return_cost_deducted_prior_execution=True,
    ) + initcode.gas_cost(fork)
    gas_limit = success_gas
    if oog:
        # Exactly one gas short, so the store is what cannot be paid for.
        gas_limit -= 1

    sender = pre.fund_eoa()
    created = compute_create_address(address=sender, nonce=0)
    pre.fund_address(created, PREFUND)

    tx = Transaction(
        sender=sender,
        to=None,
        data=initcode,
        gas_limit=gas_limit,
        value=tx_value,
    )

    if oog:
        # Creation rolled back: prefund kept, no value, nonce untouched.
        created_account = Account(
            storage={}, code=b"", nonce=0, balance=PREFUND
        )
    else:
        created_account = Account(
            storage={1: 1}, code=b"", nonce=1, balance=PREFUND + tx_value
        )

    post = {
        sender: Account(nonce=1),
        created: created_account,
    }

    state_test(pre=pre, post=post, tx=tx)
