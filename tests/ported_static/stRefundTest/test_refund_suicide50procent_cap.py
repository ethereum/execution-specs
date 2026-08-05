"""
Verify the EIP-3529 refund cap when eight storage clears surround a
gas-limited call to a self-destructing contract: the stored gas delta and
the sender's final balance track the executed gas minus the capped refund,
for both a starved and a fully funded sub-call.

Ported from:
state_tests/stRefundTest/refundSuicide50procentCapFiller.json

@manually-enhanced: Do not overwrite. The sub-call grant, the stored gas
delta, the refund cap and the budget all derive from fork composites; the
destructor self-destructs to CALLER so every address is dynamic; the post
branches on EIP-6780 for the destructor's survival.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

TARGET_BALANCE = 0xDE0B6B3A7640000
DESTRUCTOR_BALANCE = 0xDE0B6B3A7640000
INITIAL_BALANCE = 10**18
GAS_PRICE = 10
FLAG_SLOT = 0xA
RESULT_SLOT = 0xB
GAS_SLOT = 0x17
SNAPSHOT_OFFSET = 0x16
MEMORY_SIZE = SNAPSHOT_OFFSET + 32
GRANT_MARGIN = 1_000


@pytest.mark.ported_from(
    ["state_tests/stRefundTest/refundSuicide50procentCapFiller.json"],
)
@pytest.mark.valid_from("London")
@pytest.mark.parametrize(
    "call_succeeds",
    [False, True],
    ids=["starved_grant", "full_grant"],
)
def test_refund_suicide50procent_cap(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    call_succeeds: bool,
) -> None:
    """Storage clears around a self-destruct call refund up to the cap."""
    destructor_code = Op.SELFDESTRUCT(
        address=Op.CALLER, address_warm=True, account_new=False
    )
    destructor = pre.deploy_contract(
        code=destructor_code,
        balance=DESTRUCTOR_BALANCE,
    )

    # The grant either covers the destructor completely or falls one gas
    # short, so the sub-call forfeits its whole grant.
    destructor_cost = destructor_code.gas_cost(fork)
    if call_succeeds:
        grant = destructor_cost + GRANT_MARGIN
        inner_consumed = destructor_cost
    else:
        grant = destructor_cost - 1
        inner_consumed = grant
    call_result = 1 if call_succeeds else 0

    # First GAS read: the delta window opens after the GAS opcode itself.
    head = Op.MSTORE(
        offset=SNAPSHOT_OFFSET, value=Op.GAS, new_memory_size=MEMORY_SIZE
    )
    body = Op.SSTORE(
        key=FLAG_SLOT,
        value=0x1,
        key_warm=False,
        original_value=0,
        new_value=1,
    ) + Op.SSTORE(
        key=RESULT_SLOT,
        value=Op.CALL(
            gas=Op.CALLDATALOAD(offset=0x0),
            address=destructor,
            address_warm=False,
        ),
        key_warm=False,
        original_value=0,
        new_value=call_result,
    )
    for slot in range(1, 9):
        body += Op.SSTORE(
            key=slot,
            value=0x0,
            key_warm=False,
            original_value=1,
            new_value=0,
        )
    # Second GAS read closes the window; the head's own GAS cost stands in
    # for it in the derived delta (both GAS reads cost the same).
    # new_value is a placeholder: an SSTORE's cost depends only on the
    # zero/non-zero transition, not the stored magnitude.
    tail = Op.SSTORE(
        key=GAS_SLOT,
        value=Op.SUB(
            Op.MLOAD(
                offset=SNAPSHOT_OFFSET,
                new_memory_size=MEMORY_SIZE,
                old_memory_size=MEMORY_SIZE,
            ),
            Op.GAS,
        ),
        key_warm=False,
        original_value=0,
        new_value=1,
    )
    target = pre.deploy_contract(
        code=head + body + tail + Op.STOP,
        storage=dict.fromkeys(range(1, 9), 1),
        balance=TARGET_BALANCE,
    )

    gas_delta = head.gas_cost(fork) + body.gas_cost(fork) + inner_consumed

    data = Hash(grant)
    # The refund cap is a fifth of the gas actually deducted before
    # execution, which excludes the EIP-7623 calldata floor.
    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        calldata=data, return_cost_deducted_prior_execution=True
    )
    executed = intrinsic + gas_delta + tail.gas_cost(fork)
    gas_limit = executed + 5_000

    sender = pre.fund_eoa(amount=INITIAL_BALANCE)
    tx = Transaction(
        sender=sender,
        to=target,
        data=data,
        gas_limit=gas_limit,
        gas_price=GAS_PRICE,
    )

    # EIP-3529 caps the refund at a fifth of the executed gas.
    total_refund = body.refund(fork) + (
        destructor_code.refund(fork) if call_succeeds else 0
    )
    refund = min(total_refund, executed // 5)
    gas_used = executed - refund

    post = {
        target: Account(
            storage={
                FLAG_SLOT: 1,
                RESULT_SLOT: call_result,
                GAS_SLOT: gas_delta,
            },
            balance=TARGET_BALANCE
            + (DESTRUCTOR_BALANCE if call_succeeds else 0),
        ),
        # EIP-6780: a pre-existing contract is no longer deleted, only
        # its balance is transferred.
        destructor: (
            (
                Account(balance=0)
                if fork.is_eip_enabled(6780)
                else Account.NONEXISTENT
            )
            if call_succeeds
            else Account(balance=DESTRUCTOR_BALANCE, storage={})
        ),
        sender: Account(balance=INITIAL_BALANCE - gas_used * GAS_PRICE),
    }

    state_test(pre=pre, post=post, tx=tx)
