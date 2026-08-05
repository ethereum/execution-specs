"""
Verify a contract-creation transaction whose init code first calls an
existing contract and then CREATEs a child: with a full budget both the
call and the nested creation land (the child at the creator's nonce-1
address, not nonce 0); with a starved budget the callee and the whole
creation fail together.

Ported from:
state_tests/stCreateTest/CREATE_EContractCreateNEContractInInitOOG_TrFiller.json

@manually-enhanced: Do not overwrite. Budgets are derived from the fork
(intrinsic + EIP-8037 top-frame and nested-create state gas + composed
code costs), the callee call forwards all gas instead of a ported fixed
budget, and the nested child is now asserted at its real nonce-1 address
(the port only checked the vacuous nonce-0 address).
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
        value=int.from_bytes(bytes(child_runtime), "big"),
        new_memory_size=0x20,
    ) + Op.RETURN(
        offset=32 - len(bytes(child_runtime)),
        size=len(bytes(child_runtime)),
    )
    child_initcode_bytes = bytes(child_initcode)

    # Transaction init code: call the callee (forwarding all gas), then
    # CREATE the child from memory; deploys nothing itself.
    call_code = Op.POP(Op.CALL(address=callee))
    stage_code = Op.MSTORE(
        offset=0x0,
        value=int.from_bytes(child_initcode_bytes, "big"),
        new_memory_size=0x20,
        old_memory_size=0x20,
    )
    create_code = Op.CREATE(
        value=0x0,
        offset=32 - len(child_initcode_bytes),
        size=len(child_initcode_bytes),
        new_memory_size=0x20,
        old_memory_size=0x20,
        init_code_size=len(child_initcode_bytes),
    )
    initcode = call_code + stage_code + create_code

    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        calldata=initcode,
        contract_creation=True,
    )
    if oog:
        # Enough to start executing, but the forwarded 63/64 undercuts
        # the callee's store and the CREATE is unaffordable after it.
        gas_limit = intrinsic + callee_code.gas_cost(fork) // 2
    else:
        # Everything must land: the fresh create target's top-frame
        # state gas (EIP-8037), the callee, and the nested creation's
        # peak charge plus the child's execution and code deposit.
        runtime_size = len(bytes(child_runtime))
        child_total = (
            child_initcode.gas_cost(fork)
            + runtime_size * fork.gas_costs().CODE_DEPOSIT_PER_BYTE
            + fork.code_deposit_state_gas(code_size=runtime_size)
        )
        needed = (
            intrinsic
            + fork.transaction_top_frame_state_gas(contract_creation=True)
            + initcode.gas_cost(fork)
            + callee_code.gas_cost(fork)
            + child_total
        )
        # Headroom for the 63/64 withhold at the call and the CREATE.
        gas_limit = needed + needed // 63

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

    if oog:
        post = {
            sender: Account(nonce=1),
            callee: Account(storage={1: 0}),
            created: Account.NONEXISTENT,
            child: Account.NONEXISTENT,
            child_at_nonce0: Account.NONEXISTENT,
        }
    else:
        post = {
            sender: Account(nonce=1),
            callee: Account(storage={1: CALLEE_STORED}),
            created: Account(nonce=2, code=b""),
            child: Account(nonce=1, code=bytes(child_runtime), storage={}),
            child_at_nonce0: Account.NONEXISTENT,
        }

    state_test(pre=pre, post=post, tx=tx)
