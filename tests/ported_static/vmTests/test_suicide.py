"""
Test SELFDESTRUCT beneficiaries from a called contract.

The original tests were written by Ori Pomerantz.

Ported from:
state_tests/VMTests/vmTests/suicideFiller.yml

@manually-enhanced: Do not overwrite. A `caller` calls a `victim` that
SELFDESTRUCTs to the `caller`, to a nonexistent account, or to itself.
The expected state follows the fork: before EIP-6780 the victim is
deleted at the end of the transaction, burning its balance when it names
itself, and from EIP-6780 on it keeps its code and only moves its
balance. The receipt's gas used comes from the framework gas calculation,
less the SELFDESTRUCT refund the fork grants.
"""

from enum import StrEnum

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

pytestmark = [
    pytest.mark.ported_from(
        ["state_tests/VMTests/vmTests/suicideFiller.yml"],
    ),
    pytest.mark.valid_from("Frontier"),
]

VICTIM_BALANCE = 0xFF000000000000
# Explicit, so the call does not ask for more gas than is left before
# EIP-150 lets it forward all but 1/64th.
VICTIM_CALL_GAS = 0x10000


class Beneficiary(StrEnum):
    """The account the victim's SELFDESTRUCT sends its balance to."""

    CALLER = "caller"
    RANDOM = "random"
    MYSELF = "myself"


@pytest.mark.parametrize("beneficiary", list(Beneficiary), ids=str)
def test_suicide(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    beneficiary: Beneficiary,
) -> None:
    """Send the balance of a called contract to its SELFDESTRUCT target."""
    absent = pre.nonexistent_account()
    target: Address | Bytecode
    match beneficiary:
        case Beneficiary.CALLER:
            target = Op.CALLER
        case Beneficiary.RANDOM:
            target = absent
        case Beneficiary.MYSELF:
            target = Op.ADDRESS
    # Before EIP-6780 the victim is deleted, which also earns the
    # refund on forks that still grant one.
    deleted = fork.selfdestruct_deletes_existing_accounts()
    victim_code = Op.SELFDESTRUCT(
        address=target,
        address_warm=beneficiary != Beneficiary.RANDOM,
        account_new=beneficiary == Beneficiary.RANDOM,
        self_destructed_account=deleted,
    )
    victim = pre.deploy_contract(code=victim_code, balance=VICTIM_BALANCE)
    caller_code = (
        Op.SSTORE(0, Op.CALL(gas=VICTIM_CALL_GAS, address=victim)) + Op.STOP
    )
    caller = pre.deploy_contract(code=caller_code)

    executed = (
        fork.transaction_intrinsic_cost_calculator()()
        + caller_code.gas_cost(fork)
        + victim_code.gas_cost(fork)
    )
    refund = min(
        victim_code.refund(fork), executed // fork.max_refund_quotient()
    )
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller,
        protected=fork.supports_protected_txs(),
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=executed - refund
        ),
    )

    victim_after: Account | None = Account(balance=0, code=victim_code)
    if deleted:
        victim_after = Account.NONEXISTENT
    post: dict = {}
    match beneficiary:
        case Beneficiary.CALLER:
            post[caller] = Account(
                storage={0: 1}, balance_change=VICTIM_BALANCE
            )
            post[victim] = victim_after
        case Beneficiary.RANDOM:
            post[caller] = Account(storage={0: 1}, balance_change=0)
            post[absent] = Account(balance_change=VICTIM_BALANCE)
            post[victim] = victim_after
        case Beneficiary.MYSELF:
            post[caller] = Account(storage={0: 1}, balance_change=0)
            post[victim] = Account(balance_change=0, code=victim_code)
            if deleted:
                # Deleting the account burns the balance it sent itself.
                assert fork.selfdestruct_burns_balance()
                post[victim] = Account.NONEXISTENT
    state_test(pre=pre, post=post, tx=tx)
