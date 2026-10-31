"""
Archetype 15: when the calldata floor binds, a refund is invisible.

The sender-facing settlement is a maximum, not a sum
(`amsterdam/vm/gas.py:1214`, and `prague/fork.py:922` for the
EIP-7623 original):

    gas_used = max(gas_used_after_refund, calldata_floor)

So for a calldata-heavy, execution-light transaction the refund does not
reach the bill. Two transactions with identical calldata, identical gas
limits and identical fees cost their senders **exactly the same**, even
when one of them earns a large storage-clear refund and the other earns
none. A relayer, paymaster, or L2 sequencer that prices a call as
"execution minus expected refund" is computing a number the protocol
will not charge; a gas-token-style scheme that monetises refunds earns
nothing at all on this transaction shape.

**Why this is not covered already.** EIP-7976's suite has
`test_floor_cost_not_reduced_by_refunds` and a whole `test_refunds.py`,
but every one of them is `valid_from("EIP7976")` -- Amsterdam only --
and every expectation is recomputed from the fork under test
(`fork.transaction_data_floor_cost_calculator()`, `code.gas_cost(fork)`,
`fork.max_refund_quotient()`). Two gaps follow. First, the floor shipped
at **Prague** with EIP-7623 and deployed code has depended on it since;
nothing asserts the refund interaction there. Second, a test that
derives both sides of its own equality cannot fail when a cost moves
(`docs/COVERAGE-GAP.md`).

**This file asserts no gas number at all.** Two senders start with equal
balances and send transactions that differ only in whether the callee's
slots were already non-zero; a third transaction has a contract compare
their balances with `EQ(BALANCE(a), BALANCE(b))` and commit the answer
to storage. If the floor binds, the committed answer is 1. The
assertion is a committed effect, so it survives any repricing that keeps
the floor binding -- and the parametrised control arm, where the
calldata is short enough that the floor does not bind, commits 0 and
proves the comparison is not vacuous.

Measured floors, CHECKED (`tests/tools/settlement_probe/`), confirming
the per-token arithmetic by hand rather than from the fork object:

    fork         floor(len)                     per non-zero byte
    Prague       21,000 + 40 x len              TX_DATA_TOKEN_FLOOR 10 x 4 tokens
    Osaka        21,000 + 40 x len              unchanged
    Amsterdam    15,000 + 64 x len              TX_DATA_TOKEN_FLOOR 16 x 4 tokens

verified at len 128/512/2048 against 23,192 / 47,768 / 146,072
(Amsterdam) and 26,120 / 41,480 / 102,920 (Prague, Osaka). The Amsterdam
base is 15,000 not 21,000 because EIP-2780 decomposed the intrinsic base
into `TX_BASE 12,000 + COLD_ACCOUNT_ACCESS 3,000`, and the floor is
anchored on that sum (`transactions.py:777-784`). Every transaction here
is **zero-value**: a value-bearing transaction adds `TX_VALUE_COST`
6,000 to `base_execution_gas` and therefore to its floor, so a test that
did not control for `value` would be comparing two different floors.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Op,
    Storage,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7623.md"
REFERENCE_SPEC_VERSION = "N/A"

# Slots the callee clears. Eight gives a refund of 8 x 4,800 = 38,400
# (London..Osaka) or 8 x 11,616 = 92,928 (Amsterdam) before the one-fifth
# cap, i.e. far more than any rounding, so "the balances matched" cannot
# mean "the refund was negligible".
CLEARED_SLOTS = tuple(range(1, 9))

# Calldata lengths, chosen from the measured floor table above so that
# the same two lengths land on opposite sides of the floor on Prague,
# Osaka and Amsterdam alike. All bytes are non-zero, which keeps the
# token count at 4 per byte on both the EIP-7623 and EIP-7976 schedules
# and so keeps one length working across the whole span.
FLOOR_BINDS_LEN = 4096
FLOOR_SLACK_LEN = 128

# Comfortably above both the floor at 4,096 bytes (277,144 on Amsterdam)
# and the execution the callee needs.
GAS_LIMIT = 500_000

# The comparator creates one fresh storage slot, which from EIP-8037
# costs 97,920 state gas on top of its execution gas. With
# `state_gas_reservoir=0` that charge spills into `gas_left`, so the
# measured floor for "a frame that creates one slot" is ~110,026
# (`tests/frozen_budget/README.md`). An earlier 100,000 here made the
# comparator run out of gas on Amsterdam and commit 0, which looked
# exactly like "the senders paid different amounts" -- the one failure
# mode this test cannot afford to confuse.
COMPARISON_GAS_LIMIT = 400_000

# Equal starting balances; the whole test is a balance comparison.
SENDER_FUND = 10**18


def _clearing_code() -> Op:
    """Zero every slot in `CLEARED_SLOTS`, identical for both senders."""
    body = Op.SSTORE(CLEARED_SLOTS[0], 0)
    for slot in CLEARED_SLOTS[1:]:
        body += Op.SSTORE(slot, 0)
    return body + Op.STOP


@pytest.mark.parametrize(
    "data_len,floor_binds",
    [
        pytest.param(FLOOR_BINDS_LEN, True, id="floor_binds"),
        pytest.param(FLOOR_SLACK_LEN, False, id="floor_has_slack"),
    ],
)
@pytest.mark.valid_from("Prague")
def test_refund_is_invisible_while_the_calldata_floor_binds(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    data_len: int,
    floor_binds: bool,
) -> None:
    """
    Test two senders pay the same when the floor binds, despite one refunding.

    The two transactions are identical in every respect a fee depends on
    -- same calldata, same gas limit, same fees, zero value, same callee
    bytecode -- and differ only in the callee's pre-state: one callee's
    eight slots are already zero, so clearing them is a no-op that earns
    nothing, and the other's are non-zero, so clearing them earns the
    full storage-clear refund. A third transaction commits
    `EQ(BALANCE(quiet), BALANCE(refunding))`.

    `floor_binds=True` (4,096 bytes of calldata): both transactions pay
    the floor, the refund never reaches the bill, and the committed
    answer is 1.

    `floor_binds=False` (128 bytes): the refunding transaction's
    post-refund execution gas is above its floor, so it pays that
    instead and the refund *is* visible. The committed answer is 0.
    This arm is what stops the first from passing vacuously -- a broken
    comparator, or two transactions that never actually differed, would
    commit 1 here too.

    The callees' post-state storage is asserted as well, so "the
    balances matched" cannot mean "neither transaction ran".
    """
    quiet_sender = pre.fund_eoa(SENDER_FUND)
    refunding_sender = pre.fund_eoa(SENDER_FUND)
    comparing_sender = pre.fund_eoa(SENDER_FUND)

    code = _clearing_code()
    # Same bytecode, opposite pre-state: this is the only difference
    # between the two transactions.
    quiet_callee = pre.deploy_contract(code)
    refunding_callee = pre.deploy_contract(
        code, storage=dict.fromkeys(CLEARED_SLOTS, 1)
    )

    comparator_storage = Storage()
    comparator = pre.deploy_contract(
        Op.SSTORE(
            comparator_storage.store_next(
                1 if floor_binds else 0, "senders_paid_the_same"
            ),
            Op.EQ(Op.BALANCE(quiet_sender), Op.BALANCE(refunding_sender)),
        )
        + Op.STOP
    )

    data = b"\x01" * data_len

    def _tx(sender: object, to: object) -> Transaction:
        return Transaction(
            to=to,
            data=data,
            gas_limit=GAS_LIMIT,
            value=0,
            # Explicit 0 is cross-fork safe (only a positive reservoir
            # raises pre-Amsterdam, `transaction_types.py:353`) and it
            # keeps the two transactions' gas treatment identical on
            # Amsterdam, where a reservoir would change which pool the
            # state charges draw from.
            state_gas_reservoir=0,
            sender=sender,
        )

    comparison_tx = Transaction(
        to=comparator,
        gas_limit=COMPARISON_GAS_LIMIT,
        value=0,
        state_gas_reservoir=0,
        sender=comparing_sender,
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[
                    _tx(quiet_sender, quiet_callee),
                    _tx(refunding_sender, refunding_callee),
                    # Last, so it observes both senders settled.
                    comparison_tx,
                ]
            )
        ],
        post={
            quiet_callee: Account(storage=dict.fromkeys(CLEARED_SLOTS, 0)),
            refunding_callee: Account(storage=dict.fromkeys(CLEARED_SLOTS, 0)),
            comparator: Account(storage=comparator_storage),
        },
    )
