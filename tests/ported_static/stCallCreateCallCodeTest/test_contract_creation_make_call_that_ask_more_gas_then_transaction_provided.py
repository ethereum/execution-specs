"""
Verify a CALL made inside a contract-creation transaction's init code that
asks for more gas than the transaction provided: the EIP-150 clamp decides
what the callee receives, and the transaction budget decides whether that
grant covers the callee's work.

Ported from:
state_tests/stCallCreateCallCodeTest/contractCreationMakeCallThatAskMoreGasThenTransactionProvidedFiller.json

@manually-enhanced: Do not overwrite. The ask is explicitly oversized (the
ported 50000 was schedule-sized); both transaction budgets are derived from
the fork so the clamped grant lands above/below the callee's cost on every
fork; the init code writes a canary before the call (nothing after it needs
more than a POP — the 1/64 retention cannot afford an SSTORE, whose
EIP-2200 stipend rule would kill the creation), so a failed call and a
failed creation stay distinguishable.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

CANARY_SLOT = 0x2
CANARY = 0xFF

# Far larger than any gas the init frame can hold: the clamp always
# applies, which is the scenario the ported filler names.
OVERSIZED_GAS_ASK = 2**61


@pytest.mark.ported_from(
    [
        "state_tests/stCallCreateCallCodeTest/contractCreationMakeCallThatAskMoreGasThenTransactionProvidedFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Berlin")
@pytest.mark.parametrize(
    "call_covered",
    [
        pytest.param(True, id="enough_gas"),
        pytest.param(False, id="not_enough_gas"),
    ],
)
def test_contract_creation_make_call_that_ask_more_gas_then_transaction_provided(  # noqa: E501
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    call_covered: bool,
) -> None:
    """An init-code CALL asking above the tx budget gets the 63/64 clamp."""
    # Success indicator: writes one cold fresh slot when called.
    writer_store = Op.SSTORE(
        key=0x1,
        value=0x1,
        key_warm=False,
        original_value=0,
        new_value=1,
    )
    writer = pre.deploy_contract(code=writer_store + Op.STOP)

    # The init code writes a completion canary before the call (a failed
    # creation persists nothing, so the canary distinguishes it from a
    # failed call), makes the oversized ask, and deposits no code. Only a
    # POP runs after the call: the 1/64 retention on the starved arm is
    # far below the EIP-2200 stipend an SSTORE would require.
    initcode = (
        Op.SSTORE(
            key=CANARY_SLOT,
            value=CANARY,
            key_warm=False,
            original_value=0,
            new_value=CANARY,
        )
        + Op.CALL(
            gas=OVERSIZED_GAS_ASK,
            address=writer,
            address_warm=False,
            value_transfer=False,
            account_new=False,
        )
        + Op.STOP
    )

    # Derive the two budgets around the callee's fork-priced cost: the
    # clamped grant (63/64 of the base left after the charges made before
    # the forward point) lands above it on one arm and below it on the
    # other. The post-call flag write runs on the 1/64 retention.
    overhead = (
        fork.transaction_intrinsic_cost_calculator()(
            calldata=initcode,
            contract_creation=True,
            return_cost_deducted_prior_execution=True,
        )
        # EIP-8037 charges the created account's state gas to the
        # creation transaction's top frame (zero before Amsterdam).
        + fork.transaction_top_frame_state_gas(contract_creation=True)
        + initcode.gas_cost(fork)
    )
    callee_needed = writer_store.gas_cost(fork)
    # The grant, base - base // 64, is a step function that repeats at
    # every multiple of 64, so one gas less does not always forward less:
    # step until the grant really crosses the callee's cost.
    base = callee_needed * 64 // 63
    while base - base // 64 < callee_needed:
        base += 1
    if not call_covered:
        while base - base // 64 >= callee_needed:
            base -= 1
    assert base < OVERSIZED_GAS_ASK, "the 63/64 clamp must apply"
    gas_limit = overhead + base
    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=None,
        data=initcode,
        gas_limit=gas_limit,
    )

    created = tx.created_contract
    post = {
        created: Account(
            nonce=1,
            code=b"",
            storage={CANARY_SLOT: CANARY},
        ),
        writer: Account(storage={1: 1 if call_covered else 0}),
    }

    state_test(pre=pre, post=post, tx=tx)
