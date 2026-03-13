"""
Tests for SELFDESTRUCT balance transfer revert behavior (EIP-6780).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-6780.md"
REFERENCE_SPEC_VERSION = "1b6a0e94cc47e859b9866e570391cf37dc55059a"


@pytest.mark.valid_from("Cancun")
def test_selfdestruct_balance_transfer_reverted(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
) -> None:
    """
    Test that SELFDESTRUCT balance transfer is reverted on sub-call revert.

    Post-Cancun, SELFDESTRUCT does not destroy the contract but still
    transfers balance. When the sub-call containing SELFDESTRUCT reverts,
    the balance transfer must also be reverted.
    """
    storage = Storage()

    victim_balance = 1

    beneficiary_balance = 1
    beneficiary = pre.fund_eoa(amount=beneficiary_balance)

    victim = pre.deploy_contract(
        code=Op.SELFDESTRUCT(beneficiary),
        balance=victim_balance,
    )

    # Controller calls victim (triggers SELFDESTRUCT) then reverts.
    controller = pre.deploy_contract(
        Op.POP(Op.CALL(gas=100_000, address=victim))
        + Op.REVERT(offset=0, size=0)
    )

    # Outer calls controller, then checks beneficiary balance.
    outer = pre.deploy_contract(
        Op.POP(Op.CALL(gas=200_000, address=controller))
        + Op.SSTORE(
            storage.store_next(beneficiary_balance, "beneficiary_balance"),
            Op.BALANCE(beneficiary),
        )
        + Op.SSTORE(
            storage.store_next(victim_balance, "victim_balance"),
            Op.BALANCE(victim),
        )
        + Op.STOP
    )

    sender = pre.fund_eoa()

    state_test(
        env=env,
        pre=pre,
        post={
            outer: Account(storage=storage),
            # Beneficiary keeps only its initial balance (transfer reverted).
            beneficiary: Account(balance=beneficiary_balance),
            # Victim still has its balance.
            victim: Account(balance=victim_balance),
        },
        tx=Transaction(
            sender=sender,
            to=outer,
            gas_limit=1_000_000,
        ),
    )
