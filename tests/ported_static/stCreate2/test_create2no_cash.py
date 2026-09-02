"""
Verify CREATE2's endowment balance preflight: a creator one wei short of
the endowment fails without creating (and without a nonce bump), a
one-wei top-up sent with the call makes the same CREATE2 succeed, and in
a static context the CREATE2 faults the whole frame instead.

Ported from:
state_tests/stCreate2/create2noCashFiller.json

@manually-enhanced: Do not overwrite. The creation-transaction wrapper
and tuned gas budgets are replaced by a deployed entry contract that
records the call result, and the created account and the creator's
nonce (no bump on the balance preflight) are asserted explicitly.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    StateTestFiller,
    Transaction,
    compute_create2_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

CALL_RESULT_SLOT = 0x0
CREATE2_ENDOWMENT = 0x65


@pytest.mark.ported_from(
    ["state_tests/stCreate2/create2noCashFiller.json"],
)
@pytest.mark.valid_from("Constantinople")
@pytest.mark.parametrize(
    "opcode, top_up",
    [
        pytest.param(Op.CALL, 0, id="call_insufficient_balance"),
        pytest.param(Op.CALL, 1, id="call_topped_up_balance"),
        pytest.param(Op.STATICCALL, 0, id="staticcall_write_protection"),
    ],
)
def test_create2no_cash(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
    top_up: int,
) -> None:
    """A CREATE2 endowment beyond the creator's balance cannot create."""
    # The creator holds one wei less than the endowment it attempts to
    # transfer. Only the topped-up arm can afford it.
    creator = pre.deploy_contract(
        code=Op.POP(
            Op.CREATE2(value=CREATE2_ENDOWMENT, offset=0x0, size=0x0, salt=0x0)
        )
        + Op.STOP,
        balance=CREATE2_ENDOWMENT - 1,
    )

    # The entry contract forwards the transaction's value (the optional
    # top-up) and records the call result, shifted so that a failed call
    # (1), a successful call (2) and no call at all (0) all differ.
    if opcode == Op.CALL:
        call_code = Op.CALL(address=creator, value=top_up)
    else:
        call_code = Op.STATICCALL(address=creator)
    entry = pre.deploy_contract(
        code=Op.SSTORE(key=CALL_RESULT_SLOT, value=Op.ADD(0x1, call_code))
        + Op.STOP,
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=entry,
        value=top_up,
        state_gas_reservoir=0,
    )

    created = compute_create2_address(creator, 0, b"")
    create_succeeds = opcode == Op.CALL and top_up > 0
    if create_succeeds:
        # The whole (topped-up) balance moved into the created account,
        # and the creator's nonce was consumed by the creation.
        creator_account = Account(nonce=2, balance=0)
        created_account: Account | None = Account(
            nonce=1, code=b"", balance=CREATE2_ENDOWMENT
        )
    else:
        # The balance preflight (or the static fault) aborts before any
        # account is touched: no creation and no nonce bump.
        creator_account = Account(nonce=1, balance=CREATE2_ENDOWMENT - 1)
        created_account = Account.NONEXISTENT

    # A static frame faults on CREATE2, so only that arm's call fails.
    call_result = 0 if opcode == Op.STATICCALL else 1

    post = {
        entry: Account(
            storage={CALL_RESULT_SLOT: 0x1 + call_result}, balance=0
        ),
        creator: creator_account,
        created: created_account,
    }

    state_test(pre=pre, post=post, tx=tx)
