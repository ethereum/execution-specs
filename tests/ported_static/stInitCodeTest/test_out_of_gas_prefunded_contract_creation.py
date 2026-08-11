"""
Verify a contract-creation transaction targeting a prefunded address, whose
init code CREATEs a value-bearing child: the budget decides whether the
outer creation fails (prefund untouched), the child fails (value stays),
or the child succeeds (one wei moves into it).

Ported from:
state_tests/stInitCodeTest/OutOfGasPrefundedContractCreationFiller.json

@manually-enhanced: Do not overwrite. The three budgets are fork-derived
and one gas apart at each boundary: the inner CREATE's own price, and the
63/64 grant the child's init code needs. Asserting the child account is
what tells the ported "balance 1" outcomes -- outer failure and child
success -- apart.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    Hash,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

PREFUND = 1
TX_VALUE = 1
CHILD_VALUE = 1
CHILD_STORED = 0x112233


def minimum_frame_gas(needed: int) -> int:
    """
    Return the smallest frame budget whose 63/64 grant covers `needed`.

    The EVM withholds `available // 64`, which is not the same as granting
    `available * 63 // 64`: the two differ by one whenever `available` is
    not a multiple of 64, so the inverse is found by adjusting an estimate
    rather than computed directly.
    """
    available = -(-needed * 64 // 63)
    while available - available // 64 < needed:
        available += 1
    while (available - 1) - (available - 1) // 64 >= needed:
        available -= 1
    return available


@pytest.mark.ported_from(
    [
        "state_tests/stInitCodeTest/OutOfGasPrefundedContractCreationFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Berlin")
@pytest.mark.parametrize(
    "outcome", ["child_succeeds", "outer_oog", "child_oog"]
)
def test_out_of_gas_prefunded_contract_creation(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    outcome: str,
) -> None:
    """Budget decides how deep a prefunded creation's child CREATE gets."""
    # Child init code: one cold store, deposits nothing.
    child_code = Op.SSTORE(
        key=0x0,
        value=CHILD_STORED,
        key_warm=False,
        original_value=0,
        new_value=CHILD_STORED,
    )

    # Outer init code: stage the child init code -- it fits in one word --
    # then CREATE a value-bearing child from it; deposits nothing.
    inner_create = Op.CREATE(
        value=CHILD_VALUE,
        offset=0x0,
        size=len(child_code),
        # Memory is already a word wide: `stage_child` paid that expansion.
        new_memory_size=0x20,
        old_memory_size=0x20,
        init_code_size=len(child_code),
    )
    stage_child = Op.MSTORE(
        offset=0x0,
        value=Hash(child_code, right_padding=True),
        new_memory_size=0x20,
    )
    initcode = stage_child + Op.POP(inner_create) + Op.STOP

    # No top-frame new-account state gas: the prefunded target is not
    # EMPTY_ACCOUNT in the pre-state, which is the EIP-8037 behaviour these
    # exact budgets pin. The inner CREATE's composite cost is its peak
    # charge -- refunded if the child fails, but payable when charged.
    overhead = (
        fork.transaction_intrinsic_cost_calculator()(
            calldata=initcode,
            contract_creation=True,
            sends_value=TX_VALUE > 0,
            return_cost_deducted_prior_execution=True,
        )
        + stage_child.gas_cost(fork)
        + inner_create.gas_cost(fork)
    )
    # Exactly enough for the child, so one gas either side of it decides
    # whether the 63/64 grant covers the child's init code.
    child_frame_gas = minimum_frame_gas(child_code.gas_cost(fork))
    if outcome == "outer_oog":
        # One gas short of paying for the inner CREATE itself.
        gas_limit = overhead - 1
    elif outcome == "child_oog":
        # Outer completes; the child's grant undercuts its cost by one.
        gas_limit = overhead + child_frame_gas - 1
    else:
        # Child completes too and keeps the transferred wei.
        gas_limit = overhead + child_frame_gas

    sender = pre.fund_eoa()
    created = compute_create_address(address=sender, nonce=0)
    pre.fund_address(created, PREFUND)

    tx = Transaction(
        sender=sender,
        to=None,
        data=initcode,
        gas_limit=gas_limit,
        value=TX_VALUE,
    )

    child = compute_create_address(address=created, nonce=1)
    if outcome == "outer_oog":
        # Creation rolled back: only the prefund remains, nonce untouched.
        created_account = Account(nonce=0, balance=PREFUND)
        child_account: Account | None = Account.NONEXISTENT
    elif outcome == "child_oog":
        # The inner CREATE increments the creator's nonce even when the
        # child fails.
        created_account = Account(
            nonce=2, code=b"", balance=PREFUND + TX_VALUE
        )
        child_account = Account.NONEXISTENT
    else:
        created_account = Account(
            nonce=2, code=b"", balance=PREFUND + TX_VALUE - CHILD_VALUE
        )
        child_account = Account(
            nonce=1,
            balance=CHILD_VALUE,
            storage={0: CHILD_STORED},
        )

    post = {
        sender: Account(nonce=1),
        created: created_account,
        child: child_account,
    }

    state_test(pre=pre, post=post, tx=tx)
