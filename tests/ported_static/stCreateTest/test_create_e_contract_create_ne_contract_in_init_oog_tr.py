"""
Verify a contract-creation transaction whose init code first calls an
existing contract and then CREATEs a child, at the exact boundary of the
nested CREATE's EIP-150 grant: the call and the creating frame complete
either way, and one gas decides only whether the child materializes (at
the creator's nonce-1 address, not nonce 0).

Ported from:
state_tests/stCreateTest/CREATE_EContractCreateNEContractInInitOOG_TrFiller.json

@manually-enhanced: Do not overwrite. Budgets are derived from the fork
(intrinsic + EIP-8037 top-frame and nested-create state gas + composed
code costs, the child's deposit riding on its RETURN metadata), and the
frame's gas is solved for the smallest 63/64 grant that covers the child
rather than scaled by a guessed factor. The callee call forwards all gas
instead of a ported fixed budget, and the nested child is now asserted at
its real nonce-1 address (the port only checked the vacuous nonce-0
address).
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

CALLEE_STORED = 0xC


@pytest.mark.ported_from(
    [
        "state_tests/stCreateTest/CREATE_EContractCreateNEContractInInitOOG_TrFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Berlin")
@pytest.mark.parametrize("oog", [False, True], ids=["enough-gas", "oog"])
def test_create_e_contract_create_ne_contract_in_init_oog_tr(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    oog: bool,
) -> None:
    """Budget decides how far a creation's call-then-CREATE init gets."""
    sender = pre.fund_eoa()

    # Callee: one cold zero->non-zero store observed in the post.
    callee_code = (
        Op.SSTORE(
            key=0x1,
            value=CALLEE_STORED,
            key_warm=False,
            original_value=0,
            new_value=CALLEE_STORED,
        )
        + Op.STOP
    )
    callee = pre.deploy_contract(code=callee_code)

    # Child init code: return a small runtime code from memory.
    child_runtime = Op.SSTORE(key=0x0, value=CALLEE_STORED)
    child_initcode = Op.MSTORE(
        offset=0x0,
        value=int.from_bytes(child_runtime, "big"),
        new_memory_size=0x20,
    ) + Op.RETURN(
        offset=32 - len(child_runtime),
        size=len(child_runtime),
        code_deposit_size=len(child_runtime),
    )

    # Transaction init code: call the callee (forwarding all gas), then
    # CREATE the child from memory; deploys nothing itself.
    call_code = Op.POP(Op.CALL(address=callee))
    stage_code = Op.MSTORE(
        offset=0x0,
        value=int.from_bytes(child_initcode, "big"),
        new_memory_size=0x20,
    )
    create_code = Op.CREATE(
        value=0x0,
        offset=32 - len(child_initcode),
        size=len(child_initcode),
        init_code_size=len(child_initcode),
    )
    initcode = call_code + stage_code + create_code

    # The CREATE forwards only 63/64 of what the frame holds, so the
    # frame must keep more than the child needs: solve for the smallest
    # amount whose grant still covers it, then step below that grant for
    # the starved arm (the grant repeats every 64 gas, so one gas less
    # does not always forward less). The deposit rides on the child's
    # RETURN metadata.
    child_total = child_initcode.gas_cost(fork)
    frame_gas = child_total * 64 // 63
    while frame_gas - frame_gas // 64 < child_total:
        frame_gas += 1
    if oog:
        while frame_gas - frame_gas // 64 >= child_total:
            frame_gas -= 1

    # Everything else must land: the fresh create target's top-frame
    # state gas (EIP-8037), the callee, and the nested creation's peak
    # charge.
    gas_limit = (
        fork.transaction_intrinsic_cost_calculator()(
            calldata=initcode,
            contract_creation=True,
            return_cost_deducted_prior_execution=True,
        )
        + fork.transaction_top_frame_state_gas(
            contract_creation=True, sends_value=False
        )
        + callee_code.gas_cost(fork)
        + initcode.gas_cost(fork)
        + frame_gas
    )

    tx = Transaction(
        sender=sender,
        to=None,
        data=initcode,
        gas_limit=gas_limit,
    )

    created = compute_create_address(address=sender, nonce=0)
    # The nested CREATE runs while the creator's nonce is 1 (EIP-161),
    # so the child lands at the nonce-1 address and the nonce-0 address
    # must stay empty.
    child = compute_create_address(address=created, nonce=1)
    child_at_nonce0 = compute_create_address(address=created, nonce=0)

    post = {
        sender: Account(nonce=1),
        # Only the child's grant changes between the arms: the call and
        # the creating frame complete either way.
        callee: Account(storage={1: CALLEE_STORED}),
        created: Account(nonce=2, code=b""),
        child: Account(nonce=1, code=child_runtime, storage={})
        if not oog
        else Account.NONEXISTENT,
        child_at_nonce0: Account.NONEXISTENT,
    }

    state_test(pre=pre, post=post, tx=tx)
