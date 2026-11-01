"""
Archetype 14: state-gas block accounting is one-sided (EIP-8037).

EIP-8037 prices state *creation* in a second gas dimension. The obvious
reading is that the dimension is symmetric -- that freeing state returns
what creating it cost -- and that reading is wrong. The settlement
clamps the net at zero (`amsterdam/vm/gas.py:1216`):

    settled_state_gas_used = StateGas(Uint(max(0, state_gas_used)))

with the docstring explaining the clamp as *"the state gas used (clamped
to zero, since refunds can drive it negative)"*. That counter is what
the block carries (`amsterdam/fork.py:1069`), and the block header's
`gasUsed` is `max(block_gas_used, block_state_gas_used)`
(`amsterdam/fork.py:335-338`).

**The invariant:** a transaction is never paid for freeing state. Its
block-level state-gas contribution is the full price of everything it
created and **nothing** for anything it destroyed, floored at zero and
never negative. A contract, relayer, or sponsor that budgets on the
assumption that clearing storage offsets creating it is budgeting
against a rule that does not exist.

The measurements below (CHECKED, `tests/tools/settlement_probe/`) make
the one-sidedness impossible to misread: freeing two slots and freeing
four slots, each alongside one creation, carry the **same** block
state-gas figure as freeing none.

    shape                 raw state_gas_used   block state gas   header gasUsed
    free 3, create 0                       0                 0           51,318
    free 0, create 1                 +97,920            97,920           97,920
    free 2, create 1                 +97,920            97,920           97,920
    free 4, create 1                 +97,920            97,920           97,920
    set and clear one slot                 0                 0           27,212

**Where the one-sidedness actually lives, and a correction worth
recording.** It is *not* the `max(0, ...)` clamp. Clearing a slot that
was already non-zero when the transaction began accrues no state-gas
refund at all: `sstore` credits `StateGasCosts.STORAGE_SET` only under
`if original_value == 0`, i.e. only for a slot the same transaction
created (`amsterdam/vm/instructions/storage.py:149-151`). So the
asymmetry is enforced one level earlier than the clamp, in the refund
guard. Ten adversarial constructions were measured for a negative net --
in-frame set/clear, a `DELEGATECALL` child clearing the parent's fresh
slot, the same with a positive reservoir, an EIP-7702 authorization
(the only `commit_state_gas` path, which leaves the spill at zero so
later credits route to the reservoir), a `CREATE` whose child aborts
after the `NEW_ACCOUNT` charge -- and **every one measured
`state_gas_used` at exactly 0 or exactly +97,920. None was negative.**
Under the reference refund rules the clamp has nothing to clamp; it is
defensive. That is a result, not a gap, and it is why the mutation
`state-clamp-off` correctly survives while `state-clamp-min` and
`state-free-credit` are detected -- see README.md for the arithmetic.

`state_gas_reservoir=0` throughout. The reservoir changes which pool a
charge draws from and therefore `gas_used_before_refund`
(`= tx_gas - gas_left - state_gas_left`), so it has to be pinned for
the figures to be stable; 0 is the cross-fork-safe value and the
realistic one for a legacy caller that declares no reservoir.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Header,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    TransactionReceipt,
)

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-8037.md"
REFERENCE_SPEC_VERSION = "N/A"

GAS_LIMIT = 1_000_000

# COST_PER_STATE_BYTE 1530 x STATE_BYTES_PER_STORAGE_SET 64
# (`amsterdam/vm/gas.py:47,49`). One fresh storage slot.
ONE_STORAGE_SET_STATE_GAS = 97_920

# Measured, CHECKED. A net-freeing transaction: three slots zeroed, none
# created. `block_state_gas_used` is 0, so the header carries the
# execution figure, which is `gas_used_before_refund` undiminished --
# the freeing bought no reduction in either counter.
FREE_ONLY_HEADER_GAS_USED = 51_318
FREE_ONLY_RECEIPT_GAS_USED = 41_055

# Measured, CHECKED. One creation plus `frees` clears of pre-existing
# slots. The header is `max(execution, state)` and the state dimension
# wins in all three, so the pinned header figure *is* the block's
# state-gas contribution -- identical across every row.
CREATE_ONE_HEADER_GAS_USED = ONE_STORAGE_SET_STATE_GAS
CREATE_ONE_RECEIPT_GAS_USED = {0: 125_026, 2: 126_006, 4: 138_760}

# Measured, CHECKED. One slot created and then cleared by the same
# transaction: the only shape that earns a state-gas credit at all. The
# credit exactly cancels the charge, so the net is 0 and the execution
# figure is as if no state gas had moved.
SET_THEN_CLEAR_HEADER_GAS_USED = 27_212
SET_THEN_CLEAR_RECEIPT_GAS_USED = 21_770


def _storage_with_labels(slots: list[int], value: int, tag: str) -> Storage:
    """Build a labelled expected-storage map over explicit slot numbers."""
    out = Storage()
    for slot in slots:
        out._current_slot = slot
        out.store_next(value, f"{tag}_{slot}")
    return out


def _tx(pre: Alloc, target: object, receipt_gas_used: int) -> Transaction:
    return Transaction(
        to=target,
        gas_limit=GAS_LIMIT,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(gas_used=receipt_gas_used),
    )


@pytest.mark.valid_from("EIP8037")
def test_net_freeing_tx_gets_no_block_state_gas_credit(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test a transaction that only frees state contributes zero state gas.

    Three slots that were non-zero at transaction start are zeroed and
    nothing is created. The block's state-gas counter for this
    transaction is exactly 0 -- not negative, and not a credit against
    the execution dimension. The header therefore carries the execution
    figure in full, 51,318, which is `gas_used_before_refund` with no
    deduction for the three slots of state the transaction removed.

    The labelled post-state proves the frees really happened; without it
    the pinned gas figures could be satisfied by a transaction that
    cleared nothing.
    """
    slots = [1, 2, 3]
    body = Op.SSTORE(slots[0], 0)
    for slot in slots[1:]:
        body += Op.SSTORE(slot, 0)
    target = pre.deploy_contract(body + Op.STOP, storage=dict.fromkeys(slots, 1))

    state_test(
        pre=pre,
        post={target: Account(storage=_storage_with_labels(slots, 0, "freed"))},
        tx=_tx(pre, target, FREE_ONLY_RECEIPT_GAS_USED),
        blockchain_test_header_verify=Header(gas_used=FREE_ONLY_HEADER_GAS_USED),
    )


@pytest.mark.parametrize("frees", [0, 2, 4])
@pytest.mark.valid_from("EIP8037")
def test_freeing_more_than_creating_is_still_charged_in_full(
    state_test: StateTestFiller,
    pre: Alloc,
    frees: int,
) -> None:
    """
    Test the block state-gas charge ignores how much state was freed.

    One slot is created and `frees` pre-existing slots are zeroed, so at
    `frees=2` and `frees=4` the transaction is physically net-freeing:
    it leaves the trie smaller than it found it. All three params pin
    the **same** header figure, 97,920, one `STORAGE_SET`. The creation
    is charged in full and the frees earn nothing, however many there
    are.

    The receipt figures differ per param (125,026 / 126,006 / 138,760),
    and are pinned too, so "the header did not move" cannot be satisfied
    by three transactions that did the same work.

    `frees` stops at 4 on purpose. The header is
    `max(block_gas_used, block_state_gas_used)`, and each additional
    clear adds to the execution dimension; at `frees=4` the execution
    figure is 75,530, still under 97,920. Past the crossover the header
    would stop reporting the state counter and the test would silently
    change meaning.
    """
    created = 1
    freed = list(range(2, 2 + frees))
    body = Op.SSTORE(created, 1)
    for slot in freed:
        body += Op.SSTORE(slot, 0)
    target = pre.deploy_contract(
        body + Op.STOP, storage=dict.fromkeys(freed, 1)
    )

    expected = _storage_with_labels(freed, 0, "freed")
    expected._current_slot = created
    expected.store_next(1, "created")

    state_test(
        pre=pre,
        post={target: Account(storage=expected)},
        tx=_tx(pre, target, CREATE_ONE_RECEIPT_GAS_USED[frees]),
        blockchain_test_header_verify=Header(gas_used=CREATE_ONE_HEADER_GAS_USED),
    )


@pytest.mark.valid_from("EIP8037")
def test_set_then_clear_nets_to_zero_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test the one credited shape nets to exactly zero, not below it.

    A slot created and then cleared by the same transaction is the only
    case `sstore` credits state gas for (`original_value == 0`). The
    credit is one `STORAGE_SET`, exactly the charge, so the net is 0:
    the block's state-gas counter is 0 and the execution figure, 27,212,
    is as if the round trip had never touched the state dimension.

    This is the boundary the clamp guards. It sits *at* zero rather than
    below it, which is why the clamp itself is unobservable here; a rule
    that made the credit larger than the charge would push this figure
    negative, and the mutation `state-free-credit` is exactly that rule.
    """
    target = pre.deploy_contract(Op.SSTORE(1, 1) + Op.SSTORE(1, 0) + Op.STOP)

    state_test(
        pre=pre,
        post={target: Account(storage=_storage_with_labels([1], 0, "round_tripped"))},
        tx=_tx(pre, target, SET_THEN_CLEAR_RECEIPT_GAS_USED),
        blockchain_test_header_verify=Header(
            gas_used=SET_THEN_CLEAR_HEADER_GAS_USED
        ),
    )
