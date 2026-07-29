"""
Verify a contract-creation transaction targeting a prefunded address, whose
init code CREATEs a value-bearing child: the budget decides whether the
outer creation fails (prefund untouched), the child fails (value stays),
or the child succeeds (one wei moves into it).

Ported from:
state_tests/stInitCodeTest/OutOfGasPrefundedContractCreationFiller.json

@manually-enhanced: Do not overwrite. All three budgets are derived from
the fork (intrinsic + top-frame state gas + the composed init/child code
costs), and the child account is asserted, disambiguating the ported
"balance 1" outcomes (outer-failure vs child-success) that were previously
indistinguishable.
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

PREFUND = 1
TX_VALUE = 1
CHILD_VALUE = 1
CHILD_STORED = 0x112233


@pytest.mark.ported_from(
    [
        "state_tests/stInitCodeTest/OutOfGasPrefundedContractCreationFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Berlin")
@pytest.mark.parametrize(
    "outcome",
    [
        pytest.param("child_succeeds", id="g0"),
        pytest.param("outer_oog", id="g1"),
        pytest.param("child_oog", id="g2"),
    ],
)
def test_out_of_gas_prefunded_contract_creation(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    outcome: str,
) -> None:
    """Budget decides how deep a prefunded creation's child CREATE gets."""
    # Child init code: one cold store, deposits nothing.
    child_code = (
        Op.SSTORE(
            key=0x0,
            value=CHILD_STORED,
            key_warm=False,
            original_value=0,
            new_value=CHILD_STORED,
        )
        + Op.STOP * 2
    )
    child_bytes = bytes(child_code)

    # Outer init code: copy the child init code from its own tail, then
    # CREATE a value-bearing child from it; deposits nothing. The copy
    # window and memory usage stay within one word.
    inner_create = Op.CREATE(
        value=CHILD_VALUE,
        offset=0x0,
        size=len(child_bytes),
        new_memory_size=0x20,
        old_memory_size=0x20,
        init_code_size=len(child_bytes),
    )
    prefix = Op.CODECOPY(
        dest_offset=0x0,
        offset=0x1A,  # placeholder; recomputed below
        size=len(child_bytes),
        data_size=len(child_bytes),
        new_memory_size=0x20,
    )
    body = prefix + Op.POP(inner_create) + Op.STOP
    # The child code sits immediately after the executable body.
    initcode_prefix_len = len(bytes(body))
    prefix = Op.CODECOPY(
        dest_offset=0x0,
        offset=initcode_prefix_len,
        size=len(child_bytes),
        data_size=len(child_bytes),
        new_memory_size=0x20,
    )
    body = prefix + Op.POP(inner_create) + Op.STOP
    assert len(bytes(body)) == initcode_prefix_len, "stable code layout"
    initcode = body + child_code

    # Fork-derived budgets. The prefunded target is not EMPTY_ACCOUNT in
    # the pre-state, so EIP-8037 charges no top-frame new-account state
    # gas for this creation — an Amsterdam behavior this test pins. The
    # inner CREATE's composite cost covers its peak charge (its
    # new-account state gas is refunded if the child fails, but must be
    # affordable when charged).
    overhead = (
        fork.transaction_intrinsic_cost_calculator()(
            calldata=initcode,
            contract_creation=True,
        )
        + prefix.gas_cost(fork)
        + inner_create.gas_cost(fork)
    )
    child_needed = child_code.gas_cost(fork)
    if outcome == "outer_oog":
        # Dies charging the inner CREATE.
        gas_limit = overhead - inner_create.gas_cost(fork) // 2
    elif outcome == "child_oog":
        # Outer completes; the child's 63/64 grant undercuts its cost.
        gas_limit = overhead + child_needed // 2
    else:
        # Child completes too and keeps the transferred wei.
        gas_limit = overhead + -(-child_needed * 64 // 63) + 2_000

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
        child_account: Account | type = Account.NONEXISTENT
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
