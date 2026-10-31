"""
Archetype 13: block-versus-sender gas accounting divergence (EIP-7778).

Every receipt consumer on mainnet -- an L2 that reconstructs L1 data
cost, a block builder that packs by `gasUsed`, a dashboard that reports
block fullness, a relayer that reimburses a sponsored transaction -- has
exactly one number to work from: the receipt's `gasUsed`. Until
EIP-7778 that number *was* the transaction's contribution to the block,
by construction: pre-Amsterdam EELS writes

    block_output.block_gas_used += tx_gas_used_after_refund        prague/fork.py:941
    receipt = make_receipt(tx, error, block_output.block_gas_used, logs)

so the receipt field and the block counter are literally the same
variable. EIP-7778 splits them into three distinct counters
(`amsterdam/fork.py:1068-1072`):

    block_output.block_gas_used       += settlement.execution_gas_used
    block_output.block_state_gas_used += settlement.state_gas_used
    block_output.cumulative_gas_used  += settlement.gas_used

and the settlement makes the first ignore refunds while the last applies
them (`amsterdam/vm/gas.py:1210-1222`):

    gas_used_before_refund = tx_gas - gas_left - state_gas_left
    gas_refund             = min(gas_used_before_refund // Uint(5), refund_counter)
    gas_used               = max(gas_used_before_refund - gas_refund, calldata_floor)
    execution_gas_used     = max(gas_used_before_refund - settled_state_gas_used,
                                 calldata_floor)

The settlement docstring states the intent outright: *"Unlike the
sender-facing `gas_used`, it ignores refunds: block accounting counts
pre-refund gas ([EIP-7778])."*

**The invariant, two-sided.** Through Osaka, a receipt's `gasUsed` is the
transaction's block-gas contribution. From EIP-7778 the two are
different numbers, and the gap is exactly the refund. Code that infers
block fullness, an L1 charge, or a fee from a receipt must switch which
number it uses, and nothing in a receipt tells it to.

Why this needs its own archetype rather than reusing the official
EIP-7778 suite: `tests/amsterdam/eip7778_block_gas_accounting_without_refunds/`
derives every expectation from the fork under test
(`code.execution_cost(fork)`, `max_refund_quotient`, `data_floor_calc`),
so it re-computes both sides of the equality and cannot fail when a cost
or a rule moves -- see `docs/COVERAGE-GAP.md`. Nothing anywhere asserts
the *pre*-7778 identity on the forks where deployed code still relies on
it. That is what the first two tests here do.

Measured, not assumed. Every number below came from
`tests/tools/settlement_probe/`, which wraps `settle_transaction_gas`
and the t8n result builder with logging-only side effects and prints
every settlement quantity per transaction. See README.md for the
command and the full table.
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

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7778.md"
REFERENCE_SPEC_VERSION = "N/A"

# The witness shape: a transaction that clears four storage slots which
# were already non-zero when it started. This is the single most common
# refunding idiom on mainnet (a token transfer that zeroes an allowance,
# a lock being released, a queue entry being consumed), and it creates no
# state, so the state-gas dimension stays at zero and the execution
# dimension carries the whole transaction.
CLEARED_SLOTS = (0x01, 0x02, 0x03, 0x04)

# A transaction gas limit far above anything the body needs. The
# settlement figures are independent of it: `gas_used_before_refund` is
# `tx_gas - gas_left`, and `gas_left` moves with `tx_gas`. Verified by
# measurement -- the probe reports the same 63,424 at every limit tried.
GAS_LIMIT = 1_000_000

# ---------------------------------------------------------------------------
# Measured settlement figures, CHECKED (tests/tools/settlement_probe, 4 clears)
#
#   fork                 receipt gasUsed   header gas_used   divergence
#   Berlin                       20,512            20,512            0
#   London                       32,820            32,820            0
#   Cancun                       32,820            32,820            0
#   Prague                       32,820            32,820            0
#   Osaka                        32,820            32,820            0
#   Amsterdam                    50,740            63,424       12,684
#
# Berlin needs its own literal because EIP-3529 moved both the clear
# refund (15,000 -> 4,800) and the refund cap divisor (2 -> 5); London
# through Osaka share one figure, which is why one literal covers the
# whole span.
# ---------------------------------------------------------------------------
BERLIN_GAS_USED = 20_512
LONDON_THROUGH_OSAKA_GAS_USED = 32_820

AMSTERDAM_RECEIPT_GAS_USED = 50_740
AMSTERDAM_BLOCK_GAS_USED = 63_424

# The pinned Amsterdam pair is self-checking rather than two free
# numbers. In this construction the refund counter (4 x 11,616 = 46,464)
# exceeds the cap, so the cap binds and the divergence is exactly one
# fifth of the block figure -- the London refund divisor, read straight
# off `amsterdam/vm/gas.py:1212`. A re-measurement after a repricing must
# preserve this relation; if it cannot, the *rule* changed, not the cost.
assert (
    AMSTERDAM_BLOCK_GAS_USED - AMSTERDAM_RECEIPT_GAS_USED
    == AMSTERDAM_BLOCK_GAS_USED // 5
), "the pinned divergence is no longer one capped refund"


def _clearing_contract(pre: Alloc) -> tuple[object, Storage]:
    """
    Deploy a contract whose slots are non-zero and which zeroes them.

    The post-state storage is returned labelled, so a failure reads
    `cleared_3: want 0x0, got 0x1` and a reader can tell "the refund was
    never earned" apart from "the accounting changed". Without this the
    pinned gas figures could pass vacuously on a transaction that never
    refunded anything.

    Slot numbering starts at 1 deliberately. Slot 0 would assemble as
    `PUSH0` from Shanghai and `PUSH1 0` before it, a one-gas-per-slot
    fork split that would cost this archetype its single London-through-
    Osaka literal for no benefit.
    """
    expected = Storage()
    expected._current_slot = CLEARED_SLOTS[0]
    slots = [expected.store_next(0, f"cleared_{i}") for i in range(len(CLEARED_SLOTS))]
    assert tuple(slots) == CLEARED_SLOTS

    body = Op.SSTORE(slots[0], 0)
    for slot in slots[1:]:
        body += Op.SSTORE(slot, 0)
    target = pre.deploy_contract(body + Op.STOP, storage=dict.fromkeys(slots, 1))
    return target, expected


def _tx(pre: Alloc, target: object, receipt_gas_used: int) -> Transaction:
    """A refunding transaction with its receipt figure pinned."""
    return Transaction(
        to=target,
        gas_limit=GAS_LIMIT,
        # Explicit 0 is cross-fork safe: only a *positive* reservoir
        # raises pre-Amsterdam (`transaction_types.py:353`). It is also
        # the honest case here -- a legacy receipt consumer predates
        # state gas entirely, so the transaction it is reading declares
        # no reservoir and the whole cost lands in the execution
        # dimension, which is where the refund divergence lives.
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(gas_used=receipt_gas_used),
    )


@pytest.mark.valid_from("Berlin")
@pytest.mark.valid_until("Berlin")
def test_receipt_gas_used_is_the_block_contribution_berlin(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test a refunding transaction's receipt figure equals its block figure.

    Berlin arm. The same literal is pinned to the receipt's `gasUsed`
    and to the block header's `gasUsed`, so the equality is encoded in
    the test's structure and cannot be satisfied by tuning one side.
    Berlin is split out because its refund constants differ from
    London's (EIP-3529), not because the invariant differs.
    """
    target, expected_storage = _clearing_contract(pre)
    state_test(
        pre=pre,
        post={target: Account(storage=expected_storage)},
        tx=_tx(pre, target, BERLIN_GAS_USED),
        blockchain_test_header_verify=Header(gas_used=BERLIN_GAS_USED),
    )


@pytest.mark.valid_from("London")
@pytest.mark.valid_until("Osaka")
def test_receipt_gas_used_is_the_block_contribution(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test a refunding transaction's receipt figure equals its block figure.

    This is the identity every deployed receipt consumer was written
    against, asserted on the forks where it holds. One literal is pinned
    to both sides: the receipt's `gasUsed` and the block header's
    `gasUsed`. Pre-Amsterdam EELS makes them the same variable
    (`prague/fork.py:941,944`), so a fork that splits them fails here
    even if it keeps every gas cost unchanged.
    """
    target, expected_storage = _clearing_contract(pre)
    state_test(
        pre=pre,
        post={target: Account(storage=expected_storage)},
        tx=_tx(pre, target, LONDON_THROUGH_OSAKA_GAS_USED),
        blockchain_test_header_verify=Header(
            gas_used=LONDON_THROUGH_OSAKA_GAS_USED
        ),
    )


@pytest.mark.valid_from("EIP7778")
def test_receipt_gas_used_diverges_from_the_block_contribution(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test the receipt figure and the block figure are different numbers.

    The identical transaction now settles two ways: the sender is
    charged 50,740 and the block counts 63,424, a gap of 12,684 -- one
    capped refund. A receipt consumer that keeps using `gasUsed` as the
    block contribution under-reports the block by that much on every
    refunding transaction.

    Pinning the violation next to the invariant keeps the pair honest.
    If a later fork re-merges the counters, this test fails and the two
    above start applying again, which is the signal we want rather than
    silence.
    """
    target, expected_storage = _clearing_contract(pre)
    state_test(
        pre=pre,
        post={target: Account(storage=expected_storage)},
        tx=_tx(pre, target, AMSTERDAM_RECEIPT_GAS_USED),
        blockchain_test_header_verify=Header(
            gas_used=AMSTERDAM_BLOCK_GAS_USED
        ),
    )
