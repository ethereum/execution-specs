"""
Verify a CREATE2 issued from a contract-creation transaction's init
code: the transaction budget decides whether the CREATE2's child
completes its storage-writing init code or dies out of gas, while the
outer creation completes either way.

Ported from:
state_tests/stCreate2/CreateMessageRevertedOOGInInit2Filler.json

@manually-enhanced: Do not overwrite. Both budgets are derived from fork
composites (intrinsic + top-frame state gas + the composed init code);
the outer created account is asserted on both arms with a pre-CREATE2
canary, and the child account's storage on the success arm.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    StateTestFiller,
    Transaction,
    compute_create2_address,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

CANARY_SLOT = 0x2
CANARY = 0xFF
TX_VALUE = 100
CHILD_STORED = {0x0: 0xC, 0x1: 0xD}


@pytest.mark.ported_from(
    ["state_tests/stCreate2/CreateMessageRevertedOOGInInit2Filler.json"],
)
@pytest.mark.valid_from("Constantinople")
@pytest.mark.parametrize(
    "child_covered",
    [
        pytest.param(False, id="child_oog"),
        pytest.param(True, id="child_succeeds"),
    ],
)
def test_create_message_reverted_oog_in_init2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    child_covered: bool,
) -> None:
    """The budget decides how far an init-code CREATE2's child gets."""
    # The child's init code writes two fresh slots and deposits nothing.
    inner_initcode = Op.SSTORE(
        key=0x0,
        value=CHILD_STORED[0x0],
        key_warm=False,
        original_value=0,
        new_value=CHILD_STORED[0x0],
    ) + Op.SSTORE(
        key=0x1,
        value=CHILD_STORED[0x1],
        key_warm=False,
        original_value=0,
        new_value=CHILD_STORED[0x1],
    )
    inner_bytes = bytes(inner_initcode)
    assert len(inner_bytes) <= 0x20, "inner init code must fit one word"

    # The outer init code writes a completion canary before the CREATE2
    # (only a POP runs after it: on the starved arm the 1/64 retention
    # cannot afford an SSTORE), stages the child's init code in memory
    # and runs the CREATE2; it deposits no code.
    canary_store = Op.SSTORE(
        key=CANARY_SLOT,
        value=CANARY,
        key_warm=False,
        original_value=0,
        new_value=CANARY,
    )
    setup = Op.MSTORE(
        offset=0x0,
        value=int.from_bytes(inner_bytes, "big"),
        new_memory_size=0x20,
    )
    create2_code = Op.CREATE2(
        value=0x0,
        offset=0x20 - len(inner_bytes),
        size=len(inner_bytes),
        salt=0x0,
        new_memory_size=0x20,
        old_memory_size=0x20,
        init_code_size=len(inner_bytes),
    )
    outer_initcode = canary_store + setup + Op.POP(create2_code) + Op.STOP

    # Both budgets derive from the same overhead: everything the outer
    # frame pays before (and including) the CREATE2's own charges. The
    # child's grant is what remains after the 1/64 withhold.
    overhead = (
        fork.transaction_intrinsic_cost_calculator()(
            calldata=outer_initcode,
            contract_creation=True,
            sends_value=True,
        )
        + fork.transaction_top_frame_state_gas(contract_creation=True)
        + canary_store.gas_cost(fork)
        + setup.gas_cost(fork)
        + create2_code.gas_cost(fork)
    )
    child_needed = inner_initcode.gas_cost(fork)
    if child_covered:
        gas_limit = overhead + -(-child_needed * 64 // 63) + 3_000
    else:
        gas_limit = overhead + child_needed // 2

    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=None,
        data=outer_initcode,
        gas_limit=gas_limit,
        value=TX_VALUE,
    )

    outer_created = compute_create_address(address=sender, nonce=0)
    child = compute_create2_address(outer_created, 0, inner_initcode)
    post = {
        sender: Account(nonce=1),
        # The outer creation completes on both arms: the CREATE2 always
        # bumps its nonce, and a failed child costs it only the grant.
        outer_created: Account(
            nonce=2,
            code=b"",
            balance=TX_VALUE,
            storage={CANARY_SLOT: CANARY},
        ),
        child: Account(nonce=1, code=b"", balance=0, storage=CHILD_STORED)
        if child_covered
        else Account.NONEXISTENT,
    }

    state_test(pre=pre, post=post, tx=tx)
